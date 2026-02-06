# Architecture Finale Unified ELF - Édition Utilisateur

**Date**: 2026-02-06  
**Définit par**: Utilisateur

---

## Les 3 Seuls Composants Nécessaires

```
Open_ELF/
├── orchestrator/
│   ├── unified_orchestrator.py          ← **ORCHESTRATION**
│   │   ├─> Gère WORKFLOWS
│   │   ├─> Gère DÉCISIONS IA
│   │   ├─> Découverte d'agents
│   │   ├─> Escalade CEO
│   │   └─> Coordination multi-agents
│   │
│   └── event_bridge.py                  ← **COMMUNICATION**
│       ├─> Gère SESSIONS (singleton)
│       ├─> Gère HTTP/SSE
│       ├─> Heartbeat
│       ├─> Hooks ELF
│       └─> Point d'entrée UNIQUE vers OpenCode
│
└── agents/
    └── elf_logging.py                    ← **INFRASTRUCTURE**
        ├─> Logging unifié
        ├─> Crash policy
        └─> CRASH.log
```

---

## Responsabilités Claires

### 1. unified_orchestrator.py - Orchestration Layer

**Ce qu'il fait:**
- Orchestre les workflows complexes
- Prend les décisions IA (escalade, retry, skip, etc.)
- Charge les agents depuis `~/.config/opencode/agents/*.md`
- Gère les swarms multi-agents
- Découverte d'agents disponibles

**Ce qu'il NE fait PAS:**
- ❌ Gère directement les sessions OpenCode
- ❌ Fait des requêtes HTTP directes vers localhost:4096
- ❌ Écoute SSE directement

**Comment il communique:**
```python
# Dans unified_orchestrator.py

class UnifiedOrchestrator:
    def __init__(self):
        self.bridge = EventBridge()  # Utilise event_bridge pour communication

    def run_agent_workflow(self, agent_name: str, task: str):
        """
        Orchestre un workflow d'agent.

        1. Charge le prompt de l'agent
        2. Prépare le message
        3. Déduit via event_bridge
        4. Prend une décision
        """
        # Charge prompt (responsabilité d'orchestration)
        agent_prompt = self._load_agent_prompt(agent_name)
        full_message = f"{agent_prompt}\n\nTASK:\n{task}"

        # Délègue à bridge (responsabilité de communication)
        response = self.bridge.send_message(full_message, agent=agent_name)

        # Décision IA
        decision = self._decide_next_action(response)

        return decision
```

---

### 2. event_bridge.py - Communication Layer

**Ce qu'il fait:**
- Gestion UNIQUE des sessions OpenCode (singleton)
- HTTP requests vers localhost:4096
- SSE listening (événements OpenCode)
- Heartbeat session keepalive
- Hooks ELF (UserPromptSubmit, PostToolUse, PreToolUse, learning-loop)
- Status endpoint Web

**Ce qu'il NE fait PAS:**
- ❌ Prend des décisions IA
- ❌ Orchestre des workflows complexes
- ❌ Charge des prompts d'agents

**Règle d'Or:**
> **Toute fonction qui instancie ou tente d'ouvrir une session en direct sur le serveur opencode devrait être éradiquée.**

**API publique:**
```python
# Dans event_bridge.py

class EventBridge:
    # Gestion communication
    def send_message(message: str, agent: Optional[str] = None) -> str:
        """Envoyer message via session unique"""

    def send_message_async(message: str, agent: Optional[str] = None) -> str:
        """Envoyer message async"""

    # Hooks (pour ELF)
    def run_hook(hook_type: str, event_data: dict) -> bool:
        """Déclencher hook ELF"""
```

---

### 3. elf_logging.py - Infrastructure Layer

**Ce qu'il fait:**
- Logging unifié pour tout le système
- Crash policy (ça marche ou ça crash)
- CRASH.log (erreurs critiques)
- Escalade log

**API:**
```python
from agents.elf_logging import get_logger, log_critical, log_error, log_warning, log_info

logger = get_logger("my_component")
logger.info("Message")

# Ou direct
log_critical("my_agent", "Critical error", crash=True)
```

---

## Flux de Données

### Exemple: Workflow Agent Orchestration

```
User Request
    ↓
unified_orchestrator.run_agent_workflow()
    ↓
    1️⃣ Charge agent prompt
    ↓
    2️⃣ Orchestrat workflow (décisions)
    ↓
    3️⃣ Déduit à event_bridge.send_message()
    ↓
event_bridge (Communication)
    └─> Gère session unique
        └─> Envoie à OpenCode (localhost:4096)
            └─> Récupération via SSE
                ↓
            Réponse retourne
                ↓
unified_orchestrator
    └─> Analyse réponse
        └─> Décision prochaine action
            ↓
elf_logging (Infrastructure)
```

### Exemple: Event Hook

```
OpenCode Event (via SSE)
    ↓
event_bridge._listen_events()
    ↓
    1️⃣ Parse événement
    ↓
    2️⃣ Déclenche hook (run_hook)
    ↓
    ├─> UserPromptSubmit → Hook ELF
    ├─> PostToolUse → Hook ELF
    └─> learning-loop → Hook ELF
            ↓
elf_logging (log)
```

---

## Fichiers à SUPPRIMER (radicalement)

### ❌ Toute instanciation directe de sessions

```bash
# Ces fichiers créent directement des sessions → SUPPRIMER/MIGRER
rm agents/unified_orchestrator.py  # (agents/, PAS orchestrator/)
rm agents/opconnection.py
rm agents/opencode_client.py
rm agents/agent_status_api.py  # Redondant
```

### ❌ Redondants

```bash
rm agents/logger.py  # Fusionné dans elf_logging.py
rm orchestrator/async_opencode_client.py  # Fonctionnalités fusionnées dans event_bridge.py
```

### ⚠️ À archiver (si jamais besoin)

```bash
# Si unified_orchestrator.py (orchestrator/) fait des décisions supplémentaires
# vérifier si ces fonctionnalités sont nécessaires
mv orchestrator/unified_orchestrator.py archived/orchestrator/
```

---

## Migration Plan

### Étape 1: Renforcer event_bridge.py (Communication Layer)

**Ajouter dans event_bridge.py:**
- ✅ Session singleton (optimisé)
- ✅ Heartbeat auto (déjà présent)
- ✅ Async communication (aiohttp)
- ✅ Status endpoint (déjà présent)
- ✅ Hooks ELF (déjà présent)

**Code à ajouter:**
```python
# Dans event_bridge.py

class EventBridge:
    def __init__(self):
        # Session singleton
        self.opencode_session_id = None
        self.http_session = requests.Session()  # Réutiliser connexion HTTP
        self.session_lock = threading.Lock()

        # Heartbeat thread
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_worker, daemon=True
        )
        self.heartbeat_thread.start()

    async def send_message_async(self, message: str, agent: Optional[str] = None):
        """Envoyer message async avec aiohttp"""
        if not self.opencode_session_id:
            await self._ensure_session()

        # ... implémentation async
```

---

### Étape 2: Renforcer unified_orchestrator.py (Orchestration Layer)

**Ajouter dans unified_orchestrator.py:**
- ✅ Agent discovery (`~/.config/opencode/agents/*.md`)
- ✅ Agent prompt loading
- ✅ Decision engine (escalade, retry, etc.)
- ✅ Swarm coordination

**Code à utiliser:**
```python
# Dans unified_orchestrator.py

from pathlib import Path
import yaml

AGENTS_DIR = Path.home() / ".config" / "opencode" / "agents"

class UnifiedOrchestrator:
    def __init__(self):
        self.bridge = EventBridge()  # Déle guée communication
        self.agents_cache = {}

    def _load_agent_prompt(self, agent_name: str) Optional[str]:
        """Charge prompt d'agent depuis OpenCode config"""
        agent_file = AGENTS_DIR / f"{agent_name}.md"

        if not agent_file.exists():
            logger.warning(f"Agent {agent_name} not found")
            return None

        if agent_name in self.agents_cache:
            return self.agents_cache[agent_name]

        content = agent_file.read_text()

        # Parse frontmatter
        if content.startswith("---"):
            frontmatter_end = content.find("---", 4)
            yaml_content = content[4:frontmatter_end]
            prompt = content[frontmatter_end + 4:].strip()
        else:
            prompt = content.strip()

        self.agents_cache[agent_name] = prompt
        return prompt

    def run_agent(self, agent_name: str, task: str) -> str:
        """Orchestre appel agent"""
        # 1. Charge prompt
        agent_prompt = self._load_agent_prompt(agent_name)

        # 2. Prépare message
        full_message = f"{agent_prompt}\n\nTASK:\n{task}" if agent_prompt else task

        # 3. Délègue à bridge
        response = self.bridge.send_message(full_message, agent=agent_name)

        return response

    def run_swarm(self, task: str, agents_sequence: List[str]):
        """Orchestre swarm multi-agents"""
        results = []

        for agent_name in agents_sequence:
            logger.info(f"🤖 Running agent: {agent_name}")
            response = self.run_agent(agent_name, task)

            results.append({
                "agent": agent_name,
                "response": response
            })

            # Optionnel: décider d'arrêter le swarm si réponse suffisante
            if self._is_sufficient(response):
                break

        return results
```

---

### Étape 3: Migrer appelants

**Avant (CRÉATION SESSION DIRECTE):**
```python
# ❌ À remplacer
session_response = requests.post(
    f"http://localhost:4096/session",
    json={"title": "Session"},
    timeout=30
)
session_id = session_response.json()["id"]
response = requests.post(f"http://localhost:4096/session/{session_id}/message", ...)
```

**Après (DÉLÉGATION À EVENT_BRIDGE):**
```python
# ✅ Utiliser unified_orchestrator
orchestrator = UnifiedOrchestrator()
response = orchestrator.run_agent("researcher", "Analyze this code")
```

**ou même:**

```python
# ✅ Direct avec event_bridge
from orchestrator.event_bridge import EventBridge

bridge = EventBridge()
response = bridge.send_message("Analyze this code", agent="researcher")
```

---

## Diagramme d'Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   unified_orchestrator.py                   │
│                         (ORCHESTRATION)                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Agent Discovery                                   │  │
│  │  - ~/.config/opencode/agents/*.md                   │  │
│  │  - Load prompts                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Decision Engine                                   │  │
│  │  - Escalate to CEO                                 │  │
│  │  - Retry / Skip                                    │  │
│  │  - Swarm coordinator                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                 │
└───────────────────────────┼─────────────────────────────────┘
                            │ Délégation
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     event_bridge.py                        │
│                        (COMMUNICATION)                      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Session Management (SINGLETON)                     │  │
│  │  - Create session once                              │  │
│  │  - Heartbeat keepalive                              │  │
│  │  - Reuse for all calls                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  HTTP/SSE Layer                                    │  │
│  │  - Requests to localhost:4096                      │  │
│  │  - SSE listening                                   │  │
│  │  - Hooks ELF (UserPromptSubmit, PostToolUse...)     │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                 │
└───────────────────────────┼─────────────────────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   OpenCode      │
                   │  (4096)         │
                   └─────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   elf_logging.py                            │
│                      (INFRASTRUCTURE)                       │
│                                                              │
│  - Centralized logging                                       │
│  - Crash policy                                             │
│  - CRASH.log                                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Benefits de cette Architecture

### 1. **Single Source of Truth pour Sessions**
- **Règle**: Toute instanciation de session OpenCode → ÉRADICATÉE
- Seul `event_bridge.py` gère les sessions
- Économie de RAM: ~80-90 Go

### 2. **Séparation des Responsabilités**
- Orchestration (workflows, décisions) → `unified_orchestrator.py`
- Communication (sessions, HTTP, SSE) → `event_bridge.py`
- Infrastructure (logs) → `elf_logging.py`

### 3. **Extensibilité**
- Ajouter agent? → Mettre fichier dans `~/.config/opencode/agents/`
- Ajouter workflow? → Ajouter méthode dans `unified_orchestrator.py`
- Ajouter hook? → Hook python dans `~/.opencode/hooks/`

### 4. **Maintenabilité**
- Plus besoin de "chercher ou est la session"
- Points d'entrée clairs
- Code prévisible

### 5. **Testabilité**
- Chaque couche testable indépendamment
- Mock event_bridge pour tester unified_orchestrator
- Mock unified_orchestrator pour tester event_bridge

---

## Checklist de Validation

### Phase 1: Communication Layer (event_bridge.py)

- [ ] Session singleton implémenté
- [ ] Heartbeat actif (5 min)
- [ ] Send message async disponible
- [ ] SSE listening opérationnel
- [ ] Hooks fonctionnent (UserPromptSubmit, PostToolUse, etc.)
- [ ] Status endpoint actif

### Phase 2: Orchestration Layer (unified_orchestrator.py)

- [ ] Chargement d'agents depuis `~/.config/opencode/agents/`
- [ ] Frontmatter YAML parsing
- [ ] Run agent workflow
- [ ] Run swarm multi-agents
- [ ] Decision engine (escalade, retry)

### Phase 3: Nettoyage

- [ ] Supprimé `agents/logger.py` (fusionné)
- [ ] Supprimé `agents/opconnection.py` (éradiqué)
- [ ] Supprimé `agents/opencode_client.py` (éradiqué)
- [ ] Supprimé `agents/agent_status_api.py` (redondant)
- [ ] Supprimé `orchestrator/async_opencode_client.py` (fusionné)
- [ ] Supprimé `agents/unified_orchestrator.py` (éradiqué sessions directes)
- [ ] Migré tous les appelants vers `unified_orchestrator.py` ou `event_bridge.py`

### Phase 4: Logging

- [ ] Tous les imports de `logger.py` remplacés par `elf_logging.py`
- [ ] CRASH.log existe
- [ ] Crash policy fonctionnelle

---

## Conclusion

**Architecture Finalisée:**

```
unified_orchestrator.py: WORKFLOWS + DÉCISIONS → Orchestration Layer
event_bridge.py:        SESSIONS + HTTP/SSE → Communication Layer
elf_logging.py:          LOGS → Infrastructure Layer
```

**Règle d'Or:**
> Toute fonction qui instancie ou tente d'ouvrir une session en direct sur le serveur opencode
> devrait être éradiquée.

**Résultat attendu:**
- ✅ Architecture propre et logique
- ✅ Économie de RAM: ~80-90 Go
- ✅ Code maintainable
- ✅ Points d'entrée uniques

**Architecture approuvée par utilisateur!** 🎉
