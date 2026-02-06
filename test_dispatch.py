#!/usr/bin/env python3

import requests
import os
import json

os.chdir('/home/bamer/.opencode/emergent-learning/Open_ELF')

print("Testing event dispatch...")

try:
    # Envoyer un message simple (utilise session existante d'OpenCode)
    print("\nChecking OpenCode sessions...")
    resp = requests.get("http://localhost:4096/session", timeout=5)
    if resp.status_code == 200:
        sessions = resp.json()
        print(f"✅ Found {len(sessions)} sessions")
        
        if sessions:
            session_id = sessions[0]["id"]
            print(f"Using existing session: {session_id[:8]}...")
            
            # Envoyer message
            print("Sending test message...")
            resp = requests.post(
                f"http://localhost:4096/session/{session_id}/message",
                json={"parts": [{"type": "text", "text": "Test registration dispatch - Unified Orchestrator should receive this!"}]},
                timeout=10
            )
            print(f"Message sent: {resp.status_code}")
            
            # Attendre pour voir dispatch
            import time
            time.sleep(3)
            
            # Vérifier logs
            print("\n=== Checking Event Bridge logs ===")
            os.system("tail -30 /home/bamer/.opencode/emergent-learning/Open_ELF/logs/event_bridge_test.log | grep -E 'unified_orchestrator|dispatched'")
            
            # Vérifier stats
            print("\n=== Event Bridge Stats ===")
            resp = requests.get("http://localhost:9998/status", timeout=5)
            stats = json.loads(resp.text)
            print(f"Events processed: {stats['events_processed']}")
            
        else:
            print("⚠️  No sessions found")
    else:
        print("❌ Failed to list sessions")

except Exception as e:
    print(f"❌ Error: {e}")
