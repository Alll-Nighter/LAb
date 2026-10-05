import cv2
import yaml
from datetime import datetime
from .camera_manager import CameraManager
from .detector import Detector
from .tracker import TrackerManager
from .rules import check_ppe_violations, ViolationEvent
from .event_emitter import EventEmitter
from .zones import check_zones_for_point

def load_ppe_config(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_cv_pipeline(config_path: str, ppe_config_path: str, api_base_url: str):
    cam_mgr = CameraManager(config_path)
    detector = Detector("yolov8n.pt")
    track_mgr = TrackerManager()
    emitter = EventEmitter(api_base_url)
    ppe_cfg = load_ppe_config(ppe_config_path)
    class_mapping = {int(k): v for k, v in ppe_cfg.get("class_mapping", {}).items()}
    min_frames = ppe_cfg.get("violation", {}).get("min_frames", 10)
    conf = ppe_cfg.get("thresholds", {}).get("conf", 0.25)
    iou = ppe_cfg.get("thresholds", {}).get("iou", 0.45)
    detector.model.conf = conf
    detector.model.iou = iou

    sources = cam_mgr.get_sources()
    print(f"Running CV pipeline on {len(sources)} cameras. Press 'q' to exit.")

    # Per-track violation counters (missing set) to enforce temporal smoothing
    track_violation_state = {}  # track_id -> {zone_name, vtype, count}

    try:
        while True:
            for src in sources:
                ret, frame = src.read()
                if not ret:
                    continue

                results = detector.detect_with_tracking(frame)

                # Draw detections and tracks
                for r in results:
                    boxes = r.boxes
                    if boxes is None:
                        continue
                    for box, cid, cf in zip(boxes.xyxy, boxes.cls, boxes.conf):
                        x1, y1, x2, y2 = map(int, box.tolist())
                        label = class_mapping.get(int(cid), f"C{int(cid)}")
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f"{label} {cf:.2f}", (x1, y1 - 8),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                # Map detections to tracks and evaluate violations
                candidates = check_ppe_violations(results, src.zones, track_mgr, class_mapping, min_frames)

                # Attach candidates to tracks by proximity (use box overlap with track's last_bbox)
                for c in candidates:
                    cbox = c["box"]
                    # Find best matching track by overlap
                    best_tid = None
                    best_iou = 0.3
                    for tid, t in track_mgr.tracks.items():
                        if t.last_bbox is None:
                            continue
                        iou = ((max(cbox, t.last_bbox) - min(cbox[2], t.last_bbox[2])) * 0.0)  # placeholder
                        # Simpler: use centroid distance
                        cx1 = (cbox + cbox[2]) / 2
                        cy1 = (cbox[1] + cbox[3]) / 2
                        cx2 = (t.last_bbox + t.last_bbox[2]) / 2
                        cy2 = (t.last_bbox[1] + t.last_bbox[3]) / 2
                        dist = ((cx1 - cx2)**2 + (cy1 - cy2)**2)**0.5
                        if dist < 60:  # pixels
                            best_tid = tid
                            break

                    if best_tid is None:
                        continue

                    key = (best_tid, c["zone_name"], c["violation_type"])
                    state = track_violation_state.get(key, {"count": 0})
                    state["count"] += 1
                    track_violation_state[key] = state

                    if state["count"] >= min_frames:
                        event = {
                            "camera_id": src.cam_id,
                            "track_id": best_tid,
                            "zone_name": c["zone_name"],
                            "violation_type": c["violation_type"],
                            "confidence": c["confidence"],
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                        emitter.emit(event, frame)
                        # Reset counter after emitting to avoid spam
                        state["count"] = 0
                        track_violation_state[key] = state

                # Draw zones
                for z in src.zones:
                    poly = z.get("polygon", [])
                    if len(poly) >= 3:
                        pts = [(int(p), int(p[1])) for p in poly]
                        cv2.polylines(frame, [pts], isClosed=True, color=(255, 0, 0), thickness=2)

                cv2.imshow(f"Cam {src.name}", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    return
    finally:
        cam_mgr.close_all()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    run_cv_pipeline(
        config_path="configs/cameras.yaml",
        ppe_config_path="configs/ppe_rules.yaml",
        api_base_url="http://localhost:8000"
    )
