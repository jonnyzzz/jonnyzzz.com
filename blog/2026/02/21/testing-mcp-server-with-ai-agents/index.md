# Testing Your MCP Server with Real AI Agents in Docker

**Date:** February 21, 2026  
**Author:** Eugene Petrenko  
**Tags:** ai-agents, ai-coding, mcp, testing, developer-experience, docker

---

The only way to know your MCP server actually works is to test it with a real AI Agent.

Unit tests can tell you whether a JSON schema is valid.
Mock tests can verify your handler returns the right bytes, and can deviate from the logic.
But none of them tell you whether an AI Agent will actually discover your tool,
call it correctly, and do something useful with the result.

The core insight that drove our testing approach:

> **Tests should be assertions about the agentic loop itself** -- not just about
> individual functions. A test that passes only when a real agent, starting from
> a cold container, successfully discovers and calls your tool is the only test
> that proves the contract is real.

We built this for [mcp-steroid][mcp-steroid], an MCP server that gives AI Agents deep
access to IntelliJ IDEA. The server has dozens of tools. Each agent CLI handles
MCP registration, tool discovery, and streaming output differently. The only way to catch
regressions was to test with real agents.

So we did.


## The Architecture

The test setup has three moving parts:

- **The MCP server** runs inside the IntelliJ test process on the host machine,
  listening on random port, say `0.0.0.0:17820`
- **The AI Agent** runs inside a Docker container
- **Docker networking** connects them: `host.docker.internal` resolves to the host from inside
  any container

When the test starts, it binds the MCP server to all interfaces (not just `localhost`),
so it is reachable from the Docker network. The container gets started with
`--add-host=host.docker.internal:host-gateway`, which maps that hostname to the
host gateway address. The test then translates the MCP URL from `localhost:17820`
to `http://host.docker.internal:17820` before handing it to the agent.

```
┌──────────────────────────────────────────────────────┐
│  Host machine                                        │
│                                                      │
│  JVM test process                                    │
│  ┌──────────────────────────────────────────────┐    │
│  │  IntelliJ test framework                     │    │
│  │  MCP server: 0.0.0.0:17820                   │    │
│  └──────────────────────────────────────────────┘    │
│                              ▲                       │
│                              │ host.docker.internal  │
└──────────────────────────────┼───────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────┐
│  Docker container            │                       │
│                              │ HTTP/SSE              │
│  AI Agent CLI ───────────────┘                       │
│  (Claude / Codex / Gemini)                           │
└──────────────────────────────────────────────────────┘
```

The test class wires this together before each test:

```kotlin
override fun setUp() {
    // Bind server to all interfaces, not just localhost
    System.setProperty("mcp.steroid.server.host", "0.0.0.0")
    System.setProperty("mcp.steroid.server.port", "17820")
    super.setUp()
}

private fun resolveDockerUrl(): String {
    val mcpUrl = SteroidsMcpServer.getInstance().getSseUrl()
    // Replace localhost with the Docker-accessible hostname
    return mcpUrl
        .replace("localhost", "host.docker.internal")
        .replace("127.0.0.1", "host.docker.internal")
}
```

Each agent session lives inside a Docker container. The container starts once, receives
the MCP registration command, and then runs prompts via `docker exec`. The container
is reused across calls within a single test.

Basically, each AI Agent container starts with `sleep infinity` command as the entrypoint, 
and we use `docker exec` commands to start various processes inside, even IntelliJ IDEA or Git.


### API Keys

The agent containers need API keys to talk to their respective model providers.
We pass them as environment variables when running commands inside the container.
The test harness reads the key from the environment and creates environment
variables internally -- `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`.
The key is injected only into the `docker exec` call, never stored in the image.
We also redact the key from all log output so it doesn't leak into CI logs.

## Claude Code -- `--verbose` or You Are Flying Blind

### The Dockerfiles

All three containers follow the same structure: Node.js 20 base, install the agent CLI,
non-root user. The only difference is the npm package name.

```dockerfile
FROM debian:bookworm-slim

# ── Node.js 20 via NodeSource
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl ca-certificates gnupg && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | \
        gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] \
          https://deb.nodesource.com/node_20.x nodistro main" \
        > /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# ── Agent CLI -- swap this line per agent
RUN npm install -g @anthropic-ai/claude-code   # Claude Code
RUN npm install -g @openai/codex               # Codex
RUN npm install -g @google/gemini-cli          # Gemini

# ── Non-root user for isolation
RUN useradd -m -s /bin/bash agent
USER agent
WORKDIR /home/agent

# ── Keep the container alive; commands run via docker exec
CMD ["sleep", "infinity"]
```

The container starts with `sleep infinity` and stays alive.
All commands run via `docker exec` -- the container is never restarted between calls.

### MCP Registration

Before running any prompt, we register the MCP server:

```
claude mcp add --transport http intellij http://host.docker.internal:17820
```

### Running a Prompt

Claude Code has a non-interactive mode (`-p`) with streaming JSON output:

```
claude \
  --permission-mode bypassPermissions \
  --tools default \
  --input-format text \
  --output-format stream-json \
  --verbose \
  -p "List the MCP tools and call steroid_list_projects"
```

The `--output-format stream-json --verbose` flags are essential.
Without them, Claude only emits the final text response after the agent finishes.
We want to see if the Claude process is alive, and thus the verbose output with
progress messages is very essential.
With them, every event streams to stdout as NDJSON (one JSON object per line)
in real time: assistant messages, tool calls, tool results, token usage.
This is what makes debugging tests tractable -- you see exactly what the agent did.

### Parsing the JSON Output

Claude Code's `stream-json` format is event-driven. Tool calls are nested inside
`assistant` message events (in the current format), and the final `result` event
carries cost and timing:

```json
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"I'll list..."}]}}
{"type":"assistant","message":{"content":[{"type":"tool_use","name":"steroid_list_projects","input":{}}]}}
{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"...","content":"..."}]}}
{"type":"result","cost_usd":0.0042,"duration_ms":3200,"num_turns":2}
```

We parse this with a streaming NDJSON loop that routes on `type`.
Tool calls render as `>> steroid_list_projects`, tool results as `<< steroid_list_projects`,
assistant text prints as-is, and cost appears at the end.
We never buffer the full output -- lines are processed as they arrive.


## Codex -- stderr Will Fool You

### MCP Registration

```
codex mcp add intellij --url http://host.docker.internal:17820
```

### Running a Prompt

Codex uses the `exec` subcommand for non-interactive batch mode:

```
codex exec \
  --dangerously-bypass-approvals-and-sandbox \
  --skip-git-repo-check \
  --json \
  "List the MCP tools and call steroid_list_projects"
```

The `--json` flag makes Codex emit NDJSON to stdout.
Without it, you get the interactive terminal UI -- not useful inside a test.
The `--dangerously-bypass-approvals-and-sandbox` flag disables safety confirmation
prompts so the agent can run without blocking on human input.

### Parsing the JSON Output

Codex's format uses `item` events:

```json
{"type":"item.started","item":{"type":"mcp_tool_call","name":"steroid_list_projects"}}
{"type":"item.completed","item":{"type":"agent_message","text":"I found the following tools..."}}
{"type":"item.completed","item":{"type":"mcp_tool_call","name":"steroid_list_projects","output":"..."}}
{"type":"turn.completed","usage":{"input_tokens":400,"output_tokens":200}}
```

We route on `item.type`. The `mcp_tool_call` items show us tool invocations.
The `agent_message` items (with a flat `text` field) give us the assistant's text.
`turn.completed` shows token usage.

One thing that burned us early: **Codex writes to stderr in some modes and stdout in others**.
In `--json` mode, structured events go to stdout and plain diagnostic messages go to stderr.
We spent a week thinking our output filter was broken before we realized we were reading
the wrong stream. We now capture both streams separately and only parse stdout as NDJSON.


## Gemini -- Exit Code 137 Is Actually Fine

### MCP Registration

Gemini's registration syntax is the most verbose. It requires `--type http`,
`--scope user`, and `--trust` to avoid interactive confirmation:

```
gemini mcp add intellij \
  --type http \
  http://host.docker.internal:17820 \
  --scope user \
  --trust
```

### Running a Prompt

```
gemini \
  --screen-reader true \
  --sandbox-mode none \
  --approval-mode yolo \
  --output-format stream-json \
  --prompt "List the MCP tools and call steroid_list_projects"
```

The `--approval-mode yolo` disables tool-use confirmation prompts.
The `--screen-reader true` flag suppresses ANSI terminal formatting.

Note: newer Gemini CLI versions replaced `--sandbox-mode none` with `--sandbox false`.
We handle this with a simple retry -- if the first attempt fails with
`unknown arguments: sandbox-mode`, we retry with `--sandbox false`.
This keeps the tests passing across CLI version bumps without needing to pin an exact version.

### Parsing the JSON Output

Gemini's format uses typed events with field names that differ from Claude's:

```json
{"type":"message","role":"assistant","content":"I'll start by listing...","delta":true}
{"type":"tool_use","tool_name":"steroid_list_projects","tool_id":"tool-1","parameters":{}}
{"type":"tool_result","tool_id":"tool-1","tool_name":"steroid_list_projects","status":"success","output":"..."}
{"type":"result","status":"success","stats":{"input_tokens":800,"output_tokens":400,"tool_calls":2,"duration_ms":1200}}
```

A few quirks worth knowing:
- `message.content` is a plain string, not an array -- unlike Claude's format
- Tool calls use `tool_name` and `parameters`, not `name` and `input`
- The `result` stats have separate `input_tokens` and `output_tokens`, not a combined total

One more surprise: **Gemini CLI occasionally exits with code 137 (SIGKILL) even after
successfully completing a request**. We detect this by checking the raw NDJSON for
`"status":"success"` and treating exit code 137 as success when that signal is present.
Without this guard, valid runs fail spuriously about 5% of the time.

The Gemini API also drops the socket mid-stream on transient errors
(`UND_ERR_SOCKET`, `terminated`). We retry once when we see these patterns.
Transient infrastructure failures shouldn't count as test failures.


## What a Passing Test Looks Like

The test prompts the agent with explicit instructions and then asserts on the output:

```kotlin
fun testDiscoversSteroidTools() = timeoutRunBlocking(300.seconds) {
    val result = session.runPrompt("""
        List all MCP tools starting with "steroid_" and print each as:
        TOOL: <name> - <description>

        Then call steroid_list_projects exactly once and print the result as:
        PROJECTS: <raw JSON>
    """)
    .assertExitCode(0, "prompt")
    .assertNoErrorsInOutput(message = "prompt")

    assertTrue(result.output.contains("PROJECTS:"))
    assertTrue(result.output.contains(project.name))
    assertTrue(result.output.contains(project.basePath.toString()))
}
```

The structured output format (`TOOL:`, `PROJECTS:`) makes assertions mechanical.
The test fails if the agent hallucinates a tool call, misreads the MCP response,
or doesn't actually invoke the tool. That is precisely the contract we want to enforce.

We run all three agents against the same test cases. This has surfaced real differences:
tools with ambiguous descriptions that Claude calls correctly but Gemini mis-calls,
JSON response shapes that Codex handles but another rejects, and timeout boundaries
that only appear under real container-to-host network latency.


## The Development Loop

Before we had these tests, adding a new MCP tool meant:
1. Implement the tool handler
2. Start IntelliJ manually, open Claude Code, hope the tool showed up
3. Try a prompt and see if it worked
4. Debug output format issues in the UI
5. Repeat -- usually four or five times

With integration tests, the loop is:
1. Implement the tool handler
2. Run `./gradlew :ij-plugin:test --tests "*CliClaudeIntegrationTest*"`
3. Read the test output -- the full NDJSON-filtered agent transcript is there
4. Fix what's broken, re-run

Faster. Reproducible. And it runs in CI without any human in the loop. It runs inside
Agentic loop too.

> Having real end-to-end tests with real AI Agents is the fastest feedback loop
> we have found for MCP server development. The 60 seconds it takes to spin up
> a Docker container is cheaper than the 10 minutes of manual testing it replaces.


## Container Lifecycle

One infrastructure detail worth mentioning: we use a lightweight reaper container
to handle cleanup. When the test JVM exits or gets killed with SIGKILL, we need
all agent containers cleaned up. The reaper registers containers via a simple
TCP socket protocol (`container=<id>` messages) and kills them all when the
connection drops.

This means test runs don't leave orphaned Docker containers even when the process
is forcibly terminated during development or in CI.


## What This Enables

This approach enables the **Agentic Loop**, the way to make your coding
agents receive instant feedback from the tests. My AI Agents broke these
tests multiple times, and thanks to the tests, we were able to recover/rollaback,
without breaking the real production. Integration tests, and the testing itself,
is the vital building block, especially when AI Agents write the most of the code.

The test harness is part of [mcp-steroid][mcp-steroid]. If you want to build
your own MCP server for IntelliJ, the same infrastructure is available.
You can write a test that starts the real IDE, registers your server,
and runs a real AI Agent against it -- all from a single `./gradlew test` command.

We've used this to test over 20 distinct tools across three agent CLIs,
catching dozens of issues that would have been invisible in unit tests:
tools with ambiguous descriptions that agents mis-call, JSON response shapes
one CLI handles but another rejects, and timeout boundaries that only show up
under real network latency between host and container.

While writing tests for every tool, we also noticed something else. Some tools were
so simple that the agents could have called them just as well through a shell command.
That observation turned into a broader question.


## MCP Is One Way

MCP Server is not the only way to give AI Agents access to your tools.

In a [recent post about CLI tools for AI Agents][cli-post], I wrote about how well-designed
command-line interfaces are often sufficient. Agents already know how to run shell commands,
parse text output, and chain calls. If your tool has a good CLI, you may not need
an MCP server at all.

For [mcp-steroid][mcp-steroid], MCP made sense: we need structured tool calls,
streaming data, and tight IDE integration that a CLI cannot provide. But for many tools --
build systems, package managers, code search, deployment pipelines -- a CLI
is simpler to build, simpler to test, and works with every agent out of the box.

The question to ask is not "should I build an MCP server?" but "what interface
does an AI Agent need to use this tool reliably?" Sometimes that is MCP.
Sometimes it is a shell command. And sometimes it is both.

If you are building an MCP server and want to share how you tested it, I'd like to hear
about it -- reach out on [LinkedIn][linkedin] or [Twitter][twitter].


[mcp-steroid]: https://mcp-steroid.jonnyzzz.com
[cli-post]: {% post_url blog/2026-02-20-cli-tools-for-ai-agents %}
[linkedin]: https://www.linkedin.com/in/jonnyzzz/
[twitter]: https://twitter.com/jonnyzzz