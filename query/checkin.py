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
        print("   ⚙️  Starting OpenCode server...")
        
        try:
            # Start server in background
            self.server_process = subprocess.Popen(
                ["opencode", "serve", "--port", "4096"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True  # Detach from current process
            )
            
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
            
        except FileNotFoundError:
            print("   ❌ OpenCode not found in PATH")
            print("   Install with: npm install -g opencode")
            return False
        except Exception as e:
            print(f"   ❌ Failed to start server: {e}")
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
    
    def print_next_steps(self, all_ok: bool):
        """Print recommendations"""
        print("\n" + "="*60)
        
        if all_ok:
            print("✅ Ready to Use:\n")
            print("   # Run orchestrator")
            print("   python3 emergent-learning/src/orchestrator.py\n")
            print("   # Or test agents")
            print("   python3 emergent-learning/agents/base_agent.py\n")
            print("   # Or run demo")
            print("   bash demo_agents.sh\n")
        else:
            if not self.results.get("server", False):
                print("❌ OpenCode Server Required:\n")
                print("   opencode serve --port 4096\n")
        
        print("="*60 + "\n")
    
    def run(self) -> bool:
        """Run full checkin"""
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
            self.print_next_steps(False)
            return False
        
        # Continue checks if server OK
        self.results["agents"], _ = self.check_agents()
        self.results["orchestrator"], _ = self.check_orchestrator()
        self.results["watcher"], _ = self.check_watcher()
        self.results["framework"], _ = self.check_agents_framework()
        
        # Check overall status
        all_ok, _ = self.check_system_status()
        self.all_ok = all_ok
        
        # Print recommendations
        self.print_next_steps(all_ok)
        
        return all_ok


def main() -> int:
    """Main entry point"""
    orchestrator = CheckinOrchestrator()
    success = orchestrator.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
