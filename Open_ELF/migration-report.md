Open_ELF Migration Report
============================================================

Files analyzed: 46
Core modules needed: config, database, logging, utils


File: /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator/mission_bridge.py
----------------------------------------
Pattern: config_access
  Matches: 4
Suggested migrations:
  config: 3 actions

File: /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator/event_bridge.py
----------------------------------------
Pattern: logging_setup
  Matches: 5
Pattern: config_access
  Matches: 9
Suggested migrations:
  logging: 3 actions
  config: 3 actions
Already using: logging

File: /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator/orchestrator.py
----------------------------------------
Pattern: logging_setup
  Matches: 3
Pattern: config_access
  Matches: 8
Suggested migrations:
  logging: 3 actions
  config: 3 actions
Already using: logging

File: /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator/test_mission_queue.py
----------------------------------------
Pattern: config_access
  Matches: 2
Suggested migrations:
  config: 3 actions

File: /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator/event_bridge_sdk.py
----------------------------------------
Pattern: logging_setup
  Matches: 4
Pattern: config_access
  Matches: 8
Suggested migrations:
  logging: 3 actions
  config: 3 actions
Already using: logging

File: /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator/unified_orchestrator.py
----------------------------------------
Pattern: sqlite_connection
  Matches: 1
Pattern: logging_setup
  Matches: 3
Pattern: config_access
  Matches: 10
Suggested migrations:
  database: 3 actions
  logging: 3 actions
  config: 3 actions
Already using: logging

File: /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator/opencode_client.py
----------------------------------------
Pattern: logging_setup
  Matches: 3
Suggested migrations:
  logging: 3 actions
Already using: logging

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/TalkinHead/process_phrases.py
----------------------------------------
Pattern: config_access
  Matches: 2
Suggested migrations:
  config: 3 actions

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/TalkinHead/ivy_overlay.py
----------------------------------------
Pattern: file_operations
  Matches: 14
Pattern: config_access
  Matches: 8
Suggested migrations:
  utils: 3 actions
  config: 3 actions
Already using: config

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/TalkinHead/main.py
----------------------------------------
Pattern: config_access
  Matches: 2
Suggested migrations:
  config: 3 actions

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/TalkinHead/event_watcher.py
----------------------------------------
Pattern: config_access
  Matches: 1
Suggested migrations:
  config: 3 actions

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/session_index.py
----------------------------------------
Pattern: sqlite_connection
  Matches: 3
Pattern: logging_setup
  Matches: 2
Pattern: config_access
  Matches: 4
Suggested migrations:
  database: 3 actions
  logging: 3 actions
  config: 3 actions
Already using: database, logging, utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/main.py
----------------------------------------
Pattern: logging_setup
  Matches: 5
Pattern: config_access
  Matches: 6
Suggested migrations:
  logging: 3 actions
  config: 3 actions
Already using: logging, utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/setup_security.py
----------------------------------------
Pattern: config_access
  Matches: 8
Suggested migrations:
  config: 3 actions

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/quick_performance_test.py
----------------------------------------
Already using: utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/test_query_performance.py
----------------------------------------
Pattern: sqlite_connection
  Matches: 12
Pattern: config_access
  Matches: 1
Suggested migrations:
  database: 3 actions
  config: 3 actions
Already using: utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/repositories/__init__.py
----------------------------------------
Already using: database

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/tests/test_broadcast_race.py
----------------------------------------
Already using: utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/tests/conftest.py
----------------------------------------
Pattern: sqlite_connection
  Matches: 8
Pattern: config_access
  Matches: 7
Suggested migrations:
  database: 3 actions
  config: 3 actions

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/tests/test_websocket_stress.py
----------------------------------------
Already using: utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/tests/test_auto_capture_rollback.py
----------------------------------------
Pattern: sqlite_connection
  Matches: 17
Pattern: config_access
  Matches: 6
Suggested migrations:
  database: 3 actions
  config: 3 actions
Already using: utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/migrations/run_migration.py
----------------------------------------
Pattern: sqlite_connection
  Matches: 3
Pattern: logging_setup
  Matches: 4
Suggested migrations:
  database: 3 actions
  logging: 3 actions
Already using: logging, utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/queries.py
----------------------------------------
Already using: utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/persistence.py
----------------------------------------
Pattern: logging_setup
  Matches: 2
Pattern: config_access
  Matches: 4
Suggested migrations:
  logging: 3 actions
  config: 3 actions
Already using: logging, utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/analytics.py
----------------------------------------
Already using: utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/runs.py
----------------------------------------
Already using: utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/auth.py
----------------------------------------
Pattern: logging_setup
  Matches: 4
Pattern: config_access
  Matches: 9
Suggested migrations:
  logging: 3 actions
  config: 3 actions
Already using: logging, utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/admin.py
----------------------------------------
Pattern: sqlite_connection
  Matches: 13
Pattern: logging_setup
  Matches: 2
Suggested migrations:
  database: 3 actions
  logging: 3 actions
Already using: logging, utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/agents_old.py
----------------------------------------
Pattern: config_access
  Matches: 2
Suggested migrations:
  config: 3 actions
Already using: logging

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/sessions.py
----------------------------------------
Pattern: logging_setup
  Matches: 2
Suggested migrations:
  logging: 3 actions
Already using: logging, utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/game.py
----------------------------------------
Pattern: config_access
  Matches: 7
Suggested migrations:
  config: 3 actions
Already using: utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/heuristics.py
----------------------------------------
Pattern: logging_setup
  Matches: 2
Suggested migrations:
  logging: 3 actions
Already using: logging, utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/semantic.py
----------------------------------------
Pattern: sqlite_connection
  Matches: 5
Pattern: logging_setup
  Matches: 2
Pattern: config_access
  Matches: 2
Suggested migrations:
  database: 3 actions
  logging: 3 actions
  config: 3 actions
Already using: logging

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/context.py
----------------------------------------
Already using: utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/live.py
----------------------------------------
Pattern: logging_setup
  Matches: 2
Pattern: config_access
  Matches: 18
Suggested migrations:
  logging: 3 actions
  config: 3 actions
Already using: logging, utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/workflows.py
----------------------------------------
Pattern: logging_setup
  Matches: 2
Suggested migrations:
  logging: 3 actions
Already using: logging, utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/agents.py
----------------------------------------
Pattern: logging_setup
  Matches: 3
Pattern: config_access
  Matches: 9
Suggested migrations:
  logging: 3 actions
  config: 3 actions
Already using: logging

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/monitoring.py
----------------------------------------
Pattern: sqlite_connection
  Matches: 5
Pattern: logging_setup
  Matches: 5
Pattern: config_access
  Matches: 6
Suggested migrations:
  database: 3 actions
  logging: 3 actions
  config: 3 actions
Already using: logging, utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/fraud.py
----------------------------------------
Pattern: logging_setup
  Matches: 2
Suggested migrations:
  logging: 3 actions
Already using: logging

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/setup.py
----------------------------------------
Pattern: config_access
  Matches: 5
Suggested migrations:
  config: 3 actions

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/knowledge.py
----------------------------------------
Already using: utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/utils/repository.py
----------------------------------------
Pattern: sqlite_connection
  Matches: 1
Suggested migrations:
  database: 3 actions
Already using: utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/utils/auto_capture.py
----------------------------------------
Pattern: logging_setup
  Matches: 2
Pattern: config_access
  Matches: 1
Suggested migrations:
  logging: 3 actions
  config: 3 actions
Already using: logging, utils

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/utils/broadcast.py
----------------------------------------
Pattern: logging_setup
  Matches: 2
Suggested migrations:
  logging: 3 actions
Already using: logging

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/utils/database.py
----------------------------------------
Pattern: sqlite_connection
  Matches: 7
Pattern: logging_setup
  Matches: 2
Suggested migrations:
  database: 3 actions
  logging: 3 actions
Already using: logging

File: /home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/utils/outcome_inference.py
----------------------------------------
Pattern: config_access
  Matches: 1
Suggested migrations:
  config: 3 actions

============================================================
MIGRATION PATCHES
============================================================

# Migration suggestions for mission_bridge.py

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.config import get_config, set_config


# Migration suggestions for event_bridge.py

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.openelf_logging import setup_logger, get_logger
from core.config import get_config, set_config


# Migration suggestions for orchestrator.py

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.openelf_logging import setup_logger, get_logger
from core.config import get_config, set_config


# Migration suggestions for test_mission_queue.py

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.config import get_config, set_config


# Migration suggestions for event_bridge_sdk.py

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.openelf_logging import setup_logger, get_logger
from core.config import get_config, set_config


# Migration suggestions for unified_orchestrator.py

# DATABASE MODULE
# - Replace sqlite3.connect() with core.database.get_connection()
# - Use execute_query() and execute_transaction() for database operations
# - Remove manual connection management

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.database import get_connection, execute_query, execute_transaction
from core.openelf_logging import setup_logger, get_logger
from core.config import get_config, set_config


# Migration suggestions for opencode_client.py

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# Suggested imports:
from core.openelf_logging import setup_logger, get_logger


# Migration suggestions for process_phrases.py

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.config import get_config, set_config


# Migration suggestions for ivy_overlay.py

# UTILS MODULE
# - Use lib.utils.resolve_path() for path resolution
# - Use lib.utils.validate_file() for file validation
# - Consolidate file operations

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from lib.utils import resolve_path, validate_file, format_timestamp
from core.config import get_config, set_config


# Migration suggestions for main.py

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.config import get_config, set_config


# Migration suggestions for event_watcher.py

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.config import get_config, set_config


# Migration suggestions for session_index.py

# DATABASE MODULE
# - Replace sqlite3.connect() with core.database.get_connection()
# - Use execute_query() and execute_transaction() for database operations
# - Remove manual connection management

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.database import get_connection, execute_query, execute_transaction
from core.openelf_logging import setup_logger, get_logger
from core.config import get_config, set_config


# Migration suggestions for main.py

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.openelf_logging import setup_logger, get_logger
from core.config import get_config, set_config


# Migration suggestions for setup_security.py

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.config import get_config, set_config


# Migration suggestions for test_query_performance.py

# DATABASE MODULE
# - Replace sqlite3.connect() with core.database.get_connection()
# - Use execute_query() and execute_transaction() for database operations
# - Remove manual connection management

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.database import get_connection, execute_query, execute_transaction
from core.config import get_config, set_config


# Migration suggestions for conftest.py

# DATABASE MODULE
# - Replace sqlite3.connect() with core.database.get_connection()
# - Use execute_query() and execute_transaction() for database operations
# - Remove manual connection management

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.database import get_connection, execute_query, execute_transaction
from core.config import get_config, set_config


# Migration suggestions for test_auto_capture_rollback.py

# DATABASE MODULE
# - Replace sqlite3.connect() with core.database.get_connection()
# - Use execute_query() and execute_transaction() for database operations
# - Remove manual connection management

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.database import get_connection, execute_query, execute_transaction
from core.config import get_config, set_config


# Migration suggestions for run_migration.py

# DATABASE MODULE
# - Replace sqlite3.connect() with core.database.get_connection()
# - Use execute_query() and execute_transaction() for database operations
# - Remove manual connection management

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# Suggested imports:
from core.database import get_connection, execute_query, execute_transaction
from core.openelf_logging import setup_logger, get_logger


# Migration suggestions for persistence.py

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.openelf_logging import setup_logger, get_logger
from core.config import get_config, set_config


# Migration suggestions for auth.py

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.openelf_logging import setup_logger, get_logger
from core.config import get_config, set_config


# Migration suggestions for admin.py

# DATABASE MODULE
# - Replace sqlite3.connect() with core.database.get_connection()
# - Use execute_query() and execute_transaction() for database operations
# - Remove manual connection management

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# Suggested imports:
from core.database import get_connection, execute_query, execute_transaction
from core.openelf_logging import setup_logger, get_logger


# Migration suggestions for agents_old.py

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.config import get_config, set_config


# Migration suggestions for sessions.py

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# Suggested imports:
from core.openelf_logging import setup_logger, get_logger


# Migration suggestions for game.py

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.config import get_config, set_config


# Migration suggestions for heuristics.py

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# Suggested imports:
from core.openelf_logging import setup_logger, get_logger


# Migration suggestions for semantic.py

# DATABASE MODULE
# - Replace sqlite3.connect() with core.database.get_connection()
# - Use execute_query() and execute_transaction() for database operations
# - Remove manual connection management

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.database import get_connection, execute_query, execute_transaction
from core.openelf_logging import setup_logger, get_logger
from core.config import get_config, set_config


# Migration suggestions for live.py

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.openelf_logging import setup_logger, get_logger
from core.config import get_config, set_config


# Migration suggestions for workflows.py

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# Suggested imports:
from core.openelf_logging import setup_logger, get_logger


# Migration suggestions for agents.py

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.openelf_logging import setup_logger, get_logger
from core.config import get_config, set_config


# Migration suggestions for monitoring.py

# DATABASE MODULE
# - Replace sqlite3.connect() with core.database.get_connection()
# - Use execute_query() and execute_transaction() for database operations
# - Remove manual connection management

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.database import get_connection, execute_query, execute_transaction
from core.openelf_logging import setup_logger, get_logger
from core.config import get_config, set_config


# Migration suggestions for fraud.py

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# Suggested imports:
from core.openelf_logging import setup_logger, get_logger


# Migration suggestions for setup.py

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.config import get_config, set_config


# Migration suggestions for repository.py

# DATABASE MODULE
# - Replace sqlite3.connect() with core.database.get_connection()
# - Use execute_query() and execute_transaction() for database operations
# - Remove manual connection management

# Suggested imports:
from core.database import get_connection, execute_query, execute_transaction


# Migration suggestions for auto_capture.py

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.openelf_logging import setup_logger, get_logger
from core.config import get_config, set_config


# Migration suggestions for broadcast.py

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# Suggested imports:
from core.openelf_logging import setup_logger, get_logger


# Migration suggestions for database.py

# DATABASE MODULE
# - Replace sqlite3.connect() with core.database.get_connection()
# - Use execute_query() and execute_transaction() for database operations
# - Remove manual connection management

# LOGGING MODULE
# - Replace logging.basicConfig() with core.openelf_logging.setup_logger()
# - Use get_logger() instead of logging.getLogger()
# - Consolidate logging configuration

# Suggested imports:
from core.database import get_connection, execute_query, execute_transaction
from core.openelf_logging import setup_logger, get_logger


# Migration suggestions for outcome_inference.py

# CONFIG MODULE
# - Use core.config.get_config() for configuration access
# - Replace manual JSON/YAML parsing with config module
# - Centralize configuration management

# Suggested imports:
from core.config import get_config, set_config

