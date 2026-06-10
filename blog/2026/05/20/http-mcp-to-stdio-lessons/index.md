# From HTTP MCP to stdio: Lessons Connecting an AI Agent to a Desktop IDE

**Date:** May 20, 2026  
**Author:** Eugene Petrenko  
**Tags:** mcp, mcp-steroid, devrig, ai-agents, ai-coding, intellij, architecture, cli

---

If you want to connect an AI Agent to a locally running desktop application — in my case the
IntelliJ family — there is one obvious idea. Run an MCP server *inside* the application. Bind it to a
port. Point the agent at that port as an HTTP MCP server. Done.

It is the obvious idea because it is the correct first idea. I built exactly that, shipped it
as part of my independent experiment, and
used it every day. It kept breaking in real workstation setups — including my own. This is the
story of why, and why the answer turned out to be the least glamorous transport in the spec:
**stdio**, behind a small CLI that does the routing.

## The obvious approach: an HTTP MCP server inside the IDE

The MCP standard defines two transports: [stdio and Streamable HTTP][mcp-transports] (the older
HTTP+SSE transport was deprecated in the 2025-03-26 spec). For a desktop app the HTTP route looks
natural — the IDE is already a long-running statefull process, so let it open a socket and answer MCP calls.

So I implemented the HTTP layer and reached for the [Ktor MCP integration in the Kotlin SDK][kotlin-sdk].
And immediately hit the first snag (state January 2026): at the time, that integration only spoke the **SSE** transport,
not the newer **Streamable HTTP** the latest spec wanted. I was stuck on a spec-version mismatch
before I had connected a single agent. (The Kotlin SDK has since grown `mcpStreamableHttp()` helpers;
back then it had not.)

The thing that saved me here was not clever code. It was **integration tests for the MCP layer**.
It was using Docker image, where an agent (claude, codex, gemini) is started and connected
to the MCP server running in the test. It asks an agent to look at the MCP tools and call them.

Every time I or an AI Agent re-implemented the transport, a test would go red and tell me I had broken the contract.
I re-did that layer more than once, and the test suite caught a regression every single time. If you
take one portable lesson from this whole post, take that one: an agent-facing protocol is exactly the
kind of surface that deserves real integration tests, because the consumer -- an LLM -- will not file a
bug report unless you ask it explicitly (which I often do)

> Good integration-test coverage of the MCP layer paid for itself many times over. 

## Where HTTP-against-a-desktop-app falls apart

The naive model assumes one user, one machine, one IDE. That is not what a real agentic-coding
workstation looks like. Here is the pile of complications, roughly in the order they bit me.

**A dynamic port at startup, with no limit on instances.** Nothing stops you from running several
instances of the same IDE at once — distinct processes, each launched with its own config directory.
A *fixed* port is therefore impossible — the first IDE would grab it and every other instance would
have to fail to bind. So each IDE has to pick its port dynamically: start
from a configurable base and increment until one is free. This is, not coincidentally, exactly how
the [IntelliJ built-in web server][intellij-port] behaves (it starts from `63342`). It works. But it
turns the port into a moving target.

**Several IDEs at once, by design.** IntelliJ is not a single app — JetBrains ships a [whole family
of IDEs][jb-products] (IDEA, PyCharm, GoLand, WebStorm, Rider, and more). One can have
two or three of them open at once; power users run more than one
instance — distinct processes with their own config directories — for different projects. Some use
EAP versions in a row with release builds. Each such IntelliJ-based IDE
process is its own MCP server on its own base-plus-increment port. (Several project *windows* in one
instance are a different axis — one port, several projects.) Now I have a *set* of endpoints to
discover and route between, not one.

**Start-order dependence.** Because the ports are assigned first-come-first-served from the base, the
port a given IDE gets depends on the order you launched everything in. To make the agent talk to a
*specific* IDE, you have to start that IDE first so it grabs the predictable port. That is a terrible
thing to ask a human to remember, and an impossible thing to ask an agent to reason about. That is
not manageable to maintain each time the port changes.

**Agents can't disambiguate identically-named MCP servers.** This was the quiet killer. You cannot
simply register five "mcp-steroid" servers with an agent and expect it to choose wisely — to the
agent they look like the same server, and it does not understand that they are different IDEs. In
practice, I ended up registering exactly one server, on the first port in the range — and then back to
the start-order ritual to make sure the right IDE owned that port.

**Nested IDEs.** Sometimes an IDE is launched *from* another IDE. Now the set of processes the MCP
server must cover is not even stable for the duration of a session.

**Agent up, IDE down.** The one that hurt the most in daily use. The agent runs for hours; the IDE
does not. I shut an IDE down to update it, or it crashed, or I just forgot to open it — and the agent
was instantly dead in the water, frequently unable to reconnect even after the IDE came back. An HTTP
client dialing a port that no longer answers has nowhere to go. The MCP Steroid implementation
specifically handles unknown sessions to keep an agent working after an IDE is restarted.

| Real-world setup                             | What HTTP-in-the-IDE breaks                            |
|----------------------------------------------|--------------------------------------------------------|
| Two instances of the same IDE                | Can't share a port; base+increment; which one answers? |
| IDEA + PyCharm + GoLand open at once         | Several servers, several ports, agent picks one        |
| "Use *this* IDE" intent                      | Depends on launch order — start it first or lose       |
| Agent registered with N identical servers    | Agent can't disambiguate; only one ends up usable      |
| IDE shut down to update while the agent runs | Agent dead, often can't reconnect                      |

None of these is fatal on its own. I worked around every one of them and kept using the tool. But the
workarounds stack into a fragile pile, and the pile is the point: HTTP-against-a-desktop-app is
fighting the environment instead of fitting it.

## The pivot: the app doesn't care about the transport

Here is the schema that unlocked everything.

> The IDE side does not care whether the bytes arrive over HTTP or stdio. MCP is MCP. The transport
> is a detail at the edge.

Instead of forcing the *application* to host the network endpoint, move all the routing and
connection-handling to a small program the agent launches directly — and let *that* talk to the IDEs
however it likes.

That program is a CLI. The agent speaks MCP to it over **stdio**: launch a subprocess, talk over
pipes. No agent-facing ports, no DNS, no firewall, no "which IDE answered?". And because the CLI owns
the routing,
it can do all the things the IDE-hosted server could not: discover every running IDE, pick the right
one, start one if none exists, and survive an IDE restarting underneath it.

In MCP Steroid this CLI is **devrig**. The agent's entire configuration becomes one stdio command;
`devrig` is the coordinator that connects to all your IDEs, regardless of how many are running. The
mechanics of what `devrig` discovers, downloads, and routes — and the screenshots — are the subject of
a follow-up, the [Level 3 post][level3]; this post is about *why* it has to exist.

```text
        Coding Agent
            │  MCP over stdio  (one subprocess, no ports)
            ▼
        devrig  ── coordinator / router ──┐
            │            │            │   │
            ▼            ▼            ▼   ▼
        IDEA #1      PyCharm       GoLand   (start one on demand if none)
```

## Why stdio + a coordinator is actually more powerful

Moving to stdio is not just "the same thing without ports." It changes what is *possible*.

**Sessionless routing, because the state lives on disk.** MCP Steroid is a *stateful* MCP — its
commands change the IDE's state (files, refactorings, run configs, etc.). That sounds like it would
*need* sticky sessions, but it is the opposite: because the durable state is in the process,
there is no MCP session to pin. Any command can be routed to **any** backend capable of
executing it. That is what makes multi-IDE-per-project realistic — GoLand handling the Go module,
an IntelliJ handling the Java service, both serving the same checkout. The one catch I am still
sharpening: the project key has to encode the *IDE type*, or the agent can't reliably tell the
GoLand-`myapp` from the IDEA-`myapp` and route to the right one. The data is there; making it obvious
to the agent is the open challenge.

**Restart resilience.** The stdio coordinator can let connections come and go. The "agent up, IDE
down" dead end stops being a dead end — `devrig` can reconnect, or start an IDE, instead of leaving the
agent staring at a closed socket. It can also provision the IDE configurations if neccessary for the project.

**Provision on demand.** Once the agent talks to a coordinator instead of a fixed socket, "no IDE is
running" stops being a dead end — the coordinator can bring one into existence for the task rather
than asking a human to "please leave the IDE open for the next four hours." How that will work once
devrig ships it is the story for the follow-up [Level 3 post][level3]; the point here is that the
architecture is what makes it possible at all.

**A path to remote.** Once the agent talks to a coordinator instead of a fixed local socket, the
particular local IDE stops being the center of the architecture. The same protocol extends to remote
IDEs — and eventually to fleets of them. That is the part I am most interested in commercially, and
the reason `devrig` itself is the thing worth promoting, not any single IDE behind it.

## Routing to a project: `project_name` and discovery

A coordinator only helps if the agent can say *which* project it means without knowing anything about
ports, process ids, or how many IDEs are open. So the most important thing the coordinator does is
turn "all the IDEs on this machine" into one flat, addressable list of projects. Two halves make that
work: **discovery** and a single addressing key, **`project_name`**.

**Discovery** is the coordinator's live picture of the world. It keeps an up-to-date view of the
IDEs running on the machine and the projects each one currently has open, as one map — every open
project, across every running IDE, in a single table. When an IDE opens or closes a project, the map
updates; the agent never has to be told.

**`project_name`** is the only thing the agent has to care about. The coordinator exposes each
discovered project under a stable name and hands the agent that list. Every project-targeting tool
takes exactly one project argument — `project_name` — and nothing else about *where* the project
lives. The agent reads the list, picks a name, and calls the tool.

The routing itself is then almost boring, which is the point. On each call the coordinator looks the
`project_name` up in its discovery map, finds the IDE that actually has that project open, and
forwards the call there — translating the exposed name back to whatever that IDE calls the project
internally. If two IDEs happen to have a project with the same name open, the coordinator makes the
exposed `project_name` unique, so the agent can still aim at exactly one. The agent addresses a name;
the coordinator does the plumbing.

This is the concrete shape of the sessionless routing above: the key is the *project*, not a session,
so any call for a given `project_name` simply lands wherever that project lives. That's the whole
trick behind "one agent, many IDEs" — the agent holds a list of names, and discovery keeps that list
honest.

## MCP, CLI, or skill? There is no single answer

One more thing the journey clarified, and I want to leave it as an open question rather than a verdict.
There is a real design-space discussion hiding under all of this: should a capability be exposed as an
**MCP** tool, a **CLI**, or an agent **skill** — or some combination, skill+CLI, skill+MCP?

These are at least three distinct axes in a multidimensional feature space, not a ranked list. Some
combinations are clearly more powerful for specific scenarios, and I do not believe there is one
correct point. The honest design move is to assume you will want several of them and factor your
architecture so that adding another surface is cheap. Choosing stdio + a CLI coordinator was partly a
bet on exactly that flexibility: the CLI is a substrate the MCP, the skills, and the human-facing
commands can all sit on top of.

Give `devrig` a try. And let me know what MCP+CLI+Skills equation looks like for you.

## What I would tell my earlier self

* **Start with the obvious transport, but treat it as a hypothesis.** HTTP-in-the-IDE was the right
  thing to try first and the right thing to abandon once the environment voted against it.
* **Match the transport to the environment, not to the protocol's defaults.** A desktop app full of
  swappable, restartable, multi-instance processes wants a subprocess-and-pipes model, not a
  server-and-port one.
* **Push routing to the edge you control.** The IDE can't own discovery sanely; a CLI the agent
  launches can.
* **Stateful-on-disk means sessionless.** That inversion is what makes many-backends routing simple.
* **Test the agent-facing layer like a public API.** Your most demanding consumer can't describe what
  you broke.

This is experimental, in-progress work — `devrig` is the go-to direction now, but I am still learning
where it bends. It has rough edges I am not hiding: a runtime prerequisite you have to satisfy by
hand, single-user assumptions, and lifecycle operations that serialize. Rather than restate the exact
version numbers here (they will move release to release), the prerequisites, the trade-offs I am
least sure about, and an explicit list of open questions are what the follow-up [Level 3 post][level3]
will cover — head there when you want to actually run it.

If you have wired an agent to a desktop app and hit a different wall than these — or solved one of
them a better way — I want to hear it. Reply on [LinkedIn][linkedin] or [Twitter][twitter], or open an
issue on [jonnyzzz/mcp-steroid][mcp-steroid]. The more concrete the workstation you describe, the more
directly it shapes what `devrig` does next.

[mcp-steroid]: https://github.com/jonnyzzz/mcp-steroid
[level3]: {% post_url blog/2026-06-02-devrig-mcp-steroid-level-3 %}
[mcp-transports]: https://modelcontextprotocol.io/specification/2025-03-26/basic/transports
[kotlin-sdk]: https://github.com/modelcontextprotocol/kotlin-sdk
[intellij-port]: https://www.jetbrains.com/help/idea/settings-tools-built-in-server.html
[jb-products]: https://www.jetbrains.com/products/
[linkedin]: https://www.linkedin.com/in/jonnyzzz/
[twitter]: https://twitter.com/jonnyzzz