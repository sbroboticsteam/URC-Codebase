#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module Name: serial_send_node.py
Description: This node streams all data published to serial_send topic over serial connection.
"""
__author__ = "Farhaan Khan"


import rclpy
import serial
import time
from rclpy.node import Node

from std_msgs.msg import UInt8MultiArray


class SerialSendNode(Node):
    def __init__(self):
        super().__init__('serial_send_node')

        # Declare configurable params
        self.declare_parameter('baud_rate', 9600)
        self.declare_parameter('port', "/dev/ttyUSB0")
        self.declare_parameter('timeout', 0.1)

        port = self.get_parameter('port').get_parameter_value().string_value
        baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value
        timeout = self.get_parameter('timeout').get_parameter_value().double_value

        # Create subscriber 
        self.serial_subscription = self.create_subscription(UInt8MultiArray, 'serial_send', self.serial_send_callback, 10)
        self.serial_subscription # prevent unused var warning

        # Try to open serial port 
        self.get_logger().info(f"Opening serial port: {port} at {baudrate} baud...")
        try:
            self.Ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
            time.sleep(2) # Small delay 
            self.get_logger().info("Serial port opened successfully.")
        except serial.SerialException as e:
            self.get_logger().error(f"Failed to open serial port: {e}")
            raise e


    # Send the data published to topic over serial 
    def serial_send_callback(self, msg: UInt8MultiArray):
        try:
           if self.Ser.is_open:
                self.Ser.write(bytes(msg.data))
                self.get_logger().info(f"Sent over serial: {msg.data}")
            
        except serial.SerialException as e:
            self.get_logger().error(f"Error writing to serial: {e}")
            

def main(args=None):
    rclpy.init(args=args)
    serial_node = SerialSendNode()

    try:
        rclpy.spin(serial_node)
    except KeyboardInterrupt:
        pass
    finally:
        serial_node.destroy_node()
        rclpy.try_shutdown()

    
if __name__ == '__main__':
    main()