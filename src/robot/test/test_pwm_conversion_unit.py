import time
from unittest.mock import MagicMock

import pytest
import rclpy
from rclpy.parameter import Parameter
from std_msgs.msg import Float32MultiArray

from robot.pwm_conversion import PWMNode

# Run with :
# colcon test --packages-select robot \
#   --pytest-args test/test_pwm_conversion_unit.py \
#   --event-handlers console_direct+ 

@pytest.fixture
def make_node():
    state = {}

    def _make(**params):
        args = ["--ros-args"]
        for k, v in params.items():
            args += ["-p", f"{k}:={v}"]
        rclpy.init(args=args)
        n = PWMNode()
        n.publisher = MagicMock()
        state["node"] = n
        return n

    yield _make

    if "node" in state:
        state["node"].destroy_node()
        rclpy.shutdown()


def published(node):
    return list(node.publisher.publish.call_args.args[0].data)

def send_commands(node, values):
    node.on_commands(Float32MultiArray(data=[float(v) for v in values]))
    node.publish_pwm()
    return published(node)

def test_custom_pwm_range(make_node):
    node = make_node(pwm_min=1100, pwm_max=1700)  # midpoint is 1400
    node.on_commands(Float32MultiArray(data=[-1.0, 0.0, 0.5, 1.0]))
    node.publish_pwm()
    assert published(node) == [1100, 1400, 1550, 1700]


def test_custom_neutral_used_before_command_and_on_timeout(make_node):
    node = make_node(neutral_pwm=1450, command_timeout_sec=0.1)

    node.publish_pwm()
    assert published(node) == [1450] * 4

    node.on_commands(Float32MultiArray(data=[1.0] * 4))
    node.last_command_at = time.monotonic() - 0.2
    node.publish_pwm()
    assert published(node) == [1450] * 4


def test_custom_motor_count(make_node):
    node = make_node(motor_count=6)

    node.on_commands(Float32MultiArray(data=[0.0] * 4))  # old length, now invalid
    assert node.last_command_at is None

    node.on_commands(Float32MultiArray(data=[0.0, 0.5, -0.5, 1.0, -1.0, 0.0]))
    node.publish_pwm()
    assert published(node) == [1500, 1750, 1250, 2000, 1000, 1500]

@pytest.mark.parametrize(
    "cmds, expected",
    [
        ([-1.0, -0.5, 0.0, 0.5], [1000, 1250, 1500, 1750]),
        ([1.0, 1.0, 1.0, 1.0], [2000] * 4),
    ],
)
def test_conversion(make_node, cmds, expected):
    assert send_commands(make_node(), cmds) == expected


def test_saturation(make_node):
    assert send_commands(make_node(), [5.0, -5.0, 1.1, -1.1]) == [2000, 1000, 2000, 1000]


def test_startup_neutral(make_node):
    node = make_node()
    node.publish_pwm()
    assert published(node) == [1500] * 4


def test_timeout_neutral(make_node):
    node = make_node()
    send_commands(node, [1.0] * 4)
    node.last_command_at = time.monotonic() - (node.timeout + 0.1)
    node.publish_pwm()
    assert published(node) == [1500] * 4


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_non_finite_keeps_previous(make_node, bad):
    node = make_node()
    send_commands(node, [0.5] * 4)
    assert send_commands(node, [bad] * 4) == [1750] * 4