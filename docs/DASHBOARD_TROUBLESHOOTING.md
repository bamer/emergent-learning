# Dashboard Troubleshooting Guide

## Common Issues and Solutions

### "Connection Error" in Monitoring Panels

**Symptom:** Dashboard panels show "Connection Error" even though backend services are running.

#### Root Cause 1: Double API Prefix (Most Common)

The most common cause is a double prefix in API routes.

**Problem:**
```python
# Router file (routers/monitoring.py)
router = APIRouter(prefix="/api/v1", tags=["monitoring"])  # Prefix here

# Main file (main.py)
app.include_router(monitoring_router, prefix="/api/v1")    # AND prefix here
# Result: /api/v1/api/v1/monitoring/... (404 error)
```

**Solution:**
```python
# Router file - NO prefix
router = APIRouter(tags=["monitoring"])

# Main file - prefix only here
app.include_router(monitoring_router, prefix="/api/v1")
# Result: /api/v1/monitoring/... (correct)
```

**How to verify:**
```bash
# Test the endpoint directly
curl http://localhost:8888/api/v1/sentinel/status

# If you get 404, check if double prefix exists
curl -v http://localhost:8888/api/v1/api/v1/monitoring/ollama/status
```

#### Root Cause 2: Wrong Frontend Port

**Problem:**
Frontend component hardcodes wrong port:
```typescript
// WRONG - port 4096 is OpenCode internal server
const baseUrl = apiBaseUrl || 'http://localhost:4096';
```

**Solution:**
```typescript
// CORRECT - port 8888 is dashboard backend
const baseUrl = apiBaseUrl || 'http://localhost:8888';
```

---

### Standard Port Configuration

| Service | Port | URL |
|---------|------|-----|
| Dashboard Backend | 8888 | http://localhost:8888 |
| Dashboard Frontend | 3001 | http://localhost:3001 |
| Semantic Daemon | 5001 | http://localhost:5001 |
| OpenCode Server | 4096 | http://localhost:4096 |

**Important:** Frontend components should use port 8888 (dashboard backend), NOT 4096 (OpenCode server).

---

### Quick Diagnostic Commands

```bash
# 1. Check if backend is running
pgrep -f "uvicorn main:app" && echo "Backend running" || echo "Backend not running"

# 2. Test backend health
curl http://localhost:8888/api/v1/health

# 3. Test specific endpoint
curl http://localhost:8888/api/v1/sentinel/status | jq

# 4. Check all monitoring endpoints
for endpoint in sentinel/status event-bridge/status orchestrator/status; do
  echo "=== $endpoint ==="
  curl -s "http://localhost:8888/api/v1/$endpoint" | jq -r '.status // .running // .error'
done

# 5. Check frontend is running
pgrep -f "vite" && echo "Frontend running" || echo "Frontend not running"

# 6. Check frontend port
curl http://localhost:3001 | head -5
```

---

### Restarting Services

```bash
# Kill and restart backend
pkill -f "uvicorn main:app"
cd emergent-learning/Open_ELF/dashboard-app/backend
python3 -m uvicorn main:app --host 127.0.0.1 --port 8888 --reload

# Kill and restart frontend
pkill -f "vite"
cd emergent-learning/Open_ELF/dashboard-app/frontend
pnpm dev
```

---

### Checking for Double Prefixes in Code

```bash
# Find all routers with prefix defined
grep -r "APIRouter(prefix=" emergent-learning/Open_ELF/dashboard-app/backend/routers/

# Find all include_router calls with prefix
grep -r "include_router.*prefix=" emergent-learning/Open_ELF/dashboard-app/backend/

# If both return results, you likely have a double prefix issue
```

---

### Browser Cache Issues

If changes don't appear after fixing code:

1. **Hard refresh:** `Ctrl+F5` or `Cmd+Shift+R`
2. **Clear cache:** DevTools → Network → Disable cache
3. **Clear localStorage:** DevTools → Application → Local Storage → Clear

---

### Log Locations

| Service | Log File |
|---------|----------|
| Dashboard Backend | `/tmp/backend.log` or `Open_ELF/logs/dashboard.log` |
| Event Bridge | `Open_ELF/logs/event_bridge.log` |
| Sentinel | `Open_ELF/logs/sentinel.log` |
| Semantic Daemon | `Open_ELF/logs/semantic-daemon.log` |

```bash
# Tail all logs
tail -f emergent-learning/Open_ELF/logs/*.log

# Watch for errors
tail -f emergent-learning/Open_ELF/logs/*.log | grep -i error
```

---

## Prevention Checklist

When adding new API endpoints:

- [ ] Router uses `APIRouter(tags=["..."])` without prefix
- [ ] `main.py` uses `app.include_router(router, prefix="/api/v1")`
- [ ] Frontend uses `http://localhost:8888` as base URL
- [ ] Test endpoint with curl before testing in browser
- [ ] Check for 404 errors in browser DevTools Network tab

---

**Last Updated:** 2026-02-19
**Related:** [DEVELOPMENT_GUIDELINES.md](./DEVELOPMENT_GUIDELINES.md)