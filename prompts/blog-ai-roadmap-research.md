# Blog Post: AI Agent Swarm for Product Roadmap Research

## Goal

Write and publish a blog post for jonnyzzz.com about using an AI agent swarm to review
and research a large product roadmap. Publish date: **2026-03-25** (Wednesday).

The post should be written in Eugene's voice (see SKILL.md and CLAUDE.md for style rules).

---

## What You Must Read First

1. Read `/Users/jonnyzzz/Work/jonnyzzz.com-src/SKILL.md` — author voice, style, length targets
2. Read `/Users/jonnyzzz/Work/jonnyzzz.com-src/CLAUDE.md` — front matter format, tags, file naming
3. Read `/Users/jonnyzzz/Work/jonnyzzz.com-src/RLM.md` — RLM methodology (referenced in the post)
4. Read these example posts for style reference:
   - `/Users/jonnyzzz/Work/jonnyzzz.com-src/_posts/blog/2026-02-06-run-agent-multi-agent-orchestration.md`
   - `/Users/jonnyzzz/Work/jonnyzzz.com-src/_posts/blog/2026-01-30-orchestrating-ai-fleets.md`
   - `/Users/jonnyzzz/Work/jonnyzzz.com-src/_posts/blog/2026-03-17-run-agent-v2-release.md`

## What the Post Is About

This is a case study of using an AI agent swarm to do something normally reserved for senior
engineers: **research and analyze a large product roadmap** — hundreds of open issues against
a multi-million-line codebase — and produce actionable implementation specs, effort estimates,
dependency graphs, and solution designs for each one.

You may use run-agent.sh recursively (research sub-agents to read source files, writing
sub-agents to draft sections, review sub-agents to check quality). See instructions below.

---

## Content Brief — What to Cover

### The Problem

A product team has a large backlog of open issues. Each issue is a YouTrack stub: title,
description, maybe some comments. No implementation plan. No code-level analysis. No effort
estimate. No dependency map.

A senior engineer would spend 2–4 hours per issue reading the codebase, understanding the
architecture, scoping the change, writing it up. For 130+ issues, that's weeks of analyst work.

### The Experiment

We ran an AI agent swarm to do this work instead. The swarm used:
- **run-agent.sh** (`https://run-agent.jonnyzzz.com`) — orchestration shell script that launches
  Claude, Codex, and Gemini agents with a prompt file and a working directory
- **MCP Steroid** (`https://mcp-steroid.jonnyzzz.com`) — IntelliJ plugin giving agents programmatic
  access to the entire codebase: search, PSI navigation, class resolution, call graph tracing
- **Shell orchestration scripts** — bash pipelines that parallelise work, detect completion,
  skip resolved issues, handle retries, and maintain a message bus
- **TASK*.md files** — structured task definitions written once, consumed by many agents

### The Pipeline

Three rounds per issue (R1 → R2 → R3):
1. **R1 (Claude)** — reads the issue, explores the codebase with MCP Steroid, produces a
   first-draft research document: problem analysis, relevant files, 2–3 solution options with
   effort/complexity/risk
2. **R2 (Codex)** — validates all R1 file references against the actual codebase, finds exact
   line numbers, checks git history for recent changes, identifies edge cases R1 missed
3. **R3 (Claude)** — synthesises R1+R2, resolves conflicts, writes the final recommendation
   with concrete implementation steps, test strategy, and follow-up work

Two issues processed in parallel at all times.

### The Scale

Metrics to include in the post (these are real):
- **130+ issues** analyzed
- **818 agent runs** (Claude 39%, Codex 39%, Gemini 1%, unknown 20%)
- **~$576 total cost** at published API prices (~$315 Codex + ~$259 Claude)
- **~$6 per fully-researched issue**
- **4 calendar days** (with overnight gaps — continuous would be ~2 days)
- **~155–200M tokens** consumed
- **93 issues** received full 3-round research
- **~40,000 lines** of structured output (avg ~400 lines per issue)
- **9 issues** identified as already implemented during research (saved rework)
- **~39%** of the backlog identified as directly implementable by agents with low risk

### The Output Quality

Each researched issue contains:
- Concrete file:class:method references with line numbers
- 2–3 solution options each with Complexity (Low/Med/High), Effort (S/M/L/XL),
  Key Changes list, Test Strategy, and Trade-offs table
- A final Recommendation with rationale
- Validation status (R2 confirmed files exist in codebase)

This is not summarization. It is the analyst work a senior engineer does before writing code.

### What We Learned

- **The R1→R2→R3 pipeline matters**: R1 alone produces ~60% quality. R2 catches phantom file
  references (files R1 hallucinated or misnamed). R3 resolves conflicts and produces the
  actionable recommendation. Skipping R2 leads to brittle outputs.
- **MCP Steroid as the force multiplier**: Without codebase access, agents produce vague
  summaries. With MCP Steroid, they produce specific class names, method signatures, and
  line ranges. This is the difference between a research document and a useful one.
- **One file per MCP call is an anti-pattern**: Agents default to reading one file per call.
  A Kotlin script reading 5–10 files in one call would be 5–10x more efficient. Future
  improvement.
- **Codex buffers all output**: Codex writes 0 bytes until the run completes. Monitoring
  scripts need to account for this — a 0-byte file is not necessarily a stuck agent.
- **Context rot is real, RLM is the fix**: Each agent works on one issue with a fresh context.
  The message bus (MESSAGE-BUS.md) carries findings between rounds. This is RLM in practice.
- **Cost is not the constraint**: $6/issue is negligible. The constraint is human review
  bandwidth — someone needs to read the outputs and decide which solutions to implement.

### The AI-ization Angle

Connect this to the broader pattern: AI Agents are not just for writing code. They're for
doing the *thinking before the code* — scoping, analyzing, comparing options, recommending.
The research swarm shifts the team's role from "spending 4h to understand an issue" to
"spending 20min reviewing what the agent found."

Frame the ~39% figure: roughly 4 in 10 issues are small, self-contained, well-understood
enough that an agent could implement them end-to-end with low risk. The research produces
the spec; the same pipeline can implement from the spec.

---

## What You Must NOT Include

- Do NOT mention the product name, the team, or the company
- Do NOT include any issue IDs (no CPP-XXXXX, no CLPM-XXXXX)
- Do NOT include YouTrack URLs or internal URLs
- Do NOT describe internal team structure or plans
- Refer to it generically as "a product team", "a large product", "a popular IDE component",
  "a complex codebase", or similar

---

## Output File

Create the blog post at:
`/Users/jonnyzzz/Work/jonnyzzz.com-src/_posts/blog/2026-03-25-ai-agent-roadmap-research.md`

Front matter must include:
- `date: 2026-03-25`
- `author: Eugene Petrenko`
- Tags from: `ai-agents`, `ai-coding`, `multi-agent`, `orchestration`, `mcp`, `run-agent`
- `categories: blog`
- A strong excerpt (1–2 sentences)
- A good title (not too generic — something like "We Let AI Agents Research Our Entire
  Product Roadmap. Here's What They Found." or similar — you decide the best title)

Target length: **2000–3500 words**. This is a deep-dive / case study post.

---

## How to Use Sub-Agents

You may use `run-agent.sh` recursively. The binary is at:
`~/Work/run-agent/run-agent.sh`

Usage: `run-agent.sh [claude|codex] <working-dir> <prompt-file>`

Suggested multi-agent approach:
1. Spawn a **research agent** (claude) to read all the source material listed above
   and extract key quotes, numbers, and narrative threads — write to a temp file
2. Spawn a **draft writer** (claude) with the research notes + style guide to write
   the full draft post
3. Spawn a **reviewer** (claude) to check: Is it in Eugene's voice? Does it follow
   the "Must NOT include" rules? Is it too long/short?
4. If the reviewer flags issues, spawn another draft writer to fix them
5. Write the final post to the output file

Store intermediate files in:
`/Users/jonnyzzz/Work/jonnyzzz.com-src/_temp/blog-roadmap-research/`
(create the directory if needed)

---

## Communication

When done, append to the message bus:
`/Users/jonnyzzz/Work/jonnyzzz-ai-coder/projects/clion/roadmap/MESSAGE-BUS.md`

```
## YYYY-MM-DD HH:MM — blog post
**FACT**: Blog post written at _posts/blog/2026-03-25-ai-agent-roadmap-research.md
**FACT**: Title: <title>
**FACT**: Word count: ~N words
```
