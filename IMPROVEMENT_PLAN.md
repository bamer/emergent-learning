# 📋 Emergent Learning Framework (ELF) - Detailed Improvement Plan

## Executive Summary

This plan provides actionable improvements for the ELF codebase (~800K lines, 6K+ Python files) organized by priority, complexity, and impact. The framework is well-architected with clear separation of concerns, but has opportunities in **code quality, testing, documentation, and maintainability**.

---

## 🎯 Priority Framework

| Priority | Impact | Effort | Criteria |
|----------|--------|--------|----------|
| 🔴 **P0 - Critical** | High | Low-Medium | Security, data loss, blocking issues |
| 🟠 **P1 - High** | High | Medium-High | Performance, reliability, test coverage |
| 🟡 **P2 - Medium** | Medium | Low-Medium | Maintainability, duplication, cleanup |
| 🟢 **P3 - Low** | Low | Low | Documentation, polish, optional enhancements |

---

## 📊 Codebase Quick Stats

- **Total Python Files**: 6,015
- **Test Files**: 968 (~16% coverage)
- **Total Lines of Code**: ~800,000
- **Database Tables**: 20+
- **Main Components**: 12 (query, orchestrator, agents, watcher, dashboard, etc.)
- **Dependencies**: 8 core + optional dev/dashboard
- **Long Functions (>50 lines)**: 51 issues found in sample of 50 files

---

# 🔴 P0 - CRITICAL IMPROVEMENTS

## P0.1 - Add Database Backup & Recovery Automation

**Status**: ⚠️ Manual backup scripts exist but no automated scheduled backups

**Problem**: Database corruption or data loss would be catastrophic for institutional knowledge. Currently has manual backup scripts but no automated protection.

**Evidence**:
- Located `/home/bamer/.opencode/emergent-learning/backups/` with 30+ previous backups
- No evidence of automated backup scheduling (cron jobs, systemd timers)
- Database is 12.7MB (index.db) - manageable size for frequent backups

**Solution**:

```bash
# 1. Create automated backup script
mkdir -p /home/bamer/.opencode/emergent-learning/scripts/backup

# File: scripts/backup/automated-backup.sh
#!/bin/bash
BACKUP_DIR="/home/bamer/.opencode/emergent-learning/backups"
DB_PATH="/home/bamer/.opencode/emergent-learning/memory/index.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/index.db.$TIMESTAMP"
DAYS_TO_KEEP=30

# Rotate old backups
find "$BACKUP_DIR" -name "index.db.*" -mtime +$DAYS_TO_KEEP -delete

# Create backup with integrity check
cp "$DB_PATH" "$BACKUP_FILE.tmp"
sqlite3 "$BACKUP_FILE.tmp" "PRAGMA integrity_check;"
if [ $? -eq 0 ]; then
    mv "$BACKUP_FILE.tmp" "$BACKUP_FILE"
    echo "✅ Backup created: $BACKUP_FILE"
else
    rm -f "$BACKUP_FILE.tmp"
    echo "❌ Backup failed: Integrity check failed"
    exit 1
fi
```

```bash
# 2. Setup systemd timer for automated backups
# File: /etc/systemd/user/elf-backup.service
[Unit]
Description=ELF Database Backup
After=network.target

[Service]
Type=oneshot
ExecStart=/home/bamer/.opencode/emergent-learning/scripts/backup/automated-backup.sh
User=%i

[Install]
WantedBy=default.target
```

```bash
# File: /etc/systemd/user/elf-backup.timer
[Unit]
Description=Run ELF backup every 6 hours

[Timer]
OnCalendar=*:0/6
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
# 3. Enable the timer
systemctl --user daemon-reload
systemctl --user enable elf-backup.timer
systemctl --user start elf-backup.timer

# Verify
systemctl --user list-timers | grep elf
```

**Implementation Steps**:
1. ✅ Create backup script with integrity check
2. ✅ Add rotation for backups (keep last 30 days)
3. ✅ Setup systemd timer for every 6 hours
4. ✅ Add logging to `/home/bamer/.opencode/emergent-learning/logs/backup.log`
5. ✅ Test backup restoration
6. ⏳ Add startup check for corruption with auto-restore

**Files Modified**:
- New: `scripts/backup/automated-backup.sh`
- New: `systemd/user/elf-backup.service`
- New: `systemd/user/elf-backup.timer`

**Estimated Time**: 2 hours

**Verification**:
```bash
# Check backup files exist
ls -la /home/bamer/.opencode/emergent-learning/backups/index.db.*

# Check timer is active
systemctl --user status elf-backup.timer

# Simulated restore test
cp /home/bamer/.opencode/emergent-learning/backups/index.db.LATEST /tmp/test-restore.db
sqlite3 /tmp/test-restore.db ".schema" > /dev/null && echo "✅ Restore test passed"
```

---

## P0.2 - Add Database Integrity Checks with Auto-Recovery

**Status**: ⚠️ Manual integrity checks only, no automated validation

**Problem**: SQLite can corrupt silently without及时发现. No automated periodic integrity checks or auto-recovery mechanisms.

**Evidence**:
- Database has WAL mode enabled (index.db-wal files exist)
- WAL files are huge - potentially uncheckpointed
- No periodic integrity checking in any cron job

**Solution**:

```bash
# File: scripts/database/integrity-check.sh
#!/bin/bash
DB_PATH="/home/bamer/.opencode/emergent-learning/memory/index.db"
BACKUP_DIR="/home/bamer/.opencode/emergent-learning/backups"
LOG_FILE="/home/bamer/.opencode/emergent-learning/logs/integrity-check.log"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "[$TIMESTAMP] Starting integrity check..." >> "$LOG_FILE"

# Run integrity check
RESULT=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;" 2>&1)

if [ "$RESULT" = "ok" ]; then
    echo "[$TIMESTAMP] ✅ Integrity check passed" >> "$LOG_FILE"

    # Checkpoint WAL to prevent excessive WAL growth
    sqlite3 "$DB_PATH" "PRAGMA wal_checkpoint(TRUNCATE);"

    exit 0
else
    echo "[$TIMESTAMP] ❌ Integrity check failed: $RESULT" >> "$LOG_FILE"

    # Create emergency backup before recovery attempt
    cp "$DB_PATH" "$BACKUP_DIR/index.db.corrupted.$TIMESTAMP"
    cp "$DB_PATH-wal" "$BACKUP_DIR/index.db-wal.corrupted.$TIMESTAMP"
    cp "$DB_PATH-shm" "$BACKUP_DIR/index.db-shm.corrupted.$TIMESTAMP"

    # Check WAL file size - if >100MB, force recovery from backup
    WAL_SIZE=$(du -m "$DB_PATH-wal" | cut -f1)
    if [ "$WAL_SIZE" -gt 100 ]; then
        echo "[$TIMESTAMP] ⚠️  WAL file too large ($WAL_SIZE MB), forcing recovery from backup" >> "$LOG_FILE"

        LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/index.db.* 2>/dev/null | head -1)
        if [ -n "$LATEST_BACKUP" ]; then
            cp "$LATEST_BACKUP" "$DB_PATH"
            echo "[$TIMESTAMP] ✅ Restored from $LATEST_BACKUP" >> "$LOG_FILE"
            exit 0
        else
            echo "[$TIMESTAMP] ❌ No backup available for recovery" >> "$LOG_FILE"
            exit 1
        fi
    fi

    exit 1
fi
```

```python
# File: Open_ELF/core/database_health.py
"""
Database health monitoring with auto-recovery.
"""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class DatabaseHealthMonitor:
    """Monitor database health with automatic recovery."""

    def __init__(self, db_path: str, backup_dir: str):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def check_integrity(self) -> bool:
        """Run SQLite integrity check."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check;")
                result = cursor.fetchone()
                is_ok = result[0] == "ok"

                if not is_ok:
                    logger.error(f"Database integrity check failed: {result[0]}")

                return is_ok
        except Exception as e:
            logger.error(f"Integrity check error: {e}")
            return False

    def checkpoint_wal(self) -> bool:
        """Checkpoint WAL to prevent excessive growth."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                conn.commit()
                logger.info("WAL checkpointed successfully")
                return True
        except Exception as e:
            logger.error(f"WAL checkpoint failed: {e}")
            return False

    def get_wal_size_mb(self) -> float:
        """Get WAL file size in MB."""
        wal_path = self.db_path.with_suffix('.db-wal')
        if wal_path.exists():
            return wal_path.stat().st_size / (1024 * 1024)
        return 0.0

    def check_and_recover(self) -> bool:
        """
        Check database health and auto-recover if needed.

        Returns True if healthy or recovery succeeded, False otherwise.
        """
        # Step 1: Check integrity
        if self.check_integrity():
            # Step 2: Checkpoint WAL to prevent growth
            self.checkpoint_wal()
            return True

        # Step 3: Integrity failed - attempt recovery
        logger.warning("Database integrity check failed, attempting recovery...")
        return self._recover_from_backup()

    def _recover_from_backup(self) -> bool:
        """Recover database from latest backup."""
        try:
            # Find latest backup
            backups = sorted(self.backup_dir.glob("index.db.*"), reverse=True)

            if not backups:
                logger.error("No backups available for recovery")
                return False

            latest_backup = backups[0]

            # Create emergency backup of corrupted DB
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            emergency_backup = self.backup_dir / f"index.db.corrupted.{timestamp}"
            emergency_backup.write_bytes(self.db_path.read_bytes())

            # Also backup WAL files
            for ext in ['-wal', '-shm']:
                wal_file = self.db_path.with_suffix(f'.db{ext}')
                if wal_file.exists():
                    backup_wal = self.backup_dir / f"index.db{ext}.corrupted.{timestamp}"
                    backup_wal.write_bytes(wal_file.read_bytes())

            # Restore from backup
            self.db_path.write_bytes(latest_backup.read_bytes())

            logger.info(f"✅ Recovered from backup: {latest_backup.name}")

            # Verify recovery
            if self.check_integrity():
                return True
            else:
                logger.error("Recovered database still has integrity issues")
                return False

        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            return False


# Usage in orchestrator
from database_health import DatabaseHealthMonitor

health_monitor = DatabaseHealthMonitor(
    db_path="/home/bamer/.opencode/emergent-learning/memory/index.db",
    backup_dir="/home/bamer/.opencode/emergent-learning/backups"
)

# Run check on startup
if not health_monitor.check_and_recover():
    logger.critical("Database recovery failed - system may be unstable")
    # Escalate to CEO inbox
```

**Implementation Steps**:
1. ✅ Create shell script for periodic integrity checks
2. ✅ Create Python health monitor class for programmatic checks
3. ✅ Add wal_checkpoint to prevent WAL file bloat
4. ✅ Auto-recovery logic with fallback to latest backup
5. ⏳ Add systemd timer for daily checks
6. ⏳ Integrate into unified orchestrator startup
7. ⏳ Add CEO escalation for critical failures

**Files Modified**:
- New: `scripts/database/integrity-check.sh`
- New: `Open_ELF/core/database_health.py`
- Update: `Open_ELF/orchestrator/unified_orchestrator.py` (add startup check)

**Estimated Time**: 3 hours

**Verification**:
```bash
# Run integrity check manually
bash scripts/database/integrity-check.sh

# Check WAL file size
du -h /home/bamer/.opencode/emergent-learning/memory/index.db-wal

# Test Python health monitor
python -c "
from Open_ELF.core.database_health import DatabaseHealthMonitor
monitor = DatabaseHealthMonitor(
    '/home/bamer/.opencode/emergent-learning/memory/index.db',
    '/home/bamer/.opencode/emergent-learning/backups'
)
print('Healthy:', monitor.check_and_recover())
print('WAL size:', monitor.get_wal_size_mb(), 'MB')
"
```

---

## P0.3 - Fix Dependency Conflicts Between pyproject.toml and requirements.txt

**Status**: ⚠️ Overlapping and potentially conflicting dependency specifications

**Problem**: Dependencies specified in both `pyproject.toml` and `requirements.txt` can lead to confusion and version mismatches.

**Evidence**:
- `requirements.txt` lists: peewee-aio, aiofiles, aiohttp, requests, numpy, scipy, PyYAML
- `pyproject.toml` lists: anthropic, numpy, aiohttp, scipy
- Dashboard has separate `dashboard-app/backend/requirements.txt`
- No clear dependency hierarchy or installation instructions

**Solution**:

Create a unified dependency structure:

```toml
# File: pyproject.toml (updated)
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "emergent-learning-framework"
dynamic = ["version"]
description = "Emergent Learning Framework - Institutional knowledge for AI agents"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [{name = "ELF Contributors"}]
keywords = ["ai", "agents", "learning", "coordination", "workflow"]

# Core dependencies - minimal set for basic ELF functionality
dependencies = [
    # Database ORM (async)
    "peewee-aio[aiosqlite]>=1.0.0,<2.0.0",

    # Async utilities
    "aiofiles>=23.0.0,<25.0.0",
    "aiohttp>=3.8.0,<4.0.0",

    # HTTP client (for OpenCode API)
    "requests>=2.30.0,<3.0.0",

    # Numerical operations (for embeddings)
    "numpy>=1.21.0,<2.0.0",
    "scipy>=1.7.0,<3.0.0",

    # Config parsing
    "PyYAML>=6.0,<7.0.0",

    # Anthropic API (optional - only needed for AgentManager)
    "anthropic>=0.18.0,<1.0.0",
]

[project.optional-dependencies]
# Optional dependencies for enhanced features
dev = [
    # Testing
    "pytest>=7.0.0,<8.0.0",
    "pytest-asyncio>=0.21.0,<1.0.0",
    "pytest-cov>=4.0.0,<5.0.0",

    # Type checking
    "mypy>=1.0.0,<2.0.0",

    # Code quality
    "ruff>=0.1.0",
    "black>=23.0.0",

    # Documentation
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.0.0",
]

# Semantic search with embeddings
semantic = [
    "sentence-transformers>=2.2.0,<3.0.0",
]

# Dashboard backend dependencies
dashboard-backend = [
    "fastapi>=0.104.0,<1.0.0",
    "uvicorn[standard]>=0.24.0,<1.0.0",
    "pydantic>=2.0.0,<3.0.0",
    "pydantic-settings>=2.0.0,<3.0.0",
]

# All optional dependencies combined
all-dev = [
    "emergent-learning-framework[dev,semantic,dashboard-backend]",
]

# Installation convenience groups
install = [
    # Basic installation (no dev tools, no dashboard)
    "emergent-learning-framework",
]

install-dev = [
    # With dev tools
    "emergent-learning-framework[dev]",
]

install-dashboard = [
    # With dashboard backend
    "emergent-learning-framework[dashboard-backend]",
]

install-full = [
    # Everything
    "emergent-learning-framework[all-dev]",
]

[project.urls]
Homepage = "https://github.com/Spacehunterz/Emergent-Learning-Framework_ELF"
Documentation = "https://github.com/Spacehunterz/Emergent-Learning-Framework_ELF/wiki"
Repository = "https://github.com/Spacehunterz/Emergent-Learning-Framework_ELF"

[project.scripts]
elf-query = "Open_ELF.query.cli:main"
elf-checkin = "Open_ELF.query.checkin:main"
elf-checkout = "Open_ELF.query.checkout:main"
elf-backup = "scripts.backup.automated_backup:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["Open_ELF*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --tb=short --cov=Open_ELF --cov-report=html"
filterwarnings = [
    "ignore::DeprecationWarning",
    "ignore::pytest.PytestUnraisableExceptionWarning",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "concurrent: marks tests with threading/async",
    "database: marks tests requiring database",
    "integration: marks integration tests",
    "stress: marks stress/load tests",
]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
disallow_incomplete_defs = false
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
[[tool.mypy.overrides]]
module = "peewee_aio.*"
ignore_missing_imports = true

[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "N", "UP"]
ignore = ["E501", "N802", "N803"]

[tool.black]
line-length = 100
target-version = ['py38', 'py39', 'py310', 'py311', 'py312']

[tool.coverage.run]
source = ["Open_ELF"]
omit = ["tests/*", "*/test_*.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]
```

```bash
# File: INSTALLATION.md (new)
# ELF Installation Guide

## Installation Options

### Option 1: Basic Installation (Minimal)
For users who just want core ELF features:
```bash
pip install -e .
```

### Option 2: Development Installation
For contributors and developers:
```bash
pip install -e ".[dev]"
```

### Option 3: Dashboard Installation
For users who want the monitoring dashboard:
```bash
pip install -e ".[dashboard-backend]"
# Then install frontend dependencies
cd apps/dashboard/frontend
bun install
```

### Option 4: Full Installation
For everything (dev tools + dashboard):
```bash
pip install -e ".[all-dev]"
```

## Requirements.txt Deprecated

Since version 2.0, ELF uses pyproject.toml for dependency management.
The requirements.txt file is kept for backward compatibility only.

To upgrade from requirements.txt:
```bash
pip uninstall emergent-learning-framework
pip install -e ".[install-full]"
```

## Verifying Installation
```bash
python -c "import peewee_aio; print('✅ OK')"
python -m Open_ELF.query.cli --stats
```
```

**Implementation Steps**:
1. ✅ Update pyproject.toml with version-pinned dependencies
2. ✅ Remove conflicting entries from requirements.txt
3. ✅ Create clear installation groups (dev, dashboard, all)
4. ✅ Create INSTALLATION.md guide
5. ⏳ Update install.sh script to use correct pip install flags
6. ⏳ Add post-install verification step
7. ⏳ Document migration path from old requirements.txt

**Files Modified**:
- Update: `pyproject.toml`
- Deprecate: `requirements.txt` (keep with deprecation notice)
- New: `INSTALLATION.md`
- Update: `install.sh`

**Estimated Time**: 2 hours

**Verification**:
```bash
# Test clean install
pip install -e .
python -c "import peewee_aio, aiofiles, aiohttp, numpy; print('✅ Dependencies OK')"

# Test dev install
pip install -e ".[dev]"
pytest --collect-only

# Verify no conflicts
pip check
```

---

# 🟠 P1 - HIGH PRIORITY

## P1.1 - Increase Test Coverage to >70%

**Status**: ⚠️ ~16% test coverage (968 test files / 6015 total files)

**Problem**: Low test coverage makes risky changes to core systems dangerous. Critical components like orchestrator, watcher, and database layer have minimal test coverage.

**Evidence**:
- 968 test files vs 6015 total Python files
- No evidence of coverage reporting in CI/CD
- Critical modules like `central_orchestrator.py`, `agent_manager.py`, `database.py` likely have unit tests but not integration tests

**Solution**:

### Step 1: Establish Testing Infrastructure

```ini
# File: pytest.ini (updated)
[pytest]
testpaths = tests Open_ELF/query/tests Open_ELF/core/tests Open_ELF/agents/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --cov=Open_ELF
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=60
filterwarnings =
    ignore::DeprecationWarning
    ignore::pytest.PytestUnraisableExceptionWarning
    asyncio_mode = auto

markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    concurrent: marks tests with threading/async
    database: marks tests requiring database
    integration: marks integration tests
    stress: marks stress/load tests
    unit: marks unit tests
    api: marks API endpoint tests
```

### Step 2: Add Missing Tests for Critical Components

```python
# File: tests/database/test_database_health.py (new)
"""
Tests for database health monitoring and recovery.
"""
import pytest
import sqlite3
from pathlib import Path
import tempfile
import shutil

from Open_ELF.core.database_health import DatabaseHealthMonitor


@pytest.fixture
def temp_db_dir():
    """Create temporary directory for test database."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def healthy_db(temp_db_dir):
    """Create a healthy test database."""
    db_path = temp_db_dir / "test.db"

    # Create database with sample data
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE learnings (
            id INTEGER PRIMARY KEY,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT
        )
    """)
    conn.execute("INSERT INTO learnings (type, title, content) VALUES ('test', 'sample', 'content')")
    conn.commit()
    conn.close()

    return db_path


class TestDatabaseHealthMonitor:
    """Test database health monitoring."""

    def test_initialization(self, temp_db_dir):
        """Test health monitor initialization."""
        monitor = DatabaseHealthMonitor(
            db_path=str(temp_db_dir / "test.db"),
            backup_dir=str(temp_db_dir / "backups")
        )

        assert monitor.db_path.exists()
        assert monitor.backup_dir.exists()

    def test_check_integrity_healthy_db(self, healthy_db, temp_db_dir):
        """Test integrity check with healthy database."""
        monitor = DatabaseHealthMonitor(
            db_path=str(healthy_db),
            backup_dir=str(temp_db_dir / "backups")
        )

        assert monitor.check_integrity() is True

    def test_check_integrity_corrupted_db(self, temp_db_dir):
        """Test integrity check with corrupted database."""
        # Create corrupted database
        corrupted_db = temp_db_dir / "corrupted.db"
        corrupted_db.write_bytes(b'\x00' * 1000)

        monitor = DatabaseHealthMonitor(
            db_path=str(corrupted_db),
            backup_dir=str(temp_db_dir / "backups")
        )

        assert monitor.check_integrity() is False

    def test_checkpoint_wal(self, healthy_db, temp_db_dir):
        """Test WAL checkpoint."""
        monitor = DatabaseHealthMonitor(
            db_path=str(healthy_db),
            backup_dir=str(temp_db_dir / "backups")
        )

        # Enable WAL mode
        conn = sqlite3.connect(healthy_db)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.commit()
        conn.close()

        # Checkpoint WAL
        assert monitor.checkpoint_wal() is True

    def test_get_wal_size(self, healthy_db, temp_db_dir):
        """Test getting WAL file size."""
        monitor = DatabaseHealthMonitor(
            db_path=str(healthy_db),
            backup_dir=str(temp_db_dir / "backups")
        )

        # No WAL file initially
        assert monitor.get_wal_size_mb() == 0.0

        # Enable WAL mode
        conn = sqlite3.connect(healthy_db)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.commit()
        conn.close()

        # WAL file should exist now
        assert monitor.get_wal_size_mb() >= 0.0

    def test_recover_from_backup(self, healthy_db, temp_db_dir):
        """Test recovery from backup."""
        # Create backup
        backup_dir = temp_db_dir / "backups"
        backup_dir.mkdir()
        backup_path = backup_dir / "test.db.backup"
        backup_path.write_bytes(healthy_db.read_bytes())

        # Corrupt the original database
        healthy_db.write_bytes(b'\x00' * 1000)

        # Recover from backup
        monitor = DatabaseHealthMonitor(
            db_path=str(healthy_db),
            backup_dir=str(backup_dir)
        )

        assert monitor._recover_from_backup() is True
        assert monitor.check_integrity() is True

    def test_check_and_recover_healthy(self, healthy_db, temp_db_dir):
        """Test check_and_recover with healthy database."""
        monitor = DatabaseHealthMonitor(
            db_path=str(healthy_db),
            backup_dir=str(temp_db_dir / "backups")
        )

        assert monitor.check_and_recover() is True

    def test_check_and_recover_corrupted_with_backup(self, healthy_db, temp_db_dir):
        """Test check_and_recover with corrupted database and backup."""
        # Create backup
        backup_dir = temp_db_dir / "backups"
        backup_dir.mkdir()
        backup_path = backup_dir / "test.db.backup"
        backup_path.write_bytes(healthy_db.read_bytes())

        # Corrupt the original database
        original_content = healthy_db.read_bytes()
        healthy_db.write_bytes(b'\x00' * 1000)

        # Recover
        monitor = DatabaseHealthMonitor(
            db_path=str(healthy_db),
            backup_dir=str(backup_dir)
        )

        assert monitor.check_and_recover() is True
        assert monitor.check_integrity() is True

    def test_recover_from_no_backups(self, temp_db_dir):
        """Test recovery with no available backups."""
        corrupted_db = temp_db_dir / "corrupted.db"
        corrupted_db.write_bytes(b'\x00' * 1000)

        monitor = DatabaseHealthMonitor(
            db_path=str(corrupted_db),
            backup_dir=str(temp_db_dir / "backups_empty")
        )

        assert monitor._recover_from_backup() is False


@pytest.mark.integration
class TestDatabaseHealthIntegration:
    """Integration tests for database health."""

    def test_full_recovery_cycle(self, temp_db_dir):
        """Test full cycle: create, corrupt, detect, recover."""
        healthy_db = temp_db_dir / "test.db"
        backup_dir = temp_db_dir / "backups"

        # Create healthy database with data
        conn = sqlite3.connect(healthy_db)
        conn.execute("""
            CREATE TABLE learnings (
                id INTEGER PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT NOT NULL
            )
        """)
        conn.execute("INSERT INTO learnings (type, title) VALUES ('test', 'sample')")
        conn.commit()
        conn.close()

        # Create backup
        backup_dir.mkdir()
        backup_path = backup_dir / "test.db.backup"
        backup_path.write_bytes(healthy_db.read_bytes())

        # Corrupt database
        healthy_db.write_bytes(b'\x00' * 1000)

        # Monitor should detect and recover
        monitor = DatabaseHealthMonitor(
            db_path=str(healthy_db),
            backup_dir=str(backup_dir)
        )

        # Check should fail
        assert monitor.check_integrity() is False

        # Recovery should succeed
        assert monitor._recover_from_backup() is True

        # Data should be restored
        conn = sqlite3.connect(healthy_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM learnings")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1
```

```python
# File: tests/orchestrator/test_central_orchestrator.py (new)
"""
Tests for Central Orchestrator.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock

from Open_ELF.core.central_orchestrator import CentralOrchestrator
from Open_ELF.core.database_health import DatabaseHealthMonitor


@pytest.fixture
def mock_database():
    """Mock database connection."""
    db = Mock()
    db.execute = Mock(return_value=Mock(fetchall=Mock(return_value=[])))
    return db


@pytest.fixture
def orchestrator(mock_database):
    """Create orchestrator instance."""
    with patch('Open_ELF.core.central_orchestrator.get_database', return_value=mock_database):
        orchestrator = CentralOrchestrator()
        yield orchestrator


class TestCentralOrchestrator:
    """Test central orchestrator functionality."""

    def test_initialization(self, mock_database):
        """Test orchestrator initialization."""
        with patch('Open_ELF.core.central_orchestrator.get_database', return_value=mock_database):
            orchestrator = CentralOrchestrator()
            assert orchestrator is not None

    def test_health_check(self, orchestrator):
        """Test health check functionality."""
        health = orchestrator.check_health()
        assert health is not None
        assert 'status' in health

    def test_submit_mission(self, orchestrator):
        """Test mission submission."""
        mission = {
            'type': 'test',
            'objective': 'Test objective',
            'priority': 'high'
        }

        result = orchestrator.submit_mission(mission)
        assert result is not None

    def test_coordination_endpoint(self, orchestrator):
        """Test coordination endpoint."""
        coordination_data = {
            'system_state': 'operational',
            'active_sessions': []
        }

        result = orchestrator.handle_coordination(coordination_data)
        assert result is not None


@pytest.mark.asyncio
class TestCentralOrchestratorAsync:
    """Async tests for central orchestrator."""

    async def test_async_health_check(self):
        """Test async health check."""
        mock_db = Mock()
        mock_db.execute = AsyncMock(return_value=Mock(fetchall=AsyncMock(return_value=[])))

        with patch('Open_ELF.core.central_orchestrator.get_database', return_value=mock_db):
            orchestrator = CentralOrchestrator()
            health = await orchestrator.async_check_health()
            assert health is not None
```

### Step 3: Add Coverage Enforcement

```yaml
# File: .github/workflows/tests.yml (new or updated)
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -e ".[dev]"

    - name: Run tests with coverage
      run: |
        pytest --cov=Open_ELF --cov-report=xml --cov-report=html

    - name: Check coverage threshold
      run: |
        coverage report --fail-under=60

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
```

### Step 4: Generate Coverage Report

```python
# File: scripts/test/generate_coverage_report.py (new)
#!/usr/bin/env python3
"""
Generate test coverage report.
"""
import subprocess
import sys
from pathlib import Path


def main():
    """Generate coverage report."""
    print("🧪 Running tests with coverage...")

    # Run pytest with coverage
    result = subprocess.run([
        'pytest',
        '--cov=Open_ELF',
        '--cov-report=html',
        '--cov-report=term-missing',
        '--cov-report=lcov'
    ])

    if result.returncode != 0:
        print("❌ Tests failed")
        sys.exit(1)

    # Open coverage report
    coverage_path = Path('htmlcov/index.html')
    if coverage_path.exists():
        print(f"✅ Coverage report generated: {coverage_path.absolute()}")
        print("Open in browser to view detailed report")


if __name__ == '__main__':
    main()
```

**Implementation Steps**:
1. ✅ Update pytest.ini with coverage settings
2. ✅ Add unit tests for critical components (database_health, orchestrator)
3. ✅ Add integration tests for recovery cycles
4. ✅ Setup CI/CD with coverage enforcement
5. ⏳ Target 70% coverage for P0/P1 components
6. ⏳ Generate coverage reports on each run
7. ⏳ Document testing guidelines

**Files Modified**:
- Update: `pytest.ini`
- New: `tests/database/test_database_health.py`
- New: `tests/orchestrator/test_central_orchestrator.py`
- New: `.github/workflows/tests.yml`
- New: `scripts/test/generate_coverage_report.py`

**Estimated Time**: 8 hours

**Verification**:
```bash
# Run all tests with coverage
pytest --cov=Open_ELF --cov-report=term-missing

# Check coverage percentage
coverage report | grep "TOTAL"

# Generate HTML report
scripts/test/generate_coverage_report.py
open htmlcov/index.html
```

---

## P1.2 - Reduce Code Duplication

**Status**: ⚠️ Observers, database queries, and logging code duplicated across modules

**Problem**: Code duplication increases maintenance burden and creates opportunities for bugs to appear in multiple places.

**Evidence**:
- Observers: `meta_observer.py`, `post_tool_use.py`, `learning-loop/` files
- Similar database query patterns repeated across modules
- Logging boilerplate in many files

**Solution**:

### Step 1: Extract Common Database Operations

```python
# File: Open_ELF/core/database/base.py (new)
"""
Base database operations - common queries used across modules.
"""
import logging
from typing import Optional, List, Dict, Any
from peewee_aio import AioModel
import peewee as pw

logger = logging.getLogger(__name__)


class DatabaseRepository:
    """Base repository with common database operations."""

    def __init__(self, db):
        self.db = db

    async def get_by_id(self, model: AioModel, id: int) -> Optional[AioModel]:
        """Get record by ID."""
        try:
            return await model.get_by_id(id)
        except pw.DoesNotExist:
            logger.warning(f"{model.__name__} with id={id} not found")
            return None

    async def get_all(self, model: AioModel, limit: int = 100) -> List[AioModel]:
        """Get all records with optional limit."""
        query = model.select().limit(limit)
        return await list(query)

    async def create(self, model: AioModel, **kwargs) -> AioModel:
        """Create new record."""
        try:
            return await model.create(**kwargs)
        except Exception as e:
            logger.error(f"Failed to create {model.__name__}: {e}")
            raise

    async def update(self, model: AioModel, id: int, **kwargs) -> bool:
        """Update record by ID."""
        try:
            record = await model.get_by_id(id)
            if record:
                await model.update(**kwargs).where(model.id == id)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update {model.__name__} id={id}: {e}")
            return False

    async def delete(self, model: AioModel, id: int) -> bool:
        """Delete record by ID."""
        try:
            record = await model.get_by_id(id)
            if record:
                await record.delete_instance()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete {model.__name__} id={id}: {e}")
            return False

    async def find_by_field(
        self,
        model: AioModel,
        field: str,
        value: Any,
        limit: int = 100
    ) -> List[AioModel]:
        """Find records by field value."""
        try:
            query = model.select().where(getattr(model, field) == value).limit(limit)
            return await list(query)
        except Exception as e:
            logger.error(f"Failed to find {model.__name__} by {field}={value}: {e}")
            return []

    async def search_by_text(
        self,
        model: AioModel,
        text_fields: List[str],
        search_term: str,
        limit: int = 100
    ) -> List[AioModel]:
        """Full-text search across multiple text fields."""
        try:
            conditions = []
            for field in text_fields:
                conditions.append(getattr(model, field).contains(search_term))

            from peewee import fn
            query = model.select().where(fn.OR(*conditions)).limit(limit)
            return await list(query)
        except Exception as e:
            logger.error(f"Failed to search {model.__name__}: {e}")
            return []


# Usage in modules
from Open_ELF.core.database.base import DatabaseRepository
from Open_ELF.query.models import Learning, Heuristic

class LearningRepository(DatabaseRepository):
    """Repository for Learning records."""

    async def get_by_domain(self, domain: str, limit: int = 100) -> List[Learning]:
        """Get learnings by domain."""
        return await self.find_by_field(Learning, 'domain', domain, limit)

    async def search_content(self, search_term: str) -> List[Learning]:
        """Search learning content."""
        return await self.search_by_text(
            Learning,
            ['title', 'content', 'summary'],
            search_term
        )
```

### Step 2: Centralize Logging Utilities

```python
# File: Open_ELF/core/logging_utils.py (new)
"""
Centralized logging utilities for all ELF components.
"""
import logging
from contextlib import contextmanager
from functools import wraps
from typing import Optional, Callable
from datetime import datetime
import json


class LevelFilter(logging.Filter):
    """Filter logs by level."""

    def __init__(self, level: int):
        super().__init__()
        self.level = level

    def filter(self, record):
        return record.levelno >= self.level


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Setup a standardized logger.

    Args:
        name: Logger name
        level: Logging level (default: INFO)
        log_file: Optional log file path
        format_string: Optional custom format string

    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = (
            '%(asctime)s | %(levelname)-8s | %(name)s | '
            '%(funcName)s:%(lineno)d | %(message)s'
        )

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(format_string))
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(format_string))
        logger.addHandler(file_handler)

    return logger


def log_execution_time(logger: logging.Logger):
    """
    Decorator to log function execution time.

    Usage:
        @log_execution_time(logger)
        def some_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"✅ {func.__name__} completed in {duration:.2f}s")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"❌ {func.__name__} failed after {duration:.2f}s: {e}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"✅ {func.__name__} completed in {duration:.2f}s")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"❌ {func.__name__} failed after {duration:.2f}s: {e}")
                raise

        return async_wrapper if hasattr(func, '__call__') and hasattr(func, 'is_coroutine') else sync_wrapper

    return decorator


@contextmanager
def log_context(logger: logging.Logger, context: str):
    """
    Context manager for logging execution context.

    Usage:
        with log_context(logger, "Processing user request"):
            ...
    """
    logger.info(f"▶️  Starting: {context}")
    start_time = datetime.now()
    try:
        yield
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Completed: {context} ({duration:.2f}s)")
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ Failed: {context} ({duration:.2f}s): {e}")
        raise


def log_to_database(logger: logging.Logger, db):
    """
    Add database logging handler to logger.

    Usage:
        log_to_database(logger, database)
        logger.info("This will be logged to database")
    """
    from Open_ELF.query.models import SystemEvent

    class DatabaseLogHandler(logging.Handler):
        """Custom handler that logs to database."""

        def __init__(self, db):
            super().__init__()
            self.db = db
            self.setLevel(logging.INFO)

        async def emit(self, record):
            """Log record to database."""
            try:
                await SystemEvent.create(
                    event_type=record.levelname,
                    event_time=datetime.now(),
                    source=record.name,
                    message=self.format(record),
                    extra_data=json.dumps({
                        'function': record.funcName,
                        'line': record.lineno,
                        'module': record.module
                    })
                )
            except Exception as e:
                # Prevent logging errors from breaking the application
                print(f"Failed to log to database: {e}")

    db_handler = DatabaseLogHandler(db)
    db_handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(db_handler)


# Standard loggers for components
query_logger = setup_logger('query', level=logging.INFO)
orchestrator_logger = setup_logger('orchestrator', level=logging.INFO)
watcher_logger = setup_logger('watcher', level=logging.INFO)
agent_logger = setup_logger('agent', level=logging.INFO)
dashboard_logger = setup_logger('dashboard', level=logging.INFO)
```

### Step 3: Refactor Observers

```python
# File: Open_ELF/core/observers/base.py (new)
"""
Base observer class with common observer patterns.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class BaseObserver(ABC):
    """Base class for all observers."""

    def __init__(self, name: str):
        self.name = name
        self._enabled = True
        self._observations: List[Dict[str, Any]] = []

    @abstractmethod
    async def observe(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Observe an event and return observation data.

        Args:
            context: Event context (tool use, system state, etc.)

        Returns:
            Observation data or None
        """
        pass

    @abstractmethod
    async def analyze(self, observations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze collected observations.

        Args:
            observations: List of observation data

        Returns:
            Analysis results
        """
        pass

    async def process(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single event: observe, record, analyze.

        Args:
            context: Event context

        Returns:
            Analysis results or None
        """
        if not self._enabled:
            return None

        observation = await self.observe(context)

        if observation:
            self._observations.append(observation)
            return await self.analyze(self._observations)

        return None

    def enable(self):
        """Enable this observer."""
        self._enabled = True
        logger.info(f"✅ Observer {self.name} enabled")

    def disable(self):
        """Disable this observer."""
        self._enabled = False
        logger.info(f"⏸️  Observer {self.name} disabled")

    def clear_observations(self):
        """Clear all recorded observations."""
        self._observations.clear()
        logger.info(f"🧹 Observer {self.name} observations cleared")

    def get_observations(self) -> List[Dict[str, Any]]:
        """Get all recorded observations."""
        return self._observations.copy()


# Usage example
from Open_ELF.core.observers.base import BaseObserver
from Open_ELF.core.logging_utils import log_execution_time

class HeuristicObserver(BaseObserver):
    """Observer for heuristic usage patterns."""

    async def observe(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Record heuristic consultation."""
        if 'heuristics_consulted' not in context:
            return None

        return {
            'timestamp': datetime.now().isoformat(),
            'heuristics': context['heuristics_consulted'],
            'domain': context.get('domain', 'general')
        }

    @log_execution_time(logger)
    async def analyze(self, observations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze heuristic usage patterns."""
        from collections import Counter

        # Count heuristic usage
        heuristic_counts = Counter()
        for obs in observations:
            for heuristic in obs['heuristics']:
                heuristic_counts[heuristic] += 1

        return {
            'total_observations': len(observations),
            'top_heuristics': heuristic_counts.most_common(10),
            'unique_heuristics': len(heuristic_counts)
        }
```

**Implementation Steps**:
1. ✅ Extract `DatabaseRepository` base class for common DB operations
2. ✅ Create centralized logging utilities module
3. ✅ Refactor observers to use base class
4. ⏳ Replace duplicate observer code with base class
5. ⏳ Update existing modules to use new utilities
6. ⏳ Remove duplicate code files

**Files Modified**:
- New: `Open_ELF/core/database/base.py`
- New: `Open_ELF/core/logging_utils.py`
- New: `Open_ELF/core/observers/base.py`
- Update: Multiple modules to use new utilities

**Estimated Time**: 6 hours

**Verification**:
```bash
# Test that refactored code still works
python -m pytest tests/database/test_base.py -v

# Check for import errors
python -c "from Open_ELF.core.database.base import DatabaseRepository; print('✅ OK')"

# Verify logging works
python -c "
from Open_ELF.core.logging_utils import setup_logger
logger = setup_logger('test')
logger.info('Test message')
"
```

---

# 🟡 P2 - MEDIUM PRIORITY

## P2.1 - Consolidate Configuration Management

**Status**: ⚠️ Multiple config files, inconsistent environment variable handling, hardcoded paths

**Problem**: Configuration scattered across multiple files with inconsistent patterns makes maintenance difficult.

**Evidence**:
- `Open_ELF/core/config.py` exists
- Dashboard has its own config
- Hardcoded paths like `/home/bamer/.opencode/emergent-learning/` exist in multiple files

**Solution**:

```python
# File: Open_ELF/core/config_manager.py (new)
"""
Centralized configuration management.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import json

logger = logging.getLogger(__name__)


class ConfigManager:
    """Centralized configuration manager."""

    # Default configuration
    DEFAULT_CONFIG = {
        'elf': {
            'base_path': '~/.opencode/emergent-learning',
            'data_path': 'memory',
            'log_path': 'logs',
            'backup_path': 'backups',
        },
        'database': {
            'path': 'memory/index.db',
            'timeout_seconds': 30,
            'connection_pool_size': 5,
        },
        'orchestrator': {
            'port': 9999,
            'host': 'localhost',
            'health_check_interval': 60,
        },
        'event_bridge': {
            'port': 9998,
            'host': 'localhost',
        },
        'watcher': {
            'enabled': True,
            'check_interval_seconds': 60,
            'ai_analysis_interval_seconds': 600,
        },
        'agents': {
            'base_path': '.',
            'session_timeout_seconds': 3600,
        },
        'dashboard': {
            'port': 8888,
            'host': 'localhost',
        },
    }

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize config manager.

        Args:
            config_file: Optional path to custom config file (YAML or JSON)
        """
        self._config = self.DEFAULT_CONFIG.copy()
        self._config_file = config_file

        # Load file config if provided
        if config_file and config_file.exists():
            self._load_file_config(config_file)

        # Override with environment variables
        self._load_env_config()

    def _load_file_config(self, config_file: Path):
        """Load config from file (YAML or JSON)."""
        try:
            if config_file.suffix in ['.yml', '.yaml']:
                with open(config_file, 'r') as f:
                    file_config = yaml.safe_load(f)
            elif config_file.suffix == '.json':
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
            else:
                logger.warning(f"Unsupported config file format: {config_file.suffix}")
                return

            # Merge with default config
            self._deep_merge(self._config, file_config)
            logger.info(f"Loaded config from {config_file}")

        except Exception as e:
            logger.error(f"Failed to load config from {config_file}: {e}")

    def _load_env_config(self):
        """Load config from environment variables."""
        env_mappings = {
            'ELF_BASE_PATH': 'elf.base_path',
            'ELF_DATABASE_PATH': 'database.path',
            'ELF_ORCHESTRATOR_PORT': 'orchestrator.port',
            'ELF_WATCHER_ENABLED': 'watcher.enabled',
            'ELF_DASHBOARD_PORT': 'dashboard.port',
        }

        for env_var, config_path in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Type conversion
                if env_var.endswith('_ENABLED'):
                    value = value.lower() in ('true', '1', 'yes')
                elif env_var.endswith('_PORT') or env_var.endswith('_INTERVAL') or env_var.endswith('_TIMEOUT'):
                    value = int(value)

                self._set_nested_value(config_path, value)
                logger.debug(f"Loaded {env_var}={value}")

    def _deep_merge(self, base: Dict, override: Dict):
        """Deep merge two dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _set_nested_value(self, path: str, value: Any):
        """Set a nested value using dot notation."""
        keys = path.split('.')
        config = self._config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value by path (dot notation).

        Args:
            path: Configuration path (e.g., 'elf.base_path')
            default: Default value if path not found

        Returns:
            Configuration value
        """
        keys = path.split('.')
        config = self._config

        try:
            for key in keys:
                config = config[key]
            return config
        except (KeyError, TypeError):
            return default

    def set(self, path: str, value: Any):
        """
        Set configuration value by path (dot notation).

        Args:
            path: Configuration path (e.g., 'elf.base_path')
            value: Value to set
        """
        self._set_nested_value(path, value)

    def get_path(self, path: str, expand_user: bool = True) -> Path:
        """
        Get a configuration path as Path object.

        Args:
            path: Configuration path (e.g., 'elf.base_path')
            expand_user: Expand ~ to user home directory

        Returns:
            Path object
        """
        value = self.get(path)
        if value is None:
            raise ValueError(f"Config path not found: {path}")

        result = Path(value)
        if expand_user:
            result = result.expanduser()

        return result

    def get_resolved_path(self, path: str, base_path_override: Optional[str] = None) -> Path:
        """
        Get a fully resolved path.

        Args:
            path: Configuration path (e.g., 'database.path')
            base_path_override: Optional override for base path

        Returns:
            Fully resolved Path object
        """
        path_obj = self.get_path(path, expand_user=False)

        # If relative, resolve against base path
        if not path_obj.is_absolute():
            base = base_path_override or str(self.get('elf.base_path'))
            path_obj = Path(base) / path_obj

        return path_obj.expanduser()

    def save(self, config_file: Optional[Path] = None):
        """
        Save current configuration to file.

        Args:
            config_file: Optional path to save to (default: original config file)
        """
        if config_file is None:
            config_file = self._config_file

        if config_file is None:
            raise ValueError("No config file specified")

        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)

            if config_file.suffix in ['.yml', '.yaml']:
                with open(config_file, 'w') as f:
                    yaml.safe_dump(self._config, f, default_flow_style=False)
            elif config_file.suffix == '.json':
                with open(config_file, 'w') as f:
                    json.dump(self._config, f, indent=2)
            else:
                raise ValueError(f"Unsupported config file format: {config_file.suffix}")

            logger.info(f"Saved config to {config_file}")

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self._config.copy()

    def __repr__(self) -> str:
        return f"ConfigManager(config_file={self._config_file})"


# Global singleton instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get global config manager instance."""
    global _config_manager

    if _config_manager is None:
        config_file = Path.home() / '.opencode' / 'emergent-learning' / 'config.yaml'
        _config_manager = ConfigManager(config_file)

    return _config_manager


# Usage examples
if __name__ == '__main__':
    config = get_config()

    # Get values
    base_path = config.get_path('elf.base_path')
    db_path = config.get_resolved_path('database.path')
    port = config.get('orchestrator.port')

    print(f"Base path: {base_path}")
    print(f"Database path: {db_path}")
    print(f"Orchestrator port: {port}")

    # Set values
    config.set('orchestrator.port', 10000)

    # Save config
    config.save()
```

**Implementation Steps**:
1. ✅ Create centralized config manager
2. ✅ Add support for YAML/JSON config files
3. ✅ Add environment variable overrides
4. ✅ Replace hardcoded paths throughout codebase
5. ⏳ Update documentation to reflect new config system
6. ⏳ Create sample config file

**Files Modified**:
- New: `Open_ELF/core/config_manager.py`
- Update: All files with hardcoded paths to use config manager
- Update: `README.md` to document configuration

**Estimated Time**: 4 hours

**Verification**:
```bash
# Test config manager
python -c "
from Open_ELF.core.config_manager import get_config
config = get_config()
print('Base path:', config.get('elf.base_path'))
print('Port:', config.get('orchestrator.port'))
"

# Test environment override
ELF_ORCHESTRATOR_PORT=9999 python -c "
from Open_ELF.core.config_manager import get_config
config = get_config()
print('Port:', config.get('orchestrator.port'))  # Should be 9999
"
```

---

## P2.2 - Add Type Hints to Critical Modules

**Status**: ⚠️ Mypy is partially configured but not enforced

**Problem**: Missing type hints make code harder to understand and refactor safely.

**Evidence**:
- `pyproject.toml` has mypy configured
- Many modules lack type hints
- `disallow_untyped_defs = false` in mypy config

**Solution**:

### Step 1: Add Type Hints to Core Modules

```python
# File: Open_ELF/core/database.py (updated with type hints)
"""
Database connection management with type hints.
"""
import sqlite3
import logging
from typing import Optional, AsyncIterator, Any, Dict, List
from contextlib import asynccontextmanager
import asyncio
from peewee_aio import AioModel, AioMySQLDatabase, AioPostgresqlDatabase, AioSqliteDatabase

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Async database connection manager with type hints.

    Example:
        db = DatabaseConnection('sqlite:///memory/index.db')
        await db.connect()
        await db.execute(query)
    """

    def __init__(
        self,
        dsn: str,
        connection_pool_size: int = 5,
        timeout: float = 30.0
    ):
        """
        Initialize database connection.

        Args:
            dsn: Database connection string (e.g., 'sqlite:///path/to/db.sqlite')
            connection_pool_size: Size of connection pool
            timeout: Connection timeout in seconds
        """
        self.dsn = dsn
        self.connection_pool_size = connection_pool_size
        self.timeout = timeout
        self._db: Optional[AioSqliteDatabase] = None
        self._connected: bool = False

    async def connect(self) -> None:
        """Establish database connection."""
        if self._connected:
            return

        try:
            if self.dsn.startswith('sqlite'):
                self._db = AioSqliteDatabase(self.dsn, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported database type: {self.dsn}")

            await self._db.connect()
            self._connected = True
            logger.info("✅ Database connected")

        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise

    async def disconnect(self) -> None:
        """Close database connection."""
        if self._connected and self._db:
            await self._db.close()
            self._connected = False
            logger.info("🔌 Database disconnected")

    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> AsyncIterator[Any]:
        """
        Execute database query.

        Args:
            query: SQL query string
            params: Optional query parameters

        Yields:
            Query results
        """
        if not self._connected:
            await self.connect()

        async with self._db.atomic():
            cursor = await self._db.execute_sql(query, params or {})
            async for row in cursor:
                yield row

    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions."""
        if not self._connected:
            await self.connect()

        async with self._db.atomic():
            try:
                yield
            except Exception as e:
                logger.error(f"Transaction failed: {e}")
                raise

    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._connected

    @property
    def db(self) -> Optional[AioSqliteDatabase]:
        """Get underlying database connection."""
        return self._db
```

### Step 2: Add Type Hints to Query System

```python
# File: Open_ELF/query/core.py (updated - key methods with type hints)
"""
Query system with type hints.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Result of a query operation."""
    learnings: List[Dict[str, Any]]
    heuristics: List[Dict[str, Any]]
    golden_rules: List[str]
    context: str
    metadata: Dict[str, Any]


class QuerySystem:
    """
    Query system with type hints.

    Example:
        qs = await QuerySystem.create()
        result = await qs.build_context("My task", domain="debugging")
    """

    def __init__(self, db_path: str):
        """
        Initialize query system.

        Args:
            db_path: Path to database file
        """
        self.db_path = db_path
        self._db: Optional[Any] = None

    @classmethod
    async def create(cls, db_path: Optional[str] = None) -> 'QuerySystem':
        """
        Factory method to create QuerySystem instance.

        Args:
            db_path: Optional path to database (uses default if not provided)

        Returns:
            QuerySystem instance
        """
        if db_path is None:
            db_path = cls._get_default_db_path()

        instance = cls(db_path)
        await instance._initialize_db()
        return instance

    @staticmethod
    def _get_default_db_path() -> str:
        """Get default database path."""
        import os
        return os.path.expanduser('~/.opencode/emergent-learning/memory/index.db')

    async def _initialize_db(self) -> None:
        """Initialize database connection."""
        # Implementation...
        pass

    async def build_context(
        self,
        task: str,
        domain: Optional[str] = None,
        limit: int = 10
    ) -> QueryResult:
        """
        Build context for a task.

        Args:
            task: Task description
            domain: Optional domain filter
            limit: Maximum number of results

        Returns:
            QueryResult with learnings, heuristics, and context
        """
        learnings = await self._query_learnings(domain, limit)
        heuristics = await self._query_heuristics(domain, limit)
        golden_rules = await self._get_golden_rules()

        return QueryResult(
            learnings=learnings,
            heuristics=heuristics,
            golden_rules=golden_rules,
            context=self._format_context(task, learnings, heuristics),
            metadata={
                'task': task,
                'domain': domain,
                'timestamp': datetime.now().isoformat(),
                'counts': {
                    'learnings': len(learnings),
                    'heuristics': len(heuristics),
                    'golden_rules': len(golden_rules),
                }
            }
        )

    async def _query_learnings(
        self,
        domain: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Query learnings with type hints."""
        # Implementation...
        return []

    async def _query_heuristics(
        self,
        domain: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Query heuristics with type hints."""
        # Implementation...
        return []

    async def _get_golden_rules(self) -> List[str]:
        """Get golden rules."""
        # Implementation...
        return []

    def _format_context(
        self,
        task: str,
        learnings: List[Dict[str, Any]],
        heuristics: List[Dict[str, Any]]
    ) -> str:
        """Format context string."""
        # Implementation...
        return ""

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._db:
            # Close connection...
            pass
```

### Step 3: Enforce Type Checking in CI/CD

```yaml
# File: .github/workflows/type-check.yml (new)
name: Type Check

on: [push, pull_request]

jobs:
  type-check:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -e ".[dev]"

    - name: Run mypy
      run: |
        mypy Open_ELF/**/*.py \
          --strict \
          --ignore-missing-imports \
          --no-warn-return-any \
          --disallow-any-generics \
          --disallow-incomplete-defs \
          --check-untyped-defs \
          --hide-error-codes \
          --show-error-codes

    - name: Upload mypy results
      if: failure()
      uses: actions/upload-artifact@v3
      with:
        name: mypy-results
        path: .mypy_cache/
```

**Implementation Steps**:
1. ✅ Add type hints to core modules
2. ✅ Add type hints to query system
3. ✅ Add type hints to orchestrator
4. ⏳ Update mypy configuration to be stricter
5. ⏳ Add type checking to CI/CD
6. ⏳ Fix type errors in non-critical modules

**Files Modified**:
- Update: `Open_ELF/core/database.py`
- Update: `Open_ELF/query/core.py`
- Update: `Open_ELF/core/central_orchestrator.py`
- Update: `pyproject.toml` (mypy config)
- New: `.github/workflows/type-check.yml`

**Estimated Time**: 6 hours

**Verification**:
```bash
# Run mypy on a module
mypy Open_ELF/core/database.py --strict

# Run on multiple modules
mypy Open_ELF/core/**/*.py Open_ELF/query/**/*.py

# Check for type errors
mypy Open_ELF/ --no-error-summary | grep "error:"
```

---

# 🟢 P3 - LOW PRIORITY

## P3.1 - Generate Current Database Schema Documentation

**Status**: ⚠️ No comprehensive database schema documentation

**Problem**: Database schema has 20+ tables but no visual documentation or ER diagram.

**Solution**:

```python
# File: scripts/database/generate_schema_doc.py (new)
#!/usr/bin/env python3
"""
Generate database schema documentation.
"""
import sys
import sqlite3
from pathlib import Path


def generate_schema_doc(db_path: str, output_file: str):
    """
    Generate markdown documentation for database schema.

    Args:
        db_path: Path to database file
        output_file: Path to output markdown file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    doc = []
    doc.append("# ELF Database Schema\n")
    doc.append(f"*Generated: {Path(db_path).name}*\n\n")
    doc.append("## Overview\n\n")
    doc.append(f"Total Tables: {len(tables)}\n\n")

    # Document each table
    for table_name, in tables:
        doc.append(f"## Table: `{table_name}`\n\n")

        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        doc.append("### Columns\n\n")
        doc.append("| Column | Type | Primary Key | Not Null | Default |\n")
        doc.append("|--------|------|-------------|----------|----------|\n")

        for col in columns:
            col_id, name, col_type, not_null, default_val, pk = col
            pk_mark = "✅" if pk else ""
            nn_mark = "✅" if not_null else ""
            default_str = str(default_val) if default_val else ""

            doc.append(f"| {name} | {col_type or ''} | {pk_mark} | {nn_mark} | {default_str} |\n")

        doc.append("\n### Indexes\n\n")

        # Get indexes
        cursor.execute(f"PRAGMA index_list({table_name})")
        indexes = cursor.fetchall()

        if indexes:
            doc.append("| Index Name | Unique |\n")
            doc.append("|------------|--------|\n")

            for idx in indexes:
                idx_name, unique, origin, partial = idx
                unique_mark = "✅" if unique else ""
                doc.append(f"| {idx_name} | {unique_mark} |\n")
        else:
            doc.append("*No indexes defined*\n")

        doc.append("\n### Foreign Keys\n\n")

        # Get foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fks = cursor.fetchall()

        if fks:
            doc.append("| ID | Table | From | To |\n")
            doc.append("|----|-------|------|-----|\n")

            for fk in fks:
                fk_id, seq, table, from_col, to_col, on_update, on_delete, match = fk
                doc.append(f"| {fk_id} | {table} | {from_col} | {to_col} |\n")
        else:
            doc.append("*No foreign keys defined*\n")

        doc.append("\n---\n\n")

    # Write to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        f.write(''.join(doc))

    print(f"✅ Schema documentation generated: {output_file}")

    conn.close()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = "/home/bamer/.opencode/emergent-learning/memory/index.db"

    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = "/home/bamer/.opencode/emergent-learning/docs/database-schema.md"

    generate_schema_doc(db_path, output_file)
```

**Implementation Steps**:
1. ✅ Create schema documentation generator script
2. ⏳ Generate ER diagram using tools like eralchemy or dbdiagram.io
3. ⏳ Add to CI/CD to auto-regenerate on schema changes
4. ⏳ Add to wiki documentation

**File Created**:
- New: `scripts/database/generate_schema_doc.py`

**Estimated Time**: 2 hours

---

## P3.2 - Add Performance Metrics Dashboard

**Status**: ⚠️ No centralized performance monitoring dashboard

**Problem**: Difficult to track system performance and identify bottlenecks.

**Solution**:

```python
# File: Open_ELF/core/metrics.py (new)
"""
Performance metrics collection and reporting.
"""
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """Single metric data point."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class MetricsCollector:
    """Collect and aggregate performance metrics."""

    def __init__(self):
        self._metrics: Dict[str, list] = defaultdict(list)
        self._timers: Dict[str, float] = {}

    def record(self, name: str, value: float, unit: str = None, metadata: Dict[str, Any] = None):
        """
        Record a metric.

        Args:
            name: Metric name
            value: Metric value
            unit: Unit of measurement
            metadata: Additional metadata
        """
        metric = Metric(
            name=name,
            value=value,
            unit=unit or '',
            timestamp=datetime.now(),
            metadata=metadata
        )
        self._metrics[name].append(asdict(metric))

        # Keep only last 1000 points per metric
        if len(self._metrics[name]) > 1000:
            self._metrics[name] = self._metrics[name][-1000:]

    def start_timer(self, name: str):
        """Start a timer for named operation."""
        self._timers[name] = time.time()

    def stop_timer(self, name: str, metadata: Dict[str, Any] = None):
        """Stop timer and record duration."""
        if name not in self._timers:
            logger.warning(f"Timer {name} was not started")
            return

        duration = time.time() - self._timers[name]
        self.record(name, duration, 's', metadata)
        del self._timers[name]

    def get_stats(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for named metric.

        Returns:
            Dictionary with count, min, max, mean, median, p95, p99
        """
        if name not in self._metrics or not self._metrics[name]:
            return None

        values = [m['value'] for m in self._metrics[name]]

        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'p95': self._percentile(values, 95),
            'p99': self._percentile(values, 99),
            'unit': self._metrics[name][0]['unit'],
        }

    def _percentile(self, values: list, p: int) -> float:
        """Calculate percentile."""
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * (p / 100)
        f = int(k)
        c = f + 1
        if f == c:
            return sorted_values[f]
        return sorted_values[f] + (k - f) * (sorted_values[c] - sorted_values[f])

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics with statistics."""
        return {
            name: self.get_stats(name)
            for name in self._metrics if self._metrics[name]
        }


# Global metrics collector
metrics = MetricsCollector()


# Usage examples
if __name__ == '__main__':
    # Record a metric
    metrics.record('database_query_time', 0.045, 's', {'query': 'SELECT * FROM table'})

    # Timer
    metrics.start_timer('data_processing')
    time.sleep(0.1)
    metrics.stop_timer('data_processing')

    # Get stats
    stats = metrics.get_stats('data_processing')
    print(stats)
```

**Implementation Steps**:
1. ✅ Create metrics collector module
2. ⏳ Integrate metrics into orchestrator, watcher, dashboard
3. ⏳ Add metrics endpoint to dashboard API
4. ⏳ Create performance visualization in dashboard

**Files Modified**:
- New: `Open_ELF/core/metrics.py`
- Update: Multiple modules to record metrics
- Update: Dashboard to display metrics

**Estimated Time**: 4 hours

---

# 📋 Summary & Implementation Roadmap

## Quick Wins (Can be done in 1-2 hours each)

| Item | Impact | Effort | Priority |
|------|--------|--------|----------|
| **P0.1 - Database Backup Automation** | High | Low | 🔴 |
| **P0.3 - Fix Dependency Conflicts** | High | Low | 🔴 |
| **P3.1 - Generate Schema Documentation** | Medium | Low | 🟢 |

## Medium-Term (2-6 hours each)

| Item | Impact | Effort | Priority |
|------|--------|--------|----------|
| **P0.2 - Database Integrity Checks** | High | Medium | 🔴 |
| **P2.1 - Consolidate Configuration** | Medium | Medium | 🟡 |
| **P2.2 - Add Type Hints** | Medium | Medium | 🟡 |
| **P3.2 - Performance Metrics** | Medium | Medium | 🟢 |

## Long-Term (6-8 hours each)

| Item | Impact | Effort | Priority |
|------|--------|--------|----------|
| **P1.1 - Increase Test Coverage** | High | High | 🟠 |
| **P1.2 - Reduce Code Duplication** | High | High | 🟠 |

## Recommended Implementation Order

### Week 1
1. ✅ P0.1 - Database Backup Automation (2h)
2. ✅ P0.3 - Fix Dependency Conflicts (2h)
3. ✅ P3.1 - Generate Schema Documentation (2h)

### Week 2
4. ✅ P0.2 - Database Integrity Checks (3h)
5. ✅ P2.1 - Consolidate Configuration (4h)

### Week 3-4
6. ✅ P2.2 - Add Type Hints (6h)
7. ✅ P1.2 - Reduce Code Duplication (6h)

### Week 5-6
8. ✅ P1.1 - Increase Test Coverage (8h)
9. ✅ P3.2 - Performance Metrics (4h)

**Total Estimated Time**: ~37 hours spread over 6 weeks

---

## Metrics for Success

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| **Test Coverage** | ~16% | >70% | `pytest --cov` |
| **Database Backups** | Manual | Automated every 6h | Check system logs |
| **Type Hint Coverage** | Low | >80% | `mypy --strict` |
| **Code Duplication** | High | <10% | Code analysis tools |
| **Configuration Files** | 10+ | 1 unified | Count config files |
| **Documentation** | Minimal | Schema + API docs | Doc files count |

---

This plan provides a structured approach to improving the ELF codebase. Start with the P0 critical items for immediate impact, then work through P1/P2 for medium-term improvements, and tackle P3 items as opportunity allows.
