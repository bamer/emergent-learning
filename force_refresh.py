#!/usr/bin/env python3
"""
Force dashboard data refresh by creating real-time updates
"""

import requests
import json
import sqlite3
from datetime import datetime


def force_refresh():
    print("🔄 Forcing dashboard data refresh...")

    # 1. Add more test data to ensure visibility
    conn = sqlite3.connect("/home/bamer/.claude/emergent-learning/memory/index.db")
    cursor = conn.cursor()

    # Add a second learning with different type
    cursor.execute(
        """
    INSERT OR IGNORE INTO learnings (type, filepath, title, summary, tags, domain, severity, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    """,
        (
            "heuristic",
            "/test/live_heuristic.md",
            "Live Test: Dashboard Auto-Refresh",
            "Testing real-time data flow from database to frontend dashboard interface.",
            "test,dashboard,realtime,refresh",
            "dashboard_monitoring",
            2,
        ),
    )

    conn.commit()
    conn.close()

    # 2. Ping backend to trigger any WebSocket updates
    try:
        response = requests.get(
            "http://localhost:8888/api/learnings?limit=10", timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend responding with {len(data)} learnings")
            print(f"📊 Latest: {data[-1].get('title', 'Unknown') if data else 'None'}")
        else:
            print(f"❌ Backend error: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")

    # 3. Test frontend data endpoint
    try:
        response = requests.get(
            "http://localhost:3001/api/learnings?limit=5", timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Frontend proxy working with {len(data)} learnings")
            if data:
                print(f"📊 Via frontend: {data[-1].get('title', 'Unknown')}")
        else:
            print(f"❌ Frontend proxy error: {response.status_code}")
    except Exception as e:
        print(f"❌ Frontend connection failed: {e}")

    print("🎯 Dashboard should now show new data!")
    print("🌐 Visit: http://localhost:3001")
    print("💡 If still not visible, try hard refresh (Ctrl+F5)")


if __name__ == "__main__":
    force_refresh()
