#!/usr/bin/env python3
"""
Base Agent Class - HTTP API Integration

All agents inherit from BaseAgent to use OpenCode HTTP API on port 4096.
Handles:
- Session creation/cleanup
- Model configuration
- Message routing
- Error handling
- Logging
"""

import json
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable
from abc import ABC, abstractmethod
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"
)


class BaseAgent(ABC):
    """Base class for all OpenCode-powered agents."""
    
    def __init__(
        self,
        name: str,
        role: str = "assistant",
        server_url: str = "http://localhost:4096",
        model: str = "z-ai/glm4.7",
        provider: str = "nvidia",
        timeout: int = 30000,
    ):
        """
        Initialize agent with HTTP API configuration.
        
        Args:
            name: Agent name (e.g., "Researcher", "Architect")
            role: Agent role description
            server_url: OpenCode server URL (default: http://localhost:4096)
            model: Model ID (default: z-ai/glm4.7)
            provider: Provider ID (default: nvidia)
            timeout: Request timeout in seconds
        """ 
        self.name = name
        self.role = role
        self.server_url = server_url
        self.model = model
        self.provider = provider
        self.timeout = timeout
        self.logger = logging.getLogger(name)
        self.conversation_history = []
        
        # Verify server is accessible
        self._verify_server()
    
    def _verify_server(self) -> bool:
        """Verify OpenCode server is accessible."""
        try:
            resp = requests.get(
                f"{self.server_url}/",
                timeout=5
            )
            if resp.status_code == 200:
                self.logger.info(f"✓ Connected to OpenCode server at {self.server_url}")
                return True
        except requests.exceptions.ConnectionError:
            self.logger.error(f"✗ Cannot connect to OpenCode server at {self.server_url}")
            self.logger.error(f"  Start server with: opencode serve --port 4096")
        except Exception as e:
            self.logger.error(f"✗ Server verification failed: {e}")
        
        return False
    
    @property
    def system_prompt(self) -> str:
        """Override in subclass to provide agent-specific system prompt."""
        return f"You are {self.name}, a {self.role}. Help the user with expert guidance."
    
    def _create_session(self) -> Optional[str]:
        """Create a new OpenCode session."""
        try:
            resp = requests.post(
                f"{self.server_url}/session",
                json={"title": self.name.lower()},
                timeout=10
            )
            
            if resp.status_code in (200, 201):
                data = resp.json()
                session_id = data.get("id")
                if session_id:
                    self.logger.debug(f"Session created: {session_id}")
                    return session_id
            else:
                self.logger.error(f"Failed to create session: {resp.status_code}")
        except Exception as e:
            self.logger.error(f"Session creation error: {e}")
        
        return None
    
    def _send_message(
        self,
        session_id: str,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Tuple[Optional[str], bool]:
        """Send message to OpenCode and get response."""
        try:
            # Build message with system prompt
            full_prompt = prompt
            if system_prompt or self.system_prompt:
                full_prompt = f"{system_prompt or self.system_prompt}\n\n{prompt}"
            
            resp = requests.post(
                f"{self.server_url}/session/{session_id}/message",
                json={
                    "model": {
                    "provider": self.provider,
                        "providerID": self.provider,
                        "modelID": self.model
                    },
                    "parts": [{"type": "text", "text": full_prompt}]
                    },
                timeout=self.timeout
            )
            
            if resp.status_code == 200:
                data = resp.json()
                parts = data.get("parts", [])
                response = ""
                for part in parts:
                    if part.get("type") == "text":
                        response += part.get("text", "")
                
                if response:
                    self.logger.debug(f"Got response ({len(response)} chars)")
                    return response.strip(), True
                else:
                    self.logger.warning("Empty response from server")
                    return None, False
            else:
                self.logger.error(f"Message failed: {resp.status_code}")
                if resp.text:
                    self.logger.error(f"  Details: {resp.text[:200]}")
                return None, False
                
        except requests.exceptions.Timeout:
            self.logger.error(f"Request timeout after {self.timeout}s")
        except Exception as e:
            self.logger.error(f"Message send error: {e}")
        
        return None, False
    
    def _cleanup_session(self, session_id: str) -> bool:
        """Delete session after use."""
        try:
            resp = requests.delete(
                f"{self.server_url}/session/{session_id}",
                timeout=5
            )
            if resp.status_code in (200, 204):
                self.logger.debug(f"Session cleaned up: {session_id}")
                return True
        except Exception as e:
            self.logger.debug(f"Cleanup warning (non-critical): {e}")
        
        return False
    
    def call(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """
        Call the agent with a prompt and get response.
        
        Args:
            prompt: User prompt
            system_prompt: Optional custom system prompt (overrides agent's)
        
        Returns:
            Response text or None if failed
        """
        session_id = self._create_session()
        if not session_id:
            self.logger.error("Cannot proceed without session")
            return None
        
        try:
            response, success = self._send_message(
                session_id,
                prompt,
                system_prompt
            )
            
            if success:
                # Store in conversation history
                self.conversation_history.append({
                    "role": "user",
                    "content": prompt
                })
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })
            
            return response if success else None
            
        finally:
            self._cleanup_session(session_id)
    
    def call_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        on_chunk: Optional[Callable[..., Any]] = None
    ) -> Optional[str]:
        """
        Call with streaming (if server supports it).
        Falls back to regular call if streaming unavailable.
        
        Args:
            prompt: User prompt
            system_prompt: Optional custom system prompt
            on_chunk: Callback for each chunk (not used yet)
        
        Returns:
            Full response text
        """
        # For now, just use regular call
        # Can be extended when OpenCode supports streaming
        return self.call(prompt, system_prompt)
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return self.conversation_history.copy()
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    @abstractmethod
    def analyze(self, task: str) -> Dict[str, Any]:
        """
        Analyze a task (implement in subclass).
        
        Args:
            task: Task description
        
        Returns:
            Analysis results as dict
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, role={self.role})"


class ResearcherAgent(BaseAgent):
    """Agent specialized in research and investigation."""
    
    def __init__(self, **kwargs):
        super().__init__(name="Researcher", role="research specialist", **kwargs)
    
    @property
    def system_prompt(self) -> str:
        return """You are the Researcher Agent - an expert at investigating topics, finding information,
and understanding complex domains. Your approach:
- Ask clarifying questions
- Research thoroughly
- Consider multiple perspectives
- Cite sources when possible
- Provide comprehensive background

Help investigate and understand the user's research question."""
    
    def analyze(self, task: str) -> Dict[str, Any]:
        """Analyze research task."""
        response = self.call(f"Research the following:\n{task}")
        return {
            "agent": "researcher",
            "task": task,
            "findings": response,
            "status": "success" if response else "failed"
        }


class ArchitectAgent(BaseAgent):
    """Agent specialized in architecture and design."""
    
    def __init__(self, **kwargs):
        super().__init__(name="Architect", role="systems architect", **kwargs)
    
    @property
    def system_prompt(self) -> str:
        return """You are the Architect Agent - an expert at system design and architecture.
Your approach:
- Evaluate system requirements
- Design scalable solutions
- Consider trade-offs
- Propose clear architectures
- Think about maintainability

Help design and architect systems."""
    
    def analyze(self, task: str) -> Dict[str, Any]:
        """Analyze architecture task."""
        response = self.call(f"Design an architecture for:\n{task}")
        return {
            "agent": "architect",
            "task": task,
            "design": response,
            "status": "success" if response else "failed"
        }


class SkepticAgent(BaseAgent):
    """Agent specialized in critical review."""
    
    def __init__(self, **kwargs):
        super().__init__(name="Skeptic", role="critical reviewer", **kwargs)
    
    @property
    def system_prompt(self) -> str:
        return """You are the Skeptic Agent - an expert at finding flaws, edge cases, and vulnerabilities.
Your approach:
- Question assumptions
- Find edge cases
- Identify risks
- Suggest improvements
- Challenge proposals constructively

Review and critique the user's work."""
    
    def analyze(self, task: str) -> Dict[str, Any]:
        """Analyze and critique task."""
        response = self.call(f"Critically review and identify issues with:\n{task}")
        return {
            "agent": "skeptic",
            "task": task,
            "critique": response,
            "status": "success" if response else "failed"
        }


class CreativeAgent(BaseAgent):
    """Agent specialized in creative thinking."""
    
    def __init__(self, **kwargs):
        super().__init__(name="Creative", role="creative specialist", **kwargs)
    
    @property
    def system_prompt(self) -> str:
        return """You are the Creative Agent - an expert at generating ideas and thinking outside the box.
Your approach:
- Generate multiple ideas
- Think unconventionally
- Explore possibilities
- Make novel connections
- Inspire with creative solutions

Help brainstorm creative solutions."""
    
    def analyze(self, task: str) -> Dict[str, Any]:
        """Analyze creative task."""
        response = self.call(f"Generate creative ideas for:\n{task}")
        return {
            "agent": "creative",
            "task": task,
            "ideas": response,
            "status": "success" if response else "failed"
        }


# Convenience function for quick access
def get_agent(agent_type: str, **kwargs) -> BaseAgent:
    """Get an agent instance by type."""
    agents = {
        "researcher": ResearcherAgent,
        "architect": ArchitectAgent,
        "skeptic": SkepticAgent,
        "creative": CreativeAgent,
    }
    
    agent_class = agents.get(agent_type.lower())
    if not agent_class:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    return agent_class(**kwargs)


if __name__ == "__main__":
    # Quick test
    print("Testing BaseAgent with HTTP API...")
    
    try:
        researcher = ResearcherAgent()
        print(f"\n{researcher}")
        
        result = researcher.analyze("What is machine learning?")
        print(f"\nResult: {json.dumps(result, indent=2)[:500]}...")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure OpenCode server is running: opencode serve --port 4096")
