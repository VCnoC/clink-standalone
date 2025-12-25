"""Claude-specific CLI agent hooks."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..parsers import ParserError
from .base import AgentOutput, BaseCLIAgent

if TYPE_CHECKING:
    from ..models import ResolvedCLIRole


class ClaudeAgent(BaseCLIAgent):
    """Claude CLI agent with system-prompt injection support."""

    def _build_command(self, *, role: "ResolvedCLIRole", system_prompt: str | None) -> list[str]:
        """Build command with optional system prompt injection."""
        command = list(self.client.executable)
        command.extend(self.client.base_args)

        # Inject system prompt if provided and not already in config
        if system_prompt and "--append-system-prompt" not in self.client.base_args:
            command.extend(["--append-system-prompt", system_prompt])

        command.extend(role.role_args)
        return command

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
        """Try to parse output even on non-zero exit."""
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
