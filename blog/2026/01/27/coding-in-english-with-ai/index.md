# Coding in English with AI

**Date:** January 27, 2026  
**Author:** Eugene Petrenko  
**Tags:** ai, coding, future, ai-agents, multi-agent, sub-agent

---

About a year ago, I was wondering when programming would move to natural languages, and what it would look like.
**Now I know**. For the last two months, English has become my main coding language to instruct AI agents,
build pipelines, and architect systems. **I'm coding in English to make AI Agents code in code.**

----

Running sub-agents is the new trend. We move from `$ralph` towards a multiple-agent swarm, 
where an agent calls sub-agents and monitors the outcomes.
ClaudeCode and Codex (and other vendors) recently included sub-agent support, too.
You make bigger tasks smaller by running sub-agents, and only if the whole chain of command can start sub-agents 
do we have the ability to split tasks, iterate, and so on.

My main challenge is to check whether an agent can control sub-agents, 
so instead of a bash or Python loop, we put a managing agent at the top who will review 
the outcomes and decide on the next step.

The whole agentic development process starts to look like an agentic waterflow workflow of many activities, each of which
is done my various AI agents, or even multiple agents, with multiple various 
agentic roles, repeats, and cycles. Should something go wrong, it should restart. 
I created a ~10-step instruction locally for a 25-year-old monorepo and keep testing it to see how
it goes. Agents tend to use the native sub-agent implementation instead of running the console 
script, so I need to explain more carefully that I need processes created. Running sub agent
as sub process gives the sub agent more power, another working directory, another `CLAUDE.md/AGENTS.md`,
different MCP Servers, and much more fresh context. And we can switch between different agents
within the same waterflow.

After all iterations and tuning, it looks like Codex can do that better. Sometimes it falls back
to native sub-agent implementation. And my goal is to make agentic swarm function by itself
most of the time. Agents should cooperate to decide on the complex problems, research for solutions.

Agents can fix your prompts, that is how I improved mine as well. Just ask it to start all 
supported agents to interview them for problems and suggestions. Process outcomes with agents.

With that, I came to the next question: how can one monitor the graph of agents running? Not that I 
want to interact, just out of curiosity. Agents helped me create the monitoring scripts for 
that, so now I can see all agents started. Such code
is cheap, and experimentation is not blocked by that.

Today, I have multiple code repositories of **prompts**. I task selected agents to write prompts 
for their sub-agents. I version-control and back-up kilobytes of prompts. I ask agents
to interview agents on selected agentic integration topics. And of course some agents
will code, run tests in IntelliJ via the [MCP Steroid](https://mcp-steroid.jonnyzzz.com/)
plugin, debug the code and so on. 

We are approaching a shift where AI Agents become the primary users of software development tools.
The 'Buying Persona' remains human, but the 'User Persona' is becoming digital. Tools must
now be optimized for agentic consumption — APIs first, GUIs second.

---- 

About a year ago, I was wondering when programming would move to natural languages, and what it would look like.
**Now I know**. For the last two months, English has become my main coding language to instruct AI agents,
build pipelines, and architect systems. **I'm coding in English to make AI Agents code in code.**

**I'm coding in English to make AI Agents code in code.** 

----

## Instead of Conclusion
Below is what Gemini 3 told me

The landscape of software development is undergoing a seismic shift. For decades, learning to code 
meant mastering syntax, understanding memory management, and debugging cryptic error messages. Today, 
with the rise of powerful AI models, the most important programming language might just be English.

### The Shift from Syntax to Semantics

Traditionally, developers acted as translators, converting human intent into machine-readable 
code. AI agents are now taking over this translation layer.

### Prompt Engineering as the New Coding

Writing clear, unambiguous instructions—prompt engineering—is becoming a critical skill. It 
shares many principles with traditional coding: precision, modularity, and iterative refinement.

### The Future of Development

Does this mean the end of programmers? Unlikely. Instead, it elevates the role of the 
developer from a bricklayer to an architect. We spend less time on boilerplate and more 
time on system design and problem-solving.

### Conclusion by AI

Coding in English doesn't mean coding without thinking. It requires a different kind of discipline—one 
focused on clarity of thought and structural understanding.

----

**I'm coding in English to make AI Agents code in code.**