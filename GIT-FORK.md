# GIT-FORK.md - Git Fork Pattern for AI Agents

**Version:** v1.0.0
**Last Updated:** 2026-02-02

## Purpose

Create independent git workspaces that share objects with source repository. Alternative to `git worktree` with full git capabilities and dual-remote setup for multi-agent workflows.

**Core insight:** Full git checkouts with shared objects eliminate worktree constraints while maintaining disk efficiency. Two-remote pattern (origin + parent) enables local sync and remote collaboration.

**Related Documentation:**
- [RLM.md](https://jonnyzzz.com/RLM.md) - Task decomposition patterns
- [MULTI-AGENT.md](https://jonnyzzz.com/MULTI-AGENT.md) - Agent orchestration
- [Blog Post](https://jonnyzzz.com/blog/2026/02/02/git-fork-pattern/) - Detailed explanation

---

## Quick Start

When you need an independent git workspace, create a fork that shares objects with the source repository.

### Agent Prompt

```
Agent, fork my git repository as suggested in GIT-FORK.md
```

---

## Implementation (5 steps)

```bash
# 1. Create and initialize new repository
mkdir -p /path/to/fork
cd /path/to/fork
git init

# 2. Set up object sharing (use absolute path)
mkdir -p .git/objects/info
echo "/absolute/path/to/source/.git/objects" > .git/objects/info/alternates

# 3. Copy git config (inherits origin remote)
cp /absolute/path/to/source/.git/config .git/config

# 4. Add parent remote (points to local source repo)
git remote add parent /absolute/path/to/source
git fetch parent

# 5. Checkout branch (track from parent)
git checkout -b main parent/main
```

Done. You now have a full git repository with two remotes.

---

## Two Remotes Explained

After copying `.git/config`, you inherit the source repository's remotes:

- **origin** → Points to the real remote (GitHub, GitLab, etc.) from the copied config
- **parent** → Points to the local source repository you forked from

### Why Two Remotes?

**origin (from config):**
- Push your changes to the real remote: `git push origin feature-branch`
- Pull from the real remote: `git pull origin main`
- Create PRs, collaborate with team

**parent (added manually):**
- Fetch latest local changes: `git fetch parent`
- Sync with parent's working changes: `git merge parent/main`
- Get updates from parent before they're pushed to origin

### Example Workflow

```bash
# Working in fork
echo "new feature" > feature.txt
git add feature.txt
git commit -m "add feature"

# Get latest from parent (local changes)
git fetch parent
git merge parent/main

# Push to real remote
git push origin feature-branch
```

This is powerful for multi-agent workflows where:
- Parent repository has uncommitted/unpushed work
- Fork needs to sync with parent's latest state
- Eventually push to shared remote (origin)

---

## What This Does

- **Shared objects**: Fork reads commits/trees/blobs from source via alternates
- **Local changes**: New commits stored in fork's `.git/objects`
- **Full git**: All operations work (unlike git worktree limitations)
- **Disk efficient**: Only new objects consume space (~5MB vs 150MB)
- **Two remotes**: Access both local parent and real remote

---

## Why Not Git Worktree?

Git worktree has constraints:
- Can't checkout same branch twice
- Limited operations (rebase, submodules)
- Tool compatibility issues

Git fork is a complete repository with full capabilities.

---

## Important

1. **Absolute paths only** in alternates file
2. **Source must exist** - fork depends on source for shared objects
3. **For local development** - not for distributing repositories
4. **Config copied** - includes user settings and original remotes

---

## Testing

Verify it works:

```bash
# Check alternates configured
cat .git/objects/info/alternates

# Check both remotes exist
git remote -v
# Should show:
#   origin  <real-remote-url> (fetch)
#   origin  <real-remote-url> (push)
#   parent  /path/to/source (fetch)
#   parent  /path/to/source (push)

# Verify object sharing (should be small)
du -sh .git/objects

# Test git operations
git log --oneline
git status

# Create test commit
echo "test" > test.txt
git add test.txt
git commit -m "test"

# Verify can fetch from parent
git fetch parent
```

---

## Use Cases

**Multiple agents on same codebase:**
```bash
# Agent A working on main
mkdir ~/work/agent-a && cd ~/work/agent-a && git init
echo "$HOME/work/main/.git/objects" > .git/objects/info/alternates
cp ~/work/main/.git/config .git/config
git remote add parent ~/work/main && git fetch parent
git checkout -b main parent/main

# Agent B working on feature
mkdir ~/work/agent-b && cd ~/work/agent-b && git init
echo "$HOME/work/main/.git/objects" > .git/objects/info/alternates
cp ~/work/main/.git/config .git/config
git remote add parent ~/work/main && git fetch parent
git checkout -b feature parent/feature
```

Both agents can:
- Fetch from parent to get each other's changes
- Push to origin independently
- Work with full git capabilities

**Syncing between fork and parent:**
```bash
# In parent repository
echo "urgent fix" >> fix.txt
git add fix.txt && git commit -m "urgent fix"

# In fork - get the fix immediately
git fetch parent
git merge parent/main

# Continue working with the fix
echo "using the fix" >> feature.txt
git add feature.txt && git commit -m "feature uses fix"

# Push to real remote
git push origin feature-branch
```

---

## Troubleshooting

**"Object not found" error:**
```bash
# Check alternates path is correct and absolute
cat .git/objects/info/alternates
ls -la $(cat .git/objects/info/alternates)
```

**No remotes after copying config:**
```bash
# Source repository might not have remotes configured
# Manually add origin if needed:
git remote add origin https://github.com/user/repo.git

# Always add parent:
git remote add parent /absolute/path/to/source
```

**Large .git/objects:**
```bash
# Alternates not working - check path is absolute
cat .git/objects/info/alternates
# Should be: /Users/name/projects/repo/.git/objects
# Not: ../repo/.git/objects
```

**Wrong remote tracked:**
```bash
# Make sure to track parent, not origin
git checkout -b main parent/main   # Correct
# Not: git checkout -b main origin/main
```

---

## Remote Management

**See all remotes:**
```bash
git remote -v
```

**Fetch from specific remote:**
```bash
git fetch parent    # Get parent's latest commits
git fetch origin    # Get origin's latest commits
```

**Push to specific remote:**
```bash
git push parent main    # Push to local parent
git push origin main    # Push to real remote
```

**Update from both remotes:**
```bash
git fetch parent
git fetch origin
git merge parent/main    # or origin/main
```

---

*Follow [@jonnyzzz](https://twitter.com/jonnyzzz) on X and [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) for more on AI agents and developer tooling.*
