import cv2
import yaml
from pathlib import Path

class CameraSource:
    def __init__(self, cam_id, name: str, zones: list):
        self.cam_id = cam_id
        self.name = name
        self.zones = zones or []
        self.cap = cv2.VideoCapture(cam_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera {cam_id}")

    def read(self):
        return self.cap.read()

    def release(self):
        self.cap.release()

class CameraManager:
    def __init__(self, config_path: str):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        self.sources = []
        for c in cfg.get("cameras", []):
            cam_id = c["id"]
            name = c.get("name", f"Cam-{cam_id}")
            zones = c.get("zones", [])
            self.sources.append(CameraSource(cam_id, name, zones))

    def get_sources(self):
        return self.sources

    def close_all(self):
        for s in self.sources:
            s.release()
