from rcl_interfaces.msg import (
    FloatingPointRange,
    ParameterDescriptor,
    SetParametersResult,
)
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Joy
from std_msgs.msg import Float32MultiArray


class JoystickMotor(Node):
    def __init__(self):
        super().__init__('joystick_motor')
        print('controller detected')
        deadzone_descriptor = ParameterDescriptor(
            description='Joystick dead zone, between 0.0 and 1.0',
            floating_point_range=[
                FloatingPointRange(
                    from_value=0.0,
                    to_value=1.0,
                    step=0.0,
                )
            ],
        )

        self.declare_parameter(
            'deadzone',
            0.05,
            deadzone_descriptor,
        )

        self.add_on_set_parameters_callback(
            self.validate_parameters
        )

        self.subscription = self.create_subscription(
            Joy,
            '/joy',
            self.joystick_callback,
            qos_profile_sensor_data,
        )

        self.publisher = self.create_publisher(
            Float32MultiArray,
            '/motor_speeds',
            10,
        )

        self.get_logger().info(
            'Joystick motor controller started.'
        )
        self.get_logger().info(
            f'Dead zone: {self.get_deadzone():.3f}'
        )
        self.get_logger().info(
            'Listening for joystick messages on /joy'
        )

    def get_deadzone(self):
        """Return the current dead zone parameter."""
        return self.get_parameter('deadzone').value

    def validate_parameters(self, parameters):
        """Reject dead zone values outside the range [0.0, 1.0]."""
        for parameter in parameters:
            if parameter.name == 'deadzone':
                if parameter.type_ != parameter.Type.DOUBLE:
                    return SetParametersResult(
                        successful=False,
                        reason='deadzone must be a floating-point value',
                    )

                value = parameter.value

                if not 0.0 <= value <= 1.0:
                    return SetParametersResult(
                        successful=False,
                        reason='deadzone must be between 0.0 and 1.0',
                    )

        return SetParametersResult(successful=True)

    def apply_deadzone(self, value):
        """Set small joystick inputs to zero."""
        deadzone = self.get_deadzone()

        if abs(value) < deadzone:
            return 0.0

        return value

    def joystick_callback(self, msg):
        """Convert joystick inputs into four motor speed commands."""
        if len(msg.axes) < 2:
            self.get_logger().warning(
                'Joystick message contains fewer than 2 axes.'
            )
            return

        x = -msg.axes[0]
        y = msg.axes[1]

        x = self.apply_deadzone(x)
        y = self.apply_deadzone(y)

        left_speed = y + x
        right_speed = y - x

        left_speed = max(-1.0, min(1.0, left_speed))
        right_speed = max(-1.0, min(1.0, right_speed))

        # Order: [Front Left, Front Right, Back Left, Back Right]
        motor_speeds = [
            left_speed,
            right_speed,
            left_speed,
            right_speed,
        ]

        # Publish the motor speeds.
        output = Float32MultiArray()
        output.data = motor_speeds
        self.publisher.publish(output)

    def stop_motors(self):
        """Publish zero speeds to all four motors."""
        output = Float32MultiArray()
        output.data = [0.0, 0.0, 0.0, 0.0]
        self.publisher.publish(output)


def main(args=None):
    rclpy.init(args=args)
    node = JoystickMotor()

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
