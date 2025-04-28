import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess

def generate_launch_description():
    # Try to use a standard Gazebo model for a person standing
    actor_spawn_cmd = ExecuteProcess(
        cmd=['ros2', 'service', 'call', '/spawn_entity', 'gazebo_msgs/SpawnEntity', 
             '{ name: "actor", xml: "<?xml version=\'1.0\'?><sdf version=\'1.6\'><include><uri>model://person_standing</uri><pose>2 2 0 0 0 0</pose><name>walking_person</name></include></sdf>" }'],
        output='screen'
    )
    
    return LaunchDescription([
        actor_spawn_cmd,
    ])