"""Ask Claude Code for one structured answer, and trace the call.

Calls run `claude -p` with MCP servers and settings turned off and only the tools a step asks for,
so each call carries a few hundred tokens of setup instead of tens of thousands. Every call appends
one line to trace.jsonl.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

SYSTEM = "You are a careful analyst. Answer only in the requested JSON format."


def ask(prompt: str, schema: dict, model: str, trace: Path, label: str, tools: str = "") -> dict:
    """`tools` is a comma-separated list such as "WebSearch,WebFetch"; empty means none."""
    command = ["claude", "-p", prompt, "--model", model, "--output-format", "json",
               "--json-schema", json.dumps(schema), "--system-prompt", SYSTEM,
               "--tools", tools, "--strict-mcp-config", "--setting-sources", "",
               "--no-session-persistence"]
    if tools:
        command += ["--allowedTools", tools]
    done = subprocess.run(command, capture_output=True, text=True, timeout=900)
    if done.returncode != 0:
        raise RuntimeError(f"claude failed for {label}: {done.stderr.strip() or done.stdout[:300]}")
    reply = json.loads(done.stdout)
    usage = reply.get("usage", {})
    with open(trace, "a") as f:
        f.write(json.dumps({
            "time": datetime.now().isoformat(timespec="seconds"),
            "label": label,
            "model": model,
            "prompt": prompt,
            "answer": reply.get("structured_output"),
            "input_tokens": usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0)
                            + usage.get("cache_read_input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "seconds": reply.get("duration_ms", 0) / 1000,
            "list_price_usd": reply.get("total_cost_usd"),
        }, ensure_ascii=False) + "\n")
    if reply.get("subtype") != "success" or reply.get("structured_output") is None:
        raise RuntimeError(f"claude gave no structured answer for {label}: {reply.get('result')}")
    return reply["structured_output"]
