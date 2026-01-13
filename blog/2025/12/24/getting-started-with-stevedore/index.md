# Tutorial: Deploying Your First App with Stevedore

**Date:** December 24, 2025  
**Author:** Eugene Petrenko  
**Tags:** stevedore, tutorial, gitops, raspberry-pi, docker, github

---

Ready to turn your Raspberry Pi into a GitOps powerhouse? Let's install Stevedore and deploy a simple web server.

## Series: Stevedore on a Raspberry Pi

- [Stevedore: GitOps for your Raspberry Pi]({% post_url blog/2025-12-24-introducing-stevedore %})
- [Under the Hood: How Stevedore Works]({% post_url blog/2025-12-24-stevedore-architecture %})
- [Tutorial: Deploying Your First App with Stevedore]({% post_url blog/2025-12-24-getting-started-with-stevedore %})
- [Production Notes: Deploying Stevedore on a Raspberry Pi]({% post_url blog/2026-01-01-production-raspberry-pi-deployment %})
- [Stevedore DynDNS: Dynamic DNS and HTTPS for Your Homelab]({% post_url blog/2026-01-02-stevedore-dyndns %})

## Prerequisites

*   A Linux host (Ubuntu or Raspberry Pi OS) with sudo access.
*   Docker installed (`curl -fsSL https://get.docker.com | sh`).
*   A GitHub account.

## Step 1: Fork and Install

First, fork the [Stevedore repository](https://github.com/jonnyzzz/stevedore). This is your personal control plane.

SSH into your server and run:

```bash
git clone https://github.com/<YOUR_USERNAME>/stevedore.git
cd stevedore
./stevedore-install.sh
```

This script does a few things:
1.  Builds the Stevedore image.
2.  Sets up the `/opt/stevedore` directory.
3.  Installs a systemd service (`stevedore.service`) when systemd is available; otherwise starts the container with a Docker restart policy.
4.  Generates your `admin.key` and `db.key`.

Verify it's running:

```bash
stevedore doctor
```

## Step 2: Add a Repository

Let's say you have a repository `my-web-app` with a `docker-compose.yaml`.

Tell Stevedore to watch it:

```bash
stevedore repo add my-app git@github.com:<YOUR_USERNAME>/my-web-app.git
```

If your repo default branch isn't `main`, add `--branch <branch>` to the command.

Stevedore will generate a unique SSH Key for this deployment. View it:

```bash
stevedore repo key my-app
```

Copy that key. Go to your GitHub repo -> **Settings** -> **Deploy keys** -> **Add deploy key**. Paste it there. This gives Stevedore read-only access to just that repo.

Prefer GitHub CLI? This does the same thing (read-only):

```bash
gh api -X POST repos/<YOUR_USERNAME>/my-web-app/keys \
  -f title="stevedore-my-app" \
  -f key="$(stevedore repo key my-app)" \
  -F read_only=true
```

## Step 3: Deploy!

Now, kick off the first sync:

```bash
stevedore deploy sync my-app
```

Stevedore will pull the code (it also hard-resets the repo and cleans untracked files by default; use `--no-clean` to skip the cleanup). Now, bring it up:

```bash
stevedore deploy up my-app
```

Boom. Your app is running.

## Step 4: The Magic

Here is the best part. Make a change to your `my-web-app` on your laptop. Change the HTML title.

```bash
git commit -am "Update title"
git push
```

Wait a few minutes (Stevedore polls on its configured interval; default is 5 minutes). Refresh your browser.

**It updated automatically.**

You can check the status at any time:

```bash
stevedore status my-app
```

## Managing Secrets

Need to set an API key? Don't commit it.

```bash
stevedore param set my-app API_KEY "super-secret-value"
```

Stevedore stores this in its encrypted database. Stevedore injects parameters as environment variables on deploy (including automatic redeploys).

## Conclusion

It's that simple. No Kubernetes manifests. No complex CI/CD pipelines. Just Git, Docker, and Stevedore keeping watch.

Give it a try and let me know what you think!