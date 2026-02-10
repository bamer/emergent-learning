#!/usr/bin/env python3
"""
ELF Coordination Module - SQLite-based agent coordination, heartbeat, and messaging.

Replaces static JSON files (.coordination/blackboard.json, agent_registry.json)
with a durable SQLite-backed coordination store.

Provides:
- Agent registration with heartbeat
- Inter-agent messaging (send/receive)
- Task tracking for swarm operations
- Blackboard snapshot generation (derived from DB state)

Usage:
    from Open_ELF.core.coordination import CoordinationStore
    
    store = CoordinationStore()
    store.register_agent("sentinel", pid=12345, capabilities=["monitoring"])
    store.heartbeat("sentinel")
    store.send_message("sentinel", "orchestrator", "status", {"health": "ok"})
    messages = store.receive_messages("orchestrator")
    store.write_blackboard_snapshot()
"""

import json
import os
import sqlite3
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional


DB_PATH = Path("/home/bamer/.opencode/emergent-learning/memory/index.db")
COORDINATION_DIR = Path("/home/bamer/.opencode/emergent-learning/.coordination")
BLACKBOARD_PATH = COORDINATION_DIR / "blackboard.json"
REGISTRY_PATH = COORDINATION_DIR / "agent_registry.json"

DEFAULT_STALE_TIMEOUT = 120  # seconds
DEFAULT_HEARTBEAT_INTERVAL = 30  # seconds


class CoordinationStore:
    """SQLite-backed coordination store for ELF agents."""

    def __init__(self, db_path: Optional[Path] = None, stale_timeout: int = DEFAULT_STALE_TIMEOUT):
        self.db_path = db_path or DB_PATH
        self.stale_timeout = stale_timeout
        self._init_tables()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coord_agents (
                name TEXT PRIMARY KEY,
                pid INTEGER DEFAULT 0,
                status TEXT DEFAULT 'registered',
                capabilities TEXT DEFAULT '[]',
                model TEXT DEFAULT '',
                meta TEXT DEFAULT '{}',
                registered_at TEXT NOT NULL,
                last_heartbeat TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coord_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_agent TEXT NOT NULL,
                to_agent TEXT NOT NULL,
                msg_type TEXT NOT NULL,
                payload TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                read_at TEXT DEFAULT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_coord_messages_to
            ON coord_messages(to_agent, read_at)
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coord_tasks (
                id TEXT PRIMARY KEY,
                owner TEXT NOT NULL,
                state TEXT DEFAULT 'pending',
                spec TEXT NOT NULL DEFAULT '{}',
                result TEXT DEFAULT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT DEFAULT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_coord_tasks_state
            ON coord_tasks(state, owner)
        """)

        conn.commit()
        conn.close()

    # ========== Agent Registration ==========

    def register_agent(self, name: str, pid: int = 0,
                      capabilities: Optional[List[str]] = None,
                      model: str = "", meta: Optional[Dict] = None):
        now = datetime.now().isoformat()
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO coord_agents (name, pid, status, capabilities, model, meta, registered_at, last_heartbeat)
            VALUES (?, ?, 'active', ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                pid = excluded.pid,
                status = 'active',
                capabilities = excluded.capabilities,
                model = excluded.model,
                meta = excluded.meta,
                last_heartbeat = excluded.last_heartbeat
        """, (
            name, pid,
            json.dumps(capabilities or []),
            model,
            json.dumps(meta or {}),
            now, now
        ))
        conn.commit()
        conn.close()

    def unregister_agent(self, name: str):
        conn = self._get_conn()
        conn.execute(
            "UPDATE coord_agents SET status = 'stopped', last_heartbeat = ? WHERE name = ?",
            (datetime.now().isoformat(), name)
        )
        conn.commit()
        conn.close()

    def heartbeat(self, name: str):
        now = datetime.now().isoformat()
        conn = self._get_conn()
        conn.execute(
            "UPDATE coord_agents SET last_heartbeat = ?, status = 'active' WHERE name = ?",
            (now, name)
        )
        conn.commit()
        conn.close()

    def get_agent_status(self, name: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM coord_agents WHERE name = ?", (name,)).fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def get_all_agents(self) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM coord_agents ORDER BY name").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def cleanup_stale_agents(self) -> int:
        cutoff = (datetime.now() - timedelta(seconds=self.stale_timeout)).isoformat()
        conn = self._get_conn()
        cursor = conn.execute(
            "UPDATE coord_agents SET status = 'stale' WHERE last_heartbeat < ? AND status = 'active'",
            (cutoff,)
        )
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count

    # ========== Messaging ==========

    def send_message(self, from_agent: str, to_agent: str,
                    msg_type: str, payload: Optional[Dict] = None) -> int:
        now = datetime.now().isoformat()
        conn = self._get_conn()
        cursor = conn.execute("""
            INSERT INTO coord_messages (from_agent, to_agent, msg_type, payload, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (from_agent, to_agent, msg_type, json.dumps(payload or {}), now))
        msg_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return msg_id

    def receive_messages(self, agent_name: str, mark_read: bool = True,
                        msg_type: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        
        if msg_type:
            rows = conn.execute("""
                SELECT * FROM coord_messages
                WHERE to_agent = ? AND read_at IS NULL AND msg_type = ?
                ORDER BY created_at ASC
            """, (agent_name, msg_type)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM coord_messages
                WHERE to_agent = ? AND read_at IS NULL
                ORDER BY created_at ASC
            """, (agent_name,)).fetchall()
        
        messages = [dict(r) for r in rows]
        
        if mark_read and messages:
            now = datetime.now().isoformat()
            ids = [m["id"] for m in messages]
            placeholders = ','.join('?' * len(ids))
            conn.execute(
                f"UPDATE coord_messages SET read_at = ? WHERE id IN ({placeholders})",
                [now] + ids
            )
            conn.commit()
        
        conn.close()
        
        for m in messages:
            try:
                m["payload"] = json.loads(m["payload"]) if isinstance(m["payload"], str) else m["payload"]
            except (json.JSONDecodeError, TypeError):
                pass
        
        return messages

    def broadcast_message(self, from_agent: str, msg_type: str,
                         payload: Optional[Dict] = None,
                         exclude: Optional[List[str]] = None):
        agents = self.get_all_agents()
        exclude = set(exclude or [])
        exclude.add(from_agent)
        for agent in agents:
            if agent["name"] not in exclude and agent["status"] == "active":
                self.send_message(from_agent, agent["name"], msg_type, payload)

    # ========== Task Tracking ==========

    def create_task(self, task_id: str, owner: str, spec: Dict) -> str:
        now = datetime.now().isoformat()
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO coord_tasks (id, owner, state, spec, created_at, updated_at)
            VALUES (?, ?, 'pending', ?, ?, ?)
        """, (task_id, owner, json.dumps(spec), now, now))
        conn.commit()
        conn.close()
        return task_id

    def update_task(self, task_id: str, state: str, result: Optional[Dict] = None):
        now = datetime.now().isoformat()
        conn = self._get_conn()
        if state in ("completed", "failed"):
            conn.execute("""
                UPDATE coord_tasks SET state = ?, result = ?, updated_at = ?, completed_at = ?
                WHERE id = ?
            """, (state, json.dumps(result or {}), now, now, task_id))
        else:
            conn.execute("""
                UPDATE coord_tasks SET state = ?, updated_at = ? WHERE id = ?
            """, (state, now, task_id))
        conn.commit()
        conn.close()

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM coord_tasks WHERE id = ?", (task_id,)).fetchone()
        conn.close()
        if row:
            task = dict(row)
            for field in ("spec", "result"):
                if task.get(field) and isinstance(task[field], str):
                    try:
                        task[field] = json.loads(task[field])
                    except (json.JSONDecodeError, TypeError):
                        pass
            return task
        return None

    def get_active_tasks(self, owner: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        if owner:
            rows = conn.execute(
                "SELECT * FROM coord_tasks WHERE state IN ('pending', 'running') AND owner = ?",
                (owner,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM coord_tasks WHERE state IN ('pending', 'running')"
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ========== Blackboard Snapshot ==========

    def write_blackboard_snapshot(self):
        """Write blackboard.json as a derived snapshot from DB state."""
        self.cleanup_stale_agents()
        
        agents = self.get_all_agents()
        active_tasks = self.get_active_tasks()
        
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "agents": {},
            "agent_files": [],
            "stop_requested": False,
            "status": "active" if any(a["status"] == "active" for a in agents) else "idle",
            "last_check": datetime.now().isoformat(),
            "active_tasks": len(active_tasks),
        }
        
        for agent in agents:
            snapshot["agents"][agent["name"]] = {
                "status": agent["status"],
                "pid": agent["pid"],
                "last_heartbeat": agent["last_heartbeat"],
                "capabilities": json.loads(agent["capabilities"]) if isinstance(agent["capabilities"], str) else agent["capabilities"],
            }
        
        COORDINATION_DIR.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(COORDINATION_DIR), prefix='.bb_', suffix='.tmp')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, indent=2)
            os.replace(tmp, str(BLACKBOARD_PATH))
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def write_registry_snapshot(self):
        """Write agent_registry.json as a derived snapshot from DB state."""
        agents = self.get_all_agents()
        
        registry = {
            "timestamp": datetime.now().isoformat(),
            "version": "3.0",
            "registered_agents": {},
            "source": "coordination_store",
        }
        
        for agent in agents:
            caps = json.loads(agent["capabilities"]) if isinstance(agent["capabilities"], str) else agent["capabilities"]
            meta = json.loads(agent["meta"]) if isinstance(agent["meta"], str) else agent["meta"]
            
            registry["registered_agents"][agent["name"]] = {
                "name": agent["name"],
                "status": agent["status"],
                "last_seen": agent["last_heartbeat"],
                "capabilities": caps,
                "model": agent.get("model", ""),
                "pid": agent["pid"],
                "config": meta,
            }
        
        COORDINATION_DIR.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(COORDINATION_DIR), prefix='.reg_', suffix='.tmp')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2)
            os.replace(tmp, str(REGISTRY_PATH))
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise


# Singleton
_store_instance: Optional[CoordinationStore] = None

def get_coordination_store(db_path: Optional[Path] = None) -> CoordinationStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = CoordinationStore(db_path)
    return _store_instance


if __name__ == "__main__":
    print("Testing CoordinationStore...")
    store = CoordinationStore()
    
    store.register_agent("test_agent", pid=os.getpid(), capabilities=["testing"])
    store.heartbeat("test_agent")
    
    msg_id = store.send_message("test_agent", "orchestrator", "status", {"test": True})
    print(f"Sent message {msg_id}")
    
    msgs = store.receive_messages("orchestrator")
    print(f"Received {len(msgs)} messages")
    
    store.write_blackboard_snapshot()
    print("Blackboard snapshot written")
    
    store.write_registry_snapshot()
    print("Registry snapshot written")
    
    store.unregister_agent("test_agent")
    print("Test complete!")
