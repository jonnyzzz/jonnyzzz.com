# 130 Release-Roadmap Issues, 818 Agent Runs: A Mid-Iteration Reality Check

**Date:** April 28, 2026  
**Author:** Eugene Petrenko  
**Tags:** ai-agents, ai-coding, multi-agent, orchestration, mcp, mcp-steroid, run-agent

---

Every product team running toward a release has the same artifact: a roadmap. Not the whole
backlog — the **umbrella epic for the next release**, with a hundred-plus sub-issues hanging off
it. Most are stubs: a title, a description, maybe some comments. No implementation plan. No
code-level analysis. No effort estimate. No dependency map.

A senior engineer researching one such issue typically spends 2–4 hours: reading the codebase,
understanding the architecture, scoping the change, writing it up as an actionable spec. For a
release roadmap of 130+ issues against a multi-million-line codebase, that's weeks of analyst
work before anyone writes a single line of code.

We ran an AI agent swarm instead — **three different agent CLIs, Claude, Codex, and Gemini**,
orchestrated together. Four calendar days. 818 agent runs. ~$576 total cost. Every roadmap issue
researched. Then, **while the release was still in flight**, we ran a second pass to check the
research against what the team was actually doing — explicitly *not* a "did it ship" scorecard,
because nothing was expected to be done yet. Here's how it works, what it produced, and the
honest verdict.

## It's a release roadmap, and there is a process

This was not "point a swarm at a backlog and see what happens." It was a release roadmap, and the
swarm followed a defined process, orchestrated by a root agent that does as little work as
possible and delegates everything:

1. **Collect.** Pull every unresolved sub-issue of the release umbrella epic from the issue
   tracker (through a small tracker CLI we built). Pick the product-requirements (PRD-prefixed)
   issues and the engineering issues, and reconstruct the **tree of linked sub-issues** for each root — the
   dependency graph matters as much as the issues themselves.
2. **Research.** Run each issue through the multi-round pipeline below.
3. **Review by quorum.** When a root issue is done, or whenever a decision is unclear, spin up
   **three review agents** and take the quorum verdict — not one model's opinion.
4. **Loop.** Keep going in a `/loop` until the roadmap is covered, applying the same principle
   recursively: the orchestrator delegates, the sub-agents do the work.

The whole thing runs on [run-agent.sh][run-agent] and the [RLM methodology][rlm-post] — one task
per agent, fresh context, markdown files carrying state between them.

## The Pipeline: R1 → R2 → R3

Each issue goes through three rounds of agent work. Two issues run in parallel at all times, with
the shell orchestration managing dispatch, detecting completion, skipping already-researched
issues, and retrying agents that time out.

**Round 1 (Claude)** reads the issue text, explores the codebase using [MCP Steroid][mcp-steroid],
and produces a first-draft research document: problem framing, relevant source files with class
and method references, and 2–3 solution options. Each option includes a complexity rating
(Low / Med / High), effort estimate (S / M / L / XL), key changes, test strategy, and a trade-offs
table.

**Round 2 (Codex)** validates every file reference from Round 1 against the actual codebase. It
finds exact line numbers, checks git history for recent changes to the relevant files, and flags
edge cases Round 1 missed. Every file reference gets a validation status: confirmed, renamed, or
not found. This is the mechanical correctness pass.

**Round 3 (Claude)** synthesises Round 1 + Round 2, resolves conflicts, and writes the final
recommendation: a concrete implementation plan with validated code references, a test strategy,
and follow-up work.

Claude for R1/R3 and Codex for R2 reflects what each model does well in practice. R2 is largely
mechanical — check that this file exists, find this class, confirm this method — and Codex handles
that efficiently. R1 and R3 require reasoning across options and writing a coherent
recommendation, where Claude produces better outputs. Gemini was in the swarm too, mostly in the
review quorum (more on its small share below).

## The Tools

Three things make this pipeline work at scale.

**[run-agent.sh][run-agent-site]** is the orchestration script that launches Claude, Codex, and
Gemini in isolated sub-processes. Each run gets its own
timestamped directory: exact prompt, full stdout/stderr capture, PID tracking, exit codes. Full
traceability for every agent execution. The shell orchestration loops over TASK files, detects
completion by checking output files, skips already-researched issues, and retries timeouts. See
the [full description here][run-agent-post].

**[MCP Steroid][mcp-steroid-site]** gives agents programmatic access
to the full codebase: PSI navigation, class resolution, call graph tracing, symbol search. Without
it, agents produce vague references like "look in the parser module" or "check the rendering
pipeline". With it, they produce specific class names, method signatures, and
line ranges — navigating the actual PSI tree and resolving inheritance chains. This is the
difference between a summary and a useful research document.

**TASK\* files** are structured task definitions written once and consumed by many agents (they
carry no extension — the orchestration matches `TASK`, `TASK-2`, and friends by name). The shell
script loops over them and dispatches agent runs accordingly. The format is simple and consistent
enough that agents parse it without extra tooling. Here are the actual task files that drove the
run (generalized — internal identifiers removed):

<details>
<summary><strong>TASK</strong> — collect the roadmap and orchestrate</summary>

```text
Your main goal is to collect all the relevant issues from the release-roadmap umbrella epic
in our issue tracker (query: all unresolved sub-tasks of the release epic).

Use our small issue-tracker CLI to read the tracker. If it lacks a feature or fails, start
run-agent.sh with a task to fix it. Equip that agent with THE_PROMPT_v5.md from
https://run-agent.sh to research, fix, review, deploy, and build the fix to the CLI, so you
can move on. Repeat that process as many times as you need.

Pick all tasks with the PRD* prefix and the engineering tasks for the product without the
prefix. For each task create a <task-id>.md document with discussion. Each such task has a
tree of linked tasks, which you need to include in the document. I want the graph of linked
sub-tasks for each root task.

Do that work in parallel using https://jonnyzzz.com/RLM.md. Our main goal is descriptive
write-ups for all selected tasks, and the related/linked issue tree.

Once a selected root issue is done, start 3 agents with run-agent.sh to review the work and
do the fixes.

Repeat that work in a /loop until the work is complete. You are the root agent; your main
goal is to orchestrate the research, do as little actual work as possible, and delegate
everything to run-agent.sh, as suggested in RLM.md and THE_PROMPT_v5.md. Apply it recursively.

When not clear, start 3x run-agents and make the quorum decisions.
```
</details>

<details>
<summary><strong>TASK-2</strong> — the research group of five</summary>

```text
Now create a research group of 5 agents running on the target codebase, each via
run-agent.sh. Our goal is to research each task as deeply as possible and provide 3 potential
ways of solving it. Use MCP Steroid to work on the assignment. Since there are far too many
tasks, prepare all the prompts in the prompts/ folder and a run script that calls all agents
on all tasks. For each task, 3 runs: claude -> codex -> claude. Each run includes the same
run-agent.sh and THE_PROMPT_v5.md, and refers to MCP Steroid's AGENTS.md as the usage guide.
Write all the outcomes to the issue-id.md file respectively. Make each agent use run-agent.sh
to research different parts of the monorepo. Your goal is to delegate and manage the process;
set up a /loop so we keep running and don't stop. Work one issue at a time. For issues with
linked issues, prefer the leaf issues first; create a dedicated file like
issue-id-leaf-another-issue-id.md and place details there. Include a high-level overview in
the initial issue.
```
</details>

<details>
<summary><strong>TASK-3</strong> — close the gap on the stub issues</summary>

```text
## Goal
Research all remaining .md files in this directory that have no proposed solutions yet
(53 standalone stubs with only tracker metadata, plus 2 leaf files missing solutions).

For each issue:
1. Check tracker status via our issue-tracker CLI — if already resolved/closed, append
   "Status: Resolved" and skip deep research.
2. Check for sufficient information — if the description is primarily marketing/strategy
   language with no concrete technical requirements (no user-facing behaviour, no API
   contract, no acceptance criteria), append "Status: Insufficient information — PRD lacks
   technical detail" and list what is missing. Do NOT fabricate solutions for thin PRDs.
3. If still open and detailed enough, run the full R1 -> R2 -> R3 pipeline
   (claude -> codex -> claude) via run-agent.sh, writing solutions into the issue's .md file.

Each agent fetches the latest issue description from the tracker before researching. Apply
THE_PROMPT_v5.md from https://run-agent.sh and use MCP Steroid to research the monorepo. Work
2 issues in parallel. The process may already be running — check existing .md sizes before
launching agents (skip if a file already has solution sections).
```
</details>

<details>
<summary><strong>TASK-4</strong> — the mid-iteration snapshot</summary>

```text
Your goal now is to run a snapshot review of the investigation. Time has passed since the
original research, and the release is still in flight — so we should be able to see what has
moved, how the team approached features, and which approaches were selected, without expecting
anything to be finished.

For each suggested ticket, run a batch of run-agent.sh agents to review whether and how it was
addressed. Learn from each decision and compare it against the options we proposed.

Use RLM.md, run-agent.sh, and any other tools to assess all the tickets. For more context and
approaches, look at the other TASK*.md files in this folder; they contain the necessary
information and approaches you should re-use.
```
</details>

## The Numbers

Here's what the full run produced:

| Metric                                    | Value                          |
|-------------------------------------------|--------------------------------|
| Issues analyzed                           | 130+                           |
| Agent runs total                          | 818                            |
| Codex runs                                | 322 (~39%)                     |
| Claude runs                               | 318 (~39%)                     |
| Gemini runs                               | 12 (~1%)                       |
| Other / unattributed (orchestration, review, retries) | 166 (~20%)         |
| Total token consumption                   | ~155–200M tokens               |
| Total cost (API prices)                   | ~$576 (~$315 Codex, ~$259 Claude) |
| Cost per fully-researched issue           | ~$5 (~$576 / 120)              |
| Calendar days                             | 4 (overnight gaps)             |
| Issues with full 3-round research         | 120                            |
| Total output                              | 52,162 lines                   |
| Average output per issue                  | ~435 lines                     |
| Issues found already implemented          | 9                              |
| Issues flagged as directly implementable  | ~39%                           |

A few of those numbers deserve commentary.

**Three agents, very uneven shares.** Codex and Claude split the pipeline almost evenly. Gemini
landed at ~1% (12 runs) — not because of model quality, but because it kept tripping over filesystem
**sandbox path restrictions** in this setup and we fell back to the other two rather than fight
it mid-run. Worth knowing if you're planning a three-CLI swarm: the orchestration is easy; the
per-CLI sandbox and auth quirks are what actually cost you time.

**~$5 per issue.** ~$576 across 120 fully-researched issues — the cost of 2–4 hours of senior
engineer analysis, done in roughly 90 minutes of wall-clock time per issue (two pipelines in
parallel). At any reasonable engineer billing rate, the economics aren't close.

**9 issues already implemented.** During research, agents cross-referenced issue descriptions
against the current codebase and found nine cases where the requested functionality already
existed — implemented at some point without closing the ticket. Catching this early avoids days
of duplicated work.

**120 of 130+ got full 3-round research.** The initial four-day swarm covered 65 issues; a later
pass researched the 55 remaining stubs — 8h49m of continuous execution, two parallel workers, no
API failures — bringing the total to 120. (Peak concurrency
was only two workers, with a long overnight idle gap; there's easy throughput left on the table.)

## What the Output Looks Like

This is not summarization. It's the analyst work a senior engineer does before writing code. A
typical fully-researched issue document contains:

- A **problem framing** section: what the issue requests, what the codebase does instead, where the
  gap is
- **File:class:method references** with line numbers — confirmed by R2 against the actual repository
- A **git history note** on recent changes to those files — flagging active areas where merge risk
  is higher
- **Two or three solution options**, each with complexity, effort, key changes, test strategy, and a
  trade-offs table
- A **validation section** from Round 2: which references were confirmed, which were corrected,
  which edge cases were added
- A **final recommendation** from Round 3 with rationale, implementation sequence, and follow-up work

When the output is good, a team lead reads it in 15–20 minutes and makes a prioritization decision
with full context. The shift is real: from "I need half a day to understand this issue before I can
scope it" to "I need to review what the agent found and decide which option makes sense."

## A Mid-Iteration Snapshot, Not a Postmortem

Here is the part that's easy to get wrong. After the research, while the release was **still in
flight**, we ran a second pass against the same roadmap — same orchestration, same MCP Steroid,
same `run-agent.sh` — asking a different question. Not "what should we implement," but "what is the
team actually doing, and how does it compare to what we proposed?"

This is a **mid-iteration snapshot**, and the framing matters: at the time of the check, **nothing
was expected to be finished.** The release hadn't shipped. So this is not a scorecard of "did the
research come true." It's a directional read — a chance to see, on the issues where work *had*
started, whether the research pointed the right way.

The snapshot was map-reduce: one agent per issue (refetch status, scan git history for related
commits, compare proposal vs. current direction), then a thematic reduce across about eight
subsystem groupings, then a final reduce into a single lessons document. Same RLM principle — one
task per agent, fresh context, markdown carries state — with two reduce stages because the input
was too large for one synthesis pass.

| Snapshot outcome (138 items, incl. parent/leaf) | Share |
|--------------------------------------------------|-------|
| Work landed — matched the proposal                | 5%    |
| Work landed — diverged from the proposal          | 33%   |
| In progress                                       | 23%   |
| Still open — proposal still valid                 | 27%   |
| Abandoned / obsolete                              | 11%   |
| Insufficient PRD — never actionable               | 1%    |

Read against a finished release, "5% matched" would look brutal. Read as a mid-cycle snapshot, it's
the wrong number to fixate on — because of what "diverged" means for the other 33%. In most diverged
cases the agent identified the right root cause or dependency, but maintainers chose a different
implementation layer, scope, or product shape. The research was directionally right, even if the
patch landed elsewhere — in an adjacent caller, an integration layer, or a shared platform surface
rather than where it pointed.

That reframes what the pipeline is for. The output is **not** a patch location to apply as-is. It's
a structured comparison of options plus an identification of root cause and dependencies. The hit
rate is the wrong metric; the value is in the framing and the dependency map.

## What We Learned

### Some solutions aren't viable — even after three review rounds

This is the uncomfortable one. A non-trivial share of recommendations were simply **not good**, and
three rounds of review didn't save them. The agents over-technicalized product questions (treating
"should we keep this feature" as an engineering task), confidently prescribed a local patch where
the real decision was about ownership or release sequencing, overcomplicated easy tasks, and
oversimplified hard ones. Three passes of a confident model reviewing another confident model can
converge on a polished, plausible, **wrong** answer. More rounds did not fix wrong framing.

### Agents reject their own options — then keep them anyway

The clearest tell came from a reviewer's note. In one document, the agent had generated three
solution options and **explicitly marked the third "should not be implemented"** — and then left it in
the final write-up. The agent's own judgment said *no*, and the option still shipped into the
document, adding clutter a human had to read past. An output set that never drops the ideas its own
author rejected isn't a research report; it's a transcript. The fix is mechanical: prune options
the agent flags as non-viable before synthesis, instead of dutifully carrying every branch forward.

### We needed an *adaptive* number of iterations, not a fixed three

Three rounds was the wrong constant in both directions. For small, well-groomed issues with an
obvious code seam, R1 alone was enough — R2 and R3 just reworded it. For cross-module, cross-repo,
or product-gated issues, three rounds weren't nearly enough to converge, and a fixed cap let
unresolved disagreement get written up as a confident recommendation. The right design is an
**adaptive iteration count**: keep looping review-and-revise on a task until it *converges* — until
a fresh reviewer adds no new finding — and stop early when it already has. A product-gated task
should short-circuit to "ask the owner," not burn three deep-research passes on a moving foundation.

### MCP Steroid is the force multiplier

The gap between agent outputs with and without full codebase access is large. Without it, agents
default to generic descriptions: "update the parser", "check the rendering pipeline". With
[MCP Steroid][mcp-steroid-site], they navigate the actual PSI tree, resolve inheritance chains,
and trace call graphs to find where a change propagates. That's not a small specificity bump —
it's the difference between a useful document and
a vague one. One pattern to fix: agents default to one file per MCP call; a small script that reads
5–10 related files per call would cut round-trips and speed up R1 noticeably.

### The message bus was useful enough to graduate

Between rounds, findings flowed through a single append-only markdown file — `MESSAGE-BUS.md`. Each
agent wrote what it learned; later agents and the reducers read it back. It was the most reusable
artifact of the whole run, and it has since **graduated into the agent-orchestration framework we
use elsewhere** as a first-class, append-only, typed protocol — messages carry a type (`FACT`,
`DECISION`, `QUESTION`, `ANSWER`, `PROGRESS`, `ERROR`, `BLOCKER`, `COMPLETE`), an id, and a
back-reference, so a swarm can coordinate without a shared database. The honest caveat: because
parent and leaf tickets often referenced the same root problem, the bus filled with duplicates —
so any reducer has to **dedupe by the underlying issue** before drawing conclusions, or it
double-counts.

### Codex buffers all output

Codex streams its progress to stderr and writes nothing to its stdout file until the run
completes. A monitor that watches the stdout file size will conclude a running Codex agent is
stuck. It isn't — it's thinking. Check the process PID (or stderr), not the stdout file size. We
spent more time than we'd like to admit investigating "stalled" agents that were running normally.
It's already improved in the recent version of `run-agent.sh` where we run agents with a verbose mode,
NDJSON outout, and better monitoring of file sizes.

### Cost is not the constraint — human review is

At ~$5 per fully-researched issue, cost doesn't register for any team with a real roadmap. The constraint is human
review bandwidth: the pipeline produced ~435 lines per issue, 52,000+ lines total, all waiting for
judgment. Designing the output format for fast human review matters far more than shaving a dollar
off the per-issue cost.

## The Human Verdict, Honestly

A senior product lead reviewed the output and gave a blunt read, which I'll paraphrase because it's
the most useful thing in this whole post. Handing this research — with its implementation advice —
straight to junior, mid, or even early-senior engineers is **dangerous**, because the agents:

1. describe even complete nonsense very convincingly, instead of saying *"I don't have enough
   information, I give up"*;
2. charge ahead researching a technical solution without thinking about the product side;
3. overcomplicate easy things and oversimplify hard ones.

His conclusion: this kind of mass research is something you show a **product lead plus a tech
lead** for a fast review — people with enough context to validate or dismiss it quickly, and who,
frankly, would have gotten there without the research anyway. The genuine upside: for small,
well-groomed tasks where the product direction is settled, the output is exactly the spec an
implementation pipeline can run with.

He also flagged the small, human things the agents missed and the ones they nailed: handle
externally-reported issues more cautiously (have a human confirm before acting, and check whether
the product already does the requested thing); and **diagrams and flow charts are genuinely
helpful** — the kind a senior draws by hand to think, and the kind the agents should produce more
of.

The honest position: agent research is a tool for **senior judgment to operate on**, not a
substitute for it.

## What's Next

The changes the snapshot points to — none of which remove the senior human from the loop:

- **Product-state precheck** before deep research — assignee, fix version, recent human comments,
  decision state — so product-gated issues short-circuit instead of getting three rounds.
- **Adaptive iteration count** — loop review-and-revise until convergence, not a fixed three.
- **Prune agent-rejected options** before synthesis.
- **Mandatory alternate-layer enumeration** — at least one plausible alternate implementation
  surface per recommendation, with the rationale for the recommended one.
- **External-repo scanning** for build/CI/release issues, which often land in adjacent repos.
- **Dedupe by underlying issue** before any reduce.

The bulk-implementation idea survives the snapshot. For the subset of issues where the product
direction is settled, the paths still hold, and the change is self-contained, the same pipeline can
keep going — R4 implements from the R3 spec, R5 reviews and validates tests, R6 does a final
integration check — closing the loop from issue stub to pull request, without the over-confident
handoffs the first round would have produced.

---

The pipeline is built on tools I've written about before: [run-agent.sh][run-agent-site] for agent
execution, [MCP Steroid][mcp-steroid-site] for codebase access, and the [RLM methodology][rlm-post]
for keeping context manageable. What this experiment adds is evidence that they work together at
scale — not for a handful of issues, but for an entire release roadmap — and an honest account of
where the output needs a senior human in the loop.

**Questions about the pipeline or running research swarms at scale?**
Find me on [LinkedIn][linkedin] or [X][twitter].

[run-agent]: https://run-agent.sh
[run-agent-site]: https://run-agent.sh
[mcp-steroid]: https://mcp-steroid.jonnyzzz.com
[mcp-steroid-site]: https://mcp-steroid.jonnyzzz.com
[run-agent-post]: {% post_url blog/2026-02-06-run-agent-multi-agent-orchestration %}
[rlm-post]: {% post_url blog/2026-01-05-rlm-multi-agent-orchestration %}
[linkedin]: https://www.linkedin.com/in/jonnyzzz/
[twitter]: https://x.com/jonnyzzz