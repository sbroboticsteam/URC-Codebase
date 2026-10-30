import time
import unittest

import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
import launch_testing.asserts
import pytest
from rcl_interfaces.srv import GetParameters
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Joy


def get_node_deadzone(node, timeout=5.0):
    """Ask the running joystick_motor node for its deadzone."""
    client = node.create_client(
        GetParameters, '/joystick_motor/get_parameters')
    if not client.wait_for_service(timeout_sec=timeout):
        raise RuntimeError('joystick_motor parameter service not available')
    req = GetParameters.Request()
    req.names = ['deadzone']
    future = client.call_async(req)
    rclpy.spin_until_future_complete(node, future, timeout_sec=timeout)
    return future.result().values[0].double_value


@pytest.mark.launch_test
def generate_test_description():
    return (
        launch.LaunchDescription([
            launch_ros.actions.Node(
                package='joy', executable='joy_node', name='joy_node',
                parameters=[{'device_id': 0,
                             'deadzone': 0.0,
                             'autorepeat_rate': 20.0}],
            ),
            launch_ros.actions.Node(
                package='robot',
                executable='joy_mirror',
                name='joystick_motor',
                parameters=[{'deadzone': 0.5}],
            ),
            launch.actions.TimerAction(
                period=1.0, actions=[launch_testing.actions.ReadyToTest()]),
        ]),
        {},
    )


# Active tests
class TestJoy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.shutdown()

    def setUp(self):
        self.node = rclpy.create_node('test_joystick_mirror')
        self.deadzone = get_node_deadzone(self.node)

    def tearDown(self):
        self.node.destroy_node()

    def test_publishes_joy(self, proc_output):
        """Check whether joy messages are published."""
        msgs_rx = []
        sub = self.node.create_subscription(
            Joy, 'joy',
            lambda msg: msgs_rx.append(msg), qos_profile_sensor_data)
        try:
            # Listen to the joy topic for 10 s
            end_time = time.time() + 10
            while time.time() < end_time:
                # spin to get subscriber callback executed
                rclpy.spin_once(self.node, timeout_sec=10)
            # At 20 Hz there should have been ~200 messages; 100 leaves margin
            assert len(msgs_rx) > 100, (
                f'Only {len(msgs_rx)} /joy messages received. '
                'Is the controller connected?')
        finally:
            self.node.destroy_subscription(sub)

    def test_joy_message_contents(self, proc_output):
        """Check whether joy messages have valid axes and buttons."""
        msgs_rx = []
        sub = self.node.create_subscription(
            Joy, 'joy',
            lambda msg: msgs_rx.append(msg), qos_profile_sensor_data)
        try:
            # Listen to the joy topic for 3 s
            end_time = time.time() + 3
            while time.time() < end_time:
                rclpy.spin_once(self.node, timeout_sec=1)
            assert len(msgs_rx) > 0, 'No /joy messages received'
            for msg in msgs_rx:
                assert len(msg.axes) > 0
                assert len(msg.buttons) > 0
                assert all(-1.0 <= a <= 1.0 for a in msg.axes)
                assert all(b in (0, 1) for b in msg.buttons)
        finally:
            self.node.destroy_subscription(sub)

    def test_logs_opened_joystick(self, proc_output):
        """Check that joy_node logs the opened joystick."""
        proc_output.assertWaitFor(
            'Opened joystick',
            timeout=5, stream='stderr')

    def test_interactive_physical_stick_response(self, proc_output):
        """Interactive test: prompts the user to move the physical controller."""
        msgs_rx = []
        sub = self.node.create_subscription(
            Joy, 'joy',
            lambda msg: msgs_rx.append(msg), qos_profile_sensor_data
        )

        print('\n' + '=' * 50)
        print(' [HIL TEST] Please push the Left Joystick FULLY FORWARD.')
        print('=' * 50 + '\n')
        BTN_A = 0
        BTN_B = 1
        BTN_X = 2
        BTN_Y = 3
        BTN_BACK = 6
        BTN_GUIDE = 8
        BTN_START = 7
        BTN_LB = 4
        BTN_RB = 5
        BTN_L1 = 9
        BTN_R1 = 10
        BTN_SHARE = 11  # Series X only
        try:
            # Give the user 30 seconds to press everything
            end_time = time.time() + 90.0
            forward_detected = False
            abutton_detected = False
            bbutton_detected = False
            xbutton_detected = False
            ybutton_detected = False
            backbutton_detected = False
            guidebutton_detected = False
            startbutton_detected = False
            l1button_detected = False
            r1button_detected = False
            lbbutton_detected = False
            rbbutton_detected = False
            # dpadupbutton_detected = False
            # dpaddownbutton_detected = False
            # dpadleftbutton_detected = False
            # dpadrightbutton_detected = False
            sharebutton_detected = False
            confirmed = 0
            total = 12  # 1 stick + 16 buttons

            while time.time() < end_time and confirmed < total:
                rclpy.spin_once(self.node, timeout_sec=0.1)
                if msgs_rx:
                    latest_msg = msgs_rx[-1]
                    buttons = latest_msg.buttons

                    # Check if axis 1 (y-axis) shows significant movement
                    if (len(latest_msg.axes) > 1
                            and abs(latest_msg.axes[1]) > 0.7):
                        if not forward_detected:
                            confirmed += 1
                            print('Left stick', flush=True)
                        forward_detected = True

                    if len(buttons) > BTN_A and buttons[BTN_A] == 1:
                        if not abutton_detected:
                            confirmed += 1
                            print('A', flush=True)
                        abutton_detected = True

                    if len(buttons) > BTN_B and buttons[BTN_B] == 1:
                        if not bbutton_detected:
                            confirmed += 1
                            print('B', flush=True)
                        bbutton_detected = True

                    if len(buttons) > BTN_X and buttons[BTN_X] == 1:
                        if not xbutton_detected:
                            confirmed += 1
                            print('X', flush=True)
                        xbutton_detected = True

                    if len(buttons) > BTN_Y and buttons[BTN_Y] == 1:
                        if not ybutton_detected:
                            confirmed += 1
                            print('Y', flush=True)
                        ybutton_detected = True

                    if len(buttons) > BTN_BACK and buttons[BTN_BACK] == 1:
                        if not backbutton_detected:
                            confirmed += 1
                            print('Back', flush=True)
                        backbutton_detected = True

                    if len(buttons) > BTN_GUIDE and buttons[BTN_GUIDE] == 1:
                        if not guidebutton_detected:
                            confirmed += 1
                            print('Guide', flush=True)
                        guidebutton_detected = True

                    if len(buttons) > BTN_START and buttons[BTN_START] == 1:
                        if not startbutton_detected:
                            confirmed += 1
                            print('Start', flush=True)
                        startbutton_detected = True

                    if len(buttons) > BTN_L1 and buttons[BTN_L1] == 1:
                        if not l1button_detected:
                            confirmed += 1
                            print('L1', flush=True)
                        l1button_detected = True

                    if len(buttons) > BTN_R1 and buttons[BTN_R1] == 1:
                        if not r1button_detected:
                            confirmed += 1
                            print('R1', flush=True)
                        r1button_detected = True

                    # if (len(buttons) > BTN_LEFT_STICK
                    #         and buttons[BTN_LEFT_STICK] == 1):
                    #     if not leftstickbutton_detected:
                    #         confirmed += 1
                    #         print('Left stick click', flush=True)
                    #     leftstickbutton_detected = True

                    # # if (len(buttons) > BTN_RIGHT_STICK
                    # #         and buttons[BTN_RIGHT_STICK] == 1):
                    # #     if not rightstickbutton_detected:
                    # #         confirmed += 1
                    # #         print('Right stick click', flush=True)
                    # #     rightstickbutton_detected = True

                    if len(buttons) > BTN_LB and buttons[BTN_LB] == 1:
                        if not lbbutton_detected:
                            confirmed += 1
                            print('LB', flush=True)
                        lbbutton_detected = True

                    if len(buttons) > BTN_RB and buttons[BTN_RB] == 1:
                        if not rbbutton_detected:
                            confirmed += 1
                            print('RB', flush=True)
                        rbbutton_detected = True
                    
                    if len(buttons) > BTN_SHARE and buttons[BTN_SHARE] == 1:
                        if not sharebutton_detected:
                            confirmed += 1
                            print('Share', flush=True)
                        sharebutton_detected = True

                    # # if len(buttons) > BTN_DPAD_UP and buttons[BTN_DPAD_UP] == 1:
                    # #     if not dpadupbutton_detected:
                    # #         confirmed += 1
                    # #         print('D-pad up', flush=True)
                    # #     dpadupbutton_detected = True

                    # # if (len(buttons) > BTN_DPAD_DOWN
                    # #         and buttons[BTN_DPAD_DOWN] == 1):
                    # #     if not dpaddownbutton_detected:
                    # #         confirmed += 1
                    # #         print('D-pad down', flush=True)
                    # #     dpaddownbutton_detected = True

                    # # if (len(buttons) > BTN_DPAD_LEFT
                    # #         and buttons[BTN_DPAD_LEFT] == 1):
                    # #     if not dpadleftbutton_detected:
                    # #         confirmed += 1
                    # #         print('D-pad left', flush=True)
                    # #     dpadleftbutton_detected = True

                    # # if (len(buttons) > BTN_DPAD_RIGHT
                    # #         and buttons[BTN_DPAD_RIGHT] == 1):
                    # #     if not dpadrightbutton_detected:
                    # #         confirmed += 1
                    # #         print('D-pad right', flush=True)
                    # #     dpadrightbutton_detected = True


            assert confirmed == total, (
                f'Only {confirmed}/{total} inputs detected. '
                'Press every button and push the left stick forward.'
            )
        finally:
            self.node.destroy_subscription(sub)


@launch_testing.post_shutdown_test()
class TestJoyShutdown(unittest.TestCase):
    def test_exit_codes(self, proc_info):
        """Check if the processes exited normally."""
        launch_testing.asserts.assertExitCodes(
            proc_info,
            allowable_exit_codes=[
                launch_testing.asserts.EXIT_OK,
                launch_testing.asserts.EXIT_SIGINT,
            ])
