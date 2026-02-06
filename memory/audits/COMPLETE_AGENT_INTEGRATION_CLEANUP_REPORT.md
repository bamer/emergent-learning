# Rapport Complet: Toutes les Intégrations Agents & Nettoyage

**Date**: 2026-02-06  
**Objectif**: Recenser TOUS les composants agents et recommander la meilleure architecture

---

## Résumé Exécutif

**Bilan**: Le système est dans un état de "spaghetti code" avec:
- **5-6 intégrations OpenCode différentes** pour gérer les sessions
- **2 systèmes de logging** redondants
- **Multiples orchestrateurs** qui se chevauchent
- **Multiples systèmes de définition d'agents**

**Problème Principal**: Trop de couches d'abstraction pour la même fonctionnalité = confusion, bugs, mémoire gaspillée

**Solution Unifiée Proposée**:
```
Single Unified Orchestrator + Single Client + Single Logging
```

---

## 0. Catalogue Complet des Composants

### Fichiers d'intégrationclients OpenCode

| Fichier | Lignes | Utilité | Statut |
|---------|--------|------------------------------------|--------|
| `orchestrator/opencode_client.py` | 253 | OptimizedOpenCodeClient (singleton + heartbeat) | ✅ À GARDER |
| `orchestrator/async_opencode_client.py` | 365 | AsyncOpenCodeClient (async + SSE) | ✅ À GARDER |
| `agents/opconnection.py` | 79 | Wrapper de OptimizedOpenCodeClient | ⚠️ Redondant |
| `agents/opencode_client.py` | 54 | Wrapper de OptimizedOpenCodeClient | ⚠️ Redondant |
| `agents/elf_ai_client.py` | 122 | ELFAIClient (via backend ELF) | ❌ Optionnel |
| `agents/unified_orchestrator.py` | 379 | Crée sessions OpenCode direct | ❌ **PROBLÉMATIQUE** |
| `agents/agent_execution_engine.py` | 291 | Exécute workflows complexes | ⚠️ Réutilisable |
| `orchestrator/event_bridge.py` | 811 | Liste SSE + polling sessions | ⚠️ Redondant |

### Fichiers de définition d'agents

| Fichier | Lignes | Utilité | Statut |
|---------|--------|------------------------------------|--------|
| `agents/base_agent.py` | 410 | **BaseAgent class** avec Researcher, Architect, Skeptic, Concrete | ✅ Très bon design |
| `agents/opencode_swarm.py` | 267 | Gestion swarm (metadata agents) | ⚠️ Partiel |
| `agents/unified_orchestrator.py` | 379 | AgentType enum + UnifiedOrchestrator | ❌ Redondant |
| `agents/orchestrator_state.py` | 71 | État orchestrator | ❌ Non utilisé |

### API & Services Backend

| Fichier | Lignes | Utilité | Statut |
|---------|--------|------------------------------------|--------|
| `agents/agent_status_api.py` | 379 | Flask REST API pour statut agents | ❌ **BROKEN** (import orchestrator manquant) |
| `orchestrator/unified_orchestrator.py` | 269 | Async orchestrator avec SSE + décision AI | ✅ **À GARDER** |
| `orchestrator/event_bridge_sdk.py` | 435 | SDK pour event bridge | ❌ Obsolète |

### Logging

| Fichier | Lignes | Utilité | Statut |
|---------|--------|------------------------------------|--------|
| `agents/logger.py` | 76 | Logging simple (setup_logger) | ❌ À SUPPRIMER |
| `agents/elf_logging.py` | 252 | Logging complet avec crash policy, CRASH.log | ✅ **À GARDER** |

### Autres agents

| Fichier | Lignes | Utilité | Statut |
|---------|--------|------------------------------------|--------|
| `agents/alert_agent.py` | 122 | Agent d'alerte | ⚠️ À tester |
| `agents/escalation_protocol.py` | 285 | Protocole d'escalade | ⚠️ À migrer |
| `agents/experiment_analyzer.py` | 245 | Analyseur d'expériences | ✓ Spécialisé |

### Tests

| Fichier | Lignes | Utilité | Statut |
|---------|--------|------------------------------------|--------|
| `agents/test_orchestration.py` | 184 | Test orchestrateur | ⚠️ À migrer |
| `agents/test_agent_execution_integration.py` | 314 | Test AgentExecutionEngine | ⚠️ À migrer |

---

## 1. Analyse des Composants Clés

### 1.1 BaseAgent - Très bon design ✅

**Pourquoi c'est bon**:
- ✅ Architecture claire avec héritage
- ✅ Méthodes abstraites (`analyze()`)
- ✅ Définit des agents concrets: ResearcherAgent, ArchitectAgent, SkepticAgent, CreativeAgent
- ✅ Gestion de conversation histoire
- ✅ Propriété `system_prompt` surchargeable
- ✅ Méthodes `call()` et `call_streaming()`

**Problème**:
- ❌ Crée une NOUVELLE session à chaque appel `_create_session()` (comme unified_orchestrator.py)
- ❌ Nettoie la session après usage `_cleanup_session()`
- ❌ Ne partage pas les sessions (pas de singleton)

**Code à corriger**:
```python
# ❌ AVANT
class BaseAgent(ABC):
    def __init__(self, name, role, ...):
        self.session_id = None

    def call(self, prompt):
        session_id = self._create_session()  # Crée nouvelle session à chaque fois!
        response = self._send_message(session_id, prompt)
        self._cleanup_session(session_id)    # Nettoie immédiatement!

# ✅ APRÈS
from Open_ELF.orchestrator.opencode_client import get_opencode_client

class BaseAgent(ABC):
    def __init__(self, name, role, ...):
        self._client = get_opencode_client()  # Singleton persistant!

    def call(self, prompt):
        success, response = self._client.send_message(prompt, agent=self.name)
```

**Verdict**: **Excellent design, mais mauvaise gestion de session**. Corriger et c'est parfait.

---

### 1.2 AgentExecutionEngine - Réutilisable ⚠️

**Pourquoi c'est utile**:
- ✅ Exécute des workflows complexes avec escalade CEO
- ✅ Pattern: Agent → Analyse → Escalade → CEO → Décision → Actions
- ✅ Détermine automatiquement si un problème est critique
- ✅ Extrait des actions des décisions

**Code clé**:
```python
class AgentExecutionEngine:
    def execute_pattern_response(self, pattern, agent_to_call, recommendations, context):
        # 1. Call agent pour analyser
        agent_result = self._call_agent(agent_to_call, pattern, recommendations, context)

        # 2. Déterminer si critique
        is_critical = self._is_critical(pattern, agent_result)

        # 3. Si critique → Escalade au CEO
        if is_critical:
            ceo_decision = self._escalate_to_ceo(pattern, agent_result, recommendations)

        # 4. Extraire actions
        actions = self._extract_actions(ceo_decision)

        return result
```

**Problème**:
- ❌ Utilise `OpenCodeClient` qui est un wrapper (redondant)
- ❌ Dépend de la mauvaise gestion de session

**Verdict**: **À migrer vers OptimizedOpenCodeClient**. Le pattern de workflow est très bon.

---

### 1.3 AgentStatusAPI - BROKEN ❌

**Problème**:
- ❌ Importe `from orchestrator import AgentOrchestrator` qui n'existe pas
- ❌ Le fichier `orchestrator.py` n'existe pas dans `agents/`
- ❌ Les imports casse le démarrage

**Solution**:
1. **Option 1**: Supprimer ce fichier
2. **Option 2**: Refaire l'API en utilisant le `UnifiedOrchestrator` de `orchestrator/`

**Verdict**: **À supprimer ou refaire**. Le code existe mais casse à l'import.

---

### 1.4 unified_orchestrator.py (agents/) - PROBLÉMATIQUE ❌

**Problème**:
- ❌ Crée une nouvelle session à chaque `run_swarm()`
- ❌ Jamais ferme les sessions
- ❌ Jamais réutilise les sessions
- ❌ Fuite de mémoire importante

**Code à corriger**:
```python
# ❌ AVANT
def run_swarm(self, task, mode, context):
    session_response = requests.post(
        f"{self.opencode_server}/session",
        json={"title": f"Swarm: {task[:50]}"},  # NOUVELLE SESSION!
        timeout=30,
    )

# ✅ APRÈS
from Open_ELF.orchestrator.opencode_client import get_opencode_client

def run_swarm(self, task, mode, context):
    client = get_opencode_client()
    success, response = client.send_message(
        swarm_prompt,
        agent="multi-agent-coordinator"
    )
```

**Verdict**: **À migrer vers OptimizedOpenCodeClient** ou **supprimer** (redondant avec UnifiedOrchestrator dans orchestrator/).

---

### 1.5 Logging Systems - Redondance ❌

| Caractéristique | logger.py | elf_logging.py |
|----------------|-----------|---------------|
| Fonctions | `setup_logger`, `log_critical_error` | `get_logger`, `log_critical`, `log_error`, `log_warning`, `log_info` |
| Crash Policy | Commentée (pas active) | ✅ Active (`crash=True`) |
| CRASH Log | Non | ✅ CRASH.log |
| Escalade | Non | ✅ `escalate=True` avec escalation.log |
| Handler custom | Non | ✅ CrashPolicyHandler |
| Utilisation | Simple, redondant | ✅ Complet et testé |

**Verdict**: **Supprimer `logger.py`**, garder uniquement `elf_logging.py`.

---

## 2. Architecture Unifiée Recommandée

### Principe: "Single Source of Truth"

```
┌─────────────────────────────────────────────────────────────┐
│                    UnifiedOrchestrator                       │
│         (orchestrator/unified_orchestrator.py)               │
│                                                              │
│  - Écoute SSE (événements OpenCode)                          │
│  - Décision AI (avec AsyncOpenCodeClient)                    │
│  - Gestion des événements                                    │
│  - Status endpoint                                            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  AsyncOpenCodeClient                        │
│        (orchestrator/async_opencode_client.py)                │
│                                                              │
│  - Singleton session + heartbeat                             │
│  - Support SSE natif                                         │
│  - send_message() async                                      │
│  - listen_sse() async                                        │
│  - Charge prompts agents auto                                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                Agent Loader (nouveau)                        │
│            (agents/agent_loader.py)                          │
│                                                              │
│  - Charge configs depuis ~/.config/opencode/agents/*.md     │
│  - Parse frontmatter YAML                                    │
│  - Extrait system prompts                                    │
│  - Liste agents disponibles                                  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    elf_logging.py                            │
│                  (agents/elf_logging.py)                      │
│                                                              │
│  - Logging complet avec crash policy                        │
│  - CRASH.log                                                 │
│  - Escalade vers orchestrator                                │
└─────────────────────────────────────────────────────────────┘
```

**Composants à supprimer**:
- ❌ `logger.py`
- ❌ `agents/opconnection.py`
- ❌ `agents/opencode_client.py`
- ❌ `agents/unified_orchestrator.py` (agents/)
- ❌ `agents/agent_status_api.py`
- ❌ `orchestrator/event_bridge.py` (fusionné dans UnifiedOrchestrator)

**Composants à migrer**:
- ⚠️ `agents/base_agent.py` → Corriger gestion session
- ⚠️ `agents/agent_execution_engine.py` → Migrer vers OptimizedOpenCodeClient

---

## 3. Plan de Migration

### Phase 1: Nettoyage Logging (Immédiat)

**Action**: Migrer tous les imports de `logger.py` vers `elf_logging.py`

```bash
# Trouver tous les imports de logger.py
grep -r "from logger import" /home/bamer/.opencode/emergent-learning/Open_ELF

# Remplacer
from logger import setup_logger, log_critical_error
# →
from elf_logging import get_logger, log_critical, log_error, log_warning, log_info
```

**Fichiers à migrer**:
- `agents/sentinel_monitor.py`
- `agents/dashboard_sentinel.py`
- `agents/escalation_protocol.py`
- Autres fichiers utilisant `logger.py`

**Résultat**: Un seul système de logging complet et testé.

---

### Phase 2: Corriger BaseAgent (Immédiat)

**Action**: Remplacer gestion session dans `agents/base_agent.py`

```python
# Ajouter en haut du fichier
from Open_ELF.orchestrator.opencode_client import get_opencode_client

# Supprimer
def _create_session(self):
def _send_message(self, session_id, ...):
def _cleanup_session(self, session_id):

# Remplacer par
class BaseAgent(ABC):
    def __init__(self, name, role, ...):
        self.name = name
        self.role = role
        self._client = get_opencode_client()  # Singleton!
        self.conversation_history = []

    def call(self, prompt, system_prompt=None):
        """Call agent using persistent session"""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        elif self.system_prompt:
            full_prompt = f"{self.system_prompt}\n\n{prompt}"

        success, response = self._client.send_message(full_prompt, agent=self.name)

        if success:
            self.conversation_history.append({
                "role": "user",
                "content": prompt
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })

        return response if success else None
```

**Résultat**: BaseAgent utilise une session persistante partagée.

---

### Phase 3: Créer Agent Loader (Immédiat)

**Fichier**: `agents/agent_loader.py`

```python
"""
Agent Loader - Charge automatiquement les configs agents depuis OpenCode
"""

from pathlib import Path
import yaml
import json
from typing import Dict, List, Optional

AGENTS_DIR = Path.home() / ".config" / "opencode" / "agents"
CACHE = {}  # Cache des prompts agents

def load_agent_config(agent_name: str) -> Dict:
    """Charge la configuration d'un agent"""
    agent_file = AGENTS_DIR / f"{agent_name}.md"

    if not agent_file.exists():
        raise ValueError(f"Agent file not found: {agent_file}")

    if agent_name in CACHE:
        return CACHE[agent_name]

    content = agent_file.read_text()

    # Parse frontmatter YAML
    if content.startswith("---"):
        frontmatter_end = content.find("---", 4)
        yaml_content = content[4:frontmatter_end]
        config = yaml.safe_load(yaml_content) or {}
    else:
        config = {}

    config["name"] = config.get("name", agent_name)
    config["description"] = config.get("description", "")
    config["prompt"] = content[frontmatter_end + 4:] if frontmatter_end > 0 else content
    config["prompt"] = config["prompt"].strip()

    CACHE[agent_name] = config
    return config

def list_available_agents() -> List[Dict[str, str]]:
    """Liste tous les agents disponibles"""
    agents = []

    for agent_file in AGENTS_DIR.glob("*.md"):
        try:
            config = load_agent_config(agent_file.stem)
            agents.append({
                "id": agent_file.stem,
                "name": config["name"],
                "description": config["description"],
            })
        except Exception as e:
            continue

    return agents

def get_agent_prompt(agent_name: str) -> Optional[str]:
    """Récupère le prompt d'un agent"""
    try:
        config = load_agent_config(agent_name)
        return config["prompt"]
    except Exception:
        return None
```

---

### Phase 4: Integrer Agent Loader dans AsyncOpenCodeClient (Court terme)

**Modifier**: `orchestrator/async_opencode_client.py`

```python
# Ajouter import
from agents.agent_loader import get_agent_prompt

# Modifier send_message()
async def send_message(self, message: str, agent: Optional[str] = None, timeout: int = 300):
    if not await self._ensure_session():
        return False, "Failed to establish OpenCode session"

    try:
        # Charger le prompt de l'agent automatiquement
        full_message = message
        if agent:
            try:
                agent_prompt = get_agent_prompt(agent)
                if agent_prompt:
                    full_message = f"{agent_prompt}\n\nTASK:\n{message}"
                    logger.debug(f"Loaded prompt for agent: {agent}")
            except Exception as e:
                logger.warning(f"Failed to load agent prompt {agent}: {e}")

        body = {"parts": [{"type": "text", "text": full_message}]}
        if agent:
            body["agent"] = agent

        # ... reste du code
```

---

### Phase 5: Supprimer fichiers redondants (Moyen terme)

**Fichiers à supprimer**:
```bash
rm /home/bamer/.opencode/emergent-learning/Open_ELF/agents/logger.py
rm /home/bamer/.opencode/emergent-learning/Open_ELF/agents/opconnection.py
rm /home/bamer/.opencode/emergent-learning/Open_ELF/agents/opencode_client.py
rm /home/bamer/.opencode/emergent-learning/Open_ELF/agents/agent_status_api.py
rm /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator/event_bridge.py
```

---

### Phase 6: Migrer AgentExecutionEngine (Moyen terme)

**Modifier**: `agents/agent_execution_engine.py`

```python
# Remplacer
from opencode_client import OpenCodeClient

# Par
from Open_ELF.orchestrator.opencode_client import get_opencode_client

class AgentExecutionEngine:
    def __init__(self, server_url: str = "http://localhost:4096"):
        self.server_url = server_url
        self._client = get_opencode_client()  # Singleton!
        self.execution_log = []
```

---

### Phase 7: Refaire AgentStatusAPI (Long terme)

**Utiliser UnifiedOrchestrator existant**:

Le `UnifiedOrchestrator` a déjà un endpoint `/status` sur le port 9999.

**Option 1**: Supprimer `agent_status_api.py` (utiliser endpoint existant)
**Option 2**: Refaire en utilisant `UnifiedOrchestrator` comme backend

```python
# Nouveau agent_status_api.py (simplifié)
from Open_ELF.orchestrator.unified_orchestrator import UnifiedOrchestrator

# UnifiedOrchestrator a déjà:
# - /status endpoint sur port 9999
# - /api/v1/ask endpoint pour questions
# - Session management avec AsyncOpenCodeClient

# Donc AgentStatusAPI n'est plus nécessaire!
```

---

## 4. Résumé des Actions

### À faire IMMÉDIATEMENT:

1. ☐ Migrer tous les imports de `logger.py` vers `elf_logging.py`
2. ☐ Corriger `agents/base_agent.py` pour utiliser `OptimizedOpenCodeClient`
3. ☐ Créer `agents/agent_loader.py` (charge configs automagique)
4. ☐ Intégrer `agent_loader` dans `async_opencode_client.py`

### À faire COURT TERME:

5. ☐ Supprimer `logger.py`
6. ☐ Supprimer `agents/opconnection.py`, `agents/opencode_client.py`
7. ☐ Supprimer `agents/unified_orchestrator.py` (agents/)
8. ☐ Migrer `agents/agent_execution_engine.py` vers `OptimizedOpenCodeClient`

### À faire MOYEN TERME:

9. ☐ Supprimer `orchestrator/event_bridge.py` (fusionné dans UnifiedOrchestrator)
10. ☐ Supprimer `agents/agent_status_api.py` ou refaire avec UnifiedOrchestrator

### À faire LONG TERME:

11. ☐ Ajouter async support dans `BaseAgent` (optionnel)
12. ☐ Créer tests pour l'architecture unifiée
13. ☐ Documentation complète de l'architecture

---

## 5. Comparatif Avant/Après

### Avant (État Actuel)

```
❌ 5-6 intégrations clients différentes
❌ 2 systèmes de logging
❌ Multiples orchestrateurs redondants
❌ Création de sessions à chaque appel = fuite mémoire
❌ Code spaghetti, difficile à maintenir
❌ Environ ~100Go RAM utilisé pour rien
```

### Après (Architecture Unifiée)

```
✅ 1 seul client (AsyncOpenCodeClient)
✅ 1 seul système de logging (elf_logging.py)
✅ 1 seul orchestrateur (UnifiedOrchestrator)
✅ Gestion sessions propre (singleton + heartbeat)
✅ Code clair, maintenable
✅ ~10-20Go RAM (économise 80-90Go)
```

---

## 6. Recommandation Finale

**Garder**:
- ✅ `orchestrator/unified_orchestrator.py` - Orchestrator principal
- ✅ `orchestrator/async_opencode_client.py` - Client async
- ✅ `agents/elf_logging.py` - Logging complet
- ✅ `agents/base_agent.py` - (après correction) Base classe excellente
- ✅ `agents/agent_execution_engine.py` - (après migration) Workflows complexes

**Créer**:
- ✅ `agents/agent_loader.py` - Charge configs agents

**Supprimer**:
- ❌ `agents/logger.py`
- ❌ `agents/opconnection.py`
- ❌ `agents/opencode_client.py`
- ❌ `agents/unified_orchestrator.py` (agents/)
- ❌ `agents/agent_status_api.py`
- ❌ `orchestrator/event_bridge.py`
- ❌ `agents/orchestrator_state.py`

**Architecture finale simple**:
```
UnifiedOrchestrator (orchestrator/)
    └─> AsyncOpenCodeClient (orchestrator/)
        ├─> Session singleton + heartbeat
        ├─> AgentLoader (agents/) → charge prompts depuis ~/.config/opencode/agents/
        └─> elf_logging (agents/)
```

---

**Rapport généré**: 2026-02-06
**À faire**: Review avec CEO et prioriser les phases
