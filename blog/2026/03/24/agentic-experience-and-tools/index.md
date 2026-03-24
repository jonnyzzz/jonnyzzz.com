# Agentic Experience and Tools: My Program

**Date:** March 24, 2026  
**Author:** Eugene Petrenko  
**Tags:** ai-agents, mcp, ai-coding, developer-experience, agentic-experience

---

> AI Agents can think. They cannot always act. I build the **bridges** between
> agent intelligence and the real-world tools that agents cannot reach.

I have spent twenty+ years at [JetBrains](https://jetbrains.com) making software developers more
productive. I started [IDE Services](https://www.jetbrains.com/ide-services/) from zero, grew 
it to 500+ enterprise customers, and handed it to the team. I have given fifty-plus [talks](/talks) on developer
tooling around the world. **I am a founder** -- I create products, take them
from inception to stable results, and move on to the next thing. That is
what drives me.

In late 2025 I saw a shift. AI Agents crossed a threshold. They could read
code, reason about architecture, propose changes, write tests, iterate
on feedback, deploy services. The intelligence was there.

But agents live in a world of tokens and text. Our development
infrastructure -- IDEs, CI pipelines, code review systems, debuggers --
lives in the human world. Agents cannot run your IDE's thousand
inspections. They cannot trigger your CI pipeline. They cannot start a
debugger. They cannot navigate your code review system or debug your GUI app.

The gap between what agents can think and what they can do is the
defining bottleneck of this era. **I am building the bridges that close it.**

I call this domain **Agentic Experience & Tools**. For me, I work in that domain
and in the scope of exiting old products, where Agentic Experience and Tools are the most
challenging to deliver.

## The Mission: Agentic Experience & Tools

I make AI Agents more effective at solving problems on real-world projects
by building the missing connections between agents and existing tools,
processes, and infrastructure -- including optimizing how agents work
together, which models they use, and how they learn from their own runs.

> The AI Agent is not an implementation detail. **It is the user,** and the product persona.
> The human is the stakeholder.

The biggest **misconception** I see: people keep designing products for
humans with AI tools bolted on. I am doing the opposite. I build products
intended directly for agentic usage. No UX, no UI in the traditional
sense -- APIs, [CLIs][cli-post], [MCPs](https://modelcontextprotocol.io/), and
structured outputs that agents consume natively. Humans buy and install
these tools to improve the performance metrics of their agents. Later,
other AI Agents may do the buying too.

Only agents can validate what is actually better for agents. So I use an
agentic learning process: agents define the evaluation, run it, and
self-improve based on collected data. When I built the
[MCP Steroid][mcp-steroid] debugger, one agent ran
the debug task through IntelliJ while another reviewed the logs and
rewrote the prompts. Multiple times. After iterations, the agent went from failing --
falling back to screenshots just to see what was happening -- to solving
the debug task on the first attempt. That is the kind of improvement I
am after: measurable, agent-validated, compounding.

I do not compete with AI Agents. I make every agent better. Whatever your
team already uses -- Claude, Codex, Gemini, Junie, Cursor, Augment, Kilo --
my tools remove the walls between that agent and your development
infrastructure. I integrate with all of them. I replace none of them.
When there is no AI Agents in use, I enable them.

## The Agentic Loop

Agents need real-world feedback: build the code, run the tests, deploy
to staging. Once these loops are established, agents iterate on their
own, improving quality with each pass.

**The principle: agents follow the same processes as humans.** No
shortcuts. No special agent-only paths. That is what makes the output
trustworthy. The human decides how much autonomy to grant, and signs off
on the result.

## What Is Still Broken

**Agents cannot react to events yet.** Today, a human kicks off agent
runs. Agents should wake up automatically when a CI build fails, a code
review gets comments, or a merge pipeline completes. I am looking for
design partners to implement event-driven workflows.

**Setup takes too long.** Configuring the full stack is a 30-minute
process. The goal is one Docker command to start.

**Agents do not learn enough from failures.** Every agent run generates
telemetry. That data should feed back automatically -- agents reporting
problems to other agents that fix them.

## What I Have Built

I have built a portfolio of tools that address different parts of the gap:

[MCP Steroid][mcp-steroid] gives agents access to
the full IntelliJ IDE runtime -- inspections, refactorings, debugger,
screenshots. On DPAIA benchmarks, agents with MCP Steroid are
[20-54% faster][mcp-steroid] on tasks requiring
semantic understanding and multi-file refactoring. It works with Claude,
Codex, Gemini, Cursor, and any MCP client. See it in action: the
[demo playlist](https://youtube.com/playlist?list=PLitZWClhc4Qgz3w8qrtctMR_lpIc81n0f)
includes debugger integration, monorepo deep dives, and more.
[Try it](https://mcp-steroid.jonnyzzz.com/releases/) on your IDE today.

[run-agent.sh][run-agent] orchestrates agent
swarms with full isolation and traceability -- up to 16 agents in
parallel, coordinating through an append-only
[message bus](https://run-agent.jonnyzzz.com/MESSAGE-BUS.md).

[RLM][rlm] decomposes tasks that exceed one
context window into sub-agent work.

Dedicated posts about each are coming.

## Find the Others

I am looking for the people who are actually doing this -- not
theorizing, not pitching, but deploying agents on real codebases and
hitting real walls.

**If your agents are stuck** -- they can generate code but cannot get it
reviewed, tested, merged, or deployed -- I want to hear about it. That
is the exact gap I work on.

**If you are building tools that agents use**, I want to compare notes.
What works, what breaks, what the models still cannot do.

Join the conversation and follow me on [LinkedIn][linkedin] -- that
is where most of the discussion happens.

---

Andrej Karpathy on the [No Priors podcast](https://podcasts.apple.com/us/podcast/no-priors-artificial-intelligence-technology-startups/id1668002688)
(March 2026): 

> Just I think everything, like so many things, even if they
> don't work, I think to a large
> extent you feel like it's a skill issue.
> It's not that the capability is not there; it's that you
> just haven't found a way to string together what's available. Like, I
> didn't give good enough instructions to the agents.

---

The agents are capable. 

**The bridges are missing. I build them.** Reach out on [LinkedIn][linkedin] or [X][x].

[mcp-steroid]: https://mcp-steroid.jonnyzzz.com/
[run-agent]: https://run-agent.jonnyzzz.com/
[rlm]: {% post_url blog/2026-01-05-rlm-multi-agent-orchestration %}
[cli-post]: {% post_url blog/2026-02-20-cli-tools-for-ai-agents %}
[linkedin]: https://www.linkedin.com/in/jonnyzzz/
[x]: https://x.com/jonnyzzz