"""Event normalization - converts heterogeneous formats to canonical schema."""

from datetime import datetime
from typing import Any, Dict, Optional

from src.models.schemas import CanonicalEvent, EventType, PersonInfo, QueueInfo, ZoneInfo


class EventNormalizer:
    """Normalizes varied event formats into canonical schema."""

    FIELD_MAPPINGS = {
        "store_id": ["store_id", "store_code"],
        "camera_id": ["camera_id"],
        "track_id": ["track_id", "id_token"],
        "timestamp": ["event_timestamp", "event_time", "timestamp"],
        "gender": ["gender", "gender_pred"],
        "age": ["age", "age_pred"],
    }

    @staticmethod
    def _get_field(data: Dict[str, Any], field_name: str) -> Optional[Any]:
        possible_keys = EventNormalizer.FIELD_MAPPINGS.get(field_name, [field_name])
        for key in possible_keys:
            if key in data:
                return data[key]
        return None
    
    @staticmethod
    def _normalize_store_id(store_id: Optional[str]) -> Optional[str]:
        """Normalize store_id to consistent format."""
        if not store_id:
            return None
        # Convert ST1076 -> store_1076 for consistency
        if store_id.startswith("ST"):
            return f"store_{store_id[2:]}"
        return store_id

    @staticmethod
    def _normalize_timestamp(ts: Any) -> datetime:
        if isinstance(ts, datetime):
            return ts
        if isinstance(ts, str):
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except:
                return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%f")
        raise ValueError(f"Cannot parse timestamp: {ts}")

    @staticmethod
    def _normalize_track_id(track_id: Any) -> Optional[int]:
        if track_id is None:
            return None
        if isinstance(track_id, int):
            return track_id
        if isinstance(track_id, str):
            if track_id.startswith("ID_"):
                try:
                    return int(track_id.split("_")[1])
                except:
                    pass
        return None

    @classmethod
    def normalize(cls, data: Dict[str, Any]) -> CanonicalEvent:
        event_type = data.get("event_type")
        if not event_type:
            raise ValueError("Missing event_type")
        
        # Try to get timestamp from standard fields, fallback to queue timestamps
        timestamp = cls._get_field(data, "timestamp")
        if not timestamp:
            # For queue events, use queue_exit_ts if available, else queue_join_ts
            if data.get("queue_exit_ts"):
                timestamp = data["queue_exit_ts"]
            elif data.get("queue_join_ts"):
                timestamp = data["queue_join_ts"]
            elif data.get("queue_served_ts"):
                timestamp = data["queue_served_ts"]
        
        if not timestamp:
            raise ValueError("Missing timestamp")
        
        person = PersonInfo(
            gender=cls._get_field(data, "gender"),
            age=cls._get_field(data, "age"),
            age_bucket=data.get("age_bucket"),
            is_staff=data.get("is_staff", False),
            is_face_hidden=data.get("is_face_hidden"),
            group_id=data.get("group_id"),
            group_size=data.get("group_size"),
        )
        
        zone = ZoneInfo(
            zone_id=data.get("zone_id"),
            zone_name=data.get("zone_name"),
            zone_type=data.get("zone_type"),
            is_revenue_zone=data.get("is_revenue_zone"),
            hotspot_x=data.get("zone_hotspot_x"),
            hotspot_y=data.get("zone_hotspot_y"),
        )
        
        queue = QueueInfo(
            queue_event_id=data.get("queue_event_id"),
            join_timestamp=(
                cls._normalize_timestamp(data["queue_join_ts"])
                if data.get("queue_join_ts")
                else None
            ),
            served_timestamp=(
                cls._normalize_timestamp(data["queue_served_ts"])
                if data.get("queue_served_ts")
                else None
            ),
            exit_timestamp=(
                cls._normalize_timestamp(data["queue_exit_ts"])
                if data.get("queue_exit_ts")
                else None
            ),
            wait_seconds=data.get("wait_seconds"),
            position_at_join=data.get("queue_position_at_join"),
            abandoned=data.get("abandoned"),
        )
        
        return CanonicalEvent(
            event_type=EventType(event_type),
            timestamp=cls._normalize_timestamp(timestamp),
            store_id=cls._normalize_store_id(cls._get_field(data, "store_id")),
            camera_id=cls._get_field(data, "camera_id"),
            track_id=cls._normalize_track_id(cls._get_field(data, "track_id")),
            person=person,
            zone=zone,
            queue=queue,
        )
