#!/usr/bin/env python3
"""Clink - Standalone CLI bridge for external AI CLIs.

Usage:
    python clink.py <cli_name> <prompt> [--role ROLE] [--files FILE...]

Examples:
    python clink.py gemini "Explain async/await in Python"
    python clink.py codex "Review auth.py" --files src/auth.py
    python clink.py gemini "Plan migration" --role planner
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clink_core import get_registry


def main():
    parser = argparse.ArgumentParser(
        description="Clink - Bridge to external AI CLIs (gemini, codex, claude)"
    )
    parser.add_argument("cli_name", nargs="?", help="CLI to use: gemini, codex, or claude")
    parser.add_argument("prompt", nargs="?", help="Prompt to send to the CLI")
    parser.add_argument("--role", "-r", default="default", help="Role to use (default: default)")
    parser.add_argument("--files", "-f", nargs="*", default=[], help="File paths to reference")
    parser.add_argument("--images", "-i", nargs="*", default=[], help="Image paths to include")
    parser.add_argument("--config-dir", help="Custom config directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--list-clients", action="store_true", help="List available CLIs")
    parser.add_argument("--list-roles", help="List roles for a CLI")

    args = parser.parse_args()

    registry = get_registry(Path(args.config_dir) if args.config_dir else None)

    # Handle list commands
    if args.list_clients:
        clients = registry.list_clients()
        print("Available CLIs:")
        for cli in clients:
            print(f"  - {cli}")
        return 0

    if args.list_roles:
        try:
            roles = registry.list_roles(args.list_roles)
            print(f"Roles for {args.list_roles}:")
            for role in roles:
                print(f"  - {role}")
            return 0
        except KeyError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    # Run CLI
    if not args.cli_name or not args.prompt:
        parser.error("cli_name and prompt are required unless using --list-clients or --list-roles")

    try:
        client = registry.get_client(args.cli_name)
        role = client.get_role(args.role)

        from clink_core import run_cli
        result = run_cli(client, role, args.prompt, args.files, args.images)

        if args.json:
            output = {
                "content": result.content,
                "metadata": result.metadata,
                "success": result.success,
                "duration_seconds": result.duration_seconds,
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print(result.content)

        return 0 if result.success else 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
