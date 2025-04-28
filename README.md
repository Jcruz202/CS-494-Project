# CS-494-Project
A human following robot named Chester using ROS and Python.

Python packages to install:
```
pip install ultralytics transforms3d opencv-python numpy pandas
```

How to Build Code
Make sure you have installed all the Turtlebot 3 packages

Node Image_Saver will publish to chester/human_position

At the project root:
```
export TURTLEBOT3_MODEL=waffle_pi
source /opt/ros/foxy/setup.bash
colcon build
source install/setup.bash
ros2 launch chester tb4_image_saver.launch.py
```

Step 1: Run the Gazebo Simulation
```
export TURTLEBOT3_MODEL=waffle_pi
source /opt/ros/foxy.setup.bash
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

Step 2: In a different terminal run:
```
cd <into chester workspace>
export TURTLEBOT3_MODEL=waffle_pi
source /opt/ros/foxy.setup.bash
colcon build
source install/setup.bash
ros2 run chester image_saver.py
```

Step 3: In a different terminal run:
```
export TURTLEBOT3_MODEL=waffle_pi
cd <into chester workspace>
source /opt/ros/foxy.setup.bash
colcon build
source install/setup.bash
ros2 run chester move_chester.py
```

Step 4:
Pray that the turtlebot is moving