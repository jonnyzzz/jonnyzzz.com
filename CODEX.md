# CODEX.md - Using Codex CLI as Sub-Agent

## Purpose

This document instructs AI agents (Claude Code, Junie, etc.) on how to spawn Codex CLI as a sub-agent for specialized tasks. Codex excels at non-interactive, focused work on files with explicit prompts.

---

## When to Use Codex as Sub-Agent

### Ideal Use Cases

| Scenario | Why Codex |
|----------|-----------|
| **IntelliJ IDE Operations** | ✅ Sees IntelliJ MCP Steroid when registered |
| **Image Analysis (png/jpg)** | Codex handles image input with `-i` flag |
| **Focused Code Review** | Non-interactive `review` mode for specific files |
| **Large File Processing** | Codex can work independently without context rot |
| **Parallel Workloads** | Multiple Codex instances can run simultaneously |
| **Cross-Validation** | Different AI agent provides second opinion |
| **Full MCP Access** | Sees registered MCP servers (Playwright, IntelliJ MCP, etc.) |

### When NOT to Use Codex

- Interactive debugging requiring back-and-forth
- Tasks needing access to conversation history
- Simple edits that Claude Code can do directly

### ✅ MCP Server Visibility

**VERIFIED:** Codex sub-agents INHERIT all registered MCP servers automatically.

| MCP Server | Visibility | Requirements |
|------------|-----------|--------------|
| Playwright | ✅ Auto-inherited | `codex mcp add playwright npx "@playwright/mcp@latest"` |
| IntelliJ MCP Steroid | ✅ Auto-inherited | `codex mcp add intellij --url <URL>` |
| Any Custom MCP | ✅ Auto-inherited | Register once with `codex mcp add` |

**Key insight:** MCP servers registered with `codex mcp add` are available to ALL Codex sessions, including sub-agents spawned with any command-line flags.

**To check registered MCPs:**
```bash
codex mcp list
```

**To register IntelliJ MCP Steroid:**
```bash
# IntelliJ writes the MCP server URL to a file in your home directory
# Find the file (named after the IntelliJ process ID)
cat ~/.*.mcp-steroid

# Use the URL from that file to register
codex mcp add intellij --url <URL-from-file>

# Verify it's connected
codex mcp list
```

---

## Codex CLI Reference

### Installation Check

```bash
# Verify Codex is available
which codex
# Expected: /opt/homebrew/bin/codex (macOS) or similar

# Check available commands
codex --help

# Check exec command options
codex exec --help
```

### Core Commands

```bash
# RECOMMENDED: Minimal non-interactive run with full parameters
codex -a never -s workspace-write -C /path/to/repo --add-dir /path/to/other/repo exec -m gpt-5.2-codex

# RECOMMENDED: Low-friction auto mode (alias for -a on-request --sandbox workspace-write)
codex --full-auto exec "your prompt here" 2>&1

# Fully autonomous (no approval prompts; sandboxed)
codex -a never --sandbox workspace-write exec "your prompt here" 2>&1

# With output capture to file (use shell redirection)
codex -a never --sandbox workspace-write exec "prompt" > /tmp/codex-output.txt 2>&1

# Stream JSON events (machine-readable logs)
codex -a never --sandbox workspace-write --json exec "prompt" 2>&1

# Code review mode
codex -a never --sandbox workspace-write review "review instructions" 2>&1

# With model selection
codex -a never --sandbox workspace-write -m gpt-5.2-codex exec "prompt" 2>&1
```

### Stdin Input with Heredoc

```bash
cat <<'PROMPT' | codex -a never -s workspace-write -C /path/to/repo exec -m gpt-5.2-codex
Your multi-line prompt here.

Can include variable references and complex formatting.
PROMPT

# Shorter heredoc pattern
cat <<'EOF' | codex --full-auto exec
Task description here
EOF
```

### Performance and Config Notes

- **Give sub-agents full access** - don't restrict capabilities unnecessarily.
- Codex reads defaults from `~/.codex/config.toml` (for example `model`).
- Prefer defaults unless you have a concrete reason to override config.
- Avoid setting `reasoning_effort` explicitly; if a task is slow, increase command timeout or split prompts instead.
- If you rely on MCP servers or skills configured in config, avoid feature disables and use `--search` when you need web search.
- For extra workspace access (cross-repo work), add writable roots explicitly:

```bash
codex --full-auto --add-dir /path/to/other/repo exec "prompt" 2>&1
```

- Full access only if the environment is already externally sandboxed:

```bash
codex --dangerously-bypass-approvals-and-sandbox exec "prompt" 2>&1
```

- Startup logs may show MCP servers initializing; factor that into timeouts.
- If Codex timeouts on large repos, run tasks sequentially and use a longer timeout (for example `gtimeout 900 codex -a never --sandbox workspace-write exec ...`).

### Sandbox Parameters (Detailed)

Codex provides multiple sandbox-related flags for controlling execution security and permissions:

#### Available Sandbox Flags

| Flag | Description |
|------|-------------|
| `-s, --sandbox <MODE>` | Select sandbox policy (e.g., `workspace-write`, `never`) |
| `--full-auto` | **Recommended:** Low-friction sandboxed auto-execution (alias for `-a on-request -s workspace-write`) |
| `--dangerously-bypass-approvals-and-sandbox` | Skip ALL confirmations and sandboxing (DANGEROUS - testing only) |
| `-c 'sandbox_permissions=[...]'` | Configure specific sandbox permissions |

#### Sandbox Modes

```bash
# Recommended for sub-agents: Full-auto mode
codex --full-auto exec "prompt" 2>&1

# Explicit workspace-write sandbox
codex -a never -s workspace-write exec "prompt" 2>&1

# No sandbox (requires external sandboxing)
codex -a never -s never exec "prompt" 2>&1
```

#### Advanced: Custom Sandbox Permissions

```bash
# Grant disk-full-read-access
codex -c 'sandbox_permissions=["disk-full-read-access"]' --full-auto exec "prompt" 2>&1

# Multiple permissions
codex -c 'sandbox_permissions=["disk-full-read-access", "network-access"]' --full-auto exec "prompt" 2>&1
```

### Sandbox Limitations and Nested Execution

**IMPORTANT:** When running Codex sub-agents from within a Codex session, you may encounter permission errors accessing `~/.codex/sessions`:

```
Error: Fatal error: Codex cannot access session files at ~/.codex/sessions
(permission denied)
```

**Cause:** Parent Codex session's sandbox restricts writes to `~/.codex/` directory.

**Solution 1: HOME Directory Workaround** (Recommended)

```bash
# Create temporary home directory for nested Codex sessions
TMP_HOME=/tmp/codex-home
mkdir -p "$TMP_HOME/.codex"

# Copy authentication (required for API access)
cp ~/.codex/auth.json "$TMP_HOME/.codex/"

# Optional: copy config to preserve settings
cp ~/.codex/config.toml "$TMP_HOME/.codex/" 2>/dev/null || true

# Run Codex with redirected HOME
HOME="$TMP_HOME" codex --full-auto exec "your prompt here" 2>&1
```

**Solution 2: Dangerous Bypass** (Testing only)

```bash
# ONLY for isolated testing environments
codex --dangerously-bypass-approvals-and-sandbox exec "prompt" 2>&1
```

**When is HOME workaround needed?**
- Running Codex sub-agents from within a Codex agent (nested execution)
- Running from Docker containers or restricted environments
- Any scenario where `~/.codex/` is not writable
- When you see "Operation not permitted" errors

### Image Input

```bash
# Single image
codex -a never --sandbox workspace-write -i screenshot.png exec "Analyze this image" 2>&1

# Multiple images
codex -a never --sandbox workspace-write -i screen1.png -i screen2.jpg exec "Compare these" 2>&1

# PDFs: convert to text or images first (pdftotext/pdftoppm), then analyze
pdftotext report.pdf /tmp/report.txt
codex -a never --sandbox workspace-write exec "Read /tmp/report.txt and summarize the key findings." 2>&1
```

---

## Working Directory Requirements

**IMPORTANT:** Always spawn Codex sub-agents from the correct working directory to inherit project-specific configurations and MCP servers.

### Why Working Directory Matters

Codex inherits configuration from:
1. **`.mcp.json`** - MCP server configurations (FULL visibility - both Playwright and IntelliJ!)
2. **Project configs** - Build files, git settings, editor configs
3. **Skills** - Project-specific and global skills
4. **AGENTS instructions** - If present in parent session

### Recommended Pattern with -C Flag

```bash
# Use -C flag to specify working directory
codex -C /path/to/project --full-auto exec "prompt" 2>&1

# With additional directories
codex -C /path/to/project --add-dir /path/to/other --full-auto exec "prompt" 2>&1

# From subshell (alternative)
(cd /path/to/project && codex --full-auto exec "prompt" 2>&1)
```

### Verification

Test that Codex sees project configs and MCP servers:

```bash
codex -C /path/to/project --full-auto exec "What is your current working directory? What MCP servers are available? What config files do you see?" 2>&1
```

**Expected output:**
- Working directory: `/path/to/project`
- Config files: `.mcp.json`, build files, etc.
- MCP servers: **BOTH Playwright AND IntelliJ MCP Steroid** ✅

---

## Spawning Codex from Claude Code

### Basic Pattern

```bash
# From Claude Code, use Bash tool:
codex -a never --sandbox workspace-write exec "Your detailed prompt here" 2>&1
```

### With File Context

```bash
# Point Codex at files to read (Codex will read them via tools)
codex -a never --sandbox workspace-write exec "Read /path/to/file.md and output:
1. Key concepts
2. Implementation patterns
3. Recommended improvements for TARGET_FILE.md" 2>&1
```

### Capturing Output

```bash
# Capture all output with shell redirection
codex -a never --sandbox workspace-write exec "prompt" > /tmp/codex-output.txt 2>&1

# Then read the output
cat /tmp/codex-output.txt

# Filter for just the result (if JSON output is needed)
codex -a never --sandbox workspace-write --json exec "prompt" 2>&1 | tee /tmp/codex-output.txt
```

---

## Automation with Python UV and Bash Scripts

### Using Python with UV

```python
#!/usr/bin/env python3
"""Example: Parallel Codex sub-agents with Python UV"""
import subprocess
import asyncio
from pathlib import Path

async def run_codex_agent(
    prompt: str,
    output_file: Path,
    repo_path: str = ".",
    model: str = "gpt-5.2-codex"
) -> int:
    """Run Codex sub-agent and capture output."""
    cmd = [
        "codex",
        "-a", "never",
        "-s", "workspace-write",
        "-C", repo_path,
        "exec",
        "-m", model
    ]

    with output_file.open('w') as f:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=subprocess.PIPE,
            stdout=f,
            stderr=subprocess.STDOUT
        )

        await proc.communicate(input=prompt.encode())
        return proc.returncode

async def main():
    """Launch 3 Codex agents in parallel."""
    repo = "/Users/jonnyzzz/Work/jonnyzzz.com-src"

    tasks = [
        run_codex_agent(
            "Read CLAUDE.md and extract key technologies",
            Path("/tmp/codex-out1.txt"),
            repo
        ),
        run_codex_agent(
            "Read RLM.md and summarize main concepts",
            Path("/tmp/codex-out2.txt"),
            repo
        ),
        run_codex_agent(
            "Read SKILL.md and identify writing patterns",
            Path("/tmp/codex-out3.txt"),
            repo
        )
    ]

    results = await asyncio.gather(*tasks)
    print(f"All agents completed with codes: {results}")

    # Aggregate results
    for i in range(1, 4):
        print(f"\n=== Agent {i} Output ===")
        print(Path(f"/tmp/codex-out{i}.txt").read_text())

if __name__ == "__main__":
    asyncio.run(main())
```

### Bash Script Template

```bash
#!/usr/bin/env bash
# run-parallel-codex-agents.sh
# Launch multiple Codex sub-agents in parallel

set -euo pipefail

# Configuration
REPO_PATH="/Users/jonnyzzz/Work/jonnyzzz.com-src"
OUTPUT_DIR="/tmp/codex-agents"
TIMEOUT_SEC=300
MODEL="gpt-5.2-codex"

# Tasks array
declare -a TASKS=(
    "Read CLAUDE.md and extract Docker configuration"
    "Read RLM.md and identify partition strategies"
    "Read SKILL.md and summarize writing style"
)

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Launch agents in parallel
echo "=== Launching ${#TASKS[@]} Codex agents in parallel ==="
pids=()

for i in "${!TASKS[@]}"; do
    task="${TASKS[$i]}"
    output_file="$OUTPUT_DIR/agent-$((i+1)).txt"

    echo "Starting agent $((i+1)): ${task:0:50}..."

    # Launch in background with timeout protection
    (
        timeout "$TIMEOUT_SEC" bash -c \
            "echo \"$task\" | codex -a never -s workspace-write -C \"$REPO_PATH\" \
             exec -m \"$MODEL\" > \"$output_file\" 2>&1"
    ) &
    pids+=($!)
done

# Wait for all agents
echo "Waiting for all agents to complete..."
for pid in "${pids[@]}"; do
    wait "$pid" && echo "Agent $pid completed successfully" || echo "Agent $pid failed"
done

# Aggregate results
echo ""
echo "=== Aggregated Results ==="
for i in $(seq 1 ${#TASKS[@]}); do
    echo ""
    echo "--- Agent $i ---"
    cat "$OUTPUT_DIR/agent-$i.txt"
done

echo ""
echo "=== Execution Complete ==="
echo "Individual outputs saved to: $OUTPUT_DIR"
```

Make executable with: `chmod +x run-parallel-codex-agents.sh`

---

## Prompt Engineering for Codex Sub-Agents

### Structure Template

```
CONTEXT:
[Brief description of the overall task]

INPUT FILES:
[Paths Codex should read]

IMAGE INPUTS:
[List images passed with -i, if any]

TASK:
[Specific, actionable instructions]

OUTPUT FORMAT:
[Exactly what format you expect]

CONSTRAINTS:
[Any limitations or requirements]
```

### Example: PDF Analysis for Documentation Improvement

```bash
pdftotext paper.pdf /tmp/paper.txt
codex -a never --sandbox workspace-write exec "CONTEXT:
We are improving RLM.md documentation based on the original research paper.

INPUT FILES:
- /tmp/paper.txt: Extracted text from the original PDF

TASK:
Read /tmp/paper.txt and:
1. Extract key concepts not currently in our documentation
2. Identify implementation details we may have missed
3. Find specific examples or benchmarks worth adding
4. Note any corrections needed for accuracy

OUTPUT FORMAT:
## Missing Concepts
- Concept 1: description
- Concept 2: description

## Implementation Details
- Detail 1: explanation
- Detail 2: explanation

## Recommended Additions
- Section: specific content to add

## Corrections
- Current text: corrected text

CONSTRAINTS:
- Focus on actionable improvements
- Reference specific page numbers when possible
- Keep suggestions concrete and implementable" 2>&1
```

---

## Parallel Execution (CRITICAL)

**Always run independent Codex sub-agents in parallel** for maximum throughput. Each instance runs in isolation with its own context.

### From Bash (Background Jobs)

```bash
# Launch multiple Codex instances IN PARALLEL
codex -a never --sandbox workspace-write exec "Read /tmp/task1.txt and do Task 1" > /tmp/out1.txt 2>&1 &
codex -a never --sandbox workspace-write exec "Read /tmp/task2.txt and do Task 2" > /tmp/out2.txt 2>&1 &
codex -a never --sandbox workspace-write exec "Read /tmp/task3.txt and do Task 3" > /tmp/out3.txt 2>&1 &

# Wait for ALL to complete
wait

# Collect and combine results
cat /tmp/out1.txt /tmp/out2.txt /tmp/out3.txt
```

### With Timeout Protection

```bash
# Run parallel tasks with timeout (macOS: use gtimeout from coreutils)
timeout 300 codex -a never --sandbox workspace-write exec "Task 1" > /tmp/out1.txt 2>&1 &
timeout 300 codex -a never --sandbox workspace-write exec "Task 2" > /tmp/out2.txt 2>&1 &
timeout 300 codex -a never --sandbox workspace-write exec "Task 3" > /tmp/out3.txt 2>&1 &
wait
```

### Parallel Map Pattern

```bash
# Process multiple files in parallel
for file in src/module1.ts src/module2.ts src/module3.ts; do
  codex -a never --sandbox workspace-write exec "Read $file and identify potential issues" > "/tmp/analysis-$(basename $file).txt" 2>&1 &
done
wait

# Aggregate results
cat /tmp/analysis-*.txt
```

---

## Integration with RLM Methodology

### Partition+Map+Reduce Pattern

```bash
# Step 1: PARTITION (orchestrating agent splits the work)
# Create task descriptions for each chunk

# Step 2: MAP (Codex sub-agents process IN PARALLEL)
codex -a never --sandbox workspace-write exec "Process chunk 1: $CHUNK1_DESCRIPTION" > /tmp/result1.txt 2>&1 &
codex -a never --sandbox workspace-write exec "Process chunk 2: $CHUNK2_DESCRIPTION" > /tmp/result2.txt 2>&1 &
codex -a never --sandbox workspace-write exec "Process chunk 3: $CHUNK3_DESCRIPTION" > /tmp/result3.txt 2>&1 &
wait

# Step 3: REDUCE (orchestrating agent aggregates results)
# Read /tmp/result*.txt and synthesize final output
```

### Cross-Validation Pattern

```bash
# Primary analysis done by main agent
# Validate with Codex sub-agent:
codex -a never --sandbox workspace-write exec "Read /tmp/primary-analysis.md and review for:
1. Logical consistency
2. Missing edge cases
3. Incorrect assumptions
4. Factual errors

Output only issues found, or 'VALIDATED: No issues found' if none." 2>&1
```

---

## Error Handling

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `command not found` | Codex not installed | Install via official instructions |
| `timeout` | Task too complex | Break into smaller sub-tasks |
| `context length exceeded` | Input too large | Use Peek strategy first |
| `rate limit` | Too many requests | Add delays between calls |

### Robust Execution Pattern

```bash
# With timeout and retry logic
MAX_RETRIES=3
RETRY_COUNT=0
TIMEOUT_SEC=300

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  if timeout $TIMEOUT_SEC codex -a never --sandbox workspace-write exec "prompt" 2>&1; then
    break
  fi
  RETRY_COUNT=$((RETRY_COUNT + 1))
  echo "Retry $RETRY_COUNT of $MAX_RETRIES..."
  sleep 5
done
```

---

## Comparing CLI Tools

### Feature Comparison

| Feature | Claude Code | Codex | Gemini |
|---------|-------------|-------|--------|
| Interactive mode | ✓ | ✓ | ✓ |
| Non-interactive | `claude -p` | `codex exec` | `gemini` one-shot |
| File input | Read tool | `-i` flag | via prompt |
| Image/PDF support | Read tool | `-i` flag | via prompt |
| Model selection | in settings | `-m` flag | `-m` flag |
| Parallel execution | background jobs | background jobs | background jobs |
| **Playwright MCP** | ✅ **Yes** | ✅ **Yes** | ❌ **No** |
| **IntelliJ MCP** | ❌ **No** | ✅ **Yes** | ❌ **No** |
| Working dir inheritance | ✓ | ✓ (with `-C`) | ✓ |

### MCP Visibility Summary

| CLI | Playwright | IntelliJ MCP | Best For |
|-----|------------|--------------|----------|
| **Claude Code** | ✅ Yes (if registered) | ✅ Yes (if registered) | Web research, general coding, browser automation |
| **Codex** | ✅ Yes (if registered) | ✅ Yes (if registered) | IntelliJ IDE work, full MCP access |
| **Gemini** | ❌ No | ❌ No | Cross-validation, alternative perspective, non-MCP tasks |

**Key:** MCP servers must be registered using `claude mcp add` or `codex mcp add` commands. Once registered, they are automatically inherited by all sub-agents.

### When to Use Which CLI

| Scenario | Best Tool | Reason |
|----------|-----------|--------|
| **IntelliJ IDE operations** | Claude Code or Codex | Both see IntelliJ MCP when registered |
| **Browser automation** | Claude Code or Codex | Both have Playwright MCP when registered |
| **Web research** | Claude Code | Built-in WebSearch, WebFetch |
| **Image/PDF analysis** | Codex | Native `-i` flag support |
| **Cross-validation** | Gemini | Different model, alternative perspective |
| **Primary orchestration** | Claude Code | Full tool suite, conversation context |
| **Focused non-interactive** | Codex | `exec` mode for non-interactive work |
| **Long context tasks** | Gemini | Large context window |
| **Pure code analysis** | Gemini | Good without MCP dependencies |

---

## Best Practices

### DO

1. **Run sub-agents in parallel** - Never run sequentially when tasks are independent
2. **Provide complete context** - Each call is isolated with no conversation history
3. **Specify output format** - Be explicit about expected structure
4. **Capture stderr** - Use `2>&1` to see all output including errors
5. **Add timeouts** - Prevent indefinite hangs with `timeout` command
6. **Use `--output-last-message`** - Capture clean final output without logs

### DON'T

1. **Don't assume context** - Each Codex call starts fresh
2. **Don't chain dependencies** - Results aren't automatically passed between calls
3. **Don't skip error handling** - Network/API issues happen
4. **Don't overload prompts** - One focused task per sub-agent call
5. **Don't run sequentially** - Always parallelize independent tasks

---

## Example: Full Workflow

```bash
# 1. Download source material
curl -L -o paper.pdf "https://arxiv.org/pdf/XXXX.XXXXX.pdf"

# 2. Initial analysis with Codex
pdftotext paper.pdf /tmp/paper.txt
codex -a never --sandbox workspace-write exec "Read /tmp/paper.txt and extract the 5 most important concepts from this paper.
For each concept:
- Name
- One-sentence description
- Key implementation detail
Output as markdown list." > concepts.md 2>&1

# 3. Review existing documentation
codex -a never --sandbox workspace-write exec "Read concepts.md and existing-docs.md. Compare these files.
Identify gaps in existing-docs.md based on concepts.md.
Output specific additions needed." > improvements.md 2>&1

# 4. Apply improvements (back to Claude Code)
# Read improvements.md and apply edits
```

---

## Quick Reference Card

```bash
codex -a never -s workspace-write -C /path/to/repo --add-dir /path/to/other exec -m gpt-5.2-codex

# RECOMMENDED: Low-friction auto mode
codex --full-auto exec "prompt" 2>&1

# Basic non-interactive execution
codex -a never --sandbox workspace-write exec "prompt" 2>&1

# With output capture to file (shell redirection)
codex -a never --sandbox workspace-write exec "prompt" > /tmp/codex-output.txt 2>&1

# Stream JSON events (machine-readable logs)
codex -a never --sandbox workspace-write --json exec "prompt" 2>&1

# With stdin heredoc
cat <<'EOF' | codex --full-auto exec
Multi-line prompt here
EOF

# With image input
codex -a never --sandbox workspace-write -i screenshot.png exec "prompt" 2>&1

# Code review mode
codex review "review instructions" 2>&1

# PARALLEL EXECUTION (always prefer this)
codex -a never --sandbox workspace-write exec "Task 1" > /tmp/out1.txt 2>&1 &
codex -a never --sandbox workspace-write exec "Task 2" > /tmp/out2.txt 2>&1 &
codex -a never --sandbox workspace-write exec "Task 3" > /tmp/out3.txt 2>&1 &
wait
cat /tmp/out*.txt

# With timeout
timeout 300 codex -a never --sandbox workspace-write exec "prompt" 2>&1
```

---

*Follow [@jonnyzzz](https://twitter.com/jonnyzzz) on X and [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) for more on AI agents and developer tooling.*
