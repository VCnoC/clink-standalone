# Clink Standalone

**[English](README.md)** | **[中文](README_CN.md)**

独立运行的 CLI 桥接工具，用于调用外部 AI CLI（gemini、codex、claude），**无需 MCP 服务器依赖**。

## 什么是 Clink？

Clink 让你可以在对话中启动外部 AI CLI 工具，每个工具都具有：
- 独立的上下文窗口
- 完整的原生能力（网络搜索、文件工具）
- 基于角色的行为（default、planner、codereviewer）

## 快速开始

只需将此仓库克隆到你的 AI 编程助手的 skills 文件夹中即可使用！

### Claude Code

```bash
# 直接克隆到 Claude Code skills 文件夹
git clone https://github.com/VCnoC/clink-standalone.git ~/.claude/skills/clink-standalone
```

### OpenAI Codex CLI

```bash
# 直接克隆到 Codex skills 文件夹
git clone https://github.com/VCnoC/clink-standalone.git ~/.codex/skills/clink-standalone
```

### Gemini CLI

```bash
# 直接克隆到 Gemini skills 文件夹
git clone https://github.com/VCnoC/clink-standalone.git ~/.gemini/skills/clink-standalone
```

就这么简单！AI 助手会自动读取 skill 定义并知道如何使用它。

## 目录结构

```
clink-standalone/
├── bin/clink.py          # 主 CLI 入口
├── clink_core/           # 核心 Python 模块
│   ├── models.py         # Pydantic 数据模型
│   ├── registry.py       # 配置加载器
│   └── runner.py         # CLI 执行引擎
├── config/               # CLI 配置
│   ├── gemini.json
│   ├── codex.json
│   └── claude.json
├── systemprompts/        # 角色专用提示词
│   ├── gemini/
│   ├── codex/
│   └── claude/
├── SKILL.md              # Skill 定义（AI 自动读取）
└── README.md             # 英文说明
```

## 使用示例

安装后，你可以让 AI 助手委派任务：

```
> 使用 gemini 解释 Rust 的所有权机制
> 让 codex 审查 src/auth.py 的安全问题
> 用 claude 的 planner 角色设计迁移策略
```

或者直接通过命令行运行：

```bash
# 简单查询
python bin/clink.py gemini "Python 3.13 有什么新特性？"

# 带文件的代码审查
python bin/clink.py codex "审查安全问题" --files src/auth.py

# 使用 planner 角色
python bin/clink.py gemini "规划数据库迁移" --role planner

# JSON 输出
python bin/clink.py gemini "解释装饰器" --json

# 列出可用的 CLI 和角色
python bin/clink.py --list-clients
python bin/clink.py --list-roles gemini
```

## 可用的 CLI 和角色

| CLI | 优势 | 角色 |
|-----|------|------|
| **gemini** | 100万 token 上下文、网络搜索 | default, planner, codereviewer |
| **codex** | 代码分析、审查 | default, planner, codereviewer |
| **claude** | 通用任务 | default, planner, codereviewer |

### 角色说明

| 角色 | 用途 | 最适合 |
|------|------|--------|
| `default` | 通用任务 | 问答、摘要、快速回答 |
| `planner` | 战略规划 | 多阶段计划、架构设计、迁移方案 |
| `codereviewer` | 代码分析 | 安全审查、质量检查、Bug 排查 |

## Python API

```python
from clink_core import get_registry, run_cli

registry = get_registry()
client = registry.get_client("gemini")
role = client.get_role("planner")

result = run_cli(client, role, "规划 REST API 重构")
print(result.content)
```

## 配置

编辑 `config/*.json` 自定义 CLI 命令、参数和超时时间。

在 `systemprompts/<cli>/<role>.txt` 添加新的角色提示词。

## 系统要求

- Python 3.9+
- pydantic

## 致谢与许可证

本项目提取自 BeehiveInnovations 的 [PAL MCP Server](https://github.com/BeehiveInnovations/pal-mcp-server)（原名 Zen MCP Server）。

### 致谢

- [PAL MCP Server](https://github.com/BeehiveInnovations/pal-mcp-server) - 原始多模型 AI 协作框架
- [MCP (Model Context Protocol)](https://modelcontextprotocol.com)
- [Claude Code](https://claude.ai/code) by Anthropic
- [Gemini CLI](https://ai.google.dev/) by Google
- [Codex CLI](https://developers.openai.com/codex/cli) by OpenAI

### 许可证

Apache 2.0 许可证 - 详情请参阅原始 [PAL MCP Server LICENSE](https://github.com/BeehiveInnovations/pal-mcp-server/blob/main/LICENSE)。
