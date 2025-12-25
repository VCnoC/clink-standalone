"""Configuration registry for clink CLI integrations.

Standalone version - loads configs from local config directory.
"""

from __future__ import annotations

import json
import logging
import shlex
from collections.abc import Iterable
from pathlib import Path

from .models import (
    CLIClientConfig,
    CLIRoleConfig,
    OutputToFileConfig,
    ResolvedCLIClient,
    ResolvedCLIRole,
)

logger = logging.getLogger("clink.registry")

# Default paths
DEFAULT_CONFIG_DIR = Path(__file__).parent.parent / "config"
DEFAULT_SYSTEMPROMPTS_DIR = Path(__file__).parent.parent / "systemprompts"
USER_CONFIG_DIR = Path.home() / ".clink" / "cli_clients"

# Built-in CLI defaults with parser and output_to_file support
DEFAULT_TIMEOUT_SECONDS = 1800  # 30 minutes

INTERNAL_DEFAULTS: dict[str, dict] = {
    "gemini": {
        "command": "gemini",
        "additional_args": ["--telemetry", "false", "--yolo", "-o", "json"],
        "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
        "parser": "gemini_json",
    },
    "codex": {
        "command": "codex",
        "additional_args": ["exec", "--json", "--dangerously-bypass-approvals-and-sandbox", "--skip-git-repo-check"],
        "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
        "parser": "codex_jsonl",
    },
    "claude": {
        "command": "claude",
        "additional_args": ["--print", "--output-format", "json", "--permission-mode", "acceptEdits"],
        "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
        "parser": "claude_json",
    },
}


class ClinkRegistry:
    """Loads CLI client definitions from config directory.

    Load order (later overrides earlier):
    1. Built-in defaults (INTERNAL_DEFAULTS)
    2. Package config directory (./config/)
    3. User config directory (~/.clink/cli_clients/)
    """

    def __init__(
        self,
        config_dir: Path | None = None,
        user_config_dir: Path | None = None,
    ) -> None:
        self._config_dir = config_dir or DEFAULT_CONFIG_DIR
        self._user_config_dir = user_config_dir or USER_CONFIG_DIR
        self._systemprompts_dir = DEFAULT_SYSTEMPROMPTS_DIR
        self._clients: dict[str, ResolvedCLIClient] = {}
        self._load()

    def _load(self) -> None:
        self._clients.clear()

        # Collect all config directories to scan
        config_dirs = [self._config_dir]
        if self._user_config_dir.exists():
            config_dirs.append(self._user_config_dir)

        # Load from all config directories
        for config_dir in config_dirs:
            if not config_dir.exists():
                continue
            for config_path in sorted(config_dir.glob("*.json")):
                try:
                    data = json.loads(config_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError as exc:
                    logger.warning(f"Invalid JSON in {config_path}: {exc}")
                    continue

                if not data:
                    continue

                try:
                    config = CLIClientConfig.model_validate(data)
                    resolved = self._resolve_config(config)
                    key = resolved.name.lower()
                    self._clients[key] = resolved
                    logger.debug(f"Loaded CLI configuration for '{resolved.name}' from {config_path}")
                except Exception as exc:
                    logger.warning(f"Failed to load {config_path}: {exc}")

        if not self._clients:
            logger.warning("No CLI clients configured. Using built-in defaults.")
            # Create minimal default configs from internal defaults
            for name, defaults in INTERNAL_DEFAULTS.items():
                config = CLIClientConfig(
                    name=name,
                    command=defaults["command"],
                    additional_args=defaults["additional_args"],
                    timeout_seconds=defaults["timeout_seconds"],
                    parser=defaults.get("parser"),
                )
                resolved = self._resolve_config(config)
                self._clients[name] = resolved

    def reload(self) -> None:
        """Reload configurations from disk."""
        self._load()

    def list_clients(self) -> list[str]:
        return sorted(client.name for client in self._clients.values())

    def list_roles(self, cli_name: str) -> list[str]:
        config = self.get_client(cli_name)
        return sorted(config.roles.keys())

    def get_client(self, cli_name: str) -> ResolvedCLIClient:
        key = cli_name.lower()
        if key not in self._clients:
            available = ", ".join(self.list_clients())
            raise KeyError(f"CLI '{cli_name}' is not configured. Available clients: {available}")
        return self._clients[key]

    def _resolve_config(self, raw: CLIClientConfig) -> ResolvedCLIClient:
        if not raw.name:
            raise ValueError("CLI configuration is missing a 'name' field")

        normalized_name = raw.name.strip()
        internal_defaults = INTERNAL_DEFAULTS.get(normalized_name.lower(), {})

        # Resolve executable
        command = raw.command or internal_defaults.get("command")
        if not command:
            raise ValueError(f"CLI '{raw.name}' must specify a 'command'")
        executable = shlex.split(command)

        # Resolve args: config overrides internal defaults
        if raw.additional_args:
            base_args = list(raw.additional_args)
        else:
            base_args = list(internal_defaults.get("additional_args", []))

        timeout_seconds = raw.timeout_seconds or internal_defaults.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)

        env = dict(raw.env)
        working_dir = self._resolve_optional_path(raw.working_dir)

        roles = self._resolve_roles(raw, normalized_name)

        # Resolve parser: config -> internal default -> passthrough
        parser = raw.parser or internal_defaults.get("parser", "passthrough")

        # Resolve output_to_file
        output_to_file: OutputToFileConfig | None = None
        if raw.output_to_file:
            output_to_file = OutputToFileConfig(
                flag_template=raw.output_to_file.flag_template,
                cleanup=raw.output_to_file.cleanup,
            )
        elif "output_to_file" in internal_defaults:
            otf_default = internal_defaults["output_to_file"]
            output_to_file = OutputToFileConfig(
                flag_template=otf_default["flag_template"],
                cleanup=otf_default.get("cleanup", True),
            )

        return ResolvedCLIClient(
            name=normalized_name,
            executable=executable,
            working_dir=working_dir,
            base_args=base_args,
            env=env,
            timeout_seconds=int(timeout_seconds),
            roles=roles,
            parser=parser,
            output_to_file=output_to_file,
        )

    def _resolve_roles(self, raw: CLIClientConfig, cli_name: str) -> dict[str, ResolvedCLIRole]:
        roles: dict[str, CLIRoleConfig] = dict(raw.roles)

        # Ensure default role exists
        if "default" not in roles:
            default_prompt = self._systemprompts_dir / cli_name / "default.txt"
            if default_prompt.exists():
                roles["default"] = CLIRoleConfig(prompt_path=str(default_prompt))
            else:
                # Create empty default role
                roles["default"] = CLIRoleConfig(prompt_path=None)

        resolved: dict[str, ResolvedCLIRole] = {}
        for role_name, role_config in roles.items():
            prompt_path_str = role_config.prompt_path

            if prompt_path_str:
                prompt_path = Path(prompt_path_str)
                if not prompt_path.is_absolute():
                    # Try relative to systemprompts dir
                    prompt_path = self._systemprompts_dir / cli_name / f"{role_name}.txt"
                prompt_text = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
            else:
                # Try systemprompts directory
                prompt_path = self._systemprompts_dir / cli_name / f"{role_name}.txt"
                prompt_text = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""

            resolved[role_name] = ResolvedCLIRole(
                name=role_name,
                prompt_path=prompt_path if prompt_path_str else Path(""),
                prompt_text=prompt_text,
                role_args=list(role_config.role_args),
                description=role_config.description,
            )
        return resolved

    def _resolve_optional_path(self, candidate: str | None) -> Path | None:
        if not candidate:
            return None
        path = Path(candidate).expanduser()
        return path if path.exists() else None


_REGISTRY: ClinkRegistry | None = None


def get_registry(config_dir: Path | None = None) -> ClinkRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = ClinkRegistry(config_dir)
    return _REGISTRY
