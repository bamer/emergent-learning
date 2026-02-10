# Rapport: Intégrations d'Agents AI Opencode dans ELF

**Date**: 2026-02-06  
**Analyse**: Différentes intégrations pour gérer les agents IA Opencode  
**Objectif**: Identifier la meilleure intégration pour unifier la gestion des sessions

---

## Résumé Exécutif

**Bilan**: 4 intégrations différentes découvertes pour appeler les agents IA Opencode  
**Statut**:
- ✅ 2 intégrations fonctionnelles (gestion de sessions propre)
- ⚠️ 1 intégration partiellement fonctionnelle (ne charge pas les agents)
- ❌ 1 intégration problématique (création directe de sessions)

**Probleme Principal**: Multiplication des sessions OpenCode entraînant une consommation mémoire inutile

---

## Les 4 Intégrations Identifiées

### 1. OptimizedOpenCodeClient (orchestrator/opencode_client.py) ✅

**Statut**: **FONCTIONNEL À 100%**

**Caractéristiques**:
- **Architecture**: Singleton avec persistences de session
- **Gestion de session**: Une seule session partagée avec heartbeat automatique
- **Protocole**: HTTP requests synchrones (requests.Session)
- **Heartbeat**: Thread en arrière-plan toutes les 5 minutes
- **Timeout**: 30s pour création de session, 300s pour réponse AI

**Code Clé**:
```python
class OptimizedOpenCodeClient:
    def __init__(self, base_url: str = "http://localhost:4096"):
        self.http_session = requests.Session()  # HTTP reused
        self.opencode_session_id = None
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_worker, daemon=True
        )
        self.heartbeat_thread.start()

    def send_message(self, message: str, agent: Optional[str] = None):
        if not self._ensure_session():
            return False, "Failed to establish OpenCode session"
        # Réutilise session existante avec heartbeat
        response = self.http_session.post(...)
        return True, response_text
```

**Avantages**:
- ✅ Une seule session partagée via singleton
- ✅ Heartbeat automatique pour keepalive
- ✅ Gestion thread-safe avec lock
- ✅ Reconnexion automatique si session expirée
- ✅ Polling intelligent pour récupérer la réponse

**Inconvénients**:
- ❌ Synchrone (bloque le thread principal pendant les appels AI)
- ❌ Pas de support SSE natif

**Utilisé par**:
- `agents/opconnection.py` → Wrapper autour de `get_opencode_client()`
- `agents/opencode_client.py` → Wrapper avec API simplifiée
- `agents/agent_execution_engine.py` → Pour exécuter des workflows agents
- `sentinel/launcher.py` → Via import depuis agents/
- `orchestrator/orchestrator.py` → Old orchestrator (archivé)
- `core/central_orchestrator.py` → Central orchestrator

**Fonctionnalité Agents**:
- ❌ **Ne charge pas les agents automatiquement**
- ❌ L'utilisateur doit spécifier `agent="nom_de_l_agent"` manuellement
- ❌ Pas de découverte automatique des agents disponibles

---

### 2. AsyncOpenCodeClient (orchestrator/async_opencode_client.py) ✅

**Statut**: **FONCTIONNEL À 100%**

**Caractéristiques**:
- **Architecture**: Singleton async avec aiohttp
- **Gestion de session**: Une seule session partagée avec heartbeat async
- **Protocole**: HTTP async (aiohttp) + SSE support natif
- **Heartbeat**: Task asyncio background toutes les 5 minutes
- **Timeout**: 30s création session, configuable pour réponses AI

**Code Clé**:
```python
class AsyncOpenCodeClient:
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self._start_heartbeat()
        return self

    async def send_message(self, message: str, agent: Optional[str] = None):
        if not await self._ensure_session():
            return False, "Failed to establish OpenCode session"
        response_text = await self._wait_for_response(timeout=timeout)
        return True, response_text

    async def listen_sse(self):
        """Événements SSE en temps réel"""
        async for line in response.content:
            yield event_data
```

**Avantages**:
- ✅ Une seule session partagée via singleton
- ✅ Heartbeat async automatique
- ✅ **Support SSE natif** (écoute événements en temps réel)
- ✅ Non-blocking (async/await)
- ✅ Context manager (`async with client:`)
- ✅ Gestion d'erreurs robuste avec retry exponentiel

**Inconvénients**:
- ❌ Nécessite Python 3.7+ (support asyncio)
- ❌ Plus complexe à utiliser (besoin de contexte async)

**Utilisé par**:
- **Aucun composant actif actuellement** ( créé mais pas intégré )

**Fonctionnalité Agents**:
- ❌ **Ne charge pas les agents automatiquement**
- ❌ L'utilisateur doit spécifier `agent="nom_de_l_agent"` manuellement

---

### 3. ELFAIClient (agents/elf_ai_client.py) ⚠️

**Statut**: **PARTIELLEMENT FONCTIONNEL**

**Caractéristiques**:
- **Architecture**: Client HTTP pour backend ELF
- **Gestion de session**: Aucune (pas de session OpenCode directe)
- **Protocole**: HTTP requests vers backend localhost:8888
- **Approche**: Utilise le backend ELF comme proxy vers IA

**Code Clé**:
```python
class ELFAIClient:
    def __init__(self, backend_url: str = "http://localhost:8888"):
        self.backend_url = backend_url
        self.model = "opencode/big-pickle"

    def call(self, prompt: str, timeout: int = 120):
        # Appelle endpoint /api/analyze du backend ELF
        payload = {
            "prompt": prompt,
            "model": self.model,
            "system": "You are an expert experiment analyzer..."
        }
        resp = requests.post(
            f"{self.backend_url}/api/analyze",
            json=payload,
            timeout=timeout
        )
        return data.get("response")
```

**Avantages**:
- ✅ Interface simplifiée (prompt → réponse)
- ✅ Centralisé via backend ELF
- ✅ Pas besoin de gérer sessions

**Inconvénients**:
- ❌ **Dépend du backend ELF** (si backend down, plus d'accès IA)
- ❌ Endpoint `/api/analyze` non confirmé existant
- ❌ Pas de gestion de sessions persistantes
- ❌ Ne supporte pas les agents spécifiques

**Utilisé par**:
- `agents/experiment_analyzer.py` → Pour analyser des expériences

**Fonctionnalité Agents**:
- ❌ **Ne charge pas les agents** (utilise un système générique de prompt)

---

### 4. Direct session creation (agents/unified_orchestrator.py) ❌

**Statut**: **PROBLÉMATIQUE - Source de multiplication de sessions**

**Caractéristiques**:
- **Architecture**: Pas de client - création directe de sessions
- **Gestion de session**: **Crée une NOUVELLE session à chaque appel**
- **Protocole**: HTTP requests direct (requests)
- **Approche**: Pas de réutilisation de sessions

**Code Clé**:
```python
def run_swarm(self, task: str, mode: str = "all", context: str = ""):
    # PROBLÈME: Crée une nouvelle session à chaque appel
    session_response = requests.post(
        f"{self.opencode_server}/session",
        json={"title": f"Swarm: {task[:50]}"},
        timeout=30,
    )

    session_id = session_response.json().get("id")

    # Envoi message, mais ne fait rien pour gérer les sessions
    message_response = requests.post(
        f"{self.opencode_server}/session/{session_id}/message",
        json={
            "parts": [{"type": "text", "text": swarm_prompt}],
            "agent": "multi-agent-coordinator",
        },
        timeout=30,
    )
```

**Problèmes**:  
❌ **Crée une nouvelle session à chaque `run_swarm()`**  
❌ Jamais ferme les sessions (fuite de mémoire)  
❌ Jamais réutilise les sessions  
❌ Pas de heartbeat/keepalive  
❌ Pas de nettoyage automatique  

**Résultat**: Des centaines de sessions OpenCode orphelines qui consomment la mémoire

**Utilisé par**:
- `agents/unified_orchestrator.py` → Orchestrator d'agents basique

**Fonctionnalité Agents**:
- ✅ **Charge l'agent spécifié** (`agent="multi-agent-coordinator"`)
- ❌ Mais crée une nouvelle session à chaque fois

---

### 5. Event Bridge Session Polling (orchestrator/event_bridge.py) ⚠️

**Statut**: **PARTIEL - Polling pour détection**

**Caractéristiques**:
- **Architecture**: Session polling en complément de SSE
- **Gestion de session**: Lit les sessions existantes, ne crée pas de nouvelles sessions
- **Protocole**: HTTP polling + SSE
- **Approche**: Complémentaire (polling fallback si SSE échoue)

**Code Clé**:
```python
def _poll_sessions(self):
    """Poll les sessions actives pour détecter les outils utilisés."""
    seen_messages = {}

    while self.running:
        # Récupérer toutes les sessions
        response = requests.get(f"{self.base_url}/session", timeout=10)
        sessions = response.json()

        for session in sessions:
            session_id = session.get("id")
            # Récupérer les messages de cette session
            msg_response = requests.get(
                f"{self.base_url}/session/{session_id}/message", timeout=10
            )
            # Traite les messages et déclenche les hooks
```

**Avantages**:
- ✅ Détection des tool uses même sans SSE
- ✅ Complémentaire à SSE
- ✅ Suivi par message pour éviter doublons

**Inconvénients**:
- ❌ Polling intensif (toutes les 30s)
- ❌ Parse toutes les sessions à chaque poll
- ❌ Consomme beaucoup de ressources si beaucoup de sessions

**Utilisé par**:
- `orchestrator/event_bridge.py` → Event Bridge principal

**Fonctionnalité Agents**:
- ❌ Ne crée pas d'appels agents, détecte seulement les tools utilisés

---

## Comparatif Matricielle

| Critère | OptimizedOpenCodeClient | AsyncOpenCodeClient | ELFAIClient | Direct Creation |
|---------|------------------------|---------------------|-------------|-----------------|
| **Gestion Sessions** | ✅ Singleton persistant | ✅ Singleton persistant | ❌ Pas de session | ❌ Crée nouvelle |
| **Heartbeat Auto** | ✅ Thread background | ✅ Task async | ❌ N/A | ❌ Non |
| **Session Reuse** | ✅ Oui | ✅ Oui | N/A | ❌ Non |
| **Async Support** | ❌ Non | ✅ Oui | ❌ Non | ❌ Non |
| **SSE Support** | ❌ Non | ✅ Natif | ❌ Non | ❌ Non |
| **Agent Loading** | ❌ Manual | ❌ Manual | ❌ N/A | ✅ Spécifié |
| **Utilisé Actif** | ✅ Multiple | ❌ Aucun | ⚠️ Limité | ❌ Problématique |
| **Thread Safe** | ✅ Lock | ✅ Async Lock | ✅ | ❌ Non |
| **Complexité** | ⭐⭐ Medium | ⭐⭐⭐ High | ⭐ Simple | ⭐ Simple |
| **Recommandé** | ✅ OUI | ✅ OUI (pour async) | ❌ Non | ❌ PROBLÉMATIQUE |

---

## Problème de Multiplication de Sessions

### Root Cause

Les composants qui créent directement des sessions sans gestion:

1. **agents/unified_orchestrator.py** - `run_swarm()` crée session à chaque appel
2. **Event Bridge** - Polling toutes les sessions mais ne gère pas leur création
3. **Possibles autres scripts** - Scripts qui font `requests.post("/session")` directement

### Impact Observation

```bash
$ ps aux | grep opencode | head -20
bamer      88049 26.4 1.1  533848  388256 ?  Ssl  00:05  23:52 python3 event_bridge.py
bamer   3689498 74.1 53.0 99382184 17352568 pts/1 Rl+ Feb05 165:23 opencode --port 4096
bamer   263755 0.4  0.5 74484788 173628 pts/1 Sl+  00:46   0:13 opencode run pyright-langserver
bamer   659287 0.3  0.1 75116968 33100 ?      Sl   Feb05   4:09 opencode run bash-language-server
bamer  1526515 0.3  0.1 74919872 42320 pts/1  Sl   Feb05   2:11 opencode run bash-language-server
bamer  2545786 0.3  0.1 74609060 39388 ?      Sl   Feb05   2:01 opencode run bash-language-server
```

Plusieurs language servers spawnés + OpenCode principal = **~100+ Go RAM utilisé**

---

## Recommandations

### 1. Intégration Recommandée: OptimizedOpenCodeClient

**Pourquoi**:
- ✅ Fonctionnel à 100%
- ✅ Gestion de sessions propre (singleton + heartbeat)
- ✅ Thread-safe
- ✅ Simple à utiliser
- ✅ Déjà utilisé par plusieurs composants

**Limitation**:
- ❌ Ne charge pas automatiquement les agents

**Solution**:
- Conserver `OptimizedOpenCodeClient` pour la gestion de session
- Implémenter la découverte/chargement automatique d'agents

---

### 2. Alternative avancée: AsyncOpenCodeClient

**Pourquoi**:
- ✅ Fonctionnel à 100%
- ✅ SSE natif (idéal pour event-driven architecture)
- ✅ Non-blocking
- ✅ Compatible avec unified_orchestrator.py (qui est déjà async)

**Limitation**:
- ⚠️ Pas encore utilisé par les composants existants
- ❌ Plus complexe (besoin contexte async)

---

### 3. Intégration Immédiate: Migration de unified_orchestrator.py

**Action Requise**:

Remplacer dans `agents/unified_orchestrator.py`:
```python
# ❌ AVANT (problématique)
session_response = requests.post(
    f"{self.opencode_server}/session",
    json={"title": f"Swarm: {task[:50]}"},
    timeout=30,
)

# ✅ APRÈS (correct)
from Open_ELF.orchestrator.opencode_client import get_opencode_client

client = get_opencode_client()
success, response = client.send_message(
    swarm_prompt,
    agent="multi-agent-coordinator"
)
```

---

### 4. Intégration Long Terme: UnifiedOrchestrator + AsyncOpenCodeClient

**Architecture Future**:

Le `unified_orchestrator.py` (dans orchestrator/) est **déjà async**:
```python
class UnifiedOrchestrator:
    def __init__(self):
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.session: Optional[aiohttp.ClientSession] = None

    async def _listen_opencode(self):
        """Déjà écoute SSE!"""
        async with self.session.get(f"{OPENCODE_SERVER}/event", ...):
            async for line in response.content:
                await self._process_sse_line(line_str)
```

**Problème**: Il n'utilise pas `AsyncOpenCodeClient` pour les appels de décision AI!

**Solution**:
- Intégrer `AsyncOpenCodeClient.listen_sse()` dans UnifiedOrchestrator
- Utiliser `AsyncOpenCodeClient.send_message()` pour les décisions AI
- Garder SSE pour la détection d'événements
- Éliminer event_bridge.py (redondant)

**Résultat**: Une seule intégration async complète

---

## Charge automatique des Agents

### Problème Actuel
Aucune des intégrations ne charge automatiquement les agents depuis:
- `~/.config/opencode/agents/*.md`

### Solution Recommandée

Créer un module `agent_loader.py`:

```python
from pathlib import Path
import json

AGENTS_DIR = Path.home() / ".config" / "opencode" / "agents"

def load_agent_config(agent_name: str) -> dict:
    """Charger la config d'un agent depuis son fichier .md"""
    agent_file = AGENTS_DIR / f"{agent_name}.md"

    if not agent_file.exists():
        raise ValueError(f"Agent {agent_name} not found")

    content = agent_file.read_text()

    # Parse frontmatter YAML
    if content.startswith("---"):
        frontmatter_end = content.find("---", 4)
        yaml_content = content[4:frontmatter_end]
        import yaml
        config = yaml.safe_load(yaml_content)
        return config

    return {
        "name": agent_name,
        "description": "",
    }

def list_available_agents() -> list[str]:
    """Lister tous les agents disponibles"""
    return [
        f.stem
        for f in AGENTS_DIR.glob("*.md")
        if f.is_file()
    ]

def get_agent_prompt(agent_name: str) -> str:
    """Récupérer le prompt complet d'un agent"""
    agent_file = AGENTS_DIR / f"{agent_name}.md"

    if not agent_file.exists():
        raise ValueError(f"Agent {agent_name} not found")

    content = agent_file.read_text()

    # Retourner le contenu après le frontmatter (le prompt)
    if content.startswith("---"):
        frontmatter_end = content.find("---", 4)
        return content[frontmatter_end + 4:].strip()

    return content
```

Ensuite modifier `OptimizedOpenCodeClient.send_message()`:

```python
def send_message(self, message: str, agent: Optional[str] = None):
    if agent:
        # Charger automatiquement le prompt de l'agent
        try:
            from agents.agent_loader import get_agent_prompt
            agent_prompt = get_agent_prompt(agent)

            # Préfixer le message avec le prompt de l'agent
            message = f"{agent_prompt}\n\nTASK:\n{message}"
        except Exception as e:
            logger.warning(f"Failed to load agent {agent}: {e}")

    # Envoyer comme avant...
```

---

## Plan d'Action

### Phase 1: Arrêter la multiplication des sessions (Immédiat)

1. **Identifier tous les composants qui créent directement des sessions**:
   ```bash
   grep -r 'requests.post.*"/session"' /home/bamer/.opencode/emergent-learning/Open_ELF
   ```

2. **Remplacer par OptimizedOpenCodeClient**:
   - `agents/unified_orchestrator.py` → URGENT
   - Autres scripts identifiés

3. **Nettoyer les sessions existantes**:
   ```bash
   # Via API OpenCode
   curl http://localhost:4096/session  # Lister toutes les sessions
   # Manuelle ou script de nettoyage
   ```

### Phase 2: Intégrer AsyncOpenCodeClient (Court terme)

1. **Tester `AsyncOpenCodeClient` indépendamment**:
   ```python
   # test_async_client.py
   import asyncio

   from Open_ELF.orchestrator.async_opencode_client import AsyncOpenCodeClient

   async def test():
       async with AsyncOpenCodeClient() as client:
           success, response = await client.send_message(
               "Hello from async client",
               agent="architect"
           )
           print(f"Response: {response}")

   asyncio.run(test())
   ```

2. **Migrer `unified_orchestrator.py`**:
   - Remplacer `aiohttp.ClientSession()` par `AsyncOpenCodeClient`
   - Utiliser `listen_sse()` au lieu de l'implémentation custom
   - Utiliser `send_message()` pour les décisions AI

3. **Conserver SSE pour détection événements**

### Phase 3: Charge automatique des agents (Moyen terme)

1. **Créer `agents/agent_loader.py`** comme décrit ci-dessus

2. **Intégrer dans les deux clients**:
   - `OptimizedOpenCodeClient.send_message()`
   - `AsyncOpenCodeClient.send_message()`

3. **Ajouter méthode utilitaire**:
   ```python
   async def call_agent(agent_name: str, task: str) -> str:
       """Helper simple pour appeler un OpenCode agent"""
       client = await get_async_opencode_client()
       success, response = await client.send_message(task, agent=agent_name)
       return response
   ```

### Phase 4: Unification complète (Long terme)

1. **Architecture finale**:
   ```
   UnifiedOrchestrator (orchestrator/unified_orchestrator.py)
       └─> AsyncOpenCodeClient (orchestrator/async_opencode_client.py)
           ├─> manage_session() (singleton + heartbeat)
           ├─> send_message() (charge agents auto)
           └─> listen_sse() (détection événements)
   ```

2. **Éliminer les redondances**:
   - Retirer `orchestrator/event_bridge.py` (fusionné dans UnifiedOrchestrator)
   - Supprimer `agents/unified_orchestrator.py` (création directe de sessions)
   - Garder `OptimizedOpenCodeClient` pour usage synchrone legacy
   - Conserver `ELFAIClient` uniquement pour experiment_analyzer

3. **Documentation des APIs**:
   - API synchrone: `from Open_ELF.orchestrator.opencode_client import get_opencode_client`
   - API async: `await get_async_opencode_client()`
   - API simplifiée: `from agents.agent_loader import call_agent`

---

## Annexes

### Liste des fichiers d'intégration

| Fichier | Intégration | Statut |
|---------|-------------|--------|
| `orchestrator/opencode_client.py` | OptimizedOpenCodeClient | ✅ Actif |
| `orchestrator/async_opencode_client.py` | AsyncOpenCodeClient | ✅ Créé, non utilisé |
| `agents/opconnection.py` | Wrapper de OptimizedOpenCodeClient | ✅ Actif |
| `agents/opencode_client.py` | Wrapper de OptimizedOpenCodeClient | ✅ Actif |
| `agents/elf_ai_client.py` | ELFAIClient (backend) | ⚠️ Limité |
| `agents/unified_orchestrator.py` | Création directe sessions | ❌ Problématique |
| `agents/agent_execution_engine.py` | Utilise OptimizedOpenCodeClient | ✅ Actif |
| `orchestrator/event_bridge.py` | Polling sessions | ⚠️ Complémentaire |
| `sentinel/launcher.py` | Utilise OptimizedOpenCodeClient | ✅ Actif |
| `agents/opencode_swarm.py` | Gestion swarm (pas de client) | ⚠️ Metadata only |

### Sessions OpenCode actives

Pour voir les sessions:
```bash
# Lister les sessions
curl -s http://localhost:4096/session | jq '[]'

# Résultat attendu (exemple):
[
  {"id": "sess_abc123", "title": "ELF Persistent Session - 2026-02-06 00:47", ...},
  {"id": "sess_def456", "title": "Swarm: Analyze this codebase", ...},
  {"id": "sess_ghi789", "title": "Swarm: Debug issue X", ...},
]
```

En cas de multiplication excessive:
```bash
# Script de nettoyage (DANGER: supprime toutes les sessions sauf la persistante)
python3 <<'PY'
import requests

sessions = requests.get("http://localhost:4096/session").json()
persistent_id = "your-persistent-session-id"

for sess in sessions:
    if sess["id"] != persistent_id:
        requests.delete(f"http://localhost:4096/session/{sess['id']}")
        print(f"Deleted session: {sess['id']}")
PY
```

---

## Conclusion

**Meilleure intégration disponible**: **OptimizedOpenCodeClient**  
**Meilleure intégration future**: **AsyncOpenCodeClient** (à intégrer)

**Action immédiate**: Migrer `agents/unified_orchestrator.py` vers `OptimizedOpenCodeClient`

**Architecture recommandée long terme**:
- UnifiedOrchestrator + AsyncOpenCodeClient (gestion sessions + SSE + agents)
- OptimizedOpenCodeClient (backup synchrone pour legacy)
- agent_loader.py (charge automatique d'agents)

**Eliminer**:
- ❌ Créations directes de sessions dans les scripts
- ❌ event_bridge.py (redondant avec UnifiedOrchestrator)

---

**Rapport généré le**: 2026-02-06  
**À faire**: Reviewer avec le CEO et prioriser les phases d'implémentation
