#!/usr/bin/env python3
import os
import cv2

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan
from cv_bridge import CvBridge
from datetime import datetime

import math
import numpy as np

# ros2 topics we need for turtlebot 4
# /oakd/rgb/preview/camera_info     Intrinsics
# /oakd/rgb/preview/depth           
# /oakd/rgb/preview/depth/points    
# /oakd/rgb/preview/image_raw       RGB
# /scan

#ros2 topics we need for turtlebot 3
# /camera/camera_info
# /camera/image_raw
# /scan


class ImageSaver(Node):
    def __init__(self):
        super().__init__('chester')
        # save images parameters
        self.topic      = '/camera/image_raw'
        self.output_dir = os.path.expanduser('~/gazebo_images')
        self.save_rate  = 1.0

        os.makedirs(self.output_dir, exist_ok=True)
        self.bridge    = CvBridge()
        self.last_save = self.get_clock().now()
        
        # subscribe to the image raw topic and then post the starting logger message
        self.create_subscription(Image, self.topic, self.takePhoto, 10)
        self.get_logger().info(f'Listening to {self.topic}, saving @ {self.save_rate}Hz -> {self.output_dir}')

    def takePhoto(self, msg: Image):
        now = self.get_clock().now()
        elapsed = (now - self.last_save).nanoseconds * 1e-9
        if elapsed < 1.0/self.save_rate:
            return

        # convert & save
        cv_img = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        fn = os.path.join(self.output_dir, f'img_{ts}.jpg')
        cv2.imwrite(fn, cv_img)
        self.get_logger().info(f'Saved {fn}')
        self.last_save = now

def main(args=None):
    rclpy.init(args=args)
    node = ImageSaver()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
