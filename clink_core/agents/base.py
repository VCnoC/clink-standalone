"""Base CLI agent for executing external AI CLIs."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ..parsers import get_parser, BaseParser, ParsedCLIResponse, ParserError

if TYPE_CHECKING:
    from ..models import ResolvedCLIClient, ResolvedCLIRole

logger = logging.getLogger("clink.agent")

DEFAULT_STREAM_LIMIT = 10 * 1024 * 1024  # 10MB per stream


@dataclass
class AgentOutput:
    """Container returned by CLI agents after successful execution."""

    parsed: ParsedCLIResponse
    sanitized_command: list[str]
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    parser_name: str
    output_file_content: str | None = None


class CLIAgentError(RuntimeError):
    """Raised when a CLI agent fails (non-zero exit, timeout, parse errors)."""

    def __init__(
        self,
        message: str,
        *,
        returncode: int | None = None,
        stdout: str = "",
        stderr: str = "",
    ) -> None:
        super().__init__(message)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class BaseCLIAgent:
    """Execute a configured CLI command and parse its output."""

    def __init__(self, client: "ResolvedCLIClient"):
        self.client = client
        self._parser: BaseParser = get_parser(client.parser)
        self._logger = logging.getLogger(f"clink.agent.{client.name}")

    async def run(
        self,
        *,
        role: "ResolvedCLIRole",
        prompt: str,
        system_prompt: str | None = None,
        files: list[str] | None = None,
        images: list[str] | None = None,
    ) -> AgentOutput:
        """Execute the CLI and return parsed output."""
        files = files or []
        images = images or []

        command = self._build_command(role=role, system_prompt=system_prompt)
        env = self._build_environment()

        # Resolve executable path
        executable_name = command[0]
        resolved_executable = shutil.which(executable_name)
        if resolved_executable is None:
            raise CLIAgentError(
                f"Executable '{executable_name}' not found in PATH for CLI '{self.client.name}'. "
                f"Ensure the command is installed and accessible."
            )
        command[0] = resolved_executable

        sanitized_command = list(command)
        cwd = str(self.client.working_dir) if self.client.working_dir else None
        limit = DEFAULT_STREAM_LIMIT

        stdout_text = ""
        stderr_text = ""
        output_file_content: str | None = None
        start_time = time.monotonic()

        # Handle output_to_file mode
        output_file_path: Path | None = None
        command_with_output_flag = list(command)

        if self.client.output_to_file:
            fd, tmp_path = tempfile.mkstemp(prefix="clink-", suffix=".json")
            os.close(fd)
            output_file_path = Path(tmp_path)
            flag_template = self.client.output_to_file.flag_template
            try:
                rendered_flag = flag_template.format(path=str(output_file_path))
            except KeyError as exc:
                raise CLIAgentError(f"Invalid output flag template '{flag_template}': missing placeholder {exc}")
            command_with_output_flag.extend(rendered_flag.split())
            sanitized_command = list(command_with_output_flag)

        self._logger.debug("Executing CLI command: %s", " ".join(sanitized_command))
        if cwd:
            self._logger.debug("Working directory: %s", cwd)

        try:
            process = await asyncio.create_subprocess_exec(
                *command_with_output_flag,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                limit=limit,
                env=env,
            )
        except FileNotFoundError as exc:
            raise CLIAgentError(f"Executable not found for CLI '{self.client.name}': {exc}") from exc

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(prompt.encode("utf-8")),
                timeout=self.client.timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            process.kill()
            await process.communicate()
            raise CLIAgentError(
                f"CLI '{self.client.name}' timed out after {self.client.timeout_seconds} seconds",
                returncode=None,
            ) from exc

        duration = time.monotonic() - start_time
        return_code = process.returncode or 0
        stdout_text = stdout_bytes.decode("utf-8", errors="replace")
        stderr_text = stderr_bytes.decode("utf-8", errors="replace")

        # Read output file if used
        if output_file_path and output_file_path.exists():
            output_file_content = output_file_path.read_text(encoding="utf-8", errors="replace")
            if self.client.output_to_file and self.client.output_to_file.cleanup:
                try:
                    output_file_path.unlink()
                except OSError:
                    pass

            # Use file content as stdout if stdout is empty
            if output_file_content and not stdout_text.strip():
                stdout_text = output_file_content

        # Try error recovery for non-zero exit
        if return_code != 0:
            recovered = self._recover_from_error(
                returncode=return_code,
                stdout=stdout_text,
                stderr=stderr_text,
                sanitized_command=sanitized_command,
                duration_seconds=duration,
                output_file_content=output_file_content,
            )
            if recovered is not None:
                return recovered

        if return_code != 0:
            raise CLIAgentError(
                f"CLI '{self.client.name}' exited with status {return_code}",
                returncode=return_code,
                stdout=stdout_text,
                stderr=stderr_text,
            )

        try:
            parsed = self._parser.parse(stdout_text, stderr_text)
        except ParserError as exc:
            raise CLIAgentError(
                f"Failed to parse output from CLI '{self.client.name}': {exc}",
                returncode=return_code,
                stdout=stdout_text,
                stderr=stderr_text,
            ) from exc

        return AgentOutput(
            parsed=parsed,
            sanitized_command=sanitized_command,
            returncode=return_code,
            stdout=stdout_text,
            stderr=stderr_text,
            duration_seconds=duration,
            parser_name=self._parser.name,
            output_file_content=output_file_content,
        )

    def _build_command(self, *, role: "ResolvedCLIRole", system_prompt: str | None) -> list[str]:
        """Build the command to execute."""
        base = list(self.client.executable)
        base.extend(self.client.base_args)
        base.extend(role.role_args)
        return base

    def _build_environment(self) -> dict[str, str]:
        """Build environment variables for the CLI."""
        env = os.environ.copy()
        env.update(self.client.env)
        return env

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
        """Hook for subclasses to convert CLI errors into successful outputs.

        Return an AgentOutput to treat the failure as success, or None to signal
        that normal error handling should proceed.
        """
        return None
