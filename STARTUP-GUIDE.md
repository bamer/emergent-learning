# ELF OpenCode - Guide de Démarrage

## 🚀 Démarrage Rapide

### 1. Démarrer tout le système
```bash
cd /home/bamer/.opencode/emergent-learning
./start-elf-system.sh
```

### 2. Effectuer un check-in complet
```bash
cd /home/bamer/.opencode/emergent-learning
./checkin-elf.sh
```

## 📋 Scripts Disponibles

### `start-elf-system.sh` - Démarrage du système
Modes disponibles:
- `all` (défaut) - Démarre tous les services
- `minimal` - OpenCode Server + Dashboard Backend
- `test` - Mode test rapide

### `checkin-elf.sh` - Check-in complet
Vérifie:
- État des processus
- Connectivité des services
- Fonctionnalité des APIs
- Agents disponibles
- Hooks installés
- Système d'apprentissage
- Logs récents

## 🌐 URLs des Services

| Service | URL | Port |
|---------|-----|------|
| Dashboard Frontend | http://localhost:3001 | 3001 |
| Dashboard Backend | http://localhost:8888 | 8888 |
| Event Bridge | http://localhost:9998/status | 9998 |
| OpenCode Server | http://localhost:4096 | 4096 |

## 🛠️ Commandes Utiles

### Gestion des services
```bash
# Voir les processus ELF
ps aux | grep -E "(opencode\|uvicorn\|event_bridge)"

# Arrêter tous les services
pkill -f "opencode.*serve"
pkill -f "uvicorn.*8888"
pkill -f "event_bridge.py"
pkill -f "npm.*dev"

# Redémarrer le backend
cd dashboard-app/backend && source venv/bin/activate
pkill -f "uvicorn.*8888"
uvicorn main:app --host 0.0.0.0 --port 8888

# Redémarrer l'Event Bridge
cd Open_ELF/orchestrator
pkill -f "event_bridge.py"
python3 event_bridge.py start
```

### Test des composants
```bash
# Test API agents
curl http://localhost:8888/api/v1/agents/status

# Test Event Bridge
curl http://localhost:9998/status

# Test OpenCode
curl http://localhost:4096/global/health

# Liste des agents
curl http://localhost:8888/api/v1/agents/list

# Liste des modèles
curl http://localhost:8888/api/v1/agents/models
```

### Vérification du learning system
```bash
# Voir les heuristiques
sqlite3 ~/.opencode/emergent-learning/memory/index.db "SELECT COUNT(*) FROM heuristics;"

# Voir les trails
sqlite3 ~/.opencode/emergent-learning/memory/index.db "SELECT COUNT(*) FROM pheromone_trails;"

# Voir les embeddings
sqlite3 ~/.opencode/emergent-learning/memory/index.db "SELECT COUNT(*) FROM embeddings;"

# Dernières heuristiques
sqlite3 ~/.opencode/emergent-learning/memory/index.db "SELECT title, domain, created_at FROM heuristics ORDER BY created_at DESC LIMIT 5;"
```

### Gestion des hooks
```bash
# Lister les hooks
ls -la ~/.opencode/hooks/

# Tester un hook
cd ~/.opencode/emergent-learning
export ELF_BASE_PATH=/home/bamer/.opencode/emergent-learning
export PYTHONPATH=/home/bamer/.opencode/emergent-learning

echo '{"tool_name": "Read", "tool_input": {"path": "/tmp/test.txt"}, "tool_output": {"content": "test"}, "success": true, "session_id": "test123"}' | python3 ~/.opencode/hooks/PostToolUse/post_tool_learning.py
```

### Logs
```bash
# Logs Event Bridge
tail -f /home/bamer/.opencode/emergent-learning/Open_ELF/logs/event_bridge.log

# Logs Backend
tail -f /home/bamer/.opencode/emergent-learning/Open_ELF/logs/backend.log

# Logs Frontend
tail -f /home/bamer/.opencode/emergent-learning/Open_ELF/logs/frontend.log

# Logs OpenCode
tail -f /home/bamer/.opencode/emergent-learning/Open_ELF/logs/opencode-server.log
```

## 🐛 Dépannage

### Problèmes courants

**Backend ne démarre pas**
```bash
# Vérifier les dépendances
cd dashboard-app/backend
source venv/bin/activate
pip install -r requirements.txt

# Vérifier le port
lsof -i :8888
```

**Event Bridge ne reçoit pas d'événements**
```bash
# Vérifier OpenCode
curl http://localhost:4096/global/health

# Redémarrer Event Bridge
pkill -f event_bridge
cd Open_ELF/orchestrator
python3 event_bridge.py start
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

# Tester manuellement
./checkin-elf.sh  # Inclut un test de hook
```

### Reset complet
```bash
# Arrêter tout
pkill -f "opencode\|uvicorn\|event_bridge\|npm"

# Nettoyer les processus orphelins
pkill -f "python.*orchestrator"
pkill -f "node.*dev"

# Redémarrer
./start-elf-system.sh
```

## 📊 Monitoring

### Statut en temps réel
```bash
# Script de monitoring rapide
watch -n 5 './checkin-elf.sh | grep -E "(✅|❌|⚠️)"'
```

### Performance
```bash
# Voir l'utilisation CPU/mémoire
htop -p $(pgrep -f "opencode\|uvicorn\|event_bridge\|npm" | tr '\n' ',' | sed 's/,$//')
```

---

*Dernière mise à jour: 2026-02-01*
*Version: ELF OpenCode 2.0*