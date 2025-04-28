import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node

def generate_launch_description():
    # Get the launch directory
    chester_dir = get_package_share_directory('chester')
    
    # Get the TURTLEBOT3_MODEL environment variable
    turtlebot3_model = os.environ.get('TURTLEBOT3_MODEL', 'waffle')  # Default to waffle if not set
    
    # Launch configuration variables
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    x_pose = LaunchConfiguration('x_pose', default='0.0')
    y_pose = LaunchConfiguration('y_pose', default='0.0')
    
    # Declare the launch arguments
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true')
    
    declare_x_pose_cmd = DeclareLaunchArgument(
        'x_pose', default_value='0.0',
        description='Initial x-position of the robot')
    
    declare_y_pose_cmd = DeclareLaunchArgument(
        'y_pose', default_value='0.0',
        description='Initial y-position of the robot')
    
    # Get URDF via the xacro command
    urdf_file = os.path.join(
        get_package_share_directory('turtlebot3_description'),
        'urdf', f'turtlebot3_{turtlebot3_model}.urdf')
    
    # Create the robot state publisher node
    start_robot_state_publisher_cmd = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time,
                    'robot_description': Command(['xacro ', urdf_file])}])
    
    # Spawn the robot in Gazebo
    start_gazebo_spawner_cmd = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'turtlebot3',
            '-x', x_pose,
            '-y', y_pose,
            '-z', '0.01',
            '-file', urdf_file],
        output='screen')
    
    # Start a node to publish LiDAR scan visualization
    start_rviz_cmd = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', os.path.join(get_package_share_directory('turtlebot3_gazebo'), 'rviz', 'tb3_gazebo.rviz')],
        output='screen'
    )
    
    # Create the launch description and populate
    ld = LaunchDescription()
    
    # Add the commands to the launch description
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_x_pose_cmd)
    ld.add_action(declare_y_pose_cmd)
    ld.add_action(start_robot_state_publisher_cmd)
    ld.add_action(start_gazebo_spawner_cmd)
    ld.add_action(start_rviz_cmd)  # Added RViz to visualize sensor data
    
    return ld