import time

class TrackState:
    def __init__(self, track_id: int):
        self.track_id = track_id
        self.first_seen = time.time()
        self.last_seen = time.time()
        self.last_bbox = None
        self.last_zone = None
        self.violation_frames = 0

class TrackerManager:
    def __init__(self):
        self.tracks: dict[int, TrackState] = {}

    def update_tracks(self, results):
        # results is Ultralytics Results list
        for r in results:
            boxes = r.boxes
            if boxes is None:
                continue
            ids = boxes.id
            xyxy = boxes.xyxy
            if ids is None:
                continue
            for tid, box in zip(ids.tolist(), xyxy.tolist()):
                tid = int(tid)
                if tid not in self.tracks:
                    self.tracks[tid] = TrackState(tid)
                t = self.tracks[tid]
                t.last_seen = time.time()
                t.last_bbox = box
        # Optional: cleanup old tracks not seen for >5s
        now = time.time()
        stale = [tid for tid, t in self.tracks.items() if now - t.last_seen > 5.0]
        for tid in stale:
            del self.tracks[tid]

    def get_track_state(self, track_id: int):
        return self.tracks.get(track_id)
