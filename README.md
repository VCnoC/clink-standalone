# Clink Standalone

Standalone CLI bridge for external AI CLIs (gemini, codex, claude) **without MCP server dependency**.

## What is Clink?

Clink lets you launch external AI CLI tools from within a conversation, giving each tool:
- Its own isolated context window
- Full access to native capabilities (web search, file tools)
- Role-based behavior (default, planner, codereviewer)

## Quick Start

```bash
# 1. Install dependencies
pip install pydantic

# 2. Install a CLI (e.g., Gemini)
npm install -g @google/gemini-cli
gemini auth login

# 3. Run clink
python bin/clink.py gemini "Explain async/await in Python"
```

## Directory Structure

```
clink-standalone/
├── bin/clink.py          # Main CLI entry point
├── clink_core/           # Core Python module
│   ├── models.py         # Pydantic data models
│   ├── registry.py       # Config loader
│   └── runner.py         # CLI execution engine
├── config/               # CLI configurations
│   ├── gemini.json
│   ├── codex.json
│   └── claude.json
├── systemprompts/        # Role-specific prompts
│   ├── gemini/
│   ├── codex/
│   └── claude/
├── SKILL.md              # Claude Code skill definition
└── README.md             # This file
```

## Usage Examples

```bash
# Simple query
python bin/clink.py gemini "What's new in Python 3.13?"

# Code review with files
python bin/clink.py codex "Review for security issues" --files src/auth.py

# Use planner role
python bin/clink.py gemini "Plan a database migration" --role planner

# JSON output
python bin/clink.py gemini "Explain decorators" --json

# List available CLIs and roles
python bin/clink.py --list-clients
python bin/clink.py --list-roles gemini
```

## Python API

```python
from clink_core import get_registry, run_cli

registry = get_registry()
client = registry.get_client("gemini")
role = client.get_role("planner")

result = run_cli(client, role, "Plan a REST API redesign")
print(result.content)
```

## Configuration

Edit `config/*.json` to customize CLI commands, args, and timeouts.

## Requirements

- Python 3.9+
- pydantic

## Supported CLIs

| CLI | Install | Features |
|-----|---------|----------|
| gemini | `npm install -g @google/gemini-cli` | 1M context, web search |
| codex | [Sourcegraph](https://docs.sourcegraph.com/codex) | Code analysis |
| claude | [Anthropic](https://www.anthropic.com/claude-code) | General purpose |

## License

Extracted from zen-mcp-server.
