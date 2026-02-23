# MCP Steroid Project Assessment: 75 Days, 1300+ Commits, One Plugin

**Date:** February 23, 2026  
**Author:** Eugene Petrenko  
**Tags:** mcp, intellij, ai-agents, ai-coding, developer-experience, plugin-development

---

I decided to take a step back and look at what has been built so far.

MCP Steroid started on December 10, 2025. It is an IntelliJ Platform plugin that exposes
the full IDE JVM runtime to AI Agents via the Model Context Protocol. Instead of reading and
writing files, agents can compile code, run inspections, trigger refactorings, use the
debugger, and take screenshots -- all through one MCP tool that executes Kotlin inside
the IDE's JVM -- a much more flexible, powerful, and minimalistic API an AI Agent can use.

75 days later, the numbers tell an interesting story.

## The numbers

| Metric                     | Value                      |
|----------------------------|----------------------------|
| Total commits              | 1,306                      |
| Active development days    | 52 of 75 (69% utilization) |
| Avg commits per active day | ~25                        |
| Production Kotlin LOC      | 27,505                     |
| Test Kotlin LOC            | 110,482                    |
| Test-to-production ratio   | 4:1                        |
| Gradle submodules          | 8                          |
| Releases                   | 2 tagged (0.87.0, 0.88.0)  |

The 4:1 test-to-production ratio is not an accident. The Docker-based integration tests
launch a full IntelliJ IDE in a container, connect real AI Agents (Claude Code, Codex,
Gemini CLI), and verify end-to-end MCP workflows. Arena tests run curated project
benchmarks comparing agent performance with and without the plugin.

## Architecture highlights

The core execution pipeline follows a two-phase design: compile first with an external
`kotlinc` process, then run the compiled code inside the IDE's JVM with coroutine-based
timeout enforcement. This separation means agents get compilation errors immediately
without waiting for execution.

A few technical decisions that turned out well:

- **Modal dialog race detection** -- Kotlin `select{}` races script execution against
  IDE dialog appearance. If a dialog pops up mid-execution, the script cancels and
  a screenshot goes back to the agent.
- **External Kotlin compiler isolation** -- agent scripts cannot starve the IDE's own
  Kotlin daemon. The plugin recovers automatically when the daemon dies.
- **Transport-agnostic MCP core** -- the JSON-RPC dispatcher has zero HTTP dependencies.
  The Ktor transport layer is pluggable.
- **Append-only execution storage** -- every script, compilation output, and result is
  stored as an immutable audit trail under `.idea/mcp-steroid/`.

## Quality scorecard

| Dimension                     | Score      |
|-------------------------------|------------|
| Code Organization             | 9/10       |
| Error Handling                | 9/10       |
| Test Coverage                 | 8.5/10     |
| Architectural Sophistication  | 9/10       |
| Coroutine Patterns            | 9.5/10     |
| IntelliJ Platform Integration | 9/10       |
| Extensibility                 | 9/10       |
| **Overall**                   | **8.8/10** |

Zero `runBlocking()` in production code. Proper `readAction{}`/`writeAction{}` threading.
`ProcessCanceledException` always rethrown. IntelliJ service model used correctly throughout.

## What makes this unique

MCP Steroid is the only product that gives AI Agents visual IDE access -- screenshots
with component trees, keyboard and mouse input dispatch, OCR integration. Agents operate
at the same level of semantic understanding that the IDE itself uses: type-aware symbol
search, real inspections, IDE-native refactorings, live test results.

The plugin works with Claude Code, OpenAI Codex, and Google Gemini CLI today.
Human-in-the-loop review gates are configurable per project.

## Where it is heading

Multi-IDE support is already underway (GoLand, WebStorm). The NPX proxy aggregates
multiple IDE instances. The arena benchmarking framework measures agent quality across
curated project scenarios. Enterprise deployment works via a custom plugin repository.

## Read the full assessment

The complete project assessment with detailed architecture analysis, commit theme
breakdown, competitive positioning, and executive vision is published on the
MCP Steroid documentation site:

[**Project Assessment -- 2026-02-22**](https://mcp-steroid.jonnyzzz.com/docs/project-assessment-2026-02-22/)

If you are building with AI Agents and want to give them the full IDE,
[get started with MCP Steroid](https://mcp-steroid.jonnyzzz.com/docs/getting-started/)
or [join the Slack community](https://join.slack.com/t/mcp-steroid/shared_invite/zt-3p3oq91kx-BXJng8GSXveqncFVYWUcpQ).