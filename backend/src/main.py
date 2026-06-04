"""Store Intelligence Platform - Event Processing System"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import json
from pathlib import Path

from src.database import get_db
from src.normalization import EventNormalizer
from src.analytics import AnalyticsEngine
from src.anomaly import AnomalyDetector

app = FastAPI(
    title="Store Intelligence Platform",
    description="Real-time retail analytics from event streams",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = get_db()
analytics = AnalyticsEngine(db)
anomaly_detector = AnomalyDetector(db)


@app.get("/")
def root():
    return {
        "name": "Store Intelligence Platform",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    events_count = len(db.get_recent_events(limit=1))
    return {
        "status": "healthy",
        "database": "connected",
        "events_loaded": events_count
    }


@app.post("/ingest")
def ingest_sample_data():
    """Ingest sample events from Info folder."""
    info_path = Path("../Info/sample_eventsbe42122.json")
    
    if not info_path.exists():
        raise HTTPException(404, "Sample events file not found. Ensure Info folder is mounted.")
    
    count = 0
    errors = []
    
    with open(info_path) as f:
        for line_num, line in enumerate(f, 1):
            try:
                raw_event = json.loads(line.strip())
                canonical = EventNormalizer.normalize(raw_event)
                
                event_dict = {
                    'event_id': str(canonical.event_id),
                    'event_type': canonical.event_type.value,
                    'timestamp': canonical.timestamp.isoformat(),
                    'store_id': canonical.store_id,
                    'camera_id': canonical.camera_id,
                    'track_id': canonical.track_id,
                    'person': {
                        'gender': canonical.person.gender,
                        'age': canonical.person.age,
                        'age_bucket': canonical.person.age_bucket,
                        'is_staff': canonical.person.is_staff
                    },
                    'zone': {
                        'zone_id': canonical.zone.zone_id,
                        'zone_name': canonical.zone.zone_name,
                        'zone_type': canonical.zone.zone_type,
                        'is_revenue_zone': canonical.zone.is_revenue_zone
                    },
                    'queue': {
                        'wait_seconds': canonical.queue.wait_seconds,
                        'abandoned': canonical.queue.abandoned
                    },
                    'raw_data': raw_event
                }
                
                db.insert_event(event_dict)
                count += 1
            except Exception as e:
                errors.append({"line": line_num, "error": str(e)})
    
    return {
        "status": "success",
        "ingested": count,
        "errors": len(errors),
        "error_details": errors[:5] if errors else []
    }


@app.post("/ingest-cv")
def ingest_cv_events():
    """Ingest CV-generated events from video processing."""
    cv_events_path = Path("../Info/cv_generated_events.jsonl")
    
    if not cv_events_path.exists():
        raise HTTPException(404, "CV events file not found. Run video processing first.")
    
    count = 0
    errors = []
    
    with open(cv_events_path) as f:
        for line_num, line in enumerate(f, 1):
            try:
                raw_event = json.loads(line.strip())
                canonical = EventNormalizer.normalize(raw_event)
                
                event_dict = {
                    'event_id': str(canonical.event_id),
                    'event_type': canonical.event_type.value,
                    'timestamp': canonical.timestamp.isoformat(),
                    'store_id': canonical.store_id,
                    'camera_id': canonical.camera_id,
                    'track_id': canonical.track_id,
                    'person': {
                        'gender': canonical.person.gender,
                        'age': canonical.person.age,
                        'age_bucket': canonical.person.age_bucket,
                        'is_staff': canonical.person.is_staff
                    },
                    'zone': {
                        'zone_id': canonical.zone.zone_id,
                        'zone_name': canonical.zone.zone_name,
                        'zone_type': canonical.zone.zone_type,
                        'is_revenue_zone': canonical.zone.is_revenue_zone
                    },
                    'queue': {
                        'wait_seconds': canonical.queue.wait_seconds,
                        'abandoned': canonical.queue.abandoned
                    },
                    'raw_data': raw_event
                }
                
                db.insert_event(event_dict)
                count += 1
            except Exception as e:
                errors.append({"line": line_num, "error": str(e)})
    
    return {
        "status": "success",
        "source": "computer_vision",
        "ingested": count,
        "errors": len(errors),
        "error_details": errors[:5] if errors else []
    }


@app.get("/events/recent")
def get_recent_events(limit: int = 50, store_id: str = None, event_type: str = None):
    """Get recent events with optional filters."""
    events = db.get_recent_events(limit=limit, store_id=store_id, event_type=event_type)
    return {
        "count": len(events),
        "events": events
    }


@app.get("/analytics/store-summary")
def get_store_summary(store_id: str = "store_1076", hours: int = 2160):
    """Get comprehensive store analytics."""
    summary = analytics.compute_store_summary(store_id, hours)
    return summary


@app.get("/analytics/zones")
def get_zone_analytics(store_id: str = "store_1076", hours: int = 2160):
    """Get zone engagement metrics."""
    zones = analytics.compute_zone_metrics(store_id, hours)
    return {
        "store_id": store_id,
        "period_hours": hours,
        "zones": zones
    }


@app.get("/analytics/queue")
def get_queue_analytics(store_id: str = "store_1076", hours: int = 2160):
    """Get queue performance metrics."""
    metrics = analytics.compute_queue_metrics(store_id, hours)
    return {
        "store_id": store_id,
        "period_hours": hours,
        **metrics
    }


@app.get("/analytics/anomalies")
def get_anomalies(store_id: str = None, severity: str = None, limit: int = 20):
    """Detect and return anomalies."""
    anomalies = anomaly_detector.detect_anomalies(store_id, severity, limit)
    return {
        "count": len(anomalies),
        "anomalies": anomalies
    }


@app.get("/analytics/demographics")
def get_demographics(store_id: str = "store_1076", hours: int = 2160):
    """Get detailed demographic breakdown."""
    demographics = analytics.compute_demographics(store_id, hours)
    return demographics


# Future CCTV Integration Stub
@app.post("/cctv/webhook")
def cctv_webhook(events: List[Dict[str, Any]]):
    """
    Webhook endpoint for future CCTV event ingestion.
    
    External vision systems should POST normalized events here.
    Expected format: List of canonical event objects.
    """
    return {
        "status": "stub",
        "message": "CCTV integration endpoint ready for external vision pipeline",
        "received_events": len(events),
        "note": "Vision processing is handled by upstream systems"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
