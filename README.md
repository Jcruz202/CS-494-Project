# CS-494-Project
A human following robot named Chester using ROS and Python.

Python packages to install:
```
pip install ultralytics transforms3d opencv-python numpy pandas
```

How to Build Code
Make sure you have installed all the Turtlebot 3 packages

At the project root:
```
export TURTLEBOT3_MODEL=waffle_pi
source /opt/ros/foxy.setup.bash
colcon build
source install/setup.bash
ros2 launch chester tb4_image_saver.launch.py
ros2 run turtlebot3_teleop teleop_keyboard
```

Node Image_Saver will publish to chester/human_position