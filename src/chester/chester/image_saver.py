#!/usr/bin/env python3
import os
import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from datetime import datetime

class ImageSaver(Node):
    def __init__(self):
        super().__init__('image_saver')
        # declare & read params
        self.declare_parameter('image_topic', '/camera/color/image_raw')
        self.declare_parameter('output_dir', os.path.expanduser('~/gazebo_images'))
        self.declare_parameter('save_rate_hz', 1.0)

        p = self.get_parameters(['image_topic', 'output_dir', 'save_rate_hz'])
        self.topic      = p[0].value
        self.output_dir = p[1].value
        self.save_rate  = p[2].value

        os.makedirs(self.output_dir, exist_ok=True)
        self.bridge    = CvBridge()
        self.last_save = self.get_clock().now()

        self.create_subscription(Image, self.topic, self.cb, 10)
        self.get_logger().info(f'Listening to {self.topic}, saving @ {self.save_rate}Hz → {self.output_dir}')

    def cb(self, msg: Image):
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
