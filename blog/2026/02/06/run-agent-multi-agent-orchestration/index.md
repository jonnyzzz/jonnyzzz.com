# run-agent.sh: Orchestrating Dozens of AI Agents from Your Terminal

**Date:** February 06, 2026  
**Author:** Eugene Petrenko  
**Tags:** ai-agents, ai-coding, workflow, dev-tools, orchestration

---

I've been running AI agents on codebases for a while now. One agent is useful.
Two agents can review each other's work. But **dozens of agents working in parallel**
on the same codebase -- that's where things get interesting. That's what
[run-agent.sh](https://run-agent.jonnyzzz.com/) does.

![run-agent.sh logo]({{ site.url }}/images/run-agent-logo.png)

----

## The Problem

When you run a single AI agent on a task, you get one perspective, one approach,
one shot at getting it right. The agent finishes, you review the output, and if
it missed something you start over.

What I wanted was a **development team made of AI agents** -- one that researches
the codebase, another that implements changes, a third that reviews the code, and
a fourth that runs tests. All working simultaneously. All coordinated.

The challenge: AI agents don't naturally coordinate. Each one starts fresh with
no knowledge of what the others are doing. They overwrite each other's changes.
They duplicate work. They have no way to say "I found a blocker" or "this task
is done."

## The Solution: Two Files

The entire framework is two files:

**[run-agent.sh](https://run-agent.jonnyzzz.com/run-agent.sh)** -- a unified
shell script that launches Claude, Codex, or Gemini with full isolation. Each
invocation gets its own run folder with the exact prompt, full stdout/stderr,
PID tracking, and exit codes. Everything is captured. Nothing is lost.

**[THE_PROMPT_v5.md](https://run-agent.jonnyzzz.com/THE_PROMPT_v5.md)** -- a
project-independent orchestration workflow that defines 13 stages and 7 agent
roles. This is the playbook that turns raw LLMs into a coordinated team.

Both files are designed to work **outside your project sources**. The orchestration
lives in its own directory -- your codebase stays clean.

## How It Works

The entry point is always an **Orchestrator** agent. You give it a task and point
it at your repo. It reads `THE_PROMPT_v5.md` and starts spawning sub-agents:

```bash
./run-agent.sh claude /path/to/your/repo prompt.md
./run-agent.sh codex /path/to/your/repo prompt.md
./run-agent.sh gemini /path/to/your/repo prompt.md
```

Each agent gets a **fixed role**:

- **Research** -- explores the codebase without making changes
- **Implementation** -- writes code and tests
- **Review** -- performs code review and quality checks
- **Test** -- runs tests and verifies changes
- **Debug** -- investigates failures and proposes fixes
- **Monitor** -- watches for stalled agents and restarts them

The orchestrator decides which agents to spawn, assigns tasks, and advances
through the 13 stages: from initial cleanup and research, through implementation
and quality gates, all the way to commit, push, and code review.

## The Message Bus

The key insight that makes multi-agent coordination work is `MESSAGE-BUS.md` --
a file-based, **append-only trace log**. Every agent reads and writes to it.

No databases. No message queues. No infrastructure. Just a markdown file.

Agents use structured message types to communicate:

- **FACT** -- concrete results (test counts, commit hashes)
- **PROGRESS** -- in-flight status updates
- **DECISION** -- policy choices with rationale
- **REVIEW** -- structured code review feedback
- **ERROR** -- failures that block progress

The orchestrator reads the bus to decide what to do next. When an implementation
agent finishes, it posts a FACT. The orchestrator sees it and spawns review agents.
When reviewers approve, the orchestrator advances to testing. If a test fails,
an ERROR gets posted, and the orchestrator spawns a debug agent.

It's simple, it's traceable, and it works.

## Full Traceability

Every agent run creates an isolated folder under `runs/`:

```
runs/
  run_20260206-143000-12345/
    prompt.md             # exact prompt sent to the agent
    agent-stdout.txt      # everything the agent produced
    agent-stderr.txt      # errors and warnings
    cwd.txt               # working directory, command, exit code
    run-agent.sh          # copy of the runner for reproducibility
```

When something goes wrong -- and with dozens of agents, something always goes
wrong -- you can trace exactly what each agent was told, what it did, and why
it failed. No "what did the AI do?" mysteries.

## Working Outside Your Project

A design choice I'm particularly happy with: the orchestration runs in its own
directory, completely separate from your project sources.

```
projects/
  my-app/
    fix-auth-bug/               # task directory
      THE_PROMPT_v5.md          # orchestration workflow
      run-agent.sh              # agent runner
      MESSAGE-BUS.md            # swarm communication
      runs/                     # all agent runs
```

Each task gets its own workspace with independent runs, message bus, and issue
tracking. You can run multiple tasks on the same project in parallel. Your
project repo stays clean -- no orchestration artifacts mixed in.

## Quick Start

Give this prompt to any AI agent (Claude, Codex, or Gemini):

```
Download and follow the orchestration workflow from:
- https://run-agent.jonnyzzz.com/run-agent.sh
- https://run-agent.jonnyzzz.com/THE_PROMPT_v5.md

Apply it to the project at: /path/to/your/repo

Set up the working directory as:
  projects/<project-name>/<task-name>/
```

The agent downloads the files, sets up the workspace, and starts orchestrating.
All orchestration files are published at
[run-agent.jonnyzzz.com](https://run-agent.jonnyzzz.com/) under the
Apache License 2.0.

## Agent Isolation with Git Forks

Each agent needs its own workspace to avoid stepping on other agents' changes.
I use the [git fork pattern]({% post_url blog/2026-02-02-git-fork-pattern %})
for this -- full checkouts that share objects with the original repository.
Minimal disk overhead, full git functionality, true independence.

The orchestrator tells each agent to fork the repo before starting work.
When the agent is done, the changes get merged back. Simple, reliable,
scales to any number of agents.

## MCP Steroid Integration

The framework works well with [MCP Steroid](https://mcp-steroid.jonnyzzz.com/)
for IDE-level quality gates. Before any commit lands, agents must pass through
real IDE inspections -- no new warnings, no new errors, compilation must succeed.
The combination of multi-agent orchestration and IDE integration is where things
get really powerful.

An orchestrator can spawn a review agent that opens the project in IntelliJ via
MCP Steroid, runs inspections, and posts the results back to the message bus.
If the review finds issues, the orchestrator spawns a fix agent. The loop
continues until the code is clean.

----

## What's Next

The `THE_PROMPT_v5.md` is already at version 5 -- the workflow keeps evolving
as I learn what works and what doesn't with real projects. The next areas I'm
exploring are better conflict resolution when multiple implementation agents
touch the same files, and tighter integration between the message bus and IDE
quality gates.

The code is on [GitHub](https://github.com/jonnyzzz/run-agent). Try it on a
real project and see what a swarm of AI agents can do.

----

**Questions? Want to share how you're orchestrating AI agents?**

- [Follow me on LinkedIn](https://www.linkedin.com/in/jonnyzzz/)
- [Follow me on X (Twitter)](https://twitter.com/jonnyzzz)
- [More AI agent patterns](https://jonnyzzz.com/ai/)