import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # Get the launch directory
    chester_dir = get_package_share_directory('chester')
    tb3_gazebo_dir = get_package_share_directory('turtlebot3_gazebo')
    
    # Include the empty world launch file (which also spawns TurtleBot3)
    empty_world_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(tb3_gazebo_dir, 'launch', 'empty_world.launch.py')
        )
    )
    
    # Delay actor spawn to ensure Gazebo is fully loaded
    actor_spawn_with_delay = TimerAction(
        period=3.0,  # 5 second delay
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(chester_dir, 'launch', 'spawn_actor.launch.py')
                )
            )
        ]
    )
    
    return LaunchDescription([
        empty_world_launch,
        actor_spawn_with_delay,
    ])