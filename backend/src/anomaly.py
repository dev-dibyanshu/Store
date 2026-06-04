"""Anomaly detection engine."""

from typing import List, Dict, Optional
from datetime import datetime, timedelta


class AnomalyDetector:
    """Detects operational anomalies in store events."""
    
    def __init__(self, db):
        self.db = db
        
        # Thresholds
        self.HIGH_ABANDONMENT_THRESHOLD = 0.3  # 30%
        self.LONG_WAIT_THRESHOLD = 60  # 60 seconds
        self.LOW_FOOTFALL_THRESHOLD = 2  # Less than 2 people in 1 hour
    
    def detect_anomalies(
        self, 
        store_id: Optional[str] = None, 
        severity: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Detect anomalies across all stores or specific store."""
        anomalies = []
        
        # Detect high queue abandonment
        anomalies.extend(self._detect_high_abandonment(store_id))
        
        # Detect long wait times
        anomalies.extend(self._detect_long_waits(store_id))
        
        # Detect low footfall
        anomalies.extend(self._detect_low_footfall(store_id))
        
        # Detect unbalanced zones
        anomalies.extend(self._detect_zone_imbalance(store_id))
        
        # Filter by severity if specified
        if severity:
            anomalies = [a for a in anomalies if a['severity'] == severity]
        
        # Sort by timestamp desc
        anomalies.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return anomalies[:limit]
    
    def _detect_high_abandonment(self, store_id: Optional[str]) -> List[Dict]:
        """Detect high queue abandonment rates."""
        conn = self.db._get_conn()
        threshold_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        
        query = """
            SELECT 
                store_id,
                SUM(CASE WHEN abandoned = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as rate,
                COUNT(*) as total
            FROM events
            WHERE event_type IN ('queue_completed', 'queue_abandoned')
              AND timestamp >= ?
        """
        params = [threshold_time]
        
        if store_id:
            query += " AND store_id = ?"
            params.append(store_id)
        
        query += " GROUP BY store_id HAVING rate > ?"
        params.append(self.HIGH_ABANDONMENT_THRESHOLD)
        
        cursor = conn.execute(query, params)
        anomalies = []
        
        for row in cursor.fetchall():
            anomalies.append({
                'type': 'high_abandonment',
                'store_id': row['store_id'],
                'severity': 'high',
                'timestamp': datetime.utcnow().isoformat(),
                'description': f"Queue abandonment rate at {row['rate']:.1%} (threshold: {self.HIGH_ABANDONMENT_THRESHOLD:.0%})",
                'value': row['rate'],
                'threshold': self.HIGH_ABANDONMENT_THRESHOLD,
                'recommendation': 'Add checkout counters or staff during peak hours'
            })
        
        conn.close()
        return anomalies
    
    def _detect_long_waits(self, store_id: Optional[str]) -> List[Dict]:
        """Detect unusually long queue wait times."""
        conn = self.db._get_conn()
        threshold_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        
        query = """
            SELECT 
                store_id,
                MAX(wait_seconds) as max_wait,
                AVG(wait_seconds) as avg_wait,
                COUNT(*) as count
            FROM events
            WHERE event_type IN ('queue_completed', 'queue_abandoned')
              AND timestamp >= ?
              AND wait_seconds > ?
        """
        params = [threshold_time, self.LONG_WAIT_THRESHOLD]
        
        if store_id:
            query += " AND store_id = ?"
            params.append(store_id)
        
        query += " GROUP BY store_id"
        
        cursor = conn.execute(query, params)
        anomalies = []
        
        for row in cursor.fetchall():
            anomalies.append({
                'type': 'long_wait_time',
                'store_id': row['store_id'],
                'severity': 'medium',
                'timestamp': datetime.utcnow().isoformat(),
                'description': f"Average wait time of {row['avg_wait']:.0f}s (max: {row['max_wait']:.0f}s, threshold: {self.LONG_WAIT_THRESHOLD}s)",
                'value': row['avg_wait'],
                'threshold': self.LONG_WAIT_THRESHOLD,
                'recommendation': 'Optimize checkout process or add capacity'
            })
        
        conn.close()
        return anomalies
    
    def _detect_low_footfall(self, store_id: Optional[str]) -> List[Dict]:
        """Detect unusually low footfall."""
        conn = self.db._get_conn()
        threshold_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        
        query = """
            SELECT 
                store_id,
                COUNT(*) as footfall
            FROM events
            WHERE event_type = 'entry'
              AND timestamp >= ?
        """
        params = [threshold_time]
        
        if store_id:
            query += " AND store_id = ?"
            params.append(store_id)
        
        query += " GROUP BY store_id HAVING footfall < ?"
        params.append(self.LOW_FOOTFALL_THRESHOLD)
        
        cursor = conn.execute(query, params)
        anomalies = []
        
        for row in cursor.fetchall():
            anomalies.append({
                'type': 'low_footfall',
                'store_id': row['store_id'],
                'severity': 'low',
                'timestamp': datetime.utcnow().isoformat(),
                'description': f"Only {row['footfall']} visitors in last hour (threshold: {self.LOW_FOOTFALL_THRESHOLD})",
                'value': row['footfall'],
                'threshold': self.LOW_FOOTFALL_THRESHOLD,
                'recommendation': 'Review marketing or store visibility'
            })
        
        conn.close()
        return anomalies
    
    def _detect_zone_imbalance(self, store_id: Optional[str]) -> List[Dict]:
        """Detect zones with no activity in revenue areas."""
        conn = self.db._get_conn()
        threshold_time = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        
        query = """
            SELECT DISTINCT
                store_id,
                zone_id,
                zone_name
            FROM events
            WHERE event_type = 'zone_entered'
              AND is_revenue_zone = 1
              AND timestamp >= ?
        """
        params = [threshold_time]
        
        if store_id:
            query += " AND store_id = ?"
            params.append(store_id)
        
        cursor = conn.execute(query, params)
        active_zones = {(row['store_id'], row['zone_id']) for row in cursor.fetchall()}
        
        # Get all revenue zones
        cursor = conn.execute("""
            SELECT DISTINCT
                store_id,
                zone_id,
                zone_name
            FROM events
            WHERE is_revenue_zone = 1
        """ + (" AND store_id = ?" if store_id else ""), 
        [store_id] if store_id else [])
        
        all_zones = cursor.fetchall()
        anomalies = []
        
        for zone in all_zones:
            if (zone['store_id'], zone['zone_id']) not in active_zones:
                anomalies.append({
                    'type': 'inactive_revenue_zone',
                    'store_id': zone['store_id'],
                    'severity': 'medium',
                    'timestamp': datetime.utcnow().isoformat(),
                    'description': f"Revenue zone '{zone['zone_name']}' had no visitors in 2 hours",
                    'affected_zone': zone['zone_name'],
                    'recommendation': 'Check product placement or zone visibility'
                })
        
        conn.close()
        return anomalies
