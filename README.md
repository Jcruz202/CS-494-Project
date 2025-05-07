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

Step 1: Run the Gazebo Simulation

```
export TURTLEBOT3_MODEL=waffle_pi
source /opt/ros/foxy/setup.bash
colcon build
source install/setup.bash
ros2 launch chester main.launch.py
```

You should see a gazebo window open now
1. In the gazebo window, you can move the objects around. We recommend moving the house simulation to the left to give the turtlebot more room. This is a good time to practice moving the model around.

2. Insert a human model from the gazebo window, there are many predefine human models that gazebo gives you. We use the standing_person in the demo.
3. Place the human in front of the turtlebot within the FOV.

Step 2: In a different terminal run:
```
export TURTLEBOT3_MODEL=waffle_pi
cd <into chester workspace>
source /opt/ros/foxy/setup.bash
colcon build
source install/setup.bash
ros2 run chester move_chester.py
```

4. move the human periodically (staying within the field of view)
Note: moving too fast will cause the turtlebot to lose view of the human.