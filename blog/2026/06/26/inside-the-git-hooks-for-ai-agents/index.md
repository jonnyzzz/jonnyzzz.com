# Inside the Git Hooks: Tagging Every AI Agent Commit (Part 3)

**Date:** June 26, 2026  
**Author:** Eugene Petrenko  
**Tags:** ai-agents, ai-coding, git, infrastructure, workflow

---

This is the third part of the series. [Part 1]({% post_url blog/2026-06-20-auditing-git-for-ai-agents %})
laid out the approach — keep the keys away from the agent, a git proxy as the hard boundary, git hooks as
the lighter alternative. [Part 2]({% post_url blog/2026-06-22-inside-the-git-proxy-for-ai-agents %}) was the
build of the proxy. This one is the build of the **hooks**: the in-container layer you reach for when you
own the image but not the network path.

The job is the same two questions — *which commits did the agent produce, and did it touch only what we
allowed?* — answered from inside the sandbox instead of on the wire. A reminder from Part 1: this is
**best-effort observability, not a security boundary**. A sufficiently determined agent in its own sandbox
can defeat any of it. We build it anyway, because for the overwhelmingly common case where the agent is
just doing its work, it gives you clean provenance for almost nothing — and the proxy is still there as the
floor.

The plan: stamp a session-id [trailer](https://git-scm.com/docs/git-interpret-trailers) on every commit as
it is written, keep that tag alive across amend/rebase/squash, and on push capture a restorable copy of
what is going out. Four hooks do it — `prepare-commit-msg`, `commit-msg`, `post-rewrite`, `pre-push` — wired
in through `core.hooksPath`. Let me walk the load-bearing parts.

----

## Wiring: Hijack Every Hook Without Breaking the Repo's Own

Part 1 covered the install: bake the hooks into the image root-owned and read-only, and point
[`core.hooksPath`](https://git-scm.com/docs/git-config) at them in the system config so *every* repository
the agent touches — `/workspace` and any clone it makes later — runs them. But `core.hooksPath` is greedy:
it **replaces** `$GIT_DIR/hooks` entirely. The moment you set it, a project's own `.git/hooks/pre-commit`
stops firing. That is a regression you do not want to ship to developers who rely on their own hooks.

So the first thing each of our hooks does is run the repository's own hook of the same name, honor its exit
code, and only then do our work:

```text
run_local_hook(name, args, stdin):
    # resolve the MAIN repo's .git even from a linked worktree, and as an absolute path
    git_dir = git rev-parse --path-format=absolute --git-common-dir
    local   = "$git_dir/hooks/$name"
    if is_executable(local):
        exec local with (args, stdin)   # its exit code becomes ours — honor a rejection
    # else: nothing to chain, carry on
```

Two traps hide in those four lines. First, **recursion**: if you resolve the hook path through
`core.hooksPath` you point straight back at yourself and loop forever — so resolve the *literal*
`$GIT_DIR/hooks`, never the configured path. Second, **worktrees**: a linked worktree has its own private
gitdir, but the conventional hooks live in the main repo's `.git`. `--git-common-dir` resolves to the main
`.git` from anywhere, so a hook running inside a worktree still finds the project's real hooks.

For hooks that receive data on stdin (`pre-push`, `post-rewrite`), there is a third trap: you need that
stdin *twice* — once for your own logic, once to replay to the local hook — and command substitution
silently strips trailing newlines and mangles blank lines. So buffer stdin to a temp file and replay the
**exact bytes**:

```text
stdin_buf = mktemp(); read all of stdin into stdin_buf
... parse stdin_buf for our own work ...
run_local_hook(name, args, stdin=stdin_buf)   # byte-for-byte, not via $(...)
```

One more constraint shaped the whole library: it runs on the macOS dev host *and* the Linux agent image,
so it is written for **bash 3.2** — no associative arrays, no namerefs. Portability is a feature when your
hooks have to behave identically in two very different places

## Tagging: One Trailer, Re-Collected Every Time

The tag itself is a git *trailer* — a structured `Key: value` line at the foot of the commit message, the
same machinery as `Signed-off-by`:

```
Agent-Session: 2026-06-20T11:04:18Z-7f3a9c
```

The naive approach — append that line to the message — falls apart the first time someone squashes three
commits or rebases a branch. Trailers get duplicated, buried mid-message, or dropped. The robust approach
is to treat the trailer block as something you **recompute** on every message, not something you append
once:

```text
apply_tag(msgfile, sid):
    existing = all "Agent-Session:" values already in the message
    from_urls = session ids parsed out of any orchestrator URLs pasted in the body
    all = dedup(existing + from_urls + [sid])        # order-preserving, drop blanks
    body = message with the raw Agent-Session lines AND those URLs stripped out
    # re-emit ONE trailing trailer block, deduped, via the real tool
    git interpret-trailers --if-exists addIfDifferent --if-missing add \
        (one --trailer "Agent-Session: <v>" per v in all) <<< body  > msgfile
```

Three things matter here. We let [`git interpret-trailers`](https://git-scm.com/docs/git-interpret-trailers)
place the block — it knows where the trailer section ends and how to keep it well-formed, which hand-rolled
string-appending never gets right. We **re-collect** existing values before re-emitting, so a squash of
commits from different sessions *preserves every distinct* session id and *dedups identical* ones — the
audit trail survives history rewriting. And we also harvest ids out of any session URL the agent pasted
into the message body, so a commit references its origin even when the trailer was never added by hand.

This runs in **`prepare-commit-msg`**, the primary tagging point. It fires for commit, amend, merge,
cherry-pick and every rebase reword/squash/fixup path — and, as Part 1 noted, it is the one commit-time
hook that `git commit --no-verify` does **not** suppress, which is exactly why the tag lives there.

```text
# prepare-commit-msg
run_local_hook("prepare-commit-msg", argv, stdin)  || exit with its code
apply_tag(msgfile, resolve_sid())   || warn "tagging failed (continuing)"
exit 0
```

**`commit-msg`** is a thin backstop: `prepare-commit-msg` already covers every path, so this one only acts
if the final message somehow has no tag — a guard against a future regression, never the normal route. It
never blocks the commit

Where does the session id come from? From a fixed file the environment writes once per session — covered in
[Part 1]({% post_url blog/2026-06-20-auditing-git-for-ai-agents %}). The resolver reads the first line of
that file and sanitizes it into a trailer-safe token: keep the `:` so an ISO-8601 timestamp survives, drop
`/` so it can never break a path you later build from the id. No file, or a blank one, means "skip
tagging" — the hooks never block on a missing id.

## Provenance Across Rewrites

When the agent amends or rebases, commit hashes change, and a tag-by-hash audit trail would lose the
thread. [`post-rewrite`](https://git-scm.com/docs/githooks) closes that gap: git hands it
`<old-sha> <new-sha>` pairs on stdin (space-separated — *not* tab, a detail that has bitten many a hook),
and we append them to a per-session provenance log before delegating to the repo's own hook:

```text
# post-rewrite  (stdin: "<old> <new>" per line)
buffer stdin
for "<old> <new>" in stdin:
    append "<timestamp>  <mode>  <old>  <new>"  to  $ARTIFACTS/_provenance/<sid>.log
run_local_hook("post-rewrite", argv, stdin=buffer)
```

Now an `old → new` chain is recoverable even after the local history has been reshaped, and that log later
travels with the push capture

## Enforcement on Push: Re-Tag, or Bail Out

The commit hooks are easy to bypass — `--no-verify`, a tool that writes commits directly, an agent in a
hurry. [`pre-push`](https://git-scm.com/docs/githooks) is the net that catches untagged commits before they
leave the box. For each pushed branch it works out which commits are actually new, and if any of them lack
the tag, it rewrites them and **aborts the push** so the corrected commits go out on the retry — what you
might call "amend on push".

The first subtlety is **bounding the range**. git hands `pre-push` a line per ref —
`<local-ref> <local-sha> <remote-ref> <remote-sha>` — and the `remote-sha` is the authoritative "what the
server already has" boundary. Except when it is all-zero, which means a *brand-new* branch: there is no
remote tip, and if you naively take "everything reachable from local-sha" you will try to re-tag and
capture the entire history of the repo. So for a new branch, fall back to the merge-base against the
remote's existing tracking tips; if even that cannot be found, do not guess — skip:

```text
push_base(local_sha, remote_sha, remote):
    if remote_sha is not all-zero:  return remote_sha          # normal update
    tips = object names of refs/remotes/<remote>/*
    if no tips:  return ""                                     # cannot bound — caller must skip
    return git merge-base local_sha <tips...>                  # new branch: nearest known ancestor
```

(A small landmine worth flagging: `git merge-base --remotes` is **not** a thing. You have to enumerate the
tracking-tip object names and pass them explicitly.)

With a base in hand, the enforcement pass is straightforward — only rewrite real `refs/heads/*` updates
(skip deletions, and skip tags, since rewriting a tag ref would clobber it):

```text
# pre-push enforcement
need_retry = 0
for "<localref> <localsha> _ <remotesha>" in stdin:
    skip if deletion, or localref not under refs/heads/
    base = push_base(localsha, remotesha, remote)   ; skip if empty
    if any commit in base..localsha has no Agent-Session trailer and we have a sid:
        retag_range(base, localref, localsha, sid)   # checkout-free, see below
        need_retry = 1
if need_retry: exit 1   # "re-tagged commits; please re-run your push"
```

Checking a commit for the trailer is a one-liner thanks to git's own formatter —
`git show -s --format='%(trailers:key=Agent-Session,valueonly)'` prints the value or nothing.

### Re-Tagging Without a Checkout

Rewriting commits inside a hook is where most implementations reach for `git rebase` — and inherit all of
rebase's hazards: it checks out, it fights a dirty working tree, it can drop empty commits, and a failure
leaves rebase state lying around. We avoid all of it with [`git
commit-tree`](https://git-scm.com/docs/git-commit-tree), which builds a commit object from a tree with no
working-tree involvement at all:

```text
retag_range(boundary, tipref, tip, sid):
    map = {}                                  # old sha -> new sha
    for c in  git rev-list --reverse --topo-order  boundary..tip:     # parents before children
        tree     = c^{tree}
        newparents = [ map[p] or p  for p in parents(c) ]             # remap to rewritten parents
        msg      = apply_tag(message_of(c), sid)
        newc     = commit-tree tree (-p each newparent) -F msg \
                       with c's original author/committer name+email+DATE preserved
        map[c]   = newc
    git update-ref tipref  map[tip]           # move the branch to the rewritten tip
```

Two details make it correct. **Topological order, parents first**, with a parent-remap table: when you
rewrite a commit its children must be re-pointed at the *new* parent, or you fork history. And you must
**preserve the original author and committer identity and dates** (`GIT_AUTHOR_DATE`, `GIT_COMMITTER_DATE`,
and the name/email pairs) — otherwise the "re-tag" silently rewrites timestamps and authorship, which is
both wrong and alarming in a blame view. Because nothing is ever checked out, a dirty tree is fine and an
empty commit is fine; there is no rebase state to clean up if a step fails. This is the same
"rewrite the whole pushed suffix in topological order" idea Part 2 mentioned for the proxy — here is the
actual mechanism.

This only makes sense for a real branch ref. A delete, a detached-HEAD push, or a raw-SHA push has no
branch to move, so the hook skips the rewrite there rather than do something surprising.

## Capture on Push: a Restorable Copy, Never Blocking

After enforcement, a second pass captures what is going out — and unlike enforcement, capture **never**
blocks a push. If any of it fails, the developer's push still succeeds; the failure is logged and that is
all. Each piece is bounded to the push range (`base..local-sha`), and if the range is empty or cannot be
bounded, the whole capture is skipped rather than writing a degenerate artifact or dumping full history.

```text
# pre-push capture (per pushed ref, in a subshell so a failure is contained)
base  = push_base(...)            ; skip if empty
range = base..localsha
skip if  git rev-list --count range  == 0          # nothing new

git bundle create   bundle.bundle  localref --not base                 # restorable clone source
git rev-list --objects range | git pack-objects --no-thin --stdout  > pack.pack
git format-patch -o patches/  range                                    # human-readable, per commit
git rev-list --merges range  > merges.txt                              # format-patch omits merges
copy the provenance log + write metadata.json
```

A few choices worth calling out:

- **The non-thin pack.** Here is the contrast with Part 2 that I like. The proxy could not pass a flag to
  the agent's git — it had to *advertise* the `no-thin` capability and let the client comply. In a hook,
  **you are the client**, so you just say `git pack-objects --no-thin` and get a self-contained pack you can
  re-index anywhere. Same goal, opposite side of the wire.
- **Stream with `--stdout`.** Letting `pack-objects` write its own file drops it in the repo and then
  `rename()`s it into place — which fails with `EXDEV` when your artifacts directory is on a different mount
  than the repo (it usually is). Streaming to stdout and redirecting sidesteps the cross-mount rename
  entirely.
- **A bundle *and* patches *and* a pack.** They serve different masters: the
  [bundle](https://git-scm.com/docs/git-bundle) is a one-file restorable clone source, the patches are
  what a human actually reads in review, and the pack is the raw objects. Cheap to produce, and you will be
  glad of all three the day you need to reconstruct a branch the agent deleted.
- **`metadata.json` built with a JSON tool**, not string interpolation — branch names and URLs contain
  characters that turn hand-built JSON into a parsing bug. Let the tool escape them.

Everything lands under one auto-uploaded artifacts directory, and capture directories are named flat (slash
in a branch name becomes a dash) so a branch like `feature/x` does not blow up the path.

## The Limits, Again — Briefly

Everything in [Part 1's "hooks can be broken"]({% post_url blog/2026-06-20-auditing-git-for-ai-agents %})
still holds and I will not repeat it in full: `core.hooksPath` can be overridden from a per-user config or
`-c` on the command line, `git push --no-verify` skips `pre-push`, and an agent with `sudo` can simply
delete the hook directory. None of that is a defect — it is the definition of an in-sandbox layer. The
hooks make the honest, common case observable and cheap; when you need a *guarantee*, that is the proxy's
job, because the proxy is the one control the agent cannot reach.

There is also a softer failure mode the hooks lean into deliberately: they **warn rather than block**.
Every hook writes its warnings both to stderr and to a log in the artifacts tree, so a tagging or capture
hiccup is visible after the fact without ever having stopped the developer's commit or push. For
observability, a tool that breaks the thing it observes is worse than no tool.

## Where This Sits in the Series

Two builds, one goal. The [proxy]({% post_url blog/2026-06-22-inside-the-git-proxy-for-ai-agents %}) is the
wall outside the sandbox that the agent cannot route around; these hooks are the diligent assistant inside
it. Run the proxy when you control the network, run the hooks when you control the image, and run both when
you can — the hooks enrich the common case while the proxy guarantees the floor.

And both feed the same thing: a complete, attributed record of what every agent did to the code. That
record is not just an audit trail — it is the raw material for measuring a fleet of agents and making the
next run better, which is the larger system I am building now and will write about separately.

If you implement a version of this — a smarter tagging scheme, a cheaper capture, a hook trick I missed — I
would love to hear it on [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) or
[Twitter](https://twitter.com/jonnyzzz). And if your team is wiring AI Agents into real infrastructure and
wants a hand on the boundary and the audit trail, that is exactly the kind of problem I enjoy — reach out
and let's scope it together.

----

## Git Documentation Used in This Post

- [githooks](https://git-scm.com/docs/githooks) — `prepare-commit-msg`, `commit-msg`, `post-rewrite`, `pre-push`
- [git-config](https://git-scm.com/docs/git-config) — `core.hooksPath`
- [git-interpret-trailers](https://git-scm.com/docs/git-interpret-trailers) — recomputing the trailer block
- [git-commit-tree](https://git-scm.com/docs/git-commit-tree) — checkout-free commit rewriting
- [git-rev-list](https://git-scm.com/docs/git-rev-list) and [git-rev-parse](https://git-scm.com/docs/git-rev-parse) — ranges, `--git-common-dir`
- [git-bundle](https://git-scm.com/docs/git-bundle), [git-pack-objects](https://git-scm.com/docs/git-pack-objects), [git-format-patch](https://git-scm.com/docs/git-format-patch) — the capture artifacts

*Related reading on this blog:
[What Did the Agent Just Push? (Part 1)]({% post_url blog/2026-06-20-auditing-git-for-ai-agents %}),
[Inside the Git Proxy (Part 2)]({% post_url blog/2026-06-22-inside-the-git-proxy-for-ai-agents %}),
[Git Fork Pattern]({% post_url blog/2026-02-02-git-fork-pattern %}), and
[Efficient Git Replication]({% post_url blog/2019-04-09-git-replication %}).*