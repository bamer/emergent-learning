#!/usr/bin/env python3
"""
Open_ELF Scheduler - Asynchronous Orchestrator with Persistent Sessions
=============================================

Asynchronous orchestrator that processes missions without blocking.
Uses single persistent OpenCode session and background task management.

Features:
- Asynchronous mission processing (no blocking)
- Single persistent OpenCode session (no spawning)
- Background task management
- Proper error handling and timeouts
- Mission file status updates
"""

import json
import logging
import sys
import time
import threading
import asyncio
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from http.server import HTTPServer, BaseHTTPRequestHandler

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OpenELF")

# Constants
OPENCODE_SERVER = "http://localhost:4096"
TASKS_DIR = Path.home() / ".opencode" / "tasks"
COORDINATION_DIR = Path.home() / ".opencode" / "emergent-learning" / ".coordination"
MISSIONS_DIR = COORDINATION_DIR / "missions"

# Import optimized OpenCode client
from opencode_client import get_opencode_client

@dataclass
class Mission:
    """Représente une mission en cours."""

    id: str
    agent_type: str
    mission: str
    status: str  # pending, in_progress, completed, error
    start_time: datetime
    end_time: Optional[datetime] = None
    response: Optional[str] = None
    session_id: Optional[str] = None
    task_file: Optional[Path] = None

class TaskManager:
    """Gère les tasks dans ~/.opencode/tasks/"""

    def __init__(self):
        self.tasks_dir = TASKS_DIR
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def create_task(self, mission: Mission) -> Path:
        """Crée un fichier de task pour le dashboard."""
        # Créer un répertoire de session unique
        session_dir = self.tasks_dir / f"elf_{mission.start_time.strftime('%Y%m%d')}"
        session_dir.mkdir(exist_ok=True)

        # Générer ID de task
        task_id = f"{mission.agent_type}_{mission.id}"
        task_file = session_dir / f"{task_id}.json"

        task_data = {
            "id": task_id,
            "subject": f"[{mission.agent_type.upper()}] {mission.mission[:80]}...",
            "description": mission.mission,
            "status": mission.status,
            "session_id": session_dir.name,
            "session_name": f"ELF Orchestrator {mission.start_time.strftime('%Y-%m-%d')}",
            "notes": [
                {
                    "text": f"Mission started at {mission.start_time.isoformat()}",
                    "timestamp": mission.start_time.isoformat(),
                    "source": "orchestrator",
                }
            ],
        }

        with open(task_file, "w") as f:
            json.dump(task_data, f, indent=2)

        mission.task_file = task_file
        logger.info(f"📝 Task created: {task_file.name}")
        return task_file

    def update_task(self, mission: Mission):
        """Met à jour le fichier de task avec le résultat."""
        if not mission.task_file or not mission.task_file.exists():
            return

        try:
            with open(mission.task_file, "r") as f:
                task_data = json.load(f)

            task_data["status"] = mission.status

            if mission.response:
                task_data["notes"].append(
                    {
                        "text": f"Response: {mission.response[:500]}",
                        "timestamp": datetime.now().isoformat(),
                        "source": mission.agent_type,
                    }
                )

            if mission.end_time:
                task_data["notes"].append(
                    {
                        "text": f"Mission completed at {mission.end_time.isoformat()}",
                        "timestamp": mission.end_time.isoformat(),
                        "source": "orchestrator",
                    }
                )

            with open(mission.task_file, "w") as f:
                json.dump(task_data, f, indent=2)

            logger.info(
                f"📝 Task updated: {mission.task_file.name} -> {mission.status}"
            )
        except Exception as e:
            logger.error(f"Failed to update task: {e}")

class AsyncOpenCodeClient:
    """Async wrapper for optimized OpenCode client"""

    def __init__(self):
        self.client = get_opencode_client()

    async def health_check(self) -> bool:
        return self.client.health_check()

    async def send_message(self, message: str, agent: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """Async send message - runs in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.client.send_message, message, agent)

class AsyncOrchestrator:
    """Asynchronous Orchestrator with background task management"""

    def __init__(self):
        self.client = AsyncOpenCodeClient()
        self.task_manager = TaskManager()
        self.running = False
        self.missions: Dict[str, Mission] = {}
        self.processing_missions: set = set()
        self.mission_queue: asyncio.Queue = asyncio.Queue()

    async def start(self):
        """Démarre l'orchestrator asynchrone."""
        logger.info("======================================================================")
        logger.info("🚀 Async Open_ELF Scheduler Starting")
        logger.info("======================================================================")
        
        if not await self.client.health_check():
            logger.error("❌ OpenCode server not accessible")
            return

        logger.info("✅ Connected to OpenCode server")
        self.running = True

        # Start status server
        self._start_status_server()

        # Start mission monitoring
        monitor_task = asyncio.create_task(self._monitor_missions())
        logger.info("👀 Mission monitoring started")

        # Start mission processor
        processor_task = asyncio.create_task(self._process_missions())
        logger.info("⚙️  Mission processor started")

        # Main scheduler loop
        tick_count = 0
        try:
            while self.running:
                tick_count += 1
                if tick_count == 1 or tick_count % 10 == 0:
                    logger.info(f"⏰ Scheduler tick #{tick_count} - {datetime.now().isoformat()}")
                else:
                    logger.debug(f"⏰ Scheduler tick #{tick_count} - {datetime.now().isoformat()}")

                # Ici on peut ajouter des missions automatiques si besoin
                await asyncio.sleep(10)  # Non-blocking sleep
                
        except KeyboardInterrupt:
            logger.info("\n👋 Shutting down...")
            self.running = False

    async def _monitor_missions(self):
        """Surveille le répertoire des missions en arrière-plan."""
        logger.info(f"👀 Monitoring {MISSIONS_DIR} for new missions")
        processed_missions = set()
        
        while self.running:
            try:
                if not MISSIONS_DIR.exists():
                    await asyncio.sleep(10)
                    continue
                
                for mission_file in MISSIONS_DIR.glob("mission-*.json"):
                    if mission_file.name in processed_missions or mission_file.name in self.processing_missions:
                        continue
                    
                    try:
                        # Read mission file
                        async with aiofiles.open(mission_file, 'r') as f:
                            content = await f.read()
                            mission_data = json.loads(content)
                        
                        agent_type = mission_data.get("role", "researcher")
                        description = mission_data.get("description", "Unknown mission")
                        task_id = mission_data.get("taskId", f"m{int(time.time())}")
                        
                        logger.info(f"📥 Queued mission: {mission_file.name}")
                        
                        # Add to processing set and queue
                        self.processing_missions.add(mission_file.name)
                        await self.mission_queue.put({
                            'file': mission_file,
                            'data': mission_data,
                            'agent_type': agent_type,
                            'description': description,
                            'task_id': task_id
                        })
                        
                    except Exception as e:
                        logger.error(f"❌ Error reading mission {mission_file.name}: {e}")
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"❌ Error in mission monitoring: {e}")
                await asyncio.sleep(10)

    async def _process_missions(self):
        """Traite les missions de la file d'attente."""
        while self.running:
            try:
                # Get mission from queue (blocking but async)
                mission_info = await self.mission_queue.get()
                
                # Process in background task
                asyncio.create_task(self._execute_mission(mission_info))
                
                # Mark task as done
                self.mission_queue.task_done()
                
            except Exception as e:
                logger.error(f"❌ Error processing mission queue: {e}")
                await asyncio.sleep(1)

    async def _execute_mission(self, mission_info: dict):
        """Exécute une mission de manière asynchrone."""
        mission_file = mission_info['file']
        mission_data = mission_info['data']
        agent_type = mission_info['agent_type']
        description = mission_info['description']
        task_id = mission_info['task_id']
        
        try:
            # Create mission object
            mission = Mission(
                id=task_id,
                agent_type=agent_type,
                mission=description,
                status="pending",
                start_time=datetime.now(),
            )
            
            self.missions[task_id] = mission
            
            # Create task file
            self.task_manager.create_task(mission)
            
            logger.info(f"🎯 Mission started: {agent_type} - {description[:60]}...")
            
            # Update status to in_progress
            mission.session_id = "persistent-session"
            mission.status = "in_progress"
            self.task_manager.update_task(mission)
            
            # Update mission file
            mission_data["status"] = "in_progress"
            mission_data["startedAt"] = datetime.now().isoformat()
            async with aiofiles.open(mission_file, 'w') as f:
                await f.write(json.dumps(mission_data, indent=2))
            
            # Send message via optimized client (async)
            logger.info(f"📤 Sending message for mission {task_id}")
            success, response_text = await self.client.send_message(description, agent_type)
            
            # Update mission with results
            mission.end_time = datetime.now()
            
            if success:
                if response_text:
                    mission.response = response_text
                    mission.status = "completed"
                    logger.info(f"✅ Mission completed: {agent_type}")
                else:
                    mission.status = "error"
                    mission.response = "No response received from agent"
                    logger.error(f"❌ No response from {agent_type}")
            else:
                mission.status = "error"
                mission.response = response_text or "Failed to send message to agent"
                logger.error(f"❌ Failed to send message to {agent_type}")
            
            # Update task file
            self.task_manager.update_task(mission)
            
            # Update mission file
            mission_data["status"] = mission.status
            mission_data["completedAt"] = mission.end_time.isoformat()
            mission_data["response"] = mission.response[:1000] if mission.response else ""
            async with aiofiles.open(mission_file, 'w') as f:
                await f.write(json.dumps(mission_data, indent=2))
            
            logger.info(f"✅ Mission {mission_file.name} processing completed")
            
        except Exception as e:
            logger.error(f"❌ Error executing mission {mission_file.name}: {e}")
            # Update with error status
            try:
                mission_data["status"] = "error"
                mission_data["error"] = str(e)
                mission_data["completedAt"] = datetime.now().isoformat()
                async with aiofiles.open(mission_file, 'w') as f:
                    await f.write(json.dumps(mission_data, indent=2))
            except:
                pass
        finally:
            # Remove from processing set
            self.processing_missions.discard(mission_file.name)

    def _start_status_server(self):
        """Démarre un serveur HTTP simple pour exposer le status."""
        orchestrator_self = self

        class StatusHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/status":
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()

                    status = {
                        "running": orchestrator_self.running,
                        "missions_count": len(orchestrator_self.missions),
                        "processing_count": len(orchestrator_self.processing_missions),
                        "queue_size": orchestrator_self.mission_queue.qsize(),
                        "missions": [
                            {
                                "id": m.id,
                                "agent_type": m.agent_type,
                                "status": m.status,
                                "start_time": m.start_time.isoformat()
                                if m.start_time
                                else None,
                                "end_time": m.end_time.isoformat()
                                if m.end_time
                                else None,
                            }
                            for m in orchestrator_self.missions.values()
                        ],
                    }
                    self.wfile.write(json.dumps(status).encode())
                else:
                    self.send_response(404)
                    self.end_headers()

        server = HTTPServer(("localhost", 9999), StatusHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        logger.info("📊 Status server started on http://localhost:9999/status")

async def main_async():
    """Point d'entrée asynchrone."""
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py <command> [args]")
        print("Commands:")
        print("  start                    - Start the scheduler")
        print("  run <agent> <mission>    - Run a single mission")
        print("  status                   - Show current status")
        sys.exit(1)

    command = sys.argv[1]
    orchestrator = AsyncOrchestrator()

    if command == "start":
        await orchestrator.start()

    elif command == "run":
        if len(sys.argv) < 4:
            print("Usage: python orchestrator.py run <agent_type> <mission>")
            sys.exit(1)

        agent_type = sys.argv[2]
        mission_text = " ".join(sys.argv[3:])

        if not await orchestrator.client.health_check():
            print("❌ OpenCode server not accessible")
            sys.exit(1)

        # For single run, we'll run synchronously
        mission = Mission(
            id=f"m{int(time.time())}",
            agent_type=agent_type,
            mission=mission_text,
            status="pending",
            start_time=datetime.now(),
        )

        print(f"🎯 Mission started: {agent_type} - {mission_text[:60]}...")
        
        success, response_text = await orchestrator.client.send_message(mission_text, agent_type)
        
        if success:
            if response_text:
                mission.response = response_text
                mission.status = "completed"
                print(f"✅ Mission completed: {agent_type}")
            else:
                mission.status = "error"
                mission.response = "No response received from agent"
                print(f"❌ No response from {agent_type}")
        else:
            mission.status = "error"
            mission.response = response_text or "Failed to send message to agent"
            print(f"❌ Failed to send message to {agent_type}")

        mission.end_time = datetime.now()
        print(f"\nStatus: {mission.status}")
        if mission.response:
            print(f"Response: {mission.response[:500]}...")

    elif command == "status":
        try:
            import requests
            response = requests.get("http://localhost:9999/status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                print(f"Running: {status['running']}")
                print(f"Missions: {status['missions_count']}")
                print(f"Processing: {status['processing_count']}")
                print(f"Queue: {status['queue_size']}")
                for m in status["missions"]:
                    print(f"  - {m['agent_type']}: {m['status']}")
            else:
                print("❌ Scheduler not running")
        except Exception as e:
            print(f"❌ Scheduler not running: {e}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

def main():
    """Point d'entrée principal."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("\n👋 Shutdown requested")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
