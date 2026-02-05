# ELF Unified Orchestration System

Système d'orchestration unifié pour tous les agents ELF avec OpenCode.

## Exigences respectées

✅ **1. Système unique utilisé partout**
- Tous les agents utilisent `unified_orchestrator.py`
- Un seul point d'entrée pour spawn/stop des agents

✅ **2. Fiable et facile à utiliser**
- Spawn d'agents: `python unified_orchestrator.py spawn <agent>`
- Arrêt d'agents: `python unified_orchestrator.py kill <agent>`
- Scripts shell: `start-elf-orchestrator.sh` et `stop-elf-orchestrator.sh`

✅ **3. Arrêt propre des agents**
- Arrêt gracieux avec timeout
- Force kill si nécessaire
- Cleanup automatique

✅ **4. Coordination complète**
- **Sentinel**: Surveillance continue
- **Watcher**: Vérifications périodiques
- **4 agents spécialisés**: Researcher, Architect, Skeptic, Creative
- **CEO**: Décisions exécutives
- **Système d'escalade**: Intégré avec politique stricte

✅ **5. Logging centralisé**
- Tous les logs dans: `/home/bamer/.opencode/emergent-learning/logs/`
- Chaque agent a son propre fichier: `<agent_name>.log`
- Fichier de crash: `CRASH.log`

✅ **6. Politique "ça marche ou ça crash"**
- Aucune erreur silencieuse
- Les erreurs critiques arrêtent le système
- Logs détaillés pour debugging

✅ **7. Plus de références à Claude**
- Toutes les fonctionnalités migrées sont indépendantes
- Utilise uniquement OpenCode

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    UnifiedOrchestrator                      │
│                    (Coordination centrale)                  │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Sentinel   │    │   Watcher    │    │  4 Agents    │
│  (Continue)  │    │ (Périodique) │    │  (On-demand) │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Escalation Manager                          │
│         (Gestion des erreurs et escalade)                   │
└─────────────────────────────────────────────────────────────┘
```

## Utilisation

### Démarrer l'orchestrateur

```bash
# Via le script shell
./scripts/start-elf-orchestrator.sh

# Ou directement
python agents/unified_orchestrator.py start
```

### Arrêter l'orchestrateur

```bash
# Via le script shell
./scripts/stop-elf-orchestrator.sh

# Ou directement
python agents/unified_orchestrator.py stop
```

### Voir le status

```bash
python agents/unified_orchestrator.py status
```

### Spawner un agent spécifique

```bash
python agents/unified_orchestrator.py spawn researcher
python agents/unified_orchestrator.py spawn architect
python agents/unified_orchestrator.py spawn skeptic
python agents/unified_orchestrator.py spawn creative
```

### Arrêter un agent spécifique

```bash
python agents/unified_orchestrator.py kill researcher
python agents/unified_orchestrator.py kill architect --force
```

## Agents disponibles

| Agent | Rôle | Auto-start | Icon |
|-------|------|------------|------|
| orchestrator | Coordination centrale | ✅ | 🎯 |
| sentinel | Surveillance continue | ✅ | 🔍 |
| watcher | Vérifications périodiques | ✅ | 👁️ |
| researcher | Investigation | ❌ | 🔬 |
| architect | Conception | ❌ | 🏗️ |
| skeptic | Analyse critique | ❌ | ❓ |
| creative | Innovation | ❌ | 💡 |
| ceo | Décisions exécutives | ❌ | 👑 |

## Système de logging

Tous les agents loguent dans `/home/bamer/.opencode/emergent-learning/logs/`:

- `unified_orchestrator.log`: Logs de l'orchestrateur
- `sentinel.log`: Logs du sentinel
- `watcher.log`: Logs du watcher
- `researcher.log`: Logs du researcher
- `architect.log`: Logs de l'architect
- `skeptic.log`: Logs du skeptic
- `creative.log`: Logs du creative
- `ceo.log`: Logs du CEO
- `CRASH.log`: Logs des crashes critiques
- `escalation.log`: Logs des escalades

## Politique "ça marche ou ça crash"

Le système est conçu pour être strict:

1. **Aucune erreur silencieuse**: Toutes les erreurs sont loguées
2. **Crash sur erreur critique**: Si quelque chose d'important échoue, le système s'arrête
3. **Redémarrage automatique**: Les agents peuvent redémarrer jusqu'à 3 fois
4. **Escalade**: Les erreurs persistantes sont escaladées au CEO

## Tests

Pour vérifier que tout fonctionne:

```bash
cd agents
python test_orchestration.py
```

## Intégration avec les agents existants

Pour migrer un agent existant:

```python
from elf_agent_wrapper import AgentWrapper, AgentConfig
from elf_logging import get_logger

config = AgentConfig(
    name="mon_agent",
    description="Description de mon agent",
    icon="🤖",
    auto_start=False,
    restart_on_error=True
)

wrapper = AgentWrapper(config)
logger = get_logger("mon_agent")

# Votre code d'agent ici
def run_agent():
    logger.info("Agent démarré")
    # ...

# Exécuter avec le wrapper
wrapper.run(run_agent)
```

## Fichiers importants

- `agents/unified_orchestrator.py`: Orchestrateur principal
- `agents/elf_logging.py`: Système de logging centralisé
- `agents/elf_agent_wrapper.py`: Wrapper pour les agents
- `agents/test_orchestration.py`: Tests du système
- `scripts/start-elf-orchestrator.sh`: Script de démarrage
- `scripts/stop-elf-orchestrator.sh`: Script d'arrêt

## Prérequis

- Python 3.7+
- OpenCode CLI (`npm install -g opencode`)
- OpenCode server running on port 4096

## Dépannage

### L'orchestrateur ne démarre pas

1. Vérifier qu'OpenCode server tourne: `curl http://localhost:4096/health`
2. Vérifier les logs: `tail -f logs/unified_orchestrator.log`
3. Lancer le test: `python agents/test_orchestration.py`

### Un agent ne démarre pas

1. Vérifier le status: `python agents/unified_orchestrator.py status`
2. Vérifier les logs de l'agent: `tail -f logs/<agent>.log`
3. Essayer de le redémarrer: `python agents/unified_orchestrator.py restart <agent>`

### Erreurs silencieuses

Si vous suspectez une erreur silencieuse:
1. Vérifier `logs/CRASH.log`
2. Vérifier `logs/escalation.log`
3. Activer le mode debug dans le logging

## License

MIT - Part of the Emergent Learning Framework (ELF)
