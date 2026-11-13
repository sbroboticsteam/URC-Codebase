# SBRT URC Codebase 2026-2027

## Description

This repository contains all of the software and research developed for our robotics platform. 

As the project evolves, additional documentation covering setup, architecture, hardware, and usage will be added.

## Camera classification session

The `robot` ROS 2 Python package provides a `classify_sequence_server` action server. A goal starts a session that subscribes to the configured camera image topic. Canceling the goal or reaching the no-frame timeout ends that session; the camera driver remains responsible for the camera stream.

Each complete sequence window is passed to the classifier hook. Valid classifications are published as `robot_interfaces/msg/Classification` messages, including the class label and the window's image-header start/end timestamps. If no valid classification is produced, no classification message is published. The action result reports whether the session produced a classification and includes the latest one when available.

The image topic, output topic, sequence length, maximum timestamp gap, no-frame timeout, and image queue depth are ROS parameters. Windows are non-overlapping groups of `sequence_length` frames; a timestamp gap or backwards timestamp discards a partial window. The classifier implementation is intentionally a placeholder until the team selects and integrates its model.

Build the packages from a ROS 2 Humble workspace with `colcon build`. The `robot_interfaces` package generates the action and message definitions; the `robot` package contains the Python server.

## Contributors

- Alexander Wiegand - Software Lead
