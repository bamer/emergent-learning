# ELF OpenCode - Commandes de Gestion

## Démarrage des Services

### 1. Dashboard Backend

```bash
# Démarrer le backend FastAPI (port 8888)
cd /home/bamer/.opencode/emergent-learning/dashboard-app/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8888
```

### 2. Event Bridge (Hooks)

```bash
# Démarrer le pont d'événements (port 9998)
cd /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator
python3 event_bridge.py start
```

### 3. Orchestrateur ELF (Optionnel)

```bash
# Démarrer l'orchestrateur ELF (port 9999)
cd /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator
python3 orchestrator.py start
```

### 4. Démarrage Complet (Tous les services)

```bash
# Script pour tout démarrer
cd /home/bamer/.opencode/emergent-learning

# Terminal 1 - Backend
cd dashboard-app/backend && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8888

# Terminal 2 - Event Bridge
cd Open_ELF/orchestrator && python3 event_bridge.py start

# Terminal 3 - Dashboard Frontend
cd dashboard-app/frontend && npm run dev
```

## Vérification des Services

### Status des services

```bash
# Vérifier le backend
curl -s http://localhost:8888/api/v1/agents/status | python3 -m json.tool

# Vérifier Event Bridge
curl -s http://localhost:9998/status | python3 -m json.tool

# Vérifier OpenCode Server
curl -s http://localhost:4096/global/health

# Vérifier l'orchestrateur
curl -s http://localhost:9999/status | python3 -m json.tool
```

### Liste des processus

```bash
# Voir tous les services ELF en cours
ps aux | grep -E "(uvicorn|event_bridge|orchestrator)" | grep -v grep

# Ports utilisés
netstat -tlnp | grep -E "(8888|9998|9999|4096)"
```

## Gestion des Agents

### Lister les agents

```bash
# Liste complète via API
curl -s http://localhost:8888/api/v1/agents/list | python3 -m json.tool

# Liste OpenCode
curl -s http://localhost:8888/api/v1/agents/opencode/list | python3 -m json.tool

# Liste via OpenCode directement
curl -s http://localhost:4096/agent | python3 -m json.tool
```

### Lister les modèles disponibles

```bash
# Modèles via backend
curl -s http://localhost:8888/api/v1/agents/models | python3 -m json.tool

# Modèles via OpenCode directement
curl -s http://localhost:4096/config/providers | python3 -m json.tool
```

### Exécuter une mission

```bash
# Mode smart (auto-détection)
curl -s -X POST http://localhost:8888/api/v1/agents/run \
  -H "Content-Type: application/json" \
  -d '{"mission": "Analyser le code", "mode": "smart"}'

# Mode auto (sélection automatique)
curl -s -X POST http://localhost:8888/api/v1/agents/run \
  -H "Content-Type: application/json" \
  -d '{"mission": "Debug error", "mode": "auto"}'

# Mode swarm (multi-agents)
curl -s -X POST http://localhost:8888/api/v1/agents/run \
  -H "Content-Type: application/json" \
  -d '{"mission": "swarm: Refactor codebase", "mode": "swarm"}'

# Mode manuel (agent spécifique)
curl -s -X POST http://localhost:8888/api/v1/agents/run \
  -H "Content-Type: application/json" \
  -d '{"mission": "Design API", "mode": "manual", "agent_type": "architect"}'
```

### Démarrer/Arrêter un agent

```bash
# Démarrer un agent
curl -s -X POST http://localhost:8888/api/v1/agents/spawn \
  -H "Content-Type: application/json" \
  -d '{"agent_type": "researcher"}'

# Arrêter un agent
curl -s -X POST http://localhost:8888/api/v1/agents/kill \
  -H "Content-Type: application/json" \
  -d '{"agent_type": "researcher"}'

# Tester un agent
curl -s -X POST http://localhost:8888/api/v1/agents/test \
  -H "Content-Type: application/json" \
  -d '{"agent_type": "researcher"}'
```

## Gestion des Sessions OpenCode

### Sessions

```bash
# Lister les sessions
curl -s http://localhost:4096/session | python3 -m json.tool

# Créer une session
curl -s -X POST http://localhost:4096/session \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Session"}' | python3 -m json.tool

# Voir les messages d'une session
curl -s http://localhost:4096/session/{SESSION_ID}/message | python3 -m json.tool

# Envoyer un message
curl -s -X POST http://localhost:4096/session/{SESSION_ID}/message \
  -H "Content-Type: application/json" \
  -d '{"parts": [{"type": "text", "text": "Hello"}]}'

# Supprimer une session
curl -s -X DELETE http://localhost:4096/session/{SESSION_ID}
```

### Stream d'événements SSE

```bash
# Écouter les événements (à exécuter dans un terminal séparé)
curl -s -N http://localhost:4096/event -H "Accept: text/event-stream"

# Test rapide (5 secondes)
timeout 5 curl -s -N http://localhost:4096/event -H "Accept: text/event-stream"
```

## Logs et Debugging

### Logs des services

```bash
# Logs Event Bridge
tail -f /home/bamer/.opencode/emergent-learning/Open_ELF/logs/event_bridge.log

# Logs Orchestrateur
tail -f /home/bamer/.opencode/emergent-learning/Open_ELF/logs/orchestrator.log

# Logs des hooks
tail -f /home/bamer/.opencode/emergent-learning/Open_ELF/logs/heuristics.log

# Logs backend (dans le terminal où il tourne)
# ou via journalctl si configuré
```

### Vérifier les hooks

```bash
# Lister les hooks installés
ls -la ~/.opencode/hooks/

# Vérifier un hook spécifique
ls -la ~/.opencode/hooks/PostToolUse/
ls -la ~/.opencode/hooks/PreToolUse/
ls -la ~/.opencode/hooks/learning-loop/

# Tester un hook manuellement
cd ~/.opencode/hooks/PostToolUse
echo '{"test": "data"}' | python3 post_tool_learning.py
```

### Debugging

```bash
# Tester la connexion OpenCode
curl -s http://localhost:4096/global/health

# Tester le backend
curl -s http://localhost:8888/api/v1/agents/status

# Tester Event Bridge
curl -s http://localhost:9998/status

# Voir les erreurs récentes
grep -i "error" /home/bamer/.opencode/emergent-learning/Open_ELF/logs/event_bridge.log | tail -20
```

## Recherche Sémantique

### Index et recherche

```bash
# Statistiques
curl -s http://localhost:8888/api/v1/semantic/stats | python3 -m json.tool

# Santé du service
curl -s http://localhost:8888/api/v1/semantic/health | python3 -m json.tool

# Recherche
curl -s -X POST http://localhost:8888/api/v1/semantic/search \
  -H "Content-Type: application/json" \
  -d '{"query": "python code", "top_k": 5}' | python3 -m json.tool

# Lister les embeddings
curl -s "http://localhost:8888/api/v1/semantic/embeddings?limit=10" | python3 -m json.tool
```

## Tasks et Trails

### Gestion des tasks

```bash
# Lister les tasks
ls -la ~/.opencode/tasks/

# Voir une task spécifique
cat ~/.opencode/tasks/elf_*/{TASK_ID}.json | python3 -m json.tool

# Nombre de tasks
find ~/.opencode/tasks -name "*.json" | wc -l
```

### Trails (Phéromones)

```bash
# Voir les trails dans la base de données
sqlite3 ~/.opencode/emergent-learning/memory/index.db \
  "SELECT * FROM pheromone_trails ORDER BY timestamp DESC LIMIT 10;"

# Compter les trails
sqlite3 ~/.opencode/emergent-learning/memory/index.db \
  "SELECT COUNT(*) FROM pheromone_trails;"
```

## Base de Données

### Requêtes SQL utiles

```bash
# Se connecter à la base
sqlite3 ~/.opencode/emergent-learning/memory/index.db

# Voir les tables
.tables

# Structure des tables
.schema embeddings
.schema heuristics
.schema pheromone_trails

# Nombre d'embeddings
SELECT COUNT(*) FROM embeddings;

# Nombre d'heuristiques
SELECT COUNT(*) FROM heuristics;

# Heuristiques récentes
SELECT id, title, domain, created_at FROM heuristics 
ORDER BY created_at DESC LIMIT 10;

# Quitter
.quit
```

## Arrêt des Services

### Arrêter proprement

```bash
# Trouver les PIDs et arrêter
pkill -f "uvicorn.*8888"
pkill -f "event_bridge.py"
pkill -f "orchestrator.py"

# Ou plus spécifiquement
pgrep -f "uvicorn" | xargs kill -9
pgrep -f "event_bridge" | xargs kill -9
```

### Redémarrage complet

```bash
# Script de redémarrage
cd /home/bamer/.opencode/emergent-learning

# 1. Arrêter tout
pkill -f "uvicorn\|event_bridge\|orchestrator"
sleep 2

# 2. Démarrer backend
cd dashboard-app/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8888 &

# 3. Démarrer Event Bridge
cd ../../Open_ELF/orchestrator
python3 event_bridge.py start &

# 4. Vérifier
echo "Services démarrés:"
curl -s http://localhost:8888/api/v1/agents/status | grep -o '"running": true'
curl -s http://localhost:9998/status | grep -o '"running": true'
```

## Commandes de Test

### Test complet du système

```bash
#!/bin/bash
# test_elf.sh

echo "=== Test ELF System ==="

# Test 1: Backend
echo -n "Backend: "
curl -s http://localhost:8888/api/v1/agents/status > /dev/null && echo "✅ OK" || echo "❌ FAIL"

# Test 2: Event Bridge
echo -n "Event Bridge: "
curl -s http://localhost:9998/status > /dev/null && echo "✅ OK" || echo "❌ FAIL"

# Test 3: OpenCode
echo -n "OpenCode: "
curl -s http://localhost:4096/global/health > /dev/null && echo "✅ OK" || echo "❌ FAIL"

# Test 4: Agents
echo -n "Agents: "
AGENTS=$(curl -s http://localhost:8888/api/v1/agents/list | grep -o '"id"' | wc -l)
echo "✅ $AGENTS agents"

# Test 5: Modèles
echo -n "Modèles: "
MODELS=$(curl -s http://localhost:8888/api/v1/agents/models | grep -o '"id"' | wc -l)
echo "✅ $MODELS modèles"

echo "=== Test Complete ==="
```

## Raccourcis Utiles

### Aliases Bash (à ajouter dans ~/.bashrc)

```bash
# ELF Backend
alias elf-start='cd /home/bamer/.opencode/emergent-learning/dashboard-app/backend && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8888'
alias elf-bridge='cd /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator && python3 event_bridge.py start'
alias elf-status='curl -s http://localhost:8888/api/v1/agents/status | python3 -m json.tool'
alias elf-agents='curl -s http://localhost:8888/api/v1/agents/list | python3 -m json.tool'
alias elf-logs='tail -f /home/bamer/.opencode/emergent-learning/Open_ELF/logs/event_bridge.log'
alias elf-stop='pkill -f "uvicorn\|event_bridge"'

# OpenCode
alias oc-health='curl -s http://localhost:4096/global/health'
alias oc-agents='curl -s http://localhost:4096/agent | python3 -m json.tool'
alias oc-models='curl -s http://localhost:4096/config/providers | python3 -m json.tool'
```

## URLs Importantes

| Service | URL |
|---------|-----|
| Dashboard Frontend | <http://localhost:3001> |
| Dashboard Backend API | <http://localhost:8888> |
| Event Bridge Status | <http://localhost:9998/status> |
| Orchestrateur Status | <http://localhost:9999/status> |
| OpenCode Server | <http://localhost:4096> |
| OpenCode Health | <http://localhost:4096/global/health> |
| OpenCode Docs | <http://localhost:4096/doc> |

## Troubleshooting

### Problèmes courants

**Backend ne démarre pas (erreur 500)**

```bash
# Vérifier les dépendances
cd dashboard-app/backend
source venv/bin/activate
pip install -r requirements.txt

# Vérifier les imports
python3 -c "import fastapi; print('FastAPI OK')"
python3 -c "import requests; print('Requests OK')"
```

**Event Bridge se reconnecte en boucle**

```bash
# Vérifier OpenCode
curl http://localhost:4096/global/health

# Redémarrer Event Bridge
pkill -f event_bridge
cd Open_ELF/orchestrator
python3 event_bridge.py start

python3 ~/.opencode/emergent-learning/Open_ELF/orchestrator event_bridge.py start

```

**Pas d'agents dans le dashboard**

```bash
# Vérifier OpenCode
curl http://localhost:4096/agent

# Vérifier le backend
curl http://localhost:8888/api/v1/agents/list
```

**Hooks ne se déclenchent pas**

```bash
# Vérifier les hooks
ls ~/.opencode/hooks/PostToolUse/
ls ~/.opencode/hooks/PreToolUse/

# Vérifier Event Bridge
curl http://localhost:9998/status
tail -f /home/bamer/.opencode/emergent-learning/Open_ELF/logs/event_bridge.log
```

---

*Dernière mise à jour: 2026-02-01*
*Version: ELF OpenCode 2.0*
