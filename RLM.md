# RLM.md - Recursive Language Models Implementation Guide

## Paper Reference

- **Title:** Recursive Language Models
- **Authors:** Alex L. Zhang, Tim Kraska, Omar Khattab (MIT CSAIL)
- **Paper:** https://arxiv.org/abs/2512.24601
- **Blog:** https://alexzhang13.github.io/blog/2025/rlm/
- **Code:** https://github.com/alexzhang13/rlm
- **Minimal Implementation:** https://github.com/alexzhang13/rlm-minimal

---

## Executive Summary

Recursive Language Models (RLM) solve **context rot** - performance degradation as context length increases - by treating the prompt as a **Python variable** rather than neural network input. The model interacts with context programmatically through a REPL environment, spawning recursive sub-calls to process unbounded inputs.

**Key Results (from Paper Table 1, p.4):**
- Handles inputs **2 orders of magnitude** beyond context windows (10M+ tokens)
- RLM(GPT-5) outperforms GPT-5 by **+12.5 points** on OOLONG (44.00 → 56.50)
- OOLONG-Pairs: **58.00% vs 0.04%** (GPT-5 RLM vs base) - most dramatic gain
- BrowseComp+ (1K docs): **91.33%** on 150-task eval (base scores 0%)
- **~3x cheaper** than summarization approaches on BrowseComp+

**Paper Architecture Note:**
- GPT-5 is root LM, GPT-5-mini used only for recursive sub-LM calls
- Max recursion depth = 1 in experiments (sub-calls are LMs, not RLMs)
- Synchronous blocking calls; async/sandboxed REPLs noted as future work (p.8)

---

## Part 0: Instructions for AI Agents

This section provides explicit instructions for AI agents on how to apply RLM principles during task execution.

---

### 0.1 When to Activate RLM Mode

Evaluate the following triggers at the start of any task. If **any trigger fires**, engage RLM patterns.

#### Trigger Matrix

| Trigger Category | Specific Condition | Action |
|-----------------|-------------------|--------|
| **Context Size** | Total context > 50K tokens | Activate RLM |
| **Context Size** | Single file > 500 lines | Consider chunking |
| **Context Size** | > 10 files to process | Activate RLM |
| **Task Complexity** | Multi-hop reasoning required | Activate RLM |
| **Task Complexity** | Aggregation across sources | Activate RLM |
| **Task Complexity** | Classification + counting | Activate RLM |
| **Multi-Entity** | > 5 documents/files to analyze | Activate RLM |
| **Multi-Entity** | Cross-reference between sources | Activate RLM |
| **Output Size** | Expected output > 10K tokens | Consider Long I/O |

#### Task Complexity Scaling (Paper p.3)

Effective context window depends not just on token count but on **task complexity**:

| Task Type | Processing Cost | Example | RLM Benefit |
|-----------|-----------------|---------|-------------|
| S-NIAH (needle search) | O(1) constant | Find one phrase | Low - base LMs handle well |
| OOLONG (aggregation) | O(n) linear | Classify all entries | High - +12 points gain |
| OOLONG-Pairs | O(n²) quadratic | Pair-wise reasoning | Critical - 0.04% → 58% |

**Key Insight:** More complex tasks exhibit context rot at shorter lengths. RLM benefits scale with task complexity.

#### When NOT to Use RLM (Paper p.6)

**Base LM outperforms RLM in these cases:**
- Short context (<16K tokens for simple tasks)
- Simple needle-in-haystack queries
- When direct LM call fits comfortably in context
- Tasks with O(1) information density

**Cost-benefit threshold:** For context lengths <2^14 tokens (~16K), base LM is often preferable. RLM overhead doesn't pay off for simple retrieval.

#### Quick Decision Tree

```
START
  |
  +-- Context > 50K tokens? ---------------------- YES --> ACTIVATE RLM
  |     |
  |     NO
  |     |
  +-- Context > 16K AND complexity > O(1)? ------- YES --> CONSIDER RLM
  |     |
  |     NO
  |     |
  +-- Files to process > 5? ---------------------- YES --> ACTIVATE RLM
  |     |
  |     NO
  |     |
  +-- Multi-hop/aggregation reasoning needed? ---- YES --> ACTIVATE RLM
  |     |
  |     NO
  |     |
  +-- PROCEED WITH DIRECT PROCESSING
```

---

### 0.2 Step-by-Step Protocol

Execute these steps **in order** when RLM mode is activated.

#### Step 1: ASSESS (Peek at Context Structure)

**Objective:** Understand context shape before committing to strategy.

**Actions:**
1. Determine total context size (token count, file count, line count)
2. Sample context structure:
   - First 100-200 lines of each file
   - File/directory listing
   - Metadata if available
3. Identify context type (unstructured text, structured data, code, multi-document)

**Output:** Mental model of context structure and size.

```
ASSESS CHECKLIST:
[ ] Total size determined
[ ] Structure type identified (text/JSON/code/mixed)
[ ] Natural boundaries identified (files/sections/records)
[ ] Relevant vs. noise ratio estimated
```

#### Step 2: DECIDE (Select Strategy)

**Objective:** Choose the optimal processing strategy based on assessment.

**Strategy Selection Table:**

| Context Type | Size | Task | Strategy |
|--------------|------|------|----------|
| Text (unstructured) | < 4K | Any | Direct |
| Text (unstructured) | 4K-50K | Search | Grep |
| Text (unstructured) | > 50K | Any | Partition + Map |
| Structured (JSON/XML) | Any | Search | Grep |
| Structured (JSON/XML) | Large | Transform | Partition + Map |
| Multi-document | 3-10 docs | Analysis | Sequential |
| Multi-document | > 10 docs | Analysis | Parallel sub-agents |
| Code | Single file < 500L | Any | Direct |
| Code | Multiple files | Any | Partition by file/concern |
| Mixed/Unknown | Any | Any | Peek --> Grep --> Partition |

**Decision Output:** Selected strategy with rationale.

#### Step 3: DECOMPOSE (Partition if Needed)

**Objective:** Divide work into parallelizable or sequential sub-tasks.

**Partitioning Strategies:**

| Boundary Type | When to Use | Example |
|--------------|-------------|---------|
| By file | Multi-file analysis | One sub-agent per file |
| By section | Single large document | Split at headers/chapters |
| By record | Structured data | Batch of N records per chunk |
| By size | Unknown structure | Fixed token windows |
| By concern | Complex task | Auth vs. UI vs. DB |

**Chunking Guidelines:**
- Target chunk size: 4K-10K tokens per sub-task
- Preserve semantic boundaries (don't split mid-sentence/function)
- Include overlap if context continuity matters (10-20% overlap)
- Include necessary shared context in each chunk (imports, type definitions)

**Output:** List of sub-tasks with their assigned context partitions.

#### Step 4: EXECUTE (Run Sub-Agents)

**Objective:** Process partitions via sub-agents.

**Execution Modes:**

| Mode | When to Use | Implementation |
|------|-------------|----------------|
| **Parallel** | Independent sub-tasks | Spawn all sub-agents simultaneously |
| **Sequential** | Dependent sub-tasks | Chain results between agents |
| **Hybrid** | Partial dependencies | Parallel groups with sequential phases |

**Sub-Agent Prompt Template:**
```
CONTEXT: [Partition description and content]
TASK: [Specific sub-task extracted from main task]
CONSTRAINTS: [Relevant constraints from main task]
OUTPUT FORMAT: [Expected format for aggregation]
```

**Parallel Execution Pattern:**
```
FOR EACH partition IN partitions:
  SPAWN sub-agent(partition, sub-task)
WAIT FOR all sub-agents
COLLECT results[]
```

#### Step 5: SYNTHESIZE (Combine Results)

**Objective:** Aggregate sub-agent outputs into coherent final result.

**Synthesis Patterns:**

| Pattern | Description | Use When |
|---------|-------------|----------|
| **Concatenate** | Join results sequentially | Order matters, no conflicts |
| **Merge** | Combine overlapping results | Deduplication needed |
| **Reduce** | Apply aggregation function | Counting, statistics |
| **Vote** | Take majority/consensus | Classification tasks |
| **Hierarchical** | Summarize summaries | Multi-level compression |

**Synthesis Checklist:**
```
[ ] All sub-agent results received
[ ] Conflicts/contradictions resolved
[ ] Duplicates removed
[ ] Format unified
[ ] Coverage verified (no gaps)
```

#### Step 6: VERIFY (Check Completeness)

**Objective:** Ensure the final result satisfies the original query.

**Verification Questions:**
1. Does the result directly answer the original query?
2. Have all parts of the context been covered?
3. Are there gaps or missing information?
4. Does the confidence level match the evidence?

**Verification Actions:**
- Spot-check: Verify 2-3 specific claims against source
- Coverage check: Ensure all partitions contributed
- Format check: Output matches requested format

---

### 0.3 Self-Check Questions

Ask yourself these questions at each decision point.

#### Before Processing

| Question | If YES | If NO |
|----------|--------|-------|
| Is this context too large for direct processing (> 50K tokens)? | Use RLM | May proceed directly |
| Can I identify keywords/patterns to narrow scope? | Use Grep first | Consider full scan |
| Are there natural partition boundaries? | Plan decomposition | Use size-based chunking |
| Do I understand the context structure? | Proceed to strategy | Peek first |

#### During Decomposition

| Question | If YES | If NO |
|----------|--------|-------|
| Are these sub-tasks independent? | Parallelize | Sequence them |
| Does each sub-task have sufficient context? | Proceed | Add shared context |
| Can a sub-task be further decomposed? | Recurse if beneficial | Keep atomic |
| Is the chunk size reasonable (4K-10K)? | Proceed | Re-partition |

#### During Synthesis

| Question | If YES | If NO |
|----------|--------|-------|
| Did all sub-agents return results? | Proceed | Investigate failures |
| Are results consistent/compatible? | Merge | Resolve conflicts |
| Is there redundant information? | Deduplicate | Proceed |
| Does synthesis answer the original query? | Finalize | Iterate |

#### Final Check

```
COMPLETENESS CHECK:
[ ] Original query fully addressed
[ ] All relevant context examined
[ ] No obvious gaps in coverage
[ ] Confidence level appropriate
[ ] Output format matches request
```

---

### 0.4 Anti-Patterns to Avoid

#### Anti-Pattern 1: Reading Everything First

**Wrong:**
```
1. Read all 50 files completely
2. Load entire context into memory
3. Then start thinking about the task
```

**Right:**
```
1. Peek at structure (first 100 lines, file list)
2. Grep for relevant patterns
3. Read only matching/relevant sections
4. Expand if initial results insufficient
```

**Why it matters:** Reading everything causes context overflow and dilutes attention.

---

#### Anti-Pattern 2: Sub-Agent Explosion

**Wrong:**
```
- Spawn 100 sub-agents for 100 files
- Each sub-agent spawns 10 more
- Uncontrolled recursion depth
```

**Right:**
```
- Group files logically (by directory, type, concern)
- Target 3-10 sub-agents maximum per level
- Limit recursion depth to 1-2 levels
- Batch small files together
```

**Thresholds:**

| Metric | Maximum | Action if Exceeded |
|--------|---------|-------------------|
| Sub-agents per parent | 10 | Batch/group items |
| Recursion depth | 2 | Flatten or summarize |
| Total sub-agents | 30 | Re-architect decomposition |

---

#### Anti-Pattern 3: Context Starvation

**Wrong:**
```
Sub-agent prompt: "Analyze this code"
[Provides only a function body without imports, types, or usage context]
```

**Right:**
```
Sub-agent prompt: "Analyze this code"
[Provides:]
- The function body
- Relevant imports/dependencies
- Type definitions used
- Example usage (if available)
- Relationship to other components
```

**Context Inclusion Checklist:**
```
[ ] Sub-task has clear, specific objective
[ ] Necessary shared context included (types, imports)
[ ] Output format specified
[ ] Success criteria defined
[ ] Relevant constraints from parent task passed down
```

---

#### Anti-Pattern 4: Blind Partitioning

**Wrong:**
```
Split 100K tokens into 10 x 10K chunks at arbitrary byte boundaries
```

**Right:**
```
1. Identify natural boundaries (files, sections, records)
2. Split at semantic boundaries
3. Ensure each chunk is self-contained or has overlap
4. Verify no critical information spans chunk boundaries
```

---

#### Anti-Pattern 5: Ignoring Grep

**Wrong:**
```
Task: "Find all error handling in codebase"
Action: Read every file completely, then search
```

**Right:**
```
Task: "Find all error handling in codebase"
Action:
1. Grep for: try, catch, except, error, Error, throw, raise
2. Get file list with matches
3. Read only matched sections with context
```

**When to Grep First:**
- Keyword/pattern search tasks
- Looking for specific identifiers
- Finding usages of functions/classes
- Locating configuration values

---

### 0.5 Quick Reference Card

```
+-------------------------------------------------------------+
|                    RLM QUICK REFERENCE                      |
+-------------------------------------------------------------+
| TRIGGERS:                                                   |
|   - Context > 50K tokens                                    |
|   - Files > 5                                               |
|   - Multi-hop reasoning                                     |
|   - Cross-document aggregation                              |
+-------------------------------------------------------------+
| PROTOCOL:                                                   |
|   1. ASSESS  --> Peek, don't read everything                |
|   2. DECIDE  --> Match context type + task to strategy      |
|   3. DECOMPOSE --> Partition at natural boundaries          |
|   4. EXECUTE --> Parallel if independent, sequence if not   |
|   5. SYNTHESIZE --> Merge, dedupe, resolve conflicts        |
|   6. VERIFY  --> Check completeness and accuracy            |
+-------------------------------------------------------------+
| KEY QUESTIONS:                                              |
|   - Can I grep to narrow scope?                             |
|   - Are sub-tasks independent (parallel) or dependent?      |
|   - Does each sub-agent have enough context?                |
+-------------------------------------------------------------+
| AVOID:                                                      |
|   X Reading everything before thinking                      |
|   X Spawning > 10 sub-agents per level                      |
|   X Providing insufficient context to sub-agents            |
|   X Splitting at arbitrary byte boundaries                  |
+-------------------------------------------------------------+
```

---

## Part 1: Core Concepts

### Context Rot

**Definition:** Performance degradation as context length increases, manifesting as reduced accuracy on information-dense tasks even when all information remains accessible.

**Why It Occurs:**
| Cause | Description |
|-------|-------------|
| Distribution Shift | Long sequences fall outside training distributions |
| Higher Entropy | Extended contexts reduce attention effectiveness |
| Attention Dilution | Weights spread across more tokens |
| Complexity Scaling | Linear/quadratic tasks degrade faster than constant-time lookups |

**Traditional Solutions and Their Failures:**

| Approach | Why It Fails |
|----------|--------------|
| Summarization | Lossy - information-dense tasks need fine-grained details |
| Truncation | Arbitrary loss - cannot know what matters a priori |
| Fixed Chunking | Static partitioning ignores task-specific needs |
| RAG/Retrieval | Fails multi-hop reasoning where relevance isn't obvious |
| Simple Splitting | Cross-chunk reasoning still fails |

### Query-Context Separation

**Definitions:**
- **Query (q):** The specific question or task
- **Context (C):** Associated information (documents, code, data) - potentially unbounded
- **Separation:** Root model receives only query; context stored in accessible environment

**Benefits:**
- Prevents context window saturation
- Enables programmatic exploration (grep, peek, partition)
- Supports diverse modalities (text, images, structured data)
- Allows adaptive decomposition strategies

### Prompt-as-Variable Paradigm

Instead of feeding context to attention, store it as a Python variable:

```python
# Traditional: Context enters neural network
response = llm(prompt="Here is 100K tokens... Now answer: What is X?")

# RLM: Context stays external, accessed programmatically
context = load_context()  # Never enters LLM directly
response = root_llm(
    prompt="You have variable 'context'. Write code to answer: What is X?",
    environment={"context": context, "llm_query": recursive_call}
)
```

**Capabilities This Unlocks:**
- Slicing: `context[:2000]` - peek without processing everything
- Regex: `re.findall(pattern, context)` - grep without materializing
- Partitioning: Split context based on observed structure
- Recursive delegation: `llm_query(chunk, sub_question)`

---

## Part 2: Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Root LM (Depth=0)                        │
│  - Receives query only (not full context)                   │
│  - Context exists as variable in REPL environment           │
│  - Generates Python code to interact with context           │
│  - Controls decomposition strategy                          │
│  - Outputs via FINAL() or FINAL_VAR()                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    REPL Environment                         │
│  - Stores context as Python variable in memory              │
│  - Executes code blocks from LM                             │
│  - Returns truncated output to prevent context overflow     │
│  - Provides llm_query() for recursive calls                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 Recursive LM (Depth=1+)                     │
│  - Spawned for intermediate computation                     │
│  - Isolated instance with own environment                   │
│  - Receives context subset, returns result to parent        │
│  - Currently limited to depth=1 in reference implementation │
└─────────────────────────────────────────────────────────────┘
```

### Formal Model

```
RLM_M(q, C) over environment E

Where:
- M = base language model
- q = query string
- C = [c1, c2, ..., cm] = context sequence
- E = (namespace, context_var, exec_engine, truncation_limit)
```

### Component Details

#### Root LM (Depth=0)
- **Input:** Query text only; context stored separately
- **Responsibilities:** Context decomposition, code generation, result aggregation
- **Output:** `FINAL(answer)` for direct answer, `FINAL_VAR(var_name)` for computed variable

#### REPL Environment
- **Context Storage:** Python variable in memory (like Jupyter notebook)
- **Execution:** Python `exec()` (local) or container runtime (Docker/Modal)
- **Output Truncation:** Returns limited output to prevent context overflow
- **Sandbox Options:**

| Environment | Security | Use Case |
|-------------|----------|----------|
| LocalREPL | Minimal (namespace isolation) | Development |
| DockerREPL | Container isolation | Production (self-hosted) |
| Modal | Full cloud isolation | Production (managed) |

#### Recursive Calls (Depth=1+)
- Spawned when Root LM writes code invoking `llm_query()`
- Each call receives: new query + transformed context subset
- Isolated environment per call
- Results returned to parent's REPL

---

## Part 3: Implementation Patterns

### Basic Setup

```python
import os
from rlm import RLM
from rlm.logger import RLMLogger

rlm = RLM(
    backend="openai",
    backend_kwargs={
        "model_name": "gpt-4",
        "api_key": os.getenv("OPENAI_API_KEY"),
    },
    environment="local",     # or "docker", "modal"
    max_depth=1,             # recursion depth limit
    max_iterations=30,       # iteration limit per call
    verbose=True,
    logger=RLMLogger(log_dir="./logs"),
)

# Replace standard LLM call
result = rlm.completion("Your query here", context=your_large_context)
print(result.response)
```

### Output Protocol

**FINAL(answer):** Direct answer output
```python
# Model generates:
"""
Based on my analysis, the key insight is...

FINAL(The document contains 3 main themes: sustainability, innovation, collaboration.)
"""
```

**FINAL_VAR(variable_name):** Return computed variable
```python
# Model generates:
"""
```repl
results = []
for doc in context['documents']:
    analysis = llm_query(f"Summarize: {doc}")
    results.append(analysis)
final_report = "\n\n".join(results)
```

FINAL_VAR(final_report)
"""
```

### Context Management

```python
# String context
result = rlm.completion("Summarize key points", context="Long document text...")

# Structured context (JSON)
context = {"documents": [...], "metadata": {...}}
result = rlm.completion("Find documents matching criteria", context=context)

# Inside REPL, model can:
chunk = context[:1000]                    # Peek at subset
chunks = [context[i:i+10000] for ...]     # Partition
matches = re.findall(r'pattern', context) # Grep
result = llm_query(prompt)                # Recursive call (~500K chars)
```

### Environment Configuration

```python
# Docker (production)
rlm = RLM(
    environment="docker",
    environment_kwargs={
        "image": "python:3.11-slim",
        "workspace": "/workspace",
    },
    ...
)

# Modal (cloud)
# First: uv add modal && modal setup
rlm = RLM(
    environment="modal",
    environment_kwargs={},
    ...
)
```

---

## Part 4: Emergent Strategies

RLM models develop these strategies without explicit training:

### Peeking

**Purpose:** Initial context exploration before committing to strategy

```python
# Model-generated code:
print(f"Context length: {len(context)} chars")
print(context[:2000])  # Preview structure

# Based on preview, decide: grep, partition, or direct process
```

**When Used:** Start of RLM interactions, unknown context structure

### Grepping

**Purpose:** Rapid search space narrowing via pattern matching

```python
import re

# Direct keyword search
matches = re.findall(r'.*festival.*', context, re.IGNORECASE)

# Structured data extraction
questions = re.findall(r'^(Q\d+):\s*(.+)$', context, re.MULTILINE)

# Line filtering
lines = context.split('\n')
filtered = [line for line in lines if 'keyword' in line.lower()]
```

**When Used:** Keyword-searchable tasks, filtering before semantic processing

### Partition + Map

**Purpose:** Divide context into chunks, process in parallel, aggregate

```python
# Partition
chunks = [context[i:i+10000] for i in range(0, len(context), 10000)]

# Map (recursive calls)
results = []
for chunk in chunks:
    result = llm_query(f"Classify items in this chunk:\n{chunk}")
    results.append(result)

# Reduce
final_answer = llm_query(f"Aggregate these results: {results}")
```

**When Used:** Per-item analysis, multi-hop reasoning, semantic classification

### Summarization

**Purpose:** Compress context while preserving decision-relevant information

```python
chunks = partition_context(context, chunk_size=4000)
summaries = []

for chunk in chunks:
    summary = llm_query(f"""
        Summarize preserving info relevant to: {query}
        Keep: key facts, dates, names, quantities
        Remove: redundant details, filler
        Chunk: {chunk}
    """)
    summaries.append(summary)

combined = '\n---\n'.join(summaries)
# May recurse if still too long
```

**When Used:** Context exceeds capacity, abstraction preserves key details

### Long I/O Processing

**Purpose:** Construct long outputs programmatically rather than generating token-by-token

```python
# Instead of generating 75k+ tokens directly:
def apply_git_diffs(base_file, diff_history):
    import subprocess
    with open('/tmp/base.txt', 'w') as f:
        f.write(base_file)

    for i, diff in enumerate(diff_history):
        with open(f'/tmp/diff_{i}.patch', 'w') as f:
            f.write(diff)
        subprocess.run(['patch', '/tmp/base.txt', f'/tmp/diff_{i}.patch'])

    with open('/tmp/base.txt', 'r') as f:
        return f.read()

result = apply_git_diffs(original, diffs)
```

**When Used:** Git diffs, file transformations, structured data processing

### Strategy Decision Flowchart

The following decision framework guides strategy selection based on context characteristics and task requirements.

#### Decision Tree

```
                                    START
                                      │
                                      ▼
                            ┌─────────────────┐
                            │  Context Size?  │
                            └────────┬────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
            <4K                   4K-100K                 >100K
              │                      │                      │
              ▼                      ▼                      ▼
      ┌───────────────┐    ┌─────────────────┐    ┌─────────────────┐
      │ Direct Process│    │   Peek First    │    │   Always Peek   │
      └───────┬───────┘    └────────┬────────┘    └────────┬────────┘
              │                     │                      │
              ▼                     ▼                      ▼
         [COMPLETE]       ┌─────────────────┐    ┌─────────────────┐
                          │ Keyword Search? │    │   Complexity?   │
                          └────────┬────────┘    └────────┬────────┘
                                   │                      │
                    ┌──────────────┴──────────────┐       │
                    │                             │       │
                   YES                           NO       │
                    │                             │       │
                    ▼                             ▼       │
              ┌──────────┐               ┌──────────┐     │
              │   Grep   │               │ Partition│     │
              └────┬─────┘               │ + Map    │     │
                   │                     └────┬─────┘     │
                   ▼                          │           │
           ┌─────────────┐                    │     ┌─────┴──────────────────┐
           │Matches Found?│                   │     │                        │
           └──────┬──────┘                    │  Linear              Quadratic
                  │                           │     │                        │
        ┌─────────┴─────────┐                 │     ▼                        ▼
        │                   │                 │ ┌──────────────┐    ┌──────────────┐
       YES                 NO                 │ │Partition+Map │    │Partition+Map │
        │                   │                 │ │(sequential)  │    │(with verify) │
        ▼                   ▼                 │ └──────┬───────┘    └──────┬───────┘
  ┌───────────┐    ┌──────────────┐          │        │                   │
  │Process    │    │Peek Different│          │        ▼                   ▼
  │Matches    │    │Sample/Expand │          │ ┌────────────┐    ┌────────────────┐
  └─────┬─────┘    │Search        │          │ │ Aggregate  │    │Cross-Validate  │
        │          └──────┬───────┘          │ └─────┬──────┘    │Results         │
        │                 │                  │       │           └───────┬────────┘
        ▼                 ▼                  ▼       ▼                   │
  ┌───────────────────────────────────────────────────────────┐         │
  │                     Result Size?                          │◄────────┘
  └─────────────────────────┬─────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
          Fits Window              Exceeds Window
              │                           │
              ▼                           ▼
         [COMPLETE]              ┌─────────────────┐
                                 │   Summarize     │
                                 │   + Recurse     │
                                 └────────┬────────┘
                                          │
                                          ▼
                                     [COMPLETE]
```

#### Decision Table with Weighted Criteria

Each strategy scores points based on applicable factors. Select strategies with highest combined scores.

| Factor | Weight | Peek | Grep | Partition | Summarize | Long I/O |
|--------|--------|:----:|:----:|:---------:|:---------:|:--------:|
| **Context Factors** |
| Context >100K tokens | High | +3 | +2 | +3 | +2 | +1 |
| Context >1M tokens | Critical | +3 | +3 | +3 | +3 | +2 |
| Unknown structure | High | +3 | | +1 | | |
| Structured/JSON data | Medium | +1 | +2 | +2 | | +1 |
| Code/Diff content | High | +1 | +1 | | | +3 |
| **Task Factors** |
| Keyword searchable | Medium | | +3 | | | |
| Per-item processing | High | | | +3 | +1 | |
| Aggregation needed | Medium | | | +2 | +2 | |
| Exact reproduction | High | | | | | +3 |
| Multi-hop reasoning | High | +1 | +1 | +3 | | |
| **Complexity Factors** |
| Linear complexity (O(n)) | Medium | | +1 | +2 | +1 | |
| Quadratic complexity (O(n^2)) | Critical | | +1 | +3 | +2 | |
| Cross-reference needed | High | +1 | +2 | +2 | | |
| **Output Factors** |
| Output exceeds window | High | | | | +3 | +3 |
| Intermediate results large | Medium | | | +1 | +2 | |

**Scoring Guide:**
- Critical (+3): Must apply strategy if factor present
- High (+2-3): Strong indicator for strategy
- Medium (+1-2): Supporting indicator

#### Strategy Combination Patterns

Strategies rarely work in isolation. These patterns represent common effective combinations:

**Pattern A: Lookup Pipeline** (for search/retrieval tasks)
```
Peek → Grep → Direct Process
└─ Use when: specific information retrieval, keyword-searchable
└─ Example: "Find all mentions of 'festival' in documents"
└─ Cost: Low (minimal LLM calls)
```

**Pattern B: MapReduce Pipeline** (for aggregation tasks)
```
Peek → Partition → Map (parallel) → Reduce
└─ Use when: per-item analysis, counting, classification
└─ Example: "Count items by category across 1000 entries"
└─ Cost: Medium (N/chunk_size LLM calls + 1 reduce)
```

**Pattern C: Hierarchical Compression** (for synthesis tasks)
```
Partition → Summarize (per chunk) → Merge → Summarize (recursive)
└─ Use when: synthesis, theme extraction, large output compression
└─ Example: "Summarize key themes across 500 documents"
└─ Cost: High (multiple summary passes)
```

**Pattern D: Verified Aggregation** (for high-stakes quadratic tasks)
```
Peek → Partition → Map → Cross-Validate → Aggregate
└─ Use when: quadratic complexity, accuracy critical
└─ Example: "Find all contradictions between document pairs"
└─ Cost: Very High (includes verification pass)
```

**Pattern E: Programmatic Transform** (for long I/O)
```
Peek → Plan → Generate Code → Execute → Verify
└─ Use when: output exceeds generation limits, deterministic transform
└─ Example: "Apply 50 git diffs to reconstruct file"
└─ Cost: Low (mostly execution, minimal generation)
```

**Pattern F: Hybrid Search** (for semi-structured data)
```
Peek → Grep (filter) → Partition (filtered) → Map → Aggregate
└─ Use when: large context but only subset relevant
└─ Example: "Analyze all ERROR entries in 10M log file"
└─ Cost: Medium (grep reduces partition size)
```

#### Failure Recovery Paths

When a strategy fails, apply these recovery procedures:

| Failure Mode | Detection | Recovery Action |
|--------------|-----------|-----------------|
| **Grep returns nothing** | Empty match list | 1. Try case-insensitive search<br>2. Broaden pattern (stem/wildcard)<br>3. Peek different sample region<br>4. Fall back to Partition+Map |
| **Grep returns too much** | Matches > 50% of context | 1. Narrow pattern<br>2. Add second filter<br>3. Sample matches then Partition |
| **Partition results conflict** | Contradictory sub-agent answers | 1. Spawn verification agent with full context<br>2. Request confidence scores<br>3. Re-partition with overlap<br>4. Escalate ambiguity to user |
| **Sub-agent fails/times out** | Error or no response | 1. Retry with smaller chunk<br>2. Retry with more context<br>3. Simplify sub-query<br>4. Mark chunk as "requires manual review" |
| **Aggregation exceeds window** | Combined results too large | 1. Apply summarization to results<br>2. Hierarchical reduce (reduce pairs)<br>3. Return structured data + sample |
| **Summary loses critical info** | Verification fails | 1. Increase summary length<br>2. Extract key facts separately<br>3. Keep original for specific lookups |
| **Long I/O code fails** | Execution error | 1. Fix code based on error<br>2. Break into smaller operations<br>3. Add validation checkpoints<br>4. Fall back to generation if small enough |

**Recovery Decision Tree:**

```
           ┌─────────────────────────┐
           │    Strategy Failed?     │
           └───────────┬─────────────┘
                       │
         ┌─────────────┴─────────────────────┐
         │                                   │
    Retrieval Failure                 Processing Failure
         │                                   │
         ▼                                   ▼
┌─────────────────┐               ┌─────────────────────┐
│ Expand Search   │               │ Conflicting Results?│
│ Parameters      │               └──────────┬──────────┘
└────────┬────────┘                          │
         │                         ┌─────────┴─────────┐
         ▼                        YES                  NO
┌─────────────────┐                │                   │
│ Still Nothing?  │                ▼                   ▼
└────────┬────────┘       ┌──────────────┐   ┌──────────────┐
         │                │ Verification │   │ Retry with   │
    ┌────┴────┐           │ Agent        │   │ More Context │
   YES       NO           └──────┬───────┘   └──────┬───────┘
    │         │                  │                  │
    ▼         ▼                  ▼                  ▼
┌────────┐ ┌────────┐     ┌────────────┐    ┌────────────┐
│Fallback│ │Continue│     │ Escalate   │    │ Still Fails│
│to Full │ │Pipeline│     │ if Unresol │    │ → Escalate │
│Scan    │ │        │     └────────────┘    └────────────┘
└────────┘ └────────┘
```

**Retry Budget Guidelines:**
- Max 2 retries per strategy before escalating
- Total recovery attempts should not exceed 3x original cost estimate
- Log all failures for strategy improvement feedback

---

### Prompt Templates for Sub-Agents

These templates are designed for spawning recursive sub-calls. Copy and adapt them for your specific use cases.

---

#### 1. Peek Agent Template

**Purpose:** Initial context exploration to determine structure and optimal processing strategy.

**When to Use:**
- At the start of any RLM interaction with unknown context
- Before committing to a specific decomposition strategy
- When context format is not pre-specified

**Template:**
```
You are analyzing a subset of a larger context.

CONTEXT SAMPLE (first {N} chars):
{context_sample}

TOTAL CONTEXT SIZE: {total_size} chars

YOUR TASK: Identify the structure and format of this context.
Report:
- Data format (JSON/CSV/plaintext/markdown/code)
- Organizational structure (sections, records, lines)
- Key patterns that could be used for grepping
- Recommended processing strategy

OUTPUT FORMAT: JSON with keys: format, structure, patterns, recommended_strategy
```

**Expected Output:**
```json
{
  "format": "JSON",
  "structure": "Array of objects with 'id', 'title', 'content' fields",
  "patterns": ["\"id\":", "\"title\":", "\\d{4}-\\d{2}-\\d{2}"],
  "recommended_strategy": "partition_by_record"
}
```

**Example Instantiation:**
```python
peek_prompt = f"""
You are analyzing a subset of a larger context.

CONTEXT SAMPLE (first 2000 chars):
{context[:2000]}

TOTAL CONTEXT SIZE: {len(context)} chars

YOUR TASK: Identify the structure and format of this context.
Report:
- Data format (JSON/CSV/plaintext/markdown/code)
- Organizational structure (sections, records, lines)
- Key patterns that could be used for grepping
- Recommended processing strategy

OUTPUT FORMAT: JSON with keys: format, structure, patterns, recommended_strategy
"""
structure_info = llm_query(peek_prompt)
```

---

#### 2. Grep Agent Template

**Purpose:** Filter context by pattern matching before semantic processing.

**When to Use:**
- Task involves keyword-searchable content
- Need to narrow search space before deeper analysis
- Looking for specific entities, dates, or structured patterns

**Template:**
```
You are a filtering agent. Your job is to extract relevant portions from context.

QUERY: {query}
SEARCH PATTERNS TO USE: {patterns}
CONTEXT CHUNK:
{context_chunk}

YOUR TASK:
1. Apply the search patterns to find relevant lines/sections
2. For each match, include surrounding context (2-3 lines before/after)
3. Remove clearly irrelevant matches (false positives)
4. Preserve source location markers for traceability

OUTPUT FORMAT:
Return a JSON array of matches:
[
  {
    "line_number": <int>,
    "matched_pattern": "<pattern>",
    "content": "<matched content with context>",
    "relevance_score": <0.0-1.0>
  }
]

If no relevant matches found, return: {"matches": [], "reason": "<explanation>"}
```

**Expected Output:**
```json
[
  {
    "line_number": 142,
    "matched_pattern": "festival",
    "content": "...The annual tech festival begins on March 15th...",
    "relevance_score": 0.95
  },
  {
    "line_number": 287,
    "matched_pattern": "festival",
    "content": "...registration for the festival closes February 28th...",
    "relevance_score": 0.85
  }
]
```

**Example Instantiation:**
```python
grep_prompt = f"""
You are a filtering agent. Your job is to extract relevant portions from context.

QUERY: Find all mentions of product launch dates
SEARCH PATTERNS TO USE: ["launch", "release", "announce", "\\d{{4}}-\\d{{2}}-\\d{{2}}"]
CONTEXT CHUNK:
{chunk}

YOUR TASK:
1. Apply the search patterns to find relevant lines/sections
2. For each match, include surrounding context (2-3 lines before/after)
3. Remove clearly irrelevant matches (false positives)
4. Preserve source location markers for traceability

OUTPUT FORMAT:
Return a JSON array of matches:
[
  {{
    "line_number": <int>,
    "matched_pattern": "<pattern>",
    "content": "<matched content with context>",
    "relevance_score": <0.0-1.0>
  }}
]

If no relevant matches found, return: {{"matches": [], "reason": "<explanation>"}}
"""
filtered_results = llm_query(grep_prompt)
```

---

#### 3. Chunk Analysis Agent Template

**Purpose:** Analyze a partition of the context for the partition+map strategy.

**When to Use:**
- Processing large context via divide-and-conquer
- Each chunk can be analyzed independently
- Task requires per-item classification, extraction, or transformation

**Template:**
```
You are a chunk analysis agent processing partition {chunk_index} of {total_chunks}.

PARENT QUERY: {original_query}
YOUR SPECIFIC TASK: {chunk_task}

CHUNK BOUNDARIES:
- Start position: {start_pos}
- End position: {end_pos}
- May contain partial records at boundaries (handle gracefully)

CONTEXT CHUNK:
{chunk_content}

INSTRUCTIONS:
1. Process only the content within this chunk
2. Handle boundary cases: if a record is cut off, note it but don't fabricate
3. Apply consistent criteria as other chunk agents will use
4. Include chunk metadata in your response for aggregation

OUTPUT FORMAT:
{
  "chunk_id": {chunk_index},
  "items_processed": <count>,
  "results": [<your analysis results>],
  "boundary_issues": ["<any truncated records>"],
  "confidence": <0.0-1.0>
}
```

**Expected Output:**
```json
{
  "chunk_id": 3,
  "items_processed": 47,
  "results": [
    {"item_id": "A123", "category": "electronics", "sentiment": "positive"},
    {"item_id": "A124", "category": "clothing", "sentiment": "neutral"}
  ],
  "boundary_issues": ["Record A170 truncated at chunk end"],
  "confidence": 0.92
}
```

**Example Instantiation:**
```python
chunk_size = 10000
chunks = [context[i:i+chunk_size] for i in range(0, len(context), chunk_size)]

results = []
for idx, chunk in enumerate(chunks):
    chunk_prompt = f"""
You are a chunk analysis agent processing partition {idx + 1} of {len(chunks)}.

PARENT QUERY: Classify each product review as positive, negative, or neutral
YOUR SPECIFIC TASK: Classify reviews in this chunk

CHUNK BOUNDARIES:
- Start position: {idx * chunk_size}
- End position: {min((idx + 1) * chunk_size, len(context))}
- May contain partial records at boundaries (handle gracefully)

CONTEXT CHUNK:
{chunk}

INSTRUCTIONS:
1. Process only the content within this chunk
2. Handle boundary cases: if a record is cut off, note it but don't fabricate
3. Apply consistent criteria as other chunk agents will use
4. Include chunk metadata in your response for aggregation

OUTPUT FORMAT:
{{
  "chunk_id": {idx + 1},
  "items_processed": <count>,
  "results": [<your analysis results>],
  "boundary_issues": ["<any truncated records>"],
  "confidence": <0.0-1.0>
}}
"""
    results.append(llm_query(chunk_prompt))
```

---

#### 4. Summarization Agent Template

**Purpose:** Compress context while preserving task-relevant information.

**When to Use:**
- Context exceeds processing capacity even after partitioning
- High-level understanding sufficient for the task
- Preparing context for a final synthesis step

**Template:**
```
You are a summarization agent. Compress the following content while preserving information relevant to the query.

ORIGINAL QUERY: {query}
COMPRESSION TARGET: Reduce to ~{target_length} chars (currently {current_length} chars)
COMPRESSION RATIO: {compression_ratio}x

CONTENT TO SUMMARIZE:
{content}

PRESERVATION PRIORITIES (in order):
1. Facts directly answering the query
2. Named entities (people, places, organizations, dates)
3. Quantitative data (numbers, statistics, measurements)
4. Causal relationships and key conclusions
5. Supporting evidence for main points

REMOVE:
- Redundant restatements
- Filler phrases and verbose language
- Examples when the pattern is clear
- Tangential information unrelated to query

OUTPUT FORMAT:
{
  "summary": "<compressed content>",
  "preserved_facts": [<list of key facts kept>],
  "removed_topics": [<list of topics dropped>],
  "compression_achieved": <actual ratio>,
  "information_loss_risk": "low|medium|high"
}
```

**Expected Output:**
```json
{
  "summary": "Q3 2024 revenue: $4.2B (+12% YoY). Key drivers: cloud services (45% of revenue), enterprise contracts. Challenges: supply chain delays reduced hardware margins by 3%. Outlook: Q4 guidance $4.5-4.7B.",
  "preserved_facts": ["Q3 revenue $4.2B", "12% YoY growth", "cloud 45% of revenue", "Q4 guidance range"],
  "removed_topics": ["executive biographies", "office locations", "historical company timeline"],
  "compression_achieved": 8.5,
  "information_loss_risk": "low"
}
```

**Example Instantiation:**
```python
summarize_prompt = f"""
You are a summarization agent. Compress the following content while preserving information relevant to the query.

ORIGINAL QUERY: What were the key financial results and outlook?
COMPRESSION TARGET: Reduce to ~500 chars (currently {len(chunk)} chars)
COMPRESSION RATIO: {len(chunk) // 500}x

CONTENT TO SUMMARIZE:
{chunk}

PRESERVATION PRIORITIES (in order):
1. Facts directly answering the query
2. Named entities (people, places, organizations, dates)
3. Quantitative data (numbers, statistics, measurements)
4. Causal relationships and key conclusions
5. Supporting evidence for main points

REMOVE:
- Redundant restatements
- Filler phrases and verbose language
- Examples when the pattern is clear
- Tangential information unrelated to query

OUTPUT FORMAT:
{{
  "summary": "<compressed content>",
  "preserved_facts": [<list of key facts kept>],
  "removed_topics": [<list of topics dropped>],
  "compression_achieved": <actual ratio>,
  "information_loss_risk": "low|medium|high"
}}
"""
compressed = llm_query(summarize_prompt)
```

---

#### 5. Synthesis Agent Template

**Purpose:** Aggregate results from multiple sub-agents into a coherent final answer.

**When to Use:**
- After partition+map phase completes
- Combining results from parallel sub-agents
- Final step before returning to user

**Template:**
```
You are a synthesis agent. Combine results from {num_sub_agents} sub-agents into a unified answer.

ORIGINAL QUERY: {query}

SUB-AGENT RESULTS:
{sub_results}

SYNTHESIS INSTRUCTIONS:
1. Identify consensus findings (mentioned by multiple sub-agents)
2. Resolve conflicts between sub-agent conclusions
3. Aggregate quantitative results (sums, counts, averages as appropriate)
4. Note any gaps or areas of uncertainty
5. Structure the final answer to directly address the original query

CONFLICT RESOLUTION RULES:
- Prefer results with higher confidence scores
- Prefer results from larger/more representative chunks
- Flag unresolvable conflicts for user attention

OUTPUT FORMAT:
{
  "answer": "<direct answer to query>",
  "confidence": <0.0-1.0>,
  "consensus_findings": [<findings agreed by multiple agents>],
  "conflicts_resolved": [<conflicts and how resolved>],
  "unresolved_issues": [<issues requiring user input>],
  "coverage": {
    "chunks_processed": <n>,
    "chunks_successful": <n>,
    "estimated_completeness": <percentage>
  }
}
```

**Expected Output:**
```json
{
  "answer": "The dataset contains 1,247 customer reviews. 68% positive (847), 22% negative (274), 10% neutral (126). Main positive themes: product quality, fast shipping. Main complaints: customer service response time, packaging.",
  "confidence": 0.94,
  "consensus_findings": ["Product quality praised", "Shipping speed appreciated", "Customer service criticized"],
  "conflicts_resolved": [{"issue": "Total count mismatch", "resolution": "Used chunk 3's count (corrected boundary duplicate)"}],
  "unresolved_issues": [],
  "coverage": {
    "chunks_processed": 5,
    "chunks_successful": 5,
    "estimated_completeness": 100
  }
}
```

**Example Instantiation:**
```python
# After collecting results from chunk agents
sub_results_formatted = "\n\n".join([
    f"=== Sub-Agent {i+1} (Chunk {r['chunk_id']}) ===\n{json.dumps(r, indent=2)}"
    for i, r in enumerate(chunk_results)
])

synthesis_prompt = f"""
You are a synthesis agent. Combine results from {len(chunk_results)} sub-agents into a unified answer.

ORIGINAL QUERY: Classify all product reviews and provide sentiment distribution

SUB-AGENT RESULTS:
{sub_results_formatted}

SYNTHESIS INSTRUCTIONS:
1. Identify consensus findings (mentioned by multiple sub-agents)
2. Resolve conflicts between sub-agent conclusions
3. Aggregate quantitative results (sums, counts, averages as appropriate)
4. Note any gaps or areas of uncertainty
5. Structure the final answer to directly address the original query

CONFLICT RESOLUTION RULES:
- Prefer results with higher confidence scores
- Prefer results from larger/more representative chunks
- Flag unresolvable conflicts for user attention

OUTPUT FORMAT:
{{
  "answer": "<direct answer to query>",
  "confidence": <0.0-1.0>,
  "consensus_findings": [<findings agreed by multiple agents>],
  "conflicts_resolved": [<conflicts and how resolved>],
  "unresolved_issues": [<issues requiring user input>],
  "coverage": {{
    "chunks_processed": <n>,
    "chunks_successful": <n>,
    "estimated_completeness": <percentage>
  }}
}}
"""
final_answer = llm_query(synthesis_prompt)
```

---

#### 6. Verification Agent Template

**Purpose:** Check completeness and correctness of processing results.

**When to Use:**
- After synthesis to validate the answer
- When task requires high accuracy guarantees
- To detect missed edge cases or processing errors

**Template:**
```
You are a verification agent. Check the completeness and correctness of the processing results.

ORIGINAL QUERY: {query}
PROPOSED ANSWER: {proposed_answer}

VERIFICATION CONTEXT (sample from original):
{verification_sample}

PROCESSING METADATA:
- Total context size: {total_size}
- Chunks processed: {chunks_processed}
- Reported coverage: {coverage_percentage}%

VERIFICATION TASKS:
1. SPOT CHECK: Verify 3-5 specific claims against the verification sample
2. COMPLETENESS: Check if answer addresses all parts of the query
3. CONSISTENCY: Look for internal contradictions in the answer
4. BOUNDARY CHECK: Verify edge cases were handled (first/last items, empty sections)
5. SANITY CHECK: Do the numbers/conclusions make logical sense?

OUTPUT FORMAT:
{
  "verification_status": "PASS|FAIL|NEEDS_REVIEW",
  "spot_checks": [
    {"claim": "<claim>", "verified": true|false, "evidence": "<supporting evidence or contradiction>"}
  ],
  "completeness_score": <0.0-1.0>,
  "issues_found": [
    {"severity": "critical|warning|info", "description": "<issue>", "recommendation": "<fix>"}
  ],
  "confidence_adjustment": <-0.2 to +0.1>,
  "recommendation": "<proceed|reprocess|manual_review>"
}
```

**Expected Output:**
```json
{
  "verification_status": "PASS",
  "spot_checks": [
    {"claim": "Total 1,247 reviews", "verified": true, "evidence": "Sample extrapolation consistent"},
    {"claim": "68% positive", "verified": true, "evidence": "Spot check of 20 items: 14 positive (70%)"},
    {"claim": "Main complaint: customer service", "verified": true, "evidence": "Found 3 mentions in sample"}
  ],
  "completeness_score": 0.95,
  "issues_found": [
    {"severity": "info", "description": "5 reviews in non-English not classified", "recommendation": "Note limitation in response"}
  ],
  "confidence_adjustment": -0.02,
  "recommendation": "proceed"
}
```

**Example Instantiation:**
```python
# Sample from different parts of context for verification
sample_start = context[:1000]
sample_middle = context[len(context)//2 : len(context)//2 + 1000]
sample_end = context[-1000:]
verification_sample = f"START:\n{sample_start}\n\nMIDDLE:\n{sample_middle}\n\nEND:\n{sample_end}"

verify_prompt = f"""
You are a verification agent. Check the completeness and correctness of the processing results.

ORIGINAL QUERY: Classify all product reviews and provide sentiment distribution
PROPOSED ANSWER: {json.dumps(synthesis_result, indent=2)}

VERIFICATION CONTEXT (sample from original):
{verification_sample}

PROCESSING METADATA:
- Total context size: {len(context)} chars
- Chunks processed: {len(chunk_results)}
- Reported coverage: {synthesis_result['coverage']['estimated_completeness']}%

VERIFICATION TASKS:
1. SPOT CHECK: Verify 3-5 specific claims against the verification sample
2. COMPLETENESS: Check if answer addresses all parts of the query
3. CONSISTENCY: Look for internal contradictions in the answer
4. BOUNDARY CHECK: Verify edge cases were handled (first/last items, empty sections)
5. SANITY CHECK: Do the numbers/conclusions make logical sense?

OUTPUT FORMAT:
{{
  "verification_status": "PASS|FAIL|NEEDS_REVIEW",
  "spot_checks": [
    {{"claim": "<claim>", "verified": true|false, "evidence": "<supporting evidence or contradiction>"}}
  ],
  "completeness_score": <0.0-1.0>,
  "issues_found": [
    {{"severity": "critical|warning|info", "description": "<issue>", "recommendation": "<fix>"}}
  ],
  "confidence_adjustment": <-0.2 to +0.1>,
  "recommendation": "<proceed|reprocess|manual_review>"
}}
"""
verification = llm_query(verify_prompt)
```

---

#### Template Selection Guide

| Task Type | Primary Template | Supporting Templates |
|-----------|-----------------|---------------------|
| Unknown context format | Peek | Grep, Chunk Analysis |
| Keyword search | Grep | Verification |
| Classification/Extraction | Chunk Analysis | Synthesis, Verification |
| Compression needed | Summarization | Synthesis |
| Multi-document QA | Peek, Chunk Analysis | Synthesis, Verification |
| High-stakes analysis | Any primary | Always include Verification |

#### Composing Templates in a Pipeline

```python
# Full RLM pipeline example
def process_large_context(query, context):
    # 1. Peek to understand structure
    structure = llm_query(peek_template.format(
        N=2000,
        context_sample=context[:2000],
        total_size=len(context)
    ))

    # 2. Decide strategy based on peek results
    if structure['recommended_strategy'] == 'grep_first':
        filtered = llm_query(grep_template.format(...))
        context = filtered  # narrowed context

    # 3. Partition and map
    chunks = partition(context, chunk_size=10000)
    chunk_results = [
        llm_query(chunk_template.format(
            chunk_index=i,
            total_chunks=len(chunks),
            ...
        ))
        for i, chunk in enumerate(chunks)
    ]

    # 4. Synthesize
    answer = llm_query(synthesis_template.format(
        num_sub_agents=len(chunks),
        sub_results=chunk_results,
        ...
    ))

    # 5. Verify (optional but recommended)
    verification = llm_query(verification_template.format(...))

    if verification['recommendation'] == 'proceed':
        return answer
    elif verification['recommendation'] == 'reprocess':
        # Retry with different strategy
        pass
    else:
        # Flag for manual review
        pass
```

---

## Part 5: Benchmark Results

### OOLONG (3,000-6,000 entries, classification + counting)

| Model | Context | Accuracy | vs Base |
|-------|---------|----------|---------|
| GPT-5 Base | 131K | 44.00% | — |
| GPT-5 RLM | 131K | 56.50% | +28% |
| GPT-5-mini RLM | 132K | ~64 pts | +114% vs GPT-5 |
| GPT-5-mini RLM | 263K | ~46 pts | +49% |

### OOLONG-Pairs (Quadratic complexity, 32K tokens)

| Model | Accuracy |
|-------|----------|
| GPT-5 Base | 0.04% |
| GPT-5 RLM | **58.00%** |
| Qwen3-Coder Base | 0.06% |
| Qwen3-Coder RLM | 23.11% |

### BrowseComp-Plus (Multi-hop, document scaling)

| Documents | Tokens | GPT-5 RLM | ReAct+BM25 | Base |
|-----------|--------|-----------|------------|------|
| 10 | Small | ~95% | ~95% | ~95% |
| 100 | ~10M | ~90% | 75% | 40% |
| 1,000 | 6-11M | **100%** | 50% | 0% |

### LoCoDiff (Git diff tracking, 75k+ tokens)

- GPT-5 Base: <10% success on 75k+ histories
- RLM: Enables one-shot solutions via programmatic processing

### Cost Analysis

| Context Range | RLM Cost Behavior |
|---------------|-------------------|
| <100K tokens | Comparable to base |
| 100K-500K | Log-linear, up to 3x cheaper than summarization |
| 500K-10M | $0.99 avg (BrowseComp+), 2-3x cheaper than direct |
| 10M+ | Only viable option |

**When to Use RLM:**
- Context >100K tokens with linear/quadratic complexity
- Multi-document synthesis (50+ documents)
- Tasks where base models fail completely
- NOT for: strict latency requirements, predictable costs, simple lookups

---

## Part 6: Claude Code Integration

### Concept Mapping

| RLM Concept | Claude Code Equivalent | Gap |
|-------------|----------------------|-----|
| Root LM | Main Claude session | None |
| REPL Environment | Bash + Read/Write/Glob/Grep | Partial |
| Context Variable | Repository files (via tools) | Significant |
| Recursive LM Calls | Task tool (subagent_type) | Partial |
| Code Block Output | Not primary paradigm | Full gap |
| Context Partitioning | Manual via prompts | Significant |

### Already RLM-like in Claude Code

1. **Hierarchical decomposition** - Main session spawns sub-agents via Task tool
2. **Parallel execution** - `run_in_background: true` enables concurrent sub-agents
3. **Context isolation** - Each sub-agent starts fresh
4. **Tool-based context access** - Glob, Grep, Read provide programmatic patterns
5. **Result synthesis** - TaskOutput collects results for orchestrator

### Pattern 1: RLM-Style Codebase Analysis

```
STRATEGY (RLM-inspired):
1. PEEK: Use Glob to understand structure before reading
2. GREP: Search for patterns rather than reading everything
3. PARTITION: If >5 files, spawn sub-agents for subsets
4. SYNTHESIZE: Combine sub-agent results

DECOMPOSITION RULES:
- >5 files matching pattern → spawn sub-agent
- File >500 lines → read in chunks or spawn file-specific agent
- Independent parts → parallelize
```

### Pattern 2: Parallel File Processing

```
PHASE 1 - DISCOVERY (Parallel):
Task(prompt: "Analyze _layouts/*.html", run_in_background: true) → id1
Task(prompt: "Analyze _includes/*.html", run_in_background: true) → id2
Task(prompt: "Analyze _sass/*.scss", run_in_background: true) → id3

PHASE 2 - COLLECT:
TaskOutput(id1) → result1
TaskOutput(id2) → result2
TaskOutput(id3) → result3

PHASE 3 - SYNTHESIZE:
Combine results into unified analysis
```

### Pattern 3: Context Manifest

For large codebases, create initial manifest:
```
1. Glob to build file index by type
2. Cache structure metadata in TodoWrite
3. Sub-agents receive relevant manifest subset
4. Lazy-load actual content only when needed
```

### Chunking Strategies for Code

| Strategy | Application |
|----------|-------------|
| By directory | Sub-agent per `_posts/`, `_layouts/`, `_plugins/` |
| By file type | Markdown agent, Ruby agent, SCSS agent |
| By concern | Content agent, config agent, build agent |
| By size | Split large files at natural boundaries |

### Limitations Claude Code Cannot Address

1. **No persistent REPL** - Tools are stateless request/response
2. **Not code-driven** - Prompt-driven interaction paradigm
3. **No automatic strategy emergence** - Requires explicit prompt engineering
4. **No fine-grained cost control** - Sub-agents are cost black boxes

---

## Part 7: Implementation Checklist

### Core Infrastructure
- [ ] RLM class with backend/environment initialization
- [ ] Execution loop with action parsing (code blocks)
- [ ] Depth tracking mechanism
- [ ] Termination detection (FINAL/FINAL_VAR parsing)

### LM Backend
- [ ] OpenAI client
- [ ] Anthropic client
- [ ] OpenRouter client
- [ ] Local model support (vLLM)

### Environment Layer
- [ ] BaseEnvironment interface (`execute`, `get_variable`)
- [ ] LocalREPL (Python `exec()`, namespace isolation)
- [ ] DockerREPL (container lifecycle, HTTP proxy)
- [ ] ModalREPL (cloud sandbox provisioning)

### Recursive Call System
- [ ] `llm_query()` function stub in REPL namespace
- [ ] Request routing to host process
- [ ] Context partitioning support
- [ ] Result marshaling

### Observability
- [ ] JSONL trajectory logging
- [ ] Call graph visualization
- [ ] Code/output inspection UI

### Optimizations (Future)
- [ ] Async sub-calls (currently blocking/sequential)
- [ ] Prefix caching for repeated context access
- [ ] Cost/runtime estimation

---

## Part 8: Error Handling and Recovery

RLM systems involve recursive sub-calls, parallel processing, and context partitioning. This complexity introduces multiple failure modes that require explicit handling strategies.

### Common Failure Modes

| Failure Mode | Detection Signal | Recovery Action |
|--------------|------------------|-----------------|
| Empty grep results | `matches == []` | Broaden pattern OR peek for structure |
| Sub-agent timeout | No response in X seconds | Reduce chunk size, retry |
| Contradictory results | Sub-results conflict | Spawn verification agent |
| Missing information | Answer incomplete | Check partition boundaries |
| Cost overrun | Token count exceeds budget | Increase chunk size, reduce parallelism |
| Recursion explosion | Depth/count exceeds limits | Terminate branch, return partial |
| Malformed output | FINAL/FINAL_VAR missing | Retry with explicit output instruction |
| Context serialization failure | Large object cannot marshal | Chunk context before passing |

### Defensive Patterns

**1. Always Peek Before Committing to Strategy**

```python
# Before deciding on grep vs partition vs direct:
print(f"Context length: {len(context)} chars")
print(f"Context type: {type(context)}")
print(context[:2000])  # Preview structure

# Only then choose strategy based on observed structure
```

**2. Validate Grep Patterns on Sample Before Full Scan**

```python
# Test pattern on small sample first
sample = context[:5000]
test_matches = re.findall(pattern, sample, re.IGNORECASE)
print(f"Sample matches: {len(test_matches)}")

# If zero matches on sample, pattern likely wrong
if not test_matches:
    # Try alternative patterns before full scan
    pass
else:
    # Proceed with full context
    matches = re.findall(pattern, context, re.IGNORECASE)
```

**3. Include Overlap in Partitions for Boundary Safety**

```python
# Bad: Hard boundaries lose cross-chunk information
chunks = [context[i:i+10000] for i in range(0, len(context), 10000)]

# Good: Overlapping chunks catch boundary cases
chunk_size = 10000
overlap = 500
chunks = []
for i in range(0, len(context), chunk_size - overlap):
    chunks.append(context[i:i+chunk_size])
```

**4. Set Explicit Limits on Recursion Depth and Sub-agent Count**

```python
rlm = RLM(
    max_depth=2,           # Prevent infinite recursion
    max_iterations=30,     # Limit per-call iterations
    max_sub_agents=10,     # Cap parallel spawning
    timeout_seconds=300,   # Global timeout
)
```

### Recovery Protocols

**Empty Grep Results Recovery**

```
IF grep_results.empty:
    1. Check pattern syntax
       - Verify regex is valid
       - Test with re.compile() first

    2. Peek at different context regions
       - Sample beginning, middle, end
       - Look for actual data format

    3. Try case-insensitive search
       - Add re.IGNORECASE flag
       - Try lowercase pattern variant

    4. Broaden pattern progressively
       - Remove specific constraints
       - Use wildcards: .* instead of specific terms

    5. Fall back to partition+scan
       - If grep fundamentally wrong approach
       - Process chunks semantically instead
```

**Conflicting Sub-results Recovery**

```
IF sub_results.conflict:
    1. Identify conflicting claims
       - Compare key assertions across results
       - Note which chunks produced which claims

    2. Spawn targeted verification agent
       - Give verifier both conflicting claims
       - Ask for evidence-based resolution

    3. Examine boundary regions between chunks
       - Conflicts often arise from split context
       - Re-process with overlapping chunks

    4. Check for context ambiguity
       - Same term, different meanings
       - Temporal conflicts (old vs new info)

    5. Report uncertainty if unresolved
       - Don't force false confidence
       - Present both interpretations with evidence
```

**Timeout Recovery**

```
IF sub_agent.timeout:
    1. Log which chunk/query caused timeout

    2. Reduce chunk size
       - Halve the partition size
       - Retry with smaller context

    3. Simplify query
       - Break complex query into sub-questions
       - Process sequentially instead of combined

    4. Check for infinite loops
       - Review sub-agent code generation
       - Add iteration limits to loops

    5. Fall back to synchronous processing
       - Disable parallelism for problematic chunks
```

**Cost Overrun Recovery**

```
IF token_count > budget:
    1. Increase chunk size (fewer sub-calls)
       - Larger chunks = fewer LLM invocations
       - Trade granularity for cost

    2. Reduce parallelism
       - Sequential processing uses less context
       - Reuse results across iterations

    3. Switch to summarization first
       - Compress context before detailed analysis
       - Accept some information loss

    4. Early termination with partial results
       - Return best answer so far
       - Flag as incomplete
```

### Graceful Degradation

**When RLM Approach Fails Entirely**

Sometimes the recursive strategy cannot succeed. Recognize and handle total failure:

```python
def attempt_rlm_with_fallback(query, context, rlm):
    try:
        result = rlm.completion(query, context=context, timeout=300)

        if result.success:
            return result.response

        # RLM returned but failed internally
        if result.error_type == "recursion_limit":
            return fallback_to_summarize_then_answer(query, context)

        if result.error_type == "no_strategy_found":
            return fallback_to_chunked_direct(query, context)

    except TimeoutError:
        return fallback_to_direct_truncated(query, context[:MAX_DIRECT_CONTEXT])

    except Exception as e:
        return {"status": "failed", "error": str(e), "suggestion": "human_review"}
```

**Communicating Partial Results**

When complete analysis isn't possible, structure partial results clearly:

```python
partial_response = {
    "status": "partial",
    "confidence": 0.6,
    "completed_chunks": 8,
    "total_chunks": 12,
    "failed_chunks": [3, 7, 11, 12],
    "partial_answer": "Based on 67% of context analyzed...",
    "limitations": [
        "Chunks 3,7 timed out - may contain relevant information",
        "Chunk 11-12 boundary may split key document"
    ],
    "suggestions": [
        "Retry with smaller chunk size",
        "Manually review chunks 3, 7, 11, 12"
    ]
}
```

**When to Ask for Human Guidance**

Escalate to human when:

| Condition | Signal | Recommended Action |
|-----------|--------|-------------------|
| Ambiguous query | Multiple valid interpretations | Ask for clarification |
| Contradictions unresolved | Verification agent also conflicts | Present options to human |
| Domain expertise required | Technical terms unknown | Request domain context |
| Ethical/safety concerns | Content requires judgment | Human review before proceeding |
| Cost exceeds threshold | Budget exhausted | Seek approval for continuation |
| Repeated failures | 3+ retries unsuccessful | Human debugging needed |

**Degradation Hierarchy**

When primary RLM strategy fails, degrade through these levels:

```
Level 0: Full RLM (parallel sub-agents, recursive calls)
    ↓ failure
Level 1: Sequential RLM (one sub-agent at a time)
    ↓ failure
Level 2: Single-pass partition (no recursion)
    ↓ failure
Level 3: Summarize-then-answer (lossy compression)
    ↓ failure
Level 4: Truncated direct (first N tokens only)
    ↓ failure
Level 5: Return "cannot answer" with diagnostics
```

Each level trades capability for reliability. Document which level produced the final answer.

---

## Part 9: Bash Script Implementation

This section provides practical bash scripts for implementing RLM patterns with AI CLI tools like Codex, Claude Code, or custom LLM wrappers.

### 9.1 Basic RLM Loop

```bash
#!/bin/bash
# rlm-basic.sh - Simple RLM implementation

set -e

CONTEXT_FILE="$1"
QUERY="$2"
MAX_CHUNK_SIZE=100000  # ~100K chars per chunk

# Step 1: ASSESS - Get context size
TOTAL_SIZE=$(wc -c < "$CONTEXT_FILE")
echo "[ASSESS] Context size: $TOTAL_SIZE chars"

# Step 2: DECIDE - Choose strategy
if [ "$TOTAL_SIZE" -lt 50000 ]; then
    echo "[DECIDE] Small context, direct processing"
    STRATEGY="direct"
else
    echo "[DECIDE] Large context, chunking required"
    STRATEGY="chunk"
fi

# Step 3: EXECUTE - Process based on strategy
if [ "$STRATEGY" = "direct" ]; then
    # Direct LLM call
    codex exec "Query: $QUERY\n\nContext:\n$(cat "$CONTEXT_FILE")" 2>&1
else
    # Chunk and process
    CHUNK_COUNT=$(( (TOTAL_SIZE + MAX_CHUNK_SIZE - 1) / MAX_CHUNK_SIZE ))
    echo "[EXECUTE] Splitting into $CHUNK_COUNT chunks"

    # Create temp dir for results
    RESULT_DIR=$(mktemp -d)

    # Process chunks in parallel
    split -b "$MAX_CHUNK_SIZE" "$CONTEXT_FILE" "$RESULT_DIR/chunk_"

    for chunk in "$RESULT_DIR"/chunk_*; do
        chunk_name=$(basename "$chunk")
        echo "[SUB-CALL] Processing $chunk_name"
        codex exec "Extract relevant information for: $QUERY\n\nChunk:\n$(cat "$chunk")" \
            > "$RESULT_DIR/result_$chunk_name" 2>&1 &
    done
    wait

    # Aggregate results
    echo "[AGGREGATE] Combining results"
    COMBINED=$(cat "$RESULT_DIR"/result_*)
    codex exec "Final answer for: $QUERY\n\nPartial results:\n$COMBINED" 2>&1

    rm -rf "$RESULT_DIR"
fi
```

### 9.2 Parallel Sub-Agent Launcher

```bash
#!/bin/bash
# rlm-parallel.sh - Launch multiple sub-agents in parallel

QUERY="$1"
shift
FILES=("$@")

MAX_PARALLEL=5
RESULT_DIR=$(mktemp -d)
PIDS=()

launch_agent() {
    local file="$1"
    local idx="$2"
    echo "[AGENT $idx] Starting: $file"
    codex exec -i "$file" "Analyze this file for: $QUERY. Return key findings." \
        > "$RESULT_DIR/result_$idx.txt" 2>&1
}

# Launch agents with parallelism limit
idx=0
for file in "${FILES[@]}"; do
    launch_agent "$file" "$idx" &
    PIDS+=($!)
    ((idx++))

    # Wait if max parallel reached
    if [ ${#PIDS[@]} -ge $MAX_PARALLEL ]; then
        wait "${PIDS[0]}"
        PIDS=("${PIDS[@]:1}")
    fi
done

# Wait for all remaining
wait

# Aggregate
echo "[AGGREGATE] Combining ${#FILES[@]} results"
codex exec "Synthesize findings for: $QUERY

Results from ${#FILES[@]} files:
$(cat "$RESULT_DIR"/result_*.txt)" 2>&1

rm -rf "$RESULT_DIR"
```

### 9.3 Dynamic Sub-Agent Spawning

```bash
#!/bin/bash
# rlm-dynamic.sh - Spawn sub-agents based on initial analysis

CONTEXT="$1"
QUERY="$2"

# Phase 1: Analyze and plan
echo "[PLAN] Analyzing context structure..."
PLAN=$(codex exec "Analyze this context and determine how to partition it for the query: $QUERY

Context preview (first 5000 chars):
$(head -c 5000 "$CONTEXT")

Output JSON with:
- partition_strategy: 'by_file' | 'by_section' | 'by_lines'
- chunk_count: number
- chunk_boundaries: array of line numbers or markers" 2>&1)

echo "$PLAN"

# Phase 2: Parse plan and execute
# (In production, parse JSON properly)
CHUNK_COUNT=$(echo "$PLAN" | grep -oP 'chunk_count.*?(\d+)' | grep -oP '\d+' | head -1)
CHUNK_COUNT=${CHUNK_COUNT:-5}  # Default to 5

echo "[EXECUTE] Spawning $CHUNK_COUNT sub-agents..."

# Phase 3: Map - process each chunk
TOTAL_LINES=$(wc -l < "$CONTEXT")
LINES_PER_CHUNK=$(( (TOTAL_LINES + CHUNK_COUNT - 1) / CHUNK_COUNT ))

RESULT_DIR=$(mktemp -d)
for i in $(seq 0 $((CHUNK_COUNT - 1))); do
    START_LINE=$((i * LINES_PER_CHUNK + 1))
    END_LINE=$(((i + 1) * LINES_PER_CHUNK))

    echo "[SUB-AGENT $i] Lines $START_LINE-$END_LINE"
    sed -n "${START_LINE},${END_LINE}p" "$CONTEXT" | \
        codex exec -m haiku "Process this chunk for: $QUERY" \
        > "$RESULT_DIR/result_$i.txt" 2>&1 &
done
wait

# Phase 4: Reduce
echo "[REDUCE] Aggregating results..."
codex exec "Final synthesis for: $QUERY

Sub-agent results:
$(for f in "$RESULT_DIR"/result_*.txt; do
    echo "=== $(basename "$f") ==="
    cat "$f"
    echo
done)" 2>&1

rm -rf "$RESULT_DIR"
```

### 9.4 Codex + Claude Code Integration

```bash
#!/bin/bash
# rlm-hybrid.sh - Use Codex for sub-calls, Claude Code for orchestration

# This script is called FROM Claude Code using Bash tool
# Claude Code handles orchestration, Codex handles focused sub-tasks

MODE="$1"  # 'chunk' | 'aggregate' | 'verify'
shift

case "$MODE" in
    chunk)
        # Process a single chunk
        CHUNK_FILE="$1"
        QUERY="$2"
        codex exec -m haiku -i "$CHUNK_FILE" \
            "Extract key information relevant to: $QUERY. Be concise." 2>&1
        ;;

    aggregate)
        # Aggregate multiple results
        QUERY="$1"
        shift
        RESULTS="$@"
        codex exec "Synthesize these partial results for: $QUERY

Results:
$(for r in $RESULTS; do cat "$r"; echo "---"; done)" 2>&1
        ;;

    verify)
        # Verify an answer
        ANSWER="$1"
        QUERY="$2"
        codex exec "Verify this answer is correct and complete for: $QUERY

Answer: $ANSWER

Output: VALID | INVALID with reason" 2>&1
        ;;
esac
```

### 9.5 Retry with Exponential Backoff

```bash
#!/bin/bash
# rlm-retry.sh - RLM with robust error handling

MAX_RETRIES=3
BASE_DELAY=2

run_with_retry() {
    local cmd="$1"
    local retry=0

    while [ $retry -lt $MAX_RETRIES ]; do
        if output=$(eval "$cmd" 2>&1); then
            echo "$output"
            return 0
        fi

        retry=$((retry + 1))
        delay=$((BASE_DELAY ** retry))
        echo "[RETRY] Attempt $retry failed, waiting ${delay}s..." >&2
        sleep $delay
    done

    echo "[ERROR] All $MAX_RETRIES attempts failed" >&2
    return 1
}

# Usage
run_with_retry "codex exec 'Your prompt here'"
```

### 9.6 Cost-Aware Processing

```bash
#!/bin/bash
# rlm-cost-aware.sh - Estimate and control costs

estimate_cost() {
    local chars="$1"
    local model="$2"

    # Rough estimates (chars to tokens ~4:1)
    local tokens=$((chars / 4))

    case "$model" in
        "opus")   echo "scale=4; $tokens * 0.000015" | bc ;;
        "sonnet") echo "scale=4; $tokens * 0.000003" | bc ;;
        "haiku")  echo "scale=4; $tokens * 0.00000025" | bc ;;
        *)        echo "scale=4; $tokens * 0.000003" | bc ;;
    esac
}

CONTEXT_SIZE=$(wc -c < "$1")
ESTIMATED_COST=$(estimate_cost "$CONTEXT_SIZE" "sonnet")

echo "[COST] Estimated input cost: \$$ESTIMATED_COST"

if (( $(echo "$ESTIMATED_COST > 1.00" | bc -l) )); then
    echo "[COST] High cost detected. Use chunking with haiku for sub-calls."
    MODEL_ROOT="sonnet"
    MODEL_SUB="haiku"
else
    MODEL_ROOT="sonnet"
    MODEL_SUB="sonnet"
fi

echo "[COST] Strategy: root=$MODEL_ROOT, sub=$MODEL_SUB"
```

---

## Sources

- [Paper (arXiv)](https://arxiv.org/abs/2512.24601)
- [Blog Post](https://alexzhang13.github.io/blog/2025/rlm/)
- [GitHub Repository](https://github.com/alexzhang13/rlm)
- [Minimal Implementation](https://github.com/alexzhang13/rlm-minimal)
- [Prime Intellect Blog](https://www.primeintellect.ai/blog/rlm)

---

## Key Insight

> "The prompt as a Python variable, which can be processed programmatically in arbitrary REPL flows."

RLM's value is not marginal improvement on standard tasks, but **enabling entire classes of problems** that base models cannot solve at all:
- 0.04% → 58% on quadratic complexity tasks (OOLONG-Pairs)
- 0% → 91.33% on 1000-document synthesis (BrowseComp+, 150-task eval)
- 100% accuracy achievable on focused 20-task subsets at 1K docs scale

The fundamental shift: **context management becomes programmatic, not neural**.
