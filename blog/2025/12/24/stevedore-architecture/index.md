# Under the Hood: How Stevedore Works

**Date:** December 24, 2025  
**Author:** Eugene Petrenko  
**Tags:** stevedore, architecture, gitops, docker, sqlite, golang

---

In my [previous post]({% post_url blog/2025-12-24-introducing-stevedore %}), I introduced Stevedore, my lightweight alternative to Kubernetes for small servers. Today, I want to dive into the architecture. How do we build a robust deployment system in Go without reinventing the wheel?

## Series: Stevedore on a Raspberry Pi

- [Stevedore: GitOps for your Raspberry Pi]({% post_url blog/2025-12-24-introducing-stevedore %})
- [Under the Hood: How Stevedore Works]({% post_url blog/2025-12-24-stevedore-architecture %})
- [Tutorial: Deploying Your First App with Stevedore]({% post_url blog/2025-12-24-getting-started-with-stevedore %})
- [Production Notes: Deploying Stevedore on a Raspberry Pi]({% post_url blog/2026-01-01-production-raspberry-pi-deployment %})
- [Stevedore DynDNS: Dynamic DNS and HTTPS for Your Homelab]({% post_url blog/2026-01-02-stevedore-dyndns %})

## The Loop

At its heart, Stevedore is a polling loop. It checks your Git repositories on a configurable schedule (per deployment). But we don't just run `git pull` on the host. That's messy.

### Worker Containers

We follow the "Docker-first" philosophy. The Stevedore daemon itself runs as a single container. When it needs to perform complex state changes or isolated tasks, it spawns a **Worker Container**.

For example, when Stevedore updates itself, it spawns an "Update Worker" that stops the old daemon and starts the new one. It's like a brain transplant, performed by a robot arm.

There is a git-worker implementation that runs operations in ephemeral `alpine/git` containers, but the daemon's polling loop uses local `git` (`GitCheckRemote`/`GitSyncClean`) rather than routing syncs through the worker container.

## State on Disk

I am tired of distributed key-value stores. Stevedore runs on *one* node. We don't need etcd.

By default, persistent state lives in `/opt/stevedore` (shared data is `/opt/stevedore/shared`; the query socket defaults to `/var/run/stevedore/query.sock`).
*   `/deployments`: per-deployment repo checkout + SSH keys, parameters/runtime state, plus `data/` and `logs/` directories.
*   `/system`: The internal database.

We use **SQLite**. It's rock solid. But storing secrets (like API keys) in plain text is a bad idea, even on a private server. So we use **SQLCipher**.

When you install Stevedore, it generates a `db.key` file. This key encrypts the SQLite database. Your secrets are safe at rest. It's a simple, pragmatic trade-off. We lose high availability (if the disk dies, we die), but we gain immense simplicity.

## Docker Compose as the Spec

I didn't want to create a `stevedore.yaml` format. Docker Compose is already the industry standard for defining multi-container applications.

Stevedore looks for `docker-compose.yaml`, `docker-compose.yml`, `compose.yaml`, `compose.yml`, or `stevedore.yaml` at the repo root. It respects standard features like `healthcheck` for status reporting. Automatic rollback on unhealthy containers is planned but not implemented yet.

We inject `STEVEDORE_DEPLOYMENT`, `STEVEDORE_DATA`, `STEVEDORE_LOGS`, and `STEVEDORE_SHARED` into the `docker compose` environment (along with any DB parameters). These are host paths you can mount in your compose file to make data/logs/shared storage persistent across redeploys.

## Go + Docker CLI (for now)

The code is written in Go. It's robust, statically typed, and has excellent libraries. For now Stevedore shells out to the Docker CLI (`docker`, `docker compose`) instead of using the Docker SDK directly. It's simple and predictable across hosts. If we need tighter control later, we can move to the SDK.

Check out `internal/stevedore/git_worker.go` to see how we manage the ephemeral containers. It's a fun read if you're into system programming!