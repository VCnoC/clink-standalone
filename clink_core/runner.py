"""CLI runner for executing external AI CLIs.

Standalone version - runs CLI commands directly without MCP.
Uses specialized agents and parsers for each CLI type.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from .agents import create_agent, CLIAgentError
from .models import ResolvedCLIClient, ResolvedCLIRole, CLIResult
from .session import get_session_manager

logger = logging.getLogger("clink.runner")

MAX_RESPONSE_CHARS = 50_000


def run_cli(
    client: ResolvedCLIClient,
    role: ResolvedCLIRole,
    prompt: str,
    files: list[str] | None = None,
    images: list[str] | None = None,
    continuation_id: str | None = None,
) -> CLIResult:
    """Run a CLI with the given prompt and return parsed result.

    Args:
        client: Resolved CLI configuration
        role: Role to use (contains prompt template)
        prompt: User prompt to send to the CLI
        files: Optional list of file paths to reference
        images: Optional list of image paths
        continuation_id: Optional session ID for conversation continuation

    Returns:
        CLIResult with content, metadata, and continuation_id
    """
    runner = ClinkRunner(client)
    return asyncio.run(
        runner.run(
            role=role,
            prompt=prompt,
            files=files or [],
            images=images or [],
            continuation_id=continuation_id,
        )
    )


class ClinkRunner:
    """Execute CLI commands using specialized agents."""

    def __init__(self, client: ResolvedCLIClient):
        self.client = client
        self._agent = create_agent(client)
        self._session_manager = get_session_manager()

    async def run(
        self,
        role: ResolvedCLIRole,
        prompt: str,
        files: list[str],
        images: list[str],
        continuation_id: str | None = None,
    ) -> CLIResult:
        """Execute CLI and return parsed result."""
        # Handle session continuation
        session_id, session, is_new = self._session_manager.get_or_create_session(
            continuation_id=continuation_id,
            cli_name=self.client.name,
            role_name=role.name,
        )

        # Build the full prompt
        full_prompt = self._build_prompt(role, prompt, files, images)

        # Add continuation context if resuming
        if not is_new and session.turn_count > 0:
            full_prompt = f"[Continuing conversation, turn {session.turn_count + 1}]\n\n{full_prompt}"

        try:
            # Execute using specialized agent
            output = await self._agent.run(
                role=role,
                prompt=full_prompt,
                system_prompt=role.prompt_text if role.prompt_text.strip() else None,
                files=files,
                images=images,
            )

            # Apply output limit
            content, metadata = self._apply_output_limit(
                output.parsed.content,
                {
                    "cli_name": self.client.name,
                    "role": role.name,
                    "duration_seconds": output.duration_seconds,
                    "return_code": output.returncode,
                    "parser_name": output.parser_name,
                    "continuation_id": session_id,
                    "turn_count": session.turn_count,
                    **output.parsed.metadata,
                },
            )

            return CLIResult(
                content=content,
                metadata=metadata,
                returncode=output.returncode,
                stdout=output.stdout,
                stderr=output.stderr,
                duration_seconds=output.duration_seconds,
                success=True,
            )

        except CLIAgentError as exc:
            logger.error(f"CLI agent error: {exc}")
            return CLIResult(
                content=f"Error executing CLI '{self.client.name}': {exc}",
                metadata={
                    "cli_name": self.client.name,
                    "role": role.name,
                    "error": str(exc),
                    "continuation_id": session_id,
                },
                returncode=exc.returncode or -1,
                stdout=exc.stdout,
                stderr=exc.stderr,
                duration_seconds=0.0,
                success=False,
            )

    def _build_prompt(
        self,
        role: ResolvedCLIRole,
        prompt: str,
        files: list[str],
        images: list[str],
    ) -> str:
        """Build the full prompt to send to the CLI."""
        sections = []

        # Add file references
        if files:
            file_refs = self._format_file_references(files)
            sections.append("=== FILE REFERENCES ===\n" + file_refs)

        # Add image references
        if images:
            image_refs = "\n".join(f"- {img}" for img in images)
            sections.append("=== IMAGES ===\n" + image_refs)

        # Add user prompt
        sections.append("=== USER REQUEST ===\n" + prompt.strip())

        return "\n\n".join(sections)

    def _format_file_references(self, files: list[str]) -> str:
        """Format file paths as references."""
        from pathlib import Path

        refs = []
        for file_path in files:
            try:
                path = Path(file_path)
                if path.exists():
                    stat = path.stat()
                    size = stat.st_size
                    refs.append(f"- {file_path} ({size} bytes)")
                else:
                    refs.append(f"- {file_path} (not found)")
            except OSError:
                refs.append(f"- {file_path} (error)")
        return "\n".join(refs) if refs else "No files provided."

    def _apply_output_limit(
        self, content: str, metadata: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Apply output length limit."""
        if len(content) <= MAX_RESPONSE_CHARS:
            return content, metadata

        # Try to extract summary
        summary = self._extract_summary(content)
        if summary:
            metadata["output_summarized"] = True
            metadata["output_original_length"] = len(content)
            metadata["output_summary_length"] = len(summary)
            return summary, metadata

        # Truncate with excerpt
        excerpt_limit = min(4000, MAX_RESPONSE_CHARS // 2)
        excerpt = content[:excerpt_limit]
        metadata["output_truncated"] = True
        metadata["output_original_length"] = len(content)
        metadata["output_excerpt_length"] = len(excerpt)

        message = (
            f"Output was {len(content)} characters, exceeding limit. "
            f"Showing excerpt:\n\n{excerpt}\n\n... (truncated)"
        )
        return message, metadata

    def _extract_summary(self, content: str) -> str | None:
        """Extract summary from content if available."""
        pattern = re.compile(r"<SUMMARY>(.*?)</SUMMARY>", re.IGNORECASE | re.DOTALL)
        match = pattern.search(content)
        if match:
            summary = match.group(1).strip()
            return summary or None
        return None
