# Clink Standalone

Standalone CLI bridge for external AI CLIs (gemini, codex, claude) **without MCP server dependency**.

## What is Clink?

Clink lets you launch external AI CLI tools from within a conversation, giving each tool:
- Its own isolated context window
- Full access to native capabilities (web search, file tools)
- Role-based behavior (default, planner, codereviewer)

## Quick Start

Simply clone this repo into your AI coding assistant's skills folder and start using it!

### Claude Code

```bash
# Clone directly to Claude Code skills folder
git clone https://github.com/VCnoC/clink-standalone.git ~/.claude/skills/clink-standalone
```

### OpenAI Codex CLI

```bash
# Clone directly to Codex skills folder
git clone https://github.com/VCnoC/clink-standalone.git ~/.codex/skills/clink-standalone
```

### Gemini CLI

```bash
# Clone directly to Gemini skills folder
git clone https://github.com/VCnoC/clink-standalone.git ~/.gemini/skills/clink-standalone
```

That's it! The AI assistant will automatically read the skill definition and know how to use it.

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
├── SKILL.md              # Skill definition (auto-read by AI)
└── README.md             # This file
```

## Usage Examples

Once installed, you can ask your AI assistant to delegate tasks:

```
> Use gemini to explain Rust ownership
> Ask codex to review src/auth.py for security issues
> Run claude with planner role to design a migration strategy
```

Or run directly via command line:

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

## Available CLIs and Roles

| CLI | Strengths | Roles |
|-----|-----------|-------|
| **gemini** | 1M context, web search | default, planner, codereviewer |
| **codex** | Code analysis, review | default, planner, codereviewer |
| **claude** | General purpose | default, planner, codereviewer |

### Role Definitions

| Role | Purpose | Best For |
|------|---------|----------|
| `default` | General tasks | Questions, summaries, quick answers |
| `planner` | Strategic planning | Multi-phase plans, architecture, migrations |
| `codereviewer` | Code analysis | Security review, quality checks, bug hunting |

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

Add new role prompts in `systemprompts/<cli>/<role>.txt`.

## Requirements

- Python 3.9+
- pydantic

## Credits & License

This project is extracted from [PAL MCP Server](https://github.com/BeehiveInnovations/pal-mcp-server) (formerly Zen MCP Server) by BeehiveInnovations.

### Acknowledgments

- [PAL MCP Server](https://github.com/BeehiveInnovations/pal-mcp-server) - The original multi-model AI collaboration framework
- [MCP (Model Context Protocol)](https://modelcontextprotocol.com)
- [Claude Code](https://claude.ai/code) by Anthropic
- [Gemini CLI](https://ai.google.dev/) by Google
- [Codex CLI](https://developers.openai.com/codex/cli) by OpenAI

### License

Apache 2.0 License - see the original [PAL MCP Server LICENSE](https://github.com/BeehiveInnovations/pal-mcp-server/blob/main/LICENSE) for details.
