#!/usr/bin/env python3
import os
import cv2
import math
import numpy as np

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan, CameraInfo
from cv_bridge import CvBridge
from datetime import datetime
from ultralytics import YOLO
from tf2_ros import Buffer, TransformListener

from chester.msg import HumanPos

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
        self.camera_topic = '/camera/image_raw'
        self.lidar_topic = '/scan'
        self.camerainfo_topic = '/camera/camera_info'
        self.output_dir = os.path.expanduser('~/gazebo_images')
        self.save_rate  = 1.0

        # YOLO parameters
        self.model = YOLO("yolov8n.pt")
        self.confidence_threshold = 0.5

        # Initalize CV_Bridge
        os.makedirs(self.output_dir, exist_ok=True)
        self.bridge    = CvBridge()
        self.last_save = self.get_clock().now()

        # parameters that get updated as the process goes on
        self.cameraMatrix = None
        self.dist_coeffs = None
        self.image_width = None
        self.image_height = None
        self.scan = None
        self.buffer = Buffer()
        self.tf_listener = TransformListener(self.buffer, self)
        
        # subscribe to the image raw topic and then post the starting logger message
        self.create_subscription(Image, self.camera_topic, self.captureView, 10)
        self.get_logger().info(f'Listening to {self.camera_topic}, saving @ {self.save_rate}Hz -> {self.output_dir}')
        #subscribe to camera info
        self.create_subscription(CameraInfo, self.camerainfo_topic, self.camerainfo_callback, 10)
        self.get_logger().info(f'Listening to {self.camerainfo_topic}, saving @ {self.save_rate}Hz -> {self.output_dir}')
        # subscribe to lidar
        self.create_subscription(LaserScan, self.lidar_topic, self.scan_callback, 10)
        self.get_logger().info(f'Listening to {self.lidar_topic}')

        #publish 
        self.pub = self.create_publisher(HumanPos, 'chester/human_position', 10)

    def camerainfo_callback(self, msg: CameraInfo):
        if self.cameraMatrix is None:
            self.cameraMatrix = np.array(msg.k).reshape(3,3)
            self.dist_coeffs = np.array(msg.d)
            self.image_width = msg.width
            self.image_height = msg.height
            self.get_logger().info('Camera parameters received')

    def scan_callback(self, msg:LaserScan):
        self.scan = msg


    def captureView(self, msg: Image):
        now = self.get_clock().now()
        elapsed = (now - self.last_save).nanoseconds * 1e-9
        if elapsed < 1.0/self.save_rate:
            return

        # convert & save what we see right in front of us
        try:
            cv_img = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            self.get_logger().warn(f'Error saving image {e}')
        
        ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        fn = os.path.join(self.output_dir, f'img_{ts}.jpg')
        cv2.imwrite(fn, cv_img)
        self.get_logger().info(f'Saved {fn}')

        if self.scan is None:
            self.get_logger().warn(f'No scan data yet')
            return
        
        if self.cameraMatrix is None:
            self.get_logger().warn(f'No camera info data yet')
            return
        
        # if we got to this point, we have what we need to do calculations about where the user is information

        found_user = False

        results = self.model.predict(cv_img)
        if len(results[0].boxes) > 0:
            markedImage = cv_img.copy()
            for box in results[0].boxes:
                class_id = int(box.cls.item())
                class_name = results[0].names[class_id]
                confidence = float(box.conf.item())

                if class_name == "person":
                    found_user = True

                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2

                    distance, person_x, person_y = self.calculate_distance_x_y(center_x, center_y)

                    cv2.rectangle(markedImage, (x1, y1), (x2, y2), (0,255, 0), 2)

                    if distance is not None:
                        # label = f"{class_name}: {confidence:.2f}, Distance: {distance:.2f}"
                        self.get_logger().info(f"Detected {class_name} at distance: {distance:.2f} Position Relative of Robot: ({person_x}, {person_y})")
                    else:
                        # label = f"{class_name}: {confidence:.2f}, Distance: Unknown"
                        self.get_logger().info(f"Detected {class_name}")

                # (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                # cv2.rectangle(markedImage, (x1, y1), (x2, y2), (0,255, 0), 2)
                # cv2.putText(markedImage, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 2)
                
                if found_user and distance is not None:
                    fn = os.path.join(self.output_dir, f'img_{self.last_save}_{class_name}_detected.jpg')
                    cv2.imwrite(fn, markedImage)
                    self.get_logger().info(f"Saved {class_name} detection image to {fn}")

                    # publish message
                    human_pos_msg = HumanPos()
                    human_pos_msg.x = float(person_x)
                    human_pos_msg.y = float(person_y)
                    human_pos_msg.distance = float(distance)
                    human_pos_msg.confidence = confidence

                    self.pub.publish(human_pos_msg)
                    self.get_logger().warn(f'Published to topic')

        else:
            self.get_logger().warn(f'No Objects found')
        

        self.last_save = now

    def calculate_distance_x_y(self, x, y):
        if self.scan is None or self.cameraMatrix is None:
            self.get_logger().warn(f"Missing scan or camera matrix")
            return None, None, None
        
        if x < 0 or x >= self.image_width or y < 0 or y >= self.image_height:
            self.get_logger().warn(f"Point {x}, {y} is outside image bounds")
            return None, None, None
        
        fx = self.cameraMatrix[0,0]
        cx = self.cameraMatrix[0,2]

        # self.get_logger().warn(f"Camera Matrix: fx={fx} cx={cx} ")
        # self.get_logger().warn(f"Image Dimensions: {self.image_width}x{self.image_height}")

        # horFOV = 2 * math.atan2(self.image_width / 2, fx)

        # self.get_logger().info(f"HORFOV: {horFOV * 180 / math.pi} degrees")

        normX = (x - cx) / fx
        angle = math.atan2(normX, 1.0)

        angle_min = self.scan.angle_min
        angle_max = self.scan.angle_max
        angle_inc = self.scan.angle_increment
        num_points = len(self.scan.ranges)

        # self.get_logger().info(f"min={angle_min} max={angle_max} inc={angle_inc}")

        lidar_angle = -angle

        while lidar_angle < angle_min:
            lidar_angle += 2 * math.pi

        while lidar_angle > angle_max:
            lidar_angle -= 2 * math.pi

        if lidar_angle < angle_min or lidar_angle > angle_max:
            self.get_logger().info(f"Angle={lidar_angle} is outside range")
            return None, None, None
        
        index = int(round((lidar_angle - angle_min) / angle_inc))

        while index < 0:
            index += num_points

        while index >= num_points:
            index -= num_points

        if index < 0 or index >= num_points:
            self.get_logger().info(f"index={index} numofpoints={num_points}")
            return None, None, None
        
        distance = self.scan.ranges[index]

        if math.isnan(distance) or distance < self.scan.range_min or distance > self.scan.range_max:
            self.get_logger().info(f"Direct measurements invalid, trying nearby points")
            window_size = 15
            valid_distances = []
            valid_indicies = []

            for i in range(-window_size, window_size+1):
                idx = (index + i) % num_points
                d = self.scan.ranges[idx]

                if not math.isnan(d) and not math.isinf(d) and d >= self.scan.range_min and d <= self.scan.range_max:
                    valid_distances.append(d)
                    valid_indicies.append(idx)

            if valid_distances:
                median_idx = valid_distances.index(sorted(valid_distances)[len(valid_distances) // 2])
                distance = valid_distances[median_idx]
                index = valid_indicies[median_idx]
                self.get_logger().info(f"found valid distance: {distance:.2f}")

                lidar_angle = angle_min + index * angle_inc
                if lidar_angle > math.pi:
                    lidar_angle -= 2 * math.pi
            else:
                self.get_logger().info(f"no valid distance")
                return None, None, None
        x_pos = distance * math.cos(lidar_angle)
        y_pos = distance * math.sin(lidar_angle)

        self.get_logger().info(f"final distance: {distance:.2f}. x={x_pos} y={y_pos}")
        return distance, x_pos, y_pos





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
