#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from chester.msg import HumanPos
from sensor_msgs.msg import LaserScan
import math
import numpy as np


class HumanFollower(Node):
    def __init__(self):
        super().__init__('human_follower')
        
        # Parameters
        self.target_distance = 1.0  # Target distance to maintain (meters)
        self.distance_tolerance = 0.1  # Tolerance range for distance (meters)
        self.min_confidence = 0.4  # Minimum confidence to consider a human detection valid
        self.obstacle_distance_threshold = 1.0 # Minimum distance to obstacles (meters)
        
        # Control parameters
        self.linear_speed = 0.1  # Maximum linear speed (m/s)
        self.angular_speed = 0.25  # Maximum angular speed (rad/s)
        self.k_linear = 0.15  # Linear speed proportional gain
        self.k_angular = 0.25  # Angular speed proportional gain
        self.k_obstacle = 1.0  # Obstacle avoidance gain
        
        # State variables
        self.current_distance = None
        self.current_x = None
        self.current_y = None
        self.detection_confidence = 0.0
        self.last_detection_time = self.get_clock().now()
        self.detection_timeout = 5.0  # Seconds before considering detection lost
        self.laser_scan = None
        
        # Memory for last valid position
        self.last_valid_x = None
        self.last_valid_y = None
        self.last_valid_distance = None
        self.position_memory_timeout = 10.0  # Seconds to remember last valid position
        
        # Create subscribers
        self.human_pos_sub = self.create_subscription(
            HumanPos, 
            'chester/human_position', 
            self.human_pos_callback, 
            10
        )
        
        # Subscribe to laser scan data
        self.laser_scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.laser_scan_callback,
            10
        )
        
        # Create publishers
        self.cmd_vel_pub = self.create_publisher(
            Twist, 
            'cmd_vel', 
            10
        )
        
        # Create a timer to update movement
        self.timer = self.create_timer(0.1, self.update_movement)
        
        self.get_logger().info('Human follower node initialized')
    
    def human_pos_callback(self, msg):
        self.current_distance = msg.distance
        self.current_x = msg.x
        self.current_y = msg.y
        self.detection_confidence = msg.confidence
        self.last_detection_time = self.get_clock().now()
        
        self.get_logger().info(
            f'Human detected: distance={self.current_distance:.2f}m, '
            f'position=({self.current_x:.2f}, {self.current_y:.2f}), '
            f'confidence={self.detection_confidence:.2f}'
        )
    
    def laser_scan_callback(self, msg):
        """Process laser scan data."""
        self.laser_scan = msg
    
    def is_detection_valid(self):
        """Check if the current human detection is valid and recent."""
        if self.current_distance is None:
            return False
            
        now = self.get_clock().now()
        elapsed = (now - self.last_detection_time).nanoseconds * 1e-9
        
        if elapsed > self.detection_timeout:
            self.get_logger().warn(f'Human detection timeout ({elapsed:.2f}s)')
            return False
            
        if self.detection_confidence < self.min_confidence:
            self.get_logger().warn(f'Low confidence detection: {self.detection_confidence:.2f}')
            return False
        
        # Store last valid position whenever we have a good detection
        self.last_valid_x = self.current_x
        self.last_valid_y = self.current_y
        self.last_valid_distance = self.current_distance
        
        return True
    
    def should_use_memory(self):
        """Check if we should use the last valid position."""
        if self.last_valid_x is None:
            return False
            
        now = self.get_clock().now()
        elapsed = (now - self.last_detection_time).nanoseconds * 1e-9
        
        # Use memory if we have a recent valid detection but current detection is invalid
        return (elapsed < self.position_memory_timeout)
    
    def normalize_angle(self, angle):
        """Normalize angle to -pi to pi."""
        # Handle both scalar and numpy array inputs
        if isinstance(angle, np.ndarray):
            return np.mod(angle + np.pi, 2 * np.pi) - np.pi
        else:
            # Original scalar implementation
            while angle > math.pi:
                angle -= 2.0 * math.pi
            while angle < -math.pi:
                angle += 2.0 * math.pi
            return angle
    
    def detect_obstacles(self):
        """Analyze laser scan data to detect obstacles."""
        if self.laser_scan is None:
            return None, None
            
        # Get the angle of the human from the robot's perspective
        if self.current_x is not None and self.current_y is not None:
            human_angle = math.atan2(self.current_y, self.current_x)
        elif self.last_valid_x is not None and self.last_valid_y is not None:
            human_angle = math.atan2(self.last_valid_y, self.last_valid_x)
        else:
            return None, None
            
        ranges = np.array(self.laser_scan.ranges)
        
        # Convert NaN and inf values to the max range
        mask = np.logical_or(np.isnan(ranges), np.isinf(ranges))
        ranges[mask] = self.laser_scan.range_max
        
        # Identify points that are closer than the threshold
        obstacle_mask = ranges < self.obstacle_distance_threshold
        
        if not np.any(obstacle_mask):
            # No obstacles detected
            return None, None
            
        # Calculate the angle for each obstacle point
        angle_min = self.laser_scan.angle_min
        angle_increment = self.laser_scan.angle_increment
        angles = np.array([angle_min + i * angle_increment for i in range(len(ranges))])
        
        # Calculate the angular width around the human to exclude from obstacle detection
        # (we don't want to avoid the human we're following)
        human_angle_width = math.atan2(0.5, self.current_distance) if self.current_distance else 0.5  # Assume human width of 0.5m
        
        # Create a mask for points that are not in the human's direction
        # Use vectorized operations for numpy arrays
        human_angle_diff = np.abs(self.normalize_angle(angles - human_angle))
        not_human_mask = human_angle_diff > human_angle_width
        
        # Combine masks to get obstacles that are not the human
        obstacle_mask = np.logical_and(obstacle_mask, not_human_mask)
        
        if not np.any(obstacle_mask):
            # No obstacles detected outside the human
            return None, None
        
        # Find the closest obstacle
        obstacle_ranges = ranges[obstacle_mask]
        min_dist_idx = np.argmin(obstacle_ranges)
        obstacle_angles = angles[obstacle_mask]
        closest_obstacle_angle = obstacle_angles[min_dist_idx]
        closest_obstacle_dist = obstacle_ranges[min_dist_idx]
        
        # Calculate the repulsive vector from the closest obstacle
        # Direction is opposite to the obstacle direction
        repulsive_angle = self.normalize_angle(closest_obstacle_angle + math.pi)
        repulsive_magnitude = self.k_obstacle * (1.0 - closest_obstacle_dist / self.obstacle_distance_threshold)
        
        return repulsive_angle, repulsive_magnitude
    
    def update_movement(self):
        """Update robot velocity based on human position and obstacle avoidance."""
        cmd_vel = Twist()
        
        # Default state - don't move
        cmd_vel.linear.x = 0.0
        cmd_vel.angular.z = 0.0
        
        # Check for valid detection
        valid_detection = self.is_detection_valid()
        
        # If no valid detection, check if we can use memory
        if not valid_detection:
            self.get_logger().warn('No valid human detection, stopping')
            self.cmd_vel_pub.publish(cmd_vel)
            return
        else:
            # Use current position
            x_pos = self.current_x
            y_pos = self.current_y
            distance = self.current_distance
        
        # Calculate distance error
        distance_error = distance - self.target_distance
        
        # Adjust linear velocity to maintain distance
        if abs(distance_error) > self.distance_tolerance:
            # Only move if error is outside tolerance
            cmd_vel.linear.x = self.k_linear * distance_error
            
            # Limit speed
            cmd_vel.linear.x = max(-self.linear_speed, min(cmd_vel.linear.x, self.linear_speed))
        
        # Calculate angle to human in robot frame
        angle_to_human = math.atan2(y_pos, x_pos)
        
        # Adjust angular velocity to face the human
        cmd_vel.angular.z = self.k_angular * angle_to_human
        
        # Check for obstacles and adjust if necessary
        repulsive_angle, repulsive_magnitude = self.detect_obstacles()
        
        if repulsive_angle is not None and repulsive_magnitude is not None:
            # Apply repulsive force to velocity commands
            # For angular velocity, we want to turn away from the obstacle
            obstacle_angle = self.normalize_angle(repulsive_angle - math.pi/2)  # 90 degrees from repulsive direction
            cmd_vel.angular.z += repulsive_magnitude * math.sin(obstacle_angle)
            
            # For linear velocity, we want to prioritize obstacle avoidance
            if repulsive_magnitude > 0.5:  # If obstacle is very close
                # Reduce forward speed or even move backward if needed
                cmd_vel.linear.x = min(cmd_vel.linear.x, -0.1)  # Move backwards
                
                self.get_logger().warn(
                    f'Obstacle detected! Distance: {self.obstacle_distance_threshold - repulsive_magnitude/self.k_obstacle:.2f}m, '
                    f'Angle: {math.degrees(self.normalize_angle(repulsive_angle - math.pi)):.1f}°'
                )
            else:
                # Just reduce speed
                cmd_vel.linear.x *= (1.0 - repulsive_magnitude)
        
        # Limit angular speed
        cmd_vel.angular.z = max(-self.angular_speed, min(cmd_vel.angular.z, self.angular_speed))
        
        self.get_logger().info(
            f'Distance: {distance:.2f}m, Error: {distance_error:.2f}m, '
            f'Position: ({x_pos:.2f}, {y_pos:.2f}), '
            f'Cmd: linear={cmd_vel.linear.x:.2f}, angular={cmd_vel.angular.z:.2f}'
        )
        
        # Publish velocity command
        self.cmd_vel_pub.publish(cmd_vel)


def main(args=None):
    rclpy.init(args=args)
    node = HumanFollower()
    
    # Print startup info
    node.get_logger().info(f"Human follower initialized with:")
    node.get_logger().info(f"- Target distance: {node.target_distance} meters")
    node.get_logger().info(f"- Min confidence: {node.min_confidence}")
    node.get_logger().info(f"- Detection timeout: {node.detection_timeout} seconds")
    node.get_logger().info(f"- Position memory timeout: {node.position_memory_timeout} seconds")
    node.get_logger().info(f"- Obstacle distance threshold: {node.obstacle_distance_threshold} meters")
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Stop the robot before shutting down
        cmd_vel = Twist()
        node.cmd_vel_pub.publish(cmd_vel)
        node.get_logger().info('Stopping robot and shutting down')
        
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()