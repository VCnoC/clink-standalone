"""Passthrough parser - returns output as-is."""

from __future__ import annotations

from .base import BaseParser, ParsedCLIResponse


class PassthroughParser(BaseParser):
    """Simple passthrough parser that returns raw output."""

    @property
    def name(self) -> str:
        return "passthrough"

    def parse(self, stdout: str, stderr: str) -> ParsedCLIResponse:
        """Return stdout as content, or stderr if stdout is empty."""
        content = stdout.strip() or stderr.strip()
        if not content:
            content = "(No output)"
        return ParsedCLIResponse(content=content, metadata={"raw": True})
