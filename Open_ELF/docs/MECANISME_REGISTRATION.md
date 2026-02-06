# Mécanisme de Registration: Event Bridge ↔ Unified Orchestrator

**Date**: 2026-02-06

## Objectif

Le Unified Orchestrator ne doit **PLUS** faire de SSE listening lui-même! Il doit:
- **S'ENREGISTRER** auprès de Event Bridge
- **SPÉCIFIER** les événements qui l'intéressent
- **RECEVOIR** les événements via callback ou queue

---

## Mécanisme à Implémenter dans event_bridge.py

### 1. Système de Listeners

```python
# Dans event_bridge.py

from typing import Callable, Dict, Set, List
from dataclasses import dataclass

@dataclass
class Listener:
    """Listener pour événements SSE"""
    id: str
    callback: Callable  # Fonction à appeler
    event_types: Set[str]  # Types d'événements intéressants
    filter_func: Callable = None  # Optionnel: filtre personnalisé


class EventBridge:
    def __init__(self):
        # ... code existant ...

        # Nouveau: système de listeners
        self._listeners: Dict[str, Listener] = {}  # id -> Listener

```

### 2. Méthode de Registration

```python
    def register_listener(
        self,
        listener_id: str,
        callback: Callable,
        event_types: List[str],
        filter_func: Callable = None
    ):
        """
        Enregistrer un listener pour recevoir des événements.

        Args:
            listener_id: ID unique du listener (ex: "unified_orchestrator")
            callback: Fonction appelée when événement reçu: callback(event_data)
            event_types: Types d'événements intéressants (ex: ["tool", "message", "error"])
            filter_func: Optionnel, filtre personnalisé: filter_func(event_data) -> bool
        """
        listener = Listener(
            id=listener_id,
            callback=callback,
            event_types=set(event_types),
            filter_func=filter_func
        )
        self._listeners[listener_id] = listener
        logger.info(f"✅ Listener registered: {listener_id} for events: {event_types}")

```

### 3. Méthode Unregistration

```python
    def unregister_listener(self, listener_id: str):
        """Désenregistrer un listener"""
        if listener_id in self._listeners:
            del self._listeners[listener_id]
            logger.info(f"🔌 Listener unregistered: {listener_id}")
        else:
            logger.warning(f"⚠️  Listener not found: {listener_id}")

```

### 4. Dispatch des Événements

```python
    def _dispatch_event(self, event_data: Dict):
        """
        Dispatcher event à tous les listeners enregistrés.

        Appelé dans _handle_event() après avoir traité l'événement.
        """
        event_type = event_data.get("type", "unknown")

        # Trouver les listeners intéressés
        for listener_id, listener in self._listeners.items():
            # Vérifier si le listener est intéressé par ce type d'événement
            if event_type not in listener.event_types:
                continue

            # Appliquer filtre personnalisé si fourni
            if listener.filter_func and not listener.filter_func(event_data):
                continue

            # Appeler le callback (séparément pour éviter blocage)
            try:
                import threading
                thread = threading.Thread(
                    target=listener.callback,
                    args=(event_data,),
                    daemon=True
                )
                thread.start()
                logger.debug(f"📤 Event dispatched to {listener_id}: {event_type}")
            except Exception as e:
                logger.error(f"❌ Error dispatching event to {listener_id}: {e}")

```

### 5. Intégration dans _handle_event()

```python
    def _handle_event(self, event: Dict[str, Any]):
        """Gère un événement reçu d'OpenCode (modifié)."""
        event_type = event.get("type", "unknown")
        event_properties = event.get("properties", {})

        # Logging (déjà existant)
        self._record_event(event_type, details="...")

        # Mapper et déclencher hooks (déjà existant)
        if event_type == "message":
            self._handle_message_event(event)
        elif event_type == "tool":
            self._handle_tool_event(event)
        # ... etc

        # NOUVEAU: Dispatch aux listeners enregistrés
        self._dispatch_event(event)

```

---

## Utilisation depuis unified_orchestrator.py

### Exemple Complet

```python
# Dans unified_orchestrator.py

from typing import Dict, Any, Optional
from pathlib import Path
import yaml
import logging

AGENTS_DIR = Path.home() / ".config" / "opencode" / "agents"

class UnifiedOrchestrator:
    def __init__(self):
        self.bridge = None  # Sera EventBridge
        self.running = False
        self.event_queue = asyncio.Queue()
        self.agents_cache = {}

    def start(self):
        """Démarrer l'orchestrateur et s'enregistrer au près du bridge"""
        logger.info("🚀 Starting Unified Orchestrator")

        # 1. Se connecter au bridge
        from orchestrator.event_bridge import EventBridge
        self.bridge = EventBridge()
        self.bridge.start()

        # 2. S'ENREGISTRER pour recevoir des événements spécifiques
        self._register_listeners()

        # 3. Démarrer le processeur d'événements
        self.running = True
        self._start_event_processor()

    def _register_listeners(self):
        """S'enregistrer auprès du Event Bridge pour les événements wanted"""
        self.bridge.register_listener(
            listener_id="unified_orchestrator",
            callback=self._on_event_received,
            event_types=[
                "tool",        # Pourvoir suivre les outils utilisés
                "message",     # Pourvoir suivre les messages utilisateurs
                "error",       # Pourvoir gérer les erreurs
                "failure",     # Pourvoir gérer les échecs
            ],
            filter_func=self._event_filter if self._event_filter else None
        )
        logger.info("✅ Registered with Event Bridge for events: tool, message, error, failure")

    def _event_filter(self, event_data: Dict) -> bool:
        """
        Filtre personnelisé (optionnel).

        Return False pour ignorer cet événement.
        """
        event_type = event_data.get("type", "")
        properties = event_data.get("properties", {})

        # Exemple: ignorer les messages système
        if event_type == "message" and properties.get("role") == "system":
            return False

        # Exemple: ignorer les outils de diagnostic
        if event_type == "tool" and properties.get("tool") in ["health_check", "status"]:
            return False

        return True

    def _on_event_received(self, event_data: Dict):
        """
        Callback appelé par Event Bridge quand événement reçu.

        Est appelé dans un thread séparé pour ne pas bloquer le bridge.
        """
        logger.debug(f"📨 Event received from bridge: {event_data.get('type')}")

        # Mettre dans l'event queue (thread-safe)
        self.event_queue.put_nowait(event_data)

    def _start_event_processor(self):
        """Démarrer le processeur d'événements async"""
        import asyncio

        async def processor():
            while self.running:
                try:
                    event = await self.event_queue.get()
                    await self._process_event(event)
                except Exception as e:
                    logger.error(f"❌ Error processing event: {e}")

        # Démarrer en background
        asyncio.create_task(processor())

    async def _process_event(self, event_data: Dict):
        """Traiter un événement"""
        event_type = event_data.get("type", "unknown")
        properties = event_data.get("properties", {})

        logger.info(f"⚙️ Processing event: {event_type}")

        # Logique de décision selon le type d'événement
        if event_type == "tool":
            await self._handle_tool_event(properties)
        elif event_type == "message":
            await self._handle_message_event(properties)
        elif event_type == "error":
            await self._handle_error_event(properties)
        elif event_type == "failure":
            await self._handle_failure_event(properties)

    async def _handle_tool_event(self, properties: Dict):
        """Gérer événement outil"""
        tool_name = properties.get("tool", "unknown")
        tool_input = properties.get("input", {})
        success = properties.get("success", True)

        logger.info(f"🔧 Tool event: {tool_name} (success={success})")

        # Décision AI: faut-il escalader?
        if not success:
            # Échec d'outil → Escalade possible
            await self._escalate_to_ceo({
                "type": "tool_failure",
                "tool": tool_name,
                "error": properties.get("output", {}).get("error", "Unknown")
            })

    async def _handle_message_event(self, properties: Dict):
        """Gérer événement message"""
        role = properties.get("role", "unknown")
        content = properties.get("content", "")

        if role == "user":
            logger.info(f"👤 User message: {content[:100]}...")

            # Optionnel: Analyser si nécessite un agent
            pass

    # ... autres handlers ...

```

---

## Avantages de ce Pattern

### 1. **Découplage Parfait**
- Event Bridge: Focus on listening et HTTP/SSE
- Unified Orchestrator: Focus on décision et workflow
- Pas de chevauchement de responsabilité

### 2. **Extensible**
- Ajouter un listener? → Juste appeler `register_listener()`
- Nouveau type d'événement? → Juste ajouter dans `event_types`
- Filtre personnalisé? → Passer `filter_func`

### 3. **Thread-Safe**
- Callback appelé dans thread séparé
- Event queue async-safe
- Pas de blocage du SSE stream

### 4. **Debuggable**
- Logger chaque dispatch
- Voir quels listeners sont enregistrés
- Filtres personnalisés testable

---

## Diagramme de Flux

```
OpenCode SSE Stream
        ↓
event_bridge._handle_event()
        ↓
    ├─> Hooks ELF (existing)
    │   ├─> UserPromptSubmit
    │   ├─> PostToolUse
    │   └─> learning-loop
    │
    └─> _dispatch_event()  ← NOUVEAU
            ↓
    Unified Orchestrator._on_event_received()
            ↓
    event_queue.put(event)
            ↓
    _process_event(event)
            ↓
    Decision Engine
        ├─> _handle_tool_event()
        ├─> _handle_message_event()
        └─> _escalate_to_ceo()
```

---

## Checklist d'Implémentation

### event_bridge.py

- [ ] Ajouter classe `Listener` (dataclass)
- [ ] Ajouter `self._listeners: Dict[str, Listener]`
- [ ] Implémenter `register_listener()`
- [ ] Implémenter `unregister_listener()`
- [ ] Implémenter `_dispatch_event()`
- [ ] Modifier `_handle_event()` pour appeler `_dispatch_event()`
- [ ] Ajouter logging pour les listeners

### unified_orchestrator.py

- [ ] Supprimer SSE listening direct (`_listen_opencode()`)
- [ ] Appeler `EventBridge().start()` au démarrage
- [ ] Implémenter `_register_listeners()`
- [ ] Implémenter `_on_event_received()`
- [ ] Maintenir `event_queue` (déjà là)
- [ ] Maintenir `_process_event()` (déjà là)
- [ ] Ajouter handlers d'événements spécifiques

---

## Tests

### Test Registration

```python
# Test simple
bridge = EventBridge()

call_count = 0

def my_callback(event_data):
    global call_count
    call_count += 1
    print(f"Event {call_count}: {event_data.get('type')}")

# Register
bridge.register_listener(
    listener_id="test_listener",
    callback=my_callback,
    event_types=["tool", "message"]
)

# Simuler événement
event_data = {"type": "tool", "properties": {"tool": "bash"}}
bridge._dispatch_event(event_data)

# Vérifier
assert call_count == 1, "Callback not called!"
print("✅ Registration test passed")
```

### Test Filtre

```python
def filter_func(event_data):
    # Ignorer les messages système
    return event_data.get("properties", {}).get("role") != "system"

bridge.register_listener(
    listener_id="test_listener_filter",
    callback=my_callback,
    event_types=["message"],
    filter_func=filter_func
)

# Les messages système sont ignorés
event_system = {"type": "message", "properties": {"role": "system"}}
bridge._dispatch_event(event_system)
assert call_count == 1  # Pas incrementé!

# Les messages utilisateur sont reçus
event_user = {"type": "message", "properties": {"role": "user"}}
bridge._dispatch_event(event_user)
assert call_count == 2  # Incrémenté!
```

---

## Exemple Avancé: Multi-Listeners

```python
# Plusieurs listeners peuvent s'enregistrer
# avec leurs propres callbacks et filtres

# Listener 1: Unifié Orchestrator (tous les événements outils)
bridge.register_listener(
    listener_id="orchestrator",
    callback=orchestrator._on_event_received,
    event_types=["tool", "message", "error"]
)

# Listener 2: Analytics (que les réussites)
bridge.register_listener(
    listener_id="analytics",
    callback=analytics.on_success_event,
    event_types=["tool", "message"],
    filter_func=lambda e: e.get("properties", {}).get("success", False) is False
)

# Listener 3: Monitoring (que les erreurs)
bridge.register_listener(
    listener_id="monitoring",
    callback=monitoring.on_error_event,
    event_types=["error", "failure"]
)
```

---

## Notes

- Les callbacks sont appelés dans des threads séparés → Pas de blocage
- L'event queue est async-safe → Bon pour asyncio
- Filtres personnalisés permettent granularité fine
- Unregistered listeners sont nettoyés automatiquement

---

**Date**: 2026-02-06
**Status**: À implémenter (priorité haute)
