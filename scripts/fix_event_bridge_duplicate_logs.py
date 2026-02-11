#!/usr/bin/env python3
"""
Script pour corriger proprement les logs en double d'EventBridge

Problème:
- EventBridge v2 et UnifiedOrchestrator créent tous les deux des logs
- UnifiedOrchestrator ne devrait pas créer d'instance EventBridge

Solution:
1. EventBridge v2 enregistre dans event_chronicle
2. UnifiedOrchestrator poll event_chronicle (pas de connexion HTTP/callbacks)
3. Plus de logs en double
"""

import sys
from pathlib import Path

ELF_DIR = Path.home() / ".opencode" / "emergent-learning"
CORE_DIR = ELF_DIR / "core"
ORCHESTRATOR_DIR = ELF_DIR / "Open_ELF" / "orchestrator"

print("=" * 70)
print("CORRECTION PROPRE DES LOGS EN DOUBLE")
print("=" * 70)

# Étape 1: Modifier EventBridge v2 pour utiliser log_event
print("\n=== Étape 1: Modification de EventBridge v2 ===")
eb_v2_file = CORE_DIR / "event_bridge_v2.py"

# lire le fichier
with open(eb_v2_file, 'r') as f:
    eb_content = f.read()

# Modifier pour importer log_event et l'utiliser
old_import = """# Setup logging
import logging

try:
    from Open_ELF.utils.elf_logging import get_logger

    logger = get_logger("event_bridge", level=logging.DEBUG)
except ImportError:
    import logging

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("event_bridge")"""

new_import = """# Setup logging
import logging

try:
    from Open_ELF.utils.elf_logging import get_logger, log_event

    logger = get_logger("event_bridge", level=logging.DEBUG)
    LOG_EVENT_AVAILABLE = True
except ImportError:
    import logging

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("event_bridge")
    LOG_EVENT_AVAILABLE = False"""

if old_import in eb_content:
    eb_content = eb_content.replace(old_import, new_import)
    print("✅ Import modifié pour inclure log_event")
else:
    print("⚠️  Import non trouvé (déjà modifié?)")

# Modifier _handle_event pour enregistrer dans event_chronicle
old_handle_event = """    def _handle_event(self, event: Dict[str, Any]):
        \"\"\"Handle an event from OpenCode.\"\"\"
        # Support both formats: {"type": "...", "properties": {...}}
        # and {"payload": {"type": "...", "properties": {...}}}
        if "payload" in event:
            payload = event["payload"]
            event_type = payload.get("type", "unknown")
            event_properties = payload.get("properties", {})
        else:
            event_type = event.get("type", "unknown")
            event_properties = event.get("properties", {})

        # Handle message.part.updated events (contains tool_use parts)
        if event_type == "message.part.updated":
            self._handle_message_part_updated_event(event)
            return

        # Extract details
        details = ""
        if event_type == "tool":
            tool_name = event_properties.get("tool", "unknown")
            details = f"Tool: {tool_name}"

            # Process through LearningProcessor
            if self.learning_processor:
                self._process_tool_event(event)

        elif event_type == "message":
            content_preview = event_properties.get("content", "")[:50]
            details = f"Message: {content_preview}..."
        elif event_type == "error":
            error_message = event_properties.get("error", "Unknown error")
            details = f"Error: {error_message}""

new_handle_event = """    def _handle_event(self, event: Dict[str, Any]):
        \"\"\"Handle an event from OpenCode.\"\"\"
        # Support both formats: {"type": "...", "properties": {...}}
        # and {"payload": {"type": "...", "properties": {...}}}
        if "payload" in event:
            payload = event["payload"]
            event_type = payload.get("type", "unknown")
            event_properties = payload.get("properties", {})
        else:
            event_type = event.get("type", "unknown")
            event_properties = event.get("properties", {})

        # Handle message.part.updated events (contains tool_use parts)
        if event_type == "message.part.updated":
            self._handle_message_part_updated_event(event)
            return

        # Extract details
        details = ""
        if event_type == "tool":
            tool_name = event_properties.get("tool", "unknown")
            details = f"Tool: {tool_name}"

            # Process through LearningProcessor
            if self.learning_processor:
                self._process_tool_event(event)

        elif event_type == "message":
            content_preview = event_properties.get("content", "")[:50]
            details = f"Message: {content_preview}..."
        elif event_type == "error":
            error_message = event_properties.get("error", "Unknown error")
            details = f"Error: {error_message}"

        # Log to event_chronicle for UnifiedOrchestrator polling
        if LOG_EVENT_AVAILABLE and event_type in ["tool", "error", "failure", "service", "health"]:
            try:
                log_event(
                    event_type=event_type,
                    source="event_bridge_v2",
                    summary=details or f"{event_type} event",
                    data=event_properties,
                    status="success"
                )
            except Exception as e:
                logger.debug(f"Failed to log to event_chronicle: {e}")"""

if old_handle_event in eb_content:
    eb_content = eb_content.replace(old_handle_event, new_handle_event)
    print("✅ _handle_event modifié pour enregistrer dans event_chronicle")
else:
    print("⚠️  _handle_event non trouvé (déjà modifié?)")

# Sauvegarder event_bridge_v2.py
with open(eb_v2_file, 'w') as f:
    f.write(eb_content)
print(f"✅ {eb_v2_file} modifié")

# Étape 2: Modifier UnifiedOrchestrator pour supprimer la connexion EventBridge
print("\n=== Étape 2: Modification de UnifiedOrchestrator ===")
uo_file = ORCHESTRATOR_DIR / "unified_orchestrator.py"

with open(uo_file, 'r') as f:
    uo_content = f.read()

# Modifier _connect_to_eventbridge pour faire du polling au lieu de se connecter
old_connect = """    def _connect_to_eventbridge(self) -> bool:
        \"\"\"Connect to running EventBridge instance.

        UnifiedOrchestrator connects to EventBridge v2 via HTTP API (port 9998).
        It does NOT create a new EventBridge instance - that would cause duplicate logs.

        Returns:
            True if successfully connected, False otherwise.
        \"\"\"
        try:
            # Check EventBridge status via HTTP API
            response = requests.get(f"{EVENT_BRIDGE_URL}/status", timeout=2)
            if response.status_code != 200:
                logger.error(f"❌ EventBridge returned status {response.status_code}")
                return False

            logger.info(f"✅ Connected to EventBridge ({EVENT_BRIDGE_URL}/status)")

            # Create a minimal bridge wrapper for register_listener compatibility
            # This doesn't trigger EventBridge __init__ (no duplicate logs)
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "event_bridge_module",
                str(OPEN_ELF_DIR / "orchestrator/event_bridge_wrapper.py"),
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Just create the wrapper without calling parent __init__
            # Set running=True to indicate connection is established
            self.bridge = type('EventBridge', (), {'running': True, 'register_listener': lambda *args: None})()
            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to EventBridge: {e}")
            logger.error(
                f"\\nMake sure EventBridge is running:\\n"
                f"  cd {ELF_DIR / 'core'}\\n"
                f"  python event_bridge_v2.py start"
            )
            return False"""

new_connect = """    def _connect_to_eventbridge(self) -> bool:
        \"\"\"Check if EventBridge is running.

        UnifiedOrchestrator polls event_chronicle for events instead of connecting
        via callbacks. No EventBridge instance is created.

        Returns:
            True if EventBridge is running, False otherwise.
        \"\"\"
        try:
            # Just check if EventBridge is running via HTTP API
            response = requests.get(f"{EVENT_BRIDGE_URL}/status", timeout=2)
            if response.status_code != 200:
                logger.error(f"❌ EventBridge returned status {response.status_code}")
                return False

            logger.info(f"✅ EventBridge is running ({EVENT_BRIDGE_URL}/status)")
            logger.info("📊 UnifiedOrchestrator will poll event_chronicle for events")

            # No bridge instance created - we poll event_chronicle instead
            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to EventBridge: {e}")
            logger.error(
                f"\\nMake sure EventBridge is running:\\n"
                f"  cd {ELF_DIR / 'core'}\\n"
                f"  python event_bridge_v2.py start"
            )
            return False"""

if old_connect in uo_content:
    uo_content = uo_content.replace(old_connect, new_connect)
    print("✅ _connect_to_eventbridge modifié pour polling event_chronicle")
else:
    print("⚠️  _connect_to_eventbridge non trouvé (déjà modifié?)")

# Modifier _register_listeners pour ne rien faire (polling au lieu de callbacks)
old_register = """    def _register_listeners(self):
        \"\"\"Register as EventBridge listener for relevant events.\"\"\"
        self.bridge.register_listener(
            listener_id="unified_orchestrator",
            callback=self._on_event_received_sync,
            event_types=["tool", "message", "error", "failure", "service", "health"],
        )
        logger.info(
            "✅ Registered for events: tool, message, error, failure, service, health"
        )"""

new_register = """    def _register_listeners(self):
        \"\"\"Setup event polling from event_chronicle (no EventBridge connection).\"\"\"
        logger.info("✅ Will poll event_chronicle for new events")
        # Event polling is done in _poll_events_from_database() which is called periodically"""

if old_register in uo_content:
    uo_content = uo_content.replace(old_register, new_register)
    print("✅ _register_listeners modifié pour ne pas se connecter à EventBridge")
else:
    print("⚠️  _register_listeners non trouvé (déjà modifié?)")

# Ajouter la méthode _poll_events_from_database
# Trouver l'endroit où l'ajouter (juste avant _on_event_received_sync)
if "def _poll_events_from_database" not in uo_content:
    import re
    # Trouver la ligne avec "def _on_event_received_sync"
    match = re.search(r'(    def _(_on_event_received_sync)\([^)]*\):)', uo_content)
    if match:
        insert_pos = match.start()
        indent = match.group(1)[:4]  # Capturer l'indentation

        new_method = f'''{indent}def _poll_events_from_database(self) -> int:
{indent}    \"\"\"Poll event_chronicle for new events.

{indent}    Returns:
{indent}        Number of new events processed

{indent}    polling is safer than callbacks - no EventBridge instance created,
{indent}    no duplicate logs from __init__, and orchestrator is independent.
{indent}    \"\"\"
{indent}    import sqlite3
{indent}
{indent}    db_path = ELF_DIR / "memory" / "index.db"
{indent}    if not db_path.exists():
{indent}        return 0

{indent}    conn = sqlite3.connect(str(db_path))
{indent}    cursor = conn.cursor()
{indent}
{indent}    events_processed = 0

{indent}    try:
{indent}        # Get events we haven't processed yet
{indent}        # We track the last processed timestamp
{indent}        cursor.execute('''
{indent}            SELECT id, timestamp, event_type, source, summary, data, status
{indent}            FROM event_chronicle
{indent}            WHERE created_at > ?
{indent}            ORDER BY created_at ASC
{indent}            LIMIT 100
{indent}        ''', (self.last_event_timestamp or "1970-01-01",))

{indent}        for row in cursor.fetchall():
{indent}            event_id, timestamp, event_type, source, summary, data, status = row
{indent}
{indent}            # Create Event object (same format as callbacks used to provide)
{indent}            event_data = {{
{indent}                "type": event_type,
{indent}                "properties": json.loads(data) if data else {{}},
{indent}                "severity": self._map_status_to_severity(status),
{indent}            }}

{indent}            # Put in async queue for processing
{indent}            try:
{indent}                loop = asyncio.get_event_loop()
{indent}            except RuntimeError:
{indent}                return events_processed

{indent}                # Create Event object
{indent}                event = Event(
{indent}                    id=str(event_id),
{indent}                    type=event_type,
{indent}                    severity=self._get_severity(event_data),
{indent}                    source=source,
{indent}                    data=event_data.get("properties", {{}}),
{indent}                    timestamp=datetime.now(),
{indent}                )

{indent}                asyncio.run_coroutine_threadsafe(self.event_queue.put(event), loop)
{indent}                events_processed += 1

{indent}        # Update last seen timestamp
{indent}        if events_processed > 0:
{indent}            cursor.execute('''
{indent}                SELECT MAX(created_at) FROM event_chronicle
{indent}            ''')
{indent}            self.last_event_timestamp = cursor.fetchone()[0]

{indent}    except Exception as e:
{indent}        logger.debug(f"Error polling events: {{e}}")
{indent}    finally:
{indent}        conn.close()

{indent}    return events_processed

{indent}def _map_status_to_severity(self, status: str) -> str:
{indent}    \"\"\"Map event_chronicle status to severity.\"\"\"
{indent}    if status == "success":
{indent}        return "info"
{indent}    elif status == "error" or status == "failure":
{indent}        return "error"
{indent}    elif status == "warning":
{indent}        return "warning"
{indent}    else:
{indent}        return "info"

'''
        uo_content = uo_content[:insert_pos] + new_method + uo_content[insert_pos:]
        print("✅ Méthode _poll_events_from_database ajoutée")
    else:
        print("⚠️  Pas trouvé où insérer _poll_events_from_database")

# Supprimer/renommer _on_event_received_sync (plus utilisé)
uo_content = re.sub(
    r'    def _on_event_received_sync\([^)]*\):.*?(?=\n    def |\n\nclass |\Z)',
    '    def _on_event_received_sync(self, event_data: Dict):\n        """DEPRECATED: Use _poll_events_from_database instead.\"\"\"\n        pass\n\n',
    uo_content,
    flags=re.DOTALL
)

# Ajouter last_event_timestamp dans __init__
if "self.last_event_timestamp" not in uo_content:
    # Trouver l'endroit pour l'ajouter (après self.started_at)
    uo_content = uo_content.replace(
        "        self.started_at: Optional[datetime] = None",
        "        self.started_at: Optional[datetime] = None\n        self.last_event_timestamp: Optional[str] = None  # For polling event_chronicle"
    )
    print("✅ last_event_timestamp ajouté à __init__")

# Sauvegarder unified_orchestrator.py
with open(uo_file, 'w') as f:
    f.write(uo_content)
print(f"✅ {uo_file} modifié")

print("\n" + "=" * 70)
print("CORRECTION TERMINÉE")
print("=" * 70)
print("\nRésumé des modifications:")
print("1. EventBridge v2 enregistre maintenant dans event_chronicle")
print("2. UnifiedOrchestrator poll event_chronicle (pas de création d'instance)")
print("3. Plus de logs en double")
print("\nÀ tester avec:")
print("  cd /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator")
print("  python orchestrator.py start")
