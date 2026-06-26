# What Did the Agent Just Push? Auditing Git for AI Agents

**Date:** June 20, 2026  
**Author:** Eugene Petrenko  
**Tags:** ai-agents, ai-coding, git, infrastructure, workflow

---

You hand a repository to an autonomous AI Agent and let it work. It clones, branches, commits, pushes,
maybe opens a pull request. A few minutes later it tells you it is done. Two questions stay on the table,
and neither has a comfortable answer:

- **Which commits did it actually produce?** Not the summary it wrote for you — the real objects that
  landed on the server.
- **Are you sure it only touched the branches you allowed?** One confused agent force-pushing `main` is
  a bad afternoon.

I have been running fleets of agents on the same codebases for a while now (see
[Orchestrating AI Fleets]({% post_url blog/2026-01-30-orchestrating-ai-fleets %}) and the
[Git Fork Pattern]({% post_url blog/2026-02-02-git-fork-pattern %})), and the more agents you run, the
more these two questions turn from curiosity into operational risk. This post is about answering them at
the layer where the truth lives: **git itself**.

This post is the approach: why this is a git problem, the one rule that makes everything else possible, and
the two mechanisms — a git proxy and git hooks — at a level you can reason about and act on. The deepest
wire-protocol mechanics of the proxy are involved enough that they get their own follow-up; here we cover
the shape and the decisions, with enough pseudo-code that your AI Agent can start implementing it in your
stack.

----

## Why This Is a Git Problem, Not a Policy Document

The naive answer is "just tell the agent which branches it may touch." That is a policy. Policies are
suggestions to a process that has a shell, a network, and a strong urge to finish its task. Agents are
smart — give one a constraint phrased as a request and it may find a creative way around it, not out of
bad intent but because working around obstacles is literally what we trained it to do.

So we do not rely on asking nicely. We rely on two properties:

- **Blast radius** — only the heads we selected can change on the real server, enforced somewhere the
  agent cannot route around.
- **Provenance** — every commit the agent created is captured and attributed, so we can recover, review,
  and audit it after the fact. This will be a great source for iterative learning later.

There are two ways to get there. The first is a **git proxy** that sits outside the agent's sandbox — the
hard boundary. The second is **git hooks** baked into the sandbox image — a lighter, best-effort layer for
when you own the image but not the network path. We use the proxy as the real wall and treat hooks as
extra telemetry. Here is why.

## The One Rule Underneath Everything: Don't Give Agents the Real Keys

Before any proxy or hook, there is a decision that makes the rest possible.

**The agent never holds the credentials to the real git server.**

Inside the sandbox, the agent gets a short-lived, scoped token that authenticates it to *our* endpoint —
not to GitHub or Space, not to your internal git host. We inject that token the boring way: a git credential helper
or a URL rewrite, never the real key on disk. The real push credential lives in the proxy, which the agent
cannot read. When a push is allowed, the proxy authenticates upstream with its own service credential.

This is the property that survives a clever agent. A sandbox is a permission boundary, and inside its own
sandbox an agent may have enough rights to do almost anything — read its environment, rewrite files,
disable the tooling we installed. If the real key were anywhere in that environment, a determined agent
could find it and talk to the Git server directly, and every control we built would be decoration. Because the
key is *not* there, the worst an escaped agent can reach is the proxy — and the proxy enforces policy and
holds the key. The blast radius is bounded by where the credential lives, not by how well-behaved the
agent is

I want to note – the pattern how we are going to limit the agent push/pull operations is not standard,
and potentially is hard-to-impossible to implement out of the box with GitHub, Space or any third-party Git host.
Agentic AI opens yet another direction for us -- software is now very cheap to build, given you know how. 

Below we explain enough ideas to implement it. Git supports multiple protocols, including HTTP, SSH, ~~and Git over TCP~~.
We decided to use HTTP below, but the same technique can be applied to other protocols as well, mainly to SSH.

## Solution 1: The Git Proxy — the Hard Boundary

A git push over HTTP is a surprisingly inspectable conversation. If you put a proxy on the path between the
agent and the server, you can read the whole exchange, decide whether to allow it, and capture everything
that flows through — without the agent being able to tell the difference, and without it being able to go
around you, because it has nowhere else to go

### What a push actually looks like on the wire

Git's "smart HTTP" protocol does a push in two HTTP requests
([gitprotocol-http](https://git-scm.com/docs/gitprotocol-http)):

1. **Ref advertisement** — `GET /info/refs?service=git-receive-pack`. After a `# service=git-receive-pack`
   header line and a flush, the server lists every ref and its current object id, and on the *first* ref
   line it appends a NUL byte followed by the
   [capabilities](https://git-scm.com/docs/gitprotocol-capabilities) it supports.
2. **The push itself** — `POST /git-receive-pack`. The body is a sequence of commands ("update
   `refs/heads/x` from `<old>` to `<new>`") followed by a `PACK` — the binary blob of objects being
   transferred.

The advertisement, the command list and the status report are all framed in **pkt-lines**: a 4-byte hex
length prefix in front of each chunk, with a special `0000` "flush" packet as a separator
([gitprotocol-common](https://git-scm.com/docs/gitprotocol-common)). The `PACK` payload itself is raw
bytes that follow the command section. That framing is the whole reason a proxy can parse the stream
cheaply — you always know where the next record starts.

### Enforcement: reject the heads you didn't allow

This is the easy and most valuable half. The `ref-update` commands sit in plain pkt-lines at the front of the
POST body, *before* the pack. Parse them, compare each target ref against your allow-list, and refuse the
ones that don't match — before a single byte reaches the real server.

```text
on POST /git-receive-pack(body):
    # read pkt-lines until the 0000 flush that ends the
    # command list; the pack begins right after it.
    # --signed wraps the commands in a push-cert ...
    # push-cert-end block (then push-options): parse the
    # commands from inside it and forward the cert
    # byte-for-byte — the signature covers it
    commands, pack = split_at_pack(body)

    for (old, new, ref) in parse_commands(commands):

        # e.g. only refs/heads/agent/* may change
        if not allowed(ref):                      
            return reject(ref, "ref not in allow-list")

        if is_delete(new) and not allow_deletes(ref):
            return reject(ref, "deletes not permitted")

    # only now, with our real credential
    response = forward_upstream(body)

    # the audit trail — the capture step, in a follow-up
    capture(response, pack)
```

Because the proxy holds the credential and the agent does not, this is a wall, not a request. An agent
that dislikes the wall cannot push around it — its token only opens the proxy.

That is the enforcement half — the part that bounds the blast radius, and the part you can ship first. The
other half is *capture*: getting the traffic to the proxy in the first place, reading the pushed pack,
logging every commit, and keeping the objects alive for recovery. It turns out to be a meaty topic on its
own — MITM and endpoint classification, thin packs and the `no-thin` trick, why a pack gives you whole
files and not diffs, backup marker refs, and the side-effects of sitting in the middle of a signed, atomic
protocol — so I'll give the build its own follow-up post. If
you only ever do one thing, do enforcement; if you want the audit trail too, that follow-up is where it
gets built.

## Solution 2: Git Hooks — the Lighter, In-Container Alternative

The proxy needs you to control the network path. Sometimes you don't — you control the *image* the agent
runs in, but the egress is whatever it is. In that case [git hooks](https://git-scm.com/docs/githooks) get
you most of the provenance, with none of the wire-protocol work.

The idea: stamp every commit with a session id as it is created, and capture artifacts on push.

- **`prepare-commit-msg`** is the primary tagging point. It fires for commit, amend, merge, cherry-pick and
  the rebase reword/squash/fixup paths — and, crucially, it is **not** suppressed by `git commit
  --no-verify` (unlike `pre-commit` and `commit-msg`, which are). That is exactly why it is the *primary*
  tag: the one commit-time hook the agent can't wave away. Have it append
  a [trailer](https://git-scm.com/docs/git-interpret-trailers) like `Agent-Session: <id>` to the message. A
  trailer is a structured `Key: value` line at the end of the message, the same machinery as
  `Signed-off-by`, so it survives rebases and you can grep for it later. Re-collect existing values and
  re-emit one block, so a squash *preserves distinct* sessions and *dedups identical* ones.
- **`commit-msg`** is a thin validator — a second chance to confirm the trailer is present. Like the
  others, it only observes and never blocks the commit.
- **`post-rewrite`** records old→new commit mapping after amend/rebase, so provenance follows the rewrite.
  (Mind the detail: its stdin is *space*-separated, not tab.)
- **`pre-push`** is the enforcement-and-capture net. If it finds an untagged commit, it rewrites the whole
  pushed suffix in topological order with a checkout-free
  [`git commit-tree`](https://git-scm.com/docs/git-commit-tree) — no rebase, so no dirty-tree or
  empty-commit hazards — re-parenting each descendant onto its rewritten ancestor (and keeping every parent
  of a merge with repeated `-p`), then moves the branch and **aborts the push** so the corrected commits go
  out on the retry. That auto-rewrite only makes sense when the pushed `<local-ref>` is a real
  `refs/heads/*` branch; for a delete, a detached-HEAD push or a raw-SHA push there is no branch to move, so
  abort with instructions instead. On a clean push it captures — a
  [`git bundle`](https://git-scm.com/docs/git-bundle) (validate it with `git bundle verify`), per-commit
  patches, and a small `metadata.json`. Be honest about what this is, though: `pre-push` fires *before* the
  remote answers, so these are **attempted-push artifacts** — they record what the agent tried to send, not
  what the server finally accepted. For "what actually landed", you need the proxy or a server-side hook.

To make the hooks apply to *every* repository — `/workspace` and any clone the agent makes later — wire
them through [`core.hooksPath`](https://git-scm.com/docs/git-config) rather than copying files into each
`.git/hooks`. Bake the hooks into the image root-owned and read-only, and set `core.hooksPath` in the
root-owned `/etc/gitconfig`.

```text
# Dockerfile (sketch)
COPY --chmod=555 --chown=root:root githooks/ /opt/githooks/
RUN git config --system core.hooksPath /opt/githooks
# resolve one canonical Agent-Session id in the entrypoint and write it to a fixed, well-known FILE
# (say /.session_id) that the hooks read — NOT an env var. A file is harder for the agent to unset or
# forge than the environment, and it survives sub-shells and `git` wrappers. Pre-create it owner-writable
# in the image (the entrypoint runs non-root); a missing or blank file just means "skip tagging" — the
# hooks still never block.
```

Why a file and not the obvious environment variable: the agent shares that environment. It can `unset` the
variable, override it, or spawn `git` with a scrubbed env — the same class of bypass we just saw with
`GIT_CONFIG_*`. A fixed path the entrypoint writes once, before the agent runs, is a smaller target. It is
still inside the sandbox, so still defeat-able by a determined agent — but it removes the easy footgun, and
that is the right bar for a best-effort layer.

### Hooks Can Be Broken by the Agent or an IDE — and That's Expected

Here is the part most write-ups skip, and the reason hooks are the *second* solution, not the first.

A hook runs *inside the agent's sandbox*, which means it lives in a place where the agent often has enough
permissions to defeat it. The honest list of holes:

- **Config precedence runs the wrong way for you.** It is tempting to think `/etc/gitconfig` is
  authoritative because it is "system". It is the opposite — system config is the *lowest* precedence, and
  a per-user `~/.gitconfig` overrides it ([git-config](https://git-scm.com/docs/git-config), SCOPES). So an
  agent that can write its own global config can point `core.hooksPath` somewhere empty. Root-owned
  read-only files raise the bar, but precedence is not on your side.
- **And precedence is only the easy bypass.** `git -c core.hooksPath=…` on the command line, a repo-local
  `.git/config`, or the `GIT_CONFIG_COUNT` / `GIT_CONFIG_NOSYSTEM` environment variables all override the
  system file too. A `git` wrapper that scrubs `GIT_CONFIG_*` and refuses `-c core.hooksPath=` would close
  these, but now you are maintaining a wrapper — and you are still inside the sandbox.
- **`git push --no-verify` skips `pre-push`** entirely, unless you also wrap the `git` binary.
- **A sufficiently privileged agent can just remove the hooks.** In a dedicated sandbox the agent may well
  have `sudo` or own the filesystem. If it decides to delete `/opt/githooks`, it can.

We do not treat any of this as a defect. **Hooks are best-effort observability, not a security boundary.**
They give you clean provenance for the overwhelmingly common case where the agent is doing ordinary work,
and they cost almost nothing. The moment you need a guarantee rather than a strong default, you are back to
the proxy — because the proxy is the one control the agent cannot reach, and the credential isolation
behind it is the one fact the agent cannot wish away.

That is the whole reason for the ordering. Proxy first, hooks as a helpful layer on top.

## The Two Solutions, Side by Side

| Property                               | Git Proxy (Solution 1)              | Git Hooks (Solution 2)             |
|----------------------------------------|-------------------------------------|------------------------------------|
| Where it runs                          | Outside the sandbox, on the path    | Inside the sandbox image           |
| Can the agent bypass it?               | No — it holds the keys, agent can't | Yes — `--no-verify`, sudo, config  |
| Enforces blast radius                  | Yes, before bytes reach the server  | Best-effort (`pre-push` only)      |
| Captures every commit                  | Yes (raw pack if `no-thin` skipped) | Attempts only, until a hook is off |
| Needs control of the network           | Yes                                 | No                                 |
| Needs control of the image             | No                                  | Yes                                |
| Right mental model                     | A wall                              | A diligent assistant               |
| Access possible outside of the session | Controlled by the proxy             | Controlled by the Git Hosting      |

If you can run only one, run the proxy. If you can run both, the hooks make the common case richer while
the proxy guarantees the floor.

The long answer actually is to design and use the combination of both. For example, I believe that we
still need to keep track of all changes that were created by the AI Agent; it will help in the future us
better understand what happened, how quality and other project metrics were affected. It will definitely
help us to improve the agent's performance and the project's quality. This information will be necessary
to measure the impact of the agent on the project.

We are missing __Solution 3__. The pipeline to mark, backup, and analyze all the AI-made changes at scale. I'm
building it now.

## Meanwhile, Git Itself Is Being Rebuilt for Agents

It is worth zooming out, because the ground under all of this is moving. In June 2026 two projects landed
that take the same problem somewhere very different. **Cursor Origin**
([overview](https://explainx.ai/blog/cursor-origin-git-hosting-github-alternative-ai-agents-2026)) is a git
*forge* built for agents rather than humans — its whole premise is that when dozens of background agents
clone, branch and push against one repository at once, git's human-scale assumptions become the bottleneck.
And [**Lore**](https://github.com/EpicGames/lore), Epic Games' new open-source version control system,
rebuilds the *substrate* — content-addressed, local-first, and equally at home with code and the
multi-gigabyte binaries that games and film drag around.

Two different layers, one signal: version control is being rethought for a world where most commits are not
typed by a person. That does not retire anything in this post. Most teams still run plain git against
GitHub, GitLab or an internal host today — and even an agent-first forge has to answer the same two
questions this whole write-up is about: *which commits did the agent produce, and did it touch only what we
allowed?* The boundary and the audit trail travel with you whatever the substrate; the proxy and the hooks
are how you get them on the git you already have.

## Conclusion: AI Automation Is Not Just Running the Jobs

It is easy to think the hard part of agent automation is getting the agent to *do* the work. It is not.
The agent does the work happily. The hard part is everything around the work:

- **Bound the blast radius.** Assume the agent is capable and occasionally wrong, keep the real
  credentials out of its reach, and put enforcement somewhere it cannot route around. A boundary the
  agent can edit is a preference, not a boundary.
- **Collect the data.** Every commit, every push, attributed to a session and stored. Not because you
  expect disaster, but because that log is the raw material for the *next* iteration — which prompts
  produce which diffs, where agents go off the rails, what a good run looks like versus a bad one. You
  cannot improve a system you cannot see, and an agent that pushes into a black box teaches you nothing.

That second point is the one our team keeps coming back to. The capture is not just an audit trail; it is a
feedback loop. The same data that lets you recover a lost branch lets you measure your fleet and tune it —
the kind of self-improvement loop I wrote about in
[the AI Agent roadmap research]({% post_url blog/2026-04-28-ai-agent-roadmap-research %}) and the
[multi-agent orchestration]({% post_url blog/2026-02-06-run-agent-multi-agent-orchestration %}) work. Give
agents room to run, take away the keys to the things they shouldn't touch, and write down everything they
do. Then read it back and make the next run better.

The mechanics of the proxy — how it intercepts the traffic, forces a parseable pack, logs every commit, and
pins the objects so nothing gets garbage-collected — are involved enough to deserve their own follow-up
post: [Inside the Git Proxy: Capturing What an AI Agent Pushed (Part 2)]({% post_url blog/2026-06-22-inside-the-git-proxy-for-ai-agents %}).
And the lighter, in-container alternative — the git hooks that stamp a session id on every commit and
capture each push from inside the sandbox — gets its own build in
[Inside the Git Hooks: Tagging Every AI Agent Commit (Part 3)]({% post_url blog/2026-06-26-inside-the-git-hooks-for-ai-agents %}).

If you have built something similar — a different boundary, a smarter capture, a hook trick I missed — I
would love to hear it. Find me on [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) or
[Twitter](https://twitter.com/jonnyzzz), and tell me what your agents tried to get away with.

And if your team is wiring AI Agents into real infrastructure and wants a second pair of hands on the
isolation and audit layer — the proxy, the credential boundary, the capture pipeline — this is exactly the
kind of problem I enjoy. I am happy to **consult and help you build it**: from a quick architecture review
to designing the whole thing with your team. Reach out on
[LinkedIn](https://www.linkedin.com/in/jonnyzzz/) and let's scope it together.

----

## Git Documentation Used in This Post

Everything above leans on the public Git documentation rather than any one implementation:

- [gitprotocol-http](https://git-scm.com/docs/gitprotocol-http) — the smart HTTP transport
- [gitprotocol-common](https://git-scm.com/docs/gitprotocol-common) — pkt-line framing
- [gitprotocol-capabilities](https://git-scm.com/docs/gitprotocol-capabilities) — capabilities on the advertisement
- [githooks](https://git-scm.com/docs/githooks) and [git-config](https://git-scm.com/docs/git-config) — hooks and `core.hooksPath`
- [git-interpret-trailers](https://git-scm.com/docs/git-interpret-trailers), [git-bundle](https://git-scm.com/docs/git-bundle), [git-commit-tree](https://git-scm.com/docs/git-commit-tree), [git-index-pack](https://git-scm.com/docs/git-index-pack) — the hook toolbox

The wire-protocol and packfile internals — `report-status`, the pack format, push certificates — are
covered in the follow-up post.

*Related reading on this blog:
[Inside the Git Proxy (Part 2)]({% post_url blog/2026-06-22-inside-the-git-proxy-for-ai-agents %}),
[Inside the Git Hooks (Part 3)]({% post_url blog/2026-06-26-inside-the-git-hooks-for-ai-agents %}),
[Git Fork Pattern]({% post_url blog/2026-02-02-git-fork-pattern %}),
[Efficient Git Replication]({% post_url blog/2019-04-09-git-replication %}), and
[the code review bottleneck]({% post_url blog/2026-01-16-code-review-bottleneck %}).*