# CLAUDE-CODE.md - Using Claude Code CLI as Sub-Agent

**Version:** v1.0.8
**Last Updated:** 2026-01-24

## Purpose

Spawn Claude Code CLI as sub-agent for non-interactive, focused work with full tool access (file operations, web search, code execution).

### Quick Start

```bash
# ✅ RECOMMENDED: Use this command for 95% of use cases
echo "your prompt here" | claude -p --tools default --permission-mode dontAsk 2>&1
```

**Why this command:**
- `echo | claude -p`: Passes prompt via stdin to non-interactive mode
- `--tools default`: Full tool access (Read, Write, Grep, Glob, Bash, etc.)
- `--permission-mode dontAsk`: Auto-approves all actions (required for sub-agents)
- `2>&1`: Captures both stdout and stderr

**When to use alternatives:** See [Core Commands](#core-commands) section below for JSON output, specific tool restrictions, etc.

**See [MULTI-AGENT.md](https://jonnyzzz.com/MULTI-AGENT.md) for:**
- When to use multi-agent orchestration
- Parallel execution patterns
- Error handling and retry logic
- Python/bash automation scripts
- Prompt engineering templates
- Cross-validation patterns

---

## When to Use Claude Code

### Ideal Use Cases

| Scenario | Why Claude Code |
|----------|-----------------|
| **Parallel Workloads** | Multiple instances run simultaneously |
| **Complex Code Analysis** | Full access to Read, Grep, Glob tools |
| **Web Research** | Built-in WebSearch and WebFetch |
| **Cross-Validation** | Different instance provides second opinion |
| **Isolated Tasks** | Each call starts fresh, prevents context pollution |

### When NOT to Use

- Interactive debugging requiring back-and-forth
- Tasks needing conversation history access
- Simple operations doable directly
- IntelliJ IDE operations (use Codex - better MCP support)

---

## Prerequisites

Before spawning Claude Code sub-agents, verify your setup:

### 1. Verify Installation

```bash
which claude
# Expected: ~/.local/bin/claude or /usr/local/bin/claude

claude --version
# Expected: 2.x.x (Claude Code)
```

**If not installed:** Visit [Claude Code documentation](https://github.com/anthropics/claude-code) for installation instructions.

### 2. Check Authentication

Claude Code uses your Anthropic account credentials automatically. No additional setup required.

### 3. Optional: MCP Servers (Advanced)

For advanced use cases involving IDE/browser automation, see the [MCP Server Visibility](#mcp-server-visibility) section at the end of this document.

**You're ready!** Proceed to Quick Start command above.

---

## Installation & Setup

```bash
# Verify installation
which claude
# Expected: ~/.local/bin/claude

# Check version
claude --version
# Expected: 2.x.x (Claude Code)
```

---

## Troubleshooting

- **CLI hangs or no output:** Check outbound DNS/network access; verify `claude --version` works, and try a trivial prompt (`echo "hi" | claude -p ...`) to confirm the runtime is reachable.

---

## Core Commands

### Recommended Pattern (Non-Interactive)

```bash
# RECOMMENDED: stdin + full tools + auto-approve
echo "<prompt>" | claude -p --tools default --permission-mode dontAsk 2>&1

# With prompt as argument
claude -p --tools default --permission-mode dontAsk "your prompt here" 2>&1

# JSON output (for programmatic parsing)
echo "prompt" | claude -p --tools default --permission-mode dontAsk --output-format json 2>&1

# Stream JSON (for real-time processing)
echo "prompt" | claude -p --tools default --permission-mode dontAsk --output-format stream-json 2>&1
```

### Tool Access Flags

**Give sub-agents full access** - don't restrict unnecessarily.

```bash
# Full access + autonomous approvals (RECOMMENDED)
echo "prompt" | claude -p --tools default --permission-mode dontAsk 2>&1

# Auto-approve edits only
echo "prompt" | claude -p --tools default --permission-mode acceptEdits 2>&1

# If you must restrict tools (rare)
echo "prompt" | claude -p --allowedTools "Read,Grep,Glob" --permission-mode dontAsk 2>&1
echo "prompt" | claude -p --disallowedTools "Edit,Write" --permission-mode dontAsk 2>&1
```

**Note:** Keep slash commands enabled (don't use `--disable-slash-commands`). MCP servers are inherited automatically - no need for `--mcp-config`.

### Permission Modes Reference

| Mode | Behavior | Use Case |
|------|----------|----------|
| `dontAsk` | Auto-approves all actions | **RECOMMENDED** for sub-agents, non-interactive execution |
| `acceptEdits` | Auto-approves edits only, prompts for bash/other | Semi-autonomous, safer but requires interaction |
| `(default)` | Prompts for all actions | Interactive use only, not suitable for sub-agents |

**For sub-agents, always use `--permission-mode dontAsk` to enable fully autonomous execution.**

### Output Formats

| Format | Flag | Use Case |
|--------|------|----------|
| Plain text | (default) | Human-readable output, logging |
| JSON | `--output-format json` | Programmatic parsing, structured data |
| Stream JSON | `--output-format stream-json` | Real-time processing, event streams |

---

## Spawning from Another Agent

### Basic Pattern

```bash
# Simple execution
claude -p --tools default --permission-mode dontAsk "Your detailed prompt here" 2>&1

# With stdin (preferred for complex prompts)
echo "Your detailed prompt here" | claude -p --tools default --permission-mode dontAsk 2>&1
```

### With File Context

```bash
# Claude Code uses Read tool to access files
echo "Read /path/to/file.md and extract:
1. Key concepts
2. Implementation patterns
3. Summary in 3 sentences" | claude -p --tools default --permission-mode dontAsk 2>&1
```

### Output Handling & Capture Strategies

**Basic Capture**

```bash
# Capture to file
echo "prompt" | claude -p --tools default --permission-mode dontAsk > /tmp/output.txt 2>&1

# Capture and display (tee)
echo "prompt" | claude -p --tools default --permission-mode dontAsk 2>&1 | tee /tmp/output.txt

# Capture only stderr
echo "prompt" | claude -p --tools default --permission-mode dontAsk 2>/tmp/errors.txt
```

**JSON Parsing**

```bash
# Parse JSON output with jq
echo "List 3 main points" | \
  claude -p --tools default --permission-mode dontAsk --output-format json 2>&1 | \
  jq -r '.result'

# Extract specific fields
echo "Analyze file.md" | \
  claude -p --tools default --permission-mode dontAsk --output-format json 2>&1 | \
  jq -r '.metadata.tokens_used'

# Stream JSON for real-time processing
echo "Long task" | \
  claude -p --tools default --permission-mode dontAsk --output-format stream-json 2>&1 | \
  while IFS= read -r line; do
    echo "$line" | jq -r '.type, .content' 2>/dev/null || true
  done
```

**Output Size Management**

```bash
# Limit output size (first 1000 lines)
echo "prompt" | claude -p --tools default --permission-mode dontAsk 2>&1 | head -1000

# Compress large outputs
echo "Generate 100 examples" | \
  claude -p --tools default --permission-mode dontAsk 2>&1 | \
  gzip > /tmp/large-output.txt.gz

# Tail last N lines for monitoring
echo "Analyze codebase" | \
  claude -p --tools default --permission-mode dontAsk 2>&1 | \
  tail -100 > /tmp/summary.txt
```

**Error Detection**

```bash
# Check exit code
echo "prompt" | claude -p --tools default --permission-mode dontAsk 2>&1
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
  echo "❌ Agent failed with exit code $EXIT_CODE"
fi

# Search for errors in output
echo "prompt" | claude -p --tools default --permission-mode dontAsk 2>&1 | tee /tmp/out.txt
if grep -qi "error\|failed\|exception" /tmp/out.txt; then
  echo "⚠️ Agent encountered errors"
fi
```

**Best Practices**

1. **Always use `2>&1`** - Captures both stdout and stderr
2. **Check output size** - Large outputs can consume disk space
3. **Use JSON for parsing** - Structured data easier to process programmatically
4. **Save intermediate results** - Don't lose expensive agent outputs
5. **Validate outputs** - Agent responses may contain errors or incomplete data
6. **Set timeouts** - Prevent indefinite hangs with `timeout` command
7. **Monitor in real-time** - Use `tee` to both save and display output

---

## Working Directory

**Always spawn from correct working directory to inherit project configs.**

```bash
# Option 1: Run from project root
cd /path/to/project
echo "prompt" | claude -p --tools default --permission-mode dontAsk 2>&1

# Option 2: Use subshell
(cd /path/to/project && echo "prompt" | claude -p --tools default --permission-mode dontAsk 2>&1)
```

**What sub-agents inherit:**
- `.claude/` directory (settings, commands, hooks, rules)
- `CLAUDE.md` (project guidelines)
- `.mcp.json` (MCP configs - limited, prefer global registration)
- Project files (git config, build files)

**See:** [MULTI-AGENT.md Part 4](https://jonnyzzz.com/MULTI-AGENT.md) for detailed working directory patterns.

---

## Parallel Execution

**See [MULTI-AGENT.md Part 7](https://jonnyzzz.com/MULTI-AGENT.md) for complete parallel execution patterns.**

### Quick Example

```bash
# Launch 3 agents IN PARALLEL
echo "Task 1" | claude -p --tools default --permission-mode dontAsk > /tmp/out1.txt 2>&1 &
echo "Task 2" | claude -p --tools default --permission-mode dontAsk > /tmp/out2.txt 2>&1 &
echo "Task 3" | claude -p --tools default --permission-mode dontAsk > /tmp/out3.txt 2>&1 &

# Wait for ALL
wait

# Collect results
cat /tmp/out*.txt
```

**Note:** Even with `--permission-mode dontAsk`, background jobs may trigger permission prompts. For truly non-interactive parallel execution within Claude Code, use the Task tool with multiple concurrent sub-agents.

---

## Automation Scripts

**See [MULTI-AGENT.md Part 8](https://jonnyzzz.com/MULTI-AGENT.md) for complete Python/bash templates.**

### Python with UV (Quick Example)

```python
#!/usr/bin/env python3
import subprocess
import asyncio
from pathlib import Path

async def run_claude_agent(prompt: str, output_file: Path) -> int:
    cmd = ["bash", "-c", f'echo "{prompt}" | claude -p --tools default --permission-mode dontAsk 2>&1']
    with output_file.open('w') as f:
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=f, stderr=subprocess.STDOUT)
        return await proc.wait()

async def main():
    tasks = [
        run_claude_agent("Task 1", Path("/tmp/out1.txt")),
        run_claude_agent("Task 2", Path("/tmp/out2.txt")),
        run_claude_agent("Task 3", Path("/tmp/out3.txt"))
    ]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
```

**Run:** `uv run script.py`

---

## CLI Comparison

**See [MULTI-AGENT.md Quick Reference](https://jonnyzzz.com/MULTI-AGENT.md) for detailed CLI comparison tables, including:**
- Feature comparison (interactive mode, file input, MCP support)
- Use case recommendations (when to use which CLI)
- Command pattern examples

**Quick Summary for Claude Code:**
- ✅ Best for: Web research, parallel workloads, cross-validation
- ✅ MCP Support: Playwright, IntelliJ (when registered)
- ✅ Built-in: WebSearch, WebFetch

---

## Quick Reference Card

```bash
# Basic execution
echo "<prompt>" | claude -p --tools default --permission-mode dontAsk 2>&1

# With prompt as argument
claude -p --tools default --permission-mode dontAsk "prompt" 2>&1

# JSON output
echo "prompt" | claude -p --tools default --permission-mode dontAsk --output-format json 2>&1

# Restricted tools (if needed)
echo "prompt" | claude -p --allowedTools "Read,Grep,Glob" --permission-mode dontAsk 2>&1

# PARALLEL (3 agents)
echo "Task 1" | claude -p --tools default --permission-mode dontAsk > /tmp/out1.txt 2>&1 &
echo "Task 2" | claude -p --tools default --permission-mode dontAsk > /tmp/out2.txt 2>&1 &
echo "Task 3" | claude -p --tools default --permission-mode dontAsk > /tmp/out3.txt 2>&1 &
wait
cat /tmp/out*.txt

# With timeout
timeout 300 bash -c 'echo "prompt" | claude -p --tools default --permission-mode dontAsk' 2>&1
```

---

## MCP Server Visibility (Advanced)

**Claude Code sub-agents INHERIT all registered MCP servers automatically.**

| MCP Server | Visibility | Registration |
|------------|-----------|--------------|
| Playwright | ✅ Auto-inherited | `claude mcp add playwright npx @playwright/mcp@latest` |
| IntelliJ MCP Steroid | ✅ Auto-inherited | `claude mcp add --transport http intellij-steroid <URL>` |
| Any Custom MCP | ✅ Auto-inherited | `claude mcp add <name> <command>` |

**Key:** MCP servers registered with `claude mcp add` are available to ALL Claude Code sessions, including sub-agents spawned with any command-line flags.

**Check registered MCPs:**
```bash
claude mcp list
```

**Register IntelliJ MCP:**
```bash
# IntelliJ writes MCP URL to ~/.*.mcp-steroid
cat ~/.*.mcp-steroid

# Register using URL from file
claude mcp add --transport http intellij-steroid <URL>
```

**See:** [MULTI-AGENT.md Part 3](https://jonnyzzz.com/MULTI-AGENT.md) for detailed MCP visibility matrix and task assignment guidelines.

---

## MCP Troubleshooting (Advanced)

### Common Issues

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Sub-agent doesn't see MCP tools | Not registered globally | `claude mcp add <name> <command>` |
| MCP listed but tools unavailable | Restrictive tool flags | Use `--tools default` instead of `--allowedTools` |
| IntelliJ MCP tools fail | IDE not running | Start IntelliJ, verify project open |
| MCP works in parent, not sub-agent | Local `.mcp.json` only | Register globally with `claude mcp add` |
| Playwright browser fails | MCP server not started | Check `claude mcp list`, restart if needed |
| Tools timeout immediately | MCP server crashed | Restart MCP server, check logs |

### Verify MCP Visibility in Sub-Agents

```bash
# Test if sub-agent sees registered MCPs
echo "List all available tools, especially MCP-provided ones" | \
  claude -p --tools default --permission-mode dontAsk 2>&1 | \
  grep -E "(playwright|intellij|steroid)"

# Expected: Should list MCP tools like browser_navigate, steroid_execute_code, etc.
```

### Important MCP Gotchas

**1. IntelliJ MCP Only Works While IDE Is Running**

IntelliJ MCP Steroid requires the IDE to be open with the MCP server running. If IntelliJ closes, all MCP tools become unavailable.

**2. Tool Restriction Flags Block MCP Access**

Using `--allowedTools` without listing MCP tools will block them:

```bash
# ❌ BAD: This blocks all MCP tools
echo "prompt" | claude -p --allowedTools "Read,Write,Grep" --permission-mode dontAsk 2>&1

# ✅ GOOD: Use --tools default to include all tools
echo "prompt" | claude -p --tools default --permission-mode dontAsk 2>&1
```

**3. IntelliJ MCP Operates on Currently Open Project**

IntelliJ MCP Steroid executes code in the context of the currently focused project in the IDE. If multiple projects are open, ensure the correct one has focus, or use the `project_name` parameter in MCP calls.

---

**For comprehensive patterns, see:**
- [MULTI-AGENT.md](https://jonnyzzz.com/MULTI-AGENT.md) - Orchestration, parallel execution, error handling
- [RLM.md](https://jonnyzzz.com/RLM.md) - Partition+Map+Reduce patterns
- [CODEX.md](https://jonnyzzz.com/CODEX.md) - Alternative CLI with IntelliJ MCP support
- [GEMINI.md](https://jonnyzzz.com/GEMINI.md) - Cross-validation with different model

*Follow [@jonnyzzz](https://twitter.com/jonnyzzz) on X and [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) for more on AI agents and developer tooling.*
