# Migration Guide: Unified Orchestration System

## Vue d'ensemble

Le système d'orchestration ELF a été unifié. Tous les agents utilisent maintenant le même système.

## Changements majeurs

### Avant
- Plusieurs orchestrateurs: `orchestrator.py`, `src/orchestrator.py`, `swarm-orchestrator.js`
- Logging dispersé dans différents répertoires
- Gestion d'erreurs inconsistante
- Références à Claude dans le code

### Après
- **Un seul orchestrateur**: `agents/unified_orchestrator.py`
- **Logging centralisé**: `/home/bamer/.opencode/emergent-learning/logs/`
- **Politique stricte**: "ça marche ou ça crash"
- **Code propre**: Plus de références à Claude

## Nouveaux fichiers

### Core
- `agents/unified_orchestrator.py` - Orchestrateur unifié (748 lignes)
- `agents/elf_logging.py` - Système de logging centralisé (220 lignes)
- `agents/elf_agent_wrapper.py` - Wrapper pour agents (150 lignes)

### Scripts
- `scripts/start-elf-orchestrator.sh` - Démarrage de l'orchestrateur
- `scripts/stop-elf-orchestrator.sh` - Arrêt de l'orchestrateur

### Tests
- `agents/test_orchestration.py` - Tests du système (200 lignes)

### Documentation
- `docs/ORCHESTRATION.md` - Documentation complète

## Comment migrer vos agents

### 1. Ancien style (à éviter)
```python
import logging

logger = logging.getLogger("mon_agent")
# Logging dispersé, pas de gestion d'erreurs stricte
```

### 2. Nouveau style (recommandé)
```python
from elf_agent_wrapper import AgentWrapper, AgentConfig
from elf_logging import get_logger

config = AgentConfig(
    name="mon_agent",
    description="Description de mon agent",
    icon="🤖",
    auto_start=False,
    restart_on_error=True,
    max_restarts=3
)

wrapper = AgentWrapper(config)
logger = get_logger("mon_agent")

def run():
    logger.info("Agent démarré")
    # Votre code ici

wrapper.run(run)
```

## Utilisation de l'orchestrateur

### Démarrer
```bash
./scripts/start-elf-orchestrator.sh
```

### Arrêter
```bash
./scripts/stop-elf-orchestrator.sh
```

### Spawner un agent
```bash
python agents/unified_orchestrator.py spawn researcher
```

### Arrêter un agent
```bash
python agents/unified_orchestrator.py kill researcher
```

### Voir le status
```bash
python agents/unified_orchestrator.py status
```

## Architecture des agents

```
┌─────────────────────────────────────┐
│     UnifiedOrchestrator             │
│     (Coordination centrale)         │
└─────────────────────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌─────────┐      ┌──────────┐
│Sentinel │      │ Sentinel  │
│(Auto)   │      │ (Auto)   │
└─────────┘      └──────────┘
    │                   │
    └─────────┬─────────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌─────────┐      ┌──────────┐
│Researcher│     │Architect │
│(On-demand)│    │(On-demand)│
└─────────┘      └──────────┘
    │                   │
    └─────────┬─────────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌─────────┐      ┌──────────┐
│Skeptic  │      │Creative  │
│(On-demand)│    │(On-demand)│
└─────────┘      └──────────┘
```

## Politique "ça marche ou ça crash"

Le système est maintenant strict:

1. **Erreurs critiques** → Crash immédiat du système
2. **Erreurs normales** → Redémarrage automatique (max 3 fois)
3. **Erreurs persistantes** → Escalade au CEO
4. **Aucune erreur silencieuse** → Tout est logué

## Fichiers de log

Tous les logs sont dans `/home/bamer/.opencode/emergent-learning/logs/`:

- `unified_orchestrator.log` - Orchestrateur principal
- `sentinel.log` - Surveillance continue
- `sentinel.log` - Vérifications périodiques
- `<agent>.log` - Logs spécifiques par agent
- `CRASH.log` - Erreurs critiques
- `escalation.log` - Escalades

## Tests

Pour vérifier que tout fonctionne:

```bash
cd agents
python test_orchestration.py
```

Résultat attendu:
```
✅ PASS: Logging System
✅ PASS: Log Directory
✅ PASS: Unified Orchestrator
✅ PASS: Agent Wrapper
✅ PASS: Scripts Executable
✅ PASS: No Claude References
```

## Agents existants à migrer

Les agents suivants doivent être migrés pour utiliser le nouveau système:

- [ ] `agents/orchestrator.py` (ancien)
- [ ] `agents/sentinel_startup.py`
- [ ] `agents/sentinel_with_learning.py`
- [ ] `src/sentinel/sentinel_loop.py`
- [ ] `sentinel/sentinel_loop.py`

## Checklist de migration

Pour chaque agent:

- [ ] Importer `elf_logging` et `elf_agent_wrapper`
- [ ] Remplacer le logging par `get_logger()`
- [ ] Wrapper l'exécution avec `AgentWrapper`
- [ ] Tester que l'agent fonctionne
- [ ] Vérifier que les logs vont dans le bon répertoire
- [ ] S'assurer qu'il n'y a pas d'erreurs silencieuses

## Support

En cas de problème:
1. Vérifier les logs: `tail -f logs/unified_orchestrator.log`
2. Lancer les tests: `python agents/test_orchestration.py`
3. Consulter la documentation: `docs/ORCHESTRATION.md`

## Date de migration

Migration complétée le: 2026-01-31
