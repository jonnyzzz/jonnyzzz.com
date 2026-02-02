# Git Fork Pattern: Full Checkouts Without the Bloat

**Date:** February 02, 2026  
**Author:** Eugene Petrenko  
**Tags:** git, dev-tools, ai-agents, workflow

---

I've been working with multiple AI agents on the same codebase, and `git worktree` kept getting in the way.
The same branch can't be checked out in multiple worktrees. Some git operations don't work well with worktrees.
**So I stopped using worktrees entirely.** Instead, I'm using full git checkouts that share objects with the
original repository. **Full git functionality, minimal disk usage.**

----

## The Problem with Git Worktree

Git worktree is useful for quick parallel work, but it has limitations that become painful when you're
orchestrating multiple AI agents or just need full git flexibility:

- **Can't checkout the same branch twice** - Want two agents working on `main`? Can't do it with worktrees.
- **Limited git operations** - Some rebase operations, submodules, and other features behave differently.
- **Tool confusion** - IDEs and git tools sometimes don't handle worktrees well.
- **Tied to main repo** - Worktrees are dependent on the main repository structure.

When you're running [multi-agent workflows](https://jonnyzzz.com/MULTI-AGENT.md) or just need multiple
independent checkouts, these constraints become blockers.

## The Solution: Git Alternates

Git has a lesser-known feature called **alternates** - you can tell one repository to use another
repository's object database. This means:

- Create as many full checkouts as you want
- Each checkout is a complete, independent git repository
- Objects (commits, trees, blobs) are shared via `.git/objects/info/alternates`
- New commits are stored locally, existing objects are read from the source
- **Full git functionality, no worktree limitations**

I tested this approach with our 25-year-old monorepo, and it works perfectly. Multiple agents can now
work independently, each in their own full checkout, sharing the same object database.

## How It Works

The implementation is straightforward. Here's what happens:

```bash
# Original repository
~/projects/myrepo/.git/objects  # Contains all git objects

# New fork
~/projects/myrepo-fork/.git/objects/info/alternates
# Contains: /Users/username/projects/myrepo/.git/objects

# Result:
# - Fork reads objects from original
# - Fork writes new objects locally
# - Both are independent repositories
```

When git needs an object, it checks the local `.git/objects` first, then checks the paths listed
in the `alternates` file. It's transparent and works with all git operations.

## The Implementation

The implementation is just 5 steps:

```bash
# 1. Create and initialize new repository
mkdir -p /path/to/fork && cd /path/to/fork && git init

# 2. Set up object sharing (use absolute path)
mkdir -p .git/objects/info
echo "/absolute/path/to/source/.git/objects" > .git/objects/info/alternates

# 3. Copy git config (inherits remotes)
cp /absolute/path/to/source/.git/config .git/config

# 4. Add parent remote and fetch
git remote add parent /absolute/path/to/source
git fetch parent

# 5. Checkout branch (track from parent)
git checkout -b main parent/main
```

Done. You now have **two remotes**: `origin` (from config) pointing to the real remote, and
`parent` pointing to your local source repository.

See [GIT-FORK.md](https://jonnyzzz.com/GIT-FORK.md) for complete documentation.

## Two Remotes Pattern

When you copy `.git/config`, you inherit the original repository's remotes. Then you add a second
remote for the local parent:

- **origin** (from config) → Real remote (GitHub, etc.) - push, pull, create PRs
- **parent** (added manually) → Local source repo - sync uncommitted changes

This is powerful for multi-agent workflows:

```bash
# Working in fork
git commit -m "feature work"

# Get latest from parent (before it's pushed anywhere)
git fetch parent
git merge parent/main

# Push to real remote
git push origin feature-branch
```

Agents can share work through the parent repository, then independently push to origin when ready.

## Disk Usage

Actual numbers from testing:

```
Original repo:     150 MB
Normal clone:      150 MB
Git fork:          ~5 MB (only new commits)
Git worktree:      ~5 MB (but with limitations)
```

The git fork gives you the disk efficiency of worktrees **plus** the full functionality of a
complete repository, **plus** access to both local and remote changes.

## AI Agent Integration

This pattern works exceptionally well with AI agents. When I orchestrate multiple agents on the
same codebase, I just tell them:

```
Agent, fork my git repository as suggested in GIT-FORK.md
```

Agents understand this pattern and implement the 5 steps automatically. Each agent gets its own
fork with:

- Full git access - create branches, rebase, merge, everything works
- Shared objects - no disk space wasted
- True independence - complete repository, no worktree constraints

I added [GIT-FORK.md](https://jonnyzzz.com/GIT-FORK.md) to my skill files alongside
[RLM.md](https://jonnyzzz.com/RLM.md) and [MULTI-AGENT.md](https://jonnyzzz.com/MULTI-AGENT.md).
Agents read it and implement the pattern without additional instructions.

## Testing and Validation

I tested this extensively:

- **Multiple forks** - Created 5+ forks from the same source, all working independently
- **All git operations** - Commit, branch, merge, rebase, cherry-pick - everything works
- **Object sharing** - Verified that shared objects aren't duplicated (checked with `du -sh .git/objects`)
- **Tool compatibility** - IntelliJ, VSCode, git CLI, git GUI tools - all work normally
- **25-year-old monorepo** - Works with large, complex repositories

The key insight: **this is just a normal git repository with an optimization**. Tools don't need
to know about alternates, they just work.

## Important Notes

A few things to keep in mind:

1. **Absolute paths** - The `alternates` file must contain absolute paths, not relative paths
2. **Source availability** - The source repository must remain available. If you delete it, forks lose shared objects
3. **Two remotes** - Copying config gives you `origin`, then you add `parent` manually
4. **Track parent** - Checkout from `parent/branch`, not `origin/branch`
5. **Garbage collection** - Each repository runs `git gc` independently, which is usually fine
6. **Not for distribution** - This is for local development, not for sharing repos with others

The two-remote pattern means you can:

```bash
git fetch parent      # Get local uncommitted changes
git fetch origin      # Get pushed changes from team
git push origin main  # Push your work to team
```

## The Pattern in Practice

Here's my typical workflow now:

1. **Main repository** - My primary working copy at `~/projects/myrepo`
2. **Tell agent** - "Fork my git as suggested in GIT-FORK.md"
3. **Agent works** - Creates fork, does work, full git capabilities
4. **Cleanup** - Delete fork when done, no impact on main repository

Some forks last minutes, some last days. The flexibility is what matters - forks are cheap (5MB),
fully functional, and agents know how to create them.

## Why This Matters

The git fork pattern enables true parallel development with AI agents. Instead of carefully
orchestrating which agent works where and managing worktree constraints, I just:

- Spin up agent with its own fork
- Agent works independently
- Agent completes task
- Results are integrated back

The pattern scales to any number of agents. I've had 5+ agents working simultaneously, each in
their own fork, no conflicts, no limitations.

For solo development, this is useful too. Want to try a risky refactoring without branching? Fork
it. Want to test something while keeping your main checkout clean? Fork it. Each fork is cheap and
fully functional.

----

## Try It Yourself

The complete pattern is in [GIT-FORK.md](https://jonnyzzz.com/GIT-FORK.md) - just 5 steps:

1. Create and initialize fork
2. Set up alternates file (absolute path)
3. Copy git config
4. Add remote and fetch
5. Checkout branch

If you're working with AI agents, just reference GIT-FORK.md and they'll implement it. If you're
doing it manually, the commands are straightforward - see the doc for exact syntax.

----

## What's Next

I'm now exploring how to chain forks - creating a fork from a fork. This could enable interesting
multi-level agent hierarchies where parent agents spawn child agents, each with their own workspace.

The git alternates mechanism has been in git for years, but it's not widely used. With AI agents
becoming primary users of development tools, patterns like this become more important. **Tools must
now be optimized for agentic consumption.**

If you're orchestrating AI agents or just want more flexibility than git worktree provides, try the
git fork pattern. It's what I use every day now.

----

**Questions? Experiments? Let me know how the git fork pattern works for you.**

- [Follow me on LinkedIn](https://www.linkedin.com/in/jonnyzzz/)
- [Follow me on X (Twitter)](https://twitter.com/jonnyzzz)
- [Check out more AI agent patterns](https://jonnyzzz.com/ai/)