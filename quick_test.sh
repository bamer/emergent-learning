#!/bin/bash

echo "🧪 Test rapide..."

# 1. Envoyer message via Event Bridge send_message
echo ""
echo "1️⃣ Test send_message via Event Bridge..."
python3 <<'PYEOF'
import sys
import os
os.chdir('/home/bamer/.opencode/emergent-learning/Open_ELF')
sys.path.insert(0, '/home/bamer/.opencode/emergent-learning/Open_ELF')
sys.path.insert(0, '/home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator')

# Import EventBridge
import importlib.util
spec = importlib.util.spec_from_file_location("event_bridge_module", "/home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator/event_bridge.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
EventBridge = module.EventBridge

# Créer instance et envoyer message
bridge = EventBridge()
success, response = bridge.send_message("Test simple", timeout=30)

if success:
    print(f"✅ send_message() fonctionne!")
    print(f"   Réponse: {response[:100]}...")
else:
    print(f"❌ send_message() a échoué: {response}")
PYEOF

echo ""
echo "2️⃣ Vérifier dispatch logs..."
echo ""
grep -i "dispatched.*unified\|listener.*unified\|received.*from.*bridge" \
  /home/bamer/.opencode/emergent-learning/Open_ELF/logs/event_bridge_test.log | tail -5 || \
  echo "Pas encore de logs de dispatch (peut être normal)"

echo ""
echo "3️⃣ Stats..."

curl -s http://localhost:9998/status 2>/dev/null | python3 -c "import sys,json; s=json.load(sys.stdin); print(f\"Events: {s.get('events_processed', 0)}\")"

echo ""
echo "✅ Test terminé!"
