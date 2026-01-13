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

### When NOT to Use Gemini

- Tasks requiring specific Claude Code tools (MCP, browser)
- When Codex non-interactive mode is more appropriate
- Simple edits that don't benefit from cross-validation
- Tasks requiring conversation history access

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
gemini "your prompt here" 2>&1

# Interactive mode
gemini

# Execute prompt then continue interactively
gemini -i "initial prompt"

# With specific model (syntax reference)
gemini -m model-name "prompt" 2>&1
```

### Approval Modes

```bash
# Default - prompts for approval on actions
gemini "prompt" 2>&1

# Auto-approve edits (careful!)
gemini --approval-mode auto_edit "prompt" 2>&1

# YOLO mode - auto-approve everything (dangerous!)
gemini --approval-mode yolo "prompt" 2>&1
# Alias: gemini -y "prompt"
```

### Output Formats

```bash
# Plain text output (default)
gemini "prompt" 2>&1

# JSON output (for parsing)
gemini -o json "prompt" 2>&1

# Streaming JSON
gemini -o stream-json "prompt" 2>&1
```

---

## Spawning Gemini from Claude Code

### Basic Pattern

```bash
# From Claude Code, use Bash tool:
gemini "Your detailed prompt here" 2>&1
```

### For File Analysis

Unlike Codex, Gemini doesn't have an `-i` flag for file input. Instead, include file content in the prompt:

```bash
# Read file content and pass to Gemini
CONTENT=$(cat /path/to/file.md)
gemini "Analyze this content:

$CONTENT

Tasks:
1. Review for accuracy
2. Identify gaps
3. Suggest improvements" 2>&1
```

### Capturing Output

```bash
# Save output to file for later processing
gemini "prompt" > /tmp/gemini-output.txt 2>&1

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

gemini "CONTEXT:
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

## Parallel Execution (CRITICAL)

**Always run independent Gemini sub-agents in parallel** for maximum throughput. Each instance runs in isolation with its own context.

### Multiple Instances

```bash
# Launch multiple Gemini instances IN PARALLEL
gemini "Task 1: analyze section A" > /tmp/out1.txt 2>&1 &
gemini "Task 2: analyze section B" > /tmp/out2.txt 2>&1 &
gemini "Task 3: analyze section C" > /tmp/out3.txt 2>&1 &

# Wait for ALL to complete
wait

# Collect and combine results
cat /tmp/out1.txt /tmp/out2.txt /tmp/out3.txt
```

### Parallel with Timeout Protection

```bash
# Run parallel tasks with timeout (macOS: use gtimeout from coreutils)
timeout 300 gemini "Task 1" > /tmp/out1.txt 2>&1 &
timeout 300 gemini "Task 2" > /tmp/out2.txt 2>&1 &
timeout 300 gemini "Task 3" > /tmp/out3.txt 2>&1 &
wait
```

### Parallel Map Pattern

```bash
# Process multiple files in parallel
for file in src/module1.ts src/module2.ts src/module3.ts; do
  CONTENT=$(cat "$file")
  gemini "Analyze this code:

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
  gemini "Process this chunk:

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
gemini "Review this for accuracy:

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
  if timeout $TIMEOUT_SEC gemini "prompt" 2>&1; then
    break
  fi
  RETRY_COUNT=$((RETRY_COUNT + 1))
  echo "Retry $RETRY_COUNT of $MAX_RETRIES..."
  sleep 5
done
```

---

## Comparing CLI Tools

| Feature | Claude Code | Codex | Gemini |
|---------|-------------|-------|--------|
| Interactive mode | ✓ | ✓ | ✓ |
| Non-interactive | via Task tool | `exec` | one-shot |
| File input | Read tool | `-i` flag | via prompt |
| PDF support | Read tool | `-i` flag | via prompt |
| Model selection | in settings | `-m` flag | `-m` flag |
| Parallel execution | Task tool | background jobs | background jobs |
| MCP support | ✓ | ✓ | ✓ |

### When to Use Which

| Scenario | Best Tool |
|----------|-----------|
| Primary orchestration | Claude Code |
| Focused non-interactive task | Codex |
| PDF/image analysis | Codex |
| Cross-validation review | Gemini |
| Alternative perspective | Gemini |
| Complex multi-step workflow | Claude Code |
| Long context tasks | Gemini (large context) |

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
gemini "prompt" 2>&1

# With model (syntax reference)
gemini -m model-name "prompt" 2>&1

# Auto-approve edits
gemini --approval-mode auto_edit "prompt" 2>&1

# JSON output
gemini -o json "prompt" 2>&1

# With file content
CONTENT=$(cat file.md)
gemini "Analyze: $CONTENT" 2>&1

# Capture output to file
gemini "prompt" > output.txt 2>&1

# PARALLEL EXECUTION (always prefer this)
gemini "Task 1" > /tmp/out1.txt 2>&1 &
gemini "Task 2" > /tmp/out2.txt 2>&1 &
gemini "Task 3" > /tmp/out3.txt 2>&1 &
wait
cat /tmp/out*.txt

# With timeout
timeout 300 gemini "prompt" 2>&1
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
gemini "Cross-validate this document:

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
