"""Output parsers for CLI responses."""

from __future__ import annotations

from .base import BaseParser, ParsedCLIResponse, ParserError
from .gemini import GeminiJSONParser
from .codex import CodexJSONLParser
from .claude import ClaudeJSONParser
from .passthrough import PassthroughParser

PARSERS: dict[str, type[BaseParser]] = {
    "gemini_json": GeminiJSONParser,
    "codex_jsonl": CodexJSONLParser,
    "claude_json": ClaudeJSONParser,
    "passthrough": PassthroughParser,
}


def get_parser(name: str) -> BaseParser:
    """Get a parser instance by name."""
    parser_class = PARSERS.get(name)
    if parser_class is None:
        available = ", ".join(sorted(PARSERS.keys()))
        raise ValueError(f"Unknown parser '{name}'. Available: {available}")
    return parser_class()


__all__ = [
    "BaseParser",
    "ParsedCLIResponse",
    "ParserError",
    "GeminiJSONParser",
    "CodexJSONLParser",
    "ClaudeJSONParser",
    "PassthroughParser",
    "get_parser",
    "PARSERS",
]
