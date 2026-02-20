# CLI Is the New API and MCP: Building Agent-Ready Tools for Enterprise Teams

**Date:** February 20, 2026  
**Author:** Eugene Petrenko  
**Tags:** ai-agents, ai-coding, developer-experience, mcp, cli, enterprise

---

Late last year, I noticed something small and very important.

My AI Agents discovered `gh` on my machine and started using it without asking me for a tutorial. I'm not even sure it was me to install `gh`.
They configured auth, read and wrote comments, opened issues, updated pull requests, and kept going.

That was my "wait, this is different" moment.

I did not build a custom integration for them. I did not write an MCP server first. I did not train a model.
I had a well-designed CLI already installed, with `--help`, good error messages, and predictable behavior.
That was enough.

## The Discovery: AI Agents Already Speak CLI

When we discuss AI tooling, we often jump directly to orchestration systems, special protocols,
or expensive platform programs. Those are useful. We use them too.

But my first real breakthrough was much more practical:

- AI Agents were already fluent with command-line workflows.
- They could compose commands, parse output, and retry after failures.
- They could guide me through auth prompts when needed.
- Agents can learn about your tools from AGENTS.md or a likes files automatically.

That changed how I think about tool strategy.

> We are building products for agents now.
>
> AI Agent is not just an implementation detail. It is a user persona.

## The Evolution: MCP, Skills, and Process Execution

MCP is excellent and increasingly important, especially when you need typed tool contracts and explicit
capabilities ([architecture](https://modelcontextprotocol.io/docs/concepts/architecture),
[spec](https://modelcontextprotocol.io/specification/latest)).

But there is a practical truth worth saying out loud:

- A good CLI is often the fastest way to make a tool usable by AI Agents.
- The CLI should have a good UX for agents (not necessary the same as a good UX for humans, but likely)
- In my experience, existing command surfaces are often most of the way there.

## The Real Unlock: Good CLI UX Is the Integration

Here is the simplest integration I now recommend to enterprise teams.

### Step 1: Ship an actually usable CLI

At minimum:

- stable commands and flags
- predictable non-zero exit codes on failure
- `--help` that explains intent, not only syntax
- machine-readable output for anything non-trivial
- clear auth and permission errors

GitHub CLI is a strong example here:

- [GitHub CLI manual](https://cli.github.com/manual/)
- [`gh api`](https://cli.github.com/manual/gh_api)

### Step 2: Tell the AI Agent that the CLI exists

A single section in your agent instruction file is enough to start.

```md
# Agent Tools

Use `acme-cli` for:
- change requests
- deployment status
- internal issue tracking

Rules:
- Prefer `acme-cli --json` for parsing.
- Run `acme-cli --help` before using a new subcommand.
- If auth fails, explain the next login step to the user.
```

That is it. No ceremony.

### Step 3: Keep command contracts stable

If the output format changes every week, your agent workflows will flap.

Treat your CLI output as an API contract. Humans can adapt quickly. Agents need consistency.

### Step 4: Improve and make AI Agents learn from the tool

On this step you are going to run the product work, and ask you AI Agents to perform
specific task with your CLI. You are not going to give many instructions just ask
one to deliver. Do several rounds, and improve the tool to avoid the common pitfalls.

Use one AI Agent as the Product manager and ask it to start the agents to conduct the review. For example, 
you can use [run-agent.sh](https://run-agent.jonnyzzz.com) as the CLI that makes one agent
start next agents, such that Claude Code, Codex, and Gemini.

I use the same **Reinforcement Learning** approach in the [MCP Steroid](https://mcp-steroid.jonnyzzz.com)
project, where we use all the call traces as the input for improvements. During that improvement process,
we created the recommendation system that suggests the best documentation articles based on the
user requests and current failures.

The part of your work is marketing. You need to explain what your tool does in the best and
the most clear and straightforward way to get your target audience -- AI Agents -- use your tool.

Iterate and improve.

### Design the Interaction and Developer Experience

Sometimes, a login or a real user interaction is necessary. You should think about that carefully, 
to make sure it will work with an AI Agent connected. An agent may give up after several failures,
and find the other way to deal with the task without your tool.

The fragile version example. It can work amazing, or block and fail:

```bash
$ acme review submit
Are you sure? [y/N]
Please open browser and login...
Operation completed successfully!!!
```

At this point, you are going to develop the best user experience for AI Agent, knowing there is
a developer behind the agent too.

## Enterprise Rollout: Small Moves, Big Impact

The deployment pattern is surprisingly simple:

1. Put the CLI binary in the repo or distribute through your MDM / endpoint management.
2. Add one line in your AGENTS.md instructions saying where the tool is or where to download it.
3. Keep login and updates frictionless.

You do not need to rebuild your whole platform before you start getting value. But make sure you are
not making the process complex, or you are not making your AI Agent asking for hundreds of permissions
to proceed with the tool or with the installation of it.  

If you already have internal CLI tools, you are not behind.
You are probably ahead.

But having the commands is only half the story. The other half is whether an AI Agent can authenticate
and recover cleanly when auth fails.

## Developer Experience Is Mostly About Authentication

In enterprise environments, auth is where good ideas go to die.

Your AI Agent can run commands, but eventually it must ask a human for approval or login.
If this flow is noisy, confusing, or brittle, the whole system slows down.

For internal tools that connect to SCM, CI/CD, review systems, and issue trackers, I now use this checklist:

- one obvious login command (`tool auth login`)
- clear status (`tool auth status`)
- explicit scopes and permission errors
- short troubleshooting message in every auth failure
- clear UX for AI Agent and the user
- explicit token mode in case of fully automated approaches

This is not only AI Agent experience. This is core developer experience.

## Tool Lifecycle: Updates, Rollbacks, and Version Control

The next failure mode is version drift.

One project needs CLI version A. Another needs B.
Agents run on laptops, ephemeral environments, and CI workers.
Now your support channel becomes chaos.

We need a lightweight control plane for versions.

I have been experimenting with this pattern in
[`devrig.dev`](https://github.com/jonnyzzz/devrig.dev): a dev environment tool that can also resolve the
right binary version, verify it, cache it, and execute it consistently.

A minimal config can look like this:

```yaml
wrapper:
  version: 0.0.1
  hash: sha-512:<wrapper-hash>

tool:
  name: jb-cli
  version: 0.9.4
  hash: sha-512:<tool-hash>
```

The wrapper resolves the right binary per platform, verifies checksums, caches locally, and executes.
That means every AI Agent on every machine runs the same version by default.

This makes updates and rollbacks explicit, reproducible, and project-aware.

## Why This Matters for SDLC Throughput

The tools like one above help to connect your AI Agents to the organizational flow,
and make agents able to code, build, test, review and comply with the changest.
Agents on the other hand work much better with the agentic loop, where feedback
flows in.

This is connected to a point I made in
[the code review bottleneck post]({% post_url blog/2026-01-16-code-review-bottleneck %}).

Generation speed is only one part of the pipeline.

If your agent can generate code quickly but cannot operate through code review,
protected delivery, and issue tracking, you did not speed up the system.
You moved the bottleneck.

The CLI approach helps because it integrates the agent into the real flow,
not a sandboxed demo flow.

## The Feedback Loop: Learn by Using Agents, With Agents, For Agents

The most interesting part starts after rollout.

If your tool is painful, AI Agents will hit that pain many times per day.
That is a gift, if you capture it correctly.

Design the tool so agents can report friction:

- open issue in tracker
- include command, error, and context
- propose a fix or a minimal reproduction

Example issue template:

```text
Title: agent failure in jb-cli review submit

Command: jb-cli review submit --id CR-123
Error: 401 token expired
Attempted recovery: jb-cli auth login
Suggested improvement: expose token expiry in auth status JSON
```

Then your team triages and improves the tool, often with another AI Agent.
That creates a practical reinforcement loop.
No custom ML pipeline required. Just disciplined engineering feedback, at high frequency.

## What I Got Wrong at First

Just start using AI Agents to code tasks in some projects. You will see soon where is
the manual work, or what you agent should be able to do automatically. 

For me, it has started with the build and tests run, for that use-case I use
the [MCP Steroid](https://mcp-steroid.jonnyzzz.com) plugin. 

For code review, I use [run-agent.sh](https://run-agent.jonnyzzz.com) and instruct
my main agent to start multiple different agents to review the code, look at the git
history to the popular patterns and behaviour of the team. 

Next I found that I need to follow internal processes and submit the code to the
safe-push pipeline. We already have the CLI tool for that task, but it was lacking
the status sub-command. Now we have it. 

I'm looking forward to support YouTrack, TeamCity and other products, and solve more
low-hanging fruits problems for AI Agents to work on the project.

## Try This Next Week

If you own internal developer tooling, try this next week:
1. Start using AI Agents for coding
2. Pick one CLI command or AGENTS.md improvement, if none look at your own experience.
3. Add agent instructions in the repo and run one real task through an AI Agent.
4. Collect stats and usages, failures, improve the CLI, and repeat.

That loop is where the leverage comes from.

If your team says, "we already have internal CLI tools," that is good news.
You already did the difficult foundation work. We are widening the interface of our systems.
For the first time, the terminal is becoming a direct product surface for both humans and AI Agents.

For new tools, if you consider to start development today. I recommend to see if the CLI too + Skills or AGENTS.md
are just enough, before you start doing the full-fledged MCP Server. I believe that we can create tools,
which require only a really short intro or a SKILL, having everything else encapsulated inside it.

If you run this pattern in your organization, I would love to hear what worked and what failed.
Reach out on [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) or
[Twitter](https://twitter.com/jonnyzzz).