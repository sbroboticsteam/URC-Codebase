
import time

import pytest
import rclpy

from sensor_msgs.msg import Joy
from std_msgs.msg import Float32MultiArray

from robot.joystick_monitor import JoystickMotor


@pytest.fixture
def ros_nodes():
    """Create the controller and a separate test node."""
    rclpy.init()

    controller = JoystickMotor()
    tester = rclpy.create_node("joystick_integration_tester")

    publisher = tester.create_publisher(Joy, "/joy", 10)

    received_messages = []

    subscription = tester.create_subscription(
        Float32MultiArray,
        "/motor_speeds",
        lambda msg: received_messages.append(list(msg.data)),
        10,
    )

    yield controller, tester, publisher, received_messages

    tester.destroy_subscription(subscription)
    tester.destroy_node()
    controller.destroy_node()
    rclpy.shutdown()


def send_and_receive(ros_nodes, x, y, timeout=3.0):
    """Publish joystick input and wait for motor output."""
    controller, tester, publisher, received = ros_nodes

    received.clear()

    msg = Joy()
    msg.axes = [float(x), float(y)]

    deadline = time.monotonic() + timeout
    next_publish = 0.0

    while time.monotonic() < deadline:
        now = time.monotonic()

        # Repeat input until ROS discovery and delivery succeed.
        if now >= next_publish:
            publisher.publish(msg)
            next_publish = now + 0.1

        rclpy.spin_once(controller, timeout_sec=0.01)
        rclpy.spin_once(tester, timeout_sec=0.01)

        if received:
            return received[-1]

    pytest.fail(
        f"No motor speed message received within {timeout} seconds"
    )


@pytest.mark.parametrize(
    "x,y,expected",
    [
        (0.0, 1.0, [1.0, 1.0, 1.0, 1.0]),  # forward
        (0.0, -1.0, [-1.0, -1.0, -1.0, -1.0]),  # backward
        (1.0, 0.0, [-1.0, 1.0, -1.0, 1.0]),  # turn right
        (-1.0, 0.0, [1.0, -1.0, 1.0, -1.0]),  # turn left
        (0.02, 0.03, [0.0, 0.0, 0.0, 0.0]),  # deadzone
        (1.0, 1.0, [0.0, 1.0, 0.0, 1.0]),  # clamping
    ],
)
def test_joystick_topic_communication(
    ros_nodes, x, y, expected
):
    actual = send_and_receive(ros_nodes, x, y)

    assert actual == pytest.approx(expected)
