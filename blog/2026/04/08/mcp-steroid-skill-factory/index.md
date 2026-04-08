# IntelliJ as a Skill Factory

**Date:** April 08, 2026  
**Author:** Eugene Petrenko  
**Tags:** mcp, mcp-steroid, intellij, android-studio, skills, agentic-coding, kotlin

---

Every time your agent needs to use an IntelliJ API it hasn't seen before, it burns tokens figuring
out PSI trees and threading rules. It tries something, gets a compilation error, tries again, gets
a wrong result, tries a third time. Eventually it works. Then the next agent -- or the same agent
in a new session -- starts the whole cycle over.

I [open-sourced MCP Steroid]({% post_url blog/2026-04-07-mcp-steroid-open-source %}) yesterday.
That post covered the what and why. This one is about the pattern that makes the plugin actually
useful day to day: **skills**.

## Two Islands

Here's how I think about the problem. There are
[two islands]({% post_url blog/2026-03-24-agentic-experience-and-tools %}).

**Island one** is the IDE world. IntelliJ platform has deep code understanding -- control flow
graphs, cross-language refactorings, structural search, a debugger, Gradle integration, Spring Integration, and the long-tail more of the features. 
It's an
extraordinary amount of engineering. But it was all built for humans clicking menus. IntelliJ IDEs
ship with a built-in MCP server since 2025.2, but it exposes a curated, fixed set of operations --
file edits, run configurations, basic code actions. A start, but not the full picture.

**Island two** is the agentic world. AI agents that can reason, plan, iterate, and write code --
but they're stuck either running `grep` and `sed`, or limited to predefined tool menus, never
touching the real depth of what the IDE already knows about the codebase.

MCP Steroid bridges them fully. An agent sends Kotlin through `steroid_execute_code`, and that code
runs inside the IDE's JVM with full access to everything IntelliJ knows. Not a curated subset.
Not a fixed menu. The actual APIs that power the IDE's own features. No abstractions skipped.

## The Skill Factory

Here's the workflow that changed how I use the plugin.

**Phase one: research.** The agent experiments with IntelliJ APIs via `steroid_execute_code`. It
tries things, fails, iterates. This phase is messy -- maybe 4-8 retries, a lot of tokens spent on
compilation errors and wrong API assumptions -- including
[JVM classloading quirks]({% post_url blog/2026-02-12-jvm-classloading-intellij %}) that trip up
even experienced developers. That's fine. The agent is learning.

At that phase Agent uses the 60+ resources that are already included into the MCP Steroid package.
For really complex tasks, I also recommend adding the [IntelliJ Community](https://github.com/JetBrains/intellij-community) sources
and the sources of your thrid-party plugins and ask the agent to conduct the reasearch there as well.

**Phase two: encapsulation.** Once the agent figures out how to solve the problem, the working
approach gets wrapped into a reusable skill -- a Kotlin snippet stored as a markdown document.
Now any agent can call it without re-discovering the API surface.

That's the skill factory. Each solved problem becomes a skill. Skills accumulate. The agent that
struggled for 8 retries to find deprecated methods with zero usages? Next time it takes one call.

The [MCP Steroid repo](https://github.com/JetBrains/mcp-steroid) ships with built-in articles that
serve a dual purpose -- they're documentation for you, and reference material that agents read to
create new skills. When your agent needs to figure out VFS or the debugger API, it reads these
articles just like you would. Check the [docs](https://mcp-steroid.jonnyzzz.com/docs/) for the
full set.

## Why Skills, Not Plugin Code

Here's what makes skills compelling: writing a skill is one markdown file with a Kotlin code snippet.
Writing the same capability as traditional plugin code means a Gradle project, extension points,
build infrastructure, and a full development cycle. Skills skip all of that -- the agent handles
compilation, threading, and iteration for you. You just need to point it in the right direction.

This also works well with
[sub-agent architectures]({% post_url blog/2026-01-30-orchestrating-ai-fleets %}). A parent agent
can delegate a specific task to a sub-agent that reads only the relevant skill documentation from
MCP resources. The sub-agent iterates until it works, and the parent's context stays clean. This is
how I run it in practice -- the orchestrator picks the skill, the worker executes it.

## Enterprise: Your Own Skills

Even if you're behind an enterprise firewall with proprietary IntelliJ plugins and internal APIs,
you can create skills that wrap your own extensions. Your agent doesn't need to know the internals
of your company's custom inspection plugin -- it just calls the skill.

This is deliberately the same pattern. Open-source skills for the public IntelliJ APIs, private
skills for your internal tooling. A team can build up a skill library for their specific codebase
and workflows, and every agent on the team benefits.

## What's Next

The immediate focus is skill coverage. More documented API patterns, more worked examples, more
pre-built skills. The goal is to shrink the research phase for common tasks until it's nearly zero.

Longer term, I want to explore event-driven skills. IntelliJ already has APIs for subscribing to
events -- a commit happens, a test fails, an inspection fires. An agent that reacts to those events
automatically, running the right skill in response, would be genuinely useful. The event APIs
exist. We haven't wired them into MCP Steroid yet.

And headless support -- running the plugin in Docker containers, in CI -- is an active investment.
We already [test MCP servers with real agents in Docker]({% post_url blog/2026-02-21-testing-mcp-server-with-ai-agents %}).
Agents don't always need a GUI, and we want MCP Steroid to work without one. That requires
packaging work that JetBrains infrastructure makes possible.

## Get Involved

The best way to contribute to MCP Steroid is to create a skill. Pick an IDE capability you use
manually -- navigate to declaration, find all usages of a deprecated API, list failing tests with
their stack traces, whatever is useful in your workflow. Point your agent at it. Let it figure
out the API. When it works, save the Kotlin as a skill file and open a pull request.

**Star and fork the repository** to get started:
[github.com/jonnyzzz/mcp-steroid](https://github.com/jonnyzzz/mcp-steroid) (original source) and
[github.com/JetBrains/mcp-steroid](https://github.com/JetBrains/mcp-steroid) (JetBrains fork).
The [docs](https://mcp-steroid.jonnyzzz.com/docs/) have worked examples, and the
[Discord](https://discord.com/invite/e9qgQ7NeTC) is where the community is building up.

You don't need to be an IntelliJ platform expert. The agent does the API exploration. You need to
know what IDE capability you want to expose -- the rest is iteration.

## Try It

According to the [MCP Steroid strategy](https://mcp-steroid.jonnyzzz.com/docs/strategy/), we start
from an explicit plugin for IntelliJ-based IDEs and Android Studio. The long-term target is a
headless, self-contained runtime -- the IDE for AI agents without the UI. But you can use it today.

You'll need any IntelliJ-based IDE or Android Studio (version 2025.3+). Install the plugin from [GitHub Releases](https://github.com/JetBrains/mcp-steroid/releases)
-- JetBrains Marketplace listing is coming soon. Once started, the plugin generates
`.idea/mcp-steroid.md` in your project with instructions. Follow those to register the MCP Server
with your agent. The server uses the Streamable HTTP protocol.

## PoC Program

We're opening a PoC program for companies that want MCP Steroid customized for their use cases --
internal skills, proprietary API integrations, team-specific workflows. If that's interesting,
reach out to me on [LinkedIn](https://www.linkedin.com/in/jonnyzzz/).