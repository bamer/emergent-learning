# Fichiers Archivés - Avant Nettoyage Définitif

**Date**: $(date +%Y-%m-%d)
**Raison**: Restructuration architecture ELF

## Architecture Nouvelle

```
Open_ELF/
├── orchestrator/
│   ├── event_bridge.py                  ← Communication Layer (sessions, SSE)
│   └── unified_orchestrator.py          ← Orchestration Layer (workflows, décisions)
└── agents/
    └── elf_logging.py                    ← Infrastructure Layer (logs)
```

## Règle d'Or

> Toute fonction qui instancie ou tente d'ouvrir une session en direct sur le serveur opencode
> devrait être éradiquée.

## Fichiers Archivés

| Fichier | Raison |
|---------|--------|
| `orchestrator/async_opencode_client.py` | Redondant avec event_bridge.py (fusionné) |
| `agents/logger.py` | Redondant avec elf_logging.py (fusionné) |
| `agents/opconnection.py` | Crée sessions directes (éradiqué) |
| `agents/opencode_client.py` | Crée sessions directes (éradiqué) |
| `agents/unified_orchestrator.py` (agents/) | Crée sessions directes (éradiqué) |
| `agents/agent_status_api.py` | Redondant (unified_orchestrator a /status) |
| `agents/orchestrator_state.py` | Obsolète (non utilisé) |

## Migration des Appelants

### Avant (CRÉATION SESSION DIRECTE - MAUVAIS):
```python
response = requests.post(
    f"http://localhost:4096/session",
    json={"title": "Session"},
)
```

### Après (DÉLÉGATION - CORRECT):
```python
from orchestrator.event_bridge import EventBridge

bridge = EventBridge()
response = bridge.send_message("Message", agent="researcher")
```

## Tests à Effectuer Avant Suppression

- [ ] unified_orchestrator.py fonctionne sans ces fichiers
- [ ] event_bridge.py fonctionne
- [ ] Toutes les old sessions sont nettoyées
- [ ] Pas de nouvelle session créée directement
- [ ] RAM usage stable (~20-30 Go, pas 100 Go)

## Si Tout Est OK

Supprimer ce dossier après 7 jours:
```bash
rm -rf /home/bamer/.opencode/emergent-learning/Open_ELF/archived_before_cleanup/*/
```

## Si Problèmes

Restaurer les fichiers depuis ce dossier:
```bash
cp archived_before_cleanup/202X-XX-XX/* .
```
