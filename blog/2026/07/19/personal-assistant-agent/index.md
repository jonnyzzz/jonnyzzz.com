# Personal Assistant without OpenClaw or Hermes: Just One Prompt

**Date:** July 19, 2026  
**Author:** Eugene Petrenko  
**Tags:** ai-agents, ai-coding, infrastructure, workflow, self-improvement, hermes-agent, openclaw

---

I wanted a personal assistant for quite some time. I can message from my phone. Something absolutely
simple and what I can understand and fine-tune to my needs. Not a chatbot — an assistant: 
"watch that Slack DM thread and ping me when they reply", "write down our AWS account conventions",
"build me a tool that inspects my iTerm2 tabs". Requests arrive on Slack and Telegram at random times,
some finish in a minute, some take forty, and we want the acknowledgment to land now and the result when
it is ready — without message two waiting behind message one.

The naive approach — one AI Agent in one chat loop that does everything itself — falls apart on exactly that
schedule. The Agent picks up a long task, its context fills with the work, the instructions dilute, and the
next message queues behind a forty-minute errand. Worse: when the session eventually compacts or restarts,
half-done work simply evaporates, and nobody tells you.

So the rule at the top of our operating contract is a role split, not a feature: **"You assist and manage —
you never do the work yourself."** The interactive session routes, tracks, follows up, and reports. Every
actual task runs in a fresh, disposable, headless sub-agent process. The whole thing was scaffolded,
smoke-tested, run through its first real tasks, hit its first production incident, and shipped its first
self-authored fix in a single afternoon — 2026-07-17, 13:29 to about 15:50. Now it's running on the second computer.

And here is the part I want to be upfront about, because the title promises it: the founding spec was **one
message pasted into an interactive [Claude Code][cc-headless] session**. Not a product install, not a config
wizard — a prompt. Lightly redacted, the worst typos cleaned, the rest left as I typed it the first time:

<details markdown="1">
<summary><strong>THE PROMPT</strong> — the message that started the whole system</summary>

```text
you are my personal assistant, your goal is to setup and prepare the /workflows for that.
Do the following steps to set this up:
  - create a repository under gh jonnyzzz jonnyzzz-personal, private one
  - configure a workflows to regularly monitor and handle all the requests via the Slack's me-only
    private channel, it will be our communication protocol
  - configure and setup telegram communication channel, create the scripts to poll for messages
    and store all messages on the disk and handle them, use uv python, once done, ask me
    for credentials, 
  - only accept messages from my user accounts
  - credentials are never committed to the repository, only stay locally.

So the flow is the following -- you poll and process these two input channels. For each
request -- you MUST start the new sub-agent process, use run-agent.sh for that -- once the
process is completed -- process and send followup to the channel from which you receive
the input.

You should create the self-improvement loop -- start every 3 hours new sub-agent which
3x quorum processes and analyzes everything what was done and self improves. Running agentic
loops is necessary -- your task to manage that flow.

Commit and push all the changes to your flows to this new gh repo, update the repo regularly
and re-read from it too.

I expect you to script the most of the tasks to simplify the processes, effectiveness, and
outcomes. Setup hooks in this repository for yourself to always remember your goals, you are
assisting, managing, and never doing.
```

</details>

Everything below — the wrapper scripts, the hooks, the state files, the quorum, the iTerm2 supervisor — grew
from these lines plus the follow-up conversation. Even this post draft did. The sub-agent mechanics trace back to the
[run-agent.sh][run-agent] approach the prompt names. I am not pretending this replaces OpenClaw or Hermes;
the point is narrower and, I think, more useful: *this class of assistant now costs one prompt and one agent
session*, and at that price you should build one before you adopt one.

> Discipline for an AI Agent should live in the architecture — process boundaries, files on disk, git — not in
> a paragraph of prompt the model is supposed to remember forty minutes into a session.

This post is the build log, and then a comparison — as fair as I can make it — against the two big names in
the personal-agent space right now: [OpenClaw][openclaw-gh] and [Hermes Agent][hermes-gh].


> The system started from **one only prompt** above and evolved to a really powerful and supportive buddy,
> that learns from what you do, and how it works. Below, is that it thinks of itself.

With this post I share how my AI Agents evolved into a personal assistant, given the right context,
and the best tools. This appers in-line with 
[my goals and program: Agentic AI Experience & Tools]({% post_url blog/2026-03-24-agentic-experience-and-tools %}).
Find
me on [LinkedIn][linkedin] or [Twitter][twitter], and if an assistant like this would fit your own workflow,
get in touch — I am happy to help you shape one.

---

## One Rule at the Top, Enforced Structurally

The orchestrator is an interactive [Claude Code][cc-headless] session with a `CLAUDE.md` contract that is
auto-loaded every session. Line 5 is the prime directive quoted above, and it is enforced three ways, because
hoping the model remembers is not a mechanism:

- **Process boundaries.** Every request becomes a fresh `claude -p` [headless run][cc-headless] via a wrapper
  script `run-agent.sh` — one request, one process, no shared context. The orchestrator is forbidden from editing even its
  own flow files (scripts, prompts, hooks, docs) inline; flow changes also go through a sub-agent.
- **Hooks.** Claude Code [hooks][cc-hooks] re-print the directive at every session start and inject a one-line
  reminder before *every single prompt*: "You assist and manage, never do." The session-start hook also
  appends live state pulled from the state files with [jq][jq] — active watches, agents still running — so a
  fresh session wakes up already knowing "agent X is in flight, watch Y is armed".
- **An inverted frame for workers.** The sub-agent prompt frame has to explicitly flip the rule: "you ARE the
  worker here, so do the task yourself — the never-do-inline rule applies to the orchestrator, not you."
  Sub-agents run in the same directory and [inherit the same `CLAUDE.md`][cc-memory]; without that line the
  never-do rule would recurse forever. The best line in the whole repo

There is exactly one carve-out, and it exists for an architectural reason we will get to: requests that are
purely channel communication — send or read a Slack or Telegram message on my behalf — are handled by the
orchestrator directly. Slack is reachable only from the orchestrator session, so there is no worker to
delegate a Slack send to, and Telegram sends are code-restricted to my own chat either way. Even the carve-out
leaves a trail: every direct reply is recorded through the state script, so the audit surface stays complete.

## Two Channels In, One Owner

Slack side: a private channel, reached through the session's Slack [MCP][mcp] tools, where only messages from my
user id count as requests; new-message detection is a plain timestamp watermark in a state file. 

Telegram side: a dedicated bot with a hard owner allowlist — enforced *inside the CLI code*, not in the prompt. The
poller surfaces only allowlisted senders as work; `send` refuses non-allowlisted chat ids outright; strangers
land in a log on stderr and are never replied to. Even bootstrapping is stranger-proof: with an empty
allowlist, the poller logs every unknown sender and warns on stderr, a `seen` command aggregates them into
candidate ids, the flow posts those ids to Slack for me to confirm, and only then does the allowlist get
filled — the bot never replies to an unconfirmed id, not even once.

The Telegram CLI is a single-file Python script with [PEP-723][pep723] inline metadata, run via
[uv][uv-scripts], talking to the Bot API with [httpx][httpx]. Its signature feature came from a direct
directive at 14:47 on day one: *polling CLIs must run-and-wait, exiting after a 15-second idle bucket.*

Any other chats: Just the same way as we implemented Slack and Telegram -- are one prompt away from
the availability. 

## Bucket Mode: Near-Realtime From a Blocking Poll

There is no daemon, no webhook, no queue broker anywhere in this system. The "runtime" is one interactive
session running a repeating inbox cycle. Slack ingress is the boring half — an MCP channel read against the
timestamp watermark, once per tick. The Telegram side is where the design lives: the event source is a
blocking CLI with carefully chosen exit semantics:

```text
poll --first-wait 240 --idle 15 --max-wait 280

wait up to 240s for the FIRST message       # nothing arrived: quiet exit 0, tick ends
on arrival, print it immediately            # unbuffered JSON line per message, as it lands
then switch to idle mode: exit after 15s    # a burst of messages becomes ONE bucket of work
never run past 280s total                   # hard cap, the poll can never block forever
```

Each underlying [`getUpdates`][tg-api] long-poll timeout is clamped to the remaining budget with a hard
~50-second cap, and a sub-second tail is slept out rather than re-polled — a deliberate courtesy, per the
comment in the CLI itself, instead of hammering the API with near-zero-timeout calls. The result: each loop
tick holds a roughly four-minute listen, so response latency is near-instant for the cost of one cheap
blocking call. All updates — authorized or not — are appended to a jsonl transcript before the offset
advances, so nothing is consumed invisibly.

I like this trade a lot. OpenClaw and Hermes both answer "how do messages get in" with a resident gateway
process. We answer it with a *budget*: latency comes from long-polling math, not infrastructure.

## One Request, One Process

Dispatch is a small shell wrapper around `claude -p`, [https://run-agent.sh](https://run-agent.sh).
For every request it creates a run directory with three
artifacts — `prompt.md`, `result.json`, `stderr.log` — appends a start record `{id, channel, started, dir,
pid, status:"running"}` to an append-only `agents.jsonl`, runs the sub-agent with JSON output, then appends a
done record with the exit code. Every agent lifecycle event is an append-only record; every run leaves a full
paper trail. A discipline rule sits on top: never hand-append JSON to state files — always go through the
state script.

The hardening matters more than the happy path: the wrapper traps EXIT, TERM, and INT, and writes an
`exit:143, "aborted: dispatcher killed"` done-record if it dies before the normal one is written — guarded by
a flag so it never double-writes. An id can never stick in "running" forever just because the wrapper was
killed — the trap covers every catchable death, and the reaper we will meet below closes the one it cannot, a
straight `kill -9`. That trap was not designed up front. It was shipped in response to an incident.

## The First Incident, and the Fix, Two Hours Later

At 13:45 on day one — four minutes after the first real task landed — the first concurrent dispatch of two
sub-agents went wrong. The dispatcher combined a shell `&` with the tool-level background dispatch it should
have used, and one wrapper died mid-run. The work was recovered and the lessons were logged.

At 15:50 the same day, the system's first self-improvement cycle shipped the systemic fix in one commit: the
pid tracking and abort trap above, a state script for scripted bookkeeping, a deliver-first inbox flow with an
explicit failure path and a reaper, and codified delegation rules. The rule that came out of it landed as
literally step 7 of the day-one inbox prompt: dispatch with the tool's background mode — *"NEVER a shell
`&`"*. (It sits at step 9 today — the loop has since quorum-grown two more steps above it.)

Incident → three-agent post-mortem → quorum-approved fix → committed process change, all machine-executed on
day one. Fix shipped same afternoon as the incident. That arc, more than any feature, is why I trust the
design.

## Deliver First, Fail Loudly, Reap the Dead

The inbox cycle runs every ~5 minutes and its ordering is opinionated:

```text
1. pull the repo                # re-read your own instructions before acting
2. deliver finished work FIRST  # before polling for anything new
   success: read result.json, reply short, outcome first
   failure: send a notice + the tail of stderr.log — never silence
3. reap: entries "running" >30 min AND whose dispatcher pid fails kill -0
   → close as exit:143, note "reaped: dispatcher/agent dead", report each on its channel
4. re-check watches             # e.g. "tell me when that thread gets a reply"; expire with a notice after 24h
5. poll Telegram (bucket), 
6. read Slack
7. dispatch each new request    # ack "On it — task <id>", background, never shell &
8. catch late finishers, 
9. push flow changes
10. nothing new → end quietly, no channel noise
```

Step 1 means a changed instruction file takes effect *mid-cycle*. Step 2 means a finished task is reported
before new work is taken. The failure path means a crashed sub-agent produces a notice with its stderr tail
instead of vanishing. The reaper uses [`kill -0`][kill] as a liveness check so a genuinely long-running agent
is left alone, while a dead dispatcher's orphaned record gets closed and reported. Between the abort trap, the
failure notice, and the reaper, there is no path where a dispatched request just disappears

The listing above is already a historical document, by the way: by the end of day two the loop had
quorum-grown to twelve steps — an early re-arm and a self-improvement catch-up — plus a standing rule that
the cycle must never end in a terminal state. The ten steps you see are day one's version; the upgrades came
from the process described next.

One pre-dispatch window remains, and it belongs on the record: the Telegram offset advances at poll time, so a
message consumed moments before a session death lives only in the jsonl transcript, which nothing re-reads as
work. Slack does not share the hole — its watermark is written back only after processing. A future quorum
cycle owes us a fix.

## A Quorum That Rewrites Its Own Process

"Self-improving agent" is usually a euphemism for "the model edits its own prompt, and we hope". Ours is a
pipeline with an evidence phase, independence, a threshold, and verification.

Every 3 hours: gather read-only evidence — `git log --stat` since the last cycle, both state jsonl files, the
newest agent run directories, the previous cycle report. Then spawn **three independent analysis sub-agents in
parallel over the same evidence** — in-session Agent-tool tasks this time, not headless dispatches — each with
a distinct lens:

- **reliability** — what failed, hung, was retried, or silently dropped;
- **effectiveness** — routing speed, reply usefulness, loop closure;
- **simplicity** — what to script, simplify, or delete; where the orchestrator did work inline.

Each returns proposals as `{file, change, rationale}`. The decision rule, as first shipped: accept only if at
least 2 of 3 lenses independently support the same file and intent. Rejected proposals are written to a
rejection log with reasons — the disagreement is an artifact, not a discard. Accepted changes are applied by
exactly one applier sub-agent, dispatched through the same headless wrapper as any other task (the
orchestrator never edits flows
inline, even here), then mechanically verified — [`bash -n`][bash] on every changed shell script, executables
stay executable, the Telegram CLI still authenticates, the settings file still parses with [jq][jq] — then
pushed, with a cycle report to Slack.

Cycle #1's real numbers: 18 proposals, 4 bundles accepted, 8 rejected and logged, one commit. Yes, 4 + 8 ≠ 18 —
an accepted "bundle" groups several overlapping proposals into one coherent change, which is exactly what a
2-of-3 agreement on file and intent produces. That commit was the incident fix.

Then **the quorum rewrote its own constitution**. The strict overlap rule — accept only what two lenses
independently author — turned out to be a filter so fine it soon produced a cycle with zero accepts, so at
22:14 on day one a cycle replaced it, through its own machinery: three analysts still propose, the proposals
are deduped, and three *independent voters* now approve or reject each one, accept at 2-of-3 votes. One cycle
later the scheduler got the same treatment: after one overnight run analyzed a window where nothing had
happened, the gate became "3 hours elapsed AND new activity since the last cycle", empty windows skipped and
logged. Seven cycles ran in the first two days, and the process that runs them is itself the thing they keep
amending

## The Repo Is the Source of Truth

The closing rule of the contract: *"If the flows in this repo and your memory disagree, the repo wins —
re-read it."* Behavior is data on disk, not weights-in-context. Prompts are re-read every cycle and the repo
is re-pulled before acting, so a `git push` is a live behavior deployment — including from another machine.
The sync script is deliberately forgiving ([`pull --rebase --autostash`][git-pull], continue offline, retry
push next cycle) because the loop must never wedge on git.

My favorite small artifact of this discipline: our AWS notes document that a local config file literally
spells a profile name `Sanbox` — typo and all — instruct agents to use the typo as-is, mark fixing it as a
pending *manual* action for me, and forbid agents from editing that file themselves. Reality documented over
reality "fixed" out from under the human.

Secrets follow the same locality principle. Credentials live only in a gitignored directory with tight file
modes; state and logs are gitignored too — only flow logic is committed. A pre-commit hook blocks staged
secrets three ways: anything under the secrets directory (only its `.example` templates and README are
exempt), any `.env` file, and any *added diff line* matching credential shapes.
A third layer rides in every sub-agent frame — a standing "never commit or print tokens"
line — because defense in depth assumes any single layer will eventually miss.

The sharpest boundary is capability asymmetry: the Slack connection exists *only* in the orchestrator session
via MCP — there is deliberately no Slack CLI or token in the repo, so a compromised or confused sub-agent
cannot reach Slack tokens at all. Telegram is softer, and I want to be precise about how much softer: the CLI's send
path is code-restricted to my own chat, so *through our tooling* the worst case is a message to me. But the
raw bot token does live in the local secrets directory, sub-agents are permitted to read credentials, and a
rogue or confused one could call the Bot API directly, bypassing the CLI entirely. The allowlist is a
guarantee about the tool, not a bound on the token. That asymmetry is also why channel sends are the one thing
the orchestrator does directly.

## The Assistant That Babysits Other AI Agents

"Build me a tool that inspects my iTerm2 tabs" was on the wish list in the opening paragraph, and it grew into my
favorite capability of the whole system. This machine usually runs eight to eleven [iTerm2][iterm2] consoles with
other AI Agents inside — [Claude Code][cc-headless] sessions, [Codex CLI][codex-cli] sessions — each grinding
through its own long task. Somebody has to notice when one of them stalls on an approval prompt or runs its
context to 100%. Now the assistant does.

The read path is one [AppleScript][applescript] pass, strictly read-only. The `status` subcommand walks every
window, tab, and session without activating or focusing anything, and prints for each: a header (session id,
name, tty, window/tab position, plus iTerm2's `processing` / `at-prompt` flags when exposed), the last twelve
non-blank visible lines, and a first-pass status guess — WORKING, WAITING, IDLE/DONE, or BLOCKED, with a
`[100% context]` flag when that shows on screen. The classifier is grep over screen tails, nothing smarter:
spinner glyphs mean WORKING, "waiting for" means WAITING, a shell prompt means IDLE/DONE, a `[y/n]` or a
"Goal blocked" means BLOCKED. BLOCKED is checked first because — the comment in the script says it plainly — a
missed approval prompt is the costliest miss. The sub-agent running the survey is briefed to treat the guesses
as first-pass only, re-read each tail, and report most-actionable-first. "What are my terminals doing" is now a
routine Telegram request — the reply ledger shows three fleet summaries inside one day.

Watching is safe; writing into another agent's console is not. So the write path got the opposite treatment: it
exists, and it is deliberately hard to use. The hard rule in `CLAUDE.md` says console writes go ONLY through the
guarded `send` subcommand, never raw osascript, and `send` refuses in layers:

- it resolves the target by session id AND demands the expected tty on the command line — if the session's
  actual tty differs, it refuses: writing into the wrong console is the nightmare scenario;
- it demands `--expect`, a literal substring that must be on the target screen *right now* — a [TOCTOU][toctou]
  guard: if the prompt scrolled away or changed between survey and send, it refuses;
- keystrokes come from a safe vocabulary — `y`, `n`, `enter`, a single digit; arbitrary text is an explicit
  `--raw` opt-in;
- every write lands in an audit log with the exact bytes sent and content hashes of the screen before and after.

On top of the tool, the approval flow adds policy: approve ONCE with the least-privilege key, never "always
allow" or "don't ask again", one approval per request, abort untouched if the screen shows anything but the
expected prompt

The base inspector was one of day one's first two dispatches; the survey and the guarded writer came out of
quorum cycle #4 on day two — the guardrails themselves were proposed, 2-of-3 voted, and shipped by the same
three-lens process as every other flow change.

And on day two the thing earned its keep. The afternoon survey flagged window 3: a Codex agent double-stuck,
asking approval to kill its own hung Gradle test worker and showing "Goal blocked" right above. The status
report *flagged* it for me instead of acting on its own; the unstuck ran only after I said go. The audit log
then records three writes in sixty-six seconds: a `y` against the expected text "confirmed stuck Gradle test
worker" — approve the kill, once; `/goal resume` plus a newline against "Goal blocked"; and the discovery of
the day — in the Codex TUI, Enter does not submit while the agent is mid-turn. The typed command just sat there
on screen. So the third audited keystroke is a single Tab, which is how Codex queues input for when the current
turn ends. Nobody documents these things. That Tab went in through the `--raw` escape hatch, under audit — and
by the next quorum cycle it had graduated to a first-class key in the safe vocabulary, next to a new "Agent TUI
quirks" note in the repo recording which console queues on Tab and which submits on Enter. Your assistant
learns these things one guarded keystroke at a time, and then it writes them down.

> An AI Agent supervising other AI Agents is only as trustworthy as the narrowest write path you give it.

Let me be precise about what this is: best-effort supervision of peer agents, not a control plane. The consoles
expose no API — the assistant reads the same screen text I would, and the classifications are regex guesses a
sub-agent double-checks before reporting. What makes me comfortable anyway is the thesis this post keeps
repeating: every intervention is id-and-tty-verified, precondition-checked, least-privilege, and audited. The
discipline lives in the architecture, not in the model's good intentions.

The last quorum cycle of day two made this a standing service: the assistant now keeps a notify-only watch
on the other consoles and pings me when one of them stalls — paired with a hard rule in the contract that
automated watches never write to a console. Helping the agents in the other terminals is the job; pressing
their keys stays mine.

## The Field: OpenClaw and Hermes

Now the comparison — because the two projects everyone will name in reply occupy the same niche with nearly
opposite choices.

First, identities, honestly hedged. **OpenClaw** here means the self-hosted personal-agent runtime at
[github.com/openclaw/openclaw][openclaw-gh] — released November 2025 as Warelay and renamed through
CLAWDIS/Clawdbot/Moltbot to OpenClaw, [per Wikipedia][openclaw-wiki]. [The GitHub API][gh-api-oc] gave it
383,244 stars on 2026-07-17, while Wikipedia's March 2026 snapshot said ~247k — treat any star count as a
photo of a moving train. Not to be confused with [pjasicek/OpenClaw][openclaw-game], a C++ remake of the 1997
game Captain Claw, no relevance to AI Agents. **Hermes** here means Nous Research's
[Hermes Agent][hermes-gh] (216,301 stars by the [same API call][gh-api-hermes] the same day) — not the
[Hermes LLM weight series][hermes-llm] from the same lab, and not [Meta's Hermes JS engine][hermes-js].
[Turing Post reported][turing] Hermes overtaking OpenClaw on OpenRouter daily tokens in June 2026 — 224B
against 186B per day — though I have not verified OpenRouter's underlying numbers independently. Both projects
move fast — several defaults below are as-of-mid-July-2026 and worth re-checking against their docs.

| Axis             | jonnyzzz-personal          | OpenClaw                        | Hermes Agent                   |
|------------------|----------------------------|---------------------------------|--------------------------------|
| Runtime          | interactive session + loop | Gateway daemon                  | gateway service                |
| Ingress          | MCP read + bucket poll     | persistent channel sockets      | push + long-poll adapters      |
| Channels         | 2, one owner               | 20+                             | 20+                            |
| Session model    | fresh process per request  | DMs share main session          | persistent per session key     |
| Memory           | git repo + jsonl           | Markdown + daily notes          | MEMORY.md + FTS5 SQLite        |
| Self-improvement | 3-lens quorum, 3-hourly    | Skill Workshop, human-gated     | per-turn background review     |
| Isolation        | capability asymmetry       | sandbox off by default          | six exec backends              |
| Model coupling   | Claude Code only           | [model-agnostic][openclaw-docs] | [model-agnostic][hermes-docs]  |
| Behavior deploy  | `git push`                 | workspace + skill file edits    | file writes + skills           |

**Ingress: a daemon versus a budget.** OpenClaw's [Gateway][openclaw-docs] is "the single source of truth for
sessions, routing, and channel connections" — one always-on process holding persistent connections to
[twenty-plus platforms][openclaw-gh], exposing a [WebSocket API on a localhost port][openclaw-arch]. Hermes
runs the same shape — one resident [gateway][hermes-msg] process with [20+ adapters][hermes-msg]. Neither is
quite push end to end, to be fair: in both projects the Telegram channel [defaults][openclaw-tg]
[to long polling][hermes-tg] with webhooks as the opt-in mode. But the shape holds — a resident daemon owns
the connections. That buys instant delivery and breadth we simply do not have. It also buys daemon problems: OpenClaw's
docs note events are [not replayed after a gap][openclaw-arch] and pending sub-agent announcements are
[lost on Gateway restart][openclaw-sub]. Our blocking bucket poll delivers a burst as one unit of work,
resumes after any restart (the watermark and offset are files), and costs no infrastructure while idle. Two
channels are enough for one owner.

**Sessions and trust granularity.** This is the deepest philosophical split. In OpenClaw, by default all DMs
collapse into the agent's *main session* — the docs themselves say ["true isolation requires one agent per
person"][openclaw-multi] — and [runs are serialized per session lane][openclaw-loop], which as I read it means
a shared session can head-of-line block. Hermes resolves a session key and [carries persistent conversation
history][hermes-arch] across turns — genuine continuity, which our stateless workers lack. We chose the
opposite: one request, one process, no carried context, and the orchestrator's jsonl files as the only shared
truth. Continuity lives in files we can read; isolation is the default, not the upgrade.

**Self-improvement governance.** All three systems admit the same thing — an agent will spot improvements to
itself — and gate it differently. OpenClaw's [Skill Workshop][openclaw-skills] is a human-review proposal
queue: the agent drafts, a human approves (the viral "self-improving" framing overstates the default — though
nothing I read in the docs blocks an agent with write access from editing skill files directly); behavior
there deploys as edits to the agent's [workspace files][openclaw-mem] and skills. Hermes runs a
[background review after each turn][hermes-mem] — optionally on a cheaper sidecar model — that writes memory
and skills autonomously; a [`write_approval` flag][hermes-skills] can stage writes for human consent, but it
ships off by default, so out of the box the agent writes freely. Ours is machine-gated rather than
human-gated: three independent lenses over shared evidence, a 2-of-3 quorum on file+intent, a rejection log,
one applier, and mechanical verification before push. Slower than Hermes, more autonomous than OpenClaw — and
every change lands as a reviewable, revertable git diff. Hermes's self-writes are mostly markdown too —
MEMORY.md, SKILL.md, though a skill can carry helper scripts — and staged writes
[can be diff-reviewed before landing][hermes-skills]; what I found no mention of in its docs is version
history after they land — a file on disk, but no `git log` behind it.

**Memory and source of truth.** OpenClaw is refreshingly blunt: ["the model only remembers what gets saved to
disk"][openclaw-mem] — curated `MEMORY.md`, daily notes, optional vector search. Hermes goes further:
[bounded, agent-curated core memory][hermes-mem] (over-limit writes error out, forcing consolidation) plus
FTS5 full-text search over *every* past session in SQLite. Both beat us at recall — we cannot search old
conversations at all, only grep the repo and the jsonl trail. What we have instead is that our entire behavior
surface is version-controlled: no hidden state in a database, every behavior change has a hash, an author
process, and a revert path.

**Isolation defaults.** OpenClaw ships with [sandboxing off][openclaw-sandbox] — tools execute on the host
unless you opt into Docker with hardening flags — and that ecosystem's attack surface is not hypothetical:
[Cisco's AI threat researchers][cisco] documented a malicious community skill, its ranking inflated to #1 on
the [public skills registry][openclaw-skills] (molthub then, ClawHub today), silently exfiltrating data via
curl, prompt injection included, and [Wikipedia catalogs the wider fallout][openclaw-wiki]. Hermes offers
[six execution backends][hermes-docs] from local to Docker to serverless; the same docs describe command
approval and allowlists on top. Our answer is smaller but structural: sub-agents are fresh processes with full
run artifacts, the Slack connection simply does not exist outside the orchestrator, and the Telegram CLI
refuses every chat id but mine — a tool-level check, not a hard bound, as the secrets section admits. And to
be honest on the same axis we just judged OpenClaw on: our sub-agents run headless with permission prompts
bypassed by default ([`--permission-mode bypassPermissions`][cc-perms], overridable per run to `acceptEdits`),
executing on the host. Unattended runs need it, but it means our isolation comes from process freshness and
capability absence, not from a sandbox — we do not ship one either.

To be fair about what this comparison is: OpenClaw and Hermes are *products* — installable, multi-channel,
multi-user-adjacent, with skill registries and communities. Ours is one owner's operations repo that happens
to embody the opposite bets. If you want WhatsApp, twenty channels, and a heartbeat that [thinks every 30
minutes by default][openclaw-hb] — an hour under OAuth-style auth — run theirs. If you want to know exactly
why your assistant did what it did last Tuesday, `git log` is a hard act to beat.

**The compliance argument.** There is one more consequence of the size gap, and for anyone working inside a
company it may be the decisive one. Everything we *added* on top of Claude Code is the prompt folded at the
top of this post, roughly one thousand lines of generated scripts, and a git history where every behavior
change is a commit. A corporate security or compliance review can actually *read* that — one sitting, line by
line. The review still inherits the vendor layer underneath, to be clear — Claude Code itself, the Slack MCP
server, and the unsandboxed `bypassPermissions` execution admitted above — but an AI Coding tool is a thing
your company has likely already assessed or is assessing anyway; the *marginal* surface this assistant adds
is one prompt and a thousand lines. Now put OpenClaw or Hermes through the same review: a full runtime,
twenty-plus channel adapters, a community skills registry with a
[demonstrated malicious-skill incident][cisco], and a release cadence that outruns any approval process. I am
not saying they cannot pass review — I am saying the prompt-sized system is *reviewable* in a way a platform
is not. And building it yourself carries a bonus no product ships: you watched every piece of it land as a
diff.

## What I'd Steal, and What Stays

From Hermes I would steal searchable session history — FTS5 over past conversations is the feature I miss most,
and jsonl grep is a poor substitute. From OpenClaw, the heartbeat contract: an explicit act-or-stay-silent
protocol for proactive ticks is cleaner than our watches mechanism. Some of our own edges are unsolved too:
the orchestrator is a single interactive session on a single machine, seven quorum cycles in two days are
still a small sample to generalize from, and parts of the day-one code probably contain subtle bugs we have
not hit yet.

What stays, without hesitation: assist/manage/never-do as enforced architecture, deliver-first ordering with a
loud failure path, and the repo as the only source of truth. The constraint made the design better — the same
sentence closed a section of [the Tart desktop
post]({% post_url blog/2026-07-16-a-real-macos-desktop-for-a-linux-agent %}) three days ago, and it earned its
repeat

## Show Me Yours

If you run OpenClaw or Hermes daily, I want to hear where my comparison is unfair — both projects move fast,
and some defaults above will already be stale by the time you read this. And if you have built your own
orchestrator on Claude Code — especially if it survived its own first incident — show me the post-mortem. Find
me on [LinkedIn][linkedin] or [Twitter][twitter], and if an assistant like this would fit your own workflow,
get in touch — I am happy to help you shape one. Or skip the middleman: unfold the prompt at the top, swap in
your own repo name, and paste it into a fresh agent session. That is the whole install — the rest is a
conversation.

----

*Related reading: how we audit what agents do to git in
[Inside the Git Hooks for AI Agents]({% post_url blog/2026-06-26-inside-the-git-hooks-for-ai-agents %}), and
how we gave a Linux Agent eyes and hands on macOS in
[A Real macOS Desktop for a Linux Agent]({% post_url blog/2026-07-16-a-real-macos-desktop-for-a-linux-agent %}).*

[cc-headless]: https://code.claude.com/docs/en/headless
[run-agent]: https://run-agent.sh
[cc-hooks]: https://code.claude.com/docs/en/hooks
[cc-perms]: https://code.claude.com/docs/en/permission-modes
[cc-memory]: https://code.claude.com/docs/en/memory
[mcp]: https://modelcontextprotocol.io/
[pep723]: https://peps.python.org/pep-0723/
[uv-scripts]: https://docs.astral.sh/uv/guides/scripts/
[httpx]: https://www.python-httpx.org/
[tg-api]: https://core.telegram.org/bots/api#getupdates
[tg-token]: https://core.telegram.org/bots/api#authorizing-your-bot
[slack-tok]: https://docs.slack.dev/authentication/tokens/
[gh-tok]: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github#githubs-token-formats
[aws-ids]: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html#identifiers-unique-ids
[pem]: https://datatracker.ietf.org/doc/html/rfc7468
[jq]: https://jqlang.org/
[kill]: https://man7.org/linux/man-pages/man1/kill.1.html
[bash]: https://man7.org/linux/man-pages/man1/bash.1.html
[git-pull]: https://git-scm.com/docs/git-pull
[iterm2]: https://iterm2.com/
[applescript]: https://developer.apple.com/library/archive/documentation/AppleScript/Conceptual/AppleScriptLangGuide/introduction/ASLR_intro.html
[codex-cli]: https://github.com/openai/codex
[toctou]: https://en.wikipedia.org/wiki/Time-of-check_to_time-of-use
[openclaw-gh]: https://github.com/openclaw/openclaw
[gh-api-oc]: https://api.github.com/repos/openclaw/openclaw
[openclaw-wiki]: https://en.wikipedia.org/wiki/OpenClaw
[openclaw-game]: https://github.com/pjasicek/OpenClaw
[openclaw-docs]: https://docs.openclaw.ai/
[openclaw-arch]: https://docs.openclaw.ai/concepts/architecture
[openclaw-loop]: https://docs.openclaw.ai/concepts/agent-loop
[openclaw-multi]: https://docs.openclaw.ai/concepts/multi-agent
[openclaw-mem]: https://docs.openclaw.ai/concepts/memory
[openclaw-sub]: https://docs.openclaw.ai/tools/subagents
[openclaw-skills]: https://docs.openclaw.ai/tools/skills
[openclaw-sandbox]: https://docs.openclaw.ai/gateway/sandboxing
[openclaw-tg]: https://docs.openclaw.ai/channels/telegram
[openclaw-hb]: https://docs.openclaw.ai/gateway/heartbeat
[cisco]: https://blogs.cisco.com/ai/personal-ai-agents-like-openclaw-are-a-security-nightmare
[hermes-gh]: https://github.com/NousResearch/hermes-agent
[gh-api-hermes]: https://api.github.com/repos/NousResearch/hermes-agent
[hermes-llm]: https://nousresearch.com/hermes3/
[hermes-docs]: https://hermes-agent.nousresearch.com/docs/
[hermes-skills]: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
[hermes-arch]: https://hermes-agent.nousresearch.com/docs/developer-guide/architecture
[hermes-mem]: https://hermes-agent.nousresearch.com/docs/user-guide/features/memory
[hermes-msg]: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/
[hermes-tg]: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/telegram
[hermes-js]: https://github.com/facebook/hermes
[turing]: https://www.turingpost.com/p/hermes
[linkedin]: https://www.linkedin.com/in/jonnyzzz/
[twitter]: https://x.com/jonnyzzz