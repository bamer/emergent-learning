# OpenELF Troubleshooting Guide

This guide helps diagnose and resolve common issues with the OpenELF plugin system.

## Common Issues and Solutions

### 1. Orchestrator Won't Start

#### Symptom
Orchestrator fails to initialize or crashes immediately.

#### Diagnosis
```bash
# Check if orchestrator is running
ps aux | grep orchestrator

# View recent logs
tail -f /home/bamer/.opencode/emergent-learning/logs/orchestrator.log

# Check OpenCode server status
curl -v http://localhost:4096/health
```

#### Solutions
1. **OpenCode Server Not Running**
   ```bash
   # Start OpenCode server
   opencode serve --port 4096
   
   # Verify server is accessible
   curl http://localhost:4096/health
   ```

2. **Port Conflicts**
   ```bash
   # Check if port 4096 is in use
   netstat -tlnp | grep 4096
   
   # Kill conflicting process or use different port
   kill -9 <PID>
   ```

3. **Missing Dependencies**
   ```bash
   # Check Python dependencies
   pip list | grep -E "(requests|flask|pyyaml)"
   
   # Install missing dependencies
   pip install requests flask pyyaml
   ```

### 2. Agents Fail to Start

#### Symptom
Agents show ERROR status or fail to initialize.

#### Diagnosis
```bash
# Check agent status
curl http://localhost:8889/agents/status

# View detailed logs
grep -A 10 -B 5 "ERROR.*agent" /home/bamer/.opencode/emergent-learning/logs/orchestrator.log
```

#### Solutions
1. **Session Creation Failed**
   ```python
   # Check personality file exists and is readable
   ls -la /home/bamer/.config/opencode/agents/researcher.md
   ls -la /home/bamer/.opencode/emergent-learning/agents/researcher/
   
   # Validate YAML syntax
   python -c "import yaml; yaml.safe_load(open('/home/bamer/.config/opencode/agents/researcher.md').read().split('---')[1])"
   ```

2. **Model Not Available**
   ```bash
   # List available models
   curl http://localhost:4096/models
   
   # Update personality to use available model
   # Edit agent file and change model field
   ```

3. **Permission Issues**
   ```bash
   # Check file permissions
   ls -la /home/bamer/.opencode/emergent-learning/agents/
   ls -la /home/bamer/.config/opencode/agents/
   
   # Fix permissions if needed
   chmod -R 644 /home/bamer/.config/opencode/agents/
   ```

### 3. Agents Not Responding

#### Symptom
Agents appear running but don't respond to calls.

#### Diagnosis
```bash
# Check agent status and session
curl http://localhost:8889/agents/status

# Test basic connectivity
curl -X POST http://localhost:4096/session \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Session"}'
```

#### Solutions
1. **Session Timeout**
   ```bash
   # Increase session timeout in agent definition
   # In orchestrator.py, increase session_timeout value
   session_timeout=7200,  # 2 hours instead of 1
   ```

2. **Busy Agent**
   ```python
   # Check if agent is stuck in BUSY state
   # Restart the agent
   curl -X POST http://localhost:8889/agents/stop/researcher
   curl -X POST http://localhost:8889/agents/start/researcher
   ```

3. **Model Processing Issues**
   ```bash
   # Check model performance
   curl http://localhost:4096/models/performance
   
   # Try different model
   curl -X POST http://localhost:8889/agents/call/researcher \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Test", "model": "opencode/kimi-k2.5-free"}'
   ```

### 4. Personality Loading Issues

#### Symptom
Wrong agent personality loaded or default personality used.

#### Diagnosis
```bash
# Test personality loading
python -c "
import sys
sys.path.append('/home/bamer/.opencode/emergent-learning/agents')
from agent_personality_manager import PersonalityManager
import logging
logging.basicConfig(level=logging.DEBUG)
pm = PersonalityManager()
personality = pm.load_personality('researcher')
print(f'Loaded: {personality.default_model}')
"

# Check file resolution order
python -c "
from pathlib import Path
elf_dir = Path('/home/bamer/.opencode/emergent-learning/agents')
opencode_dir = Path('/home/bamer/.config/opencode/agents')
locations = [
    elf_dir / 'researcher' / 'personality.md',
    elf_dir / 'researcher.md',
    opencode_dir / 'researcher.md'
]
for loc in locations:
    print(f'{loc}: {loc.exists()}')
"
```

#### Solutions
1. **Precedence Configuration**
   ```python
   # In orchestrator.py, adjust precedence
   self.personality_manager = PersonalityManager(
       opencode_precedence=True  # Prioritize OpenCode agents
   )
   ```

2. **File Naming Issues**
   ```bash
   # Ensure correct file names and locations
   ls /home/bamer/.config/opencode/agents/
   ls /home/bamer/.opencode/emergent-learning/agents/
   
   # Rename if necessary
   mv researcher.md researcher/personality.md
   ```

3. **YAML Syntax Errors**
   ```bash
   # Validate YAML syntax
   yamllint /home/bamer/.config/opencode/agents/researcher.md
   
   # Fix common issues like incorrect indentation
   ```

## Performance Issues

### 1. Slow Agent Responses

#### Diagnosis
```bash
# Monitor response times
grep "execution_time\|timeout" /home/bamer/.opencode/emergent-learning/logs/orchestrator.log

# Check system resources
top -p $(pgrep -f orchestrator)
```

#### Solutions
1. **Model Selection**
   ```python
   # Use faster model for simple tasks
   # In agent call, specify faster model
   response = orchestrator.call_agent(
       AgentType.RESEARCHER,
       "Quick code review",
       model="opencode/gpt-5-nano"  # Faster model
   )
   ```

2. **Reduce Timeout**
   ```python
   # Set appropriate timeout for task complexity
   response = orchestrator.call_agent(
       AgentType.RESEARCHER,
       "Simple analysis",
       timeout=60  # Shorter timeout
   )
   ```

3. **Optimize Prompts**
   ```python
   # Use more specific, concise prompts
   good_prompt = "Find security vulnerabilities in this function"
   bad_prompt = "Tell me everything you can about this code"
   ```

### 2. High Memory Usage

#### Diagnosis
```bash
# Monitor memory usage
ps -o pid,vsz,rss,comm -p $(pgrep -f orchestrator)

# Check for memory leaks in logs
grep -i "memory\|leak" /home/bamer/.opencode/emergent-learning/logs/orchestrator.log
```

#### Solutions
1. **Session Cleanup**
   ```python
   # Reduce session timeout
   # In AgentDefinition, decrease session_timeout
   session_timeout=1800,  # 30 minutes instead of 1 hour
   ```

2. **Cache Management**
   ```python
   # Clear personality cache periodically
   # In PersonalityManager, add cache invalidation
   def clear_cache(self):
       self.cache.clear()
   ```

## Database Issues

### 1. Database Lock Errors

#### Symptom
SQLite database locked errors in logs.

#### Diagnosis
```bash
# Check database file
ls -la /home/bamer/.opencode/emergent-learning/memory/index.db

# Check for WAL files
ls -la /home/bamer/.opencode/emergent-learning/memory/index.db-wal
```

#### Solutions
1. **Enable WAL Mode**
   ```sql
   -- In database initialization
   PRAGMA journal_mode=WAL;
   PRAGMA synchronous=NORMAL;
   ```

2. **Database Recovery**
   ```bash
   # Backup current database
   cp /home/bamer/.opencode/emergent-learning/memory/index.db /home/bamer/.opencode/emergent-learning/memory/index.db.backup
   
   # Check database integrity
   sqlite3 /home/bamer/.opencode/emergent-learning/memory/index.db "PRAGMA integrity_check;"
   ```

### 2. Missing Tables

#### Symptom
Table not found errors.

#### Solutions
```bash
# Recreate database schema
python -c "
import sqlite3
conn = sqlite3.connect('/home/bamer/.opencode/emergent-learning/memory/index.db')
conn.executescript('''
CREATE TABLE IF NOT EXISTS event_chronicle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    event_type TEXT,
    source TEXT,
    source_id TEXT,
    status TEXT,
    summary TEXT,
    data TEXT,
    created_at TEXT
);
'')
conn.close()
"
```

## Configuration Issues

### 1. Wrong Directories

#### Symptom
Agents not found or wrong personalities loaded.

#### Solutions
```python
# Verify directory configuration
# In orchestrator.py
personalities_dir = "/home/bamer/.opencode/emergent-learning/agents"
opencode_agents_dir = "/home/bamer/.config/opencode/agents"

# Test paths
import os
assert os.path.exists(personalities_dir), f"Directory not found: {personalities_dir}"
assert os.path.exists(opencode_agents_dir), f"Directory not found: {opencode_agents_dir}"
```

### 2. Environment Variables

#### Symptom
Configuration not taking effect.

#### Solutions
```bash
# Check environment variables
env | grep -i opencode

# Set required variables
export OPENCODE_SERVER_URL=http://localhost:4096
export LOG_LEVEL=DEBUG
```

## Advanced Debugging

### 1. Enable Debug Logging

```python
# In orchestrator.py
import logging
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/home/bamer/.opencode/emergent-learning/logs/orchestrator-debug.log"),
        logging.StreamHandler(),
    ],
)
```

### 2. Manual Testing

```python
# Test individual components
# Test personality manager
from agent_personality_manager import PersonalityManager
pm = PersonalityManager()
personality = pm.load_personality('researcher')
print(personality)

# Test model selection
model = pm.get_optimal_model('researcher', 'Complex analysis task')
print(f"Selected model: {model}")

# Test session creation
import requests
response = requests.post('http://localhost:4096/session', json={'title': 'Test'})
print(response.json())
```

### 3. Health Check Script

```bash
#!/bin/bash
# health_check.sh

echo "=== OpenELF Health Check ==="

# Check OpenCode server
echo "1. Checking OpenCode server..."
if curl -s http://localhost:4096/health > /dev/null; then
    echo "   ✓ OpenCode server running"
else
    echo "   ✗ OpenCode server not accessible"
    exit 1
fi

# Check orchestrator
echo "2. Checking orchestrator..."
if pgrep -f orchestrator > /dev/null; then
    echo "   ✓ Orchestrator running"
else
    echo "   ✗ Orchestrator not running"
fi

# Check agent status
echo "3. Checking agent status..."
if curl -s http://localhost:8889/agents/status | grep -q '"status": "running"'; then
    echo "   ✓ Agents operational"
else
    echo "   ⚠ Agents may have issues"
fi

# Check logs for errors
echo "4. Checking logs for recent errors..."
if tail -50 /home/bamer/.opencode/emergent-learning/logs/orchestrator.log | grep -q "ERROR"; then
    echo "   ⚠ Recent errors found in logs"
    tail -10 /home/bamer/.opencode/emergent-learning/logs/orchestrator.log | grep ERROR
else
    echo "   ✓ No recent errors in logs"
fi

echo "=== Health Check Complete ==="
```

## Preventive Maintenance

### 1. Regular Log Rotation

```bash
# Add to crontab
0 0 * * * find /home/bamer/.opencode/emergent-learning/logs/ -name "*.log" -mtime +7 -delete
```

### 2. Database Maintenance

```bash
# Weekly database optimization
0 2 * * 0 sqlite3 /home/bamer/.opencode/emergent-learning/memory/index.db "VACUUM;"
```

### 3. Session Cleanup

```python
# Add periodic session cleanup to monitoring loop
def _cleanup_expired_sessions(self):
    """Clean up expired sessions."""
    for agent_type, agent in self.agents.items():
        if agent.session_id and agent.status == AgentStatus.STOPPED:
            # Clean up session if agent is stopped
            self._close_agent_session(agent)
            agent.session_id = None
```

This troubleshooting guide should help resolve most common issues with the OpenELF system. For persistent problems, consult the logs and consider reaching out to the community or support channels.