# Roomtone: A Single-Room Call for Home

**Date:** January 03, 2026  
**Author:** Eugene Petrenko  
**Tags:** stevedore, roomtone, webrtc, websocket, self-hosting, homelab, typescript

---

I wanted a call link that belongs to my home, not to a calendar. One room, one URL, no meeting sprawl. That turned into **Roomtone**: a single-room call service that I can run on my own hardware.

Roomtone is open source at [roomtone](https://github.com/jonnyzzz/roomtone). It is intentionally small, but the code is real: a tiny Express server, a WebSocket control plane, and a minimal React client.

## Series: Holiday Sprint with AI

- [290 AI-Assisted Commits: My Holiday Sprint with Claude and Codex]({% post_url blog/2025-01-06-holiday-sprint-with-ai %})
- [MCP Steroids: An IntelliJ MCP Server with Vision]({% post_url blog/2026-01-04-mcp-steroids-intellij %})
- [Plugin Hot Reload: A Faster IntelliJ Dev Loop]({% post_url blog/2026-01-05-intellij-plugin-hot-reload %})
- [Roomtone: A Single-Room Call for Home]({% post_url blog/2026-01-03-roomtone-single-room-call %})

## One Room, One Socket

The server keeps in-memory room state and speaks WebSocket for join, leave, and signaling. There is no database. The room is literally one map in memory.

```ts
const wss = new WebSocketServer({
  server,
  path: "/ws",
  maxPayload: maxPayloadBytes
});
```

Clients join by name, receive the roster, and then the server drives peer updates. The UI is purposely boring: a join screen, a live status banner, a participant grid, and simple mic/camera toggles.

## Two Media Paths

Roomtone has two ways to move media:

- **WebRTC signaling** with ICE servers and an adjustable transport policy.
- **WebSocket relay** using MediaRecorder and MediaSource, wrapped in a small binary packet format.

This lets me choose between "real-time WebRTC" and a WebSocket relay that works on modern Chromium; Firefox needs WebRTC mode and Safari doesn't support WebSocket media.

## Invites and Access Control

I wrapped the room with a Telegram bot. The bot issues time-limited, RSA-signed JWT invite links for allowlisted users and chats. The server accepts the token in the query string, an Authorization header, or a cookie. Once in, the bot can poll `/participants` and notify a chat when someone joins.

## Operational Knobs

Roomtone keeps the operational surface small but explicit:

- `/health` and `/participants` for health checks and bot polling.
- `/logs` to collect client telemetry and churn signals.
- Environment-driven ICE server configuration and WebSocket payload limits.

## Why This Exists

Roomtone is not a general-purpose video platform. It is a single-room call that fits into a homelab mindset: explicit links, explicit ownership, and a clear understanding of what the code actually does.

Roomtone runs as a [Stevedore]({% post_url blog/2025-12-24-introducing-stevedore %}) deployment on my homelab, which handles the GitOps loop and keeps it updated alongside my other services.

If this sounds useful, grab the repo, run it, and let me know what breaks first.