# Plugin Hot Reload: A Faster IntelliJ Dev Loop

**Date:** January 05, 2026  
**Author:** Eugene Petrenko  
**Tags:** intellij, plugin-development, hot-reload, kotlin, developer-experience

---

Restarting IntelliJ for every plugin tweak is a productivity tax. The wait breaks flow, and by the time the IDE is back up you've lost the tiny detail you were trying to test. I wanted a tighter loop, so I built **intellij-plugin-hot-reload**.

## Series: Holiday Sprint with AI

- [290 AI-Assisted Commits: My Holiday Sprint with Claude and Codex]({% post_url blog/2025-01-06-holiday-sprint-with-ai %})
- [MCP Steroids: An IntelliJ MCP Server with Vision]({% post_url blog/2026-01-04-mcp-steroids-intellij %})
- [Plugin Hot Reload: A Faster IntelliJ Dev Loop]({% post_url blog/2026-01-05-intellij-plugin-hot-reload %})
- [Roomtone: A Single-Room Call for Home]({% post_url blog/2026-01-03-roomtone-single-room-call %})

## The Endpoint

The plugin registers a built-in server handler at:

```
/api/plugin-hot-reload
```

- `GET` returns a Markdown README packaged inside the plugin.
- `POST` accepts the raw plugin ZIP as the request body.

The handler is strict: it requires `Authorization: Bearer <token>` and rejects empty uploads. The token changes each IDE run, which keeps the endpoint local and short-lived.

## Discovery and Auth

On startup, the plugin writes a marker file to the user home directory:

```
~/.<pid>.hot-reload
```

It contains the POST URL, the bearer token, a timestamp, and a full IDE "About" block. The file disappears on IDE exit and stale marker files are cleaned up automatically. The Gradle `deployPlugin` task scans these markers and pushes new ZIPs to running IDEs.

## The Reload Pipeline

The reload flow is intentionally explicit:

1. Read the plugin ZIP and extract the plugin ID (supports nested JAR layouts).
2. Reject self-reload to avoid unloading the hot-reload plugin itself.
3. Unload the existing plugin via the dynamic plugin API.
4. Replace the plugin directory on disk.
5. Install and load the new plugin descriptor.

If unload fails, the service can capture an HPROF snapshot and returns `restartRequired = true`. The endpoint always finishes with a final `SUCCESS` or `FAILED` line so callers can automate around it.

## The Fine Print

There are some intentional quirks:

- The response is chunked, but progress is buffered and sent once at the end (no streaming updates).
- Requests time out after 5 minutes; a timeout still returns `FAILED`.
- A short 5-second delay is added after reload to let background invocables finish.

This is experimental and intentionally tied to IntelliJ internals. It works, but it is not guaranteed to survive major IDE releases without updates.

If you want the code, it is here: [github.com/jonnyzzz/intellij-plugin-hot-reload](https://github.com/jonnyzzz/intellij-plugin-hot-reload).

<iframe src="https://www.linkedin.com/embed/feed/update/urn:li:activity:7407749413877739520" height="520" width="504" frameborder="0" allowfullscreen="" title="Embedded post"></iframe>