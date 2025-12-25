"""Parser for Claude CLI JSON output."""

from __future__ import annotations

import json
from typing import Any

from .base import BaseParser, ParsedCLIResponse, ParserError


class ClaudeJSONParser(BaseParser):
    """Parse stdout produced by `claude --output-format json`."""

    name = "claude_json"

    def parse(self, stdout: str, stderr: str) -> ParsedCLIResponse:
        if not stdout.strip():
            raise ParserError("Claude CLI returned empty stdout while JSON output was expected")

        # Try to find JSON in stdout (might have prefix text)
        json_start = stdout.find("{")
        if json_start == -1:
            # Try array format
            json_start = stdout.find("[")

        if json_start == -1:
            raise ParserError("Claude CLI output does not contain valid JSON")

        json_text = stdout[json_start:]

        try:
            payload: Any = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise ParserError(f"Failed to decode Claude CLI JSON output: {exc}") from exc

        metadata: dict[str, Any] = {}
        content = ""

        if isinstance(payload, dict):
            # Handle various response formats
            if "result" in payload:
                content = str(payload["result"])
            elif "response" in payload:
                content = str(payload["response"])
            elif "content" in payload:
                content = str(payload["content"])
            elif "text" in payload:
                content = str(payload["text"])
            elif "message" in payload:
                content = str(payload["message"])
            else:
                # Use entire payload as content
                content = json.dumps(payload, ensure_ascii=False, indent=2)

            metadata["raw"] = payload

            # Extract usage info if present
            if "usage" in payload:
                metadata["usage"] = payload["usage"]
            if "model" in payload:
                metadata["model_used"] = payload["model"]

        elif isinstance(payload, list):
            # Handle array of messages
            messages = []
            for item in payload:
                if isinstance(item, dict):
                    text = item.get("text") or item.get("content") or item.get("message")
                    if text:
                        messages.append(str(text))
                elif isinstance(item, str):
                    messages.append(item)
            content = "\n\n".join(messages)
            metadata["raw"] = payload
        else:
            content = str(payload)
            metadata["raw"] = payload

        if not content.strip():
            raise ParserError("Claude CLI response is empty")

        if stderr and stderr.strip():
            metadata["stderr"] = stderr.strip()

        return ParsedCLIResponse(content=content.strip(), metadata=metadata)
