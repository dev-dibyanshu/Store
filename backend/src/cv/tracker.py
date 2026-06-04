"""Multi-object tracking using SORT algorithm."""

import numpy as np
from typing import List, Tuple, Dict
from filterpy.kalman import KalmanFilter


class Track:
    """Represents a tracked person."""
    
    count = 0
    
    def __init__(self, bbox: Tuple[int, int, int, int], track_id: int = None):
        self.track_id = track_id if track_id is not None else Track.count
        Track.count += 1
        
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        self.kf.F = np.array([
            [1, 0, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 1, 0],
            [0, 0, 1, 0, 0, 0, 1],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 1]
        ])
        self.kf.H = np.array([
            [1, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0]
        ])
        
        self.kf.R *= 10
        self.kf.P *= 1000
        self.kf.Q[-1, -1] *= 0.01
        self.kf.Q[4:, 4:] *= 0.01
        
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        w = x2 - x1
        h = y2 - y1
        
        self.kf.x[:4] = [[cx], [cy], [w], [h]]
        self.age = 0
        self.hits = 1
        self.hit_streak = 1
        self.time_since_update = 0
    
    def update(self, bbox: Tuple[int, int, int, int]):
        """Update track with new detection."""
        self.time_since_update = 0
        self.hits += 1
        self.hit_streak += 1
        
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        w = x2 - x1
        h = y2 - y1
        
        self.kf.update([[cx], [cy], [w], [h]])
    
    def predict(self):
        """Predict next position."""
        self.kf.predict()
        self.age += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        return self.get_state()
    
    def get_state(self) -> Tuple[int, int, int, int]:
        """Get current bounding box."""
        cx, cy, w, h = self.kf.x[:4]
        x1 = int(cx - w / 2)
        y1 = int(cy - h / 2)
        x2 = int(cx + w / 2)
        y2 = int(cy + h / 2)
        return (x1, y1, x2, y2)


class PersonTracker:
    """Track multiple people across frames using SORT."""
    
    def __init__(self, max_age: int = 30, min_hits: int = 3, iou_threshold: float = 0.3):
        """
        Initialize tracker.
        
        Args:
            max_age: Maximum frames to keep track without detection
            min_hits: Minimum hits to confirm track
            iou_threshold: IOU threshold for matching
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.tracks: List[Track] = []
        self.frame_count = 0
    
    def update(self, detections: List[Tuple[int, int, int, int, float]]) -> Dict[int, Tuple[int, int, int, int]]:
        """
        Update tracks with new detections.
        
        Args:
            detections: List of (x1, y1, x2, y2, conf)
        
        Returns:
            Dict of {track_id: (x1, y1, x2, y2)} for confirmed tracks
        """
        self.frame_count += 1
        
        # Predict all tracks
        for track in self.tracks:
            track.predict()
        
        # Match detections to tracks
        if len(detections) > 0 and len(self.tracks) > 0:
            det_boxes = [d[:4] for d in detections]
            track_boxes = [t.get_state() for t in self.tracks]
            
            iou_matrix = np.zeros((len(det_boxes), len(track_boxes)))
            for d, det in enumerate(det_boxes):
                for t, trk in enumerate(track_boxes):
                    iou_matrix[d, t] = self._iou(det, trk)
            
            # Greedy matching
            matched_indices = []
            unmatched_dets = list(range(len(det_boxes)))
            unmatched_tracks = list(range(len(track_boxes)))
            
            while len(unmatched_dets) > 0 and len(unmatched_tracks) > 0:
                max_iou = 0
                max_det, max_track = -1, -1
                for d in unmatched_dets:
                    for t in unmatched_tracks:
                        if iou_matrix[d, t] > max_iou:
                            max_iou = iou_matrix[d, t]
                            max_det, max_track = d, t
                
                if max_iou < self.iou_threshold:
                    break
                
                matched_indices.append((max_det, max_track))
                unmatched_dets.remove(max_det)
                unmatched_tracks.remove(max_track)
            
            # Update matched tracks
            for det_idx, track_idx in matched_indices:
                self.tracks[track_idx].update(det_boxes[det_idx])
            
            # Create new tracks for unmatched detections
            for det_idx in unmatched_dets:
                self.tracks.append(Track(det_boxes[det_idx]))
            
            # Remove old tracks
            self.tracks = [t for t in self.tracks if t.time_since_update < self.max_age]
        
        elif len(detections) > 0:
            # No existing tracks, create new ones
            for det in detections:
                self.tracks.append(Track(det[:4]))
        
        # Return confirmed tracks
        result = {}
        for track in self.tracks:
            if track.hits >= self.min_hits or self.frame_count <= self.min_hits:
                result[track.track_id] = track.get_state()
        
        return result
    
    @staticmethod
    def _iou(box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
        """Calculate IOU between two boxes."""
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2
        
        inter_x_min = max(x1_min, x2_min)
        inter_y_min = max(y1_min, y2_min)
        inter_x_max = min(x1_max, x2_max)
        inter_y_max = min(y1_max, y2_max)
        
        if inter_x_max < inter_x_min or inter_y_max < inter_y_min:
            return 0.0
        
        inter_area = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = box1_area + box2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0.0
