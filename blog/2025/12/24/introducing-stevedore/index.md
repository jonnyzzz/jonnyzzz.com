# Stevedore: GitOps for your Raspberry Pi

**Date:** December 24, 2025  
**Author:** Eugene Petrenko  
**Tags:** stevedore, gitops, raspberry-pi, docker, homelab, self-hosting

---

Raspberry Pi is my home server hardware. I decided if I can make my human life easier
be making the deployments of Docker containers more smooth, and more automated.

I've tried Kubernetes before, but never deployed it. It feels way too heavy to install and maintain (I could be wrong).
Is the overhead is real? I've tried shell scripts via SSH, but I must be careful.

I wanted the Heroku experience, but on my own hardware. I wanted to push code to GitHub 
and have my Pi update itself. No CI pipelines to configure, no complex Terraform state t
o manage. Just a simple loop:

1.  Is there new code?
2.  `git fetch` + reset (sync)
3.  `docker compose up -d --build`

So I built **Stevedore**. Heavily with the help of AI.

## Series: Stevedore on a Raspberry Pi

- [Stevedore: GitOps for your Raspberry Pi]({% post_url blog/2025-12-24-introducing-stevedore %})
- [Under the Hood: How Stevedore Works]({% post_url blog/2025-12-24-stevedore-architecture %})
- [Tutorial: Deploying Your First App with Stevedore]({% post_url blog/2025-12-24-getting-started-with-stevedore %})
- [Production Notes: Deploying Stevedore on a Raspberry Pi]({% post_url blog/2026-01-01-production-raspberry-pi-deployment %})
- [Stevedore DynDNS: Dynamic DNS and HTTPS for Your Homelab]({% post_url blog/2026-01-02-stevedore-dyndns %})

## What is Stevedore?

Stevedore is a lightweight GitOps-style deployment loop for Docker Compose 
on a single host. By default, the installer runs the control plane as a single Docker
container on Linux. It may spawn a short-lived update worker container for 
self-update; git sync runs via the local git binary by default. You register repos, 
and the daemon polls enabled deployments for changes and deploys them. 
The `stevedore` deployment is tracked too, but applying updates
is a manual `stevedore self-update`.

It's designed to be:
*   **Boring:** It uses Docker Compose. If you know Docker, you know Stevedore.
*   **Secure-ish:** It generates SSH deploy keys for your repos. Parameters are stored in an encrypted SQLCipher database; deploy keys are plain files protected by filesystem permissions.
*   **Self-healing:** The control plane runs as a systemd service when available (otherwise a Docker restart policy); workload restarts follow your Compose restart policy.

## Why not just a cron job?

You could write a bash script that does `git pull && docker compose up`. I did that for years. 
But then you hit edge cases:
*   What if `docker compose build` fails? You don't want to take down the running app.
*   How do you manage secrets without committing `.env` files?
*   How do you update the script itself?

Stevedore handles these gracefully. It runs builds using standard Docker Compose, ensuring 
consistency. It has a dedicated encrypted parameter store. And yes, it can update itself 
when installed in self-bootstrap mode.

## The "Fork First" Philosophy

Stevedore is open source, but it's designed to be *your* infrastructure. The installation 
process encourages you to fork the repository first. This gives you control. If I break 
something in the upstream `main`, your house doesn't burn down. You pull updates when 
you are ready.

## Coming Next

I'm still actively building it. The core "sync -> build -> deploy" loop is working. 
I'm planning a web UI (because who doesn't love a dashboard?) and more security hardening.

Check it out on [GitHub](https://github.com/jonnyzzz/stevedore). If you have a Raspberry Pi collecting dust, give it a job!

<iframe src="https://www.linkedin.com/embed/feed/update/urn:li:activity:7406407799297007617" height="520" width="504" frameborder="0" allowfullscreen="" title="Embedded post"></iframe>

## Agentic Finale

The funny fact -- I created stevedore to simplify my human actions to deploy services.
It appeared that Claude Code and Codex are much better in dealing with deployments that I,
basically, I unstructured them to use deliver the changes over SSH. Both Agents were great
to figure out how to bind the deploy keys, use stevedore to manage repositories, run updates.

<iframe src="https://www.linkedin.com/embed/feed/update/urn:li:share:7416481230835245057" height="705" width="504" frameborder="0" allowfullscreen="" title="Embedded post"></iframe>