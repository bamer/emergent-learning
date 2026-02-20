"""
Configuration du Mission Engine
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class MissionEngineConfig:
    """Configuration du Mission Engine"""
    
    # URLs et endpoints
    opencode_url: str = field(default="http://localhost:4096")
    event_bridge_url: str = field(default="http://localhost:9998")
    
    # Chemins
    agents_dir: Path = field(default_factory=lambda: Path("/home/bamer/.opencode/agents/OPC_ELF_System_Agents"))
    missions_db_path: Path = field(default_factory=lambda: Path("/home/bamer/OPC_ELF/Open_ELF/mission-engine/data/missions.db"))
    logs_dir: Path = field(default_factory=lambda: Path("/home/bamer/OPC_ELF/Open_ELF/mission-engine/logs"))
    
    # Timeouts
    agent_timeout: int = field(default=600)  # 10 minutes
    mission_timeout: int = field(default=3600)  # 1 heure
    
    # Live Tab
    live_tab_auto_refresh: bool = field(default=True)
    live_tab_refresh_interval: int = field(default=30)  # secondes
    live_tab_max_missions: int = field(default=50)
    
    # CEO Escalation
    auto_escalate_critical: bool = field(default=True)
    ceo_review_threshold: float = field(default=0.8)  # Score de criticité
    
    # Logging
    log_level: str = field(default="INFO")
    log_to_file: bool = field(default=True)
    
    @classmethod
    def from_env(cls) -> "MissionEngineConfig":
        """Charge la configuration depuis les variables d'environnement"""
        return cls(
            opencode_url=os.getenv("OPENCODE_URL", "http://localhost:4096"),
            event_bridge_url=os.getenv("EVENT_BRIDGE_URL", "http://localhost:9998"),
            agents_dir=Path(os.getenv("AGENTS_DIR", "/home/bamer/.opencode/agents/OPC_ELF_System_Agents")),
            missions_db_path=Path(os.getenv("MISSIONS_DB_PATH", "/home/bamer/OPC_ELF/Open_ELF/mission-engine/data/missions.db")),
            logs_dir=Path(os.getenv("MISSION_LOGS_DIR", "/home/bamer/OPC_ELF/Open_ELF/mission-engine/logs")),
            agent_timeout=int(os.getenv("AGENT_TIMEOUT", "600")),
            mission_timeout=int(os.getenv("MISSION_TIMEOUT", "3600")),
            live_tab_auto_refresh=os.getenv("LIVE_TAB_AUTO_REFRESH", "true").lower() == "true",
            live_tab_refresh_interval=int(os.getenv("LIVE_TAB_REFRESH_INTERVAL", "30")),
            live_tab_max_missions=int(os.getenv("LIVE_TAB_MAX_MISSIONS", "50")),
            auto_escalate_critical=os.getenv("AUTO_ESCALATE_CRITICAL", "true").lower() == "true",
            ceo_review_threshold=float(os.getenv("CEO_REVIEW_THRESHOLD", "0.8")),
            log_level=os.getenv("MISSION_LOG_LEVEL", "INFO"),
            log_to_file=os.getenv("MISSION_LOG_TO_FILE", "true").lower() == "true",
        )
    
    def ensure_directories(self):
        """Crée les répertoires nécessaires"""
        self.missions_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
