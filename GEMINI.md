# GEMINI.md - Using Gemini CLI as Sub-Agent

**Version:** v1.0.8
**Last Updated:** 2026-01-24

## Purpose

Spawn Gemini CLI as sub-agent for cross-validation and alternative perspectives. Gemini provides different model architecture for diverse reasoning.

### Quick Start

```bash
# ✅ RECOMMENDED: Use this command for 95% of use cases
gemini --approval-mode auto_edit "your prompt here" 2>&1
```

**Why this command:**
- `--approval-mode auto_edit`: Auto-approves file edits (required for non-interactive sub-agents)
- `2>&1`: Captures both stdout and stderr

**Prerequisites:** `GEMINI_API_KEY` must be set (see [API Key Configuration](#api-key-configuration-required) section)

**When to use alternatives:**
- YOLO mode (auto-approve everything): `--approval-mode yolo`
- JSON output: Add `-o json`
- Specific model: Add `-m model-name`

See [Core Commands](#core-commands) section for all options.

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
curl -O https://jonnyzzz.com/GEMINI.md
```

---

## Prerequisites

Before spawning Gemini sub-agents, complete these setup steps:

### 1. Install Gemini CLI

```bash
# Check if already installed
which gemini
# Expected: /opt/homebrew/bin/gemini (macOS) or similar

gemini --version
# Expected: 0.22.5 or newer
```

**If not installed:** Follow [Gemini CLI installation instructions](https://github.com/google/generative-ai-cli) for your platform.

### 2. Set API Key (REQUIRED)

```bash
# Get your API key from: https://makersuite.google.com/app/apikey

# Set environment variable
export GEMINI_API_KEY="your-api-key-here"

# Add to shell profile for persistence
echo 'export GEMINI_API_KEY="your-api-key"' >> ~/.bashrc  # or ~/.zshrc
source ~/.bashrc  # or source ~/.zshrc
```

### 2.1 Sandbox/CI Home Directory (Recommended in restricted environments)

If you see `EPERM` creating `~/.gemini/...`, set a writable Gemini home and
seed settings there:

```bash
# Redirect Gemini's home dir (uses ${GEMINI_CLI_HOME}/.gemini/)
export GEMINI_CLI_HOME="/path/to/writable/dir"
mkdir -p "$GEMINI_CLI_HOME/.gemini"

# Optional: disable usage stats + telemetry to avoid ClearcutLogger crashes
cat > "$GEMINI_CLI_HOME/.gemini/settings.json" <<'JSON'
{
  "privacy": { "usageStatisticsEnabled": false },
  "telemetry": { "enabled": false, "logPrompts": false }
}
JSON
```

Note: `GEMINI_CLI_HOME` is read at startup, so set it in the environment
before invoking `gemini`.

### 3. Verify Setup

```bash
# Check API key is set
echo "$GEMINI_API_KEY" | grep -q "." && echo "✅ API key set" || echo "❌ API key missing"

# Test execution
gemini --approval-mode auto_edit "echo Hello" 2>&1
# Should output "Hello"
```

**Common Issues:**
- **Exit code 41:** `GEMINI_API_KEY` not set → Run export command above
- **EPERM mkdir ~/.gemini/tmp/.../chats:** Set `GEMINI_CLI_HOME` to a writable directory (see Sandbox/CI section)
- **TypeError: Cannot read properties of undefined (reading 'model')** during startup → Disable usage stats in settings (`privacy.usageStatisticsEnabled: false`)
- **Rate limits:** Too many requests → Wait and retry or use different API key
- **Auth error:** Invalid API key → Get new key from MakerSuite
- **TypeError: fetch failed sending request:** Network/DNS blocked → confirm outbound access or set `HTTPS_PROXY`/`HTTP_PROXY`; enable `general.retryFetchErrors` in settings for transient failures

**You're ready!** Proceed to Quick Start command above.

---

## When to Use Gemini

### Ideal Use Cases

| Scenario | Why Gemini |
|----------|-----------|
| **Cross-Validation** | Different model provides second opinion |
| **Alternative Perspective** | Gemini may catch issues Claude/Codex miss |
| **Diversity in Review** | Multiple model architectures reduce blind spots |
| **Long-Context Tasks** | Gemini has large context window |
| **Non-MCP Tasks** | Good for pure code analysis without IDE integration |
| **Parallel Workloads** | Multiple instances run simultaneously |

### When NOT to Use

- **MCP-dependent tasks** - Gemini does NOT see MCP servers (use Codex or Claude instead)
- **IntelliJ IDE operations** - No MCP access (use Codex)
- **Browser automation** - No Playwright MCP (use Claude or Codex)
- Tasks requiring specific IDE or browser tools
- Simple edits not benefiting from cross-validation
- Tasks requiring conversation history access

---

## MCP Server Visibility

**Gemini does NOT integrate with MCP servers.**

| MCP Server | Visible to Gemini | Impact |
|------------|------------------|---------|
| Playwright | ❌ No | Cannot control browsers |
| IntelliJ MCP Steroid | ❌ No | Cannot use IDE operations |

**What Gemini HAS:**
- Native file system operations (read, write, search, glob)
- Web capabilities (search, fetch)
- Shell command execution
- Memory and cognition features

**Best Use:** Code review, analysis, validation tasks without IDE/browser integration.

**See:** [MULTI-AGENT.md Part 3](https://jonnyzzz.com/MULTI-AGENT.md) for detailed MCP visibility matrix.

---

## Installation & Setup

```bash
# Verify installation
which gemini
# Expected: /opt/homebrew/bin/gemini (macOS) or similar

# Check version
gemini --version
# Expected: 0.22.5 or newer
```

### API Key Configuration (REQUIRED)

Gemini CLI requires explicit API key:

```bash
# Check if API key is configured
echo $GEMINI_API_KEY

# If not set, export it
export GEMINI_API_KEY="your-api-key-here"
```

**Important for AI agents:** If `GEMINI_API_KEY` is not set, Gemini CLI fails with exit code 41. Verify environment variable exists or ask user to provide API key before spawning Gemini sub-agents.

**Get API key from:** https://makersuite.google.com/app/apikey

---

## Core Commands

### Recommended Pattern (Non-Interactive)

```bash
# Non-interactive execution (one-shot)
gemini --approval-mode auto_edit "your prompt here" 2>&1

# Interactive mode
gemini

# Execute prompt then continue interactively
gemini -i "initial prompt"

# With specific model
gemini -m model-name --approval-mode auto_edit "prompt" 2>&1
```

### Approval Modes

**Give sub-agents full access** - use auto-approve for non-interactive execution.

```bash
# Auto-approve edits (RECOMMENDED for sub-agents)
gemini --approval-mode auto_edit "prompt" 2>&1

# YOLO mode - auto-approve everything (for trusted tasks)
gemini --approval-mode yolo "prompt" 2>&1
# Alias: gemini -y "prompt"

# Default - prompts for approval (not suitable for sub-agents)
gemini "prompt" 2>&1
```

### Output Formats

```bash
# Plain text output (default)
gemini --approval-mode auto_edit "prompt" 2>&1

# JSON output (for parsing)
gemini -o json --approval-mode auto_edit "prompt" 2>&1

# Streaming JSON
gemini -o stream-json --approval-mode auto_edit "prompt" 2>&1
```

---

## Working Directory

**Spawn from correct working directory to access project configs.**

```bash
# Option 1: Run from project root
cd /path/to/project
gemini --approval-mode auto_edit "prompt" 2>&1

# Option 2: Use subshell
(cd /path/to/project && gemini --approval-mode auto_edit "prompt" 2>&1)
```

**What Gemini can access:**
- Project files - Build configs, git settings, documentation
- AI guidelines - GEMINI.md, CLAUDE.md, .ai/ directory
- `.mcp.json` - Can read but doesn't use MCP servers
- File structure - Inherits current directory

**See:** [MULTI-AGENT.md Part 4](https://jonnyzzz.com/MULTI-AGENT.md) for detailed working directory patterns.

---

## File Content in Prompts

Gemini doesn't have `-i` flag like Codex. Include file content in prompt:

```bash
# Read file content and pass to Gemini
CONTENT=$(cat /path/to/file.md)
gemini --approval-mode auto_edit "Analyze this content:

$CONTENT

Tasks:
1. Review for accuracy
2. Identify gaps
3. Suggest improvements" 2>&1
```

---

## Automation Scripts

**See [MULTI-AGENT.md Part 8](https://jonnyzzz.com/MULTI-AGENT.md) for complete Python/bash templates.**

### Quick Python Example

```python
#!/usr/bin/env python3
import subprocess
import asyncio
import os
from pathlib import Path

async def run_gemini_agent(prompt: str, output_file: Path) -> int:
    # Ensure GEMINI_API_KEY is set
    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY not set")

    cmd = ["gemini", "--approval-mode", "auto_edit", prompt]
    with output_file.open('w') as f:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=f, stderr=subprocess.STDOUT
        )
        return await proc.wait()

async def main():
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not set")
        return

    tasks = [
        run_gemini_agent("Task 1", Path("/tmp/out1.txt")),
        run_gemini_agent("Task 2", Path("/tmp/out2.txt")),
        run_gemini_agent("Task 3", Path("/tmp/out3.txt"))
    ]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
```

**Run:** `uv run script.py`

---

## Error Handling

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `command not found` | Gemini not installed | Install via official instructions |
| Exit code 41 | `GEMINI_API_KEY` not set | `export GEMINI_API_KEY="key"` |
| `EPERM mkdir ~/.gemini/tmp/.../chats` | Home dir not writable | Set `GEMINI_CLI_HOME` to a writable dir and create `${GEMINI_CLI_HOME}/.gemini` |
| `TypeError: Cannot read properties of undefined (reading 'model')` | Usage stats init issue | Set `privacy.usageStatisticsEnabled: false` in settings |
| Timeout | Task too complex | Break into smaller sub-tasks |
| Rate limit | Too many requests | Add delays between calls |
| Auth error | Invalid API key | Re-authenticate with `gemini login` |
| `TypeError: fetch failed sending request` | Network/DNS blocked | Verify outbound access or set `HTTPS_PROXY`/`HTTP_PROXY`; enable `general.retryFetchErrors` |

**See [MULTI-AGENT.md Part 9](https://jonnyzzz.com/MULTI-AGENT.md) for complete error handling patterns.**

### API Key Validation

```bash
# Verify API key is set
if [ -z "${GEMINI_API_KEY:-}" ]; then
    echo "ERROR: GEMINI_API_KEY not set"
    echo "Get key from: https://makersuite.google.com/app/apikey"
    echo "Set it: export GEMINI_API_KEY='your-key'"
    exit 1
fi
```

---

## CLI Comparison

**See [MULTI-AGENT.md Quick Reference](https://jonnyzzz.com/MULTI-AGENT.md) for detailed CLI comparison tables, including:**
- Feature comparison (interactive mode, file input, MCP support)
- Use case recommendations (when to use which CLI)
- Command pattern examples

**Quick Summary for Gemini:**
- ✅ Best for: Cross-validation, long context tasks, pure code analysis
- ❌ MCP Support: None (no Playwright, no IntelliJ MCP)
- ✅ Alternative model: Different architecture provides diverse reasoning

---

## Quick Reference Card

```bash
# Basic execution
gemini --approval-mode auto_edit "prompt" 2>&1

# With model selection
gemini -m model-name --approval-mode auto_edit "prompt" 2>&1

# Auto-approve edits
gemini --approval-mode auto_edit "prompt" 2>&1

# YOLO mode (auto-approve everything)
gemini --approval-mode yolo "prompt" 2>&1

# JSON output
gemini -o json --approval-mode auto_edit "prompt" 2>&1

# With file content
CONTENT=$(cat file.md)
gemini --approval-mode auto_edit "Analyze: $CONTENT" 2>&1

# Capture output to file
gemini --approval-mode auto_edit "prompt" > output.txt 2>&1

# PARALLEL (3 agents)
gemini --approval-mode auto_edit "Task 1" > /tmp/out1.txt 2>&1 &
gemini --approval-mode auto_edit "Task 2" > /tmp/out2.txt 2>&1 &
gemini --approval-mode auto_edit "Task 3" > /tmp/out3.txt 2>&1 &
wait
cat /tmp/out*.txt

# With timeout (macOS: use `gtimeout` from coreutils or a Python wrapper)
timeout 300 gemini --approval-mode auto_edit "prompt" 2>&1

# API key check
[ -z "$GEMINI_API_KEY" ] && echo "ERROR: Set GEMINI_API_KEY" || echo "OK"
```

---

**For comprehensive patterns, see:**
- [MULTI-AGENT.md](https://jonnyzzz.com/MULTI-AGENT.md) - Orchestration, parallel execution, error handling
- [RLM.md](https://jonnyzzz.com/RLM.md) - Partition+Map+Reduce patterns
- [CLAUDE-CODE.md](https://jonnyzzz.com/CLAUDE-CODE.md) - Alternative CLI for web research
- [CODEX.md](https://jonnyzzz.com/CODEX.md) - Alternative CLI with full MCP access

*Follow [@jonnyzzz](https://twitter.com/jonnyzzz) on X and [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) for more on AI agents and developer tooling.*
