# CLAUDE-CODE.md - Using Claude Code CLI as Sub-Agent

## Purpose

This document instructs AI agents on how to spawn Claude Code CLI as a sub-agent for specialized tasks. Claude Code excels at non-interactive, focused work with full tool access including file operations, web search, and code execution.

---

## When to Use Claude Code as Sub-Agent

### Ideal Use Cases

| Scenario | Why Claude Code |
|----------|-----------------|
| **Parallel Workloads** | Multiple Claude Code instances run simultaneously for maximum throughput |
| **Complex Code Analysis** | Full access to Read, Grep, Glob tools for codebase exploration |
| **Web Research** | Built-in WebSearch and WebFetch capabilities |
| **Cross-Validation** | Different instance provides second opinion on analysis |
| **Large File Processing** | Each instance works independently without context rot |
| **Isolated Tasks** | Each call starts fresh, preventing context pollution |

### When NOT to Use Claude Code Sub-Agent

- Interactive debugging requiring back-and-forth conversation
- Tasks needing access to parent conversation history
- Simple operations that can be done directly
- When you need the result immediately inline (sub-agents run asynchronously)

### ✅ MCP Server Visibility

**VERIFIED:** Claude Code sub-agents INHERIT all registered MCP servers automatically. Command-line arguments do NOT block MCP inheritance.

| MCP Server | Visibility | Requirements |
|------------|-----------|--------------|
| Playwright | ✅ Auto-inherited | `claude mcp add playwright npx @playwright/mcp@latest` |
| IntelliJ MCP Steroid | ✅ Auto-inherited | `claude mcp add --transport http intellij-steroid <URL>` |
| Any Custom MCP | ✅ Auto-inherited | Register once with `claude mcp add` |

**Key insight:** MCP servers registered with `claude mcp add` are available to ALL Claude Code sessions, including sub-agents spawned with any command-line flags (`-p`, `--tools default`, `--permission-mode dontAsk`, etc.).

**To check registered MCPs:**
```bash
claude mcp list
```

**To register IntelliJ MCP Steroid:**
```bash
# IntelliJ writes the MCP server URL to a file in your home directory
# Find the file (named after the IntelliJ process ID)
cat ~/.*.mcp-steroid

# Use the URL from that file to register
claude mcp add --transport http intellij-steroid <URL-from-file>

# Verify it's connected
claude mcp list
```

---

## Claude Code CLI Reference

### Installation Check

```bash
# Verify Claude Code is available
which claude
# Expected: ~/.local/bin/claude or similar

# Check version
claude --version
# Expected: 2.x.x (Claude Code)
```

### Core Commands

```bash
# RECOMMENDED: Non-interactive execution with full tools (stdin + stderr capture)
echo "<prompt>" | claude -p --tools default --permission-mode dontAsk 2>&1

# With prompt as argument
claude -p --tools default --permission-mode dontAsk "your prompt here" 2>&1

# JSON output format (for programmatic parsing)
echo "your prompt" | claude -p --tools default --permission-mode dontAsk --output-format json 2>&1

# Stream JSON output (for real-time processing)
echo "your prompt" | claude -p --tools default --permission-mode dontAsk --output-format stream-json 2>&1
```

### Tool Access

**Recommended:** Give sub-agents full tool access. Don't restrict yourself - sub-agents should have the same capabilities as the main agent.

```bash
# Full access + autonomous approvals (recommended for sub-agents)
echo "Your prompt" | claude -p --tools default --permission-mode dontAsk 2>&1

# Auto-approve edits but still prompt for higher-risk actions
echo "Your prompt" | claude -p --tools default --permission-mode acceptEdits 2>&1

# If you must restrict (rare cases)
echo "prompt" | claude -p --allowedTools "Read,Grep,Glob" --permission-mode dontAsk
echo "prompt" | claude -p --disallowedTools "Edit,Write" --permission-mode dontAsk
```

**MCP and skills:** keep slash commands enabled (do not pass `--disable-slash-commands`), and load MCP servers with `--mcp-config <path>` if they are not already in your default settings. Avoid `--strict-mcp-config` unless you provide the full MCP list.

## Spawning Claude Code from Another Agent

### Basic Pattern

```bash
# Simple execution with prompt as argument
claude -p --tools default --permission-mode dontAsk "Your detailed prompt here" 2>&1

# With stdin (preferred for complex prompts)
echo "Your detailed prompt here" | claude -p --tools default --permission-mode dontAsk 2>&1
```

### With File Context

```bash
# Claude Code will use its tools to access files
echo "Read /path/to/file.md and extract:
1. Key concepts
2. Implementation patterns
3. Summary in 3 sentences" | claude -p --tools default --permission-mode dontAsk 2>&1
```

### Capturing Structured Output

```bash
# JSON output for programmatic processing
echo "List 3 main points" | claude -p --tools default --permission-mode dontAsk --output-format json 2>&1

# Parse the result field from JSON
echo "What is 2+2?" | claude -p --tools default --permission-mode dontAsk --output-format json 2>&1 | jq -r '.result'
```

---

## Parallel Execution (CRITICAL)

**Always run independent Claude Code sub-agents in parallel** for maximum throughput. Each instance runs in isolation with its own context.

**Note on Permissions:** Even with `--permission-mode dontAsk`, background jobs using `&` may still trigger permission prompts in some scenarios. This is expected security behavior. For truly non-interactive parallel execution within Claude Code, consider using the Task tool with multiple concurrent sub-agents instead of bash background jobs.

### From Bash (Background Jobs)

```bash
# Launch multiple Claude Code instances IN PARALLEL (full tool access)
echo "Task 1: Analyze auth module" | claude -p --tools default --permission-mode dontAsk > /tmp/out1.txt 2>&1 &
echo "Task 2: Analyze database layer" | claude -p --tools default --permission-mode dontAsk > /tmp/out2.txt 2>&1 &
echo "Task 3: Analyze API endpoints" | claude -p --tools default --permission-mode dontAsk > /tmp/out3.txt 2>&1 &

# Wait for ALL to complete
wait

# Collect and combine results
cat /tmp/out1.txt /tmp/out2.txt /tmp/out3.txt
```

### Parallel with Timeout Protection

```bash
# Run parallel tasks with timeout (macOS: use gtimeout from coreutils)
timeout 300 bash -c 'echo "Task 1" | claude -p --tools default --permission-mode dontAsk' > /tmp/out1.txt 2>&1 &
timeout 300 bash -c 'echo "Task 2" | claude -p --tools default --permission-mode dontAsk' > /tmp/out2.txt 2>&1 &
timeout 300 bash -c 'echo "Task 3" | claude -p --tools default --permission-mode dontAsk' > /tmp/out3.txt 2>&1 &
wait
```

### Parallel Map Pattern

```bash
# Process multiple files in parallel (full tool access)
for file in src/module1.ts src/module2.ts src/module3.ts; do
  echo "Read $file and identify potential bugs" | \
    claude -p --tools default --permission-mode dontAsk > "/tmp/analysis-$(basename $file).txt" 2>&1 &
done
wait

# Aggregate results
cat /tmp/analysis-*.txt
```

---

## Working Directory Requirements

**IMPORTANT:** Always spawn Claude Code sub-agents from the correct working directory to inherit project-specific configurations.

### Why Working Directory Matters

Claude Code inherits configuration from:
1. **`.claude/` directory** - Settings, commands, hooks, rules
2. **`CLAUDE.md`** - Project guidelines and instructions
3. **`.mcp.json`** - MCP server configurations (limited - see MCP Visibility above)
4. **Project files** - Git config, editor config, build files

### Recommended Pattern

```bash
# Option 1: Run from project root
cd /path/to/project
echo "prompt" | claude -p --tools default --permission-mode dontAsk 2>&1

# Option 2: Use subshell
(cd /path/to/project && echo "prompt" | claude -p --tools default --permission-mode dontAsk 2>&1)
```

### Verification

Test that sub-agent sees project configs:

```bash
(cd /path/to/project && echo "What is your current working directory? What configuration files do you see?" | claude -p --tools default --permission-mode dontAsk 2>&1)
```

**Expected output:**
- Working directory: `/path/to/project`
- Config files: `.claude/`, `CLAUDE.md`, `.mcp.json`, etc.
- MCP servers: Playwright (IntelliJ MCP will be missing - use Codex instead)

---

## Automation with Python UV and Bash Scripts

### Using Python with UV

```python
#!/usr/bin/env python3
"""Example: Parallel Claude Code sub-agents with Python UV"""
import subprocess
import asyncio
from pathlib import Path

async def run_claude_agent(prompt: str, output_file: Path) -> int:
    """Run Claude Code sub-agent and capture output."""
    cmd = ["bash", "-c", f'echo "{prompt}" | claude -p --tools default --permission-mode dontAsk 2>&1']

    with output_file.open('w') as f:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=f,
            stderr=subprocess.STDOUT
        )
        return await proc.wait()

async def main():
    """Launch 3 Claude Code agents in parallel."""
    tasks = [
        run_claude_agent("Analyze auth module", Path("/tmp/out1.txt")),
        run_claude_agent("Analyze database layer", Path("/tmp/out2.txt")),
        run_claude_agent("Analyze API endpoints", Path("/tmp/out3.txt"))
    ]

    results = await asyncio.gather(*tasks)
    print(f"All agents completed with codes: {results}")

    # Aggregate results
    for i in range(1, 4):
        print(f"\n=== Agent {i} Output ===")
        print(Path(f"/tmp/out{i}.txt").read_text())

if __name__ == "__main__":
    asyncio.run(main())
```

### Bash Script Template

```bash
#!/usr/bin/env bash
# run-parallel-claude-agents.sh
# Launch multiple Claude Code sub-agents in parallel

set -euo pipefail

# Configuration
TASKS=(
    "Task 1: Analyze authentication module"
    "Task 2: Analyze database layer"
    "Task 3: Analyze API endpoints"
)
OUTPUT_DIR="/tmp/claude-agents"
TIMEOUT_SEC=300

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Launch agents in parallel
echo "=== Launching ${#TASKS[@]} Claude Code agents in parallel ==="
pids=()

for i in "${!TASKS[@]}"; do
    task="${TASKS[$i]}"
    output_file="$OUTPUT_DIR/agent-$((i+1)).txt"

    echo "Starting agent $((i+1)): $task"

    # Launch in background with timeout protection
    (
        timeout "$TIMEOUT_SEC" bash -c \
            "echo \"$task\" | claude -p --tools default --permission-mode dontAsk 2>&1" \
            > "$output_file" 2>&1
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
cat "$OUTPUT_DIR"/agent-*.txt

echo ""
echo "=== Execution Complete ==="
echo "Individual outputs saved to: $OUTPUT_DIR"
```

Make executable with: `chmod +x run-parallel-claude-agents.sh`

---

## Prompt Engineering for Claude Code Sub-Agents

### Structure Template

```
CONTEXT:
[Brief description of the overall task and why this sub-agent is being spawned]

INPUT FILES:
[Paths the sub-agent should read - it will use Read tool]

TASK:
[Specific, actionable instructions - be explicit]

OUTPUT FORMAT:
[Exactly what format you expect - markdown, JSON, plain text]

CONSTRAINTS:
[Any limitations, scope boundaries, or requirements]
```

### Example: Code Review Sub-Agent

```bash
echo "CONTEXT:
You are reviewing a pull request for security issues.

INPUT FILES:
- /path/to/changed-file.ts

TASK:
Read the file and identify:
1. SQL injection vulnerabilities
2. XSS vulnerabilities
3. Authentication/authorization issues
4. Sensitive data exposure

OUTPUT FORMAT:
## Security Review

### Critical Issues
- Issue: description and line number

### Warnings
- Warning: description and line number

### Notes
- Note: observation

If no issues found, output: '## Security Review\n\nNo security issues identified.'

CONSTRAINTS:
- Focus only on security, not code style
- Reference specific line numbers
- Provide remediation suggestions" | claude -p --tools default --permission-mode dontAsk 2>&1
```

---

## Integration with RLM Methodology

### Partition+Map+Reduce Pattern

```bash
# Step 1: PARTITION (orchestrating agent splits the work)
# Create task descriptions for each chunk

# Step 2: MAP (Claude Code sub-agents process IN PARALLEL)
echo "Process chunk 1: $CHUNK1_DESCRIPTION" | claude -p --tools default --permission-mode dontAsk > /tmp/result1.txt 2>&1 &
echo "Process chunk 2: $CHUNK2_DESCRIPTION" | claude -p --tools default --permission-mode dontAsk > /tmp/result2.txt 2>&1 &
echo "Process chunk 3: $CHUNK3_DESCRIPTION" | claude -p --tools default --permission-mode dontAsk > /tmp/result3.txt 2>&1 &
wait

# Step 3: REDUCE (orchestrating agent aggregates results)
# Read /tmp/result*.txt and synthesize final output
```

### Cross-Validation Pattern

```bash
# Primary analysis done by main agent
# Validate with Claude Code sub-agent (full tool access):
echo "Read /tmp/primary-analysis.md and review for:
1. Logical consistency
2. Missing edge cases
3. Incorrect assumptions
4. Factual errors

Output only issues found, or 'VALIDATED: No issues found' if none." | \
  claude -p --tools default --permission-mode dontAsk 2>&1
```

---

## Error Handling

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `command not found` | Claude Code not installed | Install via official instructions |
| `Input must be provided` | Missing prompt | Use stdin or prompt argument |
| Process hangs | Task too complex | Add timeout, reduce scope |
| High cost | Excessive token usage | Set `--max-budget-usd` |

### Robust Execution Pattern

```bash
# With timeout and retry logic
MAX_RETRIES=3
RETRY_COUNT=0
TIMEOUT_SEC=300

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  if timeout $TIMEOUT_SEC bash -c 'echo "your prompt" | claude -p --tools default --permission-mode dontAsk' 2>&1; then
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
| **Playwright MCP** | ✅ **Yes** (if registered) | ✅ **Yes** (if registered) | ❌ **No** |
| **IntelliJ MCP** | ✅ **Yes** (if registered) | ✅ **Yes** (if registered) | ❌ **No** |
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
| **Focused non-interactive** | Codex | `exec` mode, best MCP visibility |
| **Long context tasks** | Gemini | Large context window |
| **Pure code analysis** | Gemini | Good without MCP dependencies |

---

## Best Practices

### DO

1. **Run sub-agents in parallel** - Never run sequentially when tasks are independent
2. **Provide complete context** - Each call is isolated with no conversation history
3. **Specify output format** - Be explicit about expected structure
4. **Use --allowedTools** - Limit tools to what's needed for security and focus
5. **Capture stderr** - Use `2>&1` to see all output including errors
6. **Add timeouts** - Prevent indefinite hangs with `timeout` command

### DON'T

1. **Don't assume context** - Each Claude Code call starts fresh
2. **Don't chain dependencies** - Results aren't automatically passed between calls
3. **Don't skip error handling** - Network/API issues happen
4. **Don't overload prompts** - One focused task per sub-agent call
5. **Don't run sequentially** - Always parallelize independent tasks

---

## Quick Reference Card

```bash
echo "<prompt>" | claude -p --tools default --permission-mode dontAsk 2>&1

# With prompt as argument
claude -p --tools default --permission-mode dontAsk "prompt" 2>&1

# With specific tools only
echo "prompt" | claude -p --allowedTools "Read,Grep" --permission-mode dontAsk 2>&1

# JSON output (for programmatic parsing)
echo "prompt" | claude -p --tools default --permission-mode dontAsk --output-format json 2>&1

# PARALLEL EXECUTION (always prefer this)
echo "Task 1" | claude -p --tools default --permission-mode dontAsk > /tmp/out1.txt 2>&1 &
echo "Task 2" | claude -p --tools default --permission-mode dontAsk > /tmp/out2.txt 2>&1 &
echo "Task 3" | claude -p --tools default --permission-mode dontAsk > /tmp/out3.txt 2>&1 &
wait
cat /tmp/out*.txt

# With timeout
timeout 300 bash -c 'echo "prompt" | claude -p --tools default --permission-mode dontAsk' 2>&1
```

---

*Follow [@jonnyzzz](https://twitter.com/jonnyzzz) on X and [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) for more on AI agents and developer tooling.*
