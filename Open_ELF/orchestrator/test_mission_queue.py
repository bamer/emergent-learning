#!/usr/bin/env python3
"""
Test mission queuing without AI processing
"""

import asyncio
import json
import time
from pathlib import Path
from orchestrator import AsyncOrchestrator

async def test_mission_queue():
    """Test mission queuing system"""
    print("🚀 Testing mission queuing system...")
    
    # Create test orchestrator
    orchestrator = AsyncOrchestrator()
    
    # Create test mission directory
    test_dir = Path("/tmp/test_missions")
    test_dir.mkdir(exist_ok=True)
    
    # Create test missions
    mission1 = {
        "taskId": "test-001",
        "role": "test",
        "description": "Test mission 1",
        "status": "pending"
    }
    
    mission2 = {
        "taskId": "test-002", 
        "role": "test",
        "description": "Test mission 2",
        "status": "pending"
    }
    
    # Write test missions
    with open(test_dir / "mission-test-001.json", "w") as f:
        json.dump(mission1, f)
    
    with open(test_dir / "mission-test-002.json", "w") as f:
        json.dump(mission2, f)
    
    print(f"✅ Created test missions in {test_dir}")
    
    # Test mission discovery
    mission_files = list(test_dir.glob("mission-*.json"))
    print(f"🔍 Found {len(mission_files)} mission files")
    
    for mf in mission_files:
        print(f"  - {mf.name}")
    
    print("✅ Mission queuing test completed")

if __name__ == "__main__":
    asyncio.run(test_mission_queue())
