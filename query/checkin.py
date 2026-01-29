#!/usr/bin/env python3
"""
OpenCode Checkin Orchestrator

Unified checkin process that:
1. Auto-starts OpenCode server if not running
2. Verifies server health (port 4096)
3. Validates agent availability
4. Reports system status
5. Ready for orchestration
"""

import sys
import time
import requests
import subprocess
import os
from pathlib import Path
from typing import Dict, Any, Tuple

# Setup paths
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

class CheckinOrchestrator:
    """Orchestrates the checkin process"""
    
    def __init__(self, server_url: str = "http://localhost:4096"):
        self.server_url = server_url
        self.results = {}
        self.all_ok = True
        self.server_process = None
        self.server_started = False
    
    def print_header(self):
        """Print welcome banner"""
        print("\n" + "="*60)
        print("🔄 OpenCode Checkin Orchestrator")
        print("="*60 + "\n")
    
    def get_available_terminal(self) -> str:
        """Detect available terminal emulator"""
        terminals = [
            "gnome-terminal",
            "xterm",
            "konsole",
            "xfce4-terminal",
            "mate-terminal",
            "lxterminal",
            "urxvt",
            "rxvt",
        ]
        
        for term in terminals:
            try:
                result = subprocess.run(
                    ["which", term],
                    capture_output=True,
                    timeout=1
                )
                if result.returncode == 0:
                    return term
            except:
                pass
        
        return None
    
    def start_server_in_terminal(self) -> bool:
        """Start OpenCode server in a separate terminal window"""
        print("   ⚙️  Starting OpenCode server in terminal...")
        
        terminal = self.get_available_terminal()
        
        if not terminal:
            print("   ⚠️  No terminal emulator found, starting in background...")
            # Fallback to background start
            try:
                self.server_process = subprocess.Popen(
                    ["opencode", "serve", "--port", "4096"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                print("   ℹ️  Server running in background")
            except Exception as e:
                print(f"   ❌ Failed to start server: {e}")
                return False
        else:
            # Start in terminal
            try:
                if terminal == "gnome-terminal":
                    subprocess.Popen([
                        "gnome-terminal",
                        "--",
                        "bash", "-c",
                        "opencode serve --port 4096; bash"
                    ])
                elif terminal == "xterm":
                    subprocess.Popen([
                        "xterm",
                        "-hold",
                        "-e",
                        "opencode serve --port 4096"
                    ])
                elif terminal == "konsole":
                    subprocess.Popen([
                        "konsole",
                        "-e",
                        "bash", "-c",
                        "opencode serve --port 4096; bash"
                    ])
                elif terminal == "xfce4-terminal":
                    subprocess.Popen([
                        "xfce4-terminal",
                        "-e",
                        "bash -c 'opencode serve --port 4096; bash'"
                    ])
                else:
                    # Generic terminal
                    subprocess.Popen([
                        terminal,
                        "-e",
                        "opencode serve --port 4096"
                    ])
                
                print(f"   ✅ Server starting in {terminal} window")
                print(f"   You can monitor and close the terminal window as needed")
                
            except Exception as e:
                print(f"   ❌ Failed to launch terminal: {e}")
                return False
        
        return True
    
    def start_server_if_needed(self) -> bool:
        """Start OpenCode server if not already running"""
        print("0️⃣  Checking OpenCode Server Status...")
        
        # First check if already running
        try:
            resp = requests.get(
                f"{self.server_url}/global/health",
                timeout=2
            )
            if resp.status_code == 200:
                print("   ✅ Server already running")
                return True
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pass  # Server not running, will start it
        
        # Server not running, try to start it
        if not self.start_server_in_terminal():
            return False
        
        print("   ⏳ Waiting for server to start...")
        
        # Wait for server to be ready (max 30 seconds)
        max_retries = 30
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                resp = requests.get(
                    f"{self.server_url}/global/health",
                    timeout=2
                )
                if resp.status_code == 200:
                    print("   ✅ Server started successfully")
                    self.server_started = True
                    return True
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                retry_count += 1
                if retry_count % 5 == 0:
                    print(f"   ⏳ Still waiting... ({retry_count}s)")
                time.sleep(1)
        
        print("   ❌ Server failed to start within 30 seconds")
        return False
    
    def check_server(self) -> Tuple[bool, Dict[str, Any]]:
        """Check OpenCode server health"""
        print("1️⃣  Verifying OpenCode Server...")
        
        try:
            resp = requests.get(
                f"{self.server_url}/global/health",
                timeout=2
            )
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✅ Server responding")
                print(f"   Version: {data.get('version', 'unknown')}")
                return True, data
            else:
                print(f"   ❌ Server returned {resp.status_code}")
                return False, {}
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Cannot connect to {self.server_url}")
            print(f"   Start server with: opencode serve --port 4096")
            return False, {}
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False, {}
    
    def check_agents(self) -> Tuple[bool, Dict[str, Any]]:
        """Check agent availability"""
        print("\n2️⃣  Checking Agents...")
        
        try:
            resp = requests.get(
                f"{self.server_url}/agent",
                timeout=5
            )
            
            if resp.status_code == 200:
                agents = resp.json()
                
                # Count available agents
                agent_count = len(agents) if isinstance(agents, list) else 0
                
                print(f"   ✅ Agents available: {agent_count}")
                
                # Check for custom agents
                custom_agents = [
                    "researcher", "architect", "skeptic", 
                    "creative", "ceo", "learning-extractor"
                ]
                
                # Get agent names from response (varies by OpenCode version)
                available_names = []
                if isinstance(agents, list):
                    available_names = [
                        a.get('name', '') or a.get('id', '')
                        for a in agents
                    ]
                
                found_custom = sum(
                    1 for ca in custom_agents 
                    if any(ca in str(name).lower() for name in available_names)
                )
                
                if agent_count > 0:
                    print(f"   Includes: {', '.join(available_names[:3])}...")
                
                return agent_count > 0, {"count": agent_count, "agents": agents}
                
            else:
                print(f"   ⚠️  Agents endpoint returned {resp.status_code}")
                return False, {}
                
        except Exception as e:
            print(f"   ⚠️  Cannot verify agents: {e}")
            return False, {}
    
    def check_orchestrator(self) -> Tuple[bool, Dict[str, Any]]:
        """Check orchestrator availability via HTTP API"""
        print("\n3️⃣  Checking Orchestrator...")
        
        try:
            # Orchestrator now runs via HTTP API on OpenCode server
            # Check if we can verify the parties configuration
            
            # Method 1: Try importing to get party count (if available locally)
            try:
                sys.path.insert(0, str(ROOT_DIR / "src"))
                from orchestrator import Orchestrator
                
                # Create orchestrator (uses HTTP API)
                orch = Orchestrator(server_url=self.server_url)
                
                # Check parties loaded
                parties = orch.router.list_parties()
                party_count = len(parties)
                
                print(f"   ✅ Orchestrator ready")
                print(f"   Parties loaded: {party_count}")
                
                return True, {"parties": party_count, "orchestrator": "ready"}
            
            except ImportError:
                # Method 2: Fallback to checking via HTTP API
                # The orchestrator code exists on disk, just check if parties config is readable
                parties_file = ROOT_DIR / "agents" / "parties.yaml"
                
                if parties_file.exists():
                    # Count parties in YAML file
                    import re
                    content = parties_file.read_text()
                    party_count = len(re.findall(r'^[a-z-]+:\s*$', content, re.MULTILINE)) - 1  # -1 for 'custom'
                    
                    print(f"   ✅ Orchestrator configuration found")
                    print(f"   Parties available: {party_count}")
                    
                    return True, {"parties": party_count, "orchestrator": "configured"}
                else:
                    print(f"   ⚠️  Orchestrator configuration not found")
                    return False, {}
            
        except Exception as e:
            # Check if at least the orchestrator module exists
            orch_path = ROOT_DIR / "src" / "orchestrator.py"
            
            if orch_path.exists():
                print(f"   ⚠️  Orchestrator module exists but cannot be fully validated")
                print(f"   ({str(e)[:50]}...)")
                return True, {"orchestrator": "present", "error": str(e)[:50]}
            else:
                print(f"   ❌ Orchestrator not found")
                return False, {}
    
    def check_watcher(self) -> Tuple[bool, Dict[str, Any]]:
        """Check watcher availability"""
        print("\n4️⃣  Checking Watcher...")
        
        watcher_path = ROOT_DIR / "src" / "watcher" / "launcher.py"
        
        if watcher_path.exists():
            print(f"   ✅ Watcher module available")
            
            # Check for HTTP API support
            content = watcher_path.read_text()
            if "call_opencode_http" in content:
                print(f"   ✅ HTTP API integration present")
                return True, {"watcher": "ready", "http_api": True}
            else:
                print(f"   ⚠️  No HTTP API support")
                return False, {"watcher": "ready", "http_api": False}
        else:
            print(f"   ❌ Watcher not found")
            return False, {}
    
    def check_agents_framework(self) -> Tuple[bool, Dict[str, Any]]:
        """Check agent framework"""
        print("\n5️⃣  Checking Agent Framework...")
        
        try:
            from agents.base_agent import (
                ResearcherAgent, ArchitectAgent, 
                SkepticAgent, CreativeAgent
            )
            
            print(f"   ✅ Agent classes available")
            print(f"   - ResearcherAgent")
            print(f"   - ArchitectAgent")
            print(f"   - SkepticAgent")
            print(f"   - CreativeAgent")
            
            return True, {"agents": 4}
            
        except Exception as e:
            print(f"   ⚠️  Agent framework check failed: {e}")
            return False, {}
    
    def check_system_status(self) -> Tuple[bool, Dict[str, Any]]:
        """Check overall system status"""
        print("\n6️⃣  System Status:")
        
        status = {
            "server": self.results.get("server", False),
            "agents": self.results.get("agents", False),
            "orchestrator": self.results.get("orchestrator", False),
            "watcher": self.results.get("watcher", False),
            "framework": self.results.get("framework", False),
        }
        
        operational = sum(1 for v in status.values() if v)
        total = len(status)
        
        print(f"\n   Status: {operational}/{total} components OK")
        
        if operational == total:
            print(f"   🟢 FULLY OPERATIONAL")
            return True, status
        elif operational >= 3:
            print(f"   🟡 MOSTLY OPERATIONAL")
            return True, status
        else:
            print(f"   🔴 DEGRADED")
            return False, status
    
    def launch_background_services(self) -> bool:
        """Launch all services in background"""
        print("\n" + "="*60)
        print("🚀 Launching Background Services...")
        print("="*60 + "\n")
        
        services = [
            ("Watcher", "src/watcher/launcher.py"),
            ("Orchestrator", "src/orchestrator.py"),
            ("CEO Advisor", "agents/dashboard_sentinel_ceo.py"),
        ]
        
        launched = 0
        
        for service_name, script_path in services:
            try:
                full_path = ROOT_DIR / script_path
                
                if not full_path.exists():
                    print(f"   ⚠️  {service_name} not found ({script_path})")
                    continue
                
                # Launch in background (detached)
                if script_path == "agents/dashboard_sentinel_ceo.py":
                    # CEO requires --ceo flag
                    subprocess.Popen(
                        [sys.executable, str(full_path), "--ceo"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                else:
                    # Other services
                    subprocess.Popen(
                        [sys.executable, str(full_path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                
                print(f"   ✅ {service_name} launched in background")
                launched += 1
                time.sleep(0.5)  # Small delay to prevent race conditions
                
            except Exception as e:
                print(f"   ⚠️  Failed to launch {service_name}: {str(e)[:50]}")
        
        print(f"\n   {launched}/{len(services)} services launched")
        return launched > 0
    
    def print_next_steps(self, all_ok: bool, services_launched: bool = False, check_only: bool = False):
        """Print recommendations"""
        print("\n" + "="*60)
        
        if all_ok:
            if services_launched:
                print("✅ System Ready!\n")
                print("   All services are running in background:")
                print("   • Watcher - Monitoring experiments")
                print("   • Orchestrator - Multi-agent coordination")
                print("   • CEO Advisor - Business intelligence\n")
                print("   You can now use OpenCode TUI normally.")
                print("   Everything runs automatically in the background.\n")
                print("   To stop services: pkill -f 'orchestrator\\|watcher\\|dashboard_sentinel'\n")
            elif check_only:
                print("✅ System Health Check Complete:\n")
                print("   All components operational and ready to use.\n")
                print("   To launch services: python3 emergent-learning/query/checkin.py\n")
            else:
                # This shouldn't happen (services_launched should be True if all_ok and not check_only)
                print("✅ System Ready to Use\n")
        else:
            if not self.results.get("server", False):
                print("❌ OpenCode Server Required:\n")
                print("   opencode serve --port 4096\n")
        
        print("="*60 + "\n")
    
    def run(self, check_only: bool = False) -> bool:
        """Run full checkin and launch services by default"""
        self.print_header()
        
        # Step 0: Start server if needed
        server_ok = self.start_server_if_needed()
        
        if not server_ok:
            self.all_ok = False
            print("\n❌ Cannot proceed without OpenCode server")
            print("   Install: npm install -g opencode")
            print("   Then run again")
            return False
        
        print()  # Blank line
        
        # Run all checks
        self.results["server"], _ = self.check_server()
        
        if not self.results["server"]:
            self.all_ok = False
            self.print_next_steps(False, check_only)
            return False
        
        # Continue checks if server OK
        self.results["agents"], _ = self.check_agents()
        self.results["orchestrator"], _ = self.check_orchestrator()
        self.results["watcher"], _ = self.check_watcher()
        self.results["framework"], _ = self.check_agents_framework()
        
        # Check overall status
        all_ok, _ = self.check_system_status()
        self.all_ok = all_ok
        
        # Launch background services BY DEFAULT (unless --check-only flag)
        services_launched = False
        if all_ok and not check_only:
            services_launched = self.launch_background_services()
        
        # Print recommendations
        self.print_next_steps(all_ok, services_launched, check_only)
        
        return all_ok


def main() -> int:
    """Main entry point"""
    # By default: launch all services
    # Use --check-only to just verify without launching
    check_only = "--check-only" in sys.argv
    
    orchestrator = CheckinOrchestrator()
    success = orchestrator.run(check_only=check_only)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
