import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    # Get the turtlebot3_gazebo package directory
    turtlebot3_gazebo_dir = get_package_share_directory('turtlebot3_gazebo')
    
    # Use the turtlebot3_world launch file
    turtlebot3_world_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(turtlebot3_gazebo_dir, 'launch', 'turtlebot3_house.launch.py')
        ]),
    )
    
    # Instead of using the Gazebo ROS API plugin, we'll use a command to spawn a model
    # This uses the spawn_entity service which is already provided by the standard Gazebo launch
#     spawn_person = ExecuteProcess(
#     cmd=['ros2', 'service', 'call', '/spawn_entity', 'gazebo_msgs/srv/SpawnEntity', 
#          '{ name: "walking_person", xml: "<?xml version=\'1.0\'?><sdf version=\'1.6\'>' +
#          '<include><uri>model://person_standing</uri>' +
#          '<pose>2.0 2.0 0.0 0 0 0</pose>' +
#          '<name>human_actor</name></include></sdf>", ' +
#          'robot_namespace: "", initial_pose: { position: { x: -1.0, y: 1.5, z: 0.0 } } }'],
#     output='screen'
# )
    
    # Run human follower node
    # human_follower_node = Node(
    #     package='chester',
    #     executable='move_chester.py',
    #     name='human_follower',
    #     output='screen'
    # )

    human_detection_node = Node(
            package='chester',
            executable='image_saver.py',  # This should match the script name
            name='image_saver',
            output='screen',
            parameters=[{
                'image_topic': '/camera/image_raw',
                'camera_info_topic': '/camera/camera_info',
                'output_dir': os.path.expanduser('~/gazebo_images'),
                'save_rate_hz': 1.0
            }]
        )
    
    # Run position logger node
    chester_logger_node = Node(
        package='chester',
        executable='chester_logger.py',
        name='chester_logger',
        output='screen'
    )
    
    # Return the launch description
    return LaunchDescription([
        turtlebot3_world_launch,
        # spawn_person,
        human_detection_node,
        # human_follower_node,
        chester_logger_node
    ])