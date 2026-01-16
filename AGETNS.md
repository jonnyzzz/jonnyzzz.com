# CLAUDE.md - AI Agent Instructions for jonnyzzz.com

## Repository Purpose

Jekyll-based personal blog at https://jonnyzzz.com. See SKILL.md for author profile and writing style guide.

**Content:** Technical posts (Kotlin, JVM, IntelliJ, Gradle, AI, infrastructure), conference talks archive, professional profile.

## Formatting
We use ~120 chars per line, we do not keep infinite long lines.
We add whitespaces to Markdown tables to make them look nice in ACSII too

## Symlink Note
`AGETNS.md` is a symlink to this file for tools that look for an AGENTS-style filename.

---

## Quick Commands

```bash
# Development server (watch mode)
# Jekyll on :4000, livereload on :35729
./in.sh

# Production build
./in.sh build

# Run inside Docker container shell
./in.sh exec

# Build Docker image only (no Jekyll)
./in.sh container
```

---

## Docker Build System

**All builds run inside Docker** - Jekyll is never run locally on the host machine.

### Commands Summary

| Command | Description |
|---------|-------------|
| `./in.sh` | Start dev server at http://localhost:4000 with live reload on :35729 |
| `./in.sh build` | Production build, outputs to `_site/` and stages for git |
| `./in.sh exec` | Open bash shell inside the Docker container |
| `./in.sh container` | Build Docker image only (no Jekyll) |

### Development Flow (`./in.sh`)

1. Builds Docker image (if needed), tagged with git branch name
2. Clears and mounts `_site-debug/` as output volume
3. Runs `bundle install` inside container
4. Starts Jekyll server with flags: `--watch --livereload --incremental --future`
5. Uses config: `_config.yml` + `_config_preview.yml`
6. Shows future-dated and unpublished posts
7. Auto-restarts on crash, prompts for manual restart

### Production Flow (`./in.sh build`)

1. Builds Docker image (if needed)
2. Clears and mounts `_site-release/` as output volume
3. Runs `JEKYLL_ENV=production bundle exec jekyll build`
4. Uses config: `_config.yml` + `_config_prod.yml`
5. Rsyncs `_site-release/` to `_site/` (preserves `.git`, `README.md`, `.gitignore`)
6. Stages all changes in `_site/` for git commit

### Output Directories

| Directory | Purpose | Git Status |
|-----------|---------|------------|
| `_site-debug/` | Dev server output, cleared on each run | Ignored |
| `_site-release/` | Production build temp output | Ignored |
| `_site/` | Final deployed site | **Tracked** (separate git history) |

### Docker Image

- **Base:** Ubuntu 16.04
- **Ruby:** System Ruby + Bundler 2.3.27
- **Node.js:** 10.x
- **Python:** Python 2 + Pygments 2.14.0
- **Tag:** `jonnyzzz.com-jekyll:<branch-name>`
- **Rebuild triggers:** Missing image, CI mode, non-TTY mode, `container` command

### Environment Variables

| Variable | Effect |
|----------|--------|
| `CONTINUOUS_INTEGRATION=true` | Forces Docker image rebuild |

---

## Critical Prerequisites

**Time sync required:** Docker container must have system time in sync with host. Build timestamps affect Jekyll output. The build script warns: "It MUST be in sync with host date-time!"

**No local Jekyll:** Never install or run Jekyll on the host machine. All builds must go through `./in.sh`.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Generator | Jekyll 3.8.5 |
| Language | Ruby, SCSS, Liquid |
| Container | Docker (Ubuntu 16.04, Ruby, Bundler 2.3.27) |
| Syntax | Rouge (kramdown GFM) |
| Deploy | GitHub Actions (manual trigger) |

---

## Directory Map

```
_posts/blog/        # Blog posts (130 files: 70 .md + 60 legacy .html)
_talks/             # Conference talks (51 files)
about/              # About pages
_layouts/           # Templates: post.html, page.html, talk.html
_includes/          # Partials: head, navigation, footer, etc.
_plugins/           # Custom: taglink.rb, years_since.rb
_sass/              # SCSS with Bourbon/Neat
_data/              # authors.yml, navigation.yml
_config.yml         # Main config
_config_preview.yml # Dev overrides (future: true, unpublished: true)
_config_prod.yml    # Prod overrides (Google Analytics: G-BXXDX0ERFP)

# Build output directories (see Docker Build System section)
_site-debug/        # Dev server output (volume mounted, git ignored)
_site-release/      # Production build temp (git ignored)
_site/              # Final deployed site (git tracked, separate history)
```

---

## Adding Content

### New Blog Post

1. Create `_posts/blog/YYYY-MM-DD-slug.md`
2. Front matter:
```yaml
---
layout: post
title: "Post Title"
date: YYYY-MM-DD
author: Eugene Petrenko
tags:
  - tag1
  - tag2
excerpt:
categories: blog
---
```
3. Write content in Markdown
4. Ensure the filename date matches the `date` value in the front matter
5. Test locally (see Pre-Publish Checklist below)

### New Talk

1. Create `_talks/YYYY-MM-DD-event-name.md`
2. Front matter:
```yaml
---
event: Conference Name
title: Talk Title
year: YYYY
date: YYYY-MM-DD
type: talk
links:
  YouTube: https://youtube.com/watch?v=...
  Slides: https://docs.google.com/...
feedback:
  - https://twitter.com/...
---
```

### Draft Posts

Use future dates (e.g., `2027-xx-yy-draft-title.md`) to keep posts unpublished. Dev server shows these (`future: true`), production hides them.

---

## Custom Plugins

### `{% blog_tag TAG %}`
Creates link to tag archive: `{% blog_tag kotlin %}` → `<a href="/tags/#kotlin">kotlin</a>`

### `{% years_since YEAR MONTH %}`
Calculates elapsed full years from a date. Parameters: year (required), month (1-12, optional).

Examples:
- `{% years_since 2004 9 %}` → years since September 2004
- `{% years_since 2001 %}` → years since January 2001
- Default (no args): years since September 2001

---

## Configuration Layers

| File | Purpose | Key Settings |
|------|---------|--------------|
| `_config.yml` | Base | Site identity, plugins, collections, comments enabled |
| `_config_preview.yml` | Dev | `future: true`, `unpublished: true`, empty URL |
| `_config_prod.yml` | Prod | Google Analytics ID, site verification |

---

## Build Scripts

| File | Location | Purpose |
|------|----------|---------|
| `in.sh` | Host | Entry point - builds Docker image, runs container |
| `build.sh` | Container | Installs gems, runs Jekyll build or server |
| `Dockerfile` | Host | Defines Ubuntu 16.04 container with Ruby/Node/Python |

---

## Testing

### Cookie Compliance Test

Located in `_test/`. Uses Selenium + Chrome to verify site doesn't set cookies:

```bash
# Auto-setup virtualenv and run
./_test/run_test.sh

# Manual run
source _test/venv/bin/activate
python -m unittest _test/test_no_cookies.py
```

Test crawls all pages, simulates user interaction, checks:
- Cookies at page load
- localStorage/sessionStorage
- Third-party tracking resources

---

## Pre-Publish Checklist

Before committing content:

1. **Local build passes** - Run `./in.sh`, visit http://localhost:4000
2. **Production build passes** - Run `./in.sh build`
3. **Front matter complete** - title, date, author, tags, categories
4. **Tags are kebab-case** - `kotlin-native`, not `Kotlin Native`
5. **Internal links use post_url** - `{% post_url blog/YYYY-MM-DD-slug %}`
6. **Images in /images/** - Reference as `{{ site.url }}/images/filename`
7. **Code samples tested** - Verify code actually works
8. **Links valid** - Check external URLs resolve
9. **Date matches filename** - `YYYY-MM-DD` in filename equals front matter `date`

---

## Commit Conventions

- Lowercase, action-oriented messages
- Common prefixes: `add`, `update`, `fix`, `drop`, `remove`
- WIP allowed: `WIP new post draft`
- Multiple changes: `Add X + tune Y`

---

## Important Files

| File | Purpose |
|------|---------|
| `in.sh` | Host entry point - builds Docker image, manages volumes, runs container |
| `build.sh` | Runs inside container - installs gems, starts Jekyll |
| `Dockerfile` | Container definition (Ubuntu 16.04, Ruby, Node.js, Python) |
| `Gemfile` | Ruby dependencies (Jekyll 3.8.5, plugins) |
| `CNAME` | Custom domain (jonnyzzz.com) |
| `SKILL.md` | Writing style guide |

---

## Do Not Modify

- `_site/`, `_site-debug/`, `_site-release/` - Generated output
- `node_modules/`, `.bundle/` - Dependencies
- `.sass-cache/` - Build cache

---

## Multi-Agent Workflow

For complex tasks, use parallel sub-agents to increase throughput and quality. This repository was analyzed using 5+ concurrent agents.

**See [MULTI-AGENT.md](MULTI-AGENT.md) for comprehensive orchestration patterns, templates, and examples.**

### Related Skill Files

| File | Purpose |
|------|---------|
| **RLM.md** | Core RLM instructions - when/how to decompose large tasks |
| **RLM-extra.md** | Detailed RLM reference - templates, benchmarks, error handling |
| **MULTI-AGENT.md** | Agent orchestration patterns and templates |
| **CLAUDE-CODE.md** | Using Claude Code CLI as sub-agent |
| **CODEX.md** | Using Codex CLI as sub-agent |
| **GEMINI.md** | Using Gemini CLI as sub-agent |
| **SKILL.md** | Writing style guide |

### Quick Reference

| Task Type | Agent Strategy | Details |
|-----------|----------------|---------|
| Repository analysis | Parallel Explore agents | See MULTI-AGENT.md Pattern A |
| Writing content | Sequential pipeline | See MULTI-AGENT.md Pattern B |
| Large files (>50K tokens) | RLM Partition+Map+Reduce | See RLM.md |
| Quality validation | Cross-validation with multiple CLIs | See MULTI-AGENT.md Pattern D |

### External CLI Sub-Agents

**Give sub-agents full tool access** - don't restrict capabilities.

```bash
# Claude Code - full tool access
echo "prompt" | claude -p 2>&1

# Codex - full access, supports image/PDF input
codex exec "prompt"
codex exec -i file.pdf "analyze this"

# Gemini - full access
gemini "prompt"
```

---

## AI Agent Guidelines

When editing this repository:

1. **Read SKILL.md first** - For voice, style, and content patterns
2. **Preserve front matter structure** - Match existing post format exactly
3. **Use kebab-case tags** - Lowercase, hyphenated: `kotlin-native`, `ai-coding`
4. **Date format** - YAML accepts both `'YYYY-MM-DD'` (quoted) and `YYYY-MM-DD` (unquoted)
5. **Author field** - Always `Eugene Petrenko`
6. **Test before commit** - Run `./in.sh` to verify
7. **Link syntax** - Use `{% post_url blog/YYYY-MM-DD-slug %}` for internal links
8. **Code blocks** - Use fenced markdown (```lang) or Jekyll highlight tags
9. **Images** - Store in `/images/`, reference as `{{ site.url }}/images/filename`
10. **Social embeds** - LinkedIn/Twitter embeds are common in recent posts

---

## AI Agent Access (llms.txt)

Blog posts are available as clean markdown for AI agents, following the [llms.txt specification](https://llmstxt.org/).

### Markdown Endpoints

For any blog post URL, append `index.md` to get clean markdown:

```
https://jonnyzzz.com/blog/2024/09/17/Eugene-20-years/          → HTML page
https://jonnyzzz.com/blog/2024/09/17/Eugene-20-years/index.md  → Clean markdown
```

### Format

The `.md` files contain no YAML front matter. Metadata is in readable text:

```markdown
# Post Title

**Date:** September 17, 2024
**Author:** Eugene Petrenko
**Tags:** kotlin, intellij, jetbrains

---

Post content here...
```

### Coverage

- **72 markdown posts** → have `index.md` files
- **60 legacy HTML posts** (pre-2012) → no markdown available

### Plugin

Generated by `_plugins/markdown_output.rb` during Jekyll build.

---

## Site URLs

- Production: https://jonnyzzz.com
- Feed: https://feeds.feedburner.com/jonnyzzz
- LinkedIn: https://www.linkedin.com/in/jonnyzzz/
- Twitter: https://twitter.com/jonnyzzz
- GitHub: https://github.com/jonnyzzz
