# CODEX.md - Using Codex CLI as Sub-Agent

**Version:** v1.0.8
**Last Updated:** 2026-01-24

## Purpose

Spawn Codex CLI as sub-agent for non-interactive, focused work on files with full MCP access (IntelliJ IDE, Playwright, etc.).

### Quick Start

```bash
# ✅ RECOMMENDED: Use this command for 95% of use cases
codex --full-auto exec "your prompt here" 2>&1
```

**This is the ONE command you need.** Don't use alternative flag combinations unless you have a specific reason.

**Why this command:**
- `--full-auto`: Convenience flag that enables auto-approval and sandboxing in one flag
- `exec`: Non-interactive execution mode
- `2>&1`: Captures both stdout and stderr

**Common variations (just add to the command above):**
- Different project: `codex -C /path/to/project --full-auto exec "prompt" 2>&1`
- Specific model: `codex --full-auto -m gpt-5.2-codex exec "prompt" 2>&1`
- Multiple workspaces: `codex --full-auto --add-dir /path/to/other exec "prompt" 2>&1`

See [Core Commands](#core-commands) section for advanced options and alternatives.

**See [MULTI-AGENT.md](https://jonnyzzz.com/MULTI-AGENT.md) for:**
- When to use multi-agent orchestration
- Parallel execution patterns
- Error handling and retry logic
- Python/bash automation scripts
- Prompt engineering templates
- Cross-validation patterns

**RECOMMENDED:** Fetch documentation locally for faster sub-agent access:
```bash
curl -O https://jonnyzzz.com/RLM.md
curl -O https://jonnyzzz.com/MULTI-AGENT.md
curl -O https://jonnyzzz.com/CODEX.md
```

---

## When to Use Codex

### Ideal Use Cases

| Scenario | Why Codex |
|----------|-----------|
| **IntelliJ IDE Operations** | ✅ Full access to IntelliJ MCP Steroid (when registered) |
| **Image/PDF Analysis** | Native `-i` flag support |
| **Focused Code Review** | Non-interactive `review` mode |
| **Large File Processing** | Works independently without context rot |
| **Parallel Workloads** | Multiple instances run simultaneously |
| **Full MCP Access** | Sees all registered MCP servers |

### When NOT to Use

- Interactive debugging requiring back-and-forth
- Tasks needing conversation history access
- Simple edits doable directly

---

## Prerequisites

Before spawning Codex sub-agents, complete these setup steps:

### 1. Install Codex CLI

```bash
# Install via npm (if not already installed)
npm install -g @openai/codex-cli
```

### 2. Authenticate (REQUIRED)

```bash
# Authenticate with OpenAI
codex login
# Opens browser for authentication

# Verify auth.json was created
ls ~/.codex/auth.json
# Should show file exists
```

**Important:** Without authentication, Codex will fail with "failed to refresh available models" error.

### 3. Verify Installation

```bash
codex --version
# Expected: v0.88.0 or newer

# Test with simple command
codex --full-auto exec "echo Hello" 2>&1
# Should output "Hello"
```

### 4. Optional: Register MCP Servers

```bash
# Check registered MCP servers
codex mcp list

# Register MCP servers if needed (see MCP Server Visibility section below)
```

**Troubleshooting:**
- **Auth fails:** Run `codex login` again or check OpenAI account status
- **Command not found:** Verify npm global bin directory is in PATH
- **Nested execution issues:** See [Nested Execution](#nested-execution-codex-spawning-codex) section

**You're ready!** Proceed to Quick Start command above.

---

## MCP Server Visibility

**Codex sub-agents INHERIT all registered MCP servers automatically.**

| MCP Server | Visibility | Registration |
|------------|-----------|--------------|
| Playwright | ✅ Auto-inherited | `codex mcp add playwright npx "@playwright/mcp@latest"` |
| IntelliJ MCP Steroid | ✅ Auto-inherited | `codex mcp add intellij --url <URL>` |
| Any Custom MCP | ✅ Auto-inherited | `codex mcp add <name> <command>` |

**Key:** MCP servers registered with `codex mcp add` are available to ALL Codex sessions, including sub-agents.

**Check registered MCPs:**
```bash
codex mcp list
```

**Register IntelliJ MCP:**
```bash
# IntelliJ writes MCP URL to ~/.*.mcp-steroid
cat ~/.*.mcp-steroid

# Register using URL from file
codex mcp add intellij --url <URL>
```

**See:** [MULTI-AGENT.md Part 3](https://jonnyzzz.com/MULTI-AGENT.md) for detailed MCP visibility matrix.

---

## Installation & Setup

```bash
# Verify installation
which codex
# Expected: /opt/homebrew/bin/codex (macOS) or similar

# Check available commands
codex --help

# Check exec command options
codex exec --help
```

---

## Core Commands

### Recommended Pattern (Non-Interactive)

```bash
# RECOMMENDED: Low-friction auto mode
codex --full-auto exec "your prompt here" 2>&1

# Fully autonomous (no approval prompts; sandboxed)
codex -a never --sandbox workspace-write exec "your prompt here" 2>&1

# With output capture to file
codex --full-auto exec "prompt" > /tmp/codex-output.txt 2>&1

# Stream JSON events (machine-readable logs)
codex --full-auto --json exec "prompt" 2>&1

# Code review mode
codex --full-auto review "review instructions" 2>&1

# With model selection
codex --full-auto -m gpt-5.2-codex exec "prompt" 2>&1
```

### Stdin Input with Heredoc

```bash
cat <<'PROMPT' | codex --full-auto exec
Your multi-line prompt here.

Can include variable references and complex formatting.
PROMPT
```

### Sandbox Modes

```bash
# Recommended for sub-agents: Full-auto mode
codex --full-auto exec "prompt" 2>&1

# Explicit workspace-write sandbox
codex -a never -s workspace-write exec "prompt" 2>&1

# No sandbox (requires external sandboxing)
codex -a never -s never exec "prompt" 2>&1
```

### Image Input

```bash
# Single image
codex --full-auto -i screenshot.png exec "Analyze this image" 2>&1

# Multiple images
codex --full-auto -i screen1.png -i screen2.jpg exec "Compare these" 2>&1

# PDFs: convert to text first
pdftotext report.pdf /tmp/report.txt
codex --full-auto exec "Read /tmp/report.txt and summarize" 2>&1
```

---

## Working Directory

**Use -C flag to specify working directory for config inheritance.**

```bash
# Use -C flag to specify working directory
codex -C /path/to/project --full-auto exec "prompt" 2>&1

# With additional directories
codex -C /path/to/project --add-dir /path/to/other --full-auto exec "prompt" 2>&1

# From subshell (alternative)
(cd /path/to/project && codex --full-auto exec "prompt" 2>&1)
```

**What sub-agents inherit:**
- `.mcp.json` - MCP server configurations (FULL visibility)
- Project configs - Build files, git settings
- Skills - Project-specific and global
- AGENTS instructions (if present)

**See:** [MULTI-AGENT.md Part 4](https://jonnyzzz.com/MULTI-AGENT.md) for detailed working directory patterns.

---

## Nested Execution (Codex spawning Codex)

**When running Codex from within Codex, use HOME workaround to avoid permission errors.**

### HOME Directory Workaround (RECOMMENDED)

```bash
# Create temporary home directory
TMP_HOME=/tmp/codex-home
mkdir -p "$TMP_HOME/.codex"

# Copy authentication (required)
cp ~/.codex/auth.json "$TMP_HOME/.codex/"

# Optional: copy config
cp ~/.codex/config.toml "$TMP_HOME/.codex/" 2>/dev/null || true

# Run Codex with redirected HOME
HOME="$TMP_HOME" codex --full-auto exec "your prompt here" 2>&1
```

**When is this needed?**
- Running Codex sub-agents from within a Codex agent
- Running from Docker containers or restricted environments
- Any scenario where `~/.codex/` is not writable
- When you see "Operation not permitted" errors

---

## Automation Scripts

**See [MULTI-AGENT.md Part 8](https://jonnyzzz.com/MULTI-AGENT.md) for complete Python/bash templates.**

### Quick Python Example

```python
#!/usr/bin/env python3
import subprocess
import asyncio
from pathlib import Path

async def run_codex_agent(prompt: str, output_file: Path, repo_path: str = ".") -> int:
    cmd = ["codex", "-C", repo_path, "--full-auto", "exec", prompt]
    with output_file.open('w') as f:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=f, stderr=subprocess.STDOUT
        )
        return await proc.wait()

async def main():
    tasks = [
        run_codex_agent("Task 1", Path("/tmp/out1.txt"), "/path/to/project"),
        run_codex_agent("Task 2", Path("/tmp/out2.txt"), "/path/to/project"),
        run_codex_agent("Task 3", Path("/tmp/out3.txt"), "/path/to/project")
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

**Quick Summary for Codex:**
- ✅ Best for: IntelliJ IDE operations, image/PDF analysis, focused non-interactive tasks
- ✅ MCP Support: Playwright, IntelliJ (when registered)
- ✅ Native Support: `-i` flag for images/PDFs, `review` mode

---

## Quick Reference Card

```bash
# RECOMMENDED: Low-friction auto mode
codex --full-auto exec "prompt" 2>&1

# Basic non-interactive execution
codex -a never --sandbox workspace-write exec "prompt" 2>&1

# With working directory
codex -C /path/to/project --full-auto exec "prompt" 2>&1

# With output capture
codex --full-auto exec "prompt" > /tmp/output.txt 2>&1

# Stream JSON
codex --full-auto --json exec "prompt" 2>&1

# With stdin heredoc
cat <<'EOF' | codex --full-auto exec
Multi-line prompt here
EOF

# With image input
codex --full-auto -i screenshot.png exec "prompt" 2>&1

# Code review mode
codex --full-auto review "review instructions" 2>&1

# PARALLEL (3 agents)
codex --full-auto exec "Task 1" > /tmp/out1.txt 2>&1 &
codex --full-auto exec "Task 2" > /tmp/out2.txt 2>&1 &
codex --full-auto exec "Task 3" > /tmp/out3.txt 2>&1 &
wait
cat /tmp/out*.txt

# Nested execution (Codex from Codex)
TMP_HOME=/tmp/codex-home
mkdir -p "$TMP_HOME/.codex"
cp ~/.codex/auth.json "$TMP_HOME/.codex/"
HOME="$TMP_HOME" codex --full-auto exec "prompt" 2>&1
```

---

**For comprehensive patterns, see:**
- [MULTI-AGENT.md](https://jonnyzzz.com/MULTI-AGENT.md) - Orchestration, parallel execution, error handling
- [RLM.md](https://jonnyzzz.com/RLM.md) - Partition+Map+Reduce patterns
- [CLAUDE-CODE.md](https://jonnyzzz.com/CLAUDE-CODE.md) - Alternative CLI for web research
- [GEMINI.md](https://jonnyzzz.com/GEMINI.md) - Cross-validation with different model

*Follow [@jonnyzzz](https://twitter.com/jonnyzzz) on X and [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) for more on AI agents and developer tooling.*
