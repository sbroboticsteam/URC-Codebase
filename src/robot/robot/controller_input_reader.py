#!/usr/bin/env python3
import glob
import os
import subprocess

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy


# 1) ls /dev/input/js*
def list_js_devices():
    devices = sorted(glob.glob("/dev/input/js*"))
    if not devices:
        print("No joystick devices found at /dev/input/js*")
    for d in devices:
        print(d)
    return devices


# 2) ros2 run joy joy_enumerate_devices
def enumerate_devices(devices):
    for dev in devices:
        js = os.path.basename(dev)  # e.g. js0
        name_file = f"/sys/class/input/{js}/device/name"
        try:
            with open(name_file) as f:
                name = f.read().strip()
        except OSError:
            name = "unknown"
        print(f"{dev}: {name}")


# 3) ros2 run joy joy_node
def start_joy_node():
    return subprocess.Popen(["ros2", "run", "joy", "joy_node"])


# 4) ros2 topic echo /joy
class JoyEcho(Node):
    def __init__(self):
        super().__init__("joy_echo")
        self.create_subscription(Joy, "/joy", self.callback, 10)

    def callback(self, msg: Joy):
        # Move cursor to top-left and clear the screen
        print("\033[H\033[J", end="")
        print(f"stamp: {msg.header.stamp.sec}.{msg.header.stamp.nanosec:09d}")
        print(f"frame_id: '{msg.header.frame_id}'")
        print(f"axes: {[round(a, 2) for a in msg.axes]}")
        print(f"buttons: {list(msg.buttons)}", flush=True)


def main():
    devices = list_js_devices()
    enumerate_devices(devices)

    joy_proc = start_joy_node()

    rclpy.init()
    node = JoyEcho()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        joy_proc.terminate()
        joy_proc.wait()


if __name__ == "__main__":
    main()
