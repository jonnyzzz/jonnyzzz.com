# How 16 AI Agents Fixed Our Documentation Problem

**Date:** January 24, 2026  
**Author:** Eugene Petrenko  
**Tags:** ai-agents, multi-agent, sub-agent, documentation, rlm

---

I've been documenting multi-agent orchestration patterns for months, and I had no idea how bad our docs had become
until I asked our customers --- AI agents, and they were brutally honest.

Our documentation had grown to 2,648 lines across four files. The most important commands were buried at line 91 of
CLAUDE-CODE.md, after 90 lines of introductions, explanations, and edge cases. We'd duplicated entire sections across
three CLI docs. And when AI agents tried to use these docs to spawn other AI agents, they struggled.

Here's the recursive twist: I sent agents to interview agents about documentation for spawning agents. We used
multi-agent orchestration to fix documentation about multi-agent orchestration. The tools improved themselves.

This is the story of how 16 AI agents helped us refactor documentation that was both about them and for them. This was
attempt #3, and we finally got it right by doing something simple: we stopped guessing and started asking.

## The Bigger Picture

This wasn't just about fixing documentation. It was about proving something I'd suspected but couldn't demonstrate:
multi-agent orchestration works for real engineering problems, not just toy examples.

I've been experimenting with multi-agent patterns for months, documenting the RLM methodology, building orchestration
guides. But until this project, I hadn't stress-tested it on something complex and messy. Documentation refactoring is
exactly that - subjective, iterative, full of judgment calls.

Here's where it gets meta-recursive: we used agents to spawn agents to interview agents about documentation that
teaches agents how to spawn agents. The documentation problem was its own solution. We needed better docs for
multi-agent orchestration, so we used multi-agent orchestration to improve those docs. The methodology ate its own
dogfood and came out stronger.

The fact that 16 AI agents could analyze, interview, implement, and validate better than I could alone? That changes
how I think about engineering workflows. But more importantly, the agents-spawning-agents-to-fix-agent-docs approach
proved the recursive viability of the entire pattern.

We spawned 16 agents across four distinct phases. We ran them in parallel when possible, sequentially when necessary.
We treated AI agents as actual customers and conducted structured interviews to understand their needs. We validated
the results with fresh agents who had no prior context. Some of those interview agents spawned their own sub-agents to
dig deeper into specific sections.

The outcome? Measurable improvements: 39% shorter documentation, 15% higher quality ratings, 5x faster navigation to
key commands. Production-ready output that both humans and AI agents can use effectively.

But the bigger lesson is about treating AI agents as customers. They can't be polite out of social obligation. They
won't pretend to understand confusing documentation. They'll tell you exactly where you buried the lead, what's
missing, and what's duplicated. They're brutally honest feedback machines. And when they give feedback about their own
operational instructions? That's when the recursion gets really interesting.

## Why This Mattered

### The Dual Role Problem

We'd written 2,648 lines of documentation across four files: CLAUDE-CODE.md, CODEX.md, GEMINI.md, and MULTI-AGENT.md. 
Standard developer docs, right? Not quite.

The twist: this documentation was both **about** AI agents and **for** AI agents. Human developers would read it to 
learn how to spawn sub-agents. But more importantly, the AI agents themselves would read these docs when they needed to 
spawn other AI agents. An agent working on your behalf would need to parse these instructions, understand the patterns, 
and correctly invoke another agent with the right commands and flags.

If the documentation was confusing, ambiguous, or poorly structured, the AI wouldn't just get frustrated and ask for 
clarification. It would hallucinate. It would guess. It would burn the context and tokens to figure out the right
parameters. It would use the wrong flags or miss critical setup steps. The 
documentation quality directly impacted whether agent-to-agent orchestration actually worked.

### Why AI Agents Care About Documentation Quality

AI agents aren't just slower readers than humans - they have fundamentally different constraints:

**Token costs are real.** Reading 2,648 lines of documentation translates to roughly 40,000 tokens. Every time an agent 
needed to spawn a sub-agent, it would load these docs into context. That's not just slow, it's expensive. Token costs 
compound across every operation.

**Context limits matter.** Even with 200K token context windows, shorter is better. The more documentation an agent has 
to process, the slower it responds and the more likely it is to miss crucial details buried in the middle.

**Precision matters more than style.** Ambiguity that humans can resolve through intuition becomes a hallucination risk 
for AI. When documentation says three commands are "RECOMMENDED" with no clear priority, humans might make an educated 
guess. AI agents will pick the first one they see, or worse, combine flags in creative ways that don't work.

**Navigation is harder.** Humans can Ctrl+F for keywords or skim section headers. AI agents must parse the document 
sequentially, building a mental model as they go. If the most important information is at line 91, they've already 
spent 90 lines of processing budget on preliminaries.

### The Meta-Challenge

Here's what made this interesting: we needed documentation good enough that an AI reading it could correctly spawn 
another AI, which might then need to spawn yet another AI. The clarity requirements weren't just high - they were 
recursive. Every ambiguity would compound across agent hierarchies.

One validator put it perfectly:

> "Strong operational doc. With recommended command moved to top and error handling added, would be 9/10."

That quote came from an AI agent evaluating the documentation. And it nailed exactly what was missing: quick access to 
the essential commands and proper error handling patterns.

This was our third attempt. The first two? We tested on agents, and improved with agents with various prompts. 
Each next iteration creates a more improved outcome. But I would not run it too many times to avoid a drift
from the main focus. I'd optimized for completeness over usability, documenting every option and edge case
while forgetting to answer the only question that mattered: "What command do I run right now?"

What changed? We stopped assuming we knew what good documentation looked like and started treating AI agents as actual 
customers who could tell us. They knew what they needed better than I did.

## What the Interviews Revealed

The interview data surprised the root agent --- seven agents, completely independent, and they all complained 
about the same five things. That kind of consistency doesn't lie.

### Pain Point #1: Buried the Lead

**Severity: HIGH (reported by 5/7 interviews)**

This was the killer. I'd buried our most important command at line 91 in CLAUDE-CODE.md, after 90 lines of 
introductions, prerequisites, and edge cases.

From Interview #1:
> "Most important command (line 91) hidden after 90 lines of setup. Users want copy-paste immediately."

Looking back, I see exactly what went wrong. I wrote the docs the way I'd learned to write academic papers: 
introduction, background, methodology, results. But documentation isn't a paper. Users want the answer immediately.

**Before:**
```
[Introduction]
[Background]
[Architecture overview]
[Installation]
[Configuration]
[Prerequisites]
...
Line 91: # RECOMMENDED: Use this command...
```

**After:**
```
## Purpose
Command-line interface for spawning Claude Code sub-agents.

### Quick Start
# THIS IS THE ONE COMMAND YOU NEED
claude -p --tools default --permission-mode dontAsk "prompt" 2>&1
```

**Impact:** Time-to-command dropped from 60-90 seconds to 10-15 seconds. For an AI agent reading sequentially, that's a 
5x improvement. For a human developer scanning the page, it's the difference between finding what you need and giving 
up.

### Pain Point #2: Error Handling Completely Absent

**Severity: HIGH (4/7 interviews)**

Not a single retry example. No timeout recommendations. Zero guidance on detecting token limits or API errors. No exit 
code documentation. Our docs assumed success on first try, which is approximately never how real agent orchestration 
works.

Agent feedback from Interview #4:
> "No guidance on detecting token limits/API errors. No concrete retry example with exit code checking."

This wasn't an edge case concern. Four separate agents independently identified it as a blocker. When your sub-agent 
hits a rate limit at 3 AM, you need to know: retry or fail? How long to wait? What exit code means "try again" vs "give 
up"?

**The fix:** Added Part 9 to MULTI-AGENT.md with production-ready error handling patterns:

```bash
MAX_RETRIES=3
RETRY_COUNT=0
TIMEOUT_SEC=900

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  if timeout $TIMEOUT_SEC claude -p --tools default \
     --permission-mode dontAsk "prompt" 2>&1; then
    echo "SUCCESS"
    break
  fi
  EXIT_CODE=$?
  echo "Attempt $((RETRY_COUNT+1))/$MAX_RETRIES failed (exit $EXIT_CODE)"
  RETRY_COUNT=$((RETRY_COUNT + 1))
  sleep $((RETRY_COUNT * 2))  # Exponential backoff: 2s, 4s, 6s
done
```

The new section includes:
- Retry logic with exponential backoff (2s, 4s, 6s delays)
- Timeout recommendations by task type (30s for simple queries, 600s for complex analysis)
- Exit code meanings (0 = success, 1 = general error, 41 = rate limit, 124 = timeout)
- Token limit detection patterns (grep for specific error messages)

### Pain Point #3: Authentication Steps Missing

**Severity: HIGH (3/7 interviews)**

CODEX.md referenced `~/.codex/auth.json` in multiple places but never explained how to create it. I'd assumed you'd 
already authenticated before reading the docs.

Interview #6 agent feedback:
> "Document never explains how auth.json is created. Assumes user already authenticated."

This is the classic curse of knowledge. As the person who wrote the docs, I already had `auth.json` on my machine. I'd 
logged in months ago. The auth step was invisible to me, but catastrophic for new users.

**The fix:** Added Prerequisites sections to all three CLI docs with step-by-step auth flow:

1. Verify installation: `codex --version`
2. Authenticate: `codex login`
3. Confirm: `ls ~/.codex/auth.json`
4. Test: `codex exec "hello"`

Plus a troubleshooting table for common issues:

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| `auth.json not found` | Not logged in yet | Run `codex login` |
| `invalid credentials` | Token expired | Run `codex login` again |
| `permission denied` | Wrong file permissions | `chmod 600 ~/.codex/auth.json` |

### Pain Point #4: 20% Token Overhead from Duplication

**Severity: HIGH (reported by 2/7 interviews, measured by our team)**

We'd copy-pasted entire sections across CLAUDE-CODE.md, CODEX.md, and GEMINI.md:
- MCP visibility tables (nearly identical, 80+ lines each)
- Parallel execution patterns (minimal CLI differences, 100+ lines)
- DO/DON'T best practices lists (word-for-word duplicates, 50+ lines)

This created 795 lines of duplicated content - content that every agent reading any CLI doc had to parse.

**The fix:** Extract to MULTI-AGENT.md as single source of truth. CLI docs now reference rather than duplicate.

**Results:**
- Total lines: 2,648 → 1,618 (-39%)
- Estimated tokens: ~40,000 → ~32,000 (-20%)
- Maintenance burden: Update 1 file instead of 3
- Consistency: No more drift between docs

### Pain Point #5: MCP Troubleshooting Confusion

**Severity: MEDIUM (2/7 interviews)**

Users didn't understand when Model Context Protocol servers were available to sub-agents, or how to diagnose visibility 
issues. The docs mentioned MCP but never explained the inheritance rules or debugging steps.

**The fix:** Added MCP Troubleshooting section with diagnostic table:

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Sub-agent doesn't see MCP | Not registered globally | `claude mcp add <name> <cmd>` |
| MCP listed but unavailable | Restrictive tool flags | Use `--tools default` instead of `--tools none` |
| Connection errors | Server not running | Check IntelliJ IDE is open |
| Works in parent, not in child | Command-line args block inheritance | Remove explicit `--mcp` flags |

**Validation score:** One agent rated this 9/10, commenting: "diagnostic table format is perfect - covers the exact 
confusion I had."

### The "ONE Command" Problem

This wasn't in our original analysis, but three interviews independently mentioned it: CODEX.md had THREE commands 
marked "RECOMMENDED" with no clear priority.

Agent feedback:
> "Ambiguity about which command to use. Mark ONE as primary for 95% of cases."

I thought I was being helpful by showing options. I was actually creating decision paralysis.

The problem was real. We had:
```bash
# RECOMMENDED: Minimal non-interactive
codex exec "prompt" 2>&1

# RECOMMENDED: Low-friction auto mode
codex --full-auto exec "prompt" 2>&1

# RECOMMENDED: Maximum tool access
codex --tools default --full-auto exec "prompt" 2>&1
```

Three "recommended" commands means zero recommended commands. An AI agent parsing this has to guess which one we 
actually want them to use.

**The fix in CODEX.md:**
```bash
### Quick Start

# ✅ THIS IS THE ONE COMMAND YOU NEED
codex --full-auto exec "prompt" 2>&1

Don't use alternative flag combinations unless you have
a specific reason (debugging, restricting tool access, etc.)
```

**Validation result:** 10/10 rating from independent reviewer: "Clear and effective. Zero ambiguity."

This became our guiding principle for all three CLI docs: users need ONE command to copy-paste. Not three options. Not 
a menu of flags. One command that works 95% of the time, with a separate "Advanced Usage" section for the 5% edge cases.

---

## The Implementation: RLM in Action

### What Is RLM?

Before I explain how we fixed everything, let me introduce the pattern that made this possible.

RLM, [Recursive Language Model](https://arxiv.org/abs/2512.24601), is a workflow for breaking large 
tasks into parallel agent work. If you've used 
MapReduce for data processing, RLM is the same concept applied to AI agents:

**PARTITION:** Divide work into independent tasks with clear boundaries. The rule: no inter-task dependencies. Each 
agent must be able to complete its work without waiting for another agent's output. For this project, we partitioned by 
file: 5 agents, 5 files to refactor.

**MAP:** Execute all tasks simultaneously. Use shell background jobs (`&` and `wait`) to run agents in parallel. Watch 
for rate limits - most APIs allow 3-5 concurrent requests. Each agent writes to its own output file to avoid conflicts.

**REDUCE:** Manual synthesis of all outputs. This is where the human comes in. Check that cross-references align (no 
broken links between files). Verify terminology is consistent (don't mix "sub-agent" and "child agent"). Ensure version 
numbers match. Use `diff` to spot conflicts, `grep` to validate references, and manual review for quality.

**When RLM works:**
- Tasks are independent (refactoring separate files)
- Output format is structured (markdown, JSON)
- Human can validate and merge results
- Time savings justify coordination cost

**When RLM fails:**
- Tasks require sequential coordination (Agent 2 needs Agent 1's output first)
- Outputs conflict (both agents edit the same section differently)
- API rate limits block parallelism entirely
- Coordination overhead exceeds time savings

For this project: perfect RLM fit. Five files, five agents, independent work. Parallelism cut execution time from 2+ 
hours to 30 minutes for the implementation phase.

Full methodology (chopped for agents by agents) with error handling patterns:
[jonnyzzz.com/RLM.md](https://jonnyzzz.com/RLM.md)

### Working in Parallel

Once we had customer feedback, I had a decision: fix these issues sequentially (safe, slow) or spawn parallel agents 
(risky, fast). I chose fast.

We spawned 5 agents in parallel:

- Agent 1: Refactor CLAUDE-CODE.md (Quick Start, error handling, auth setup)
- Agent 2: Refactor CODEX.md (single "THE ONE command", prerequisites, MCP troubleshooting)
- Agent 3: Refactor GEMINI.md (consistency with other CLIs)
- Agent 4: Add Part 9 to MULTI-AGENT.md (error handling patterns with retry logic)
- Agent 5: Add Part 11 to MULTI-AGENT.md (cost management and token optimization)

This was the most nerve-wracking phase. Five agents working simultaneously meant five potential points of failure. If 
two agents edited the same section differently, we'd have merge conflicts. If one agent misunderstood the requirements, 
we'd ship broken docs. But the interviews were so specific - line numbers, severity ratings, concrete examples - that 
the risk felt manageable.

Each agent received:
- Specific pain points from interviews
- Target file to modify
- Success criteria (what "done" looks like)
- Examples of desired patterns

### Timeline and Reality Check

Here's how the complete project actually played out:

**Phase 1 - Discovery (30 minutes):**
4 analysis agents examined the existing documentation structure, identified duplication, and mapped pain points. 
Parallelism cut what would have been 2 hours of sequential reading down to 30 minutes.

**Phase 2 - Customer Interviews (45 minutes):**
9 interview agents spawned, though only 7 completed successfully (2 hit API rate limits). Most ran in parallel, with 
some sequential execution when we hit connection limits. This was the most valuable phase - getting honest feedback 
from agents who would actually use these docs.

**Phase 3 - Implementation (30 minutes execution, 2 hours human coordination):**
5 implementation agents working simultaneously on the actual file changes. Agent execution: 30 minutes. Human 
coordination in the reduce phase (checking cross-references, resolving version number mismatches, validating changes): 
2 hours. This is where the RLM pattern requires human oversight.

**Phase 4 - Validation (30 minutes):**
3 fresh validator agents reviewed the updated documentation. No prior context, just "read this and tell us if it's 
better." I was genuinely nervous. What if the refactor made things worse? What if we'd optimized for the wrong thing?

**Total: ~4 hours including human coordination, 2 hours of agent execution time**

Without parallelism? I'd still be refactoring. Twelve to fifteen hours of sequential work, minimum. Parallelism cut 
that to 4 hours total. That's why this matters.

**What went wrong:**
- 2 of 9 interview agents hit API rate limits and failed silently
- Agent 4's first attempt at error handling patterns was too generic - had to re-run with specific examples
- Manual coordination in the Reduce phase took longer than expected because version numbers didn't match across files

### Command Examples: How to Interview AI Agents

Here's the actual command we used to spawn customer interview agents. These templates are copy-paste ready:

**Template 1: Accessibility Audit**
```bash
echo "You are auditing CLAUDE-CODE.md for accessibility.

Answer these questions:
1. Where does the Quick Start section appear? (line number)
2. Can you find the most important command in 15 seconds? (yes/no + why)
3. What information is repeated unnecessarily? (quote sections)
4. Rate accessibility: 1-10

Max 300 words, be specific with line numbers." | \
  claude -p --tools default --permission-mode dontAsk 2>&1 > interview-accessibility.md
```

**Template 2: Completeness Check**
```bash
echo "You are checking CODEX.md for completeness.

Identify what's missing:
1. Prerequisites (installation, auth, dependencies)
2. Error handling (retry logic, timeouts, exit codes)
3. Examples (are they copy-paste ready?)
4. Rate completeness: 1-10

Max 300 words, cite line numbers." | \
  claude -p --tools default --permission-mode dontAsk 2>&1 > interview-completeness.md
```

**Template 3: Ambiguity Detection**
```bash
echo "You are identifying ambiguous documentation in GEMINI.md.

Find these issues:
1. Sections where the recommended action is unclear
2. Conflicting instructions (if any)
3. Jargon or undefined terms
4. Rate clarity: 1-10

Max 300 words, quote ambiguous phrases." | \
  claude -p --tools default --permission-mode dontAsk 2>&1 > interview-clarity.md
```

The key flags:
- `-p` (proactive mode): Let the agent use tools without asking
- `--tools default`: Give access to standard toolset (Read, Grep, etc.)
- `--permission-mode dontAsk`: No interactive prompts, fully automated
- `2>&1`: Capture both stdout and stderr

For parallel execution, we used background jobs:

```bash
# Run 3 interviews in parallel
(echo "Interview 1 prompt" | claude -p --tools default \
  --permission-mode dontAsk 2>&1 > interview-1.md) &

(echo "Interview 2 prompt" | claude -p --tools default \
  --permission-mode dontAsk 2>&1 > interview-2.md) &

(echo "Interview 3 prompt" | claude -p --tools default \
  --permission-mode dontAsk 2>&1 > interview-3.md) &

wait
echo "All interviews complete"
```

The `wait` command is critical - it ensures all background processes finish before proceeding to the next phase.

---

## Validation: Did It Actually Work?

### The Proof: Version 1.0.8 Testing

After implementation, we had a problem: how do we know the refactored documentation is actually better? We couldn't 
grade our own work. So we brought in external reviewers.

Except our external reviewers were AI agents.

We spawned 3 brand new agents with zero context. No memory of the interviews. No knowledge of what changed. Just: 
"Here's the documentation. Evaluate it."

The first validator came back with an 8.5/10. I exhaled. The second: 9.0/10. I started to relax. The third validator's 
report opened with: "This is exactly what I needed. Why didn't it look like this before?"

That question hit hard. Because I'd written the original docs. I'd thought they were good. I'd been wrong.

### Before/After Scores

| Document | v1.0.7 Score | v1.0.8 Score | Improvement |
|----------|--------------|--------------|-------------|
| CLAUDE-CODE.md | 8.0/10 | 8.5/10 | +6% |
| CODEX.md | 7.0/10 | 9.0/10 | +29% |
| MULTI-AGENT.md | 8.0/10 | 9.0/10 | +13% |
| **Average** | **7.67/10** | **8.83/10** | **+15%** |

The biggest improvement was CODEX.md - from 7.0 to 9.0. That makes sense: it had the most severe issues (3 
"recommended" commands, buried essentials, missing auth setup). The fixes were dramatic.

CLAUDE-CODE.md saw a smaller gain because it was already the cleanest of the three. But even there, moving the Quick 
Start section to the top and adding error handling examples pushed it from "good" to "very good."

### Validator Quotes

From VALIDATION-REPORT-v1.0.8.md:

> "Quick Start sections score 9-10/10 for accessibility"

The validators loved the new structure. Quick Start at the top meant they could find and execute the most important 
command in 15 seconds instead of scrolling through 90 lines of setup.

> "'THE ONE command' messaging is clear and effective" (10/10)

CODEX.md went from 3 ambiguous "recommended" options to one crystal-clear primary command with explicit guidance on 
when to deviate. No more decision paralysis.

> "Diagnostic table format is perfect" (9/10)

The MCP troubleshooting table gave validators a quick reference for debugging. Symptom → Diagnosis → Fix. Exactly
what they needed.

> "Production-ready guidance with measurable metrics" (9/10)

Adding error handling patterns with concrete examples (retry logic, exit codes, timeouts) transformed the docs from 
"here's what you can do" to "here's how to do it reliably."

### The Numbers

Let's look at the concrete efficiency metrics:

**Documentation efficiency:**
- Total lines: 2,648 → 1,618 (-39%)
- Duplication: 795 lines repeated → 0 lines repeated
- Distance to Quick Start: Line 90+ → Line 10-15 (80% closer)
- Error handling patterns: 0 → 15+ examples added
- Cost guidance: None → Comprehensive (Part 11 added)

**Customer satisfaction:**
- Critical issues resolved: 5 out of 5 top pain points (100%)
- Quality improvement: 7.67/10 → 8.83/10 (+15%)
- Production ready: ✅ All 3 validators approved for production use

**Time savings:**
- Time to find recommended command: 60-90 seconds → 10-15 seconds (5x faster)
- Time to understand error handling: ∞ (didn't exist) → 2-3 minutes
- Time to set up authentication: Failed often → Documented with Prerequisites section

### The Surprise

Here's what I didn't expect: the validators gave us higher scores (8.83/10) than the interviews did (7.67/10). Why?

The interviewers were looking at broken documentation with a critical eye. The validators were looking at fixed 
documentation with no prior context. They didn't know it had been worse. They just saw working, clear documentation and 
rated it highly.

This taught us something about user research: users who experience the pain give you better feedback than users who 
only see the solution. The interview phase was more valuable than the validation phase, even though validation gave us 
better scores.

---

## What I Learned

### Interview Your Users (Even If They're AIs)

I spent two full versions guessing what was wrong. Version 1.0.6? Not idea. Version 1.0.7? Still not good enough. 
One round of structured interviews revealed what users actually needed better than months of my assumptions.

AI agents are surprisingly good at articulating what makes documentation effective. They can't be polite out of social 
obligation --- if it's confusing, they'll tell you.

The practical takeaway: don't assume, ask. Spawn 5-10 agents with structured questions, collect ratings, prioritize by 
frequency. That's it.

### "Recommended" Is Not Enough

CODEX.md had three commands marked "RECOMMENDED" with no clear priority. As one validator put it: "Ambiguity about 
which command to use." I thought I was being helpful by showing options. I was actually creating decision paralysis.

Having three recommended commands equals having none. The fix: mark ONE primary command for 95% of use cases, then 
explain when to deviate. After this change, validators gave it a 10/10.

Your users shouldn't have to think about which tool to reach for.

### Duplication Has Hidden Costs

Twenty percent token overhead seems small until you multiply by every agent reading the docs, every spawned sub-agent, 
every validation test, and every future update requiring 3x maintenance work.

We removed 795 lines of duplication, saving 8,000 tokens per agent spawn. The ROI calculation: 4 hours to remove 
duplication, 2x time saved per future update, break-even after 2-3 updates.

Small percentages compound fast.

### Error Handling Is Not Optional

Zero interviews complained about lack of advanced features. Four out of seven complained about missing error handling.

Users need to know:
- What to do when it fails (retry logic)
- How long to wait (timeouts)
- How to interpret errors (exit codes)
- When to give up (max retries)

We added 15+ error handling patterns based on this feedback. The lesson: error states are not edge cases, they're the 
primary use case for production systems.

### Multi-Agent Orchestration Works

Sixteen agents spawned across four phases - analysis, interviews, implementation, validation. What made it work:
- Clear task boundaries
- Independent work with no coordination needed within phases
- Structured outputs in markdown
- A reduce phase for synthesis

What didn't work:
- Rate limits hit 2 of 9 interviews
- Nested execution failed in practice

The takeaway: plan for API constraints from the start, and test your assumptions about what's actually possible before 
committing to a strategy.

### Quantify Everything

Without numbers, we would have "made it better" instead of 39% reduction, "users liked it" instead of 8.83/10 rating, 
and "faster to use" instead of 5x improvement.

Metrics we tracked:
- Lines of code
- Duplication percentage
- Quality ratings
- Time to key information
- Issue resolution rate

Quantification turns vague improvements into compelling evidence. It also forces you to define what success looks like 
before you start.

---

## What We Shipped

The refactor produced two types of deliverables: production files (what users actually read) and research artifacts 
(how we got there).

**Production files (v1.0.8):**
- CLAUDE-CODE.md: 553 → 285 lines (-48%)
- CODEX.md: 756 → 312 lines (-59%)
- GEMINI.md: 757 → 327 lines (-57%)
- MULTI-AGENT.md: 582 → 694 lines (+19%)
- RLM.md (updated for consistency)

The numbers tell the story: three CLI docs lost more than half their length, while MULTI-AGENT.md grew slightly as the 
new single source of truth for shared patterns. Net result: 1,030 fewer lines to maintain, read, and pay tokens for.

**Research artifacts (67.5 KB total):**
- ACTION-PLAN-v1.0.8.md (8.4 KB) - Implementation roadmap
- FINAL-REPORT.md (12.1 KB) - Phase 1 summary
- INTERVIEW-RESULTS.md (15.2 KB) - Customer feedback compilation
- VALIDATION-REPORT-v1.0.8.md (8.7 KB) - Quality verification from fresh agents
- RELEASE-NOTES-v1.0.8.md (9.2 KB) - Complete changelog with migration notes
- REFACTOR-PLAN.md (6.3 KB) - Strategic analysis and approach
- REFACTOR-SUMMARY.md (4.1 KB) - Before/after comparison with metrics
- STATUS.md (3.5 KB) - Project status tracking

These artifacts became their own form of documentation - showing not just what changed, but why, how, and whether it 
worked. Anyone can follow this pattern for their own documentation refactoring.

All production files and research artifacts are available at [jonnyzzz.com](https://jonnyzzz.com/)

---

## Let's Connect

Share your results. Try this with your team's documentation - I want to see your before/after metrics. Tag me on
[LinkedIn at @jonnyzzz](https://www.linkedin.com/in/jonnyzzz/) with your quality scores. Bonus points if your AI agents
are as brutally honest as mine were.

Find a bug in the refactored docs? Submit PRs if you improve the patterns, let me know!

And if you're working on multi-agent orchestration or have questions about the RLM methodology, reach out. This is just
the beginning. We documented multi-agent orchestration, then used multi-agent orchestration to improve the
documentation about multi-agent orchestration. Agents spawning agents to interview agents. The recursive loop closed.

Now go interview your AI customers. They're waiting to tell you the truth.

---

## What's Next

The documentation is now production-ready. Quick Start sections appear in the first 15 lines. Error handling patterns
cover retry logic, timeouts, and exit codes. Authentication prerequisites are explicit. Duplication is eliminated. The
most common command is clearly marked as THE ONE command you need.

But the research artifacts themselves became something more valuable: meta-documentation about improving documentation
through multi-agent orchestration. They show the complete workflow from analysis to interviews to validation to
deployment.

The validation agents identified minor polish opportunities: reducing redundancy between Quick Start and Core Commands
sections, adding cost benchmark examples, making version requirements more specific. These are low-priority
improvements, not blockers, but they're documented and ready for v1.0.9.

I'm already thinking about the next iteration. Can we use this pattern for code refactoring? For test generation? For
architecture decisions? The interviews proved AI agents can articulate quality issues. The parallel implementation
proved they can fix those issues. That's powerful.

Next quarter, we're applying this to actual codebase refactoring. The documentation was the proof of concept. The real
work is applying this to engineering workflows where the stakes are higher and the problems are messier. That's where
this gets interesting.