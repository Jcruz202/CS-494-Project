import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # Use the empty world launch from turtlebot3_gazebo package
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('turtlebot3_gazebo'), 
                        'launch', 'empty_world.launch.py')
        ]),
    )
    
    return LaunchDescription([
        gazebo_launch,
    ])