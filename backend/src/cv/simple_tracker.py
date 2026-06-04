"""Simplified centroid-based tracker."""

import numpy as np
from typing import List, Tuple, Dict
from collections import OrderedDict


class SimpleTracker:
    """Simple centroid-based multi-object tracker with conservative track creation."""
    
    def __init__(self, max_disappeared: int = 300, max_distance: int = 300):
        """
        Initialize tracker.
        
        Args:
            max_disappeared: Frames before considering a track truly gone (very conservative)
            max_distance: Maximum pixel distance for matching (very lenient)
        """
        self.next_object_id = 0
        self.objects = OrderedDict()  # object_id -> centroid
        self.disappeared = OrderedDict()  # object_id -> frames_disappeared
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
    
    def register(self, centroid: Tuple[float, float]) -> int:
        """Register a new object."""
        object_id = self.next_object_id
        self.objects[object_id] = centroid
        self.disappeared[object_id] = 0
        self.next_object_id += 1
        return object_id
    
    def deregister(self, object_id: int):
        """Remove an object."""
        del self.objects[object_id]
        del self.disappeared[object_id]
    
    def update(self, detections: List[Tuple[int, int, int, int, float]]) -> Dict[int, Tuple[int, int, int, int]]:
        """
        Update tracker with new detections.
        
        Args:
            detections: List of (x1, y1, x2, y2, conf)
        
        Returns:
            Dict of {track_id: (x1, y1, x2, y2)}
        """
        # If no detections, mark all as disappeared
        if len(detections) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return {}
        
        # Calculate centroids for current detections
        input_centroids = []
        input_rects = []
        for det in detections:
            x1, y1, x2, y2 = det[:4]
            cx = int((x1 + x2) / 2.0)
            cy = int((y1 + y2) / 2.0)
            input_centroids.append((cx, cy))
            input_rects.append((x1, y1, x2, y2))
        
        # If no existing objects, register all as new
        if len(self.objects) == 0:
            for i in range(len(input_centroids)):
                self.register(input_centroids[i])
        else:
            # Get existing object IDs and centroids
            object_ids = list(self.objects.keys())
            object_centroids = list(self.objects.values())
            
            # Calculate distance matrix
            dist_matrix = np.zeros((len(object_centroids), len(input_centroids)))
            for i, (ox, oy) in enumerate(object_centroids):
                for j, (ix, iy) in enumerate(input_centroids):
                    dist = np.sqrt((ox - ix) ** 2 + (oy - iy) ** 2)
                    dist_matrix[i, j] = dist
            
            # Match using greedy assignment
            rows = dist_matrix.min(axis=1).argsort()
            cols = dist_matrix.argmin(axis=1)[rows]
            
            used_rows = set()
            used_cols = set()
            
            for (row, col) in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                
                # More lenient distance threshold
                if dist_matrix[row, col] > self.max_distance:
                    continue
                
                object_id = object_ids[row]
                self.objects[object_id] = input_centroids[col]
                self.disappeared[object_id] = 0
                
                used_rows.add(row)
                used_cols.add(col)
            
            # Mark unmatched existing objects as disappeared
            unused_rows = set(range(0, dist_matrix.shape[0])).difference(used_rows)
            for row in unused_rows:
                object_id = object_ids[row]
                self.disappeared[object_id] += 1
                
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            
            # Register new objects only if no close existing tracks
            unused_cols = set(range(0, dist_matrix.shape[1])).difference(used_cols)
            for col in unused_cols:
                # Double-check that this detection is far from ALL existing tracks
                min_dist_to_any = float('inf')
                for (ox, oy) in object_centroids:
                    ix, iy = input_centroids[col]
                    dist = np.sqrt((ox - ix) ** 2 + (oy - iy) ** 2)
                    min_dist_to_any = min(min_dist_to_any, dist)
                
                # Only register if truly far from all existing tracks
                if min_dist_to_any > self.max_distance:
                    self.register(input_centroids[col])
        
        # Return current objects with their bounding boxes
        result = {}
        for object_id, centroid in self.objects.items():
            # Find closest input rect to this centroid
            cx, cy = centroid
            min_dist = float('inf')
            best_rect = None
            
            for rect, (icx, icy) in zip(input_rects, input_centroids):
                dist = np.sqrt((cx - icx) ** 2 + (cy - icy) ** 2)
                if dist < min_dist:
                    min_dist = dist
                    best_rect = rect
            
            if best_rect and min_dist < self.max_distance:
                result[object_id] = best_rect
        
        return result
