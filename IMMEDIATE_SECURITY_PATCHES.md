# IMMEDIATE Security Patches for ELF

## CRITICAL - Apply Within 24 Hours

### 1. Fix SQL Injection in knowledge.py

**File:** `/dashboard-app/backend/routers/knowledge.py`

**Replace line 1075:**
```python
# VULNERABLE:
query += f" ORDER BY {sort_map.get(sort_by, 'created_at DESC')}"

# FIX:
allowed_sorts = {
    "recent": "created_at DESC",
    "useful": "usefulness_score DESC", 
    "accessed": "access_count DESC",
    "time": "time_invested_minutes DESC"
}
if sort_by not in allowed_sorts:
    sort_by = "recent"
query += f" ORDER BY {allowed_sorts[sort_by]}"
```

### 2. Add WebSocket Authentication

**File:** `/dashboard-app/backend/main.py`

**Replace lines 650-652:**
```python
# VULNERABLE:
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

# FIX:
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    # Verify authentication token
    if not token or not verify_websocket_token(token):
        await websocket.close(code=4001, reason="Unauthorized")
        return
    await manager.connect(websocket)

# Add this function to main.py:
async def verify_websocket_token(token: str) -> bool:
    """Verify WebSocket authentication token."""
    if not token:
        return False
    
    # Check against session store
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM sessions WHERE token = ? AND expires > ?",
            (token, datetime.now().isoformat())
        )
        return cursor.fetchone() is not None
```

### 3. Fix Path Traversal

**File:** `/src/semantic/daemon.py` (or add validation to any file handling)

**Add to get_db_connection() around line 71:**
```python
def get_db_connection():
    # Validate DB_PATH is within allowed bounds
    try:
        DB_PATH_RESOLVED = DB_PATH.resolve()
        BASE_DIR_RESOLVED = BASE_DIR.resolve()
        DB_PATH_RESOLVED.relative_to(BASE_DIR_RESOLVED)
    except (ValueError, RuntimeError):
        raise SecurityError("Database path outside allowed directory")
    
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn
```

### 4. Fix Command Injection in Shell Scripts

**File:** `/scripts/record-failure.sh` and other shell scripts

**Add validation function at top of each script:**
```bash
# Add after line 89 in record-failure.sh:
validate_sqlite_args() {
    for arg in "$@"; do
        if [[ "$arg" =~ [\;\&\|\<\>\$\`\\] ]]; then
            log "ERROR" "Dangerous characters detected in SQLite arguments"
            return 1
        fi
    done
    return 0
}

# Then modify sqlite_with_retry function:
sqlite_with_retry() {
    local max_attempts=5
    local attempt=1
    
    # Validate arguments first
    validate_sqlite_args "$@" || return 1
    
    while [ $attempt -le $max_attempts ]; do
        if sqlite3 "$@" 2>/dev/null; then
            return 0
        fi
        # ... rest of function
    done
}
```

### 5. Secure Backups

**File:** `/scripts/backup.sh`

**Add after line 109 (after metadata creation):**
```bash
# Verify backup integrity
verify_backup() {
    local backup_dir="$1"
    log_info "Verifying backup integrity..."
    
    # Check SQL dump files are valid
    if [ -f "$backup_dir/index.sql" ]; then
        if ! sqlite3 "$backup_dir/verify.db" < "$backup_dir/index.sql" 2>/dev/null; then
            log_error "index.sql backup is corrupted!"
            return 1
        fi
        rm -f "$backup_dir/verify.db"
        log_success "  - index.sql verified"
    fi
    
    # Check database files are readable
    if [ -f "$backup_dir/index.db" ]; then
        if ! sqlite3 "$backup_dir/index.db" "PRAGMA integrity_check" >/dev/null 2>&1; then
            log_error "index.db backup is corrupted!"
            return 1
        fi
        log_success "  - index.db verified"
    fi
    
    return 0
}

# Call verification
verify_backup "$BACKUP_DIR" || exit 1
log_success "Backup verification completed"
```

## HIGH Priority - Apply Within 1 Week

### 6. Add Rate Limiting

**Install:**
```bash
pip install slowapi
```

**Add to main.py:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
    )

# Add to endpoints:
@app.post("/api/v1/knowledge/search")
@limiter.limit("100/minute")
async def search_knowledge(request: Request, ...):
```

### 7. Add Input Validation

**Create file: dashboard-app/backend/validation.py**
```python
from pydantic import BaseModel, validator
import re

class FilePathValidator(BaseModel):
    file_path: str
    
    @validator('file_path')
    def validate_path(cls, v):
        # Reject path traversal
        if '..' in v or v.startswith('/'):
            raise ValueError('Invalid path')
        
        # Reject dangerous characters
        if re.search(r'[<>:"|?*]', v):
            raise ValueError('Invalid characters in path')
            
        return v

class SortByValidator(BaseModel):
    sort_by: str = 'recent'
    
    @validator('sort_by')
    def validate_sort(cls, v):
        allowed = ['recent', 'useful', 'accessed', 'time']
        if v not in allowed:
            v = 'recent'
        return v
```

## Testing the Patches

### Test SQL Injection Fix:
```bash
# This should now fail gracefully
curl "http://localhost:8000/api/v1/knowledge/search?sort_by=created_at; DROP TABLE heuristics; --"
```

### Test Path Traversal Fix:
```bash
# This should be rejected
curl -X POST http://localhost:8000/api/v1/semantic/index-file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "../../../etc/passwd"}'
```

### Test WebSocket Auth:
```javascript
// This should fail without token
const ws = new WebSocket('ws://localhost:8000/ws');
// Should get 4001 error
```

## Verification Checklist

- [ ] SQL injection attempts return errors
- [ ] Path traversal attempts are blocked  
- [ ] WebSocket requires authentication
- [ ] Backups are verified after creation
- [ ] Rate limiting is active
- [ ] All inputs are validated

**Apply these patches IMMEDIATELY to secure the system!**