from ament_index_python.packages import get_package_share_directory
import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    gz_pkg   = get_package_share_directory('turtlebot3_gazebo')
    gz_launch = os.path.join(gz_pkg, 'launch', 'turtlebot3_house.launch.py')

    return LaunchDescription([
        # 1) start Ignition Gazebo + sim-hardware nodes
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gz_launch),
            launch_arguments={'use_sim_time':'true'}.items()
        ),

        # 2) your image_saver node (same as before)
        Node(
            package='chester',
            executable='image_saver',
            name='image_saver',
            output='screen',
            parameters=[{
                'image_topic':     '/camera/image_raw',
                'camera_info_topic':'/camera/camera_info',
                'output_dir':      os.path.expanduser('~/gazebo_images'),
                'save_rate_hz':    1.0
            }]
        ),

        # 3) keyboard teleop so you can move the bot
        Node(
            package='teleop_twist_keyboard',
            executable='teleop_twist_keyboard',
            name='teleop_keyboard',
            output='screen',
            prefix='xterm -e',
            remappings=[('/cmd_vel','/cmd_vel')]
        ),
    ])
