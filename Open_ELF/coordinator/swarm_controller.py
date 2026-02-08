#!/usr/bin/env python3
"""
SwarmController - Orchestrates multi-agent swarm execution over AgentManager.

Distributes subtasks across specialized agents (architect, researcher, skeptic, creative),
runs them concurrently via ThreadPoolExecutor, collects results, extracts learnings,
and stores everything in the coordination store.

Usage:
    from coordinator.swarm_controller import SwarmController
    
    controller = SwarmController()
    result = controller.execute_swarm("Analyze authentication system")
"""

import json
import re
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

AGENT_ROLES = {
    "architect": {
        "role": "System design & structure",
        "perspective": "Top-down, big picture, scalability",
        "prefix": "As the Architect agent, analyze from a structural and design perspective:",
    },
    "researcher": {
        "role": "Research & validation",
        "perspective": "Evidence-based, thorough, standards-driven",
        "prefix": "As the Researcher agent, investigate thoroughly with evidence:",
    },
    "skeptic": {
        "role": "Testing & edge cases",
        "perspective": "Adversarial, defensive, failure-focused",
        "prefix": "As the Skeptic agent, find flaws, edge cases, and risks:",
    },
    "creative": {
        "role": "Novel solutions",
        "perspective": "Innovative, unconventional, cross-domain",
        "prefix": "As the Creative agent, propose novel and innovative approaches:",
    },
}

DEFAULT_AGENTS = ["architect", "researcher", "skeptic", "creative"]

SWARM_MODES = {
    "analysis": ["researcher", "architect"],
    "design": ["architect", "creative", "skeptic"],
    "implementation": ["architect", "researcher", "skeptic"],
    "learning": ["researcher", "architect"],
    "all": DEFAULT_AGENTS,
}


class SwarmController:
    """Orchestrates multi-agent swarm execution."""

    def __init__(self, max_workers: int = 4, timeout: int = 120):
        self.max_workers = max_workers
        self.timeout = timeout
        self._agent_manager = None
        self._coordination = None

    def _get_agent_manager(self):
        if self._agent_manager is None:
            try:
                from Open_ELF.agents.agent_manager import get_agent_manager
                self._agent_manager = get_agent_manager()
            except ImportError:
                try:
                    from agents.agent_manager import get_agent_manager
                    self._agent_manager = get_agent_manager()
                except ImportError:
                    raise RuntimeError("AgentManager not available. Ensure Open_ELF is in path.")
        return self._agent_manager

    def _get_coordination(self):
        if self._coordination is None:
            try:
                from Open_ELF.core.coordination import get_coordination_store
                self._coordination = get_coordination_store()
            except ImportError:
                try:
                    from core.coordination import get_coordination_store
                    self._coordination = get_coordination_store()
                except ImportError:
                    self._coordination = None
        return self._coordination

    def _generate_subtasks(self, task: str, agents: List[str]) -> Dict[str, str]:
        subtasks = {}
        for agent_name in agents:
            role_info = AGENT_ROLES.get(agent_name, {})
            prefix = role_info.get("prefix", f"As {agent_name}, analyze:")
            subtasks[agent_name] = (
                f"{prefix}\n\nTask: {task}\n\n"
                "Provide your analysis. Include [LEARNED:domain] markers for any key insights discovered."
            )
        return subtasks

    def _run_agent(self, agent_name: str, prompt: str) -> Dict[str, Any]:
        start = datetime.now()
        try:
            manager = self._get_agent_manager()
            result = manager.ask_agent(agent_name, prompt)
            duration_ms = int((datetime.now() - start).total_seconds() * 1000)

            if result.get("success"):
                response = result.get("response", "")
                learnings = self._extract_learnings(response)
                return {
                    "agent": agent_name,
                    "status": "completed",
                    "response": response,
                    "learnings": learnings,
                    "learnings_count": len(learnings),
                    "duration_ms": duration_ms,
                }
            else:
                return {
                    "agent": agent_name,
                    "status": "failed",
                    "error": result.get("error", "Unknown error"),
                    "learnings": [],
                    "learnings_count": 0,
                    "duration_ms": duration_ms,
                }
        except Exception as e:
            duration_ms = int((datetime.now() - start).total_seconds() * 1000)
            return {
                "agent": agent_name,
                "status": "error",
                "error": str(e),
                "learnings": [],
                "learnings_count": 0,
                "duration_ms": duration_ms,
            }

    def _extract_learnings(self, text: str) -> List[Dict[str, str]]:
        pattern = r'\[LEARNED:?\s*([^\]]*)\]\s*(.+?)(?=\[LEARNED|$)'
        learnings = []
        for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
            domain = match.group(1).strip() or "general"
            lesson = match.group(2).strip()
            if lesson and len(lesson) > 5:
                learnings.append({"domain": domain, "lesson": lesson[:500]})
        return learnings

    def _store_learnings(self, learnings: List[Dict[str, str]], task_id: str):
        try:
            import sqlite3
            db_path = Path("/home/bamer/.opencode/emergent-learning/memory/index.db")
            conn = sqlite3.connect(str(db_path), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")

            for learning in learnings:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO learnings
                        (type, domain, description, outcome, timestamp, context)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        "observation",
                        learning["domain"],
                        learning["lesson"][:1000],
                        "swarm_extracted",
                        datetime.now().isoformat(),
                        json.dumps({"source": "swarm", "task_id": task_id}),
                    ))
                except Exception:
                    continue

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Failed to store learnings: {e}", file=sys.stderr)

    def execute_swarm(
        self,
        task_description: str,
        mode: str = "all",
        custom_agents: Optional[List[str]] = None,
        subtasks: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a swarm of agents on a task.

        Args:
            task_description: Main task to analyze
            mode: Swarm mode (analysis, design, implementation, learning, all)
            custom_agents: Override agent list
            subtasks: Override auto-generated subtasks {agent_name: prompt}

        Returns:
            Dictionary with swarm results
        """
        task_id = f"swarm_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        if custom_agents:
            agents = [a for a in custom_agents if a in AGENT_ROLES]
        else:
            agents = SWARM_MODES.get(mode, DEFAULT_AGENTS)

        if not agents:
            return {"task_id": task_id, "status": "failed", "error": "No valid agents for swarm"}

        if subtasks is None:
            subtasks = self._generate_subtasks(task_description, agents)

        coord = self._get_coordination()
        if coord:
            try:
                coord.create_task(task_id, "swarm_controller", {
                    "task": task_description, "mode": mode, "agents": agents,
                })
                coord.write_blackboard_snapshot()
            except Exception:
                pass

        results = {
            "task_id": task_id,
            "task": task_description,
            "mode": mode,
            "agents_used": agents,
            "timestamp": datetime.now().isoformat(),
            "agent_results": {},
            "all_learnings": [],
            "status": "running",
        }

        print(f"\n{'='*60}")
        print(f"SWARM: {task_description}")
        print(f"Mode: {mode} | Agents: {', '.join(agents)}")
        print(f"Task ID: {task_id}")
        print(f"{'='*60}\n")

        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(agents))) as executor:
            futures = {}
            for agent_name in agents:
                prompt = subtasks.get(agent_name, task_description)
                future = executor.submit(self._run_agent, agent_name, prompt)
                futures[future] = agent_name
                print(f"  Spawned: {agent_name}")

            for future in as_completed(futures, timeout=self.timeout):
                agent_name = futures[future]
                try:
                    agent_result = future.result(timeout=self.timeout)
                    results["agent_results"][agent_name] = agent_result

                    icon = "+" if agent_result["status"] == "completed" else "!"
                    print(f"  [{icon}] {agent_name}: {agent_result['status']} "
                          f"({agent_result.get('duration_ms', 0)}ms, "
                          f"{agent_result.get('learnings_count', 0)} learnings)")

                    results["all_learnings"].extend(agent_result.get("learnings", []))
                except Exception as e:
                    results["agent_results"][agent_name] = {
                        "agent": agent_name, "status": "timeout",
                        "error": str(e), "learnings": [], "learnings_count": 0,
                    }
                    print(f"  [!] {agent_name}: timeout/error - {e}")

        completed = sum(1 for r in results["agent_results"].values() if r["status"] == "completed")
        total = len(agents)

        if completed == total:
            results["status"] = "success"
        elif completed > 0:
            results["status"] = "partial_success"
        else:
            results["status"] = "failed"

        results["completed_count"] = completed
        results["total_count"] = total
        results["total_learnings"] = len(results["all_learnings"])

        if results["all_learnings"]:
            self._store_learnings(results["all_learnings"], task_id)

        if coord:
            try:
                coord.update_task(task_id, results["status"], {
                    "completed": completed, "total": total,
                    "learnings": len(results["all_learnings"]),
                })
                coord.write_blackboard_snapshot()
            except Exception:
                pass

        print(f"\n{'='*60}")
        print(f"SWARM COMPLETE: {results['status']}")
        print(f"  Agents: {completed}/{total} completed")
        print(f"  Learnings: {results['total_learnings']} extracted")
        print(f"{'='*60}\n")

        return results


if __name__ == "__main__":
    print("SwarmController module loaded. Use swarm_cli.py for CLI access.")
