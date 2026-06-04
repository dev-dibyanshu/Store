"""Video processing pipeline."""

import cv2
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from .detector import PersonDetector
from .simple_tracker import SimpleTracker
from .zone_mapper import ZoneMapper


class VideoProcessor:
    """Process video files to generate events."""
    
    def __init__(self, store_id: str, sample_every_n_frames: int = 3):
        """
        Initialize video processor.
        
        Args:
            store_id: Store identifier
            sample_every_n_frames: Process every N frames (for speed)
        """
        self.store_id = store_id
        self.sample_every_n_frames = sample_every_n_frames
        self.detector = PersonDetector()
        
    def process_video(
        self, 
        video_path: str, 
        camera_id: str,
        zones: List[Dict],
        start_time: Optional[datetime] = None,
        max_frames: Optional[int] = None,
        track_id_offset: int = 0
    ) -> List[Dict]:
        """
        Process a video file and generate events.
        
        Args:
            video_path: Path to video file
            camera_id: Camera identifier
            zones: List of zone definitions with 'id', 'name', 'type', 'polygon', 'is_revenue'
            start_time: Video start timestamp (defaults to now)
            max_frames: Maximum frames to process (None for all)
            track_id_offset: Offset to add to track IDs to avoid collisions
        
        Returns:
            List of generated events
        """
        if start_time is None:
            start_time = datetime.utcnow()
        
        # Initialize tracker and zone mapper with very conservative settings
        tracker = SimpleTracker(max_disappeared=300, max_distance=300)
        zone_mapper = ZoneMapper(self.store_id, camera_id)
        
        # Add zones
        for zone in zones:
            zone_mapper.add_zone(
                zone['id'],
                zone['name'],
                zone['type'],
                zone['polygon'],
                zone.get('is_revenue', True)
            )
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_time_delta = timedelta(seconds=1.0 / fps)
        
        frame_count = 0
        processed_count = 0
        current_time = start_time
        
        print(f"Processing {video_path} (FPS: {fps})")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Check frame limit
            if max_frames and processed_count >= max_frames:
                break
            
            # Sample frames
            if frame_count % self.sample_every_n_frames == 0:
                # Detect people
                detections = self.detector.detect(frame)
                
                # Update tracker
                tracks = tracker.update(detections)
                
                # Add offset to track IDs to avoid cross-camera collisions
                tracks_with_offset = {tid + track_id_offset: bbox for tid, bbox in tracks.items()}
                
                # Update zone mapper and generate events
                zone_mapper.update(tracks_with_offset, current_time)
                
                processed_count += 1
                if processed_count % 100 == 0:
                    print(f"  Processed {processed_count} frames...")
            
            current_time += frame_time_delta
            frame_count += 1
        
        cap.release()
        
        events = zone_mapper.get_all_events()
        print(f"  Generated {len(events)} events from {frame_count} frames")
        
        return events
    
    def process_store_videos(
        self,
        video_configs: List[Dict],
        start_time: Optional[datetime] = None,
        max_frames_per_video: Optional[int] = None
    ) -> List[Dict]:
        """
        Process multiple videos for a store.
        
        Args:
            video_configs: List of configs with 'path', 'camera_id', 'zones'
            start_time: Base start time
            max_frames_per_video: Limit frames per video
        
        Returns:
            Combined list of events
        """
        all_events = []
        track_offset = 0
        
        for config in video_configs:
            print(f"\nProcessing camera: {config['camera_id']}")
            events = self.process_video(
                config['path'],
                config['camera_id'],
                config['zones'],
                start_time,
                max_frames_per_video,
                track_id_offset=track_offset
            )
            all_events.extend(events)
            
            # Increment offset to avoid track ID collisions across cameras
            track_offset += 1000
        
        # Sort by timestamp
        all_events.sort(key=lambda e: e['timestamp'])
        
        return all_events
