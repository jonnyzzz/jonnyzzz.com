# MCP Steroid Is Now Open Source

**Date:** April 07, 2026  
**Author:** Eugene Petrenko  
**Tags:** mcp, mcp-steroid, intellij, android-studio, open-source, agentic-coding

---

MCP Steroid is now open source under the Apache 2.0 license. The source is at
[github.com/jonnyzzz/mcp-steroid](https://github.com/jonnyzzz/mcp-steroid), with the project
transitioning under JetBrains at [github.com/JetBrains/mcp-steroid](https://github.com/JetBrains/mcp-steroid).

## The Bridge

AI Agents can think. They cannot always act. The gap between what agents can reason about and
what they can actually do inside a codebase -- that's the bottleneck I've been working on.

I build products where the AI Agent is the user. No UI -- APIs, CLIs, MCPs. People keep designing
products for humans with AI bolted on. I'm doing the opposite: we make JetBrains tools available
for AI agents, not for humans.

IntelliJ-based IDEs have shipped with a built-in MCP server since 2025.2 -- curated tools for common
operations like running configurations, file edits, and basic code actions. Useful, but fixed.

MCP Steroid is different. It gives AI Agents the ability to write and execute arbitrary Kotlin code against
the full IntelliJ Platform API. Not a predefined menu of operations -- the actual APIs that power
the IDE's own features: inspections, refactorings, the debugger, PSI trees, screenshots.
It can access any plugins and third-party extensions too! AI Agents
get the whole IDE, not a curated subset. On [DPAI Arena](https://mcp-steroid.jonnyzzz.com/docs/strategy/)
benchmarks, agents with MCP Steroid are 20-54% faster on tasks requiring semantic understanding --
54% on rename-refactoring across 9 files, 20% on multi-layer generation across 15 files. Simple text
replacements show no improvement, which is expected.

I wrote more about this framing in
[Agentic Experience and Tools]({% post_url blog/2026-03-24-agentic-experience-and-tools %})
and in the [original MCP Steroid post]({% post_url blog/2026-01-04-mcp-steroids-intellij %}).

## How It Got Here

I started MCP Steroid in December 2025 as a free-time experiment -- one engineer building a Bridge
between AI Agents and IntelliJ's APIs. It was built with AI agents. The project uses MCP Steroid
itself plus a [run-agent.sh]({% post_url blog/2026-02-06-run-agent-multi-agent-orchestration %})
swarm for development. The main effort went into evals and integration tests -- making sure agents
actually succeed at real tasks, not just compile. MCP Steroid plugin learned from its one development too.

The codebase has 84 prompt markdown files -- 37% of production source by line count -- that teach
agents how to navigate IntelliJ APIs: the debugger, refactorings, inspections, test runners, VCS.
Just like JetBrains IDEs make software developers more professional, these resources make AI agents
more professional. There are integration tests for Claude Code, Codex, and Gemini, all
[running in Docker]({% post_url blog/2026-02-21-testing-mcp-server-with-ai-agents %})
with full IDE containers.

We validated that AI Agents can write and call Kotlin code to solve specific tasks with the help of IntelliJ.
This is quality work
and a real experiment with 1,690 commits over four months, not a rough prototype --
see the [project assessment at 75 days]({% post_url blog/2026-02-23-mcp-steroid-project-assessment %})
for the earlier snapshot.

In March 2026, we agreed to move the project under JetBrains and start using it internally. The original source is at
[github.com/jonnyzzz/mcp-steroid](https://github.com/jonnyzzz/mcp-steroid), with the JetBrains fork
at [github.com/JetBrains/mcp-steroid](https://github.com/JetBrains/mcp-steroid), released under
Apache 2.0. I'm still the main contributor.

## Skills -- a Tease

The real value isn't individual API calls. It's that solved problems accumulate into reusable skills.
An agent struggles through IntelliJ's API once, figures out the working approach, and that approach
gets wrapped into a skill any agent can call without re-discovering the surface.

The skill prototyping process has become magnitude times cheaper -- 
make an agent research the [IntelliJ Community](https://github.com/JetBrains/intellij-community)
and figure out how to solve your task. Then, turn it as a skill which uses the MCP Steroid plugin. 
Eval it.

I've got a dedicated post about the
skill factory coming next --
with code examples, the two-phase workflow, and the enterprise angle. For now: think of it as the
difference between giving an agent a tool and giving it a way to build its own tools.

## Try It

According to our [strategy](https://mcp-steroid.jonnyzzz.com/docs/strategy/), we start from an
explicit plugin for IntelliJ-based IDEs (including any third-party IDEs, e.g. **Android Studio**).
The long-term target is a headless
self-contained runtime -- available as SaaS and as an end-user product -- the headless 
**IDE for AI Agents**. The project requires investment into packaging for headless environments, and that's where
JetBrains infrastructure matters.

To get started today: install the MCP Steroid plugin in any IntelliJ-based IDE or Android Studio
(version 2025.3+). The plugin generates `.idea/mcp-steroid.md` in your project with instructions.
Follow those instructions to register the MCP Server with your agent. The server uses the
Streamable HTTP protocol.

Quick sanity check -- ask your agent to run a Kotlin code like `println(project.name)` or ask it
"What do I see in my IDE"

See it in action: [YouTube playlist](https://www.youtube.com/playlist?list=PLitZWClhc4Qgz3w8qrtctMR_lpIc81n0f),
and here's [Codex debugging an application in IntelliJ IDEA](https://www.youtube.com/watch?v=HtDDNyAoLak).

## Get Involved

The project is open source, and the community is just getting started. If you've explored IntelliJ
APIs, built agents, or solved IDE automation problems -- that knowledge is useful here.

**Star and fork the repository.** The original source is at
[github.com/jonnyzzz/mcp-steroid](https://github.com/jonnyzzz/mcp-steroid) and the JetBrains fork
is at [github.com/JetBrains/mcp-steroid](https://github.com/JetBrains/mcp-steroid). Fork it, experiment with it, write
a skill, open an issue, improve the docs. Contributions of any kind are welcome.

You can just try the plugin, download it from [the website](https://mcp-steroid.jonnyzzz.com/releases)
or from JetBrains Marketplace (soon). Share what you build, and
join the [Discord](https://discord.com/invite/e9qgQ7NeTC).

## What's Next

With JetBrains infrastructure, support, and investment, I believe MCP Steroid will be delivered
sooner and enable AI Agents of any kind with the best tools human developers love in
IntelliJ-based products.

The skill factory post is coming
tomorrow. We're also opening a proof-of-concept program for
companies that want to use MCP Steroid for their specific workflows. If that's interesting,
reach out on [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) or in the
[Discord](https://discord.com/invite/e9qgQ7NeTC).