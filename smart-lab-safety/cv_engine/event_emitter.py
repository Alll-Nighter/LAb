import requests
import cv2
import os
from pathlib import Path

class EventEmitter:
    def __init__(self, api_base_url: str, snapshots_dir: str = "snapshots"):
        self.api_base_url = api_base_url
        self.snapshots_dir = Path(snapshots_dir)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def emit(self, event_dict: dict, frame):
        # Save snapshot
        ts = event_dict["timestamp"].replace(":", "-").replace(".", "-")
        fname = f"cam{event_dict['camera_id']}_trk{event_dict['track_id']}_{ts}.jpg"
        path = self.snapshots_dir / fname
        cv2.imwrite(str(path), frame)
        payload = {
            "camera_id": event_dict["camera_id"],
            "track_id": event_dict["track_id"],
            "zone": event_dict["zone_name"],
            "violation_type": event_dict["violation_type"],
            "confidence": event_dict["confidence"],
            "timestamp": event_dict["timestamp"],
            "snapshot_path": str(path),
        }
        try:
            r = requests.post(f"{self.api_base_url}/events", json=payload, timeout=2)
            if r.status_code >= 400:
                print("API error:", r.status_code, r.text)
        except Exception as e:
            print("Failed to send event:", e)
