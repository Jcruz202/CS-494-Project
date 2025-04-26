from ultralytics import YOLO

model = YOLO("src/chester/chester/yolov8n.pt")

results = model.predict("/home/emily/gazebo_images/")

result = results[0]

print(len(result.boxes))

box = result.boxes[0]

# result.name will give a hash map of all the objects

cords = box.xyxy[0].tolist()
class_id = box.cls[0].item()
conf = box.conf[0].item()
print("Object type:", result.names[class_id])
print("Coordinates:", cords)
print("Probability:", conf)