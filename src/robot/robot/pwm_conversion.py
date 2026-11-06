"""Convert four normalized motor commands into ESC pulse widths."""

import math
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, UInt16MultiArray


class PWMNode(Node):
    def __init__(self):
        super().__init__('pwm_node')

        self.declare_parameter('publish_rate_hz', 20.0)
        self.declare_parameter('command_timeout_sec', 0.5)
        self.declare_parameter('neutral_pwm', 1500)

        
        self.declare_parameter('L', 1000)
        self.declare_parameter('H', 2000)

        self.L = int(self.get_parameter('L').value)
        self.H = int(self.get_parameter('H').value)


        rate = float(self.get_parameter('publish_rate_hz').value)
        self.timeout = float(self.get_parameter('command_timeout_sec').value)
        self.neutral = int(self.get_parameter('neutral_pwm').value)
        if rate <= 0 or self.timeout <= 0 or not (1000 <= self.neutral <= 2000):
            raise ValueError('Invalid publish rate, timeout, or neutral PWM setting')

        self.publisher = self.create_publisher(UInt16MultiArray, '/motor_pwm', 10)
        self.subscription = self.create_subscription(
            Float32MultiArray,
            '/motor_speeds',
            self.on_commands,
            10
        )
        self.commands = [0.0] * 4
        self.last_command_at = None
        self.timer = self.create_timer(1.0 / rate, self.publish_pwm)
        self.get_logger().info('PWM conversion node started')

    def on_commands(self, msg):
        if len(msg.data) != 4:
            self.get_logger().warning('Expected exactly 4 motor commands')
            return
        if not all(math.isfinite(value) for value in msg.data):
            self.get_logger().warning('Motor commands must be finite numbers')
            return

        # Saturate out-of-range inputs to the permitted [-1, 1] interval.
        self.commands = [max(-1.0, min(1.0, value)) for value in msg.data]
        self.last_command_at = time.monotonic()

    def publish_pwm(self):

        timed_out = (
            self.last_command_at is None
            or time.monotonic() - self.last_command_at > self.timeout
        )
        if timed_out:
            values = [self.neutral] * 4
        else:
            values = [self.convert_to_pwm(value) for value in self.commands]

        msg = UInt16MultiArray()
        msg.data = [int(value) for value in values]
        self.publisher.publish(msg)

    def convert_to_pwm(self, x):
        x = max(-1.0, min(1.0, x))  # Saturate to [-1, 1]

        return round(
            (self.L + self.H) / 2 
            + ((self.H - self.L) / 2) * x
        )


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = PWMNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
