from ultralytics import YOLO

class Detector:
    def __init__(self, model_name: str = "yolov8n.pt"):
        self.model = YOLO(model_name)

    def detect(self, frame):
        return self.model(frame, conf=0.25, iou=0.45)

    def detect_with_tracking(self, frame, tracker: str = "bytetrack.yaml"):
        return self.model.track(frame, conf=0.25, iou=0.45, tracker=tracker)
