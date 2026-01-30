#!/usr/bin/env python3
"""
Agent Personality Manager - Load and manage agent personalities from MD files

This makes agent personalities actually loadable and configurable,
connecting the .md files to the actual agent behavior.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AgentPersonality:
    """Agent personality loaded from markdown file."""

    # Basic info
    role: str
    description: str
    thinking_style: str

    # Behaviors
    behaviors: Dict[str, Any]
    triggers: Dict[str, Any]
    communication_style: Dict[str, str]

    # Model configuration
    default_model: str = "opencode/big-pickle"
    alternative_models: Optional[Dict[str, Any]] = None
    model_selection_criteria: Optional[Dict[str, Any]] = None

    # Model capabilities (based on OpenCode actual models)
    model_capabilities: Optional[Dict[str, Any]] = None

    # Execution preferences
    default_timeout: int = 300
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

    # Skills and capabilities
    skills: Optional[List[str]] = None
    plugins: Optional[Dict[str, Any]] = None
    tools: Optional[List[str]] = None


class PersonalityManager:
    """Load and manage agent personalities from markdown files."""

    def __init__(
        self,
        personalities_dir: str = "/home/bamer/.opencode/emergent-learning/agents",
        opencode_agents_dir: str = "/home/bamer/.config/opencode/agents",
        opencode_precedence: bool = False,
    ):
        self.personalities_dir = Path(personalities_dir)
        self.opencode_agents_dir = Path(opencode_agents_dir)
        self.opencode_precedence = (
            opencode_precedence  # If True, OpenCode agents take precedence
        )
        self.cache: Dict[str, AgentPersonality] = {}

    def load_personality(self, agent_type: str) -> AgentPersonality:
        """Load personality for a specific agent type."""
        if agent_type in self.cache:
            return self.cache[agent_type]

        # Try multiple locations for personality files
        if self.opencode_precedence:
            # OpenCode format takes precedence
            personality_locations = [
                # OpenCode format locations
                self.opencode_agents_dir / f"{agent_type.lower()}.md",
                # ELF format locations
                self.personalities_dir / agent_type.lower() / "personality.md",
                self.personalities_dir / f"{agent_type.lower()}.md",
            ]
        else:
            # ELF format takes precedence (default)
            personality_locations = [
                # ELF format locations
                self.personalities_dir / agent_type.lower() / "personality.md",
                self.personalities_dir / f"{agent_type.lower()}.md",
                # OpenCode format locations
                self.opencode_agents_dir / f"{agent_type.lower()}.md",
            ]

        personality_file = None
        for location in personality_locations:
            if location.exists():
                personality_file = location
                break

        if not personality_file:
            logger.warning(
                f"⚠️ No personality file found for {agent_type}, using default"
            )
            return self._get_default_personality(agent_type)

        try:
            # Parse markdown with YAML frontmatter
            content = personality_file.read_text()

            # Extract YAML frontmatter between --- markers
            yaml_content = {}
            markdown_content = content

            if content.startswith("---"):
                try:
                    parts = content.split("---", 3)
                    if len(parts) >= 3:
                        yaml_content = yaml.safe_load(parts[1]) or {}
                        markdown_content = parts[2].strip()
                except yaml.YAMLError as e:
                    logger.warning(f"⚠️ Failed to parse YAML for {agent_type}: {e}")

            # Handle both ELF format and OpenCode format
            if "model" in yaml_content:
                # OpenCode format
                default_model = yaml_content.get("model", "opencode/big-pickle")
                temperature = yaml_content.get("temperature", 0.7)
                name = yaml_content.get("name", agent_type)
                description = yaml_content.get("description", f"{agent_type} Agent")

                # Convert OpenCode permissions to ELF format if needed
                permissions = yaml_content.get("permissions", {})

                personality = AgentPersonality(
                    role=name,
                    description=description,
                    thinking_style="Professional",  # Default for OpenCode agents
                    behaviors={},  # Will be parsed from markdown content
                    triggers={},  # Will be parsed from markdown content
                    communication_style={
                        "verbosity": "detailed",
                        "formality": "professional",
                    },
                    # Model configuration
                    default_model=default_model,
                    alternative_models={},  # Can be extended later
                    model_selection_criteria={},  # Can be extended later
                    # Execution preferences
                    default_timeout=300,
                    max_tokens=None,
                    temperature=temperature,
                    # Skills and capabilities from OpenCode format
                    skills=yaml_content.get("skills", []),
                    plugins=yaml_content.get("plugins", {}),
                    tools=yaml_content.get("tools", []),
                )
            else:
                # Original ELF format
                personality = AgentPersonality(
                    role=yaml_content.get("Role", f"{agent_type} Agent"),
                    description=markdown_content,
                    thinking_style=yaml_content.get("Thinking Style", "Analytical"),
                    behaviors=yaml_content.get("Behaviors", {}),
                    triggers=yaml_content.get("Triggers", {}),
                    communication_style=yaml_content.get("Communication Style", {}),
                    # Model configuration
                    default_model=yaml_content.get("Model Configuration", {}).get(
                        "default_model", "opencode/big-pickle"
                    ),
                    alternative_models=yaml_content.get("Model Configuration", {}).get(
                        "alternative_models", {}
                    ),
                    model_selection_criteria=yaml_content.get(
                        "Model Configuration", {}
                    ).get("model_selection_criteria", {}),
                    # Execution preferences
                    default_timeout=yaml_content.get("Execution", {}).get(
                        "default_timeout", 300
                    ),
                    max_tokens=yaml_content.get("Execution", {}).get("max_tokens"),
                    temperature=yaml_content.get("Execution", {}).get("temperature"),
                    # Skills and capabilities for ELF format
                    skills=yaml_content.get("Skills", []),
                    plugins=yaml_content.get("Plugins", {}),
                    tools=yaml_content.get("Tools", []),
                )

            self.cache[agent_type] = personality
            logger.info(
                f"✅ Loaded personality for {agent_type}: {personality.default_model}"
            )
            return personality

        except Exception as e:
            logger.error(f"❌ Failed to load personality for {agent_type}: {e}")
            return self._get_default_personality(agent_type)

    def _get_default_personality(self, agent_type: str) -> AgentPersonality:
        """Fallback personality when file not found."""
        defaults = {
            "SENTINEL": AgentPersonality(
                role="Monitoring Agent",
                description="System monitoring and health checks",
                thinking_style="Alert and analytical",
                default_model="opencode/kimi-k2.5-free",
                alternative_models={
                    "fast": "opencode/gpt-5-nano",
                    "balanced": "opencode/gpt-5-mini",
                    "capable": "opencode/kimi-k2.5-free",
                },
                model_selection_criteria={
                    "speed_threshold": "medium",
                    "cost_threshold": "low",
                },
                default_timeout=300,
                skills=[],
                plugins={},
                tools=[],
            ),
            "RESEARCHER": AgentPersonality(
                role="Investigation Agent",
                description="Deep investigation and research",
                thinking_style="Thorough and methodical",
                default_model="opencode/trinity-large-preview-free",
                alternative_models={
                    "fast": "opencode/kimi-k2.5-free",
                    "balanced": "opencode/trinity-large-preview-free",
                    "capable": "opencode/nemotron-v3-coder",
                },
                model_selection_criteria={
                    "complexity_threshold": "high",
                    "cost_threshold": "medium",
                },
                default_timeout=600,
                skills=[],
                plugins={},
                tools=[],
            ),
            "ARCHITECT": AgentPersonality(
                role="Design Agent",
                description="System design and structure planning",
                thinking_style="Structured and systematic",
                default_model="opencode/nemotron-v3-coder",
                alternative_models={
                    "analytical": "opencode/trinity-large-preview-free",
                    "creative": "opencode/kimi-k2.5-free",
                    "balanced": "opencode/nemotron-v3-coder",
                },
                model_selection_criteria={
                    "complexity_threshold": "high",
                    "speed_threshold": "medium",
                },
                default_timeout=450,
                skills=[],
                plugins={},
                tools=[],
            ),
            "SKEPTIC": AgentPersonality(
                role="Critical Analysis Agent",
                description="Critical review and risk assessment",
                thinking_style="Critical and adversarial",
                default_model="opencode/glm-4.7-free",
                alternative_models={
                    "thorough": "opencode/trinity-large-preview-free",
                    "quick": "opencode/gpt-5-nano",
                    "balanced": "opencode/glm-4.7-free",
                },
                model_selection_criteria={
                    "risk_threshold": "high",
                    "cost_threshold": "low",
                },
                default_timeout=400,
                skills=[],
                plugins={},
                tools=[],
            ),
            "CREATIVE": AgentPersonality(
                role="Innovation Agent",
                description="Creative solutions and innovation",
                thinking_style="Divergent and possibility-focused",
                default_model="opencode/kimi-k2.5-free",
                alternative_models={
                    "innovative": "opencode/nemotron-v3-coder",
                    "diverse": "opencode/kimi-k2.5-free",
                    "structured": "opencode/trinity-large-preview-free",
                },
                model_selection_criteria={
                    "diversity_threshold": "high",
                    "creativity_threshold": "high",
                    "cost_threshold": "medium",
                },
                default_timeout=500,
                skills=[],
                plugins={},
                tools=[],
            ),
            "CEO": AgentPersonality(
                role="Executive Decision Agent",
                description="Executive decisions and strategic direction",
                thinking_style="Strategic and decisive",
                default_model="opencode/trinity-large-preview-free",
                alternative_models={
                    "strategic": "opencode/nemotron-v3-coder",
                    "balanced": "opencode/kimi-k2.5-free",
                    "economy": "opencode/glm-4.7-free",
                },
                model_selection_criteria={
                    "decision_complexity": "high",
                    "cost_threshold": "medium",
                    "urgency_threshold": "high",
                },
                default_timeout=600,
                skills=[],
                plugins={},
                tools=[],
            ),
        }

        return defaults.get(
            agent_type,
            AgentPersonality(
                role=f"{agent_type} Agent",
                description="General purpose agent",
                thinking_style="Analytical",
                default_model="opencode/big-pickle",
                skills=[],
                plugins={},
                tools=[],
            ),
        )

    def get_optimal_model(
        self, agent_type: str, prompt: str, override_model: Optional[str] = None
    ) -> str:
        """Get the optimal model for this agent and prompt."""
        personality = self.load_personality(agent_type)

        # Use override if provided
        if override_model:
            logger.info(f"🔄 Using override model for {agent_type}: {override_model}")
            return override_model

        # Check personality model selection criteria
        criteria = personality.model_selection_criteria or {}
        alternatives = personality.alternative_models or {}

        # Analyze prompt for selection
        prompt_length = len(prompt)
        prompt_words = len(prompt.split())

        # Decision logic based on agent type and criteria

        # SENTINEL: Priority on speed and reliability
        if agent_type == "SENTINEL":
            speed_threshold = criteria.get("speed_threshold", "medium")
            cost_threshold = criteria.get("cost_threshold", "low")

            if speed_threshold == "low" and prompt_words < 20:
                if "gpt-5-nano" in alternatives:
                    logger.info(f"⚡ Sentinel: Using ultra-fast model gpt-5-nano")
                    return "opencode/gpt-5-nano"
            if cost_threshold == "low" and prompt_length < 300:
                if "kimi-k2.5-free" in alternatives:
                    logger.info(f"💰 Sentinel: Using cost-effective kimi-k2.5-free")
                    return "opencode/kimi-k2.5-free"

        # RESEARCHER: Priority on capability and thoroughness
        elif agent_type == "RESEARCHER":
            complexity_threshold = criteria.get("complexity_threshold", "high")

            if complexity_threshold == "high" and prompt_length > 800:
                if "nemotron-v3-coder" in alternatives:
                    logger.info(
                        f"🧠 Researcher: Using high-capability nemotron-v3-coder"
                    )
                    return "opencode/nemotron-v3-coder"
            if prompt_length > 500:
                if "trinity-large-preview-free" in alternatives:
                    logger.info(
                        f"📚 Researcher: Using comprehensive trinity-large-preview-free"
                    )
                    return "opencode/trinity-large-preview-free"

        # ARCHITECT: Balance between analytical and creative
        elif agent_type == "ARCHITECT":
            complexity_threshold = criteria.get("complexity_threshold", "high")

            if complexity_threshold == "high" and prompt_words > 50:
                if "nemotron-v3-coder" in alternatives:
                    logger.info(f"🏗️ Architect: Using structured nemotron-v3-coder")
                    return "opencode/nemotron-v3-coder"
            if prompt_length > 300:
                if "trinity-large-preview-free" in alternatives:
                    logger.info(
                        f"🏗️ Architect: Using detailed trinity-large-preview-free"
                    )
                    return "opencode/trinity-large-preview-free"

        # SKEPTIC: Priority on thoroughness and cost-efficiency
        elif agent_type == "SKEPTIC":
            risk_threshold = criteria.get("risk_threshold", "high")
            cost_threshold = criteria.get("cost_threshold", "low")

            if risk_threshold == "high":
                if "trinity-large-preview-free" in alternatives:
                    logger.info(
                        f"❓ Skeptic: Using thorough trinity-large-preview-free"
                    )
                    return "opencode/trinity-large-preview-free"
            if cost_threshold == "low":
                if "glm-4.7-free" in alternatives:
                    logger.info(f"💰 Skeptic: Using cost-effective glm-4.7-free")
                    return "opencode/glm-4.7-free"

        # CREATIVE: Priority on diversity and innovation
        elif agent_type == "CREATIVE":
            diversity_threshold = criteria.get("diversity_threshold", "high")

            if diversity_threshold == "high" and prompt_words > 30:
                if "nemotron-v3-coder" in alternatives:
                    logger.info(f"💡 Creative: Using innovative nemotron-v3-coder")
                    return "opencode/nemotron-v3-coder"
            if prompt_length > 200:
                if "kimi-k2.5-free" in alternatives:
                    logger.info(f"💡 Creative: Using diverse kimi-k2.5-free")
                    return "opencode/kimi-k2.5-free"

        # CEO: Priority on strategic capability and reliability
        elif agent_type == "CEO":
            decision_complexity = criteria.get("decision_complexity", "high")
            urgency_threshold = criteria.get("urgency_threshold", "high")

            if decision_complexity == "high" and prompt_words > 40:
                if "nemotron-v3-coder" in alternatives:
                    logger.info(f"👑 CEO: Using strategic nemotron-v3-coder")
                    return "opencode/nemotron-v3-coder"
            if urgency_threshold == "high":
                if "trinity-large-preview-free" in alternatives:
                    logger.info(f"👑 CEO: Using reliable trinity-large-preview-free")
                    return "opencode/trinity-large-preview-free"

        # Default to personality's default model
        default_model = personality.default_model
        logger.info(f"🎯 Using default model for {agent_type}: {default_model}")
        return default_model

    def get_execution_config(self, agent_type: str, model: str) -> Dict[str, Any]:
        """Get execution configuration for this agent/model combo."""
        personality = self.load_personality(agent_type)

        config = {
            "timeout": personality.default_timeout,
            "max_tokens": personality.max_tokens,
            "temperature": personality.temperature,
        }

        # Model-specific adjustments
        if "haiku" in model.lower():
            config["timeout"] = min(config["timeout"], 300)  # Haiku is fast
        elif "opus" in model.lower():
            config["timeout"] = max(config["timeout"], 600)  # Opus needs more time

        return config

    def get_agent_prompt_prefix(self, agent_type: str) -> str:
        """Get the prompt prefix for this agent based on personality."""
        personality = self.load_personality(agent_type)

        prefixes = {
            "SENTINEL": f"@sentinel\\n\\nYou are {personality.role}. {personality.description}. {personality.thinking_style} thinking style.",
            "RESEARCHER": f"@researcher\\n\\nYou are {personality.role}. {personality.description}. {personality.thinking_style} thinking style.",
            "ARCHITECT": f"@architect\\n\\nYou are {personality.role}. {personality.description}. {personality.thinking_style} thinking style.",
            "SKEPTIC": f"@skeptic\\n\\nYou are {personality.role}. {personality.description}. {personality.thinking_style} thinking style.",
            "CREATIVE": f"@creative\\n\\nYou are {personality.role}. {personality.description}. {personality.thinking_style} thinking style.",
            "CEO": f"@general\\n\\nYou are {personality.role}. {personality.description}. {personality.thinking_style} thinking style.",
        }

        return prefixes.get(
            agent_type, f"@{agent_type.lower()}\\n\\nYou are {personality.role}."
        )

    def list_available_models(self, agent_type: str) -> Dict[str, str]:
        """List all available models for this agent."""
        personality = self.load_personality(agent_type)
        models = {
            "default": personality.default_model,
        }

        # Add alternatives with descriptions
        for name, description in (personality.alternative_models or {}).items():
            models[name] = self._get_model_description(name)

        return models

    def _get_model_description(self, model_name: str) -> str:
        """Get description for a specific model."""
        descriptions = {
            # OpenCode models (user's actual available models)
            "opencode/big-pickle": "Primary orchestrator model - Balanced capability",
            "opencode/kimi-k2.5-free": "Fast, versatile model for quick responses",
            "opencode/trinity-large-preview-free": "High-capability model for complex analysis",
            "opencode/nemotron-v3-coder": "Specialized coding and reasoning model",
            "opencode/glm-4.7-free": "Cost-effective model for routine tasks",
            "opencode/minimax-m2.1-free": "Balanced performance and cost",
            "opencode/gpt-5-nano": "Ultra-fast model for simple queries",
            "opencode/gpt-5-mini": "Fast model for moderate complexity",
            # User specified preference models
            "fast": "Optimized for speed and low latency",
            "balanced": "Balanced between capability and cost",
            "capable": "High capability for complex tasks",
            "strategic": "Optimized for strategic decision-making",
            "thorough": "Optimized for deep analysis",
            "quick": "Ultra-fast responses for routine queries",
            "economy": "Cost-optimized for high-volume usage",
            "innovative": "Creative and diverse thinking patterns",
            "diverse": "Multiple perspective generation",
            "structured": "Systematic and organized output",
            "analytical": "Detailed analytical processing",
            "creative": "Innovative solution generation",
        }

        return descriptions.get(model_name, f"Model: {model_name}")

    def get_all_available_opencode_models(self) -> Dict[str, str]:
        """Get all actual OpenCode models from the user's list."""
        return {
            "opencode/big-pickle": "Primary orchestrator model - Balanced capability",
            "opencode/kimi-k2.5-free": "Fast, versatile model for quick responses",
            "opencode/minimax-m2.1-free": "Balanced performance and cost",
            "opencode/glm-4.7-free": "Cost-effective model for routine tasks",
            "opencode/trinity-large-preview-free": "High-capability model for complex analysis",
            "opencode/nemotron-v3-coder": "Specialized coding and reasoning model",
            "opencode/gpt-5-nano": "Ultra-fast model for simple queries",
            "opencode/gpt-5-mini": "Fast model for moderate complexity",
        }


# Global personality manager instance
personality_manager = PersonalityManager()
