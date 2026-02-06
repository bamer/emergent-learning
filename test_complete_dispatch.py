#!/usr/bin/env python3

"""
Test complet de l'architecture unifiée:
1. Unified Orchestrator s'enregistre auprès de Event Bridge
2. Event Bridge reçoit des événements SSE
3. Event Bridge dispatche à Unified Orchestrator
4. Unified Orchestrator traite les événements
5. Test de send_message() pour call un agent
"""

import asyncio
import os
import time
import requests
import json

os.chdir('/home/bamer/.opencode/emergent-learning/Open_ELF')

print("=" * 70)
print("TEST COMPLETE - Unified Architecture")
print("=" * 70)

# 1. Vérifier Event Bridge
print("\n📡 1. Vérifier Event Bridge...")
try:
    resp = requests.get("http://localhost:9998/status", timeout=5)
    if resp.status_code == 200:
        stats = json.loads(resp.text)
        print(f"✅ Event Bridge running")
        print(f"   Events processed: {stats['events_processed']}")
        print(f"   Started: {stats['started_at']}")
        print(f"   Uptime: {stats['uptime_seconds']}s")
        print(f"   Running: {stats['running']}")
        
        # Vérifier si Unified Orchestrator est enregistré
        print(f"\n📊 Listener count: {len(stats.get('listeners', []))}")
        
    else:
        print(f"❌ Event Bridge not responding: {resp.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Cannot connect to Event Bridge: {e}")
    exit(1)

print("\n" + "=" * 70)
print("🧪 TEST DISPATCH: Envoyer un message qui génère un événement")
print("=" * 70)

# 2. Créer une nouvelle session pour tester
print("\n📁 2. Créer une nouvelle session de test...")
try:
    resp = requests.post(
        "http://localhost:4096/session",
        json={"title": "Test Complete Dispatch"},
        timeout=30
    )
    if resp.status_code in [200, 201]:
        session_id = resp.json()["id"]
        print(f"✅ Session created: {session_id}")
        print(f"   Full ID: {session_id}")
    else:
        print(f"❌ Failed to create session: {resp.status_code}")
        print(f"   Details: {resp.text[:200]}")
        exit(1)
except Exception as e:
    print(f"❌ Error creating session: {e}")
    exit(1)

# 3. Envoyer un message (cela générera des événements SSE)
print(f"\n💬 3. Envoyer un message simple...")
try:
    print(f"   Contenu: 'Hello from test - should trigger events!'")
    
    resp = requests.post(
        f"http://localhost:4096/session/{session_id}/message",
        json={"parts": [{"type": "text", "text": "Hello from test - should trigger events!"}]},
        timeout=30
    )
    
    print(f"   Message sent status: {resp.status_code}")
    
    if resp.status_code in [200, 201, 204]:
        print("✅ Message sent successfully")
        
        # Attendre un peu pour que les événements soient dispatchés
        print("\n⏳ 4. Attendre 5s pour traitement et dispatch...")
        time.sleep(5)
    else:
        print(f"❌ Message send failed: {resp.status_code}")
        print(f"   Details: {resp.text[:200]}")
        
except Exception as e:
    print(f"❌ Error sending message: {e}")

# 4. Vérifier les logs pour voir le dispatch
print(f"\n📋 5. Vérifier les logs...")
print("-" * 70)

print("\n=== Event Bridge logs (rechercher 'dispatched') ===")
os.system("tail -50 /home/bamer/.opencode/emergent-learning/Open_ELF/logs/event_bridge_test.log | grep -i -A 2 -B 2 'dispatched'")

print("\n=== Event Bridge logs (rechercher 'listener') ===")
os.system("tail -50 /home/bamer/.opencode/emergent-learning/Open_ELF/logs/event_bridge_test.log | grep -i -A 2 -B 2 'listener'")

print(f"\n=== Unified Orchestrator logs (rechercher 'received') ===")
if os.path.exists("/home/bamer/.opencode/emergent-learning/test_unified_orchestrator.py"):
    # Note: le test direct n'a pas de log file, mais on peut vérifier les processus
    pass
else:
    # Chercher les logs récents
    import glob
    log_files = sorted(
        glob.glob("/home/bamer/.opencode/emergent-learning/Open_ELF/logs/*.log"),
        key=os.path.getmtime
    )
    if log_files:
        recent_log = log_files[-1]
        print(f"Dernier log: {recent_log}")
        os.system(f"tail -30 {recent_log} | grep -i -A 2 -B 2 'unified_orchestr\\'")
    else:
        print("Pas de logs récents")
        
# 5. Vérifier stats après
print(f"\n📊 6. Stats après dispatch...")
print("-" * 70)

try:
    resp = requests.get("http://localhost:9998/status", timeout=5)
    if resp.status_code == 200:
        stats_after = json.loads(resp.text)
        print(f"Events processed: {stats_after['events_processed']}")
        print(f"Last event: {stats_after.get('last_event_time', 'N/A')}")
        print(f"Running: {stats_after['running']}")
        
except Exception:
    pass

print("\n" + "=" * 70)
print("✅ TEST TERMINÉ")
print("=" * 70)
print("")
print("Vérification manuelle suggérée:")
print("  1. Vérifiez que Unified Orchestrator tourne toujours (si test interactif)")
print("  2. Vérifiez les logs Event Bridge pour 'dispatched'")
print("  3. Les événements doivent être reçus et traités")
