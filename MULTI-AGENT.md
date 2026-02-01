# MULTI-AGENT.md - AI Agent Orchestration Patterns

**Version:** v1.0.8
**Last Updated:** 2026-01-24

## Purpose

Orchestrate multiple sub-agents for complex tasks using **Recursive Language Models (RLM)** patterns.

**Core insight:** Decompose complex tasks into parallel sub-agents with focused context. This prevents context rot and maximizes throughput.

**Related Documentation:**
- [RLM.md](https://jonnyzzz.com/RLM.md) - When/how to decompose tasks
- [RLM-extra.md](https://jonnyzzz.com/RLM-extra.md) - Detailed reference, benchmarks, templates
- [CLAUDE-CODE.md](https://jonnyzzz.com/CLAUDE-CODE.md) - Claude Code CLI reference
- [CODEX.md](https://jonnyzzz.com/CODEX.md) - Codex CLI reference
- [GEMINI.md](https://jonnyzzz.com/GEMINI.md) - Gemini CLI reference

---

## Part 1: When to Use Multi-Agent Orchestration

### Decision Matrix

| Condition | Single Agent | Multi-Agent |
|-----------|--------------|-------------|
| Context < 50K tokens | ✓ | |
| Context > 50K tokens | | ✓ |
| Single focused task | ✓ | |
| Multiple independent subtasks | | ✓ |
| Sequential dependencies | ✓ | |
| Parallelizable workload | | ✓ |
| Cross-validation needed | | ✓ |
| Different perspectives needed | | ✓ |

### RLM Triggers

Activate multi-agent when:
1. **Context Size:** > 50K tokens or > 10 files
2. **Task Complexity:** Multi-hop reasoning, aggregation, classification
3. **Quality Requirements:** Cross-validation, multiple perspectives
4. **Time Constraints:** Parallel execution faster than sequential

---

## Part 2: Agent Types and Tool Access

### Built-in Agents (Claude Code Task Tool)

| Agent Type | Best For | Tools Available |
|------------|----------|-----------------|
| `Explore` | Codebase exploration, file search | Glob, Grep, Read |
| `general-purpose` | Complex multi-step tasks | All tools |
| `Plan` | Architecture design, implementation planning | All tools |

### External CLI Agents

| CLI | Best For | Documentation |
|-----|----------|---------------|
| **claude** | Web research, browser automation, general coding | [CLAUDE-CODE.md](https://jonnyzzz.com/CLAUDE-CODE.md) |
| **codex** | IntelliJ IDE work, PDF/image analysis, full MCP access | [CODEX.md](https://jonnyzzz.com/CODEX.md) |
| **gemini** | Cross-validation, alternative perspective | [GEMINI.md](https://jonnyzzz.com/GEMINI.md) |

**See CLI-specific docs for:**
- Installation and setup instructions
- Command syntax and flags
- Tool access modes
- Examples and quick reference

---

## Part 3: MCP Server Visibility

**MCP servers must be registered once, then all sub-agents inherit them automatically.**

### Registration

```bash
# Find MCP Steroid URL (written by IntelliJ to ~/.*.mcp-steroid)
cat ~/.*.mcp-steroid

# Register for Claude Code
claude mcp add --transport http intellij-steroid <URL>
claude mcp add playwright npx @playwright/mcp@latest
claude mcp list

# Register for Codex
codex mcp add intellij --url <URL>
codex mcp add playwright npx "@playwright/mcp@latest"
codex mcp list
```

### Visibility Matrix

| CLI | Playwright MCP | MCP Steroid | Best Use Case |
|-----|----------------|--------------|---------------|
| **claude** | ✅ Yes (if registered) | ✅ Yes (if registered) | Web research, browser automation, general coding |
| **codex** | ✅ Yes (if registered) | ✅ Yes (if registered) | IntelliJ IDE operations, full MCP access |
| **gemini** | ❌ No | ❌ No | Cross-validation, alternative perspective, non-MCP tasks |

**Key insight:** Once registered with `claude mcp add` or `codex mcp add`, MCP servers are automatically available to ALL sub-agents, regardless of command-line flags.

### Task Assignment Based on MCP Needs

**IntelliJ Platform Development:**
- ✅ Use `claude` or `codex` (both see MCP Steroid when registered)
- Tools: `steroid_execute_code`, `steroid_open_project`, PSI, refactoring APIs

**Browser Automation:**
- ✅ Use `claude` or `codex` (both have Playwright MCP when registered)
- ❌ Don't use `gemini` (no MCP support)

**Pure Code Analysis:**
- ✅ Use any CLI
- Consider `gemini` for alternative perspective without MCP overhead

---

## Part 4: Working Directory & Config Inheritance

**Always spawn sub-agents from the correct working directory to inherit configurations.**

### What Sub-Agents Inherit

1. **`.claude/` directory** - Settings, commands, hooks, rules (claude only)
2. **`CLAUDE.md`, `AGENTS.md`** - Project guidelines
3. **`.mcp.json`** - MCP server configurations (limited - prefer global registration)
4. **Project files** - Git config, editor config, build files

### Recommended Patterns

```bash
# Option 1: Run from project root
cd /path/to/project
<CLI-command-from-docs> "prompt"

# Option 2: Use subshell
(cd /path/to/project && <CLI-command-from-docs> "prompt")
```

**See:**
- [CLAUDE-CODE.md](https://jonnyzzz.com/CLAUDE-CODE.md) for Claude Code invocation
- [CODEX.md](https://jonnyzzz.com/CODEX.md) for Codex invocation (supports -C flag)
- [GEMINI.md](https://jonnyzzz.com/GEMINI.md) for Gemini invocation

### Verification

Spawn agent from project directory with prompt: "What is your current working directory? What MCP servers are available? What config files do you see?"

**Expected output:**
- Working directory: `/path/to/project`
- Config files: `.claude/`, `CLAUDE.md`, etc.
- MCP servers: Playwright, MCP Steroid (if registered)

**See CLI-specific docs for exact invocation commands.**

---

## Part 5: Orchestration Patterns

### Pattern A: Parallel Research Agents

Use when analyzing multiple independent aspects.

```
[Orchestrator]
    |
    +-- Agent 1: "Analyze technical structure"
    +-- Agent 2: "Analyze content patterns"
    +-- Agent 3: "Analyze git history"
    +-- Agent 4: "Analyze style/branding"
    |
[Collect Results] → [Synthesize]
```

**Implementation:**
```
Task(prompt="Analyze X", subagent_type="Explore", run_in_background=true)
Task(prompt="Analyze Y", subagent_type="Explore", run_in_background=true)
Task(prompt="Analyze Z", subagent_type="Explore", run_in_background=true)
TaskOutput(task_id=..., block=true) x N
```

### Pattern B: Pipeline (Sequential)

Use when each stage depends on previous output.

```
[Research] → results
    |
[Planning] → plan
    |
[Implementation] → code
    |
[Review] → feedback
```

**Implementation:**
```
result1 = Task(prompt="Research X", run_in_background=false)
result2 = Task(prompt="Plan based on {result1}", run_in_background=false)
result3 = Task(prompt="Implement {result2}", run_in_background=false)
```

### Pattern C: Partition + Map + Reduce

Use for large inputs exceeding context limits (from RLM.md).

```
[Orchestrator]
    |
[Partition: Split input]
    |
    +-- Agent 1: Process chunk 1
    +-- Agent 2: Process chunk 2
    +-- Agent N: Process chunk N
    |
[Reduce: Aggregate results]
```

**Bash implementation:**
```bash
# Partition
split -l 1000 large_file.txt chunk_

# Map (parallel) - see CODEX.md for exact command syntax
for chunk in chunk_*; do
  <codex-command-from-docs> "Process this chunk" > "${chunk}.result" 2>&1 &
done
wait

# Reduce
cat *.result | <codex-command-from-docs> "Aggregate these results" 2>&1
```

**Note:** Replace `<codex-command-from-docs>` with actual command from [CODEX.md](https://jonnyzzz.com/CODEX.md).

### Pattern D: Cross-Validation

Use to verify quality with different models.

```
[Primary Agent] → output
    |
    +-- [Claude Review] → review 1
    +-- [Codex Review]  → review 2
    +-- [Gemini Review] → review 3
    |
[Incorporate Feedback]
```

**Implementation:**
```bash
# Primary work done by orchestrator, output saved to file

# Cross-validate with different models (parallel)
# See CLI-specific docs for exact command syntax
<claude-command> "Review output.md for technical accuracy" > review_claude.md 2>&1 &
<codex-command> "Review output.md for completeness" > review_codex.md 2>&1 &
<gemini-command> "Review output.md for clarity" > review_gemini.md 2>&1 &
wait

# Synthesize reviews
cat review_*.md
```

**Commands from:**
- [CLAUDE-CODE.md](https://jonnyzzz.com/CLAUDE-CODE.md)
- [CODEX.md](https://jonnyzzz.com/CODEX.md)
- [GEMINI.md](https://jonnyzzz.com/GEMINI.md)

---

## Part 6: Agent Prompt Engineering

### Required Components

Every agent prompt must include:
1. **Context** - What this agent is working on
2. **Specific Tasks** - Numbered, actionable items
3. **Files to Read** - Explicit paths when known
4. **Output Format** - Exact structure expected
5. **Constraints** - What to include/exclude

### Template

```
You are [role] analyzing [target] for [purpose].

CONTEXT:
[Brief background - what larger task this is part of]

TASKS:
1. [First specific action]
2. [Second specific action]
3. [Third specific action]

FILES TO READ:
- [path/to/file1] - [what to extract]
- [path/to/file2] - [what to extract]

OUTPUT FORMAT:
## Section 1: [Name]
[Description of expected content]

## Section 2: [Name]
[Description of expected content]

CONSTRAINTS:
- [Constraint 1]
- [Constraint 2]
- [What NOT to do]
```

### Example: Repository Analysis Agent

```
You are analyzing a software repository.

CONTEXT:
Multi-agent analysis to understand codebase structure. Other agents analyze: dependencies, tests, documentation.

TASKS:
1. Read configuration files to understand project settings
2. Examine source directory structure
3. Check for custom tooling or plugins
4. Analyze build process and scripts

FILES TO READ:
- Configuration files (package.json, pyproject.toml, etc.)
- Build scripts
- Dockerfile (if present)
- Custom plugins/extensions

OUTPUT FORMAT:
## Tech Stack
| Component | Technology | Version |

## Build Process
Step-by-step description

## Custom Features
List with explanations

## Key Configuration
Important settings

CONSTRAINTS:
- Focus on technical aspects only
- Do not analyze content or style
- Include exact file paths for references
```

---

## Part 7: Parallel Execution Patterns

**Always run independent sub-agents in parallel for maximum throughput.**

### Background Jobs (Bash)

```bash
# Launch multiple agents IN PARALLEL
<CLI-command-1> "Task 1" > /tmp/out1.txt 2>&1 &
<CLI-command-2> "Task 2" > /tmp/out2.txt 2>&1 &
<CLI-command-3> "Task 3" > /tmp/out3.txt 2>&1 &

# Wait for ALL to complete
wait

# Collect and combine results
cat /tmp/out1.txt /tmp/out2.txt /tmp/out3.txt
```

### Timeout Protection

```bash
# Run parallel tasks with timeout (macOS: use gtimeout from coreutils)
timeout 300 <CLI-command-1> "Task 1" > /tmp/out1.txt 2>&1 &
timeout 300 <CLI-command-2> "Task 2" > /tmp/out2.txt 2>&1 &
timeout 300 <CLI-command-3> "Task 3" > /tmp/out3.txt 2>&1 &
wait
```

### Parallel Map Pattern

```bash
# Process multiple files in parallel
for file in src/module1.ts src/module2.ts src/module3.ts; do
  <CLI-command> "Read $file and identify potential bugs" > "/tmp/analysis-$(basename $file).txt" 2>&1 &
done
wait

# Aggregate results
cat /tmp/analysis-*.txt
```

**Get exact commands from:**
- [CLAUDE-CODE.md](https://jonnyzzz.com/CLAUDE-CODE.md)
- [CODEX.md](https://jonnyzzz.com/CODEX.md)
- [GEMINI.md](https://jonnyzzz.com/GEMINI.md)

---

## Part 8: Automation Scripts

**Create bash or Python scripts for reproducible orchestration.**

### Python Template (with UV)

```python
#!/usr/bin/env python3
"""Parallel agent orchestration with Python.

Get CLI commands from:
- CLAUDE-CODE.md for Claude Code invocation
- CODEX.md for Codex invocation
- GEMINI.md for Gemini invocation
"""
import subprocess
import asyncio
from pathlib import Path

async def run_agent(cmd: list[str], output_file: Path) -> int:
    """Run CLI agent and capture output."""
    with output_file.open('w') as f:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=f,
            stderr=subprocess.STDOUT
        )
        return await proc.wait()

async def main():
    """Launch 3 agents in parallel."""
    # Replace with actual commands from CLI docs
    claude_cmd = ["bash", "-c", "<command-from-CLAUDE-CODE.md>"]
    codex_cmd = ["bash", "-c", "<command-from-CODEX.md>"]
    gemini_cmd = ["bash", "-c", "<command-from-GEMINI.md>"]

    tasks = [
        run_agent(claude_cmd, Path("/tmp/out1.txt")),
        run_agent(codex_cmd, Path("/tmp/out2.txt")),
        run_agent(gemini_cmd, Path("/tmp/out3.txt"))
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

**Run with UV:**
```bash
uv run parallel_agents.py
```

### Bash Script Template

```bash
#!/usr/bin/env bash
# parallel-agents.sh - Launch multiple sub-agents in parallel
# Get CLI commands from CLAUDE-CODE.md, CODEX.md, or GEMINI.md

set -euo pipefail

# Configuration
TASKS=(
    "Task 1: Analyze authentication module"
    "Task 2: Analyze database layer"
    "Task 3: Analyze API endpoints"
)
OUTPUT_DIR="/tmp/agents"
TIMEOUT_SEC=300

# Replace with actual command from CLI doc
CLI_COMMAND="<command-from-CLI-doc>"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Launch agents in parallel
echo "=== Launching ${#TASKS[@]} agents in parallel ==="
pids=()

for i in "${!TASKS[@]}"; do
    task="${TASKS[$i]}"
    output_file="$OUTPUT_DIR/agent-$((i+1)).txt"

    echo "Starting agent $((i+1)): $task"

    # Launch in background with timeout protection
    (
        timeout "$TIMEOUT_SEC" bash -c "$CLI_COMMAND \"$task\"" > "$output_file" 2>&1
    ) &
    pids+=($!)
done

# Wait for all agents
echo "Waiting for all agents to complete..."
for pid in "${pids[@]}"; do
    wait "$pid" && echo "Agent $pid completed" || echo "Agent $pid failed"
done

# Aggregate results
echo ""
echo "=== Aggregated Results ==="
cat "$OUTPUT_DIR"/agent-*.txt

echo ""
echo "=== Execution Complete ==="
echo "Individual outputs: $OUTPUT_DIR"
```

**Make executable:**
```bash
chmod +x parallel-agents.sh
./parallel-agents.sh
```

---

## Part 9: Error Handling

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `command not found` | CLI not installed | Install via official instructions |
| `timeout` | Task too complex | Break into smaller sub-tasks, increase timeout |
| `context length exceeded` | Input too large | Use RLM Partition+Map pattern |
| `rate limit` | Too many requests | Add delays between calls, use different API keys |
| `permission denied` | Sandbox restrictions | Check approval modes, working directory |
| Exit code 41 | API key missing (Gemini) | Set `GEMINI_API_KEY` environment variable |
| Exit code 124 | Timeout exceeded | Increase timeout or split task |

### Retry Logic Pattern

```bash
MAX_RETRIES=3
RETRY_COUNT=0
TIMEOUT_SEC=300

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  if timeout $TIMEOUT_SEC <CLI-command> "prompt" 2>&1; then
    echo "✅ SUCCESS"
    break
  fi
  EXIT_CODE=$?
  echo "⚠️ Attempt $((RETRY_COUNT+1))/$MAX_RETRIES failed (exit $EXIT_CODE)"
  RETRY_COUNT=$((RETRY_COUNT + 1))
  sleep $((RETRY_COUNT * 2))  # Exponential backoff: 2s, 4s, 6s
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo "❌ ERROR: All retries exhausted"
  exit 1
fi
```

### Timeout Recommendations by Task Type

| Task Type | Recommended Timeout | Rationale |
|-----------|---------------------|-----------|
| Simple query (< 100 tokens) | 30s | Quick response expected |
| File analysis (1-5 files) | 120s | Reading + reasoning |
| Complex analysis (5-10 files) | 300s | Multiple file ops + synthesis |
| Large codebase scan | 600s+ | Extensive file operations |
| Nested sub-agent spawn | 180s | Parent + child startup overhead |
| MCP initialization | Add 10-15s | Server startup time |

### Exit Code Detection

```bash
<CLI-command> "prompt" 2>&1
EXIT_CODE=$?

case $EXIT_CODE in
  0)
    echo "✅ Success"
    ;;
  1)
    echo "⚠️ General error - check output for details"
    ;;
  41)
    echo "🔑 API key missing - Set GEMINI_API_KEY (Gemini specific)"
    ;;
  124)
    echo "⏱️ Timeout - Increase timeout value or split task into smaller chunks"
    ;;
  *)
    echo "❌ Unknown error: exit code $EXIT_CODE"
    ;;
esac
```

### Token Limit Detection

```bash
output=$(<CLI-command> "prompt" 2>&1)

if echo "$output" | grep -qi "context length\|token limit\|too long\|maximum context"; then
  echo "⚠️ Token limit exceeded"
  echo "Solution: Use RLM Partition+Map+Reduce strategy"
  echo "See: https://jonnyzzz.com/RLM.md"
fi
```

### Rate Limit Handling

```bash
# Add delays between parallel agents to avoid rate limits
for task in "${TASKS[@]}"; do
    <CLI-command> "$task" > "output-$i.txt" 2>&1 &
    sleep 2  # 2-second delay between launches
done
wait
```

**Get specific commands from:**
- [CLAUDE-CODE.md](https://jonnyzzz.com/CLAUDE-CODE.md)
- [CODEX.md](https://jonnyzzz.com/CODEX.md)
- [GEMINI.md](https://jonnyzzz.com/GEMINI.md)

### Collecting and Synthesizing Results

**Parallel result collection:**
```
# Launch agents
agent1_id = Task(..., run_in_background=true)
agent2_id = Task(..., run_in_background=true)
agent3_id = Task(..., run_in_background=true)

# Wait for all (can be parallel)
result1 = TaskOutput(task_id=agent1_id, block=true)
result2 = TaskOutput(task_id=agent2_id, block=true)
result3 = TaskOutput(task_id=agent3_id, block=true)

# Synthesize
# - Merge complementary information
# - Resolve conflicts
# - Create unified output
```

**Synthesis guidelines:**
1. **Complementary Info:** Concatenate/merge directly
2. **Overlapping Info:** Keep the more detailed version
3. **Conflicting Info:** Verify against source files, prefer agent with direct access
4. **Gaps:** Note what wasn't covered, spawn additional agent if needed

**Validation checklist:**
- [ ] All expected sections present?
- [ ] File paths referenced actually exist?
- [ ] Numbers/statistics plausible?
- [ ] No obvious contradictions between agents?
- [ ] Adequate depth for the task?

---

## Part 10: Best Practices

### DO

1. **Fetch documentation locally** - Download all referenced .md files from https://jonnyzzz.com to project directory for faster access and offline use:
   ```bash
   curl -O https://jonnyzzz.com/RLM.md
   curl -O https://jonnyzzz.com/MULTI-AGENT.md
   curl -O https://jonnyzzz.com/CLAUDE-CODE.md
   curl -O https://jonnyzzz.com/CODEX.md
   curl -O https://jonnyzzz.com/GEMINI.md
   ```
   Sub-agents can then read files directly instead of web fetching.

2. **Explicit prompts** - Each agent starts fresh, no shared context
3. **Specific output formats** - Reduces synthesis effort
4. **Parallel when possible** - 5 agents in 1 minute vs 5 minutes sequential
5. **Cross-validate important work** - Different models catch different issues
6. **Capture stderr** - Use `2>&1` to see all output including errors
7. **Add timeouts** - Prevent indefinite hangs with `timeout` command
8. **Provide complete context** - Each call is isolated with no conversation history
9. **Give sub-agents full access** - Don't restrict tools unnecessarily

### DON'T

1. **Assume shared context** - Each agent is isolated
2. **Over-parallelize** - Diminishing returns past 5-7 agents
3. **Skip validation** - Agent outputs need verification
4. **Ignore failures** - Have fallback strategies
5. **Chain without checkpoints** - Save intermediate results
6. **Chain dependencies** - Results aren't automatically passed between calls
7. **Overload prompts** - One focused task per sub-agent call
8. **Run sequentially** - Always parallelize independent tasks

---

## Part 11: Cost & Budget Management

### Token Usage Estimates

Understanding token consumption helps you make informed decisions about agent orchestration.

| Agent Operation | Typical Token Range | Notes |
|----------------|-------------------|--------|
| Simple query (< 100 tokens) | 500-2K tokens | Quick answer, minimal context |
| File analysis (1-5 files) | 5K-20K tokens | Reading + reasoning |
| Complex analysis (5-10 files) | 20K-50K tokens | Multiple file reads + synthesis |
| Large codebase scan | 50K-200K tokens | Extensive grep/glob operations |
| Cross-validation task | 10K-30K tokens | Running same task with different model |
| Nested sub-agent spawn | +20% overhead | Parent monitors child execution |
| MCP operations | +10-30% overhead | IDE/browser automation adds context |

### Cost-Aware Orchestration Strategies

**1. Sequential vs Parallel Trade-off**

| Strategy | Time | Cost | When to Use |
|----------|------|------|-------------|
| Sequential (1 agent) | Slowest | Lowest | Budget-critical, non-urgent tasks |
| Parallel (3-5 agents) | 3-5x faster | 3-5x cost | Time-sensitive, budget available |
| Hybrid (1 + background) | Moderate | Moderate | Balance of cost and speed |

**2. Budget Tiers**

**Low Budget (< 100K tokens/day):**
- Use sequential execution for most tasks
- Reserve parallel execution for critical paths only
- Prefer cheaper models (haiku) for simple tasks
- Use cross-validation sparingly (1-2 tasks/day max)

**Medium Budget (100K-500K tokens/day):**
- Parallel execution for independent tasks (3-5 agents)
- Cross-validation for important outputs
- Mix of models: sonnet for complex, haiku for simple
- Nested sub-agents when needed

**High Budget (500K+ tokens/day):**
- Aggressive parallelization (5-10 agents)
- Cross-validation as standard practice
- Nested orchestration without constraints
- Premium models (opus) for critical analysis

**3. Cost Optimization Techniques**

```bash
# Technique 1: Use cheaper models for simple tasks
# Instead of spawning sonnet for file listing, use grep/glob directly
<CLI-command-from-docs> --model haiku "List all .md files in directory" 2>&1

# Technique 2: Batch related tasks
# Instead of: 3 separate agent calls
# Do: 1 agent call with combined prompt
<CLI-command-from-docs> "Analyze files A, B, C and summarize each" 2>&1

# Technique 3: Cache intermediate results
# Avoid re-running expensive operations
if [ ! -f /tmp/analysis-cache.txt ]; then
  <CLI-command-from-docs> "Expensive analysis" > /tmp/analysis-cache.txt 2>&1
fi
cat /tmp/analysis-cache.txt

# Technique 4: Use RLM for very large files
# Instead of: Single agent reading 100K line file (massive tokens)
# Do: Partition + Map + Reduce (distributed cost, parallel execution)
# See RLM.md for implementation
```

**4. Cost Monitoring**

```bash
# Track token usage per agent call
echo "Agent call started: $(date)" >> /tmp/agent-log.txt
<CLI-command-from-docs> "prompt" 2>&1 | tee -a /tmp/agent-output.txt
wc -w /tmp/agent-output.txt  # Rough token estimate: words * 1.3

# Aggregate daily usage
cat /tmp/agent-log.txt | grep "Agent call" | wc -l
# Shows total agent invocations

# Set budget alerts
DAILY_CALL_LIMIT=50
CALL_COUNT=$(cat /tmp/agent-log.txt | grep "Agent call" | wc -l)
if [ $CALL_COUNT -gt $DAILY_CALL_LIMIT ]; then
  echo "⚠️ Budget exceeded: $CALL_COUNT/$DAILY_CALL_LIMIT calls today"
fi
```

**5. When to Parallelize vs Serialize**

| Scenario | Decision | Reasoning |
|----------|----------|-----------|
| 5 independent file analyses | PARALLEL | No dependencies, time-sensitive |
| 5-step sequential pipeline | SEQUENTIAL | Each depends on previous result |
| Cross-validation (same input) | PARALLEL | Independent checks, speed matters |
| Large file split into chunks | PARALLEL | RLM pattern, embarrassingly parallel |
| Budget < 50K tokens remaining | SEQUENTIAL | Preserve budget for critical tasks |
| Time-critical delivery (< 5 min) | PARALLEL | Speed over cost |

**6. Cost Per Pattern**

| Pattern | Agents | Token Estimate | Time | Use Case |
|---------|--------|----------------|------|----------|
| Pattern A: Parallel Explore | 4-5 | 40K-100K | 1-2 min | Codebase analysis |
| Pattern B: Sequential Pipeline | 3-4 | 30K-60K | 3-5 min | Content generation |
| Pattern C: RLM Map-Reduce | 5-10 | 50K-150K | 2-3 min | Large file processing |
| Pattern D: Cross-Validation | 2-3 | 20K-60K | 1-2 min | Quality assurance |

**7. Budget-Aware Best Practices**

1. **Profile first, parallelize second** - Understand task cost before scaling
2. **Set daily/weekly token budgets** - Monitor and enforce limits
3. **Use haiku for exploration** - Reserve sonnet/opus for synthesis
4. **Cache expensive operations** - Don't repeat costly analysis
5. **Fail fast** - Add timeouts to prevent runaway costs
6. **Review logs weekly** - Identify cost optimization opportunities
7. **Balance speed and cost** - Not every task needs 10 parallel agents

---

## Quick Reference

### CLI Comparison

| Feature | claude | codex | gemini |
|---------|--------|-------|--------|
| Interactive mode | ✓ | ✓ | ✓ |
| Non-interactive | `claude -p` | `codex exec` | `gemini` one-shot |
| File input | Read tool | `-i` flag | via prompt |
| Image/PDF support | Read tool | `-i` flag | via prompt |
| Model selection | in settings | `-m` flag | `-m` flag |
| Parallel execution | background jobs | background jobs | background jobs |
| **Playwright MCP** | ✅ Yes (if registered) | ✅ Yes (if registered) | ❌ No |
| **MCP Steroid** | ✅ Yes (if registered) | ✅ Yes (if registered) | ❌ No |

### Command Patterns

```bash
# Parallel research
Task(subagent_type="Explore", run_in_background=true) x N
TaskOutput(block=true) x N

# External sub-agents - see CLI docs for exact commands:
# - CLAUDE-CODE.md for Claude Code
# - CODEX.md for Codex
# - GEMINI.md for Gemini

# Cross-validation (pattern)
<claude-command> "Review output.md" > review_claude.md 2>&1 &
<codex-command> "Review output.md" > review_codex.md 2>&1 &
<gemini-command> "Review output.md" > review_gemini.md 2>&1 &
wait

# RLM partition pattern
split input into chunks
for chunk: spawn agent in background
wait all
aggregate results
```

### When to Use Which CLI

| Scenario | Best Tool | Reason |
|----------|-----------|--------|
| **IntelliJ IDE operations** | claude or codex | Both see MCP Steroid when registered |
| **Browser automation** | claude or codex | Both have Playwright MCP when registered |
| **Web research** | claude | Built-in WebSearch, WebFetch |
| **Image/PDF analysis** | codex | Native `-i` flag support |
| **Cross-validation** | gemini | Different model, alternative perspective |
| **Primary orchestration** | claude | Full tool suite, conversation context |
| **Focused non-interactive** | codex | `exec` mode, best MCP visibility |
| **Long context tasks** | gemini | Large context window |
| **Pure code analysis** | gemini | Good without MCP dependencies |

---

*Follow [@jonnyzzz](https://twitter.com/jonnyzzz) on X and [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) for more on AI agents and developer tooling.*
