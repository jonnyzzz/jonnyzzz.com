# MCP Steroids: An IntelliJ MCP Server with Vision

**Date:** January 04, 2026  
**Author:** Eugene Petrenko  
**Tags:** stevedore, mcp, intellij, ai-coding, developer-experience, kotlin

---

I wanted my AI agent to act like a real teammate inside IntelliJ: open a project, run inspections, click through dialogs, and keep enough context to avoid guessing. Text-only tools were not enough. So I built **MCP Steroids**.

The project grew to 253 commits over a month of intense holiday hacking. It started as a simple Kotlin script executor and evolved into a full MCP server with vision, OCR, and human review gates.

## Series: Holiday Sprint with AI

- [290 AI-Assisted Commits: My Holiday Sprint with Claude and Codex]({% post_url blog/2025-01-06-holiday-sprint-with-ai %})
- [MCP Steroids: An IntelliJ MCP Server with Vision]({% post_url blog/2026-01-04-mcp-steroids-intellij %})
- [Plugin Hot Reload: A Faster IntelliJ Dev Loop]({% post_url blog/2026-01-05-intellij-plugin-hot-reload %})
- [Roomtone: A Single-Room Call for Home]({% post_url blog/2026-01-03-roomtone-single-room-call %})

## The MCP Server Inside IntelliJ

MCP Steroids runs a Ktor server inside the IDE using.
I tried the [Kotlin MCP SDK](https://github.com/modelcontextprotocol/kotlin-sdk), but found it
does not yet support the latest MCP spec version, same as IntelliJ-native MCP Server.
For the sake of this experiment, I decided to focus on my own implementations. 

It binds to `127.0.0.1:63150` by default (configurable via registry keys). The core 
endpoint is `/mcp`, with [Agent Skills](https://agentskills.io) discovery at `/skill.md`.

On startup, the plugin writes discovery markers so tools can connect without guessing:

- `~/.<pid>.mcp-steroid` in the user home (PID-scoped, cleaned on exit).
- `.idea/mcp-steroids.txt` inside each opened project.

### Connecting AI Agents

The server works with all major AI coding CLIs: Claude Code and Codex.

## Tool Surface: The IDE as a Toolbox

The goal is simple: expose the IDE in a way an agent can actually use. The MCP surface includes:

- **`steroid_execute_code`** to run Kotlin snippets inside IntelliJ with full IDE APIs.
- **Project and window discovery** (`steroid_list_projects`, `steroid_list_windows`).
- **Capability and action discovery** (`steroid_capabilities`, `steroid_action_discovery`).
- **Vision + input** (`steroid_take_screenshot`, `steroid_input`) to drive the UI.
- **Project lifecycle** (`steroid_open_project`).

Each tool is registered via extension points, so the surface can grow without rewriting the server.

### Why Not Just LSP?

This is similar to what LSP (Language Server Protocol) provides, but IntelliJ's native APIs go deeper:

- **PSI (Program Structure Interface)** — richer code understanding than LSP's syntax trees.
- **IDE-specific features** — inspections, refactorings, intentions, quick-fixes.
- **Full project model** — module dependencies, source roots, library references.
- **Platform indices** — fast code search across the entire project.

The preference is always IDE APIs over file operations:

| Instead of...                   | Use IntelliJ API               |
|---------------------------------|--------------------------------|
| Reading files with `cat`/`read` | VFS and PSI APIs               |
| Searching with `grep`/`find`    | Find Usages, Structural Search |
| Manual text replacement         | Automated refactorings         |
| Guessing code structure         | Query project model directly   |

The IDE has indexed everything. It knows the code better than any file search.

## Execution Pipeline With a Safety Valve

Agents submit Kotlin code via `steroid_execute_code`. Scripts must call `execute { }` to interact with the IDE:

```kotlin
execute {
    waitForSmartMode()  // Wait for indexing

    val psiFile = readAction {
        PsiManager.getInstance(project).findFile(virtualFile)
    }

    writeAction {
        document.setText("new content")
    }

    println("Done!")
}
```

The `McpScriptContext` provides built-in helpers: `readAction`, `writeAction`, 
`smartReadAction`, `findFile`, `findPsiFile`, `progress`, and `takeIdeScreenshot`. 
No imports needed for the common operations.

### Human Review Gate

A review gate sits in the middle. The default mode is `ALWAYS`, which opens submitted 
code in the editor with Approve/Reject buttons. Users can edit the code before 
approval—the LLM receives the original, the edited version, and a unified diff showing what changed.

Three modes are available:
- `ALWAYS`: Every script requires human approval (default)
- `TRUSTED`: Auto-approve all (trust MCP callers)
- `NEVER`: Auto-execute all (development only)

### Execution Storage

All requests are logged to `.idea/mcp-run/` with timestamped directories containing
the script, parameters, output, and any errors. This append-only log is invaluable
for debugging agent behavior.

## MCP Resources: Built-in Examples

The server exposes pre-built examples through MCP resource APIs. These are runnable 
Kotlin scripts that agents can load and adapt, avoiding the guesswork of writing IDE code from scratch:

- **LSP-like operations**: `intellij://lsp/go-to-definition`, `find-references`, `rename`, `code-action`, `signature-help`.
- **IDE power operations**: `intellij://ide/extract-method`, `introduce-variable`, `change-signature`, `safe-delete`, `optimize-imports`, `run-configuration`.
- **Project lifecycle**: `intellij://open-project/open-trusted`, `open-with-dialogs`.

Agents call `list_mcp_resources` to discover available resources, then `read_mcp_resource` 
with the URI to fetch the content. These examples are designed to be plugged directly 
into `steroid_execute_code` after configuring file paths and positions.

### Learning Curve Note

Writing working code for IntelliJ APIs may require several attempts. This is 
expected—the API is vast. The server includes `printException()` to help debug
stack traces when errors occur. If the first attempt fails, analyze the error,
adjust, and try again. The power of direct IDE access is worth the effort.

## Vision + OCR = Context That Sticks

The vision pipeline is more than a screenshot. A single `steroid_take_screenshot` call collects:

- The PNG image (returned as base64 in the MCP response).
- The Swing component tree (`screenshot-tree.md`) for programmatic inspection.
- OCR output when enabled (Tesseract via a bundled helper app).
- Window metadata including bounds and focus state.

The `steroid_input` tool then drives the UI using a small grammar:

```
click:Left@120,200
type:Hello World
press:ENTER
stick:ALT, delay:400, press:F4
```

Coordinates are relative to the screenshot, so agents can click what
they see. The sequence supports comments (`#`) and newline separators for readability.

## Demos

Two short demos show the system in action:

<iframe width="560" height="315" src="https://www.youtube.com/embed/6p6B5sxgXX8" title="MCP Steroids demo 1" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

<iframe width="560" height="315" src="https://www.youtube.com/embed/dz95tSD9Z-c" title="MCP Steroids demo 2" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

## The Status

This is not a polished product. Some rough edges:

- The HTTP transport is JSON-only (SSE requests are rejected as older protocol version).
- Modal dialogs can cancel script execution unexpectedly.
- Every tool call is subject to IntelliJ's threading and modality rules.
- The vision tools are marked as "heavy endpoints"—prefer `steroid_execute_code` for regular automation.

But it is already useful enough to build real workflows. The 
integration tests cover Claude Code, Codex, and Gemini CLIs 
end-to-end, including a full execute→feedback→execute cycle.

## The Bigger Picture

MCP Steroids is part of my AI-assisted development setup, running 
alongside [Stevedore]({% post_url blog/2025-12-24-introducing-stevedore %}) deployments 
on my homelab infrastructure.

The goal is to make the IDE a first-class tool for AI agents—not just a text editor they talk to, 
but a full development environment they can see, navigate, and operate. There is still a lot to 
figure out about trust, safety, and useful abstractions, but this is a start.

<iframe src="https://www.linkedin.com/embed/feed/update/urn:li:activity:7416797295112839168" height="720" width="504" frameborder="0" allowfullscreen="" title="Embedded post"></iframe>

If you are experimenting with agentic tooling inside IDEs, let's connect and share notes.

**Would you like to support the project? Just let me know! via me at jonnyzzz.com**