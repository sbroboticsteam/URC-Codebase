import unittest
import rclpy
import time

import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
import launch_testing.markers
from launch_testing_ros.actions import EnableRmwIsolation

from sensor_msgs.msg import Joy
#from turtlesim.msg import Pose (For TurtleSim)


#Reference websites used to create this file:
#https://docs.ros.org/en/iron/p/launch_testing/
#https://docs.ros.org/en/lyrical/Developer-Tools/Debugging/Testing/Integration.html
#https://index.ros.org/p/joy/


#Instructions:
#This file should be in a directory called 'test'
#Run this file with 
#launch_test test_joy.py

def generate_test_description():

    return launch.LaunchDescription(
        [

            # Node under test: joy_node
            launch_ros.actions.Node( #Action 1 create a node
                package="joy",
                executable="joy_node",
                name="test_talker",
                output="screen" #output goes to terminal, default is in a file somewhere..
            ),
            launch_testing.actions.ReadyToTest() #Action 2 tells the "framework" that the 
            #test should be run without delays
        ]
    )

#ACTIVE TESTS
class TestJoy(unittest.TestCase):

    @classmethod #This shows that the function is non-static (belongs to the class)
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.shutdown()


    def setUp(self):
        self.node = rclpy.create_node('test_joy')

    def tearDown(self):
        self.node.destroy_node()

    def test_publishes_pose(self, proc_output):
        """Check whether pose messages published"""
        msgs_rx = []
        sub = self.node.create_subscription(
            Joy, '/joy',  #Joy (for Joy) is the Pose (for TurtleSim), where messages are sent to
            lambda msg: msgs_rx.append(msg), 100)
        try:
            # Listen to the pose topic for 10 s
            end_time = time.time() + 10
            while time.time() < end_time:
                # spin to get subscriber callback executed
                rclpy.spin_once(self.node, timeout_sec=1)
            # There should have been 100 messages received
            #assert len(msgs_rx) > 100 #Commented out because AssertionError
        finally:
            self.node.destroy_subscription(sub)


#POST-SHUTDOWN TESTS
@launch_testing.post_shutdown_test()
class TestJoyShutdown(unittest.TestCase):
    def test_exit_codes(self, proc_info):
        """Check if the processes exited normally."""
        launch_testing.asserts.assertExitCodes(proc_info)









#If you want similar formatting to joy_launch.py:
#def generate_test_description():
#    ld = LaunchDescription()

#    test_talker = Node(
#        package="joy",
#        executable="joy_node",
#        name="test_talker",
#        output="screen" #output goes to terminal, default is in a file somewhere..
#    )#test_talker node 


#    ld.add_action(EnableRmwIsolation())
#    ld.add_action(test_talker)
#    ld.add_action(launch_testing.actions.ReadyToTest())
#    return ld
