# CODEX.md - Using Codex CLI as Sub-Agent

## Purpose

This document instructs AI agents (Claude Code, Junie, etc.) on how to spawn Codex CLI as a sub-agent for specialized tasks. Codex excels at non-interactive, focused work on files with explicit prompts.

---

## When to Use Codex as Sub-Agent

### Ideal Use Cases

| Scenario | Why Codex |
|----------|-----------|
| **Image Analysis (png/jpg)** | Codex handles image input with `-i` flag |
| **Focused Code Review** | Non-interactive `review` mode for specific files |
| **Large File Processing** | Codex can work independently without context rot |
| **Parallel Workloads** | Multiple Codex instances can run simultaneously |
| **Cross-Validation** | Different AI agent provides second opinion |

### When NOT to Use Codex

- Interactive debugging requiring back-and-forth
- Tasks needing access to conversation history
- Operations requiring MCP tools (browser, etc.)
- Simple edits that Claude Code can do directly

---

## Codex CLI Reference

### Installation Check

```bash
# Verify Codex is available
which codex
# Expected: /opt/homebrew/bin/codex (macOS) or similar
```

### Core Commands

```bash
# Non-interactive execution
codex exec "your prompt here" 2>&1

# Code review mode
codex review "review instructions" 2>&1

# With model selection (syntax)
codex exec -m model-name "prompt" 2>&1
```

### Performance and Config Notes

- **Give sub-agents full access** - don't restrict capabilities unnecessarily.
- Codex reads defaults from `~/.codex/config.toml` (for example `model`).
- Prefer defaults unless you have a concrete reason to override config.
- Avoid setting `reasoning_effort` explicitly; if a task is slow, increase command timeout or split prompts instead.
- For full filesystem access (recommended for cross-repo work):

```bash
codex exec -c 'sandbox_permissions=["disk-full-read-access"]' "prompt" 2>&1
```

- Startup logs may show MCP servers initializing; factor that into timeouts.
- If Codex timeouts on large repos, run tasks sequentially and use a longer timeout (for example `gtimeout 900 codex exec ...`).

### Image Input

```bash
# Single image
codex exec -i screenshot.png "Analyze this image" 2>&1

# Multiple images
codex exec -i screen1.png -i screen2.jpg "Compare these" 2>&1

# PDFs: convert to text or images first (pdftotext/pdftoppm), then analyze
pdftotext report.pdf /tmp/report.txt
codex exec "Read /tmp/report.txt and summarize the key findings." 2>&1
```

---

## Spawning Codex from Claude Code

### Basic Pattern

```bash
# From Claude Code, use Bash tool:
codex exec "Your detailed prompt here" 2>&1
```

### With File Context

```bash
# Point Codex at files to read (Codex will read them via tools)
codex exec "Read /path/to/file.md and output:
1. Key concepts
2. Implementation patterns
3. Recommended improvements for TARGET_FILE.md" 2>&1
```

### Capturing Output

```bash
# Save only the last assistant message (avoids noisy logs)
codex exec --output-last-message /tmp/codex-output.txt "prompt" 2>&1

# Then read the output
cat /tmp/codex-output.txt
```

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
codex exec "CONTEXT:
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
codex exec "Read /tmp/task1.txt and do Task 1" > /tmp/out1.txt 2>&1 &
codex exec "Read /tmp/task2.txt and do Task 2" > /tmp/out2.txt 2>&1 &
codex exec "Read /tmp/task3.txt and do Task 3" > /tmp/out3.txt 2>&1 &

# Wait for ALL to complete
wait

# Collect and combine results
cat /tmp/out1.txt /tmp/out2.txt /tmp/out3.txt
```

### With Timeout Protection

```bash
# Run parallel tasks with timeout (macOS: use gtimeout from coreutils)
timeout 300 codex exec "Task 1" > /tmp/out1.txt 2>&1 &
timeout 300 codex exec "Task 2" > /tmp/out2.txt 2>&1 &
timeout 300 codex exec "Task 3" > /tmp/out3.txt 2>&1 &
wait
```

### Parallel Map Pattern

```bash
# Process multiple files in parallel
for file in src/module1.ts src/module2.ts src/module3.ts; do
  codex exec "Read $file and identify potential issues" > "/tmp/analysis-$(basename $file).txt" 2>&1 &
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
codex exec "Process chunk 1: $CHUNK1_DESCRIPTION" > /tmp/result1.txt 2>&1 &
codex exec "Process chunk 2: $CHUNK2_DESCRIPTION" > /tmp/result2.txt 2>&1 &
codex exec "Process chunk 3: $CHUNK3_DESCRIPTION" > /tmp/result3.txt 2>&1 &
wait

# Step 3: REDUCE (orchestrating agent aggregates results)
# Read /tmp/result*.txt and synthesize final output
```

### Cross-Validation Pattern

```bash
# Primary analysis done by main agent
# Validate with Codex sub-agent:
codex exec "Read /tmp/primary-analysis.md and review for:
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
  if timeout $TIMEOUT_SEC codex exec "prompt" 2>&1; then
    break
  fi
  RETRY_COUNT=$((RETRY_COUNT + 1))
  echo "Retry $RETRY_COUNT of $MAX_RETRIES..."
  sleep 5
done
```

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
codex exec "Read /tmp/paper.txt and extract the 5 most important concepts from this paper.
For each concept:
- Name
- One-sentence description
- Key implementation detail
Output as markdown list." > concepts.md 2>&1

# 3. Review existing documentation
codex exec "Read concepts.md and existing-docs.md. Compare these files.
Identify gaps in existing-docs.md based on concepts.md.
Output specific additions needed." > improvements.md 2>&1

# 4. Apply improvements (back to Claude Code)
# Read improvements.md and apply edits
```

---

## Quick Reference Card

```bash
# Basic non-interactive execution
codex exec "prompt" 2>&1

# With image input
codex exec -i screenshot.png "prompt" 2>&1

# With file paths (Codex reads the file)
codex exec "Read ./notes.md and summarize" 2>&1

# Code review mode
codex review "review instructions" 2>&1

# PARALLEL EXECUTION (always prefer this)
codex exec "Task 1" > /tmp/out1.txt 2>&1 &
codex exec "Task 2" > /tmp/out2.txt 2>&1 &
codex exec "Task 3" > /tmp/out3.txt 2>&1 &
wait
cat /tmp/out*.txt

# With timeout
timeout 300 codex exec "prompt" 2>&1
```

---

*Follow [@jonnyzzz](https://twitter.com/jonnyzzz) on X and [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) for more on AI agents and developer tooling.*
