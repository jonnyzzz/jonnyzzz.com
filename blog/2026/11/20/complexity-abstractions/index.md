# Disposable Software -- Abstractions Are the Complexity?

**Date:** November 20, 2026  
**Author:** Eugene Petrenko  
**Tags:** ai-agents, ai-coding, software-engineering, complexity, abstractions, disposable-software, agentic-ai

---

In the [previous post]({% post_url blog/2026-11-18-rewriting-cheaper-than-maintaining %}) we discussed
whether rewriting software could become cheaper than maintaining it. This time I want to look
at [abstractions](https://en.wikipedia.org/wiki/Abstraction_(computer_science)).

## Abstractions

Software engineering is full of abstractions. Consider the basic Internet. It starts with
a browser, which uses [HTTP](https://en.wikipedia.org/wiki/HTTP) (of some version) to fetch the content
of the page, next it deals with [HTML](https://en.wikipedia.org/wiki/HTML),
[JavaScript](https://en.wikipedia.org/wiki/JavaScript), graphics,
[process isolation](https://en.wikipedia.org/wiki/Process_isolation) and many things
in the [browser engine](https://en.wikipedia.org/wiki/Browser_engine) to render a page for you,
on your phone. HTTP usually runs over [TCP](https://en.wikipedia.org/wiki/Transmission_Control_Protocol),
or, with [HTTP/3](https://www.rfc-editor.org/rfc/rfc9114.html),
[QUIC](https://en.wikipedia.org/wiki/QUIC) over [UDP](https://en.wikipedia.org/wiki/User_Datagram_Protocol).
Underneath, we use [IPv4](https://en.wikipedia.org/wiki/IPv4) or [IPv6](https://en.wikipedia.org/wiki/IPv6),
stacked into the [Internet protocol suite](https://en.wikipedia.org/wiki/Internet_protocol_suite).
It all runs on top of [operating systems](https://en.wikipedia.org/wiki/Operating_system), which are based on
[hardware abstractions](https://en.wikipedia.org/wiki/Hardware_abstraction) and software abstractions.

My point here is to highlight that we accept complexity of some components or layers
of our solutions. That is normal to assume that a basic Internet page just works, and
most of the time we do not go beyond that abstraction to the deep technical details.

There are, of course, rare cases when one needs to dig as deep as possible to optimize
their software and gain drastic improvements in performance, stability and other aspects.
Joel Spolsky called it
[The Law of Leaky Abstractions](https://www.joelonsoftware.com/2002/11/11/the-law-of-leaky-abstractions/) --
every non-trivial abstraction leaks to some degree

I hit that when [listing files on macOS]({% post_url blog/2020-08-12-listing-files %}) -- it ended up
in native APIs and system calls.

We accept complexity and abstractions when doing software.

## AI Agents

With the rise of AI Agents I see another abstraction which comes into play.

Now you may not even know how your application works, or what code is written there. You may
trust your AI Agents did the right work and covered it with enough tests. It can be
specs, it may be no specs, it may just work. I wrote before that
[code review is the real bottleneck]({% post_url blog/2026-01-16-code-review-bottleneck %})
once AI Agents generate code faster than we can read it.

Of course, for more complex applications, people tend to understand, review, test,
and manage AI-assisted changes. I want to share my own experience doing [devrig.dev](https://devrig.dev/):

I have deep experience dealing with Java/Kotlin applications, IntelliJ API, and related
backend/desktop software application stacks.
And if I were to review the code -- it would be a deep review with enough fixes and improvements.
On the other hand, I can understand HTML, [CSS](https://en.wikipedia.org/wiki/CSS), JavaScript,
[TypeScript](https://en.wikipedia.org/wiki/TypeScript) and other web technologies, but I have much less
experience to have a deep opinion on the code, given the code renders decently.
I wrote more about devrig [here]({% post_url blog/2026-06-02-devrig-mcp-steroid-level-3 %}).

## The New Abstraction

With AI Agents, we can create
[Disposable Software]({% post_url blog/2026-11-18-rewriting-cheaper-than-maintaining %}) to solve problems faster.
There is no requirement to fully understand that software, how it's tested, and so on. We may trust
and validate an AI Agent's work.
In my case, [integration tests kept the MCP contract]({% post_url blog/2026-05-20-http-mcp-to-stdio-lessons %})
while AI Agents and I rewrote the transport.

Given that, I believe we are going to shift the abstraction level of complexity even further.

Just assume, you are running a service which does the work, it uses the database, and other tools
internally to work. Or even [SAP](https://en.wikipedia.org/wiki/SAP_ERP) or
[Spring Framework](https://en.wikipedia.org/wiki/Spring_Framework). And you have no idea what's inside.
These are the implementation details, and such details are now hidden behind a new abstraction,
very much like the classic [information hiding](https://en.wikipedia.org/wiki/Information_hiding) principle

> With AI Agents we hide software implementation details behind the new abstraction level.

## Complex Systems

You may want to stop me and say that there are still huge and complex systems, which
had been created for decades, such systems have way too many edge cases, and tricks, and
details, and these are the details the business wants to keep untouched.

I am not against that. And I personally believe I can [help](/services/) you use AI Agents to work with
such big [monoliths](https://en.wikipedia.org/wiki/Monolithic_application). We did it for a
[release roadmap of a large product]({% post_url blog/2026-04-28-ai-agent-roadmap-research %}),
and with [MCP Steroid]({% post_url blog/2026-01-04-mcp-steroids-intellij %}) AI Agents work inside IntelliJ
on big codebases.

Our industry invented [**microservices architecture**](https://en.wikipedia.org/wiki/Microservices)
([Martin Fowler's article](https://martinfowler.com/articles/microservices.html)) to solve the complexity
problems of such complex systems. And it's still an open discussion if microservices are the best solution,
see [Monolith First](https://martinfowler.com/bliki/MonolithFirst.html) and
[Microservice Trade-Offs](https://martinfowler.com/articles/microservice-trade-offs.html).
With AI Agents, I see it's changing.

## Agentic Microservices

Let's borrow the idea of [mathematical induction](https://en.wikipedia.org/wiki/Mathematical_induction) as an analogy.
Given one can create a service that solves the basic business needs with AI, and such service implementation
is fully hidden behind the new abstraction. How would you deal with more complex systems?

My answer is to use Agentic Microservices. The whole idea is to turn a complex system
into a swarm of smaller services, each created with AI Agents, and each is talking
to each other to create a more complex solution. Even the binding of such services
can be implemented as yet another service. It is similar to what we do with AI Agents
themselves, when [AI Agents manage AI Agents]({% post_url blog/2026-01-30-orchestrating-ai-fleets %})
via [run-agent.sh]({% post_url blog/2026-02-06-run-agent-multi-agent-orchestration %}).

The interfaces and interactions still need to be tested, for example with
[contract tests](https://martinfowler.com/bliki/ContractTest.html).
I think that approach will bring similar discussions and technical challenges as we had
with monolithic systems and microservices. It will open new opportunities to create
solutions with AI Agents on the other hand.

## Summary

The first -- **we are doing disposable software**. The code and the implementation details are the new abstraction
which hides everything.

The second -- **we connect such services together as Agentic Microservices**. It will allow to create
even more complex systems.

This will move the most of our software development to use the natural language and prompts,
to describe the system and its services, just as I wrote in
[Coding in English with AI]({% post_url blog/2026-01-27-coding-in-english-with-ai %}).
Just like one may not know today how exactly the CPU's
[L3 cache](https://en.wikipedia.org/wiki/CPU_cache#Multi-level_caches) works when a web page is rendered.