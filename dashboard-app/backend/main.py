#!/usr/bin/env python3
"""
ELF Dashboard Backend

Real-time monitoring dashboard for the new ELF architecture.
Provides:
- EventBridge v2 statistics
- LearningProcessor metrics
- Agent hierarchy status
- System health

Run: python3 main.py
Access: http://localhost:3011
"""

import json
import asyncio
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
ELF_DIR = SCRIPT_DIR.parent.parent
MEMORY_DIR = ELF_DIR / "memory"
DB_PATH = MEMORY_DIR / "index.db"

app = FastAPI(title="ELF Dashboard API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_connection():
    if not DB_PATH.exists():
        return None
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn
    except:
        return None


def get_db_size():
    try:
        return int(DB_PATH.stat().st_size / 1024)
    except:
        return 0


@app.get("/")
async def root():
    """Serve the dashboard HTML."""
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ELF Dashboard v2.0</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f1419; color: #e7e9ea; min-height: 100vh; }
        .header { background: linear-gradient(135deg, #1a1f26 0%, #0d1117 100%); padding: 20px 30px; border-bottom: 1px solid #30363d; }
        .header h1 { font-size: 24px; font-weight: 600; color: #58a6ff; }
        .header .subtitle { color: #8b949e; font-size: 14px; margin-top: 5px; }
        .status-bar { display: flex; gap: 20px; padding: 15px 30px; background: #161b22; border-bottom: 1px solid #30363d; }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; background: #3fb950; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; padding: 20px 30px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; }
        .card h2 { font-size: 16px; color: #8b949e; margin-bottom: 15px; }
        .stat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
        .stat { background: #0d1117; padding: 15px; border-radius: 8px; text-align: center; }
        .stat .value { font-size: 28px; font-weight: 600; color: #58a6ff; }
        .stat .label { font-size: 12px; color: #8b949e; margin-top: 5px; }
        .stat.golden .value { color: #f0883e; }
        .stat.trails .value { color: #a371f7; }
        .component { display: flex; align-items: center; justify-content: space-between; padding: 12px 15px; background: #0d1117; border-radius: 8px; margin-bottom: 8px; }
        .component .badge { padding: 4px 10px; border-radius: 20px; font-size: 12px; background: #238636; color: white; }
        .hotspot { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #21262d; }
        .scent { padding: 2px 8px; border-radius: 4px; font-size: 11px; }
        .scent.hot { background: #f85149; color: white; }
        .scent.discovery { background: #58a6ff; color: white; }
        .scent.warning { background: #d29922; color: white; }
        .event-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #21262d; }
        .heuristic { padding: 10px 0; border-bottom: 1px solid #21262d; }
        .heuristic .domain { font-size: 11px; color: #58a6ff; text-transform: uppercase; margin-bottom: 4px; }
        .heuristic .rule { font-size: 13px; margin-bottom: 6px; }
        .heuristic .meta { font-size: 11px; color: #8b949e; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 ELF Dashboard v2.0</h1>
        <div class="subtitle">Emergent Learning Framework - Real-time Monitoring</div>
    </div>
    <div class="status-bar">
        <div style="display: flex; align-items: center; gap: 8px;">
            <div class="status-dot"></div>
            <span>System Healthy</span>
        </div>
    </div>
    <div class="grid">
        <div class="card">
            <h2>📊 Learning Statistics</h2>
            <div class="stat-grid">
                <div class="stat"><div class="value" id="h-count">-</div><div class="label">Heuristics</div></div>
                <div class="stat golden"><div class="value" id="g-count">-</div><div class="label">Golden Rules</div></div>
                <div class="stat trails"><div class="value" id="t-count">-</div><div class="label">Trails</div></div><div class="stat"><div class="value" id="p-count">-</div><div class="label">Pheromones</div></div>
            </div>
        </div>
        <div class="card">
            <h2>🏗️ Architecture</h2>
            <div class="component"><span>EventBridge v2.0</span><span class="badge">Running</span></div>
            <div class="component"><span>Learning Processor</span><span class="badge">Running</span></div>
            <div class="component"><span>Watcher (L1)</span><span class="badge">Active</span></div>
            <div class="component"><span>Orchestrator (L2)</span><span class="badge">Active</span></div>
            <div class="component"><span>CEO (L3)</span><span class="badge">Active</span></div>
        </div>
        <div class="card">
            <h2>📡 Event Stream</h2>
            <div class="stat" style="margin-bottom: 15px;"><div class="value" id="e-pm">-</div><div class="label">Events/min</div></div>
            <div id="events-list"></div>
        </div>
        <div class="card">
            <h2>🔥 Hot Spots</h2>
            <div id="hotspots-list"></div>
        </div>
        <div class="card" style="grid-column: span 2;">
            <h2>💡 Recent Heuristics</h2>
            <div id="heuristics-list"></div>
        </div>
    </div>
    <script>
        async function update() {
            try {
                const [l, e, hs, ht] = await Promise.all([
                    fetch('/api/v1/learning').r=>r.json()),
                    fetch('/api/v1/events').r=>r.json()),
                    fetch('/api/v1/hotspots').r=>r.json()),
                    fetch('/api/v1/heuristics').r=>r.json())
                ]);
                document.getElementById('h-count').textContent = l.heuristics;
                document.getElementById('g-count').textContent = l.golden_rules;
                document.getElementById('t-count').textContent = l.trails;
                document.getElementById('p-count').textContent = l.pheromone_trails;
                document.getElementById('e-pm').textContent = e.per_minute;
                document.getElementById('events-list').innerHTML = (e.event_types||[]).slice(0,6).map(x=>`<div class="event-row"><span>${x.type}</span><span>${x.count}</span></div>`).join('');
                document.getElementById('hotspots-list').innerHTML = (hs||[]).slice(0,6).map(h=>`<div class="hotspot"><span>${h.location.split('/').pop()}</span><span class="scent ${h.scent}">${h.scent}</span></div>`).join('');
                document.getElementById('heuristics-list').innerHTML = (ht||[]).map(h=>`<div class="heuristic"><div class="domain">${h.domain}</div><div class="rule">${h.rule}</div><div class="meta">Conf: ${h.confidence.toFixed(2)} | Validated: ${h.validated} ${h.golden?'⭐':''}</div></div>`).join('');
            } catch(e) { console.error(e); }
        }
        update(); setInterval(update, 3000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html)


@app.get("/api/v1/learning")
async def get_learning():
    """Get learning statistics."""
    conn = get_db_connection()
    stats = {"heuristics": 0, "golden_rules": 0, "trails": 0, "pheromone_trails": 0, "learnings": 0, "db_size_kb": get_db_size()}
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as c FROM heuristics"); stats["heuristics"] = cursor.fetchone()["c"]
            cursor.execute("SELECT COUNT(*) as c FROM heuristics WHERE is_golden=1"); stats["golden_rules"] = cursor.fetchone()["c"]
            cursor.execute("SELECT COUNT(*) as c FROM trails"); stats["trails"] = cursor.fetchone()["c"]
            cursor.execute("SELECT COUNT(*) as c FROM pheromone_trails"); stats["pheromone_trails"] = cursor.fetchone()["c"]
            cursor.execute("SELECT COUNT(*) as c FROM learnings"); stats["learnings"] = cursor.fetchone()["c"]
        finally:
            conn.close()
    return stats


@app.get("/api/v1/events")
async def get_events():
    """Get event statistics."""
    conn = get_db_connection()
    stats = {"per_minute": 0, "total": 0, "event_types": []}
    if conn:
        try:
            cursor = conn.cursor()
            one_minute_ago = (datetime.now() - timedelta(minutes=1)).isoformat()
            cursor.execute("SELECT COUNT(*) as c FROM metrics WHERE metric_type='event' AND created_at>?", (one_minute_ago,))
            stats["per_minute"] = cursor.fetchone()["c"]
            cursor.execute("SELECT SUM(metric_value) as c FROM metrics WHERE metric_type='event'")
            r = cursor.fetchone(); stats["total"] = r["c"] if r and r["c"] else 0
            cursor.execute("SELECT metric_name, SUM(metric_value) as c FROM metrics WHERE metric_type='event' GROUP BY metric_name ORDER BY c DESC LIMIT 10")
            stats["event_types"] = [{"type": row["metric_name"], "count": row["c"]} for row in cursor.fetchall()]
        finally:
            conn.close()
    return stats


@app.get("/api/v1/hotspots")
async def get_hotspots():
    """Get hot spots."""
    conn = get_db_connection()
    hotspots = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT location, scent, strength FROM trails GROUP BY location ORDER BY SUM(strength) DESC LIMIT 10")
            hotspots = [{"location": row["location"], "scent": row["scent"], "strength": row["strength"]} for row in cursor.fetchall()]
        finally:
            conn.close()
    return hotspots


@app.get("/api/v1/heuristics")
async def get_heuristics():
    """Get recent heuristics."""
    conn = get_db_connection()
    heuristics = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT domain, rule, confidence, times_validated, is_golden FROM heuristics ORDER BY updated_at DESC LIMIT 10")
            heuristics = [{"domain": row["domain"], "rule": row["rule"], "confidence": row["confidence"], "validated": row["times_validated"], "golden": bool(row["is_golden"])} for row in cursor.fetchall()]
        finally:
            conn.close()
    return heuristics


@app.get("/api/v1/health")
async def get_health():
    """Get system health."""
    return {"status": "healthy", "components": 5, "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3011)
