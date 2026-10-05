from dataclasses import dataclass
from datetime import datetime
import numpy as np

@dataclass
class ViolationEvent:
    camera_id: int
    track_id: int
    zone_name: str
    violation_type: str
    confidence: float
    timestamp: str
    snapshot_path: str | None = None

def boxes_overlap_ratio(box1, box2) -> float:
    x1 = max(box1, box2)
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    a1 = (box1[2] - box1) * (box1[3] - box1[1])
    a2 = (box2[2] - box2) * (box2[3] - box2[1])
    union = a1 + a2 - inter + 1e-6
    return inter / union

def check_ppe_violations(results, zones: list[dict], track_mgr, class_mapping: dict[int, str], min_frames: int = 10):
    # Parse detections into people and PPE lists
    people = []
    ppe_items = []
    for r in results:
        boxes = r.boxes
        if boxes is None:
            continue
        cls = boxes.cls
        xyxy = boxes.xyxy
        conf = boxes.conf
        for c, box, cf in zip(cls.tolist(), xyxy.tolist(), conf.tolist()):
            cid = int(c)
            label = class_mapping.get(cid, f"CLASS_{cid}")
            if label == "PERSON":
                people.append((box, cf, cid))
            elif label in ("HELMET", "VEST"):
                ppe_items.append((box, cf, label))

    events = []
    for pbox, pconf, _ in people:
        centroid = ((pbox + pbox[2]) / 2, (pbox[1] + pbox[3]) / 2)
        in_zones = check_zones_for_point(centroid, zones)
        if not in_zones:
            continue
        # For simplicity, require all zones' PPE (or use first zone's rules)
        required = set()
        for z in in_zones:
            for r in z.get("required_ppe", []):
                required.add(r.upper())
        # Find nearby PPE
        has = set()
        for qbox, qconf, qlabel in ppe_items:
            iou = boxes_overlap_ratio(pbox, qbox)
            if iou > 0.3:  # threshold
                has.add(qlabel.upper())
        missing = required - has
        if not missing:
            # No violation this frame; reset counter if you track per-track
            continue

        # For demo, pick first zone name
        zone_name = in_zones["name"]
        vtype = "NO_HELMET" if "HELMET" in missing else "NO_VEST"
        # Attach to track if available (we don't have track_id here; main_loop will pass track_mgr state)
        # We'll return partial info; main_loop will enrich with track_id and counters.
        events.append({
            "box": pbox,
            "zone_name": zone_name,
            "violation_type": vtype,
            "confidence": float(pconf),
            "missing": missing
        })
    return events
