"""Analytics computation engine."""

from typing import Dict, List
from datetime import datetime, timedelta


class AnalyticsEngine:
    """Computes real-time analytics from event data."""
    
    def __init__(self, db):
        self.db = db
    
    def compute_store_summary(self, store_id: str, hours: int = 2160) -> Dict:
        """Compute comprehensive store metrics."""
        threshold = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        conn = self.db._get_conn()
        
        # Footfall - count only from ENTRY cameras to avoid duplicates
        cursor = conn.execute("""
            SELECT COUNT(*) as total
            FROM events
            WHERE store_id = ? AND event_type = 'entry' AND timestamp >= ?
              AND (camera_id LIKE '%ENTRY%' OR camera_id LIKE '%CAM3_ENTRY%')
            LIMIT 1
        """, (store_id, threshold))
        entry_camera_count = cursor.fetchone()['total']
        
        # If no entry cameras, fall back to first camera only
        if entry_camera_count == 0:
            cursor = conn.execute("""
                SELECT COUNT(*) as total
                FROM events
                WHERE store_id = ? AND event_type = 'entry' AND timestamp >= ?
                  AND camera_id = (SELECT camera_id FROM events WHERE store_id = ? LIMIT 1)
            """, (store_id, threshold, store_id))
            footfall = cursor.fetchone()['total']
        else:
            footfall = entry_camera_count
        
        # Unique visitors from entry cameras only
        cursor = conn.execute("""
            SELECT COUNT(DISTINCT track_id) as unique_count
            FROM events
            WHERE store_id = ? AND event_type = 'entry' 
              AND timestamp >= ? AND track_id IS NOT NULL
              AND (camera_id LIKE '%ENTRY%' OR camera_id LIKE '%CAM3_ENTRY%')
        """, (store_id, threshold))
        unique_visitors = cursor.fetchone()['unique_count']
        
        if unique_visitors == 0:
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT track_id) as unique_count
                FROM events
                WHERE store_id = ? AND event_type = 'entry' 
                  AND timestamp >= ? AND track_id IS NOT NULL
                  AND camera_id = (SELECT camera_id FROM events WHERE store_id = ? LIMIT 1)
            """, (store_id, threshold, store_id))
            unique_visitors = cursor.fetchone()['unique_count']
        
        # Demographics from entry cameras
        cursor = conn.execute("""
            SELECT gender, COUNT(*) as count
            FROM events
            WHERE store_id = ? AND event_type = 'entry' 
              AND timestamp >= ? AND gender IS NOT NULL
              AND (camera_id LIKE '%ENTRY%' OR camera_id LIKE '%CAM3_ENTRY%')
            GROUP BY gender
        """, (store_id, threshold))
        demographics = {row['gender']: row['count'] for row in cursor.fetchall()}
        
        # Average age from entry cameras
        cursor = conn.execute("""
            SELECT AVG(age) as avg_age
            FROM events
            WHERE store_id = ? AND event_type = 'entry' 
              AND timestamp >= ? AND age IS NOT NULL
              AND (camera_id LIKE '%ENTRY%' OR camera_id LIKE '%CAM3_ENTRY%')
        """, (store_id, threshold))
        avg_age = cursor.fetchone()['avg_age']
        
        # Queue stats
        cursor = conn.execute("""
            SELECT 
                AVG(wait_seconds) as avg_wait,
                MAX(wait_seconds) as max_wait,
                SUM(CASE WHEN abandoned = 1 THEN 1 ELSE 0 END) as abandonments,
                COUNT(*) as total_queue
            FROM events
            WHERE store_id = ? 
              AND event_type IN ('queue_completed', 'queue_abandoned') 
              AND timestamp >= ?
        """, (store_id, threshold))
        queue = cursor.fetchone()
        
        conn.close()
        
        return {
            'store_id': store_id,
            'period_hours': hours,
            'footfall': footfall,
            'unique_visitors': unique_visitors,
            'demographics': demographics,
            'avg_age': round(avg_age, 1) if avg_age else None,
            'queue': {
                'avg_wait_seconds': round(queue['avg_wait'], 1) if queue['avg_wait'] else 0,
                'max_wait_seconds': round(queue['max_wait'], 1) if queue['max_wait'] else 0,
                'abandonments': queue['abandonments'] or 0,
                'total': queue['total_queue'] or 0,
                'abandonment_rate': (queue['abandonments'] / queue['total_queue']) if queue['total_queue'] else 0
            }
        }
    
    def compute_zone_metrics(self, store_id: str, hours: int = 2160) -> List[Dict]:
        """Compute zone engagement metrics."""
        threshold = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        conn = self.db._get_conn()
        
        cursor = conn.execute("""
            SELECT 
                zone_id,
                zone_name,
                zone_type,
                is_revenue_zone,
                COUNT(*) as visits,
                COUNT(DISTINCT track_id) as unique_visitors
            FROM events
            WHERE store_id = ? 
              AND event_type = 'zone_entered' 
              AND timestamp >= ? 
              AND zone_id IS NOT NULL
            GROUP BY zone_id, zone_name, zone_type, is_revenue_zone
            ORDER BY visits DESC
        """, (store_id, threshold))
        
        zones = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return zones
    
    def compute_queue_metrics(self, store_id: str, hours: int = 2160) -> Dict:
        """Compute queue performance metrics."""
        threshold = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        conn = self.db._get_conn()
        
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN abandoned = 1 THEN 1 ELSE 0 END) as abandoned,
                SUM(CASE WHEN abandoned = 0 OR abandoned IS NULL THEN 1 ELSE 0 END) as completed,
                AVG(wait_seconds) as avg_wait,
                MIN(wait_seconds) as min_wait,
                MAX(wait_seconds) as max_wait
            FROM events
            WHERE store_id = ? 
              AND event_type IN ('queue_completed', 'queue_abandoned')
              AND timestamp >= ?
        """, (store_id, threshold))
        
        result = dict(cursor.fetchone())
        conn.close()
        
        total = result['total'] or 0
        abandoned = result['abandoned'] or 0
        
        return {
            'total_events': total,
            'completed': result['completed'] or 0,
            'abandoned': abandoned,
            'abandonment_rate': (abandoned / total) if total else 0,
            'avg_wait_seconds': round(result['avg_wait'], 1) if result['avg_wait'] else 0,
            'min_wait_seconds': round(result['min_wait'], 1) if result['min_wait'] else 0,
            'max_wait_seconds': round(result['max_wait'], 1) if result['max_wait'] else 0,
        }
    
    def compute_demographics(self, store_id: str, hours: int = 2160) -> Dict:
        """Compute detailed demographic breakdown."""
        threshold = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        conn = self.db._get_conn()
        
        # Gender distribution
        cursor = conn.execute("""
            SELECT gender, COUNT(*) as count
            FROM events
            WHERE store_id = ? AND event_type = 'entry' 
              AND timestamp >= ? AND gender IS NOT NULL
            GROUP BY gender
        """, (store_id, threshold))
        gender_dist = {row['gender']: row['count'] for row in cursor.fetchall()}
        
        # Age buckets
        cursor = conn.execute("""
            SELECT age_bucket, COUNT(*) as count
            FROM events
            WHERE store_id = ? AND event_type = 'entry' 
              AND timestamp >= ? AND age_bucket IS NOT NULL
            GROUP BY age_bucket
            ORDER BY age_bucket
        """, (store_id, threshold))
        age_buckets = [dict(row) for row in cursor.fetchall()]
        
        # Age stats
        cursor = conn.execute("""
            SELECT 
                AVG(age) as avg_age,
                MIN(age) as min_age,
                MAX(age) as max_age
            FROM events
            WHERE store_id = ? AND event_type = 'entry' 
              AND timestamp >= ? AND age IS NOT NULL
        """, (store_id, threshold))
        age_stats = dict(cursor.fetchone())
        
        conn.close()
        
        return {
            'store_id': store_id,
            'period_hours': hours,
            'gender_distribution': gender_dist,
            'age_buckets': age_buckets,
            'age_stats': {
                'average': round(age_stats['avg_age'], 1) if age_stats['avg_age'] else None,
                'min': age_stats['min_age'],
                'max': age_stats['max_age']
            }
        }
