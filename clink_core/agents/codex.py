"""Codex-specific CLI agent hooks."""

from __future__ import annotations

from ..parsers import ParserError
from .base import AgentOutput, BaseCLIAgent


class CodexAgent(BaseCLIAgent):
    """Codex CLI agent with error recovery."""

    def _recover_from_error(
        self,
        *,
        returncode: int,
        stdout: str,
        stderr: str,
        sanitized_command: list[str],
        duration_seconds: float,
        output_file_content: str | None,
    ) -> AgentOutput | None:
        """Try to parse output even on non-zero exit (Codex may still have useful content)."""
        try:
            parsed = self._parser.parse(stdout, stderr)
        except ParserError:
            return None

        return AgentOutput(
            parsed=parsed,
            sanitized_command=sanitized_command,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration_seconds,
            parser_name=self._parser.name,
            output_file_content=output_file_content,
        )
