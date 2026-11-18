# What If Rewriting Software Becomes Cheaper Than Maintaining It?

**Date:** November 18, 2026  
**Author:** Eugene Petrenko  
**Tags:** ai-agents, ai-coding, software-engineering, skills, disposable-software

---

Today I was discussing the cost of maintaining software with a friend. We both come from software engineering
backgrounds. We quickly started talking about architecture and maintainability. And then we wondered whether
our experience was getting in the way.

We assume code is expensive. We design it so that someone can maintain it for years.
What happens if writing it again becomes cheaper?

## A Project That Just Works

Imagine someone builds a seasonal (reporting) application for your company. An internal tool, maybe external,
used a few times a year.
The developer uses AI Agents to implement most, perhaps all, of it.

The result works. It's tested. There might still be bugs, questionable architecture, or code that experienced engineers
would never approve. But it solves the business problem. Users are happy

They need their report. They probably don't care whether the application follows SOLID principles or uses our favorite
framework. Those choices matter when they affect the result.

A year passes. The application needs changes, and the original developer is no longer available. What do you do?

## Our First Instinct: Maintainability

Was the architecture designed properly? Can another engineer understand and safely extend it?
We started discussing frameworks, documentation, and the skills the next developer would need.
That was our first instinct too

I spent [22 years at JetBrains]({% post_url blog/2024-09-17-Eugene-20-years %}) building developer tools,
creating products, and leading engineering teams.
Much of that work was about helping people understand, maintain, and evolve software. This is how I've learned to think.

But for this small application, **what if we're solving yesterday's problem?**

## In 2027, Why Not Just Ask an Agent?

Imagine revisiting that application in 2027. We could try either approach. Would one even attempt reading
the code without AI?

**Option 1: Maintain the existing implementation.**

Ask an AI Agent to understand the codebase, identify where the changes belong, implement them, and verify the results.
Perhaps we don't need the original developer, or another engineer who already knows this framework deeply.
We still need someone who can judge whether the change is correct

**Option 2: Rewrite the application.**

If the architecture gets in the way, dependencies are outdated, or the changes don't fit the design, we could try this:

1. Ask an AI Agent to analyze the existing application and extract its specifications.
2. Recover the business rules, edge cases, and expected behavior.
3. Update the specifications with the new requirements.
4. Review the specifications yourself or with another AI Agent.
5. Ask AI Agents to implement the application again.
6. Validate the new implementation against the old behavior and the updated requirements.
7. Migrate existing data if necessary, verify the result, and deploy.

The challenging part is recovering what the application actually does. The code may contain undocumented business rules.
It may also contain bugs we don't want to reproduce. A new implementation can introduce its own bugs.
Comparing the two gives us evidence, but we still have to decide which behavior is correct.

For small enough project, could doing all of this cost less than understanding and maintaining the implementation?
I think that is becoming a realistic option. It is a hypothesis we need to test with actual costs.

## Remember "Rewrite It in Rust"?

"Rewrite It in Rust", or RIIR, is a familiar idea and a meme. [Ruff](https://docs.astral.sh/ruff/)
and [uv](https://astral.sh/blog/uv) are examples of new Rust implementations of familiar tooling concepts.
They are useful parallels, rather than examples of the AI workflow above.

The usual argument for a rewrite is that we get something better: performance, memory safety, reliability,
or an architecture that fits the problem. Rewriting costs enough that we need to justify the investment.

If AI Agents reduce the cost of implementation far enough, the calculation changes.

> We might rewrite simply because it costs less than maintaining what we already have.

I would expect this to become practical first for small applications, internal tools, prototypes,
and relatively isolated business workflows.

## What Becomes Valuable When Code Becomes Cheap?

We protect source code, document it, refactor it, and invest in keeping it maintainable.
But what would we need if we wanted to reproduce this application next year?

The requirements, business rules, test cases, data models, expected behavior, and the reasons behind product decisions.
Also the conversations and prompts that helped us discover them.

**Version your prompts, requirements, conversations, and decisions. Keep the acceptance tests.**

An archive of every AI conversation is not automatically a specification. We still need reliable description of the
product: what was agreed, what changed, and which behavior the tests should verify. The existing code remains useful
evidence, especially where that description is incomplete.

If we can regenerate the implementation, this knowledge becomes the part we can least afford to lose.

## Does Architecture Still Matter?

Yes. I wouldn't casually rewrite a banking platform, a large distributed system, or safety-critical infrastructure.
Complex integrations, security, compliance, persistent data, performance, and accumulated business logic still have
to be understood and verified. AI Agents don't make that work disappear.

Even the seasonal reporting tool needs reliable testing and deployment. Its data may matter a lot to its users.
The cost of a rewrite includes recovering behavior, reviewing it, migrating data, and operating the replacement.
Generating code is only one part of the comparison.

Still, a reporting tool used by ten people and a platform serving millions are different engineering problems.
Maybe we overengineer some small projects because we assume writing code will remain the expensive part.
Users want an application that works today and can adapt when their needs change. Architecture should help us do that.

## From Writing Code to Delivering Outcomes

In January, I wrote about [coding in English with AI]({% post_url blog/2026-01-27-coding-in-english-with-ai %}).
Recently I've seen a linter for English -- [stelint](https://serejke.github.io/stelint-site/).

This is the next question for me. If AI Agents can implement, test, debug, and eventually regenerate applications,
more of our work moves to defining what needs to exist, how it should behave, and how we can prove it works.

After 22 years at JetBrains, this is where I'm focusing my work: AI-native developer tools such as
[devrig](https://devrig.dev/) and [run-agent.sh](https://run-agent.sh/), and how multiple AI Agents can collaborate
on engineering problems.

I also work independently with founders and engineering teams on AI engineering, developer tools,
0→1 product development, and technical leadership. I want to help teams find where AI Coding changes how they build
and deliver software. If you are trying this with your own applications, I'd like to compare experiences.
You can find my work and consulting at [jonnyzzz.com/services](https://jonnyzzz.com/services/).

## What Will 2027 Look Like?

I don't know whether rewriting will become the default way to maintain applications or libraries.
But I think it could become an ordinary option in our engineering decisions.

Our old assumption: code is expensive, so we design it for long-term maintenance.
If code becomes cheap, understanding requirements and verifying outcomes may still be expensive.
That changes what we should preserve, and what we can afford to generate again

Will you maintain your small software projects in 2027, or simply regenerate them?

**Are we getting to disposable software?**