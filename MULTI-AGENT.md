# MULTI-AGENT.md - AI Agent Orchestration Patterns

## Purpose

This document instructs AI agents on how to orchestrate multiple sub-agents for complex tasks. Based on **Recursive Language Models (RLM)** patterns - see RLM.md for theoretical foundation.

**Key insight:** Complex tasks benefit from decomposition into parallel sub-agents, each with focused context and specific goals. This reduces context rot and increases throughput.

---

## Related Skill Files

| File | Purpose |
|------|---------|
| **RLM.md** | Theoretical foundation - when/how to decompose tasks |
| **CODEX.md** | Using Codex CLI as sub-agent for multimodal/focused tasks |
| **GEMINI.md** | Using Gemini CLI as sub-agent for cross-validation |
| **CLAUDE.md** | Repository-specific instructions |
| **SKILL.md** | Writing style guide |

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

## Part 2: Agent Types and Capabilities

### Available Agent Types (Claude Code)

| Agent Type | Best For | Tools Available |
|------------|----------|-----------------|
| `Explore` | Codebase exploration, file search | Glob, Grep, Read |
| `general-purpose` | Complex multi-step tasks | All tools |
| `Plan` | Architecture design, implementation planning | All tools |
| `claude-code-guide` | Documentation lookup | Read, WebFetch |

### External Agent CLIs

| CLI | Best For | Invocation |
|-----|----------|------------|
| **codex** | Focused non-interactive tasks, PDF analysis | `codex exec -i file.pdf "prompt"` |
| **gemini** | Alternative perspective, cross-validation | `gemini "prompt"` |

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
You are analyzing the jonnyzzz.com Jekyll blog repository.

CONTEXT:
This is part of a multi-agent analysis to create comprehensive AI instructions.
Other agents are analyzing: content, git history, branding.

TASKS:
1. Read _config.yml to understand site configuration
2. Examine _layouts/ and _includes/ for template structure
3. Check _plugins/ for custom functionality
4. Analyze build process (in.sh, build.sh, Dockerfile)

FILES TO READ:
- _config.yml - site settings
- in.sh - development workflow
- Dockerfile - build environment
- _plugins/*.rb - custom plugins

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
  Agent 1: Technical structure (config, build, plugins)
  Agent 2: Content analysis (posts, talks)
  Agent 3: Git history (patterns, contributors)
  Agent 4: Style/branding (about, social links)
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

## Part 8: CLI Integration

### Spawning Codex Sub-Agents

```bash
# Non-interactive focused task
codex exec "Your detailed prompt" 2>&1

# With file input (PDF, image, etc.)
codex exec -i file.pdf "Analyze this document" 2>&1

# With model selection
codex exec -m gpt-5.2-codex "Complex analysis task" 2>&1

# Capture output for later processing
codex exec "prompt" > /tmp/result.txt 2>&1
```

See **CODEX.md** for complete reference.

### Spawning Gemini Sub-Agents

```bash
# Non-interactive focused task
gemini "Your detailed prompt" 2>&1

# With approval mode for file operations
gemini --approval-mode yolo "Task requiring file access" 2>&1

# Capture output
gemini "prompt" > /tmp/result.txt 2>&1
```

See **GEMINI.md** for complete reference.

### Parallel Execution Pattern

```bash
# Launch multiple sub-agents in parallel
codex exec -i doc1.pdf "Analyze section 1" > /tmp/r1.txt 2>&1 &
codex exec -i doc2.pdf "Analyze section 2" > /tmp/r2.txt 2>&1 &
gemini "Cross-validate approach" > /tmp/r3.txt 2>&1 &

# Wait for all
wait

# Collect results
cat /tmp/r1.txt /tmp/r2.txt /tmp/r3.txt
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
