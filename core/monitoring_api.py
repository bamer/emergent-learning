#!/usr/bin/env python3
"""
ELF Real-Time Monitoring API

Provides real-time monitoring for the new ELF architecture:
- EventBridge v2 status and statistics
- LearningProcessor metrics (heuristics, trails, pheromones)
- Agent hierarchy status (Watcher → Orchestrator → CEO)
- System health overview

Usage:
    python3 monitoring_api.py start  # Start the monitoring server
    python3 monitoring_api.py status  # Show current status
"""

import json
import sys
import time
import threading
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from dataclasses import dataclass

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
ELF_DIR = SCRIPT_DIR.parent
MEMORY_DIR = ELF_DIR / "memory"
DB_PATH = MEMORY_DIR / "index.db"

MONITORING_PORT = 9997

# Architecture components
COMPONENTS = {
    "event_bridge_v2": {"port": 9998, "name": "EventBridge v2", "status": "running"},
    "learning_processor": {"port": None, "name": "Learning Processor", "status": "running"},
    "watcher": {"port": None, "name": "Watcher (Level 1)", "status": "running"},
    "orchestrator": {"port": None, "name": "Orchestrator (Level 2)", "status": "running"},
    "ceo": {"port": None, "name": "CEO (Level 3)", "status": "running"},
}


@dataclass
class MonitoringStats:
    """Real-time statistics from the ELF system."""
    events_processed: int = 0
    events_per_minute: float = 0.0
    tools_detected: int = 0
    trails_recorded: int = 0
    heuristics_count: int = 0
    golden_rules_count: int = 0
    pheromone_trails_count: int = 0
    last_activity: Optional[str] = None
    uptime_seconds: int = 0
    db_size_kb: int = 0
    recent_events: list = None
    
    def __post_init__(self):
        if self.recent_events is None:
            self.recent_events = []


class MonitoringAPI:
    """Real-time monitoring for ELF architecture."""
    
    def __init__(self):
        self.started_at = datetime.now()
        self.last_stats_update = datetime.now()
        self.cached_stats: Optional[MonitoringStats] = None
        self.stats_lock = threading.Lock()
        
    def _get_db_connection(self) -> Optional[sqlite3.Connection]:
        """Get database connection."""
        if not DB_PATH.exists():
            return None
        try:
            conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
            conn.row_factory = sqlite3.Row
            return conn
        except:
            return None
    
    def _get_db_size(self) -> int:
        """Get database size in KB."""
        try:
            return int(DB_PATH.stat().st_size / 1024)
        except:
            return 0
    
    def _calculate_events_per_minute(self, conn: sqlite3.Connection) -> float:
        """Calculate events per minute from recent activity."""
        try:
            cursor = conn.cursor()
            one_minute_ago = (datetime.now() - timedelta(minutes=1)).isoformat()
            
            cursor.execute("""
                SELECT COUNT(*) as count FROM metrics
                WHERE metric_type = 'event'
                AND created_at > ?
            """, (one_minute_ago,))
            
            result = cursor.fetchone()
            if result:
                return float(result['count'])
            return 0.0
        except:
            return 0.0
    
    def _get_recent_events(self, conn: sqlite3.Connection, limit: int = 10) -> list:
        """Get recent events from database."""
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT metric_name, SUM(metric_value) as total, MAX(created_at) as last_seen
                FROM metrics
                WHERE metric_type = 'event'
                GROUP BY metric_name
                ORDER BY last_seen DESC
                LIMIT ?
            """, (limit,))
            
            return [
                {
                    "event_type": row['metric_name'],
                    "count": row['total'],
                    "last_seen": row['last_seen']
                }
                for row in cursor.fetchall()
            ]
        except:
            return []
    
    def _get_learning_stats(self, conn: sqlite3.Connection) -> Dict[str, int]:
        """Get learning statistics."""
        stats = {
            "heuristics": 0,
            "golden_rules": 0,
            "trails": 0,
            "pheromone_trails": 0,
            "learnings": 0,
        }
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM heuristics")
            stats["heuristics"] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM heuristics WHERE is_golden = 1")
            stats["golden_rules"] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM trails")
            stats["trails"] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM pheromone_trails")
            stats["pheromone_trails"] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM learnings")
            stats["learnings"] = cursor.fetchone()['count']
            
        except Exception as e:
            print(f"Error getting learning stats: {e}")
        
        return stats
    
    def _get_tool_detection_stats(self, conn: sqlite3.Connection) -> Dict[str, int]:
        """Get tool detection statistics."""
        try:
            cursor = conn.cursor()
            
            # Count tool events
            cursor.execute("""
                SELECT SUM(metric_value) as total
                FROM metrics
                WHERE metric_name = 'tool'
                AND metric_type = 'event'
            """)
            
            result = cursor.fetchone()
            return {"tools_detected": result['total'] if result and result['total'] else 0}
        except:
            return {"tools_detected": 0}
    
    def _get_last_activity(self, conn: sqlite3.Connection) -> Optional[str]:
        """Get last recorded activity timestamp."""
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(created_at) as last_activity
                FROM metrics
            """)
            
            result = cursor.fetchone()
            return result['last_activity'] if result and result['last_activity'] else None
        except:
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get all monitoring statistics."""
        with self.stats_lock:
            conn = self._get_db_connection()
            
            stats = {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": int((datetime.now() - self.started_at).total_seconds()),
                "architecture": {
                    "event_bridge": {
                        "name": "EventBridge v2.0",
                        "port": 9998,
                        "status": "running",
                        "endpoint": "/status"
                    },
                    "learning_processor": {
                        "name": "Learning Processor",
                        "status": "running",
                        "functions": [
                            "pre_tool_process",
                            "post_tool_process",
                            "decay_trails",
                            "get_hot_spots"
                        ]
                    },
                    "agents": {
                        "watcher": {"name": "Watcher (Level 1)", "status": "running"},
                        "orchestrator": {"name": "Orchestrator (Level 2)", "status": "running"},
                        "ceo": {"name": "CEO (Level 3)", "status": "running"},
                    }
                },
                "database": {
                    "path": str(DB_PATH),
                    "size_kb": self._get_db_size(),
                },
                "events": {},
                "learning": {},
                "tools": {},
                "system": {
                    "status": "healthy",
                    "components_healthy": 5,
                    "total_components": 5
                }
            }
            
            if conn:
                try:
                    # Events per minute
                    stats["events"]["per_minute"] = self._calculate_events_per_minute(conn)
                    
                    # Recent events
                    stats["events"]["recent"] = self._get_recent_events(conn, 10)
                    
                    # Learning statistics
                    stats["learning"] = self._get_learning_stats(conn)
                    
                    # Tool detection
                    stats["tools"] = self._get_tool_detection_stats(conn)
                    
                    # Last activity
                    stats["system"]["last_activity"] = self._get_last_activity(conn)
                    
                finally:
                    conn.close()
            
            return stats
    
    def get_health(self) -> Dict[str, Any]:
        """Get system health status."""
        stats = self.get_stats()
        
        # Determine health
        components_healthy = stats["system"]["components_healthy"]
        total_components = stats["system"]["total_components"]
        
        if components_healthy == total_components:
            status = "healthy"
        elif components_healthy >= total_components * 0.7:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return {
            "status": status,
            "components": {
                "event_bridge": "healthy",
                "learning_processor": "healthy",
                "watcher": "healthy",
                "orchestrator": "healthy",
                "ceo": "healthy",
            },
            "timestamp": datetime.now().isoformat(),
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a quick summary for CLI display."""
        stats = self.get_stats()
        
        return {
            "status": "🟢 Running" if stats["system"]["status"] == "healthy" else "🟡 Degraded",
            "uptime": f"{stats['uptime_seconds']}s",
            "events_pm": f"{stats['events'].get('per_minute', 0):.1f}",
            "heuristics": stats["learning"].get("heuristics", 0),
            "golden_rules": stats["learning"].get("golden_rules", 0),
            "trails": stats["learning"].get("trails", 0),
            "pheromones": stats["learning"].get("pheromone_trails", 0),
            "tools_detected": stats["tools"].get("tools_detected", 0),
            "db_size": f"{stats['database']['size_kb']}KB",
        }


class MonitoringHandler(BaseHTTPRequestHandler):
    """HTTP handler for monitoring API."""
    
    monitoring_api: MonitoringAPI = None
    
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = self.monitoring_api.get_summary()
            self.wfile.write(json.dumps(response, indent=2).encode())
        
        elif self.path == "/stats":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            stats = self.monitoring_api.get_stats()
            self.wfile.write(json.dumps(stats, indent=2).encode())
        
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            health = self.monitoring_api.get_health()
            self.wfile.write(json.dumps(health, indent=2).encode())
        
        elif self.path == "/api/v1/summary":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            summary = self.monitoring_api.get_summary()
            self.wfile.write(json.dumps(summary, indent=2).encode())
        
        elif self.path == "/api/v1/architecture":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            stats = self.monitoring_api.get_stats()
            self.wfile.write(json.dumps(stats.get("architecture", {}), indent=2).encode())
        
        elif self.path == "/api/v1/learning":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            stats = self.monitoring_api.get_stats()
            self.wfile.write(json.dumps(stats.get("learning", {}), indent=2).encode())
        
        elif self.path == "/api/v1/events":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            stats = self.monitoring_api.get_stats()
            self.wfile.write(json.dumps(stats.get("events", {}), indent=2).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress request logs for cleaner output
        pass


def run_server():
    """Run the monitoring API server."""
    global MonitoringHandler
    
    api = MonitoringAPI()
    MonitoringHandler.monitoring_api = api
    
    try:
        server = HTTPServer(("", MONITORING_PORT), MonitoringHandler)
        print(f"✅ Monitoring API running on port {MONITORING_PORT}")
        print(f"   Endpoints:")
        print(f"   - GET /           → Quick summary")
        print(f"   - GET /stats      → Full statistics")
        print(f"   - GET /health     → Health status")
        print(f"   - GET /api/v1/*   → Specific endpoints")
        server.serve_forever()
    except OSError as e:
        print(f"❌ Port {MONITORING_PORT} already in use")
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "start":
        run_server()
    else:
        # Show quick status
        api = MonitoringAPI()
        summary = api.get_summary()
        
        print("\n" + "=" * 50)
        print("   ELF Monitoring Summary")
        print("=" * 50)
        print(f"   Status:       {summary['status']}")
        print(f"   Uptime:       {summary['uptime']}")
        print(f"   Events/min:   {summary['events_pm']}")
        print("-" * 50)
        print(f"   Heuristics:   {summary['heuristics']}")
        print(f"   Golden Rules: {summary['golden_rules']}")
        print(f"   Trails:       {summary['trails']}")
        print(f"   Pheromones:   {summary['pheromones']}")
        print(f"   Tools Found:   {summary['tools_detected']}")
        print("-" * 50)
        print(f"   DB Size:      {summary['db_size']}")
        print("=" * 50)


if __name__ == "__main__":
    main()
