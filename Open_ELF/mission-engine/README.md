# Mission Engine - Composant Autonome de Gestion des Missions

Le **Mission Engine** est un composant autonome qui gère l'exécution des missions de l'onglet Live et fournit un orchestrateur de workflow complet pour le système ELF.

## 🚀 Fonctionnalités

- **Gestion des missions** : Création, exécution et suivi des missions
- **Intégration Live Tab** : Missions spécifiques pour l'onglet Live
- **Workflow intelligent** : Analyse par agent, détection de criticité, escalation CEO
- **File d'attente** : Gestion priorisée des missions
- **Mode asynchrone** : Traitement en arrière-plan
- **Callbacks** : Système d'événements extensible
- **Intégration AgentManager** : Utilise les vrais agents définis dans les fichiers .md

## 📁 Structure

```
mission-engine/
├── __init__.py              # Exports principaux
├── config.py                # Configuration
├── models.py                # Modèles de données (Mission, MissionResult, etc.)
├── mission_engine.py        # Moteur principal
├── mission_live_handler.py  # Gestionnaire spécifique Live Tab
└── README.md               # Cette documentation
```

## 🛠️ Installation

Le composant est autonome et ne nécessite pas d'installation spécifique. Assurez-vous juste que les dépendances sont disponibles :

```bash
# Le composant utilise AgentManager depuis ../agents/
# Assurez-vous que le serveur OpenCode est accessible
# Par défaut sur http://localhost:4096
```

## 📖 Usage Basique

### Créer et exécuter une mission

```python
from mission_engine import MissionEngine, MissionPriority

# Créer le moteur
engine = MissionEngine()

# Créer une mission
mission = engine.create_mission(
    title="Analyser le système",
    description="Vérifier l'état de tous les services",
    agent="sentinel",
    priority=MissionPriority.HIGH
)

# Exécuter
result = engine.execute_mission(mission.id)
print(f"Résultat: {result.output}")
```

### Gestion des missions Live

```python
from mission_engine import MissionEngine, LiveMissionHandler

engine = MissionEngine()
handler = LiveMissionHandler(engine)

# Créer une mission Live
mission = handler.create_live_mission(
    title="🔍 Analyse sécurité",
    description="Vérifier les vulnérabilités",
    agent="sentinel",
    priority="HIGH"
)

# Récupérer le dashboard
 dashboard = handler.get_live_dashboard()
print(f"Missions actives: {dashboard['stats']['total']}")

# Démarrer les mises à jour auto
handler.start_live_updates()
```

### Mode asynchrone

```python
# Démarrer le traitement en arrière-plan
engine.start_background_processing()

# Les missions sont automatiquement traitées
create_mission(...)
create_mission(...)

# Arrêter
engine.stop_background_processing()
```

## 🔧 Configuration

### Variables d'environnement

```bash
# URLs
export OPENCODE_URL="http://localhost:4096"
export EVENT_BRIDGE_URL="http://localhost:9998"

# Chemins
export AGENTS_DIR="/home/bamer/.opencode/agents/OPC_ELF_System_Agents"
export MISSIONS_DB_PATH="/path/to/missions.db"
export MISSION_LOGS_DIR="/path/to/logs"

# Comportement
export AUTO_ESCALATE_CRITICAL="true"
export CEO_REVIEW_THRESHOLD="0.8"
export LIVE_TAB_AUTO_REFRESH="true"
export LIVE_TAB_REFRESH_INTERVAL="30"
```

### Configuration par code

```python
from mission_engine import MissionEngine, MissionEngineConfig

config = MissionEngineConfig(
    opencode_url="http://localhost:4096",
    auto_escalate_critical=True,
    live_tab_refresh_interval=30,
    log_level="DEBUG"
)

engine = MissionEngine(config)
```

## 📊 Workflow d'exécution

```
1. Création de la mission
        ↓
2. Ajout à la file d'attente
        ↓
3. Détection du pattern (optionnel)
        ↓
4. Analyse par l'agent
        ↓
5. Détection de criticité
        ↓
6. Escalade CEO si critique
        ↓
7. Extraction des actions
        ↓
8. Finalisation
```

## 🎯 Types de missions

- **LIVE_TAB** : Missions affichées dans l'onglet Live
- **PATTERN_RESPONSE** : Réponse à un pattern détecté
- **AGENT_TASK** : Tâche spécifique d'agent
- **CEO_ESCALATION** : Escalade vers le CEO
- **SYSTEM_MAINTENANCE** : Maintenance système
- **CUSTOM** : Mission personnalisée

## 📡 Callbacks et Événements

### Mission Engine

```python
def on_mission_created(mission):
    print(f"Nouvelle mission: {mission.title}")

def on_mission_completed(mission):
    print(f"Mission terminée: {mission.id}")

engine.on("mission_created", on_mission_created)
engine.on("mission_completed", on_mission_completed)
```

### Live Mission Handler

```python
def on_live_updated(live_view):
    print(f"Mise à jour: {live_view.status}")

handler.on("live_mission_updated", on_live_updated)
handler.on("live_status_changed", lambda v, old: print(f"{old} → {v.status}"))
```

## 🔍 Monitoring

### Statistiques

```python
stats = engine.get_stats()
print(f"""
Total missions: {stats['total_missions']}
En attente: {stats['pending']}
En cours: {stats['running']}
Terminées: {stats['completed']}
Missions Live: {stats['live_missions']}
""")
```

### Dashboard Live

```python
# Export JSON pour l'interface
dashboard = handler.get_live_dashboard()
json_data = handler.export_live_missions_json()
```

## 🔄 Intégration avec l'ancien AgentExecutionEngine

Le Mission Engine remplace l'ancien `AgentExecutionEngine` avec une architecture plus modulaire :

```python
# Ancien code (agent_execution_engine.py)
from agents.agent_execution_engine import AgentExecutionEngine
engine = AgentExecutionEngine()
result = engine.execute_pattern_response(pattern, agent, recs, context)

# Nouveau code (mission_engine)
from mission_engine import MissionEngine, LiveMissionHandler
engine = MissionEngine()
handler = LiveMissionHandler(engine)
mission = handler.create_pattern_response_mission(pattern, agent, recs, context)
result = engine.execute_mission(mission.id)
```

## 🧪 Tests

```bash
# Test basique
cd emergent-learning/Open_ELF/mission-engine
python -c "from mission_engine import MissionEngine; e = MissionEngine(); print('OK')"

# Test avec AgentManager
python mission_engine.py

# Test Live Handler
python mission_live_handler.py
```

## 📝 Notes

- Chaque mission a un ID unique (8 caractères)
- Les missions Live ont un ID spécifique (`live_` + ID)
- L'AgentManager est utilisé automatiquement s'il est disponible
- Les sessions agent sont réutilisées (pattern singleton)
- Le modèle utilisé est lu depuis le fichier .md de l'agent

## 🔗 Dépendances

- `agent_manager` : Gestionnaire d'agents (dans ../agents/)
- `requests` : Pour les appels API OpenCode
- Python 3.8+

## 👥 Agents supportés

Tous les agents définis dans `agents/OPC_ELF_System_Agents/` :
- sentinel
- sentinel
- ceo
- researcher
- architect
- creative
- skeptic
- unified-orchestrator
- learning-extractor

## 📄 Licence

Partie du système ELF - OpenCode
