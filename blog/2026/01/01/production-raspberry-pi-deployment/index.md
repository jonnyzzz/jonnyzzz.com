# Production Notes: Deploying Stevedore on a Raspberry Pi

**Date:** January 01, 2026  
**Author:** Eugene Petrenko  
**Tags:** stevedore, raspberry-pi, production, systemd, gitops, self-hosting

---

Today is the day. I'm putting Stevedore into production on my Raspberry Pi host (`rp16g`). This is
the real deal: no hacks, no shortcuts, just the supported install path and careful verification.

Stevedore is designed for this exact setup: a single Docker-first control plane, a systemd service
when available, and a clear separation between the host and the container runtime. The goal is to
leave the machine in a stable, boring state and make future updates predictable.

## Series: Stevedore on a Raspberry Pi

- [Stevedore: GitOps for your Raspberry Pi]({% post_url blog/2025-12-24-introducing-stevedore %})
- [Under the Hood: How Stevedore Works]({% post_url blog/2025-12-24-stevedore-architecture %})
- [Tutorial: Deploying Your First App with Stevedore]({% post_url blog/2025-12-24-getting-started-with-stevedore %})
- [Production Notes: Deploying Stevedore on a Raspberry Pi]({% post_url blog/2026-01-01-production-raspberry-pi-deployment %})
- [Stevedore DynDNS: Dynamic DNS and HTTPS for Your Homelab]({% post_url blog/2026-01-02-stevedore-dyndns %})

## Guardrails

Before touching production, I’m setting a few guardrails:

* Use the official installer (`./stevedore-install.sh`), not ad-hoc docker run commands.
* Keep state under `/opt/stevedore` (default layout).
* Prefer systemd (`stevedore.service`) to ensure the container survives reboots.
* Never paste secrets into this post. Keys stay on the host, paths are fine to mention.

## The Success Story (In Short)

This deployment did exactly what Stevedore promises. I installed it using the official script,
bootstrapped the self-managed deployment, and proved the entire lifecycle: keys, sync, self-update,
and stability over time. The host is now boring in the best way: Stevedore is running under systemd,
the daemon health checks match, and updates are a controlled, repeatable process.

## Highlights

* The systemd unit keeps the control plane alive across reboots with zero manual babysitting.
* The self-deployment syncs via a read-only GitHub deploy key when the repo uses SSH (public HTTPS clones still work without it), and I can rotate it manually.
* Self-update works end-to-end when I trigger `stevedore self-update`: it pulled new commits, built a new image, and swapped cleanly.
* The five-hour stability check shows the daemon healthy and the control plane steady.
* Docs and onboarding guidance were improved based on real production friction.

## What I Learned (And Turned Into Improvements)

* GitHub deploy keys are picky: `read_only=true` needs `-F` in `gh api`, so I documented the exact
  command and wired it into the CLI guidance.
* Self-update builds run in the foreground; once the update worker is spawned, the container swap
  finishes server-side, and the backup image gives a rollback path.
* The systemd-managed control plane and a self-deployment compose project can collide on container
  naming if the compose file sets `container_name: stevedore`. That's a good reminder that "boring"
  operations need crisp boundaries.

## Outcome

Stevedore is now running in production on `rp16g`, updating itself and staying healthy without
manual intervention. The deployment is stable, the operational checks are clean, and the process is
documented end-to-end. This is exactly the boring, reliable, Git-driven workflow I wanted.

Next time, I want to tighten the self-deployment status story (so it reports cleanly even with the
systemd-managed control plane) and keep iterating on the onboarding docs as more users go through
this path.

## Agentic Finale

The funny fact -- I created stevedore to simplify my human actions to deploy services. 
It appeared that Claude Code and Codex are much better in dealing with deployments that I,
basically, I unstructured them to use deliver the changes over SSH. Both Agents were great
to figure out how to bind the deploy keys, use stevedore to manage repositories, run updates.


<iframe src="https://www.linkedin.com/embed/feed/update/urn:li:share:7416481230835245057" height="705" width="504" frameborder="0" allowfullscreen="" title="Embedded post"></iframe>