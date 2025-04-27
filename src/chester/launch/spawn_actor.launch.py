import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess

def generate_launch_description():
    # Spawn a simple actor model
    actor_spawn_cmd = ExecuteProcess(
        cmd=['ros2', 'service', 'call', '/spawn_entity', 'gazebo_msgs/SpawnEntity', 
             '{ name: "actor", xml: "<?xml version=\'1.0\'?><sdf version=\'1.6\'><model name=\'actor\'><pose>2 2 0 0 0 0</pose><static>true</static><link name=\'link\'><visual name=\'visual\'><geometry><box><size>0.5 0.5 1.5</size></box></geometry><material><ambient>0 0 1 1</ambient><diffuse>0 0 1 1</diffuse></material></visual><collision name=\'collision\'><geometry><box><size>0.5 0.5 1.5</size></box></geometry></collision></link></model></sdf>" }'],
        output='screen'
    )
    
    return LaunchDescription([
        actor_spawn_cmd,
    ])