# API Agents - Endpoints Dashboard

## Endpoints disponibles

### GET /api/v1/agents/status
Retourne le statut de tous les agents et de l'orchestrateur.

**Response:**
```json
{
  "orchestrator": {
    "running": true,
    "uptime_seconds": 123
  },
  "agents": {
    "sentinel": {
      "name": "Sentinel",
      "status": "running",
      "icon": "🔍",
      "session_id": "...",
      "error_count": 0,
      "restart_count": 0
    },
    ...
  }
}
```

### GET /api/v1/agents/list
Liste tous les agents disponibles avec leurs descriptions.

**Response:**
```json
{
  "agents": [
    {
      "type": "researcher",
      "name": "Researcher",
      "description": "Investigation approfondie",
      "icon": "🔬",
      "can_spawn": true
    },
    ...
  ]
}
```

### POST /api/v1/agents/spawn
Spawne un agent spécifique.

**Request:**
```json
{
  "agent_type": "researcher",
  "params": {}
}
```

**Response:**
```json
{
  "status": "ok",
  "agent": "researcher",
  "message": "Agent researcher spawned successfully"
}
```

### POST /api/v1/agents/kill
Arrête un agent spécifique.

**Request:**
```json
{
  "agent_type": "researcher",
  "force": false
}
```

**Response:**
```json
{
  "status": "ok",
  "agent": "researcher",
  "force": false,
  "message": "Agent researcher stopped successfully"
}
```

### POST /api/v1/agents/test
Teste un agent (spawn + kill).

**Request:**
```json
{
  "agent_type": "researcher"
}
```

**Response:**
```json
{
  "agent_type": "researcher",
  "status": "passed",
  "spawn": true,
  "kill": true,
  "message": "Agent test completed"
}
```

### GET /api/v1/agents/logs/{agent_name}
Retourne les logs récents d'un agent.

**Params:**
- `lines`: Nombre de lignes (default: 100)

**Response:**
```json
{
  "agent": "sentinel",
  "log_file": "/path/to/sentinel.log",
  "lines_returned": 100,
  "logs": ["line1", "line2", ...]
}
```

### GET /api/v1/agents/stream
SSE endpoint pour les mises à jour en temps réel des agents.

**Events:**
- `update`: Changement de statut
- `error`: Erreur de monitoring

## Agents disponibles

| Agent | Description | Auto-start | Spawnable |
|-------|-------------|------------|-----------|
| orchestrator | Coordination centrale | ✅ | ❌ |
| sentinel | Surveillance continue | ✅ | ❌ |
| watcher | Vérifications périodiques | ✅ | ❌ |
| researcher | Investigation | ❌ | ✅ |
| architect | Conception | ❌ | ✅ |
| skeptic | Analyse critique | ❌ | ✅ |
| creative | Innovation | ❌ | ✅ |
| ceo | Décisions exécutives | ❌ | ✅ |

## Exemple d'utilisation

```bash
# Voir le statut
curl http://localhost:8888/api/v1/agents/status

# Spawner un agent
curl -X POST http://localhost:8888/api/v1/agents/spawn \
  -H "Content-Type: application/json" \
  -d '{"agent_type": "researcher"}'

# Arrêter un agent
curl -X POST http://localhost:8888/api/v1/agents/kill \
  -H "Content-Type: application/json" \
  -d '{"agent_type": "researcher"}'

# Tester un agent
curl -X POST http://localhost:8888/api/v1/agents/test \
  -H "Content-Type: application/json" \
  -d '{"agent_type": "researcher"}'

# Voir les logs
curl http://localhost:8888/api/v1/agents/logs/sentinel?lines=50

# Stream SSE
curl http://localhost:8888/api/v1/agents/stream
```
