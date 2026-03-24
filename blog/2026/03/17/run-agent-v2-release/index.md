# run-agent.sh v2.0: Hardened Runner with 115 Tests, Random Selection, and Agent Environment Contract

**Date:** March 17, 2026  
**Author:** Eugene Petrenko  
**Tags:** ai-agents, multi-agent, orchestration, cli, testing, automation, ai-coding, dev-tools, sub-agent

---

I've been running AI Agents in parallel for weeks — Claude Code, Codex, Gemini —
and the launcher script that ties them together kept accumulating rough edges.
Stale PID files after crashes. No tests. No help output. And, as three AI reviewers
independently discovered, a command injection vulnerability hiding in plain sight.

Today I'm releasing [run-agent.sh v2.0][release] — a major rewrite that fixes all of that.

The script started as a quick 95-line wrapper. It now weighs in at 211 lines,
backed by 115 acceptance tests, random agent selection, and a proper environment
contract for every spawned agent.

## What is run-agent.sh?

`run-agent.sh` enables you agents to start more agent processes for sub-tasks.
That plays nice with Recursive Language Models ([RLM.md](https://jonnyzzz.com/RLM.md)),
or [THE_PROMPT_v5.md](https://run-agent.jonnyzzz.com/THE_PROMPT_v5.md) swarms,
where you use more agents. In simple words, running multiple agents allows each
agent to do fewer things at once via delegation, delivering better outcomes, while avoiding the
context rot or overflow.

As an example, use the prompt like
```
<PUT YOUR TASK DESCRIPTION HERE>

In order to deliver on the task, you should use https://run-agent.jonnyzzz.com/run-agent.sh script
to start more tasks. You should follow the https://run-agent.jonnyzzz.com/THE_PROMPT_v5.md and
other files relative to it as the main process. Your purpose is to orchestrate and delegate
the work to other run-agent's which you start, you must not do the work yourself.
So create /loop when necessary to monitor the process. Never stop unless the work is completed.

All your promots should use the https://run-agent.jonnyzzz.com/MESSAGE-BUS.md as the key
communication principle. 

Make sure you download the files locally and use the full paths to the files below.
```

[run-agent.sh][site] is a unified shell script that launches AI coding agents
in isolated sub-processes, with selected current directories. Each invocation creates a timestamped folder with
the prompt copy, captured stdout/stderr, process metadata, and a copy of the
runner itself — full traceability for every agent execution.


**This is the tool for AI Agents to help consolidate and coupe with the work more effectively**

```bash
./run-agent.sh claude ~/Work/project ./task-prompt.md
```

It powers the `marinade` agentic orchestration framework, where a root
AI Agent spawns sub-agents in parallel.

## Random agent selection

One thing I noticed while orchestrating multi-agent runs: I kept manually
rotating between agents to diversify the results. That felt like a job for the
script, not for me.

The default agent is now `any` — the script picks a random agent from the
available pool:

```bash
./run-agent.sh any ~/Work/project ./prompt.md
# AGENT_SELECTED=gemini
# RUN_ID=run_20260317-134514-27961
# RUN_DIR=./runs/run_20260317-134514-27961
```

This is useful when you want to let agents compete or diversify across runs.
When combined with `RUN_AGENT_AGENTS`, the random selection respects the
restricted pool:

```bash
# Set at the environment level
export RUN_AGENT_AGENTS=claude,codex

# The actual call
./run-agent.sh any ~/Work/project ./prompt.md
# Never picks gemini
```

## Agent availability control

A new environment variable `RUN_AGENT_AGENTS` controls which agents are
available. Agents not in the list are rejected and hidden from `--help`:

```bash
# Only claude and codex are available
RUN_AGENT_AGENTS=claude,codex ./run-agent.sh gemini ...
# stderr: Unknown agent: gemini
# stderr: Known agents: claude,codex
# exit 2
```

Invalid names in the list are caught at startup:

```bash
RUN_AGENT_AGENTS=claude,fakename ./run-agent.sh claude ...
# stderr: RUN_AGENT_AGENTS: unknown agent 'fakename'. Built-in agents: codex,claude,gemini
# exit 2
```

## Environment contract

Before this release, agents had to guess paths or rely on convention.
Now every agent gets four exported environment variables — no guesswork:

| Variable       | Value                                                      |
|----------------|------------------------------------------------------------|
| `RUNS_DIR`     | Absolute path to the runs directory                        |
| `MESSAGE_BUS`  | Absolute path to `MESSAGE-BUS.md` (now inside `RUNS_DIR`)  |
| `RUN_ID`       | Unique run identifier (e.g., `run_20260317-134514-27961`)  |
| `PROMPT`       | Absolute path to the copied prompt file                    |

Every agent knows exactly where it is, where to write messages,
and what run it belongs to.

Additionally, `CLAUDECODE` is explicitly `unset` before spawning —
preventing nested Claude Code runtime context from leaking into
sub-agents. I learned this the hard way: a Claude Code sub-agent
was picking up its parent's runtime state and behaving differently
than when launched standalone.


## 115 acceptance tests, zero API keys

The test suite uses mock agent stubs — small bash scripts that simulate
`claude`, `codex`, and `gemini` without making any API calls. The full
suite runs in under 10 seconds:

```bash
$ bash tests/test-run-agent.sh
=== run-agent.sh Acceptance Tests ===
--- Test 1: Script structure ---
  PASS: run-agent.sh is executable
  PASS: run-agent.sh has bash shebang
  PASS: run-agent.sh uses set -euo pipefail
...
=== Test Results ===
  PASSED: 115
  FAILED: 0
RESULT: PASS (all 115 tests passed)
```

The tests cover what matters:

- **Prompt delivery**: a mock agent that `cat`s stdin, verifying prompt
  content reaches the agent
- **CLI arguments**: a mock that echoes `"$@"`, verifying
  `--permission-mode`, `-C`, etc.
- **CWD with spaces**: creates a directory with spaces, runs an agent,
  checks `pwd` output
- **Injection rejection**: passes `$(echo pwned)`, `foo;bar`, `../etc`
  as agent names — all exit 2
- **Environment exports**: mock agents print `$RUN_ID`, `$PROMPT`,
  `$MESSAGE_BUS` — verified against expected values
- **CLAUDECODE sanitization**: sets `CLAUDECODE=should_be_removed`,
  verifies agent sees it unset
- **cwd.txt correctness**: checks not just key presence but actual values
  (absolute paths, numeric PID, matching RUN_ID)
- **Help side effects**: verifies `--help` creates no run directories

The three-agent review also identified tests that were "vacuously true" —
tests that would pass even if the behavior they claimed to test was broken.
For example, test 15 originally grepped the script source for
`export MESSAGE_BUS` instead of verifying the agent process actually
received the variable. That is the kind of bug that hides in plain sight
until someone (or some agent) asks the right question.

## The exit code bug

This one was subtle. The original script had `set -euo pipefail` and then:

```bash
wait "$AGENT_PID"
EXIT_CODE=$?
rm -f "$PID_FILE"
echo "EXIT_CODE=$EXIT_CODE" >> "$CWD_FILE"
```

When an agent exited non-zero, `set -e` caused the script to bail at
`wait` before cleaning up `pid.txt` or recording `EXIT_CODE`. Monitoring
scripts that checked `pid.txt` would think the agent was still running.
I spent more time than I'd like to admit debugging "zombie" agents that
were actually long dead. The fix:

```bash
EXIT_CODE=0
wait "$AGENT_PID" || EXIT_CODE=$?
rm -f "$PID_FILE"
echo "EXIT_CODE=$EXIT_CODE" >> "$CWD_FILE"
```

The `|| EXIT_CODE=$?` captures the non-zero exit code without triggering
`set -e`. Standard bash idiom, but easy to miss when you write the happy
path first.

## CI/CD

Two GitHub Actions workflows keep the project honest:

- **Tests** — runs all 115 acceptance tests on every push
- **Deploy** — syncs static files, builds the site, deploys to GitHub Pages

Every push to `main` makes the latest `run-agent.sh` available at
[run-agent.jonnyzzz.com/run-agent.sh][script-download].

## What's next

The script is battle-tested for the orchestration use case, but I want to
push it into real, established projects — not just greenfield AI experiments.
That will likely surface new requirements and rough edges.

Concrete plans:

- **Integration tests with real agents** — mock stubs catch regressions,
  but they cannot catch API-level breakage. I want a CI job that actually
  calls each agent with a trivial prompt and verifies end-to-end behavior.
- **Streaming output** — right now stdout/stderr are captured to files.
  For long-running agents, tailing the output and progress would help to 
  tell a suck agent from a thinking one.
- **More agents** — the `case` statement makes it trivial to add new ones.
  If you use a different AI coding tool, open a PR.

There's still so much more we can do. If you run multi-agent orchestration
or have ideas for what the runner should handle, I would love to hear about
it. Reach out on [LinkedIn][linkedin] or [Twitter/X][twitter].

---

The release is at [github.com/jonnyzzz/run-agent/releases/tag/v2.0.0][release].
The script is at [run-agent.jonnyzzz.com][site].

[release]: https://github.com/jonnyzzz/run-agent/releases/tag/v2.0.0
[site]: https://run-agent.jonnyzzz.com
[script-download]: https://run-agent.jonnyzzz.com/run-agent.sh
[linkedin]: https://www.linkedin.com/in/jonnyzzz/
[twitter]: https://x.com/jonnyzzz