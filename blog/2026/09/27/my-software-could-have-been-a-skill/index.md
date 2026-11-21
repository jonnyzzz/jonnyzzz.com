# My Software Could Have Been a Skill: Stevedore

**Date:** September 27, 2026  
**Author:** Eugene Petrenko  
**Tags:** ai-agents, ai-coding, stevedore, infrastructure, homelab, disposable-software

---

Stevedore has been running my services for almost a year. I never used it myself. I have not seen the code either.
It could have been a Skill.

_Updated in November 2026 with more reflections._

## How It Started

This story starts about a year ago, when I got a Raspberry Pi with 16GB of RAM at home. I had several
services to run on it, mainly to manage the home, TVs, and other devices. I was all into containers and
systems to manage containers at scale, such as Kubernetes.

Quickly I realized that my hardware is not enough to run Kubernetes, and I am not eager to invest my time
into managing it for a few home services. In my real projects, I used Kubernetes as a service, from dedicated
teams or from a cloud provider such as GCP or AWS. Somebody else was keeping the cluster alive, not me.

I looked for a simple solution to manage a few containers on a small box, but did not find one that fit
my setup. I decided to tightly couple containers with Git/GitHub repositories, so a commit would rebuild
and redeploy the container.
That is how [Stevedore](https://github.com/jonnyzzz/stevedore) was born. I covered the story in the older posts:
- [Stevedore: GitOps for your Raspberry Pi]({% post_url blog/2025-12-24-introducing-stevedore %})
- [Under the Hood: How Stevedore Works]({% post_url blog/2025-12-24-stevedore-architecture %})
- [Tutorial: Deploying Your First App with Stevedore]({% post_url blog/2025-12-24-getting-started-with-stevedore %})
- [Production Notes: Deploying Stevedore on a Raspberry Pi]({% post_url blog/2026-01-01-production-raspberry-pi-deployment %})
- [Stevedore DynDNS: Dynamic DNS and HTTPS for Your Homelab]({% post_url blog/2026-01-02-stevedore-dyndns %})

Now I have my simplistic solution to run all the services I need. In this post, I want to reflect on the
actual operation and usage of Stevedore and the services.

## Stevedore

I created Stevedore with AI Agents. I cannot remember how many of the commits were done by hand,
most likely none. I instructed my agents to create a decent piece of software with enough integration tests
and specifications. It was a part of my [holiday sprint]({% post_url blog/2025-01-06-holiday-sprint-with-ai %}).

The numbers from GitHub in November 2026: the repository was created on December 13, 2025, it has 139 commits,
and it is about 400KB of Go code. 99 of these commits were made in the remaining two weeks of December. The last
change was in April 2026. It is a real project, with a self-update, a watchdog, integration tests, and a CI.

## The Actual Usage

The actual usage was quite the same. I've been creating services and adding them to the system. And each
service was created with AI, extensively with AI. For example, my LG TV management service, or
[Roomtone]({% post_url blog/2026-01-03-roomtone-single-room-call %}), the single-room call for home.
All my services were added that way.

All my deployments were made with AI Agents too. Apparently, I have never used Stevedore from the CLI for my routine
deployments. It has always been much easier to ask Claude or Codex to update a service via SSH.
The agent opens the SSH connection, checks the state, runs the commands, reads the logs, and reports back

## The Twist

From my standpoint back in 2025, it was clear -- I need Stevedore to manage my deployments on the Raspberry Pi.
For a human like me, it was necessary to have a system that manages all the containers, helps to spend
much less time on every next step, and protects me from errors.

In fact, I never used it like that. All the time, an AI Agent was managing, changing, and updating my deployments.
It was never done by me. Never.

During the summer of 2026, my LG TV management service stopped working. It was no longer able to connect to the
TV. I decided to look at it manually -- the only time I tried to do it by hand. I started with the Stevedore CLI,
then the service logs, then the details. It was not easy to catch up with the project -- it was, apparently,
a new codebase for me. I did not have enough time to learn it. Next attempt -- I asked an AI Agent. The problem
was solved with a dependency update. Surprisingly, some other features started to work as well. The AI Agent
spent just several minutes on that task, much less time than I spent learning about that system.

I did not have time to learn my own tool. The AI Agent fixed the service in minutes.

## The Skill

Given all the facts, I could have had a Skill instead. An AI Agent (or a sub-agent) could easily follow the steps
from the skill to complete the deployment or update of a service. As an example, you can even just say
to your AI Agent: here is a Raspberry Pi over SSH, I need you to deploy this service as a Docker container.
For most of the cases -- it's enough.

It is my home server with a few services. I have not tried that with a production infrastructure.
Even at home, I need to check deployments, know how to recover, and decide what the AI Agent can change.

A Skill is a short Markdown file. It does not need a release, a CI, or a self-update. It describes the
conventions: where the services live, how the containers are named, where the secrets are, how to check that
a service is healthy. The AI Agent follows the steps and checks the logs. I still have
to test the steps and keep them up to date. For more production solution, I'd put the skill to Git or GitHub.

My [personal assistant]({% post_url blog/2026-07-19-personal-assistant-agent %}) started the same way --
one prompt, the scripts came later, where they were useful.

I still see the value of Stevedore. The GitOps polling and reconciliation run without anyone, a human or an agent,
and keep the services updated. The AI Agent benefits from these checks too, and a Skill alone does not poll Git.
Still, my impression is that a big part of the code is about making operations safe and easy for a human,
and the human was never there.

## Reflections from November 2026

By using Skills and AI-made services, we are moving the needle of abstractions. I describe what I need
[in English]({% post_url blog/2026-01-27-coding-in-english-with-ai %}). AI Agents pick the implementation.
I no longer know
most of the technical and implementation details of my services. I do not even control
the programming languages behind them. In fact, most of the containers are using Python with uv inside Docker.

I consider most of the services as
[Disposable Software]({% post_url blog/2026-11-18-rewriting-cheaper-than-maintaining %}), where I need
it to work, and I can easily recreate it once needed. What I still keep are the requirements, the configuration,
and the data. The implementation becomes the next abstraction, as I wrote in
[Abstractions Are the Complexity?]({% post_url blog/2026-11-20-complexity-abstractions %})

## Closing

Consider the software you create -- it could have been a Skill. Have you replaced a small tool with a Skill?
What still needed code? Looking forward to reading about your examples
on [X](https://x.com/jonnyzzz) or [LinkedIn](https://www.linkedin.com/in/jonnyzzz/).