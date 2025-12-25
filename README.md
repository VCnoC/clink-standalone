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

## Using as a Skill

This project can be used as a **Skill** in various AI coding assistants. Below are the setup instructions for each platform.

### Claude Code

1. **Copy to Claude skills directory:**

```bash
cp -r clink-standalone ~/.claude/skills/clink-standalone
```

2. **Add to your project's `.claude/commands/` (optional):**

Create custom slash commands that invoke clink:

```bash
# .claude/commands/gemini.md
---
name: gemini
description: "Delegate a task to Gemini CLI"
---
python ~/.claude/skills/clink-standalone/bin/clink.py gemini "$ARGUMENTS"
```

3. **Usage in Claude Code:**

```
> Use gemini to explain Rust ownership
> Ask codex to review src/auth.py for security issues
```

---

### OpenAI Codex CLI

1. **Add to your Codex instructions directory:**

```bash
cp -r clink-standalone ~/.codex/skills/clink-standalone
```

2. **Reference in your `codex.md` or instructions file:**

```markdown
# External CLI Tools

You can delegate tasks to external AI CLIs using the clink bridge:

- Gemini: `python ~/.codex/skills/clink-standalone/bin/clink.py gemini "<prompt>"`
- Claude: `python ~/.codex/skills/clink-standalone/bin/clink.py claude "<prompt>"`
```

3. **Usage in Codex:**

```
> Run gemini to search for the latest Python 3.13 features
```

---

### Gemini CLI / Gemini Code Assist

1. **Add to your Gemini workspace:**

```bash
cp -r clink-standalone ~/.gemini/skills/clink-standalone
```

2. **Create a GEMINI.md instruction file:**

```markdown
# Clink CLI Bridge

Use clink to delegate tasks to other AI assistants:

## Available Commands

- `python ~/.gemini/skills/clink-standalone/bin/clink.py codex "<prompt>"` - Use Codex for code analysis
- `python ~/.gemini/skills/clink-standalone/bin/clink.py claude "<prompt>"` - Use Claude for general tasks

## Roles

Add `--role planner` for planning tasks, or `--role codereviewer` for code reviews.
```

3. **Usage in Gemini:**

```
> Use codex to analyze the codebase architecture
> Run claude with planner role to design a migration strategy
```

---

### Universal Setup Tips

- **Environment Variables**: Ensure all CLI tools are in your `PATH`
- **Authentication**: Run `gemini auth login` and authenticate other CLIs before use
- **Config Customization**: Edit `config/*.json` to adjust timeouts, arguments, or add new CLIs
- **Custom Roles**: Add new role prompts in `systemprompts/<cli>/<role>.txt`

## Supported CLIs

| CLI | Install | Features |
|-----|---------|----------|
| gemini | `npm install -g @google/gemini-cli` | 1M context, web search |
| codex | [Sourcegraph](https://docs.sourcegraph.com/codex) | Code analysis |
| claude | [Anthropic](https://www.anthropic.com/claude-code) | General purpose |

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
