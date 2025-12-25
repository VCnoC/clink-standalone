"""Base parser interface for CLI output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ParserError(RuntimeError):
    """Raised when CLI output cannot be parsed."""
    pass


@dataclass
class ParsedCLIResponse:
    """Structured response from parsing CLI output."""

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseParser:
    """Base class for CLI output parsers."""

    name: str = "base"

    def parse(self, stdout: str, stderr: str) -> ParsedCLIResponse:
        """Parse CLI output and return structured response.

        Args:
            stdout: Standard output from CLI
            stderr: Standard error from CLI

        Returns:
            ParsedCLIResponse with content and metadata

        Raises:
            ParserError: If output cannot be parsed
        """
        raise NotImplementedError("Subclasses must implement parse()")
