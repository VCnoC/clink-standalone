"""Clink Core - Standalone CLI bridge without MCP dependencies.

This module provides a standalone version of clink that can launch external AI CLIs
(gemini, codex, claude) without requiring an MCP server.
"""

from .models import (
    CLIClientConfig,
    CLIRoleConfig,
    CLIResult,
    OutputToFileConfig,
    ResolvedCLIClient,
    ResolvedCLIRole,
)
from .registry import ClinkRegistry, get_registry
from .runner import run_cli
from .session import SessionManager, get_session_manager
from .agents import create_agent, BaseCLIAgent, CLIAgentError
from .parsers import get_parser, BaseParser, ParsedCLIResponse, ParserError

__all__ = [
    # Models
    "CLIClientConfig",
    "CLIRoleConfig",
    "CLIResult",
    "OutputToFileConfig",
    "ResolvedCLIClient",
    "ResolvedCLIRole",
    # Registry
    "ClinkRegistry",
    "get_registry",
    # Runner
    "run_cli",
    # Session
    "SessionManager",
    "get_session_manager",
    # Agents
    "create_agent",
    "BaseCLIAgent",
    "CLIAgentError",
    # Parsers
    "get_parser",
    "BaseParser",
    "ParsedCLIResponse",
    "ParserError",
]
