"""SQLite database for event storage and analytics."""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path("data/store.db")


class Database:
    """Lightweight event database."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()
    
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_tables(self):
        conn = self._get_conn()
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                store_id TEXT NOT NULL,
                camera_id TEXT NOT NULL,
                track_id INTEGER,
                gender TEXT,
                age INTEGER,
                age_bucket TEXT,
                is_staff INTEGER DEFAULT 0,
                zone_id TEXT,
                zone_name TEXT,
                zone_type TEXT,
                is_revenue_zone INTEGER,
                wait_seconds REAL,
                abandoned INTEGER,
                raw_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("CREATE INDEX IF NOT EXISTS idx_store_timestamp ON events(store_id, timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_zone ON events(zone_id)")
        
        conn.commit()
        conn.close()
    
    def insert_event(self, event: Dict[str, Any]) -> str:
        conn = self._get_conn()
        
        conn.execute("""
            INSERT INTO events (
                event_id, event_type, timestamp, store_id, camera_id, track_id,
                gender, age, age_bucket, is_staff,
                zone_id, zone_name, zone_type, is_revenue_zone,
                wait_seconds, abandoned, raw_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event['event_id'],
            event['event_type'],
            event['timestamp'],
            event['store_id'],
            event['camera_id'],
            event.get('track_id'),
            event.get('person', {}).get('gender'),
            event.get('person', {}).get('age'),
            event.get('person', {}).get('age_bucket'),
            1 if event.get('person', {}).get('is_staff') else 0,
            event.get('zone', {}).get('zone_id'),
            event.get('zone', {}).get('zone_name'),
            event.get('zone', {}).get('zone_type'),
            1 if event.get('zone', {}).get('is_revenue_zone') else 0,
            event.get('queue', {}).get('wait_seconds'),
            1 if event.get('queue', {}).get('abandoned') else 0,
            json.dumps(event.get('raw_data', {}))
        ))
        
        conn.commit()
        event_id = event['event_id']
        conn.close()
        
        return event_id
    
    def get_recent_events(
        self, 
        limit: int = 100, 
        store_id: str = None,
        event_type: str = None
    ) -> List[Dict]:
        conn = self._get_conn()
        
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        
        if store_id:
            query += " AND store_id = ?"
            params.append(store_id)
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(query, params)
        events = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return events


_db = None

def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db
