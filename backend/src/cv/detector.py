"""Person detection using YOLOv8."""

import cv2
import numpy as np
from typing import List, Tuple
from ultralytics import YOLO


class PersonDetector:
    """Detect people in video frames using YOLOv8."""
    
    def __init__(self, model_name: str = "yolov8n.pt", conf_threshold: float = 0.4):
        """
        Initialize YOLOv8 detector.
        
        Args:
            model_name: YOLOv8 model variant (n=nano, s=small, m=medium, l=large, x=extra-large)
            conf_threshold: Confidence threshold for detections
        """
        self.model = YOLO(model_name)
        self.conf_threshold = conf_threshold
        self.person_class_id = 0  # COCO class ID for person
    
    def detect(self, frame: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        Detect people in a frame.
        
        Args:
            frame: Input frame (BGR format)
        
        Returns:
            List of detections as (x1, y1, x2, y2, confidence)
        """
        results = self.model.predict(frame, conf=self.conf_threshold, classes=[self.person_class_id], verbose=False)
        
        detections = []
        if len(results) > 0:
            boxes = results[0].boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0].cpu().numpy())
                    detections.append((int(x1), int(y1), int(x2), int(y2), conf))
        
        return detections
