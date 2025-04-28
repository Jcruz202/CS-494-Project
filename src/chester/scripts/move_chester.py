#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from chester.msg import HumanPos
import math


class HumanFollower(Node):
    def __init__(self):
        super().__init__('human_follower')
        
        # Parameters
        self.target_distance = 2.0  # Target distance to maintain (meters)
        self.distance_tolerance = 0.1  # Tolerance range for distance (meters)
        self.min_confidence = 0.5  # Minimum confidence to consider a human detection valid
        
        # Control parameters
        self.linear_speed = 0.2  # Maximum linear speed (m/s)
        self.angular_speed = 0.5  # Maximum angular speed (rad/s)
        self.k_linear = 0.3  # Linear speed proportional gain
        self.k_angular = 0.5  # Angular speed proportional gain
        
        # State variables
        self.current_distance = None
        self.current_x = None
        self.current_y = None
        self.detection_confidence = 0.0
        self.last_detection_time = self.get_clock().now()
        self.detection_timeout = 2.0  # Seconds before considering detection lost
        
        # Create subscribers
        self.human_pos_sub = self.create_subscription(
            HumanPos, 
            'chester/human_position', 
            self.human_pos_callback, 
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
            
        return True
    
    def update_movement(self):
        """Update robot velocity based on human position."""
        cmd_vel = Twist()
        
        # Default state - don't move
        cmd_vel.linear.x = 0.0
        cmd_vel.angular.z = 0.0
        
        if not self.is_detection_valid():
            self.get_logger().warn('No valid human detection, stopping')
            self.cmd_vel_pub.publish(cmd_vel)
            return
        
        # Calculate distance error
        distance_error = self.current_distance - self.target_distance
        
        # For now, keep the robot stationary as requested
        # But include the control logic for future use
        
        # Uncomment these when ready to enable movement
        '''
        # Adjust linear velocity to maintain distance
        if abs(distance_error) > self.distance_tolerance:
            # Only move if error is outside tolerance
            cmd_vel.linear.x = self.k_linear * distance_error
            
            # Limit speed
            cmd_vel.linear.x = max(-self.linear_speed, min(cmd_vel.linear.x, self.linear_speed))
        
        # Adjust angular velocity to face the human
        # Calculate angle to human in robot frame
        angle_to_human = math.atan2(self.current_y, self.current_x)
        
        # Adjust angular velocity to face the human
        cmd_vel.angular.z = self.k_angular * angle_to_human
        
        # Limit angular speed
        cmd_vel.angular.z = max(-self.angular_speed, min(cmd_vel.angular.z, self.angular_speed))
        '''
        
        self.get_logger().info(
            f'Distance: {self.current_distance:.2f}m, Error: {distance_error:.2f}m, '
            f'Cmd: linear={cmd_vel.linear.x:.2f}, angular={cmd_vel.angular.z:.2f}'
        )
        
        # Publish velocity command
        self.cmd_vel_pub.publish(cmd_vel)


def main(args=None):
    rclpy.init(args=args)
    node = HumanFollower()
    
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