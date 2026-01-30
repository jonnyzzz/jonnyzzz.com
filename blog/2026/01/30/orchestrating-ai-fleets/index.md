# Orchestrating AI Fleets: When Agents Manage Agents

**Date:** January 30, 2026  
**Author:** Eugene Petrenko  
**Tags:** ai-agents, multi-agent, orchestration, automation, llm

---

For the last several days, I have made my AI Agents call each other. Claude Code, Codex, and Gemini. 
After several agentic improvements, the root prompt does the following steps:

- Instructs an agent to copy and adjust the prompt for their task
- Instructs to use the standard `run-agent.sh` start agents, log outputs
- Clearly states that the AI agent should use the script, not the embedded feature
- Starts the agent at any working folder
- One more secret ingredient to make it work, or two

One AI Agent controls the flow of a fleet of other agents. It is much better than just a bash loop, 
and I like how it performs and adapts to the task given.

Today:
- Deep research on a product topic was conducted by 16+ agents
- Code reading of a big monorepo, so the agent could understand how to implement the REST API client

Claude Code calling multiple agents on the JetBrains Space reposiotry to mine knowledge from my repositories
![Claude Code orchestrating multiple agents](/images/posts/2026-01-30-orchestrating-ai-fleets-example.png)

There is more
- Agent processes never ask me, and bother much less
- I manage to make a root AI Agent run for hours unattended
- It keeps the context small for each and avoid context rot
- One can manage 3-5 such sessions, and I want to grow this number
- The baseline is still the [https://jonnyzzz.com/RLM.md](https://jonnyzzz.com/RLM.md),
  which I based on the outcomes of my multiple experiments
- Look what I've done [MCP Steroid](https://mcp-steroid.jonnyzzz.com)

What's next? One part say -- do measurements. I will keep experimenting at the first place, 
and I need a partnership to set it up in a more scientific manner.

This work builds directly on the success of my previous experiment 
where [16 AI Agents Fixed Our Documentation Problem]({% post_url blog/2026-01-24-16-ai-agents-documentation-refactor %})
and relies heavily on the [Recursive Language Model (RLM)]({% post_url blog/2026-01-05-rlm-multi-agent-orchestration %})
methodology I established earlier this year.

The fleet is busy workin'
![AI Agent fleet busy working](/images/posts/2026-01-30-orchestrating-ai-fleets-busy-working.png)

Happy Friday!