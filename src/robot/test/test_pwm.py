
#!/usr/bin/env python3

"""Integration test for the four-motor PWM conversion node."""

import unittest
import rclpy
import time

import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions

from std_msgs.msg import Float32MultiArray, UInt16MultiArray


def generate_test_description():
    return launch.LaunchDescription(
        [
            launch_ros.actions.Node(
                package="robot",
                executable="pwm_conversion",
                name="pwm_node",
                output="screen",
                parameters=[{
                    "pwm_min": 1000,
                    "pwm_max": 2000,
                    "neutral_pwm": 1500,
                    "publish_rate_hz": 20.0,
                    "command_timeout_sec": 0.5
                }]
            ),
            launch_testing.actions.ReadyToTest()
        ]
    )


#tests
class TestPWM(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.shutdown()

    def setUp(self):
        self.node = rclpy.create_node("test_pwm")

    def tearDown(self):
        self.node.destroy_node()

    def test_pwm_conversion(self, proc_output):
        """Check whether motor commands are converted to PWM."""

        msgs_rx = []

        sub = self.node.create_subscription(
            UInt16MultiArray,
            "/motor_pwm",
            lambda msg: msgs_rx.append(msg),
            100
        )

        pub = self.node.create_publisher(
            Float32MultiArray,
            "/motor_commands",
            10
        )

        try:
            end_time = time.monotonic() + 5.0

            while time.monotonic() < end_time:

                msg = Float32MultiArray()
                msg.data = [-1.0, -0.5, 0.5, 1.0]

                pub.publish(msg)

                rclpy.spin_once(
                    self.node,
                    timeout_sec=0.1
                )

            self.assertGreater(
                len(msgs_rx),
                0,
                "No PWM messages received"
            )

            expected = [1000, 1250, 1750, 2000]
            self.assertTrue(
                any(
                    list(msg.data) == expected
                    for msg in msgs_rx
                ),
                "Expected PWM values were not received"
            )

        finally:
            self.node.destroy_subscription(sub)
            self.node.destroy_publisher(pub)