#!/usr/bin/env python3
"""
Orchestrator - Multi-Agent Coordination

Routes tasks to appropriate agent teams (parties) based on:
- Task type/keywords
- Available agents
- Party configuration (parties.yaml)
- Workflow type (sequential, parallel, iterative)

Uses HTTP API on port 4096 for all agent communication.
"""

import json
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add agents to path
AGENTS_DIR = Path(__file__).resolve().parents[1] / "agents"
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))

from base_agent import get_agent, BaseAgent
import yaml

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [ORCHESTRATOR] - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Orchestrator")


@dataclass
class Party:
    """Party configuration (team of agents)."""
    name: str
    description: str
    lead: str
    agents: List[str]
    workflow: str  # sequential, parallel, iterative
    triggers: List[str]


class PartyRouter:
    """Routes tasks to appropriate parties."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize router with party configuration.
        
        Args:
            config_path: Path to parties.yaml (auto-detect if None)
        """
        if config_path is None:
            config_path = AGENTS_DIR / "parties.yaml"
        
        self.config_path = Path(config_path)
        self.parties = {}
        self._load_parties()
    
    def _load_parties(self):
        """Load party definitions from YAML."""
        if not self.config_path.exists():
            logger.warning(f"parties.yaml not found at {self.config_path}")
            return
        
        try:
            with open(self.config_path) as f:
                config = yaml.safe_load(f)
            
            for party_name, party_config in config.get("parties", {}).items():
                if party_name == "custom":
                    continue
                
                party = Party(
                    name=party_name,
                    description=party_config.get("description", ""),
                    lead=party_config.get("lead", ""),
                    agents=party_config.get("agents", []),
                    workflow=party_config.get("workflow", "sequential"),
                    triggers=party_config.get("triggers", [])
                )
                self.parties[party_name] = party
                logger.debug(f"Loaded party: {party_name}")
            
            logger.info(f"Loaded {len(self.parties)} parties")
        
        except Exception as e:
            logger.error(f"Failed to load parties: {e}")
    
    def find_party(self, task: str) -> Optional[str]:
        """
        Find best party for a task based on triggers.
        
        Args:
            task: Task description
        
        Returns:
            Party name or None
        """
        task_lower = task.lower()
        
        # Check exact trigger matches
        for party_name, party in self.parties.items():
            for trigger in party.triggers:
                if trigger.lower() in task_lower:
                    logger.info(f"Found party '{party_name}' (trigger: '{trigger}')")
                    return party_name
        
        logger.warning(f"No party found for task: {task[:50]}...")
        return None
    
    def get_party(self, name: str) -> Optional[Party]:
        """Get party by name."""
        return self.parties.get(name)
    
    def list_parties(self) -> Dict[str, str]:
        """List all available parties with descriptions."""
        return {
            name: party.description
            for name, party in self.parties.items()
        }


class Orchestrator:
    """Multi-agent orchestrator using HTTP API."""
    
    def __init__(self, server_url: str = "http://localhost:4096"):
        """
        Initialize orchestrator.
        
        Args:
            server_url: OpenCode server URL
        """
        self.server_url = server_url
        self.router = PartyRouter()
        self.agents = {}
        self.results = []
        logger.info(f"Orchestrator initialized (server: {server_url})")
    
    def _get_agent(self, agent_type: str) -> Optional[BaseAgent]:
        """Get or create agent instance."""
        if agent_type not in self.agents:
            try:
                self.agents[agent_type] = get_agent(
                    agent_type,
                    server_url=self.server_url
                )
            except Exception as e:
                logger.error(f"Failed to create {agent_type} agent: {e}")
                return None
        
        return self.agents[agent_type]
    
    def execute_sequential(
        self,
        party: Party,
        task: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute party agents sequentially.
        Output of each agent becomes input for next.
        """
        context = context or {}
        logger.info(f"Executing {party.name} (sequential)...")
        
        current_input = task
        results = []
        
        for agent_name in party.agents:
            logger.info(f"  → {agent_name}")
            agent = self._get_agent(agent_name)
            
            if not agent:
                logger.error(f"  ✗ Failed to get {agent_name}")
                continue
            
            try:
                response = agent.call(current_input)
                
                if response:
                    results.append({
                        "agent": agent_name,
                        "input": current_input[:100],
                        "output": response,
                        "status": "success"
                    })
                    
                    # Use response as input for next agent
                    current_input = response
                    logger.info(f"  ✓ {agent_name} completed")
                else:
                    logger.error(f"  ✗ {agent_name} returned empty response")
                    results.append({
                        "agent": agent_name,
                        "status": "failed",
                        "error": "Empty response"
                    })
            
            except Exception as e:
                logger.error(f"  ✗ {agent_name} error: {e}")
                results.append({
                    "agent": agent_name,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "party": party.name,
            "workflow": "sequential",
            "task": task,
            "steps": results,
            "final_output": current_input if results else None,
            "success": len([r for r in results if r.get("status") == "success"])
        }
    
    def execute_parallel(
        self,
        party: Party,
        task: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute party agents in parallel.
        Each agent gets the same task.
        """
        context = context or {}
        logger.info(f"Executing {party.name} (parallel)...")
        
        results = []
        
        # In real implementation, would use threading/asyncio
        # For now, sequential for simplicity
        for agent_name in party.agents:
            logger.info(f"  → {agent_name}")
            agent = self._get_agent(agent_name)
            
            if not agent:
                logger.error(f"  ✗ Failed to get {agent_name}")
                continue
            
            try:
                response = agent.call(task)
                
                if response:
                    results.append({
                        "agent": agent_name,
                        "output": response,
                        "status": "success"
                    })
                    logger.info(f"  ✓ {agent_name} completed")
                else:
                    logger.error(f"  ✗ {agent_name} returned empty response")
                    results.append({
                        "agent": agent_name,
                        "status": "failed",
                        "error": "Empty response"
                    })
            
            except Exception as e:
                logger.error(f"  ✗ {agent_name} error: {e}")
                results.append({
                    "agent": agent_name,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "party": party.name,
            "workflow": "parallel",
            "task": task,
            "perspectives": results,
            "success": len([r for r in results if r.get("status") == "success"])
        }
    
    def execute_iterative(
        self,
        party: Party,
        task: str,
        iterations: int = 3,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute party agents iteratively.
        Refine the task through multiple rounds.
        """
        context = context or {}
        logger.info(f"Executing {party.name} (iterative, {iterations} iterations)...")
        
        current_task = task
        results = []
        
        for i in range(iterations):
            logger.info(f"  Iteration {i+1}/{iterations}")
            iteration_results = []
            
            for agent_name in party.agents:
                agent = self._get_agent(agent_name)
                
                if not agent:
                    continue
                
                try:
                    response = agent.call(current_task)
                    if response:
                        iteration_results.append({
                            "agent": agent_name,
                            "output": response
                        })
                        logger.info(f"    ✓ {agent_name}")
                except Exception as e:
                    logger.error(f"    ✗ {agent_name}: {e}")
            
            results.append(iteration_results)
            
            # Refine task for next iteration
            if iteration_results:
                current_task = f"Refine based on feedback:\n{iteration_results[-1]['output']}"
        
        return {
            "party": party.name,
            "workflow": "iterative",
            "task": task,
            "iterations": results,
            "success": sum(len(r) for r in results if r)
        }
    
    def execute(self, task: str, party_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a task using appropriate party.
        
        Args:
            task: Task description
            party_name: Optional specific party (auto-detect if None)
        
        Returns:
            Execution results
        """
        logger.info(f"=== Executing task ===")
        logger.info(f"Task: {task[:100]}...")
        
        # Find or use specified party
        if party_name is None:
            party_name = self.router.find_party(task)
        
        party = self.router.get_party(party_name)
        if not party:
            logger.error(f"Party not found: {party_name}")
            return {
                "status": "error",
                "error": f"Party not found: {party_name}"
            }
        
        logger.info(f"Using party: {party_name}")
        logger.info(f"Lead: {party.lead}")
        logger.info(f"Agents: {', '.join(party.agents)}")
        logger.info(f"Workflow: {party.workflow}")
        
        # Execute based on workflow type
        if party.workflow == "sequential":
            result = self.execute_sequential(party, task)
        elif party.workflow == "parallel":
            result = self.execute_parallel(party, task)
        elif party.workflow == "iterative":
            result = self.execute_iterative(party, task)
        else:
            result = self.execute_sequential(party, task)  # default
        
        self.results.append(result)
        logger.info(f"=== Task complete ===")
        
        return result
    
    def get_results(self) -> List[Dict[str, Any]]:
        """Get all execution results."""
        return self.results.copy()


if __name__ == "__main__":
    print("Testing Orchestrator with HTTP API...\n")
    
    try:
        orchestrator = Orchestrator()
        
        # List available parties
        print("Available parties:")
        for name, desc in orchestrator.router.list_parties().items():
            print(f"  {name}: {desc}")
        
        # Test with a task
        print("\n\nTesting code review party...")
        result = orchestrator.execute(
            "Review this code for bugs and design issues",
            party_name="code-review"
        )
        
        print(f"\nResult: {json.dumps(result, indent=2)[:500]}...")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print("\nMake sure OpenCode server is running: opencode serve --port 4096")
