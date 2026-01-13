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
# Non-interactive execution (print mode)
claude -p "your prompt here"

# With stdin input
echo "your prompt here" | claude -p

# JSON output format
claude -p --output-format json "prompt"

# Stream JSON output (for real-time processing)
claude -p --output-format stream-json "prompt"
```

### Tool Access Control

```bash
# Allow specific tools only
echo "Read /path/to/file.md and summarize" | claude -p --allowedTools "Read"

# Allow multiple tools
echo "Search and read files" | claude -p --allowedTools "Read,Grep,Glob"

# Allow Bash with specific patterns
echo "Run git status" | claude -p --allowedTools "Bash(git:*)"

# Deny specific tools
claude -p --disallowedTools "Edit,Write" "analyze this code"
```

## Spawning Claude Code from Another Agent

### Basic Pattern

```bash
# Simple execution with prompt as argument
claude -p "Your detailed prompt here" 2>&1

# With stdin (preferred for complex prompts)
echo "Your detailed prompt here" | claude -p 2>&1
```

### With File Context

```bash
# Claude Code will use Read tool to access files
echo "Read /path/to/file.md and extract:
1. Key concepts
2. Implementation patterns
3. Summary in 3 sentences" | claude -p --allowedTools "Read" 2>&1
```

### Capturing Structured Output

```bash
# JSON output for programmatic processing
echo "List 3 main points" | claude -p --output-format json 2>&1

# Parse the result field from JSON
echo "What is 2+2?" | claude -p --output-format json 2>&1 | jq -r '.result'
```

---

## Parallel Execution (CRITICAL)

**Always run independent Claude Code sub-agents in parallel** for maximum throughput. Each instance runs in isolation with its own context.

### From Bash (Background Jobs)

```bash
# Launch multiple Claude Code instances IN PARALLEL
echo "Task 1: Analyze auth module" | claude -p --allowedTools "Read,Grep" > /tmp/out1.txt 2>&1 &
echo "Task 2: Analyze database layer" | claude -p --allowedTools "Read,Grep" > /tmp/out2.txt 2>&1 &
echo "Task 3: Analyze API endpoints" | claude -p --allowedTools "Read,Grep" > /tmp/out3.txt 2>&1 &

# Wait for ALL to complete
wait

# Collect and combine results
cat /tmp/out1.txt /tmp/out2.txt /tmp/out3.txt
```

### Parallel with Timeout Protection

```bash
# Run parallel tasks with timeout (macOS: use gtimeout from coreutils)
timeout 300 bash -c 'echo "Task 1" | claude -p' > /tmp/out1.txt 2>&1 &
timeout 300 bash -c 'echo "Task 2" | claude -p' > /tmp/out2.txt 2>&1 &
timeout 300 bash -c 'echo "Task 3" | claude -p' > /tmp/out3.txt 2>&1 &
wait
```

### Parallel Map Pattern

```bash
# Process multiple files in parallel
for file in src/module1.ts src/module2.ts src/module3.ts; do
  echo "Read $file and identify potential bugs" | \
    claude -p --allowedTools "Read" > "/tmp/analysis-$(basename $file).txt" 2>&1 &
done
wait

# Aggregate results
cat /tmp/analysis-*.txt
```

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
- Provide remediation suggestions" | claude -p --allowedTools "Read" 2>&1
```

---

## Integration with RLM Methodology

### Partition+Map+Reduce Pattern

```bash
# Step 1: PARTITION (orchestrating agent splits the work)
# Create task descriptions for each chunk

# Step 2: MAP (Claude Code sub-agents process IN PARALLEL)
echo "Process chunk 1: $CHUNK1_DESCRIPTION" | claude -p > /tmp/result1.txt 2>&1 &
echo "Process chunk 2: $CHUNK2_DESCRIPTION" | claude -p > /tmp/result2.txt 2>&1 &
echo "Process chunk 3: $CHUNK3_DESCRIPTION" | claude -p > /tmp/result3.txt 2>&1 &
wait

# Step 3: REDUCE (orchestrating agent aggregates results)
# Read /tmp/result*.txt and synthesize final output
```

### Cross-Validation Pattern

```bash
# Primary analysis done by main agent
# Validate with Claude Code sub-agent:
echo "Read /tmp/primary-analysis.md and review for:
1. Logical consistency
2. Missing edge cases
3. Incorrect assumptions
4. Factual errors

Output only issues found, or 'VALIDATED: No issues found' if none." | \
  claude -p --allowedTools "Read" 2>&1
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
  if timeout $TIMEOUT_SEC bash -c 'echo "your prompt" | claude -p' 2>&1; then
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
# Basic non-interactive execution
claude -p "prompt"

# With stdin (better for complex prompts)
echo "prompt" | claude -p

# With specific tools only
echo "prompt" | claude -p --allowedTools "Read,Grep"

# JSON output
echo "prompt" | claude -p --output-format json

# PARALLEL EXECUTION (always prefer this)
echo "Task 1" | claude -p > /tmp/out1.txt 2>&1 &
echo "Task 2" | claude -p > /tmp/out2.txt 2>&1 &
echo "Task 3" | claude -p > /tmp/out3.txt 2>&1 &
wait
cat /tmp/out*.txt

# With timeout
timeout 300 bash -c 'echo "prompt" | claude -p' 2>&1
```
