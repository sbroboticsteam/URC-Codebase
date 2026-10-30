import os
from launch import LaunchDescription
from launch_ros.actions import Node

#ros2 launch joy_launch.py
#do not run it using python3

#source /opt/ros/lyrical/setup.bash
#cd ~/Desktop/"Robotics team"/launch     (or whereever the launch folder is)
#ros2 launch joy_launch.py

#then do ros2 topic echo /joy in another terminal

def generate_launch_description():
    ld = LaunchDescription()


    talker = Node(
        package = "joy",
        executable = "joy_node",
        name = "talker"
    ) #Node 1 (ros2 run joy joy_node)




    ld.add_action(talker)
    return ld
    #generate_launch_description returns a node talker