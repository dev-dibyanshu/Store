"""Zone mapping and event generation based on store layout."""

import json
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime
import uuid


class Zone:
    """Represents a zone in the store."""
    
    def __init__(self, zone_id: str, name: str, zone_type: str, polygon: List[Tuple[int, int]], is_revenue: bool = True):
        self.zone_id = zone_id
        self.name = name
        self.zone_type = zone_type
        self.polygon = polygon
        self.is_revenue = is_revenue
    
    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is inside zone polygon using ray casting."""
        n = len(self.polygon)
        inside = False
        
        p1x, p1y = self.polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = self.polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside


class ZoneMapper:
    """Maps person positions to store zones and generates events."""
    
    def __init__(self, store_id: str, camera_id: str):
        self.store_id = store_id
        self.camera_id = camera_id
        self.zones: List[Zone] = []
        self.track_zones: Dict[int, Optional[str]] = {}  # track_id -> current zone_id
        self.track_active: Set[int] = set()  # tracks currently in frame
        self.events = []
    
    def add_zone(self, zone_id: str, name: str, zone_type: str, polygon: List[Tuple[int, int]], is_revenue: bool = True):
        """Add a zone definition."""
        self.zones.append(Zone(zone_id, name, zone_type, polygon, is_revenue))
    
    def update(self, tracks: Dict[int, Tuple[int, int, int, int]], timestamp: datetime) -> List[Dict]:
        """
        Update zone state and generate events.
        
        Args:
            tracks: Dict of {track_id: (x1, y1, x2, y2)}
            timestamp: Current timestamp
        
        Returns:
            List of generated events
        """
        new_events = []
        current_tracks = set(tracks.keys())
        
        # Process each track
        for track_id, bbox in tracks.items():
            x1, y1, x2, y2 = bbox
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            # Check if new track (entry event)
            if track_id not in self.track_active:
                self.track_active.add(track_id)
                # Add simple demographic estimation for demo
                gender = 'M' if track_id % 2 == 0 else 'F'
                age = 25 + (track_id % 35)  # Ages between 25-59
                age_bucket = self._get_age_bucket(age)
                
                entry_event = self._create_event("entry", track_id, timestamp)
                entry_event.update({
                    'gender': gender,
                    'age': age,
                    'age_bucket': age_bucket
                })
                new_events.append(entry_event)
            
            # Find which zone the person is in
            current_zone = None
            for zone in self.zones:
                if zone.contains_point(center_x, center_y):
                    current_zone = zone.zone_id
                    break
            
            # Check for zone transitions
            previous_zone = self.track_zones.get(track_id)
            
            if current_zone != previous_zone:
                # Exited previous zone
                if previous_zone is not None:
                    zone_obj = next((z for z in self.zones if z.zone_id == previous_zone), None)
                    if zone_obj:
                        new_events.append(self._create_zone_event(
                            "zone_exited", track_id, timestamp, zone_obj, center_x, center_y
                        ))
                
                # Entered new zone
                if current_zone is not None:
                    zone_obj = next((z for z in self.zones if z.zone_id == current_zone), None)
                    if zone_obj:
                        new_events.append(self._create_zone_event(
                            "zone_entered", track_id, timestamp, zone_obj, center_x, center_y
                        ))
                
                self.track_zones[track_id] = current_zone
        
        # Detect exits (tracks that disappeared)
        disappeared_tracks = self.track_active - current_tracks
        for track_id in disappeared_tracks:
            new_events.append(self._create_event("exit", track_id, timestamp))
            
            # Also generate zone_exited if they were in a zone
            if self.track_zones.get(track_id):
                zone_obj = next((z for z in self.zones if z.zone_id == self.track_zones[track_id]), None)
                if zone_obj:
                    new_events.append(self._create_zone_event(
                        "zone_exited", track_id, timestamp, zone_obj, 0, 0
                    ))
            
            self.track_active.discard(track_id)
            if track_id in self.track_zones:
                del self.track_zones[track_id]
        
        self.events.extend(new_events)
        return new_events
    
    def _get_age_bucket(self, age: int) -> str:
        """Get age bucket string."""
        if age < 18:
            return "0-17"
        elif age < 25:
            return "18-24"
        elif age < 35:
            return "25-34"
        elif age < 45:
            return "35-44"
        elif age < 55:
            return "45-54"
        else:
            return "55+"
    
    def _create_event(self, event_type: str, track_id: int, timestamp: datetime) -> Dict:
        """Create a basic event."""
        return {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": timestamp.isoformat(),
            "store_id": self.store_id,
            "camera_id": self.camera_id,
            "track_id": track_id,
        }
    
    def _create_zone_event(self, event_type: str, track_id: int, timestamp: datetime, 
                          zone: Zone, x: int, y: int) -> Dict:
        """Create a zone event."""
        event = self._create_event(event_type, track_id, timestamp)
        event.update({
            "zone_id": zone.zone_id,
            "zone_name": zone.name,
            "zone_type": zone.zone_type,
            "is_revenue_zone": "Yes" if zone.is_revenue else "No",
            "zone_hotspot_x": float(x),
            "zone_hotspot_y": float(y),
        })
        return event
    
    def get_all_events(self) -> List[Dict]:
        """Get all generated events."""
        return self.events
