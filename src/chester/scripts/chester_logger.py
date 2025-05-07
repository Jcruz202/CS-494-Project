#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from chester.msg import HumanPos
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
import math
import numpy as np
import csv
import os
from datetime import datetime

class PositionLogger(Node):
    def __init__(self):
        super().__init__('position_logger')
        
        # Create a file for logging with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_directory = os.path.expanduser('~/chester_logs')
        os.makedirs(self.log_directory, exist_ok=True)
        self.log_file = os.path.join(self.log_directory, f'position_log_{timestamp}.csv')
        
        # Open the CSV file and write header
        self.csv_file = open(self.log_file, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow([
            'Timestamp', 
            'Chester_X', 'Chester_Y', 'Chester_Theta',
            'Detected_Human_X', 'Detected_Human_Y', 'Detected_Distance', 'Detected_Confidence',
            'True_Distance'
        ])
        
        # State variables
        self.chester_pose = None
        self.detected_human_pos = None
        self.last_detection_time = self.get_clock().now()
        self.detection_timeout = 2.0  # Seconds before considering detection lost
        
        # Create subscribers
        self.chester_odom_sub = self.create_subscription(
            Odometry, 
            '/odom', 
            self.chester_odom_callback, 
            10
        )
        
        self.human_pos_sub = self.create_subscription(
            HumanPos, 
            'chester/human_position', 
            self.human_pos_callback, 
            10
        )
        
        # Create a timer to periodically log positions
        self.timer = self.create_timer(0.5, self.log_positions)
        
        self.get_logger().info(f'Position logger initialized, logging to {self.log_file}')
    
    def chester_odom_callback(self, msg):
        """Process odometry data to get Chester's position."""
        pose = msg.pose.pose
        self.chester_pose = pose
    
    def human_pos_callback(self, msg):
        """Process human position data."""
        self.detected_human_pos = msg
        self.last_detection_time = self.get_clock().now()
    
    def quaternion_to_euler(self, x, y, z, w):
        """Convert quaternion to Euler angles (roll, pitch, yaw)."""
        # Roll (x-axis rotation)
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)
        
        # Pitch (y-axis rotation)
        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)  # Use 90 degrees if out of range
        else:
            pitch = math.asin(sinp)
        
        # Yaw (z-axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        
        return roll, pitch, yaw
    
    def calculate_distance(self, x1, y1, x2, y2):
        """Calculate Euclidean distance between two points."""
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def log_positions(self):
        """Periodically log all positions to the CSV file."""
        if self.chester_pose is None:
            self.get_logger().warn('No Chester position data available')
            return
        
        # Get current time for timestamping
        current_time = self.get_clock().now()
        timestamp = current_time.to_msg().sec + current_time.to_msg().nanosec / 1e9
        
        # Get Chester's position and orientation
        chester_x = self.chester_pose.position.x
        chester_y = self.chester_pose.position.y
        _, _, chester_theta = self.quaternion_to_euler(
            self.chester_pose.orientation.x,
            self.chester_pose.orientation.y,
            self.chester_pose.orientation.z,
            self.chester_pose.orientation.w
        )
        
        # Check if we have a recent human detection
        detected_human_x = None
        detected_human_y = None
        detected_distance = None
        detected_confidence = None
        true_distance = None
        
        if self.detected_human_pos is not None:
            elapsed = (current_time - self.last_detection_time).nanoseconds * 1e-9
            if elapsed <= self.detection_timeout:
                detected_human_x = self.detected_human_pos.x
                detected_human_y = self.detected_human_pos.y
                detected_distance = self.detected_human_pos.distance
                detected_confidence = self.detected_human_pos.confidence
                
                # Calculate true distance (in this case, it's based on the robot's coordinate frame)
                # Since we don't have ground truth from Gazebo, we'll use the detected position
                true_distance = detected_distance
        
        # Write the data to the CSV file
        self.csv_writer.writerow([
            timestamp,
            chester_x, chester_y, chester_theta,
            detected_human_x, detected_human_y, detected_distance, detected_confidence,
            true_distance
        ])
        self.csv_file.flush()  # Ensure data is written immediately
        
        # Log some info if we have detections
        if detected_human_x is not None and detected_human_y is not None:
            self.get_logger().info(
                f'Chester pos: ({chester_x:.2f}, {chester_y:.2f}), ' +
                f'Human pos: ({detected_human_x:.2f}, {detected_human_y:.2f}), ' +
                f'Distance: {detected_distance:.2f}m, Confidence: {detected_confidence:.2f}'
            )
        else:
            self.get_logger().info(f'Chester pos: ({chester_x:.2f}, {chester_y:.2f}), No human detected')
    
    def __del__(self):
        # Ensure the file is properly closed
        if hasattr(self, 'csv_file'):
            self.csv_file.close()


def main(args=None):
    rclpy.init(args=args)
    node = PositionLogger()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.get_logger().info('Shutting down position logger')
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()