# GEMINI.md - Using Gemini CLI as Sub-Agent

## Purpose

This document instructs AI agents (Claude Code, Codex, etc.) on how to spawn Gemini CLI as a sub-agent for specialized tasks. Gemini provides an alternative perspective for cross-validation and diverse reasoning.

---

## When to Use Gemini as Sub-Agent

### Ideal Use Cases

| Scenario | Why Gemini |
|----------|-----------|
| **Parallel Workloads** | Multiple Gemini instances run simultaneously for maximum throughput |
| **Cross-Validation** | Different model provides second opinion on analysis |
| **Alternative Perspective** | Gemini may catch issues Claude/Codex miss |
| **Diversity in Review** | Multiple model architectures reduce blind spots |
| **Long-Context Tasks** | Gemini has large context window for extensive documents |
| **Non-MCP Tasks** | Good for pure code analysis without IDE integration |

### When NOT to Use Gemini

- **MCP-dependent tasks** - Gemini does NOT see MCP servers (use Codex or Claude Code instead)
- **IntelliJ IDE operations** - No MCP access (use Codex)
- **Browser automation** - No Playwright MCP (use Claude Code or Codex)
- Tasks requiring specific IDE or browser tools
- Simple edits that don't benefit from cross-validation
- Tasks requiring conversation history access

### ⚠️ MCP Server Visibility

**IMPORTANT:** Gemini does NOT integrate with MCP servers.

| MCP Server | Visible to Gemini | Impact |
|------------|------------------|---------|
| Playwright | ❌ No | Cannot control browsers |
| IntelliJ MCP Steroid | ❌ No | Cannot use IDE operations |

**What Gemini HAS:**
- Native file system operations (read, write, search, glob)
- Web capabilities (search, fetch)
- Shell command execution
- Memory and cognition features

**Best Use:** Code review, analysis, and validation tasks that don't require IDE or browser integration.

---

## Gemini CLI Reference

### Installation Check

```bash
# Verify Gemini is available
which gemini
# Expected: /opt/homebrew/bin/gemini (macOS) or similar

# Check version
gemini --version
# Expected: 0.22.5 or newer
```

### API Key Configuration (Required)

Gemini CLI requires an explicit API key. Before spawning Gemini sub-agents, ensure the key is set:

```bash
# Check if API key is configured
echo $GEMINI_API_KEY

# If not set, ask the user for their Gemini API key
# The key must be explicitly provided - it does not work implicitly
export GEMINI_API_KEY="your-api-key-here"
```

**Important for AI agents:** If `GEMINI_API_KEY` is not set, Gemini CLI will fail with exit code 41. Before spawning Gemini sub-agents, verify the environment variable exists or ask the user to provide their API key.

### Core Commands

```bash
# Non-interactive execution (one-shot)
gemini --approval-mode auto_edit "your prompt here" 2>&1

# Interactive mode
gemini

# Execute prompt then continue interactively
gemini -i "initial prompt"

# With specific model (syntax reference)
gemini -m model-name --approval-mode auto_edit "prompt" 2>&1
```

### Approval Modes

**Give sub-agents full access** - don't restrict capabilities. Use auto-approve for non-interactive execution.

```bash
# Auto-approve edits (recommended for sub-agents)
gemini --approval-mode auto_edit "prompt" 2>&1

# YOLO mode - auto-approve everything (for trusted tasks)
gemini --approval-mode yolo "prompt" 2>&1
# Alias: gemini -y "prompt"

# Default - prompts for approval (not suitable for sub-agents)
gemini "prompt" 2>&1
```

**MCP and skills:** avoid `--allowed-mcp-server-names`, `--allowed-tools`, or `--extensions` unless you intend to restrict access. By default, all configured MCP servers and extensions remain available.

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

## Spawning Gemini from Claude Code

### Basic Pattern

```bash
# From Claude Code, use Bash tool:
gemini --approval-mode auto_edit "Your detailed prompt here" 2>&1
```

### For File Analysis

Unlike Codex, Gemini doesn't have an `-i` flag for file input. Instead, include file content in the prompt:

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

### Capturing Output

```bash
# Save output to file for later processing
gemini --approval-mode auto_edit "prompt" > /tmp/gemini-output.txt 2>&1

# Then read the output
cat /tmp/gemini-output.txt
```

---

## Prompt Engineering for Gemini Sub-Agents

### Structure Template

```
CONTEXT:
[Brief description of the overall task]

INPUT:
[Content to analyze - can be file content, code, etc.]

TASK:
[Specific, actionable instructions]

OUTPUT FORMAT:
[Exactly what format you expect]

CONSTRAINTS:
[Any limitations or requirements]
```

### Example: Cross-Validation Review

```bash
CONTENT=$(cat output.md)

gemini --approval-mode auto_edit "CONTEXT:
You are cross-validating a document produced by another AI agent.

INPUT:
$CONTENT

TASK:
1. Verify factual claims
2. Check for logical consistency
3. Identify potential gaps or blind spots
4. Note any questionable assertions
5. Suggest concrete improvements

OUTPUT FORMAT:
## Verification Results
- Claim 1: [VERIFIED/QUESTIONABLE/INCORRECT] - reason
- Claim 2: [VERIFIED/QUESTIONABLE/INCORRECT] - reason

## Logical Issues
- Issue 1: description
- Issue 2: description

## Gaps Identified
- Gap 1: what's missing
- Gap 2: what's missing

## Recommendations
1. Specific improvement
2. Specific improvement

CONSTRAINTS:
- Focus on substantive issues, not style
- Reference specific sections when noting problems
- Be constructive in recommendations" 2>&1
```

---

## Working Directory Requirements

**IMPORTANT:** Always spawn Gemini sub-agents from the correct working directory to access project-specific configuration files.

### Why Working Directory Matters

Gemini can access configuration from:
1. **Project files** - Build configs, git settings, documentation
2. **AI guidelines** - GEMINI.md, CLAUDE.md, .ai/ directory
3. **`.mcp.json`** - Can read it but doesn't use MCP servers
4. **File structure** - Inherits current directory for file operations

**Note:** Gemini does NOT inherit MCP server configurations, but can read and understand project structure.

### Recommended Pattern

```bash
# Option 1: Run from project root
cd /path/to/project
gemini --approval-mode auto_edit "prompt" 2>&1

# Option 2: Use subshell
(cd /path/to/project && gemini --approval-mode auto_edit "prompt" 2>&1)
```

### Verification

Test that Gemini sees project structure:

```bash
(cd /path/to/project && gemini --approval-mode auto_edit "What is your current working directory? What configuration files do you see? What tools are available?" 2>&1)
```

**Expected output:**
- Working directory: `/path/to/project`
- Config files: Build files, .gitignore, GEMINI.md, etc.
- Tools: Native filesystem, web, shell (NO MCP servers)

---

## Automation with Python UV and Bash Scripts

### Using Python with UV

```python
#!/usr/bin/env python3
"""Example: Parallel Gemini sub-agents with Python UV"""
import subprocess
import asyncio
from pathlib import Path
import os

async def run_gemini_agent(
    prompt: str,
    output_file: Path,
    approval_mode: str = "auto_edit"
) -> int:
    """Run Gemini sub-agent and capture output."""
    # Ensure GEMINI_API_KEY is set
    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY environment variable not set")

    cmd = [
        "gemini",
        "--approval-mode", approval_mode
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
    """Launch 3 Gemini agents in parallel."""
    tasks = [
        run_gemini_agent(
            "Read /path/to/file1.md and extract key concepts",
            Path("/tmp/gemini-out1.txt")
        ),
        run_gemini_agent(
            "Read /path/to/file2.md and identify patterns",
            Path("/tmp/gemini-out2.txt")
        ),
        run_gemini_agent(
            "Read /path/to/file3.md and summarize",
            Path("/tmp/gemini-out3.txt")
        )
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    print(f"All agents completed with results: {results}")

    # Aggregate results
    for i in range(1, 4):
        output_file = Path(f"/tmp/gemini-out{i}.txt")
        if output_file.exists():
            print(f"\n=== Agent {i} Output ===")
            print(output_file.read_text())
        else:
            print(f"\n=== Agent {i} FAILED ===")

if __name__ == "__main__":
    # Verify API key before running
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not set. Set it with:")
        print("export GEMINI_API_KEY='your-api-key-here'")
        exit(1)

    asyncio.run(main())
```

### Bash Script Template

```bash
#!/usr/bin/env bash
# run-parallel-gemini-agents.sh
# Launch multiple Gemini sub-agents in parallel

set -euo pipefail

# Check for API key
if [ -z "${GEMINI_API_KEY:-}" ]; then
    echo "ERROR: GEMINI_API_KEY environment variable not set"
    echo "Set it with: export GEMINI_API_KEY='your-api-key-here'"
    exit 1
fi

# Configuration
OUTPUT_DIR="/tmp/gemini-agents"
TIMEOUT_SEC=300
APPROVAL_MODE="auto_edit"

# Tasks array
declare -a TASKS=(
    "Analyze authentication patterns in the codebase"
    "Review error handling strategies"
    "Identify performance optimization opportunities"
)

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Launch agents in parallel
echo "=== Launching ${#TASKS[@]} Gemini agents in parallel ==="
pids=()

for i in "${!TASKS[@]}"; do
    task="${TASKS[$i]}"
    output_file="$OUTPUT_DIR/agent-$((i+1)).txt"

    echo "Starting agent $((i+1)): ${task:0:50}..."

    # Launch in background with timeout protection
    (
        timeout "$TIMEOUT_SEC" bash -c \
            "echo \"$task\" | gemini --approval-mode \"$APPROVAL_MODE\" 2>&1" \
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
for i in $(seq 1 ${#TASKS[@]}); do
    echo ""
    echo "--- Agent $i ---"
    if [ -f "$OUTPUT_DIR/agent-$i.txt" ]; then
        cat "$OUTPUT_DIR/agent-$i.txt"
    else
        echo "ERROR: Output file not found"
    fi
done

echo ""
echo "=== Execution Complete ==="
echo "Individual outputs saved to: $OUTPUT_DIR"
```

Make executable with: `chmod +x run-parallel-gemini-agents.sh`

---

## Parallel Execution (CRITICAL)

**Always run independent Gemini sub-agents in parallel** for maximum throughput. Each instance runs in isolation with its own context.

### Multiple Instances

```bash
# Launch multiple Gemini instances IN PARALLEL
gemini --approval-mode auto_edit "Task 1: analyze section A" > /tmp/out1.txt 2>&1 &
gemini --approval-mode auto_edit "Task 2: analyze section B" > /tmp/out2.txt 2>&1 &
gemini --approval-mode auto_edit "Task 3: analyze section C" > /tmp/out3.txt 2>&1 &

# Wait for ALL to complete
wait

# Collect and combine results
cat /tmp/out1.txt /tmp/out2.txt /tmp/out3.txt
```

### Parallel with Timeout Protection

```bash
# Run parallel tasks with timeout (macOS: use gtimeout from coreutils)
timeout 300 gemini --approval-mode auto_edit "Task 1" > /tmp/out1.txt 2>&1 &
timeout 300 gemini --approval-mode auto_edit "Task 2" > /tmp/out2.txt 2>&1 &
timeout 300 gemini --approval-mode auto_edit "Task 3" > /tmp/out3.txt 2>&1 &
wait
```

### Parallel Map Pattern

```bash
# Process multiple files in parallel
for file in src/module1.ts src/module2.ts src/module3.ts; do
  CONTENT=$(cat "$file")
  gemini --approval-mode auto_edit "Analyze this code:

$CONTENT

Identify potential bugs and suggest improvements." > "/tmp/analysis-$(basename $file).txt" 2>&1 &
done
wait

# Aggregate results
cat /tmp/analysis-*.txt
```

---

## RLM Integration with Gemini

### Using Gemini for RLM Sub-Calls

When implementing RLM's Partition+Map strategy, Gemini can serve as the sub-LM:

```bash
# Step 1: PARTITION (orchestrating agent splits the work)
# Split large context into chunks

# Step 2: MAP (Gemini sub-agents process IN PARALLEL)
for chunk in chunk1.txt chunk2.txt chunk3.txt; do
  CONTENT=$(cat "$chunk")
  gemini --approval-mode auto_edit "Process this chunk:

$CONTENT

Extract: [specific information]
Format: [expected output format]" > "${chunk%.txt}-result.txt" 2>&1 &
done
wait

# Step 3: REDUCE (orchestrating agent aggregates results)
# Aggregate results from *-result.txt files
```

### Gemini in Cross-Validation Pattern

From MULTI-AGENT.md Pattern D:

```bash
# Primary work done by orchestrator, output in output.md
CONTENT=$(cat output.md)

# Cross-validate with different models in parallel
codex exec -i output.md "Review for technical accuracy" > review_codex.md 2>&1 &
gemini --approval-mode auto_edit "Review this for accuracy:

$CONTENT

Output: Issues found or 'VALIDATED'" > review_gemini.md 2>&1 &
wait

# Synthesize reviews
cat review_codex.md review_gemini.md
```

---

## Error Handling

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `command not found` | Gemini not installed | Install via official instructions |
| Exit code 41 | `GEMINI_API_KEY` not set | Ask user for API key, then `export GEMINI_API_KEY="key"` |
| Timeout | Task too complex | Break into smaller sub-tasks |
| Rate limit | Too many requests | Add delays between calls |
| Auth error | Invalid API key | Re-authenticate with `gemini login` |

### Robust Execution Pattern

```bash
# With timeout and retry logic
MAX_RETRIES=3
RETRY_COUNT=0
TIMEOUT_SEC=300

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  if timeout $TIMEOUT_SEC gemini --approval-mode auto_edit "prompt" 2>&1; then
    break
  fi
  RETRY_COUNT=$((RETRY_COUNT + 1))
  echo "Retry $RETRY_COUNT of $MAX_RETRIES..."
  sleep 5
done
```

### Troubleshooting Guide

**API Key Issues:**

```bash
# Verify API key is set
if [ -z "${GEMINI_API_KEY:-}" ]; then
    echo "ERROR: GEMINI_API_KEY not set"
    echo "Get your API key from: https://makersuite.google.com/app/apikey"
    echo "Set it with: export GEMINI_API_KEY='your-api-key-here'"
    exit 1
fi

# Test API key validity
if ! gemini --approval-mode auto_edit "test" 2>&1 | grep -q "Error.*401\|Error.*API"; then
    echo "✓ API key appears valid"
else
    echo "✗ API key invalid or expired"
fi
```

**Timeout Issues:**

If Gemini sub-agents timeout frequently:
1. Increase timeout: use `timeout 600` instead of `timeout 300`
2. Reduce prompt complexity - break into smaller sub-tasks
3. Check network connectivity to Google's APIs

**Permission Issues:**

If you see permission prompts despite `--approval-mode auto_edit`:
1. Try `--approval-mode yolo` for fully automatic approval (use with caution)
2. Ensure you're not in an interactive terminal (redirecting stdin may help)

**Rate Limiting:**

If you hit rate limits with parallel agents:
```bash
# Add delays between launches
for task in "${TASKS[@]}"; do
    echo "$task" | gemini --approval-mode auto_edit > output.txt 2>&1 &
    sleep 2  # 2-second delay between launches
done
wait
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

**Key:** MCP servers must be registered using `claude mcp add` or `codex mcp add` commands. Once registered, they are automatically inherited by all sub-agents. Gemini does NOT support MCP servers.

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
2. **Provide complete context** - Gemini has no conversation history
3. **Specify output format** - Be explicit about expected structure
4. **Use for cross-validation** - Leverage different model perspective
5. **Capture stderr** - Use `2>&1` to see all output
6. **Add timeouts** - Prevent indefinite hangs with `timeout` command
7. **Include file content in prompt** - No `-i` flag like Codex

### DON'T

1. **Don't assume shared context** - Each call is isolated
2. **Don't chain dependencies** - Results aren't automatically passed between calls
3. **Don't skip error handling** - Network/API issues happen
4. **Don't overload prompts** - One focused task per sub-agent call
5. **Don't run sequentially** - Always parallelize independent tasks
6. **Don't use YOLO mode** - Unless you understand the risks

---

## Quick Reference Card

```bash
# Basic execution
gemini --approval-mode auto_edit "prompt" 2>&1

# With model (syntax reference)
gemini -m model-name --approval-mode auto_edit "prompt" 2>&1

# Auto-approve edits
gemini --approval-mode auto_edit "prompt" 2>&1

# JSON output
gemini -o json --approval-mode auto_edit "prompt" 2>&1

# With file content
CONTENT=$(cat file.md)
gemini --approval-mode auto_edit "Analyze: $CONTENT" 2>&1

# Capture output to file
gemini --approval-mode auto_edit "prompt" > output.txt 2>&1

# PARALLEL EXECUTION (always prefer this)
gemini --approval-mode auto_edit "Task 1" > /tmp/out1.txt 2>&1 &
gemini --approval-mode auto_edit "Task 2" > /tmp/out2.txt 2>&1 &
gemini --approval-mode auto_edit "Task 3" > /tmp/out3.txt 2>&1 &
wait
cat /tmp/out*.txt

# With timeout
timeout 300 gemini --approval-mode auto_edit "prompt" 2>&1
```

---

## Example: Full RLM Cross-Validation Workflow

```bash
#!/bin/bash
# Cross-validate output.md using multiple AI agents

OUTPUT_FILE="output.md"
CONTENT=$(cat "$OUTPUT_FILE")

echo "=== Starting Cross-Validation ==="
echo "File: $OUTPUT_FILE"
echo "Size: $(wc -l < "$OUTPUT_FILE") lines"
echo ""

# Launch parallel reviews
echo "Launching Codex review..."
codex exec -i "$OUTPUT_FILE" "Review for technical accuracy. Output: JSON with issues array." \
  > /tmp/review_codex.json 2>&1 &

echo "Launching Gemini review..."
gemini --approval-mode auto_edit "Cross-validate this document:

$CONTENT

Check for:
1. Factual accuracy
2. Logical consistency
3. Missing information
4. Questionable claims

Output: Markdown with ## sections" > /tmp/review_gemini.md 2>&1 &

# Wait for both
wait
echo ""

echo "=== Codex Review ==="
cat /tmp/review_codex.json
echo ""

echo "=== Gemini Review ==="
cat /tmp/review_gemini.md
echo ""

echo "=== Cross-Validation Complete ==="
```

---

*Follow [@jonnyzzz](https://twitter.com/jonnyzzz) on X and [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) for more on AI agents and developer tooling.*
