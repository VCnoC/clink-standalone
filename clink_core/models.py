"""Pydantic models for clink configuration and runtime structures.

Standalone version - no MCP dependencies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class OutputToFileConfig(BaseModel):
    """Configuration for output-to-file mode."""

    flag_template: str = Field(
        description="Flag template with {path} placeholder, e.g., '--output {path}'"
    )
    cleanup: bool = Field(
        default=True,
        description="Whether to delete the temp file after reading",
    )


class CLIRoleConfig(BaseModel):
    """Role-specific configuration loaded from JSON manifests."""

    prompt_path: str | None = Field(
        default=None,
        description="Path to the prompt file that seeds this role.",
    )
    role_args: list[str] = Field(default_factory=list)
    description: str | None = Field(default=None)

    @field_validator("role_args", mode="before")
    @classmethod
    def _ensure_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, str):
            return [value]
        raise TypeError("role_args must be a list of strings or a single string")


class OutputToFileRawConfig(BaseModel):
    """Raw output-to-file configuration from JSON."""

    flag_template: str
    cleanup: bool = True


class CLIClientConfig(BaseModel):
    """Raw CLI client configuration."""

    name: str
    command: str | None = None
    working_dir: str | None = None
    additional_args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: int = Field(default=300)
    roles: dict[str, CLIRoleConfig] = Field(default_factory=dict)
    parser: str | None = Field(
        default=None,
        description="Parser name to use for output (e.g., 'gemini_json', 'codex_jsonl')",
    )
    output_to_file: OutputToFileRawConfig | None = Field(
        default=None,
        description="Output-to-file mode configuration",
    )

    @field_validator("additional_args", mode="before")
    @classmethod
    def _ensure_args_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, str):
            return [value]
        raise TypeError("additional_args must be a list of strings or a single string")


class ResolvedCLIRole(BaseModel):
    """Runtime representation of a CLI role with resolved prompt path."""

    name: str
    prompt_path: Path
    prompt_text: str
    role_args: list[str] = Field(default_factory=list)
    description: str | None = None


class ResolvedCLIClient(BaseModel):
    """Runtime configuration after merging defaults and validating paths."""

    name: str
    executable: list[str]
    working_dir: Path | None
    base_args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: int
    roles: dict[str, ResolvedCLIRole]
    parser: str = Field(
        default="passthrough",
        description="Parser name for output processing",
    )
    output_to_file: OutputToFileConfig | None = Field(
        default=None,
        description="Output-to-file mode configuration",
    )

    def list_roles(self) -> list[str]:
        return list(self.roles.keys())

    def get_role(self, role_name: str | None) -> ResolvedCLIRole:
        key = role_name or "default"
        if key not in self.roles:
            available = ", ".join(sorted(self.roles.keys()))
            raise KeyError(f"Role '{role_name}' not configured for CLI '{self.name}'. Available roles: {available}")
        return self.roles[key]


class CLIResult(BaseModel):
    """Result from running a CLI command."""

    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    success: bool = True
