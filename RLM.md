# RLM.md - Recursive Language Models for AI Agents

## Core Principle

**Context rot** degrades LLM performance as input increases. RLM solves this by treating context as a **variable in external environment**, not neural network input.

```
Traditional: LLM(100K tokens) → attention dilutes → accuracy drops
RLM: LLM(query) + programmatic context access → accuracy maintained
```

**The shift:** Context management becomes **programmatic, not neural**.

---

## When to Activate RLM

Use this decision tree at task start:

```
Context > 50K tokens? ────────────────────────── YES → ACTIVATE RLM
    │
    NO → Context > 16K AND multi-hop reasoning? ─ YES → ACTIVATE RLM
    │
    NO → Files > 5? ─────────────────────────── YES → ACTIVATE RLM
    │
    NO → Proceed directly (no RLM needed)
```

---

## The Six-Step Protocol

Execute **in order** when RLM activated:

### 1. ASSESS → Peek at Context

**Action:** Sample structure before reading full content.

```bash
wc -c file.txt          # Get total size
head -n 100 file.txt    # Preview first 100 lines
ls -lh directory/       # Check file count and sizes
```

**Output:** Understand data type (text/JSON/code), boundaries (files/sections), total scope.

### 2. DECIDE → Select Strategy

**Action:** Match context characteristics to processing strategy.

| Context Size | Strategy | Implementation |
|--------------|----------|----------------|
| < 4K tokens | Direct processing | Read and process normally |
| 4K-50K tokens | Grep first | `grep -r "pattern"` → read matches only |
| > 50K tokens | Partition + Map | Split → parallel sub-agents → aggregate |
| Multiple files (> 5) | Parallel sub-agents | One agent per file/group |

### 3. DECOMPOSE → Partition the Work

Split at **natural boundaries**:
- By file (one agent per file)
- By section (split at headers)
- By record (batch N records per chunk)

**Target:** 4K-10K tokens per sub-task.

### 4. EXECUTE → Run Sub-Agents

**Parallel** if independent, **sequential** if dependent.

Use bash or Python scripts to orchestrate (see Orchestration section below).

### 5. SYNTHESIZE → Combine Results

| Pattern | When |
|---------|------|
| Concatenate | Order matters, no conflicts |
| Merge | Deduplication needed |
| Reduce | Counting, statistics |
| Vote | Classification (majority wins) |

### 6. VERIFY → Check Completeness

- [ ] Original query fully addressed?
- [ ] All partitions contributed?
- [ ] No gaps in coverage?
- [ ] Spot-check 2-3 claims?

---

## Critical Anti-Patterns

**❌ DON'T:**
- Read everything first → Peek → Grep → Read relevant only
- Spawn 100 sub-agents → Group logically, 3-10 per level, max depth 2
- Give sub-agents insufficient context → Include imports, types, usage context
- Split at arbitrary bytes → Split at semantic boundaries
- Skip grep for searchable tasks → `grep -r "pattern"` → Read matches only

---

## Orchestration Scripts

**Create bash or Python scripts to orchestrate sub-agents.** This provides:
- Reproducible execution
- Timeout protection
- Parallel execution control
- Result aggregation

### Bash Template

```bash
#!/bin/bash
# rlm-orchestrate.sh - Parallel sub-agent execution

QUERY="$1"
RESULT_DIR=$(mktemp -d)
TIMEOUT_SEC=300

# PARTITION: Define chunks (customize this)
CHUNKS=("chunk1.txt" "chunk2.txt" "chunk3.txt")

# MAP: Process chunks in parallel
for i in "${!CHUNKS[@]}"; do
    timeout $TIMEOUT_SEC your-agent-cli "${CHUNKS[$i]}" "$QUERY" \
        > "$RESULT_DIR/result_$i.txt" 2>&1 &
done
wait

# REDUCE: Aggregate results
cat "$RESULT_DIR"/result_*.txt > combined.txt
your-agent-cli "Synthesize these results for: $QUERY" < combined.txt

rm -rf "$RESULT_DIR"
```

### Python Template

```python
#!/usr/bin/env python3
"""RLM orchestration with parallel sub-agents."""

import subprocess
import concurrent.futures
from pathlib import Path

def process_chunk(chunk: str, query: str) -> str:
    """Process a single chunk with timeout."""
    result = subprocess.run(
        ["your-agent-cli", chunk, query],
        capture_output=True, text=True, timeout=300
    )
    return result.stdout

def orchestrate(chunks: list[str], query: str) -> str:
    # MAP: Parallel execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_chunk, c, query): c for c in chunks}
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # REDUCE: Aggregate
    combined = "\n---\n".join(results)
    return process_chunk(combined, f"Synthesize for: {query}")

if __name__ == "__main__":
    chunks = ["file1.txt", "file2.txt", "file3.txt"]
    print(orchestrate(chunks, "Your query here"))
```

**Key practices:**
- Use timeouts to prevent hangs
- Run independent sub-tasks in parallel (use `&` and `wait` in bash)
- Capture both stdout and stderr (`2>&1`)
- Store intermediate results for debugging

---

## Agent-Specific Implementation

Use these guides for spawning sub-agents with CLI tools:

| Tool | Guide | Best For |
|------|-------|----------|
| **Claude Code** | [CLAUDE-CODE.md](https://jonnyzzz.com/CLAUDE-CODE.md) | Web search, browser automation, general coding |
| **Codex** | [CODEX.md](https://jonnyzzz.com/CODEX.md) | IntelliJ IDE operations, image/PDF analysis, full MCP access |
| **Gemini** | [GEMINI.md](https://jonnyzzz.com/GEMINI.md) | Cross-validation, alternative perspective, long context |

**Multi-Agent Orchestration:** See [MULTI-AGENT.md](https://jonnyzzz.com/MULTI-AGENT.md) for patterns: Parallel Research, Pipeline, Partition+Map+Reduce, Cross-Validation.

### Quick Spawn Examples

**Give sub-agents full access** - don't restrict capabilities. Sub-agents automatically inherit:
- All OS-wide MCP servers (Playwright, MCP Steroid, etc.)
- Project-specific configurations and skills
- Custom plugins and extensions

```bash
# Claude Code (full tool access)
echo "Analyze auth module" | claude -p --tools default --permission-mode dontAsk 2>&1 &

# Codex (full access)
codex -C /path/to/project --full-auto exec "Analyze PSI structure in X.kt" 2>&1 &

# Gemini (alternative perspective)
gemini --approval-mode auto_edit "Review analysis for accuracy" 2>&1 &

# Wait for all
wait
```

**MCP Server Setup (Optional):** For browser automation or IntelliJ IDE operations, register MCP servers once:
```bash
# Optional: Enable browser automation
claude mcp add playwright npx @playwright/mcp@latest

# Optional: Enable IntelliJ IDE operations (URL from ~/.*.mcp-steroid)
codex mcp add intellij --url <URL>
```

Once registered, MCP servers are automatically available to all sub-agents.

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                    RLM QUICK REFERENCE                      │
├─────────────────────────────────────────────────────────────┤
│ TRIGGERS:                                                   │
│   • Context > 50K tokens                                    │
│   • Files > 5                                               │
│   • Multi-hop reasoning                                     │
│   • Cross-document aggregation                              │
├─────────────────────────────────────────────────────────────┤
│ PROTOCOL:                                                   │
│   1. ASSESS   → Peek, don't read everything                 │
│   2. DECIDE   → Match context + task to strategy            │
│   3. DECOMPOSE → Partition at natural boundaries            │
│   4. EXECUTE  → Parallel if independent (use scripts!)      │
│   5. SYNTHESIZE → Merge, dedupe, resolve conflicts          │
│   6. VERIFY   → Check completeness and accuracy             │
├─────────────────────────────────────────────────────────────┤
│ KEY QUESTIONS:                                              │
│   • Can I grep to narrow scope first?                       │
│   • Are sub-tasks independent (parallel) or dependent?      │
│   • Does each sub-agent have enough context?                │
│   • Should I write a script to orchestrate this?            │
├─────────────────────────────────────────────────────────────┤
│ ORCHESTRATION:                                              │
│   • Write bash or Python scripts for reproducibility        │
│   • Use timeouts to prevent hangs                           │
│   • Run independent tasks in parallel (& and wait)          │
│   • Capture stderr: 2>&1                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Reference

For comprehensive documentation including:
- Formal architecture and system design
- Benchmark results (OOLONG: +28%, OOLONG-Pairs: 0.04% → 58%)
- Detailed prompt templates for sub-agents
- Error handling and recovery protocols
- Complete bash/Python script implementations
- Strategy decision flowcharts
- Paper analysis and key findings

See **[RLM-extra.md](https://jonnyzzz.com/RLM-extra.md)**.

---

## Sources

- [Paper (arXiv)](https://arxiv.org/abs/2512.24601) - Zhang, Kraska, Khattab (MIT CSAIL)
- [Blog Post](https://alexzhang13.github.io/blog/2025/rlm/)
- [GitHub Repository](https://github.com/alexzhang13/rlm)

---

*Follow [@jonnyzzz](https://twitter.com/jonnyzzz) on X and [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) for more on AI agents and developer tooling.*
