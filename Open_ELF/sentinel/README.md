# ELF Watcher - Hybrid Monitoring System

## Overview

The ELF Watcher is a modern continuous monitoring system that implements a hybrid approach combining frequent basic system checks with periodic deep AI analysis. This replaces the original tiered sentinel pattern with a more efficient and practical implementation.

## New Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ELF_WATCHER.PY                           │
│  Hybrid monitoring with intelligent scheduling              │
│  - Basic checks: Every 60 seconds (system health)          │
│  - AI analysis: Every 300 seconds (5 minutes)              │
└─────────────────────────────────────────────────────────────┘
                │               │
                ▼               ▼
    ┌──────────────────┐  ┌──────────────────────┐
    │  BASIC CHECKS    │  │   AI ANALYSIS        │
    │  Fast health     │  │  Deep system         │
    │  monitoring      │  │  understanding       │
    │                  │  │                      │
    └──────────────────┘  └──────────────────────┘
                │               ▲
                │               │
                └───────────────┘
                
       ┌────────────────────────┐
       │   .coordination/       │
       │   - blackboard.json    │
       │   - sentinel-log.md     │
       │   - sentinel-stop       │
       └────────────────────────┘
```

## Key Improvements Over Original Design

### Performance Optimization
- **Reduced Frequency**: Basic checks every 60 seconds instead of 30 seconds
- **Smart Scheduling**: AI analysis every 5 minutes to allow adequate processing time
- **Resource Efficiency**: Single monitoring process instead of tiered orchestration

### Integration Updates
- **Direct EventBridge Communication**: No longer requires external API calls
- **Simplified Architecture**: Single Python script replaces complex launcher system
- **Better Error Handling**: Improved logging and status reporting

### Modern Implementation
- **Hybrid Monitoring**: Combines fast system checks with intelligent AI analysis
- **Self-Contained**: All functionality in one file (`elf_sentinel.py`)
- **Modern Dependencies**: Uses current Python libraries and practices

## Concept

The hybrid approach solves the problem of balancing continuous monitoring efficiency with deep analytical capabilities:

- **Problem**: Constant deep AI analysis is computationally expensive
- **Solution**: Fast system checks for immediate issues + periodic AI analysis for deeper insights
- **Benefit**: Continuous monitoring without resource waste

### Basic Checks (Every 60 seconds)
- Checks system health and service availability
- Detects immediate issues (down services, connection problems)
- Handles simple problems autonomously
- Minimal computational overhead

### AI Analysis (Every 5 minutes)
- Deep system analysis with artificial intelligence
- Pattern recognition and anomaly detection
- Predictive maintenance and optimization suggestions
- Higher computational cost but infrequent execution

### Core Functionality
- **Service Monitoring**: Checks health of dashboard, EventBridge, and other services
- **Self-Healing**: Attempts to fix common issues automatically
- **Escalation**: Sends alerts to EventBridge for critical problems
- **Logging**: Records all activities to coordination log
- **Process Management**: Can restart services when needed

## Quick Start

### 1. Start Watcher

```bash
# From ELF directory
cd /home/bamer/.opencode/emergent-learning
python Open_ELF/sentinel/elf_sentinel.py

# Or use the start script
cd scripts
./start-sentinel.sh
```

### 2. Start in Background

```bash
# Direct background execution
nohup python Open_ELF/sentinel/elf_sentinel.py > /tmp/sentinel.log 2>&1 &

# Or using the start script
./start-sentinel.sh --daemon
```

### 3. Monitor Status

```bash
# View logs
tail -f /tmp/sentinel.log

# Or check coordination log
tail -f .coordination/sentinel-log.md

# Check if running
pgrep -f "elf_sentinel.py"
```

### 4. Stop Watcher

```bash
# Graceful shutdown via stop file
touch .coordination/sentinel-stop

# Or kill process
pkill -f "elf_sentinel.py"
```

## Configuration

The sentinel uses the following configuration constants in `elf_sentinel.py`:

- `BASIC_POLL_INTERVAL = 60` (seconds between basic checks)
- `AI_ANALYSIS_INTERVAL = 300` (seconds between AI analyses)
- `EVENT_BRIDGE_URL = "http://localhost:9998"` (EventBridge endpoint)

These can be modified directly in the source code if needed.

## Integration Points

### EventBridge Communication
- Posts analysis requests to `http://localhost:9998/api/v1/ask`
- Submits escalations to `http://localhost:9998/api/v1/mission`
- Checks EventBridge health at `http://localhost:9998/status`

### Dashboard Integration
- Updates coordination log at `.coordination/sentinel-log.md`
- Process detection via `pgrep -f "elf_sentinel.py"`
- Status information via dashboard backend monitoring API

## Exit Codes

- **Exit 0**: Normal operation, continue monitoring
- **Exit 1**: Escalation requested, handled internally
- **Exit 2**: Error occurred, retry in next cycle

Note: Unlike the original tiered approach, all escalation is handled internally via EventBridge communication.

## Maintenance

### Log Management
Logs are written to `.coordination/sentinel-log.md` in Markdown format:
```
2026-02-07 00:00:00 | STATUS: healthy | NOTES: All systems operational
```

### Monitoring Output
Console output shows current status:
```
🔍 ELF Watcher - 00:00:00
============================================================
🟢 Statut: HEALTHY
🎯 Event Bridge: 🟢 Intégré
📊 Analyse: All systems operational
⏱️  Cycle: 1 (AI Analysis)
⏱️  Prochaine AI: 300s (5m 0s)

🌐 Services:
  dashboard_backend: 🟢
  mission_bridge: 🟢
  sentinel_monitor: 🟢
============================================================
```

## Troubleshooting

### Common Issues

1. **Services showing as down**: Check if backend services are actually running
2. **EventBridge connection issues**: Verify EventBridge is running on port 9998
3. **Analysis failures**: Ensure EventBridge can communicate with OpenCode

### Service Health Check Commands

```bash
# Check EventBridge
curl -s http://localhost:9998/status

# Check Dashboard Backend
curl -s http://localhost:8888/api/v1/health/status

# Check Sentinel Monitor
curl -s http://localhost:9998/api/v1/health/sentinel_monitor
```