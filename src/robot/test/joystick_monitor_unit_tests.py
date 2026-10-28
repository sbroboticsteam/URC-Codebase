
import pytest
import rclpy

from unittest.mock import MagicMock
from sensor_msgs.msg import Joy
from rclpy.parameter import Parameter

from robot.joystick_monitor import JoystickMotor


@pytest.fixture
def node():
    rclpy.init()
    joystick = JoystickMotor()

    # Replace the real publisher with a mock.
    real_publisher = joystick.publisher
    joystick.publisher = MagicMock()

    yield joystick

    joystick.destroy_publisher(real_publisher)
    joystick.destroy_node()
    rclpy.shutdown()


def send_joystick(node, x, y):
    """Simulate a joystick message."""
    msg = Joy()
    msg.axes = [float(x), float(y)]

    node.joystick_callback(msg)

    return node.publisher.publish.call_args.args[0].data


def test_forward(node):
    speeds = send_joystick(node, 0, 1)
    assert list(speeds) == [1.0, 1.0, 1.0, 1.0]


def test_backward(node):
    speeds = send_joystick(node, 0, -1)
    assert list(speeds) == [-1.0, -1.0, -1.0, -1.0]


def test_turn_right(node):
    speeds = send_joystick(node, 1, 0)
    assert list(speeds) == [-1.0, 1.0, -1.0, 1.0]


def test_turn_left(node):
    speeds = send_joystick(node, -1, 0)
    assert list(speeds) == [1.0, -1.0, 1.0, -1.0]


def test_deadzone(node):
    speeds = send_joystick(node, 0.02, 0.03)
    assert list(speeds) == [0.0, 0.0, 0.0, 0.0]


def test_speed_clamping(node):
    speeds = send_joystick(node, 1, 1)
    assert list(speeds) == [0.0, 1.0, 0.0, 1.0]


def test_missing_axes(node):
    msg = Joy()
    msg.axes = [0.5]

    node.joystick_callback(msg)

    node.publisher.publish.assert_not_called()


def test_invalid_deadzone(node):
    result = node.set_parameters([
        Parameter("deadzone", value=1.5)
    ])

    assert not result[0].successful


def test_stop_motors(node):
    node.stop_motors()

    message = node.publisher.publish.call_args.args[0]
    assert list(message.data) == [0.0, 0.0, 0.0, 0.0]
