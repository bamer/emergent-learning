#!/usr/bin/env python3
"""
Swarm Coordinator - Multi-Agent Orchestration System

Coordinates multiple specialized agents for complex tasks with parallel execution,
dependency management, and result aggregation.
"""

import json
import os
import sys
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class SwarmCoordinator:
    """Multi-agent swarm coordination system."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.coordination_dir = base_path / ".coordination" / "swarm"
        self.coordination_dir.mkdir(parents=True, exist_ok=True)

        # Agent definitions based on elf-swarm skill
        self.agent_catalog = {
            # Code Quality
            "code-reviewer": "Expert code analysis and review",
            "debugger": "System debugging and issue resolution",
            "test-automator": "Automated testing and quality assurance",
            # Architecture
            "architect-review": "System architecture analysis",
            "backend-architect": "Backend system design",
            "database-architect": "Database design and optimization",
            # Security
            "security-auditor": "Security vulnerability assessment",
            "backend-security-coder": "Backend security implementation",
            # Language-Specific
            "python-pro": "Python development specialist",
            "fastapi-pro": "FastAPI framework expert",
            "typescript-pro": "TypeScript/JavaScript specialist",
            "frontend-developer": "Frontend development expert",
            # Database
            "database-optimizer": "Database performance optimization",
            "sql-pro": "SQL expert",
            # Documentation
            "docs-architect": "Documentation system design",
            "tutorial-engineer": "Tutorial and guide creation",
            # Performance
            "performance-engineer": "Performance optimization",
            # Shell/Scripts
            "bash-pro": "Shell scripting expert",
        }

    def detect_domains(self, target_path: str) -> List[str]:
        """Detect technology domains from target."""
        domains = []
        path = Path(target_path)

        # Check file extensions
        if path.suffix in [".py"]:
            domains.extend(["python", "code-quality"])
        elif path.suffix in [".ts", ".tsx", ".js", ".jsx"]:
            domains.extend(["typescript", "frontend", "code-quality"])
        elif path.suffix in [".sql"]:
            domains.extend(["database", "sql"])
        elif path.suffix in [".sh", ".bash"]:
            domains.extend(["shell", "scripts"])

        # Check directory structure
        if any((path / "src").exists() for p in [path] if path.exists()):
            domains.append("architecture")
        if any((path / "test").exists() for p in [path] if path.exists()):
            domains.append("testing")
        if any((path / "docs").exists() for p in [path] if path.exists()):
            domains.append("documentation")

        return domains or ["general"]

    def select_agents(self, domains: List[str], mode: str) -> List[str]:
        """Select appropriate agents based on domains and mode."""
        agent_counts = {
            "ultrathink": {"low": 1, "high": 3},
            "focused": {"low": 1, "high": 2},
            "quick": {"low": 1, "high": 1},
        }

        max_agents = agent_counts.get(mode, {}).get("high", 2)
        selected_agents = []

        # Domain mapping
        domain_agents = {
            "python": ["python-pro", "debugger", "test-automator"],
            "typescript": ["typescript-pro", "frontend-developer"],
            "frontend": ["frontend-developer", "test-automator"],
            "database": ["database-architect", "database-optimizer", "sql-pro"],
            "architecture": ["architect-review", "backend-architect"],
            "security": ["security-auditor", "backend-security-coder"],
            "testing": ["test-automator", "code-reviewer"],
            "documentation": ["docs-architect", "tutorial-engineer"],
            "performance": ["performance-engineer", "database-optimizer"],
            "shell": ["bash-pro", "code-reviewer"],
            "scripts": ["bash-pro"],
            "code-quality": ["code-reviewer", "debugger"],
        }

        # Collect agents from domains
        domain_agents_selected = []
        for domain in domains:
            agents = domain_agents.get(domain, [])
            domain_agents_selected.extend(agents)

        # Select agents up to limit
        for agent in domain_agents_selected:
            if agent in self.agent_catalog and len(selected_agents) < max_agents:
                selected_agents.append(agent)

        # Ensure minimum coverage
        if not selected_agents:
            selected_agents = ["code-reviewer", "debugger"][:max_agents]

        return selected_agents[:max_agents]

    def create_agent_prompt(
        self, agent_type: str, target_path: str, context: str = ""
    ) -> str:
        """Create specialized prompt for each agent type."""
        base_context = f"Analyze and work on: {target_path}"
        if context:
            base_context += f"\n\nContext: {context}"

        agent_prompts = {
            "code-reviewer": f"""{base_context}

**Your Role:** Expert Code Reviewer
**Focus on:**
- Code quality and readability
- Security vulnerabilities  
- Performance issues
- Best practices compliance
- Potential bugs or edge cases

**Report findings with:**
- File:line references
- Issue severity (critical/high/medium/low)
- Recommended fixes
- Code quality metrics""",
            "debugger": f"""{base_context}

**Your Role:** System Debugger
**Focus on:**
- Runtime errors and exceptions
- Logic flow issues
- Configuration problems
- Environment setup issues
- Performance bottlenecks

**Report findings with:**
- Root cause analysis
- Debugging steps taken
- Solution recommendations
- Prevention strategies""",
            "python-pro": f"""{base_context}

**Your Role:** Python Development Expert
**Focus on:**
- Python-specific patterns and idioms
- Standard library usage
- Python ecosystem integration
- Performance optimizations
- Type hints and documentation

**Provide recommendations for:**
- Code structure improvements
- Modern Python features
- Dependency management
- Testing strategies""",
            "frontend-developer": f"""{base_context}

**Your Role:** Frontend Development Expert
**Focus on:**
- User interface design
- Client-side performance
- Accessibility compliance
- Browser compatibility
- Responsive design

**Analyze and improve:**
- Component architecture
- State management
- Build optimization
- Code splitting strategies""",
        }

        return agent_prompts.get(
            agent_type,
            f"""{base_context}

**Your Role:** {self.agent_catalog.get(agent_type, "Specialist Agent")}
**Focus on your domain expertise:**
- Domain-specific best practices
- Optimization opportunities
- Quality improvements
- Integration considerations

**Provide actionable recommendations with file:line references.**""",
        )

    def launch_agent(
        self, agent_type: str, prompt: str, output_file: str
    ) -> Dict[str, Any]:
        """Launch individual agent via Task tool."""
        try:
            # Create coordination file
            agent_input = {
                "agent_type": agent_type,
                "prompt": prompt,
                "target": Path.cwd().name,
                "timestamp": datetime.now().isoformat(),
            }

            agent_file = self.coordination_dir / f"{agent_type}_input.json"
            with open(agent_file, "w") as f:
                json.dump(agent_input, f, indent=2)

            # Note: In real implementation, this would use Task tool
            # For now, create a placeholder that shows the intended structure
            print(f"[SWARM] Launching agent: {agent_type}")
            print(f"[SWARM] Agent prompt: {prompt[:100]}...")

            # Simulate agent execution
            result = {
                "agent_type": agent_type,
                "status": "launched",
                "output_file": output_file,
                "input_file": str(agent_file),
                "timestamp": datetime.now().isoformat(),
            }

            return result

        except Exception as e:
            print(f"[SWARM ERROR] Failed to launch agent {agent_type}: {e}")
            return {"agent_type": agent_type, "status": "error", "error": str(e)}

    def aggregate_results(self, agent_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results from all agents."""
        successful_agents = [r for r in agent_results if r.get("status") == "launched"]
        failed_agents = [r for r in agent_results if r.get("status") != "launched"]

        # Group findings by category
        findings_by_severity = {"critical": [], "high": [], "medium": [], "low": []}
        recommendations = []

        # Process successful agents
        for result in successful_agents:
            agent_type = result.get("agent_type", "unknown")
            recommendations.append(f"- {agent_type}: Analysis completed")

        # Process failed agents
        for result in failed_agents:
            agent_type = result.get("agent_type", "unknown")
            error = result.get("error", "Unknown error")
            recommendations.append(f"- {agent_type}: Failed - {error}")

        return {
            "summary": {
                "total_agents": len(agent_results),
                "successful": len(successful_agents),
                "failed": len(failed_agents),
                "timestamp": datetime.now().isoformat(),
            },
            "findings_by_severity": findings_by_severity,
            "recommendations": recommendations,
            "agent_results": agent_results,
        }

    def execute_swarm(
        self, target: str, mode: str = "focused", context: str = ""
    ) -> Dict[str, Any]:
        """Execute swarm coordination."""
        print(f"🦀 SWARM COORDINATION - {mode.upper()} MODE")
        print(f"Target: {target}")
        print(f"Context: {context or 'None'}")
        print("=" * 60)

        # Step 1: Detect domains
        domains = self.detect_domains(target)
        print(f"Detected domains: {domains}")

        # Step 2: Select agents
        selected_agents = self.select_agents(domains, mode)
        print(f"Selected agents ({len(selected_agents)}): {', '.join(selected_agents)}")

        # Step 3: Launch agents in parallel
        agent_results = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for i, agent_type in enumerate(selected_agents):
            output_file = (
                self.coordination_dir / f"{agent_type}_result_{timestamp}.json"
            )
            prompt = self.create_agent_prompt(agent_type, target, context)
            result = self.launch_agent(agent_type, prompt, str(output_file))
            agent_results.append(result)

            # Add output file reference
            result["output_file"] = str(output_file)

        # Step 4: Aggregate results
        summary = self.aggregate_results(agent_results)

        # Step 5: Write summary
        summary_file = self.coordination_dir / f"swarm_summary_{timestamp}.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        print("\n" + "=" * 60)
        print("SWARM EXECUTION COMPLETE")
        print(
            f"Summary: {summary['summary']['successful']}/{summary['summary']['total_agents']} agents successful"
        )
        print(f"Results saved to: {summary_file}")

        return summary


def main():
    """CLI interface for swarm coordination."""
    if len(sys.argv) < 2:
        print(
            "Usage: python swarm_coordinator.py <target> [--mode ultrathink|focused|quick] [--context 'context']"
        )
        sys.exit(1)

    target = sys.argv[1]
    mode = "focused"
    context = ""

    # Parse arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--mode" and i + 1 < len(sys.argv):
            mode = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--context" and i + 1 < len(sys.argv):
            context = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    # Validate mode
    if mode not in ["ultrathink", "focused", "quick"]:
        print(f"Invalid mode: {mode}. Use: ultrathink, focused, quick")
        sys.exit(1)

    # Initialize swarm coordinator
    base_path = Path.home() / ".opencode" / "emergent-learning"
    if not base_path.exists():
        base_path = Path.cwd()

    coordinator = SwarmCoordinator(base_path)

    # Execute swarm
    try:
        result = coordinator.execute_swarm(target, mode, context)
        print(json.dumps(result, indent=2))
    except KeyboardInterrupt:
        print("\nSwarm execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Swarm execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
