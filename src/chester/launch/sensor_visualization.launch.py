import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # Create a node to convert the camera image to a ROS image message
    image_transport_cmd = Node(
        package='image_transport',
        executable='republish',
        name='image_republisher',
        arguments=['raw', 'in:=/camera/image_raw', 'out:=/camera/image'],
        remappings=[
            ('/camera/image_raw', '/camera/image_raw'),
            ('/camera/image', '/camera/image')
        ],
        output='screen'
    )
    
    # Create a node to process the LiDAR data (for visualization in RViz)
    scan_processor_cmd = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_pub_laser',
        arguments=['0', '0', '0', '0', '0', '0', 'base_footprint', 'base_scan'],
        output='screen'
    )
    
    # Return the launch description
    return LaunchDescription([
        image_transport_cmd,
        scan_processor_cmd,
    ])