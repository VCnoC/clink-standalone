"""CLI agents for executing external AI CLIs."""

from __future__ import annotations

from .base import BaseCLIAgent, AgentOutput, CLIAgentError
from .gemini import GeminiAgent
from .codex import CodexAgent
from .claude import ClaudeAgent

from ..models import ResolvedCLIClient

AGENTS: dict[str, type[BaseCLIAgent]] = {
    "gemini": GeminiAgent,
    "codex": CodexAgent,
    "claude": ClaudeAgent,
}


def create_agent(client: ResolvedCLIClient) -> BaseCLIAgent:
    """Create an agent instance for the given CLI client.

    Uses CLI-specific agent if available, otherwise falls back to base agent.
    """
    agent_class = AGENTS.get(client.name.lower(), BaseCLIAgent)
    return agent_class(client)


__all__ = [
    "BaseCLIAgent",
    "AgentOutput",
    "CLIAgentError",
    "GeminiAgent",
    "CodexAgent",
    "ClaudeAgent",
    "create_agent",
    "AGENTS",
]
