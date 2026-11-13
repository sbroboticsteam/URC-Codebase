"""ROS 2 action server for timestamped camera-sequence classification."""

from __future__ import annotations

import queue
import threading
import time
from typing import Optional, Sequence

import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
)
from robot_interfaces.action import ClassifySequence
from robot_interfaces.msg import Classification
from sensor_msgs.msg import Image


class ClassificationSessionServer(Node):
    """Subscribe to images during a single action-goal session."""

    def __init__(self) -> None:
        """Initialize parameters, publisher, and action server."""
        super().__init__('classify_sequence_server')

        self.declare_parameter('image_topic', 'image')
        self.declare_parameter('classification_topic', 'classification')
        self.declare_parameter('action_name', 'classify_sequence')
        self.declare_parameter('sequence_length', 30)
        self.declare_parameter('max_frame_gap_sec', 0.5)
        self.declare_parameter('no_frame_timeout_sec', 2.0)
        self.declare_parameter('image_queue_depth', 2)

        self._image_topic = str(self.get_parameter('image_topic').value)
        self._classification_topic = str(
            self.get_parameter('classification_topic').value
        )
        action_name = str(self.get_parameter('action_name').value)
        self._sequence_length = int(self.get_parameter('sequence_length').value)
        self._max_frame_gap_ns = int(
            float(self.get_parameter('max_frame_gap_sec').value) * 1_000_000_000
        )
        self._no_frame_timeout_sec = float(
            self.get_parameter('no_frame_timeout_sec').value
        )
        image_queue_depth = int(self.get_parameter('image_queue_depth').value)

        if self._sequence_length < 1:
            raise ValueError('sequence_length must be at least 1')
        if self._max_frame_gap_ns <= 0:
            raise ValueError('max_frame_gap_sec must be greater than 0')
        if self._no_frame_timeout_sec <= 0:
            raise ValueError('no_frame_timeout_sec must be greater than 0')
        if image_queue_depth < 1:
            raise ValueError('image_queue_depth must be at least 1')
        if not self._image_topic or not self._classification_topic or not action_name:
            raise ValueError('topic and action names must not be empty')

        image_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=image_queue_depth,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )
        self._publisher = self.create_publisher(
            Classification, self._classification_topic, 10
        )
        self._lock = threading.Lock()
        self._goal_reserved = False
        self._session_active = False
        self._session_id = 0
        self._image_subscription = None
        self._last_frame_received_at = 0.0
        self._latest_classification: Optional[Classification] = None
        self._classifications_published = 0
        self._frame_queue: queue.Queue[tuple[int, Image]] = queue.Queue(
            maxsize=image_queue_depth
        )

        self._action_server = ActionServer(
            self,
            ClassifySequence,
            action_name,
            execute_callback=self._execute_callback,
            goal_callback=self._goal_callback,
            cancel_callback=self._cancel_callback,
            callback_group=ReentrantCallbackGroup(),
        )
        self._image_qos = image_qos
        self._worker_shutdown = threading.Event()
        self._classifier_worker = threading.Thread(
            target=self._classification_worker,
            name='classification-worker',
            daemon=True,
        )
        self._classifier_worker.start()
        self.get_logger().info(
            f'Action {action_name!r} ready; image topic {self._image_topic!r}, '
            f'classification topic {self._classification_topic!r}'
        )

    def _goal_callback(self, _request: ClassifySequence.Goal) -> GoalResponse:
        """Allow only one active or pending session goal."""
        with self._lock:
            if self._goal_reserved:
                return GoalResponse.REJECT
            self._goal_reserved = True
        return GoalResponse.ACCEPT

    @staticmethod
    def _cancel_callback(_goal_handle) -> CancelResponse:
        return CancelResponse.ACCEPT

    def _execute_callback(self, goal_handle) -> ClassifySequence.Result:
        result = ClassifySequence.Result()
        try:
            with self._lock:
                self._session_id += 1
                self._clear_frame_queue()
                self._latest_classification = None
                self._classifications_published = 0
                self._last_frame_received_at = time.monotonic()
                self._session_active = True

            self._image_subscription = self.create_subscription(
                Image,
                self._image_topic,
                self._image_callback,
                self._image_qos,
            )
            self.get_logger().info('Classification session started')
            last_feedback_count = -1

            while True:
                if goal_handle.is_cancel_requested:
                    goal_handle.canceled()
                    break

                with self._lock:
                    received_at = self._last_frame_received_at
                    published_count = self._classifications_published

                if time.monotonic() - received_at >= self._no_frame_timeout_sec:
                    goal_handle.succeed()
                    self.get_logger().info('Session ended after the no-frame timeout')
                    break

                if published_count != last_feedback_count:
                    feedback = ClassifySequence.Feedback()
                    feedback.classifications_published = published_count
                    goal_handle.publish_feedback(feedback)
                    last_feedback_count = published_count

                time.sleep(0.05)

            with self._lock:
                latest = self._latest_classification
                result.classifications_published = self._classifications_published
                if latest is not None:
                    result.has_classification = True
                    result.latest_classification = latest
            return result
        except Exception as exc:
            self.get_logger().error(f'Classification session failed: {exc}')
            goal_handle.abort()
            return result
        finally:
            with self._lock:
                self._session_active = False
                subscription = self._image_subscription
                self._image_subscription = None
                self._goal_reserved = False
            if subscription is not None:
                self.destroy_subscription(subscription)
            self.get_logger().info('Classification session stopped')

    def _image_callback(self, message: Image) -> None:
        """Queue the newest image, dropping the oldest queued frame if full."""
        with self._lock:
            if not self._session_active:
                return
            self._last_frame_received_at = time.monotonic()
            queued_frame = (self._session_id, message)
            try:
                self._frame_queue.put_nowait(queued_frame)
            except queue.Full:
                try:
                    self._frame_queue.get_nowait()
                except queue.Empty:
                    pass
                self._frame_queue.put_nowait(queued_frame)

    def _classification_worker(self) -> None:
        """Build sequence windows and classify without blocking image callbacks."""
        frames: list[Image] = []
        last_stamp_ns: Optional[int] = None
        active_session_id: Optional[int] = None

        while not self._worker_shutdown.is_set():
            try:
                session_id, message = self._frame_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if session_id != active_session_id:
                frames.clear()
                last_stamp_ns = None
                active_session_id = session_id

            with self._lock:
                if not self._session_active or session_id != self._session_id:
                    continue

            stamp_ns = (
                message.header.stamp.sec * 1_000_000_000
                + message.header.stamp.nanosec
            )
            if stamp_ns <= 0:
                self.get_logger().warning('Ignoring image with an unset timestamp')
                continue

            if last_stamp_ns is not None:
                gap_ns = stamp_ns - last_stamp_ns
                if gap_ns <= 0 or gap_ns > self._max_frame_gap_ns:
                    frames.clear()
                    if gap_ns <= 0:
                        self.get_logger().warning(
                            'Image timestamps went backwards; resetting sequence window'
                        )
                    else:
                        self.get_logger().debug(
                            'Timestamp gap exceeded limit; resetting sequence window'
                        )

            last_stamp_ns = stamp_ns
            frames.append(message)
            if len(frames) < self._sequence_length:
                continue

            sequence = tuple(frames)
            frames.clear()
            last_stamp_ns = None
            try:
                class_label = self._classify_sequence(sequence)
            except Exception as exc:
                self.get_logger().error(f'Classifier failed: {exc}')
                continue
            if not class_label:
                continue

            classification = Classification()
            classification.class_label = class_label
            classification.window_start = sequence[0].header.stamp
            classification.window_end = sequence[-1].header.stamp
            with self._lock:
                if not self._session_active or session_id != self._session_id:
                    continue
                self._publisher.publish(classification)
                self._latest_classification = classification
                self._classifications_published += 1

    def _clear_frame_queue(self) -> None:
        """Discard images left over from a previous action session."""
        while True:
            try:
                self._frame_queue.get_nowait()
            except queue.Empty:
                return

    def destroy_node(self):
        """Stop the classifier worker before destroying ROS entities."""
        with self._lock:
            self._session_active = False
        self._worker_shutdown.set()
        self._classifier_worker.join(timeout=1.0)
        return super().destroy_node()

    @staticmethod
    def _classify_sequence(sequence: Sequence[Image]) -> Optional[str]:
        """Return a label from the model; replace this placeholder during integration."""
        # TODO: Convert the image sequence to the selected model's input and infer a label.
        del sequence
        return None


def main(args=None) -> None:
    """Run the classification action server node."""
    rclpy.init(args=args)
    node = ClassificationSessionServer()
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)
    try:
        executor.spin()
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()