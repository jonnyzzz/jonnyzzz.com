# 290 AI-Assisted Commits: My Holiday Sprint with Claude and Codex

**Date:** January 06, 2025  
**Author:** Eugene Petrenko  
**Tags:** stevedore, ai-coding, mcp, developer-experience, infrastructure, claude-code

---

Three weeks. Nine projects. 290+ commits with AI co-authors.

That's what happened when I decided to spend the holidays building instead of resting. From December 15th to January 6th, I worked alongside Claude Code and Codex on everything from MCP integrations to a single-room call app. The results surprised even me.

## The Numbers Don't Lie

Let me start with the raw data. Here's what the git logs show:

| Project | AI-Assisted Commits | Focus |
|---------|---------------------|-------|
| intellij-mcp-steroids | 134 | MCP server with OCR, vision |
| stevedore | 48 | Docker deployment automation |
| stevedore-dyndns | 35 | Dynamic DNS with Cloudflare |
| intellij-plugin-hot-reload | 25 | Plugin development workflow |
| roomtone | 22 | Roomtone single-room calling |
| teamcity-mcp-test | 14 | MCP debugging infrastructure |
| jonnyzzz.com-src | 8 | Documentation & blog |
| rp16g | 3 | Raspberry Pi deployment |
| test-ingress-svc | 2 | Ingress testing |

Every single one of these commits has `Co-Authored-By: Claude` or similar in the message. Not because I blindly accepted AI suggestions—but because we genuinely built these features together.

## The MCP Deep Dive: 134 Commits in Three Weeks

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) has been getting a lot of attention. Anthropic released it as a way for AI assistants to interact with external tools. I wanted to see what happens when you take MCP seriously inside an IDE.

The result is [intellij-mcp-steroids](https://github.com/jonnyzzz/intellij-mcp-steroids)—an IntelliJ plugin that exposes the IDE's full power through MCP. Full write-up: [MCP Steroids: An IntelliJ MCP Server with Vision]({% post_url blog/2026-01-04-mcp-steroids-intellij %}).

### What We Built

The plugin started simple: let Claude read files from the IDE. But it quickly grew into something more ambitious:

**OCR Integration**
```kotlin
// Screenshot metadata provider extension point
interface ScreenshotMetadataProvider {
    val type: String
    suspend fun provide(context: ScreenCaptureContext): ProviderResult
}
```

We added Tesseract OCR as a ScreenshotMetadataProvider service. Now Claude can "see" dialogs, read error messages from screenshots, and understand the visual state of the IDE. The extension point pattern lets other plugins contribute their own vision capabilities.

**Screen Capture with Context**
```kotlin
data class ScreenCaptureContext(
    val project: Project,
    val component: Component,
    val executionDir: Path,
    val collectedMetadata: List<ScreenshotMetadata> = emptyList()
)
```

This was the breakthrough. Each capture runs metadata providers that write files like `screenshot-tree.md` and `screenshot-ocr.md`. Raw screenshots plus a component tree and OCR text give Claude enough context to suggest precise UI actions.

**Project-Aware Tools**

The plugin exposes `steroid_open_project`, `steroid_execute_code`, and other tools that let Claude navigate the IDE like a developer would. Open a project, run a command, check the output—all through MCP.

### The Journey: What Actually Happened

I won't pretend this was smooth. Here are some challenges we hit:

**kotlinx.serialization Conflicts**

IntelliJ bundles its own version of kotlinx.serialization. Our plugin wanted a different version. Fixing this took longer than I'd like to admit:

```kotlin
// The fix: use IntelliJ's bundled version, not our own
// This single line change took 4 hours to figure out
compileOnly("org.jetbrains.kotlinx:kotlinx-serialization-json")
```

**Extension Point Discovery**

IntelliJ's extension point system is powerful but under-documented. Claude helped me explore the API surface, but we still had to reverse-engineer some behaviors from the platform source code.

**Modality State Madness**

Modal dialogs in IntelliJ block certain operations. We added a `ModalityStateMonitor` that listens for modal dialogs, captures a screenshot, and returns `ModalDialogInfo` when execution gets blocked.

## Stevedore: Infrastructure That Updates Itself

[Stevedore](https://github.com/jonnyzzz/stevedore) is my Docker deployment tool. Over the holidays, it learned some new tricks. The deeper story lives in the Stevedore series: [Stevedore: GitOps for your Raspberry Pi]({% post_url blog/2025-12-24-introducing-stevedore %}), [Under the Hood: How Stevedore Works]({% post_url blog/2025-12-24-stevedore-architecture %}), [Tutorial: Deploying Your First App with Stevedore]({% post_url blog/2025-12-24-getting-started-with-stevedore %}), [Production Notes]({% post_url blog/2026-01-01-production-raspberry-pi-deployment %}), and [Stevedore DynDNS]({% post_url blog/2026-01-02-stevedore-dyndns %}).

### Self-Update Without Downtime

The v0.8.0 release added self-update capability. Stevedore can now sync its own repo, build a new image, and restart itself:

```bash
stevedore self-update
# Sync repo, build new image, replace container
```

This required careful orchestration. The build runs in the foreground, then an update worker container stops/removes the old container and starts the new one. Health checks are still on the roadmap.

### Cross-Deployment Communication

Each Stevedore daemon exposes a local query socket for status and long-polling:

```go
mux.HandleFunc("/status/", qs.handleStatus)
mux.HandleFunc("/poll", qs.handlePoll)
```

This powers local change notifications: `/poll` wakes up when a deployment changes. Typed events are scaffolded but not emitted yet.

### Dynamic DNS with mTLS

The stevedore-dyndns companion project got a major upgrade. It now supports Cloudflare proxy mode with Authenticated Origin Pull (mTLS) enforced by Caddy:

```bash
stevedore param set dyndns CLOUDFLARE_PROXY true
# Caddy enforces client_auth with /etc/cloudflare/origin-pull-ca.pem
```

## Plugin Hot Reload: Faster IntelliJ Development

If you develop IntelliJ plugins, you know the pain: change code, rebuild, restart IDE, wait, test, repeat. The [intellij-plugin-hot-reload](https://github.com/jonnyzzz/intellij-plugin-hot-reload) project fixes this. Full write-up: [Plugin Hot Reload: A Faster IntelliJ Dev Loop]({% post_url blog/2026-01-05-intellij-plugin-hot-reload %}).

It exposes an HTTP endpoint that accepts plugin ZIPs and hot-reloads them:

```bash
# From your build script
curl -X POST http://localhost:63342/api/plugin-hot-reload \
     -H "Authorization: Bearer <token>" \
     --data-binary @build/distributions/my-plugin.zip
```

The token and URL live in `~/.<pid>.hot-reload` once the IDE starts. The IDE stays running. Reload usually works, and when it doesn't the endpoint tells you a restart is required. Iteration time drops from minutes to seconds.

The trickiest part was handling plugin unload correctly. IntelliJ's plugin system wasn't designed for repeated unload/reload cycles. We had to:

1. Resolve the plugin ID and reject self-reload
2. Verify unloadability and call the correct unload API (there are multiple!)
3. Install the new plugin from the ZIP
4. Handle the case where unload or install fails gracefully

## Roomtone: A Single-Room Call

[Roomtone](https://github.com/jonnyzzz/roomtone) became the holiday sprint home project. It is a single-room video call service with a tiny Express + WebSocket server: you join by name, get the roster, and the server either forwards MediaRecorder chunks over WebSocket or switches to WebRTC signaling with ICE servers based on config. The UI stays intentionally minimal with a join screen, live status, a participant grid, and simple mute/camera controls. Full write-up: [Roomtone: A Single-Room Call for Home]({% post_url blog/2026-01-03-roomtone-single-room-call %}).

I wrapped it with a Telegram invite workflow. The bot issues time-limited, RSA-signed JWT links to allowlisted users and chats, and the server validates the token (query/header/cookie) before letting someone in. The bot can also poll `/participants` and notify a chat when someone joins.

Concrete bits from the code:
- WebSocket room protocol for join/welcome, peer join/leave, and signaling.
- Dual media paths: WebRTC with ICE servers/policy or WebSocket relay with MediaRecorder + MediaSource.
- Signed invite auth via JWT in query/header/cookie plus secure auth cookies.
- Telegram bot allowlists, invite links, and participant notifications.

## The Documentation Sprint

Between building features, I spent time documenting the patterns we discovered.

### RLM.md: Recursive Language Models

The [RLM paper](https://arxiv.org/abs/2512.24601) describes how to handle context that exceeds model limits. I wrote a practical implementation guide that AI agents can follow:

```
PROTOCOL:
1. ASSESS  --> Peek, don't read everything
2. DECIDE  --> Match context type + task to strategy
3. DECOMPOSE --> Partition at natural boundaries
4. EXECUTE --> Parallel if independent, sequence if not
5. SYNTHESIZE --> Merge, dedupe, resolve conflicts
6. VERIFY  --> Check completeness and accuracy
```

### MULTI-AGENT.md: Orchestration Patterns

When one agent isn't enough, spawn more. The multi-agent guide covers patterns for parallel research, pipelines, cross-validation, and more.

## What I Learned About AI-Assisted Development

After 290+ commits with AI co-authors, some observations:

### The Good

**Speed on Known Patterns**

When the task matches something the AI has seen before, the speed is remarkable. Boilerplate code, test scaffolding, documentation—these fly by.

**Exploration Partner**

"What APIs does IntelliJ have for X?" became a conversation, not a documentation hunt. Claude would suggest approaches, I'd try them, we'd iterate.

**Consistency**

The code style stayed consistent across sessions. The AI remembered our patterns and applied them.

### The Challenges

**Context Window Management**

Large projects require careful context management. I learned to keep CLAUDE.md files updated with project-specific instructions.

**Novel Architecture**

When I needed something the AI hadn't seen before, progress slowed. The OCR integration required more human guidance than I expected.

**Review Still Matters**

Every commit got reviewed. AI-generated code can have subtle bugs that only become obvious when you understand the domain deeply.

## The Tools I Used

**Claude Code** (Claude Opus 4.5)

Main development partner. Handles complex reasoning well, good at understanding project context.

**Codex**

Used for focused, non-interactive tasks. Good for processing files, generating boilerplate.

**Gemini**

Occasionally used for cross-validation—having a different model review code catches different issues.

The workflow: Claude Code for interactive development, with occasional handoffs to Codex for batch operations.

## What's Next

The MCP plugin needs more testing with real users. Stevedore needs documentation for the new features. Roomtone needs time in the wild to shake out real-network edge cases.

But the biggest takeaway isn't about any specific project. It's about the workflow.

AI-assisted development isn't about replacing human judgment. It's about amplifying human capability. The 290 commits didn't write themselves—they emerged from a continuous conversation between human intent and machine execution.

Three weeks. Nine projects. One intense holiday sprint.

Want to try these tools yourself?

- [intellij-mcp-steroids](https://github.com/jonnyzzz/intellij-mcp-steroids) - MCP integration for IntelliJ
- [stevedore](https://github.com/jonnyzzz/stevedore) - Docker deployment automation
- [intellij-plugin-hot-reload](https://github.com/jonnyzzz/intellij-plugin-hot-reload) - Faster plugin development

Find AI-generated bugs. Open issues. Submit PRs. Let me know via [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) or [Twitter](https://twitter.com/jonnyzzz) what you think.

And if you spent your holidays building too—I'd love to hear what you made.