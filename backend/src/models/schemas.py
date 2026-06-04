"""Canonical event schemas for the Store Intelligence System.

This module defines the unified event schema (v1) that normalizes
all heterogeneous input events into a consistent format.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class EventType(str, Enum):
    """Supported event types in the system."""

    ENTRY = "entry"
    EXIT = "exit"
    ZONE_ENTERED = "zone_entered"
    ZONE_EXITED = "zone_exited"
    QUEUE_JOINED = "queue_joined"
    QUEUE_SERVED = "queue_served"
    QUEUE_COMPLETED = "queue_completed"
    QUEUE_ABANDONED = "queue_abandoned"


class PersonInfo(BaseModel):
    """Person demographic and group information."""

    gender: Optional[str] = Field(None, description="M, F, Unknown, or null")
    age: Optional[int] = Field(None, ge=0, le=120, description="Estimated age")
    age_bucket: Optional[str] = Field(None, description="Age range (e.g., 25-34)")
    is_staff: bool = Field(False, description="Whether person is staff member")
    is_face_hidden: Optional[bool] = Field(None, description="Face visibility status")
    group_id: Optional[str] = Field(None, description="Group identifier if in a group")
    group_size: Optional[int] = Field(None, ge=1, description="Size of the group")

    @field_validator("gender")
    @classmethod
    def normalize_gender(cls, v: Optional[str]) -> Optional[str]:
        """Normalize gender values."""
        if v is None:
            return None
        v_upper = v.upper()
        if v_upper in ["M", "MALE"]:
            return "M"
        elif v_upper in ["F", "FEMALE"]:
            return "F"
        return "Unknown"


class ZoneInfo(BaseModel):
    """Zone spatial and classification information."""

    zone_id: Optional[str] = Field(None, description="Unique zone identifier")
    zone_name: Optional[str] = Field(None, description="Human-readable zone name")
    zone_type: Optional[str] = Field(None, description="Zone category (SHELF, DISPLAY, BILLING)")
    is_revenue_zone: Optional[bool] = Field(None, description="Whether zone generates revenue")
    hotspot_x: Optional[float] = Field(None, description="X coordinate in frame")
    hotspot_y: Optional[float] = Field(None, description="Y coordinate in frame")

    @field_validator("is_revenue_zone", mode="before")
    @classmethod
    def normalize_revenue_zone(cls, v) -> Optional[bool]:
        """Normalize revenue zone to boolean."""
        if v is None:
            return None
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ["yes", "true", "1"]
        return bool(v)


class QueueInfo(BaseModel):
    """Queue event timing and position information."""

    queue_event_id: Optional[UUID] = Field(None, description="Unique queue event ID")
    join_timestamp: Optional[datetime] = Field(None, description="When person joined queue")
    served_timestamp: Optional[datetime] = Field(
        None, description="When person started being served"
    )
    exit_timestamp: Optional[datetime] = Field(None, description="When person left queue")
    wait_seconds: Optional[float] = Field(None, ge=0, description="Time waited before service")
    position_at_join: Optional[int] = Field(None, ge=1, description="Queue position when joined")
    abandoned: Optional[bool] = Field(None, description="Whether person abandoned queue")


class MetadataInfo(BaseModel):
    """Event metadata and provenance information."""

    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Detection confidence")
    model_version: Optional[str] = Field(None, description="CV model version used")
    processing_timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When event was processed"
    )
    source: str = Field(default="cv_pipeline", description="Event source system")


class CanonicalEvent(BaseModel):
    """Canonical event schema v1.

    This is the unified event format that all heterogeneous input events
    are normalized into. It supports all event types with optional fields
    to accommodate partial data.
    """

    event_id: UUID = Field(default_factory=uuid4, description="Unique event identifier")
    event_type: EventType = Field(..., description="Type of event")
    timestamp: datetime = Field(..., description="Event occurrence time (UTC)")
    store_id: str = Field(..., description="Store identifier")
    camera_id: str = Field(..., description="Camera identifier")
    track_id: Optional[int] = Field(None, description="Person track ID (may be inconsistent)")

    person: PersonInfo = Field(default_factory=PersonInfo, description="Person information")
    zone: ZoneInfo = Field(default_factory=ZoneInfo, description="Zone information")
    queue: QueueInfo = Field(default_factory=QueueInfo, description="Queue information")
    metadata: MetadataInfo = Field(default_factory=MetadataInfo, description="Event metadata")

    schema_version: str = Field(default="1.0", description="Schema version")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "event_type": "zone_entered",
                "timestamp": "2026-03-08T18:10:45.280000Z",
                "store_id": "ST1076",
                "camera_id": "CAM2",
                "track_id": 101,
                "person": {
                    "gender": "F",
                    "age": 28,
                    "age_bucket": "25-34",
                    "is_staff": False,
                    "is_face_hidden": False,
                },
                "zone": {
                    "zone_id": "PURPLLE_MUM_1076_Z01",
                    "zone_name": "Left Shelf",
                    "zone_type": "SHELF",
                    "is_revenue_zone": True,
                    "hotspot_x": 412.6,
                    "hotspot_y": 238.4,
                },
                "metadata": {
                    "confidence": 0.95,
                    "model_version": "yolov8n",
                    "processing_timestamp": "2026-03-08T18:10:45.500000Z",
                },
                "schema_version": "1.0",
            }
        }


class POSTransaction(BaseModel):
    """POS transaction record."""

    order_id: int
    order_date: str
    order_time: str
    store_id: str
    product_id: int
    brand_name: str
    total_amount: float

    @property
    def transaction_datetime(self) -> datetime:
        """Combine date and time into single datetime."""
        from datetime import datetime

        dt_str = f"{self.order_date} {self.order_time}"
        return datetime.strptime(dt_str, "%d-%m-%Y %H:%M:%S")


class StoreMetrics(BaseModel):
    """Aggregated store metrics for a time window."""

    store_id: str
    window_start: datetime
    window_end: datetime
    
    # Footfall metrics
    total_footfall: int = 0
    unique_visitors: int = 0
    staff_count: int = 0
    customer_count: int = 0
    
    # Demographics
    male_count: int = 0
    female_count: int = 0
    unknown_gender_count: int = 0
    avg_age: Optional[float] = None
    
    # Dwell metrics
    avg_dwell_seconds: Optional[float] = None
    total_dwell_seconds: float = 0
    
    # Queue metrics
    total_queue_joins: int = 0
    total_queue_completions: int = 0
    total_queue_abandonments: int = 0
    avg_wait_seconds: Optional[float] = None
    max_wait_seconds: Optional[float] = None
    abandonment_rate: Optional[float] = None
    
    # Revenue correlation
    total_transactions: int = 0
    total_revenue: float = 0
    conversion_rate: Optional[float] = None


class ZoneMetrics(BaseModel):
    """Zone-specific metrics."""

    zone_id: str
    zone_name: str
    store_id: str
    window_start: datetime
    window_end: datetime
    
    visits: int = 0
    unique_visitors: int = 0
    avg_dwell_seconds: Optional[float] = None
    total_dwell_seconds: float = 0
    heat_score: float = 0.0  # Normalized 0-1 score


class Anomaly(BaseModel):
    """Detected anomaly with explanation."""

    anomaly_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime
    store_id: str
    anomaly_type: str  # queue_spike, excessive_abandonment, low_dwell, camera_down, etc.
    severity: str  # low, medium, high, critical
    description: str
    affected_entity: Optional[str] = None  # camera_id, zone_id, etc.
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    recommended_action: Optional[str] = None
