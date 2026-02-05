#!/usr/bin/env python3
"""
swarm_controller.py - Swarm Agent Coordinator

Manages parallel execution of multiple agents for a single task.
Distributes subtasks, collects results, merges learnings, and updates confidence.

Architecture:
  Task Input
    ↓
  Parse & Divide into Subtasks
    ↓
  Spawn Agents in Parallel (big-pickle)
    ↓
  Collect Results & [LEARNED:] markers
    ↓
  Merge & Validate
    ↓
  Update Database with Learnings
    ↓
  Return Combined Result
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import sqlite3
import concurrent.futures

sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import HeuristicModel, fallback to direct DB insert
try:
    from query.models import HeuristicModel
    HAS_HEURISTIC_MODEL = True
except ImportError:
    HAS_HEURISTIC_MODEL = False

class SwarmController:
    """Orchestrates parallel agent execution for swarm tasks."""
    
    def __init__(self):
        self.elf_home = Path.home() / ".opencode" / "emergent-learning"
        self.db_path = self.elf_home / "memory" / "index.db"
        self.agents_config = self._load_agents_config()
        self.blackboard_path = self.elf_home / ".coordination" / "blackboard.json"
        self.task_id = None
        self.results = {}
        self.learnings = []
    
    def _load_agents_config(self) -> Dict:
        """Load agent configuration from parties.yaml"""
        # Default agents (always available)
        default_agents = [
            {
                'name': 'architect',
                'role': 'System design & structure',
                'model': 'opencode/big-pickle',
                'max_parallel': 1
            },
            {
                'name': 'researcher',
                'role': 'Research & validation',
                'model': 'opencode/big-pickle',
                'max_parallel': 2
            },
            {
                'name': 'skeptic',
                'role': 'Testing & edge cases',
                'model': 'opencode/big-pickle',
                'max_parallel': 2
            },
            {
                'name': 'creative',
                'role': 'Novel solutions',
                'model': 'opencode/big-pickle',
                'max_parallel': 1
            }
        ]
        
        try:
            import yaml
            config_path = self.elf_home / "agents" / "parties.yaml"
            if config_path.exists():
                config = yaml.safe_load(config_path)
                if config and 'parties' in config and 'swarm' in config['parties']:
                    swarm_agents = config['parties']['swarm']
                    if swarm_agents:
                        return config
        except:
            pass
        
        # Fallback: Return default agents
        return {
            'parties': {
                'swarm': default_agents
            }
        }
    
    def _update_blackboard(self, status: str, agents_status: Dict = None):
        """Update coordination blackboard with current status."""
        self.blackboard_path.parent.mkdir(parents=True, exist_ok=True)
        
        blackboard = {
            'task_id': self.task_id,
            'status': status,
            'updated_at': datetime.now().isoformat(),
            'agents': agents_status or {}
        }
        
        try:
            self.blackboard_path.write_text(json.dumps(blackboard, indent=2))
        except:
            pass
    
    def _spawn_agent(self, agent_name: str, subtask: str) -> Dict[str, Any]:
        """
        Spawn a single agent to handle a subtask.
        
        Args:
            agent_name: Name of agent (architect, researcher, etc.)
            subtask: The subtask description
            
        Returns:
            Dict with result and learnings
        """
        print(f"  → Spawning {agent_name} agent for: {subtask[:50]}...")
        
        agent_dir = self.elf_home / "agents" / agent_name
        run_script = agent_dir / "run_extractor.py"
        
        result = {
            'agent': agent_name,
            'subtask': subtask,
            'status': 'running',
            'output': '',
            'learnings': [],
            'confidence': 0.7
        }
        
        # Use real agent script
        if not run_script.exists():
            result['status'] = 'failed'
            result['output'] = f"Agent script not found: {run_script}"
            return result
        
        script_to_use = run_script
        
        try:
            # Execute agent with subtask prompt
            process_result = subprocess.run(
                [sys.executable, str(script_to_use), agent_name, '--prompt', subtask],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            result['output'] = process_result.stdout or process_result.stderr
            result['status'] = 'completed' if process_result.returncode == 0 else 'failed'
            
            # Extract [LEARNED:] markers from output
            result['learnings'] = self._extract_learnings(result['output'])
            
            print(f"     ✓ {agent_name}: {len(result['learnings'])} learnings extracted")
            
        except subprocess.TimeoutExpired:
            result['status'] = 'timeout'
            result['output'] = f"Agent {agent_name} timed out after 60s"
        except Exception as e:
            result['status'] = 'error'
            result['output'] = str(e)
        
        return result
    
    def _extract_learnings(self, text: str) -> List[str]:
        """Extract [LEARNED:] markers from agent output."""
        import re
        learnings = []
        pattern = r'\[LEARNED:\s*([^\]]+)\]'
        for match in re.finditer(pattern, text, re.IGNORECASE):
            learning = match.group(1).strip()
            if learning:
                learnings.append(learning)
        return learnings
    
    def _merge_results(self, all_results: List[Dict]) -> Dict[str, Any]:
        """
        Merge results from all agents.
        
        Returns:
            Combined result with all learnings and unified recommendation
        """
        merged = {
            'status': 'success',
            'all_learnings': [],
            'agent_results': all_results,
            'summary': '',
            'recommendation': ''
        }
        
        # Collect all learnings
        for result in all_results:
            merged['all_learnings'].extend(result['learnings'])
        
        # Build summary
        completed = sum(1 for r in all_results if r['status'] == 'completed')
        total = len(all_results)
        
        merged['summary'] = f"{completed}/{total} agents completed successfully"
        
        if completed == total:
            merged['status'] = 'success'
            merged['recommendation'] = "All agents converged - high confidence"
        elif completed >= total * 0.75:
            merged['status'] = 'partial_success'
            merged['recommendation'] = "Majority of agents succeeded - acceptable"
        else:
            merged['status'] = 'failed'
            merged['recommendation'] = "Too many agent failures - review manually"
        
        return merged
    
    def _store_learnings(self, learnings: List[str], agent_name: str):
        """Store extracted learnings in database."""
        if not learnings:
            return
        
        if HAS_HEURISTIC_MODEL:
            try:
                for learning_text in learnings:
                    heuristic = HeuristicModel(
                        pattern=learning_text,
                        domain=f"swarm_{agent_name}",
                        confidence=0.7,
                        tags=['swarm', 'auto-extracted'],
                        explanation=f"Learned by {agent_name} agent during swarm execution"
                    )
                    heuristic.save()
            except:
                pass  # Non-critical
        else:
            # Fallback: direct database insert
            try:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                for learning_text in learnings:
                    cursor.execute("""
                        INSERT OR IGNORE INTO heuristics 
                        (pattern, domain, confidence, created_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """, (learning_text, f"swarm_{agent_name}", 0.7))
                conn.commit()
                conn.close()
            except:
                pass  # Non-critical
    
    def execute_swarm(self, task_description: str, subtasks: List[str] = None) -> Dict[str, Any]:
        """
        Execute a task using swarm of agents.
        
        Args:
            task_description: Main task description
            subtasks: List of subtasks, or None to auto-generate
            
        Returns:
            Combined result from all agents
        """
        self.task_id = f"swarm_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"\n🐝 SWARM EXECUTION STARTED")
        print(f"   Task ID: {self.task_id}")
        print(f"   Task: {task_description[:60]}...")
        print()
        
        # Generate subtasks if not provided
        if not subtasks:
            subtasks = self._generate_subtasks(task_description)
        
        # Get available agents
        agents = self.agents_config.get('parties', {}).get('swarm', [])[:4]
        
        # Safety check: ensure we have agents
        if not agents:
            print("❌ ERROR: No agents configured")
            return {
                'status': 'failed',
                'error': 'No agents available',
                'all_learnings': [],
                'agent_results': [],
                'summary': 'No agents configured',
                'recommendation': 'Configuration error'
            }
        
        print(f"📋 SUBTASKS ({len(subtasks)}):")
        for i, subtask in enumerate(subtasks, 1):
            print(f"   {i}. {subtask[:60]}...")
        
        print()
        print(f"🤖 AGENTS ({len(agents)}):")
        for agent in agents:
            print(f"   • {agent['name']}: {agent['role']}")
        
        print()
        print("⚙️  SPAWNING AGENTS IN PARALLEL...")
        print()
        
        # Distribute subtasks to agents (round-robin)
        self._update_blackboard('spawning')
        
        agent_tasks = []
        for i, subtask in enumerate(subtasks):
            agent = agents[i % len(agents)]
            agent_tasks.append((agent['name'], subtask))
        
        # Execute agents in parallel
        all_results = []
    # IMPORTANT: Limiter les résultats pour éviter l'accumulation mémoire
    # IMPORTANT: Limiter les résultats pour éviter l'accumulation mémoire
    # IMPORTANT: Limiter les résultats pour éviter l'accumulation mémoire
    # IMPORTANT: Limiter les résultats pour éviter l'accumulation mémoire
        agents_status = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._spawn_agent, agent_name, subtask): (agent_name, subtask)
                for agent_name, subtask in agent_tasks
            }
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                all_results.append(result)
                
                agents_status[result['agent']] = {
                    'status': result['status'],
                    'learnings_count': len(result['learnings'])
                }
                
                # Store learnings immediately
                self._store_learnings(result['learnings'], result['agent'])
        
        self._update_blackboard('completed', agents_status)
        
        # Merge and return results
        print()
        print("🔀 MERGING RESULTS...")
        merged = self._merge_results(all_results)
        
        print()
        print(f"✅ SWARM EXECUTION COMPLETE")
        print(f"   Status: {merged['status']}")
        print(f"   Summary: {merged['summary']}")
        print(f"   Learnings captured: {len(merged['all_learnings'])}")
        print(f"   Recommendation: {merged['recommendation']}")
        
        return merged
    
    def _generate_subtasks(self, task_description: str) -> List[str]:
        """Generate subtasks from main task description."""
        # Simple heuristic: split by sentences or create related tasks
        subtasks = [
            f"Analyze and understand: {task_description}",
            f"Design solution for: {task_description}",
            f"Validate approach for: {task_description}",
            f"Test implementation for: {task_description}"
        ]
        return subtasks

def main():
    """CLI interface for swarm controller."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Swarm Agent Controller")
    parser.add_argument('--task', required=True, help='Main task description')
    parser.add_argument('--subtasks', nargs='+', help='Optional subtasks')
    args = parser.parse_args()
    
    controller = SwarmController()
    result = controller.execute_swarm(args.task, args.subtasks)
    
    print("\n📊 DETAILED RESULTS:")
    print(json.dumps(result, indent=2))
    
    return 0 if result['status'] == 'success' else 1

if __name__ == '__main__':
    sys.exit(main())
