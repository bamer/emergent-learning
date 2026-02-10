#!/usr/bin/env python3
"""
ELF Dashboard Backend with Model Cards

Real-time monitoring dashboard with detailed model cards for each agent:
- EventBridge v2 (Level 0 - Infrastructure)
- Watcher (Level 1 - Monitoring)
- Orchestrator (Level 2 - Service Management)
- CEO (Level 3 - Strategic Decisions)

Run: python3 main.py
Access: http://localhost:3011
"""

import json
import asyncio
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import FastAPI
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
    """Serve the dashboard HTML with model cards."""
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ELF Dashboard v2.0 - Model Cards</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0e14; color: #e6edf3; min-height: 100vh; }
        
        /* Header */
        .header { background: linear-gradient(135deg, #161b22 0%, #0d1117 100%); padding: 24px 32px; border-bottom: 1px solid #30363d; }
        .header h1 { font-size: 28px; font-weight: 700; color: #58a6ff; display: flex; align-items: center; gap: 12px; }
        .header .subtitle { color: #8b949e; font-size: 14px; margin-top: 6px; }
        
        /* Hierarchy Flow */
        .hierarchy-flow { display: flex; align-items: center; justify-content: center; gap: 20px; padding: 20px; background: #0d1117; border-bottom: 1px solid #30363d; }
        .hierarchy-item { display: flex; align-items: center; gap: 10px; padding: 12px 20px; background: #161b22; border-radius: 8px; border: 1px solid #30363d; }
        .hierarchy-item .level { font-size: 11px; color: #8b949e; text-transform: uppercase; }
        .hierarchy-item .name { font-weight: 600; font-size: 15px; }
        .hierarchy-arrow { color: #484f58; font-size: 20px; }
        
        /* Model Cards Grid */
        .model-cards { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; padding: 24px 32px; }
        .model-card { background: #161b22; border: 1px solid #30363d; border-radius: 16px; overflow: hidden; }
        .model-card.event-bridge { border-left: 4px solid #58a6ff; }
        .model-card.sentinel { border-left: 4px solid #a371f7; }
        .model-card.orchestrator { border-left: 4px solid #3fb950; }
        .model-card.ceo { border-left: 4px solid #f0883e; }
        
        .model-header { padding: 20px 24px; background: linear-gradient(135deg, #1c2128 0%, #161b22 100%); border-bottom: 1px solid #30363d; }
        .model-header .top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
        .model-header .icon { font-size: 32px; }
        .model-header .status { display: flex; align-items: center; gap: 6px; padding: 6px 12px; background: #238636; border-radius: 20px; font-size: 12px; font-weight: 500; }
        .model-header .status-dot { width: 8px; height: 8px; border-radius: 50%; background: #3fb950; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .model-header .level-badge { font-size: 10px; color: #8b949e; text-transform: uppercase; }
        .model-header h2 { font-size: 20px; font-weight: 600; color: #e6edf3; }
        .model-header .description { font-size: 13px; color: #8b949e; margin-top: 6px; }
        
        .model-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; background: #30363d; }
        .stat-cell { padding: 16px; background: #161b22; text-align: center; }
        .stat-cell .value { font-size: 24px; font-weight: 700; color: #58a6ff; }
        .stat-cell .label { font-size: 11px; color: #8b949e; text-transform: uppercase; margin-top: 4px; }
        .stat-cell.highlight .value { color: #3fb950; }
        .stat-cell.warning .value { color: #d29922; }
        
        .model-details { padding: 20px 24px; border-top: 1px solid #30363d; }
        .detail-section { margin-bottom: 16px; }
        .detail-section:last-child { margin-bottom: 0; }
        .detail-section h3 { font-size: 12px; color: #8b949e; text-transform: uppercase; margin-bottom: 10px; display: flex; align-items: center; gap: 6px; }
        .detail-list { display: flex; flex-wrap: wrap; gap: 8px; }
        .detail-tag { padding: 6px 12px; background: #21262d; border-radius: 6px; font-size: 12px; color: #e6edf3; }
        .detail-tag.active { background: #238636; color: white; }
        
        /* Escalation Flow */
        .escalation-flow { display: flex; align-items: center; gap: 12px; padding: 16px 24px; background: #0d1117; border-top: 1px solid #30363d; }
        .escalation-step { display: flex; align-items: center; gap: 6px; font-size: 12px; }
        .escalation-step .from { color: #8b949e; }
        .escalation-step .arrow { color: #484f58; }
        .escalation-step .to { color: #58a6ff; font-weight: 500; }
        
        /* Footer */
        .footer { text-align: center; padding: 20px; color: #484f58; font-size: 12px; border-top: 1px solid #30363d; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 ELF Dashboard v2.0</h1>
        <div class="subtitle">Emergent Learning Framework - Real-time Agent Monitoring</div>
    </div>
    
    <div class="hierarchy-flow">
        <div class="hierarchy-item">
            <span class="level">Level 0</span>
            <span class="name">EventBridge</span>
        </div>
        <div class="hierarchy-arrow">→</div>
        <div class="hierarchy-item">
            <span class="level">Level 1</span>
            <span class="name">Watcher</span>
        </div>
        <div class="hierarchy-arrow">→</div>
        <div class="hierarchy-item">
            <span class="level">Level 2</span>
            <span class="name">Orchestrator</span>
        </div>
        <div class="hierarchy-arrow">→</div>
        <div class="hierarchy-item">
            <span class="level">Level 3</span>
            <span class="name">CEO</span>
        </div>
    </div>
    
    <div class="model-cards">
        <!-- EventBridge Model Card -->
        <div class="model-card event-bridge">
            <div class="model-header">
                <div class="top">
                    <span class="icon">🌉</span>
                    <span class="status"><span class="status-dot"></span>Running</span>
                </div>
                <span class="level-badge">Level 0 - Infrastructure</span>
                <h2>EventBridge v2.0</h2>
                <div class="description">SSE event routing, session polling, message parsing</div>
            </div>
            <div class="model-stats">
                <div class="stat-cell highlight">
                    <div class="value" id="eb-events">-</div>
                    <div class="label">Total Events</div>
                </div>
                <div class="stat-cell">
                    <div class="value" id="eb-per-min">-</div>
                    <div class="label">Events/min</div>
                </div>
                <div class="stat-cell">
                    <div class="value" id="eb-tools">-</div>
                    <div class="label">Tools Detected</div>
                </div>
            </div>
            <div class="model-details">
                <div class="detail-section">
                    <h3>🔧 Functions</h3>
                    <div class="detail-list">
                        <span class="detail-tag active">SSE Listening</span>
                        <span class="detail-tag active">Session Polling</span>
                        <span class="detail-tag active">Message Parsing</span>
                        <span class="detail-tag active">Tool Detection</span>
                    </div>
                </div>
            </div>
            <div class="escalation-flow">
                <span class="escalation-step"><span class="from">EventBridge</span><span class="arrow">→</span><span class="to">LearningProcessor</span></span>
            </div>
        </div>
        
        <!-- Watcher Model Card -->
        <div class="model-card sentinel">
            <div class="model-header">
                <div class="top">
                    <span class="icon">👁️</span>
                    <span class="status"><span class="status-dot"></span>Active</span>
                </div>
                <span class="level-badge">Level 1 - Monitoring</span>
                <h2>Watcher v3.0</h2>
                <div class="description">Health checks, pattern detection, AI analysis (5min), escalates to Orchestrator</div>
            </div>
            <div class="model-stats">
                <div class="stat-cell">
                    <div class="value" id="w-cycles">-</div>
                    <div class="label">Cycles</div>
                </div>
                <div class="stat-cell highlight">
                    <div class="value" id="w-escalations">-</div>
                    <div class="label">Escalations</div>
                </div>
                <div class="stat-cell">
                    <div class="value" id="w-patterns">-</div>
                    <div class="label">Patterns</div>
                </div>
            </div>
            <div class="model-details">
                <div class="detail-section">
                    <h3>🎯 Responsibilities</h3>
                    <div class="detail-list">
                        <span class="detail-tag active">Service Health</span>
                        <span class="detail-tag active">Pattern Detection</span>
                        <span class="detail-tag active">AI Analysis</span>
                        <span class="detail-tag active">Escalations</span>
                    </div>
                </div>
            </div>
            <div class="escalation-flow">
                <span class="escalation-step"><span class="from">Watcher</span><span class="arrow">→</span><span class="to">Orchestrator</span> (warning/critical)</span>
            </div>
        </div>
        
        <!-- Orchestrator Model Card -->
        <div class="model-card orchestrator">
            <div class="model-header">
                <div class="top">
                    <span class="icon">🧠</span>
                    <span class="status"><span class="status-dot"></span>Active</span>
                </div>
                <span class="level-badge">Level 2 - Service Management</span>
                <h2>Orchestrator</h2>
                <div class="description">Service management, auto-restart, AI analysis, escalates to CEO (critical)</div>
            </div>
            <div class="model-stats">
                <div class="stat-cell">
                    <div class="value" id="o-services">-</div>
                    <div class="label">Services</div>
                </div>
                <div class="stat-cell warning">
                    <div class="value" id="o-restarts">-</div>
                    <div class="label">Restarts</div>
                </div>
                <div class="stat-cell">
                    <div class="value" id="o-missions">-</div>
                    <div class="label">Missions</div>
                </div>
            </div>
            <div class="model-details">
                <div class="detail-section">
                    <h3>🎯 Responsibilities</h3>
                    <div class="detail-list">
                        <span class="detail-tag active">Service Mgmt</span>
                        <span class="detail-tag active">Auto-restart</span>
                        <span class="detail-tag active">AI Decisions</span>
                        <span class="detail-tag active">Escalations</span>
                    </div>
                </div>
            </div>
            <div class="escalation-flow">
                <span class="escalation-step"><span class="from">Orchestrator</span><span class="arrow">→</span><span class="to">CEO</span> (critical only)</span>
            </div>
        </div>
        
        <!-- CEO Model Card -->
        <div class="model-card ceo">
            <div class="model-header">
                <div class="top">
                    <span class="icon">👔</span>
                    <span class="status"><span class="status-dot"></span>Active</span>
                </div>
                <span class="level-badge">Level 3 - Strategic</span>
                <h2>CEO Agent</h2>
                <div class="description">Strategic decisions, critical escalation processing, system oversight</div>
            </div>
            <div class="model-stats">
                <div class="stat-cell">
                    <div class="value" id="c-escalations">-</div>
                    <div class="label">Escalations</div>
                </div>
                <div class="stat-cell highlight">
                    <div class="value" id="c-decisions">-</div>
                    <div class="label">Decisions</div>
                </div>
                <div class="stat-cell">
                    <div class="value" id="c-heuristics">-</div>
                    <div class="label">Heuristics</div>
                </div>
            </div>
            <div class="model-details">
                <div class="detail-section">
                    <h3>🎯 Responsibilities</h3>
                    <div class="detail-list">
                        <span class="detail-tag active">Strategy</span>
                        <span class="detail-tag active">Critical Issues</span>
                        <span class="detail-tag active">Oversight</span>
                        <span class="detail-tag active">Golden Rules</span>
                    </div>
                </div>
            </div>
            <div class="escalation-flow">
                <span class="escalation-step"><span class="from">Top of</span><span class="arrow">→</span><span class="to">Hierarchy</span></span>
            </div>
        </div>
    </div>
    
    <div class="footer">
        ELF Dashboard v2.0 • Real-time monitoring with auto-refresh • Data from SQLite
    </div>
    
    <script>
        async function update() {
            try {
                // EventBridge stats
                const eb = await fetch('/api/v1/event-bridge').r=>r.json());
                document.getElementById('eb-events').textContent = (