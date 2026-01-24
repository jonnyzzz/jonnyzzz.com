# MULTI-AGENT.md - AI Agent Orchestration Patterns

## Purpose

This document instructs AI agents on how to orchestrate multiple sub-agents for complex tasks. Based on **Recursive Language Models (RLM)** patterns - see RLM.md for theoretical foundation.

**Key insight:** Complex tasks benefit from decomposition into parallel sub-agents, each with focused context and specific goals. This reduces context rot and increases throughput.

---

## Related Skill Files

| File | Purpose | Online |
|------|---------|--------|
| **RLM.md** | Core RLM instructions - when/how to decompose tasks | [View](https://jonnyzzz.com/RLM.md) |
| **RLM-extra.md** | Detailed RLM reference - templates, benchmarks, error handling | [View](https://jonnyzzz.com/RLM-extra.md) |
| **CLAUDE-CODE.md** | Using Claude Code CLI as sub-agent (⚠️ limited MCP visibility) | [View](https://jonnyzzz.com/CLAUDE-CODE.md) |
| **CODEX.md** | Using Codex CLI as sub-agent (✅ BEST for IntelliJ MCP) | [View](https://jonnyzzz.com/CODEX.md) |
| **GEMINI.md** | Using Gemini CLI as sub-agent for cross-validation (no MCP) | [View](https://jonnyzzz.com/GEMINI.md) |
| **MULTI-AGENT.md** | This document - orchestration patterns | [View](https://jonnyzzz.com/MULTI-AGENT.md) |

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

### RLM Trigger Integration

From RLM.md - activate multi-agent when:
1. **Context Size:** > 50K tokens or > 10 files
2. **Task Complexity:** Multi-hop reasoning, aggregation, classification
3. **Quality Requirements:** Cross-validation, multiple perspectives
4. **Time Constraints:** Parallel execution faster than sequential

---

## Part 1.5: MCP Server Visibility (CRITICAL)

**IMPORTANT:** MCP servers must be registered to be available. Once registered, Claude Code and Codex automatically inherit them.

### MCP Visibility Matrix

| CLI | Playwright MCP | IntelliJ MCP Steroid | Best Use Case |
|-----|----------------|---------------------|---------------|
| **Claude Code** | ✅ Yes (if registered) | ✅ Yes (if registered) | Web research, browser automation, general coding |
| **Codex** | ✅ Yes (if registered) | ✅ Yes (if registered) | IntelliJ IDE operations, full MCP access |
| **Gemini** | ❌ No | ❌ No | Cross-validation, alternative perspective, non-MCP tasks |

### MCP Registration Requirements

**To use MCP servers with sub-agents, they must be registered first:**

```bash
# Find IntelliJ MCP URL (written by IntelliJ to ~/.*.mcp-steroid)
cat ~/.*.mcp-steroid  # Shows URL and registration commands

# Claude Code registration (use URL from file above)
claude mcp add --transport http intellij-steroid <URL>
claude mcp add playwright npx @playwright/mcp@latest
claude mcp list  # Verify registration

# Codex registration (use URL from file above)
codex mcp add intellij --url <URL>
codex mcp add playwright npx "@playwright/mcp@latest"
codex mcp list  # Verify registration
```

**Key insight:** Once registered, MCP servers are automatically inherited by ALL sub-agents regardless of command-line flags used to spawn them.

### Implications for Task Assignment

**IntelliJ Platform Development:**
- ✅ **Use Claude Code or Codex** - both see IntelliJ MCP when registered
- Tools available: `steroid_execute_code`, `steroid_open_project`, PSI operations, refactoring APIs

**Browser Automation:**
- ✅ **Use Claude Code or Codex** - both have Playwright MCP when registered
- ❌ **Don't use Gemini** - no MCP support

**Pure Code Analysis (no IDE integration needed):**
- ✅ **Use any CLI** - Gemini works well for this
- Consider Gemini for alternative perspective without MCP overhead

**Working Directory:** Always spawn sub-agents from correct working directory to inherit project configurations:
```bash
(cd /path/to/project && <CLI-command> "prompt")
# or with Codex: codex -C /path/to/project --full-auto exec "prompt"
```

**See:** [CLAUDE-CODE.md](https://jonnyzzz.com/CLAUDE-CODE.md), [CODEX.md](https://jonnyzzz.com/CODEX.md), [GEMINI.md](https://jonnyzzz.com/GEMINI.md) for complete details on MCP registration and usage.

---

## Part 2: Agent Types and Capabilities

### Available Agent Types (Claude Code)

| Agent Type | Best For | Tools Available |
|------------|----------|-----------------|
| `Explore` | Codebase exploration, file search | Glob, Grep, Read |
| `general-purpose` | Complex multi-step tasks | All tools |
| `Plan` | Architecture design, implementation planning | All tools |
| `claude-code-guide` | Documentation lookup | Read, WebFetch |

### External Agent CLIs

| CLI | Best For | Playwright MCP | IntelliJ MCP | Invocation |
|-----|----------|----------------|--------------|------------|
| **claude-code** | Web research, browser automation | ✅ Yes (if registered) | ✅ Yes (if registered) | `echo "prompt" \| claude -p --tools default --permission-mode dontAsk` |
| **codex** | IntelliJ IDE work, PDF analysis, full MCP access | ✅ Yes (if registered) | ✅ Yes (if registered) | `codex --full-auto exec "prompt"` |
| **gemini** | Cross-validation, alternative perspective | ❌ No | ❌ No | `gemini --approval-mode auto_edit "prompt"` |

**Note:** MCP servers must be registered once using `claude mcp add` or `codex mcp add` commands. Once registered, they are automatically available to all sub-agents.

**Full documentation:**
- [CLAUDE-CODE.md](https://jonnyzzz.com/CLAUDE-CODE.md) - Complete Claude Code sub-agent guide
- [CODEX.md](https://jonnyzzz.com/CODEX.md) - Complete Codex sub-agent guide (includes sandbox workarounds)
- [GEMINI.md](https://jonnyzzz.com/GEMINI.md) - Complete Gemini sub-agent guide

---

## Part 3: Orchestration Patterns

### Pattern A: Parallel Research Agents

Use when analyzing multiple independent aspects of a codebase or problem.

```
[Orchestrator]
    |
    +-- Agent 1: "Analyze technical structure"
    +-- Agent 2: "Analyze content patterns"
    +-- Agent 3: "Analyze git history"
    +-- Agent 4: "Analyze style/branding"
    |
[Collect Results]
    |
[Synthesize]
```

**Implementation:**
```
Task(prompt="Analyze X", subagent_type="Explore", run_in_background=true)
Task(prompt="Analyze Y", subagent_type="Explore", run_in_background=true)
Task(prompt="Analyze Z", subagent_type="Explore", run_in_background=true)
...
TaskOutput(task_id=..., block=true) x N
```

### Pattern B: Pipeline (Sequential)

Use when each stage depends on previous output.

```
[Research Agent] --> results
       |
[Planning Agent] --> plan
       |
[Implementation Agent] --> code
       |
[Review Agent] --> feedback
```

**Implementation:**
```
result1 = Task(prompt="Research X", ..., run_in_background=false)
result2 = Task(prompt="Plan based on {result1}", ..., run_in_background=false)
result3 = Task(prompt="Implement {result2}", ..., run_in_background=false)
```

### Pattern C: Partition + Map + Reduce

Use for large inputs that exceed context limits. From RLM.md.

```
[Orchestrator]
    |
[Partition: Split input into chunks]
    |
    +-- Agent 1: Process chunk 1
    +-- Agent 2: Process chunk 2
    +-- Agent N: Process chunk N
    |
[Reduce: Aggregate results]
```

**Implementation with External CLIs:**
```bash
# Partition
split -l 1000 large_file.txt chunk_

# Map (parallel)
for chunk in chunk_*; do
  codex exec -i "$chunk" "Process this chunk" > "${chunk}.result" &
done
wait

# Reduce
cat *.result | codex exec "Aggregate these results"
```

### Pattern D: Cross-Validation

Use to verify quality by having different agents review.

```
[Primary Agent] --> output
       |
       +-- [Claude Review Agent] --> review 1
       +-- [Codex Review Agent]  --> review 2
       +-- [Gemini Review Agent] --> review 3
       |
[Incorporate Feedback]
```

**Implementation:**
```bash
# Primary work done by orchestrator

# Cross-validate with different models
codex exec -i output.md "Review for accuracy and completeness" > review_codex.md &
gemini "Review output.md for accuracy and completeness" > review_gemini.md &
wait

# Synthesize reviews
```

---

## Part 4: Agent Prompt Engineering

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
This is part of a multi-agent analysis to understand the codebase structure.
Other agents are analyzing: dependencies, tests, documentation.

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

## Part 5: Collecting and Synthesizing Results

### Parallel Result Collection

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

### Synthesis Guidelines

When merging agent outputs:

1. **Complementary Info:** Simply concatenate/merge
2. **Overlapping Info:** Keep the more detailed version
3. **Conflicting Info:** Verify against source files, prefer agent with direct file access
4. **Gaps:** Note what wasn't covered, potentially spawn additional agent

---

## Part 6: Error Handling

### Agent Failures

| Failure Type | Recovery Action |
|--------------|-----------------|
| Timeout | Retry with smaller scope |
| Context overflow | Apply RLM partition strategy |
| Wrong output format | Re-prompt with stricter format spec |
| Incomplete results | Spawn targeted follow-up agent |

### Validation Checklist

After collecting agent results:

- [ ] All expected sections present?
- [ ] File paths referenced actually exist?
- [ ] Numbers/statistics plausible?
- [ ] No obvious contradictions between agents?
- [ ] Adequate depth for the task?

---

## Part 7: Practical Examples

### Example 1: Repository Analysis (5 agents)

```
Phase 1 - Parallel Analysis:
  Agent 1: Technical structure (config, build, dependencies)
  Agent 2: Source code analysis (modules, components)
  Agent 3: Git history (patterns, contributors)
  Agent 4: Documentation (README, API docs)
  Agent 5: Testing setup (tests, CI)

Phase 2 - Parallel Review:
  Agent 6: Review combined output for accuracy
  Agent 7: Cross-check against actual files

Phase 3 - Sequential:
  Apply fixes, commit
```

### Example 2: Large Document Processing (RLM pattern)

```
Phase 1 - Assessment:
  Orchestrator: Check document size, structure

Phase 2 - Partition:
  If > 50K tokens: Split by logical sections

Phase 3 - Map (parallel):
  For each section:
    Codex: Process section with focused prompt

Phase 4 - Reduce:
  Orchestrator: Aggregate all section results
```

### Example 3: Content Creation with Review (pipeline + validation)

```
Phase 1 - Research (parallel):
  Agent 1: Analyze source material
  Agent 2: Research existing patterns
  Agent 3: Gather examples

Phase 2 - Create (sequential):
  Orchestrator: Write content based on research

Phase 3 - Review (parallel cross-validation):
  Codex: Technical accuracy review
  Gemini: Style and clarity review
  Claude Agent: Completeness review

Phase 4 - Incorporate:
  Orchestrator: Apply feedback, finalize
```

---

## Part 8: CLI Integration and Best Practices

### Choosing the Right CLI

**Decision tree:**
1. **Need IntelliJ IDE operations?** → Use **Codex** (only CLI with IntelliJ MCP)
2. **Need browser automation?** → Use **Claude Code** or **Codex** (both have Playwright)
3. **Need cross-validation?** → Use **Gemini** (alternative model)
4. **Pure code analysis?** → Any CLI works, **Gemini** good for alternative perspective

### Spawning Claude Code Sub-Agents

```bash
# From correct working directory (for config inheritance)
echo "Your detailed prompt" | claude -p --tools default --permission-mode dontAsk 2>&1

# With JSON output
echo "prompt" | claude -p --tools default --permission-mode dontAsk --output-format json 2>&1

# Parallel execution
echo "Task 1" | claude -p --tools default --permission-mode dontAsk > /tmp/out1.txt 2>&1 &
echo "Task 2" | claude -p --tools default --permission-mode dontAsk > /tmp/out2.txt 2>&1 &
wait
```

**Note:** Claude Code sub-agents do NOT see IntelliJ MCP. Use Codex for IDE work.

**Full guide:** [CLAUDE-CODE.md](https://jonnyzzz.com/CLAUDE-CODE.md)

### Spawning Codex Sub-Agents (BEST for IntelliJ)

```bash
# Recommended: Full-auto mode with working directory
codex -C /path/to/project --full-auto exec "Your detailed prompt" 2>&1

# With file input (PDF, image, etc.)
codex --full-auto -i file.pdf exec "Analyze this document" 2>&1

# With --json for structured logs
codex --full-auto --json exec "Complex analysis task" 2>&1

# Capture output for later processing
codex --full-auto exec "prompt" > /tmp/result.txt 2>&1

# For nested execution (when running Codex from within Codex)
TMP_HOME=/tmp/codex-home
mkdir -p "$TMP_HOME/.codex"
cp ~/.codex/auth.json "$TMP_HOME/.codex/"
HOME="$TMP_HOME" codex --full-auto exec "prompt" 2>&1
```

**Codex sees BOTH Playwright AND IntelliJ MCP** - use it for IDE operations!

**Full guide:** [CODEX.md](https://jonnyzzz.com/CODEX.md) (includes sandbox workarounds)

### Spawning Gemini Sub-Agents

```bash
# From correct working directory
(cd /path/to/project && gemini --approval-mode auto_edit "Your detailed prompt" 2>&1)

# With YOLO mode (auto-approve everything - use with caution)
gemini --approval-mode yolo "Task requiring file access" 2>&1

# Capture output
gemini --approval-mode auto_edit "prompt" > /tmp/result.txt 2>&1
```

**Note:** Gemini does NOT see MCP servers. Use for non-MCP tasks only.

**Full guide:** [GEMINI.md](https://jonnyzzz.com/GEMINI.md)

### Parallel Execution Pattern

```bash
# Example: IntelliJ analysis + cross-validation
# Use Codex for IDE work, Gemini for review

# Launch in parallel
codex -C /path/to/intellij --full-auto exec "Analyze PSI structure in X.kt" > /tmp/codex.txt 2>&1 &
gemini --approval-mode auto_edit "Review /path/to/intellij/X.kt for code quality" > /tmp/gemini.txt 2>&1 &

# Wait for all
wait

# Collect results
echo "=== Codex Analysis (with IntelliJ MCP) ==="
cat /tmp/codex.txt
echo ""
echo "=== Gemini Review (alternative perspective) ==="
cat /tmp/gemini.txt
```

---

## Part 9: Best Practices

### DO

1. **Explicit prompts** - Each agent starts fresh, no shared context
2. **Specific output formats** - Reduces synthesis effort
3. **Parallel when possible** - 5 agents in 1 minute vs 5 minutes sequential
4. **Cross-validate important work** - Different models catch different issues
5. **Log experiments** - Capture actual output for reproducibility

### DON'T

1. **Assume shared context** - Each agent is isolated
2. **Over-parallelize** - Diminishing returns past 5-7 agents
3. **Skip validation** - Agent outputs need verification
4. **Ignore failures** - Have fallback strategies
5. **Chain without checkpoints** - Save intermediate results

---

## Quick Reference

```
# Parallel research
Task(subagent_type="Explore", run_in_background=true) x N
TaskOutput(block=true) x N

# External sub-agents
codex exec "prompt"           # Focused task
codex exec -i file "prompt"   # With file input
gemini "prompt"               # Alternative model

# Cross-validation
codex exec -i output.md "Review for X" &
gemini "Review output.md for X" &
wait

# RLM partition pattern
split input into chunks
for chunk: spawn agent
wait all
aggregate results
```

---

*Follow [@jonnyzzz](https://twitter.com/jonnyzzz) on X and [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) for more on AI agents and developer tooling.*
