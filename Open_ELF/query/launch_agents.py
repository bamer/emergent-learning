#!/usr/bin/env python3
"""
Launch ELF Agents with Server - Improved Manager

Handles:
1. Waiting for OpenCode server to be ready
2. Launching agents in background or terminal
3. Proper environment setup
4. Logging and error handling
"""

import os
import sys
import time
import subprocess
import requests
import signal
from pathlib import Path
from typing import Optional

# Import centralized logger (NOUVEAU SYSTÈME UNIFIÉ)
try:
    from Open_ELF.utils.elf_logging import get_logger, log_critical, log_error, log_warning, log_info
    logger = get_logger("launch_agents")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("launch_agents")

# Setup logging
s] %(message)s"
)
logger = logging.getLogger("AgentLauncher")

class AgentLauncher:
    """Launch and manage ELF agents."""
    
    def __init__(self, elf_home: Path, server_url: str = "http://localhost:4096"):
        self.elf_home = elf_home
        self.server_url = server_url
        self.processes = []
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._cleanup)
        signal.signal(signal.SIGINT, self._cleanup)
    
    def _cleanup(self, signum, frame):
        """Cleanup on exit."""
        logger.info("🛑 Arrêt des agents...")
        for proc in self.processes:
            try:
                proc.terminate()
            except:
                pass
        time.sleep(1)
        sys.exit(0)
    
    def wait_for_server(self, timeout: int = 60) -> bool:
        """Wait for OpenCode server to be ready."""
        logger.info(f"⏳ Attente du serveur {self.server_url}...")
        
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = requests.get(
                    f"{self.server_url}/",
                    timeout=2
                )
                if resp.status_code == 200:
                    logger.info(f"✅ Serveur prêt! {resp.json()}")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
        
        logger.warning(f"⚠️  Serveur pas réactif après {timeout}s (continuant...)")
        return False
    
    def launch_sentinel(self) -> Optional[subprocess.Popen]:
        """Launch Dashboard Sentinel (CEO agent)."""
        sentinel_script = self.elf_home / "agents" / "sentinel_startup.py"
        
        if not sentinel_script.exists():
            logger.error(f"❌ Sentinel script not found: {sentinel_script}")
            return None
        
        logger.info("👑 Lancement du Sentinel (CEO)...")
        
        try:
            # Setup environment
            env = os.environ.copy()
            env["ELF_BASE_PATH"] = str(self.elf_home)
            env["PYTHONUNBUFFERED"] = "1"
            
            # Launch in background
            proc = subprocess.Popen(
                [
                    sys.executable,
                    str(sentinel_script),
                    "--interval", "30",
                    "--log-level", "INFO"
                ],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                preexec_fn=os.setsid  # Create process group
            )
            
            self.processes.append(proc)
            logger.info(f"✓ Sentinel lancé (PID: {proc.pid})")
            
            return proc
        
        except Exception as e:
            logger.error(f"❌ Erreur lors du démarrage du Sentinel: {e}")
            return None
    
    def launch_in_terminal(self, terminal: str = "gnome-terminal") -> bool:
        """Launch agents in visible terminal windows."""
        logger.info(f"🖥  Utilisation de {terminal}...")
        
        # Build command for agents terminal
        elf_home = str(self.elf_home)
        sentinel_script = self.elf_home / "agents" / "sentinel_startup.py"
        
        if not sentinel_script.exists():
            logger.error(f"❌ Sentinel script not found: {sentinel_script}")
            return False
        
        cmd = f"""
cd "{elf_home}"
echo '🤖 ELF Agents - Missions en cours'
echo ''
echo '👑 Sentinel (CEO): Orchestration et monitoring'
echo '🔬 Researcher: Recherche et investigation'
echo '🏗️  Architect: Design et architecture'
echo '❓ Skeptic: Revue critique'
echo '💡 Creative: Solutions créatives'
echo ''
echo 'Missions:'
echo '  - Monitoring continu'
echo '  - Analyse des patterns'
echo '  - Prise de décision autonome'
echo '  - Apprentissage itératif'
echo ''
echo '⏹️  Ctrl+C pour arrêter'
echo ''
python3 {sentinel_script} --interval 30 --log-level INFO
echo ''
echo '✅ Agents arrêtés'
read -p "Appuyez sur Entrée pour fermer..."
"""
        
        try:
            if terminal == "gnome-terminal":
                subprocess.Popen([
                    "gnome-terminal",
                    "--title=ELF Agents",
                    "--geometry=140x40",
                    "--",
                    "bash", "-c", cmd
                ])
            elif terminal == "xterm":
                subprocess.Popen([
                    "xterm",
                    "-title", "ELF Agents",
                    "-geometry", "140x40",
                    "-e", "bash", "-c", cmd
                ])
            elif terminal == "konsole":
                subprocess.Popen([
                    "konsole",
                    "--title", "ELF Agents",
                    "--", "bash", "-c", cmd
                ])
            else:
                logger.error(f"❌ Terminal non supporté: {terminal}")
                return False
            
            logger.info("✅ Terminal agents lancé!")
            return True
        
        except Exception as e:
            logger.error(f"❌ Erreur lors du lancement du terminal: {e}")
            return False
    
    def find_available_terminal(self) -> Optional[str]:
        """Find available terminal emulator."""
        terminals = [
            "gnome-terminal",
            "xterm",
            "konsole",
            "xfce4-terminal",
            "lxterminal",
            "terminator",
            "urxvt"
        ]
        
        for term in terminals:
            try:
                subprocess.run(
                    ["which", term],
                    capture_output=True,
                    check=True
                )
                return term
            except subprocess.CalledProcessError:
                continue
        
        return None
    
    def launch(self, use_terminal: bool = True) -> bool:
        """Launch agents with server."""
        logger.info("=" * 70)
        logger.info("🚀 Lancement des agents ELF")
        logger.info("=" * 70)
        
        # Step 1: Wait for server
        if not self.wait_for_server(timeout=60):
            logger.warning("⚠️  Serveur pas prêt, continuant quand même...")
        
        time.sleep(1)
        
        # Step 2: Launch agents
        if use_terminal:
            terminal = self.find_available_terminal()
            if terminal:
                logger.info(f"📱 Terminal détecté: {terminal}")
                self.launch_in_terminal(terminal)
            else:
                logger.warning("⚠️  Aucun terminal trouvé, lancement en arrière-plan...")
                self.launch_sentinel()
        else:
            self.launch_sentinel()
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ Agents lancés avec leurs missions!")
        logger.info("=" * 70)
        logger.info("")
        logger.info("📊 Monitoring:")
        logger.info(f"  - Serveur: {self.server_url}")
        logger.info(f"  - Health: {self.server_url}/")
        logger.info(f"  - API Docs: {self.server_url}/doc")
        logger.info("")
        logger.info("🤖 Agents actifs:")
        logger.info("  - Sentinel (CEO): Orchestration")
        logger.info("  - Researcher: Investigation")
        logger.info("  - Architect: Design")
        logger.info("  - Skeptic: Review")
        logger.info("  - Creative: Innovation")
        logger.info("")
        
        return True

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Launch ELF Agents with OpenCode Server"
    )
    parser.add_argument(
        "--elf-home",
        default=str(Path.home() / ".opencode" / "emergent-learning"),
        help="ELF home directory"
    )
    parser.add_argument(
        "--server-url",
        default="http://localhost:4096",
        help="OpenCode server URL"
    )
    parser.add_argument(
        "--no-terminal",
        action="store_true",
        help="Launch agents in background (no visible terminal)"
    )
    args = parser.parse_args()
    
    launcher = AgentLauncher(
        Path(args.elf_home),
        args.server_url
    )
    
    success = launcher.launch(use_terminal=not args.no_terminal)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
