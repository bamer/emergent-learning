#!/usr/bin/env python3
"""
Mission Bridge - Connects dashboard missions to orchestrator
Monitors .coordination/missions/ and converts to orchestrator format
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime

COORDINATION_DIR = Path.home() / ".opencode" / "emergent-learning" / ".coordination"
MISSIONS_DIR = COORDINATION_DIR / "missions"

def process_dashboard_mission(mission_file: Path, orchestrator):
    """Convert dashboard mission to orchestrator format and process"""
    try:
        with open(mission_file, 'r') as f:
            dashboard_mission = json.load(f)
        
        # Extract key fields
        task_id = dashboard_mission.get('taskId', 'unknown')
        agent_type = dashboard_mission.get('role', 'researcher')
        description = dashboard_mission.get('description', '')
        inputs = dashboard_mission.get('inputs', {})
        
        # Create mission text
        mission_parts = [description]
        if inputs:
            mission_parts.append(f"Inputs: {json.dumps(inputs)}")
        
        mission_text = " ".join(mission_parts)
        
        print(f"🔄 Converting dashboard mission {task_id} to orchestrator format")
        print(f"   Agent: {agent_type}")
        print(f"   Mission: {mission_text[:100]}...")
        
        # Process via orchestrator
        mission = orchestrator.run_mission(agent_type, mission_text)
        
        # Update mission file with result or delete
        if mission.status == "completed":
            # Mark as completed
            dashboard_mission['status'] = 'completed'
            dashboard_mission['completedAt'] = datetime.now().isoformat()
            dashboard_mission['response'] = mission.response[:1000] if mission.response else ''
            
            with open(mission_file, 'w') as f:
                json.dump(dashboard_mission, f, indent=2)
            
            print(f"✅ Mission {task_id} completed and updated")
        else:
            # Mark as error
            dashboard_mission['status'] = 'error'
            dashboard_mission['error'] = mission.response or 'Unknown error'
            dashboard_mission['updatedAt'] = datetime.now().isoformat()
            
            with open(mission_file, 'w') as f:
                json.dump(dashboard_mission, f, indent=2)
            
            print(f"❌ Mission {task_id} failed and updated")
            
        return True
        
    except Exception as e:
        print(f"❌ Error processing mission {mission_file}: {e}")
        return False

def monitor_missions(orchestrator):
    """Monitor missions directory and process new ones"""
    print(f"👀 Monitoring {MISSIONS_DIR} for new missions...")
    
    processed_missions = set()
    
    while True:
        try:
            if not MISSIONS_DIR.exists():
                print(f"⚠️  Missions directory not found: {MISSIONS_DIR}")
                time.sleep(10)
                continue
                
            # Check for new mission files
            for mission_file in MISSIONS_DIR.glob("mission-*.json"):
                if mission_file.name in processed_missions:
                    continue
                    
                print(f"📥 Found new mission: {mission_file.name}")
                
                if process_dashboard_mission(mission_file, orchestrator):
                    processed_missions.add(mission_file.name)
                    print(f"✅ Processed mission: {mission_file.name}")
                else:
                    print(f"❌ Failed to process mission: {mission_file.name}")
                    
            time.sleep(5)  # Check every 5 seconds
            
        except KeyboardInterrupt:
            print("👋 Mission bridge shutting down...")
            break
        except Exception as e:
            print(f"❌ Error in mission monitoring: {e}")
            time.sleep(10)

if __name__ == "__main__":
    print("🚀 Mission Bridge Starting...")
    print("This is a placeholder - will be integrated with orchestrator")
