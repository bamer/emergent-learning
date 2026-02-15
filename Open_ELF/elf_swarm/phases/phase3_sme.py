"""
Phase 3: Consult SMEs (Subject Matter Experts)
"""

from typing import List


def consult_smes(orchestrator, plan: dict) -> None:
    """
    Phase 3: Consult subject matter experts.

    Uses research agents to get domain expert guidance.
    """
    from datetime import datetime

    print("\n🔍 Phase 3: Consult SMEs")

    domains = _identify_domains(orchestrator.task, plan)
    guidance = {}

    for domain in domains:
        print(f"  Consulting {domain} SME...")

        result = orchestrator.ask_agent(
            "researcher",
            f"""
Domain: {domain}
Task: {orchestrator.task}

Provide expert guidance on:
- Best practices in this domain
- Common patterns and anti-patterns
- Key considerations and pitfalls
- Recommended tools and libraries

Report as ## GUIDANCE for domain: {domain}
""",
        )

        guidance[domain] = result.get("response", "")

    # Save to context
    context = orchestrator.swarm_manager.load_context()
    context["sme_guidance"] = guidance
    context["sme_consulted_at"] = datetime.now().isoformat()
    orchestrator.swarm_manager.save_context(context)

    # Append to markdown context
    context_file = orchestrator.swarm_manager.swarm_dir / "context.md"
    with open(context_file, "a") as f:
        f.write(f"\n## SME Consultation\n")
        for domain, content in guidance.items():
            f.write(f"\n### {domain}\n{content}\n")

    plan["sme_consulted"] = True
    plan["sme_guidance"] = guidance
    print("✓ SME consultation complete")


def _identify_domains(task: str, plan: dict) -> List[str]:
    """Identify domains relevant to the task."""
    domain_keywords = {
        "security": ["auth", "jwt", "login", "password", "token", "encryption"],
        "api": ["rest", "graphql", "endpoint", "api", "route"],
        "database": ["sql", "schema", "migration", "query", "database"],
        "frontend": ["ui", "component", "view", "react", "vue", "angular"],
        "backend": ["service", "controller", "server", "logic"],
        "performance": ["optimize", "cache", "fast", "slow"],
        "testing": ["test", "spec", "coverage", "mock"],
    }

    task_lower = task.lower()
    domains = []

    for domain, keywords in domain_keywords.items():
        if any(keyword in task_lower for keyword in keywords):
            domains.append(domain)

    # Default domains if none identified
    if not domains:
        domains = ["backend", "api"]

    return domains
