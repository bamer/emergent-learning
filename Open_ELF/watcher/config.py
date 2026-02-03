"""
Configuration for ELF Watcher system.

Based on Tiered Watcher Pattern from original ELF design.
"""

# Watcher Timing
POLL_INTERVAL = 30  # Seconds between checks
HEARTBEAT_TIMEOUT = 120  # Seconds before considering agent dead
MAX_RESTART_ATTEMPTS = 3  # Max consecutive restarts before giving up

# Logging
LOG_RETENTION = 100  # Log entries to keep in memory
MAX_LOG_SIZE_MB = 10  # Max log file size before rotation

# OpenCode Configuration
# Note: We use ONE model for both tiers, but adapt via prompt depth
OPENCODE_SERVER_URL = "http://localhost:4096"
OPENCODE_MODEL = (
    "opencode/big-pickle"  # Single model for all tiers (adapts to prompt depth)
)

# Exit Codes (from original ELF spec)
EXIT_NORMAL = 0  # Clean shutdown (user-initiated)
EXIT_INTERVENTION = 1  # Escalation needed (will be handled by launcher)
EXIT_ERROR = 2  # Error occurred (will retry)

# Paths
COORDINATION_DIR = None  # Will be set at runtime from get_base_path()
BLACKBOARD_FILE = None  # Will be set at runtime
WATCHER_LOG = None  # Will be set at runtime
STOP_FILE = None  # Will be set at runtime
