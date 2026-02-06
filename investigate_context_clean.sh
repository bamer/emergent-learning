#!/bin/bash

echo "🔍 Investiger comment OpenCode gère le context..."

echo ""
echo "1️⃣ Vérifier API OpenCode pour session..."

# Lister les sessions
curl -s http://localhost:4096/session 2>/dev/null | python3 -c "import sys,json; s=json.load(sys.stdin); print(f\"Sessions: {len(s)}\")" 2>/dev/null || echo "Cannot list sessions"

# Vérifier les options de session
echo ""
echo "2️⃣ Vérifier si OpenCode supporte 'clear' ou similar..."

# Regarder si les sessions peuvent être manipulées
echo "   Options possibles:"
echo "   - POST /session/{id}/clear (proposition)"
echo "   - DELETE /session/{id}/message (proposition)"
echo "   - GET /session/{id}/message → pourrait permettre de voir et delete"

echo ""
echo "3️⃣ Regarder la dernière session active..."
curl -s http://localhost:4096/session 2>/dev/null | python3 <<'PY'
import sys, json
import requests

sessions = json.load(sys.stdin)
if sessions:
    s = sessions[0]
    print(f"Session ID: {s.get('id')}")
    print(f"Title: {s.get('title')}")
    print(f"Created: {s.get('createdAt')}")
    
    # Essayer de récupérer les messages
    try:
        resp = requests.get(f"http://localhost:4096/session/{s.get('id')}/message", timeout=5)
        if resp.status_code == 200:
            msgs = resp.json()
            if isinstance(msgs, list):
                print(f"Messages in session: {len(msgs)}")
                print(f"Last role: {msgs[-1].get('role')}")
            else:
                print(f"Response type: {type(msgs)}")
    except Exception as e:
        print(f"Cannot get messages: {e}")
        
print("\n4️⃣ Testing 'clear' simulation...")
print("   NOTE: Pour un context clean, on peut:")
print("   - Vérifier les derniers messages")
print("   - Garder seulement le système config")
print("   - Nettoyer les messages utilisateur/assistant")
print("   - OU: Créer une nouvelle session (coûteux mais propre)")
PYEOF

chmod +x investigate_context_clean.sh && ./investigate_context_clean.sh
