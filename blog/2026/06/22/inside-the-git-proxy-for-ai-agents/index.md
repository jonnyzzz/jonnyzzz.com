# Inside the Git Proxy: Capturing What an AI Agent Pushed (Part 2)

**Date:** June 22, 2026  
**Author:** Eugene Petrenko  
**Tags:** ai-agents, ai-coding, git, infrastructure, workflow

---

This is the second half of
[What Did the Agent Just Push?]({% post_url blog/2026-06-20-auditing-git-for-ai-agents %}). Part 1 made
the case for a **git proxy** as the hard boundary, set up the one rule that makes it work — the agent never
holds the real keys — and showed the *enforcement* half: rejecting any head outside the allow-list before a
byte reaches the server. Enforcement bounds the blast radius, and it is the part you can ship first.

This part is the *capture* half: how the proxy actually gets the traffic, reads what the agent pushed, and
keeps it recoverable. It is the deep end — protocol gymnastics, packfile internals, and the side-effects of
sitting in the middle of git's wire protocol.

Recall the shape of a push from Part 1: a ref-advertisement `GET /info/refs?service=git-receive-pack`, then
a `POST /git-receive-pack` carrying pkt-line commands followed by a `PACK`. The proxy already parsed those
commands and located the pack — everything below works on that pack.

----

### Make HTTPS the Only Way In

From my standpoint, the SSH is the best transport one should use with Git. On the other hand, 
Git supports multiple transports, and the tricks we are covering here are similar for all of them.

In our case, we decided to use HTTPS with token authentication, that requires much less additional 
setup than SSH. We are not using `git://` protocol in production, as you may assume.
An agent that can open an SSH connection to the server, but we specify no access keys.
The git proxy server URL is explained to the agent in prompt files. Agent has no token to
access the original Git server via HTTPS.

For HTTPS you have two ways in. Either the agent's `https_proxy` points at you and you **MITM** the TLS
tunnel with your own CA installed in the sandbox's trust store, or you publish a dedicated hostname the
agent's remotes point at directly. If you MITM, guard one thing: a client opens the tunnel with
`CONNECT host:443` and then sends an inner `Host:` header, and the two must match — reject a mismatch with
`421 Misdirected Request`, or an agent can `CONNECT` an allowed host and then ask for a different one,
slipping past your per-host policy.

Once the bytes are yours, **classify by an exact whitelist, not a prefix match.** Git's HTTP surface is
small and each endpoint has a fixed method, query shape and content type:

| Request                                                  | Operation | Notes                              |
|----------------------------------------------------------|-----------|------------------------------------|
| `GET …/info/refs?service=git-upload-pack`                | read      | smart fetch/clone discovery        |
| `GET …/info/refs?service=git-receive-pack`               | **write** | push discovery — classified early  |
| `POST …/git-upload-pack`                                 | read      | smart fetch                        |
| `POST …/git-receive-pack`                                | **write** | smart push                         |
| `GET …/info/refs` (no query), `…/HEAD`, `…/objects/…`    | read      | dumb protocol, read-only by design |
| anything else                                            | deny      | reject reserved git paths with 400 |

Two things fall out of this. A push is a *write* the moment you see its discovery `GET`, not just at the
`POST` — so the discovery request is the natural place to influence the push (we use it below). And under
this whitelist the dumb protocol is read-only: the one write path you allow is smart `receive-pack`, which
is the one place branch policy bites. (Git also has a legacy WebDAV-style HTTP push, `git-http-push`, that
writes *outside* `receive-pack` — so deny `DAV` methods and those paths too, or a write could sneak in
behind your back). One endpoint deserves a hard no: the dumb `objects/info/alternates` (and
`http-alternates`) can point the client at object stores *outside* your proxy, so reject it — otherwise an
allow-listed clone can quietly source objects from somewhere you don't audit.

### Capture: log every commit that was pushed

The proxy already knows *which refs* moved — that was enforcement, in Part 1. Provenance needs the
*commits*. We want to read the pack and log each commit's hash, author and subject — ideally store the pack
too, for offline recovery.

There is one obstacle. By default, git is allowed to send a **thin pack**: a pack whose objects may be
deltas against base objects that are *not in the pack*, because the receiver is assumed to already have
them ([gitformat-pack](https://git-scm.com/docs/gitformat-pack)). A thin pack is efficient on the wire and
miserable to parse in isolation — you don't have the bases. (It is possible to request missing
objects via the HTTP dumb protocol from the main Git server, I would not go this way).

The fix is a capability the protocol already defines. The server can advertise **`no-thin`**, and per the
spec *"A client MUST NOT send a thin pack if the server advertises the `no-thin` capability"*
([gitprotocol-capabilities](https://git-scm.com/docs/gitprotocol-capabilities)). So the proxy rewrites the
ref advertisement on its way back to the agent, injecting `no-thin` into the capability list. The agent's
git then sends a **self-contained** pack the proxy can parse on its own.

```text
on GET /info/refs?service=git-receive-pack:
    strip_header(request, "Accept-Encoding")        # advert comes back uncompressed so we can rewrite it
    advert = fetch_upstream_advertisement()
    advert = inject_capability(advert, "no-thin")   # rewrites the first ref line's pkt-line and its
                                                    #   4-byte length prefix; mind the pkt-line limit
                                                    #   (65520 total / 65516 of payload)
    return advert
    # if no-thin won't fit, you have two choices: fail CLOSED (reject the push) if you need a hard audit
    # guarantee, or fall back to storing the raw thin pack and resolving it later against the upstream
    # objects — but do not pretend you walked it; a thin pack is not self-contained
```

Two honest caveats here, because the details bite:

- **`no-thin` does not turn off delta compression.** It only guarantees that every delta's base is
  *inside the same pack*. Git will still delta-encode a commit against another commit in the pack. So your
  pack walker must resolve in-pack commit deltas — but only the commit objects, which are few and small.
  Trees and blobs you can inflate-and-discard. Memory stays bounded by the commit set, not by the pack
  size. It means we can unpack the PACK file and read the commits, trees and the file BLOBs without
  looking for additional objects in the parent repository.
- **Self-contained packs are bigger** than thin ones, and the gap is not subtle. In one test, injecting
  `no-thin` flipped a real push from a 490-byte thin pack (a ref-delta against a base the server already
  had) to a 5,697-byte self-contained one — and it overrode the client's hardcoded `--thin` with zero
  cooperation from the agent. You can reproduce the effect yourself: push one small commit and compare the
  `POST` body size with and without `no-thin` in the advertisement (`GIT_TRACE_PACKET=1` makes the framing
  visible). For a handful of commits that is a fine trade; for a 2 GB monorepo migration it is not. Know
  which one you are running.
- **BLOGs are not DIFFS**. Git stores the whole file content in BLOGs, which are in the commit. BLOBs
  do not show what was changed, it's the *actual content of the changed file**. Git packs BLOBs with
  delta compression on the PACK file. Should you want to find the actual change -- you still need to access
  the parent commit objects -> all tree objects they reference -> and the BLOBs of the previous revisions. 
  There can be multiple base objects in the merge-commits (aka commits with multiple parents).

Capture should happen *after* the server accepts the push, gated on the upstream result. The
receive-pack response carries a [report-status](https://git-scm.com/docs/gitprotocol-pack): `unpack ok`
plus a per-ref `ok <ref>` or `ng <ref> <reason>`. A push can *partially* succeed — `unpack ok` and then
`ng` on one ref — so don't log a commit as "pushed" until the server says `ok` for the ref that carries it.

```text
capture(response, pack):                           # runs only after the server accepted the push
    status = parse_report_status(response)         # truth is in the response body, NOT the HTTP code:
    if status.unpack != "ok": return               #   "unpack ok" can still be followed by "ng <ref> ..."
    accepted = [r for r in status.refs if r.result == "ok"]   # log ONLY the refs the server actually took
    if not accepted: return                        #   (a 200 can carry per-ref "ng" — never trust the 200)
    store(pack, key = f"{session_id}/{new_head}.pack")        # spool the pack to storage; no second copy
    for commit in walk_commits(pack, reachable_from=accepted):   # bases are in-pack thanks to no-thin, so
        log(session_id, commit.hash, commit.author, commit.subject)  # resolve commit deltas; drop blobs
```

Run the capture off to the side — a detached, best-effort task. If logging fails, the developer's push
must still succeed. Observability that breaks the thing it observes is worse than no observability

### A Pack Is Snapshots, Not Diffs

There is a deeper limit worth stating plainly, because it surprises people and it decides what you can
actually recover. **Git stores snapshots, not diffs.** A blob is the *whole* file, never a change to it;
the deltas you see *inside* a packfile (thin or not) are a storage-and-transport trick — one object encoded
against another to save bytes — and not the semantic change the agent made. When you resolve the pack you
get back whole files: the complete new version of everything that was touched, never a tidy "here is what
changed". So the pack, by itself, tells you the new state, not the edit.

To learn *what changed* you have to diff a commit against its parent — and that is where the pack runs out.
For commits *inside* the pushed range you are fine: a commit and its parent are both new, both in the pack,
so you can diff them from the pack alone. The gap is the **boundary** — the first new commit's parent is
the old head, and the old head's tree and the *old* versions of the changed files are precisely the objects
the pack omits, because the server already had them. A non-thin pack is self-contained for its *new*
objects, but it is silent about the past. (A thin pack looks tempting here, since its wire bytes encode the
changed blob as a delta against the parent's version — but that base blob still is not in the pack, so you
cannot apply it without fetching the parent anyway). And you cannot cheat by faking an empty advertisement
to make the client upload all of history: `receive-pack` does a compare-and-swap on each command's old
object id and rejects a mismatch, and rewriting that old id back would break a signed push.

This has a blunt consequence, and it is the real reason the next section exists. If the same file was
touched across several commits, you can reconstruct the chain of new snapshots from the pack — but turning
that into a readable history of *changes* needs the parent at every boundary. Lose those parent objects to
garbage collection and the diff is gone for good, even though you faithfully archived every pushed pack. So
capturing the agent's pushes is necessary but not sufficient: you also have to keep the **parents**
reachable. That is why you back up *heads* in git, not just archive packs — pin the heads so the old
commits, trees and blobs survive long enough to tell you what actually changed.

### Keep the objects alive: backup marker refs

There is a subtle way to lose the very data you just captured. The agent pushes to a branch, you record
it, the agent (or a cleanup job) deletes that branch, and now those objects are unreferenced on the server
and eligible for garbage collection. Your `.pack` in object storage survives, but the *server* no longer
has them.

The cheap fix is to pin each captured head with a **backup marker ref** — a second, ref-only push that
points a marker like `refs/heads/_captures/session-<id>/<branch>-<shortsha>` at the head the agent just
pushed. Because the head's objects are *already* on the server, this push transfers **no objects at all**:
it sends the canonical empty pack (a 32-byte pack with zero objects for SHA-1 repositories). It is fast,
and idempotent — on a name collision you resolve the existing marker and confirm it points at exactly
`new_head` before treating it as success (the short SHA in the name is a convenience, not a proof of
identity) — and it keeps the commits reachable and GC-safe until your retention sweep removes them.

```text
after a successful capture of <new_head> on <branch>:
    marker = f"refs/heads/_captures/session-{session_id}/{branch}-{short(new_head)}"
    # a create command is "<zero-id> <new_head> <marker>"; the objects are already upstream, so this
    # push carries the empty pack. It uses the proxy's OWN credential and skips the allow-list — the
    # proxy writes these markers, the agent never does
    receive_pack_push(zero_id, new_head, marker)
    # on a collision, resolve the existing marker and verify it == new_head, then treat as success
```

Fire it as a separate, isolated request — *not* a second command piggybacked into the agent's own push.
That distinction is load-bearing. If you inject your marker command into the client's `receive-pack` body
and the client used `git push --atomic`, then a failure of *your* command (a name collision, a slow host)
atomically fails the *agent's* real push. You would have turned your insurance policy into the thing that
drops the developer's work. A standalone ref push, sequenced after the agent's push reports `ok`, cannot
couple to it, and it leaves the agent's signed certificate untouched. Give it its own generous timeout
(real git hosts can be slow) and never loop it back through the forward proxy. It is independent and
best-effort — if it fails, you log it and move on.

One honest limitation, though, and it is worth saying out loud: **signed pushes can take the marker away
from you entirely.** If the upstream *requires* a valid push certificate on the capture namespace, you are
blocked both ways — you cannot add the marker to the agent's own push (that alters its signed command list
and breaks the signature), and a separate marker push would itself need a certificate, which the proxy
cannot produce without a signing identity of its own. So under mandatory signed-push you have two options:
give the proxy its own service key that the host trusts for `refs/heads/_captures/*` and let it sign its
marker pushes — a *different* signature than the agent's, made by the proxy as itself — or drop the
server-side marker altogether and lean on the `.pack` you already captured into your own storage, which
needs no ref on the host at all. The marker is insurance; when the host won't let you buy it, your own
captured pack is the policy that still pays out. You can workaround that by adding the secondary Git
repository, that is synchronized with the main repository, it will be used to keep all the captured
packs and markers, and without certificates. 

Two more things make the markers pay off. First, they are exactly what saves you from a **force-push or a
delete**: the marker pins `new_head`, so even if the agent later force-pushes its branch backward or
deletes it, the objects stay reachable through the marker and survive `git gc --prune=now`. Drop the
marker in your retention sweep and they become collectable again. Second, the marker is what makes
**recovery cheap**: a warm repository that already has `old_head` fetches only the `old_head..new_head`
range, and `git log old..new` plus `git show` reconstructs exactly the commits and patches that were
pushed — force-push included, since `A..B` means "reachable from B but not A". And this is where the
snapshot/diff problem from earlier gets solved almost for free: because *every* push gets its own marker,
the marker you wrote for the **previous** push pins what is now the **parent** of this one. The chain of
markers keeps each boundary's old side reachable, so the parent objects you need to compute a real diff are
still there — you backed up the heads as you went, exactly as that section argued. One caveat from the real
world: a custom ref namespace like `refs/captures/*` is not portable — some hosts honor only `refs/heads/*`
and `refs/tags/*` and silently reject the rest, so a lightweight **tag** is often the most portable pin.
Tags auto-follow into clones, though, so remember to clean them up after recovery

### Side-Effects to Watch

A proxy that parses pushes is a man-in-the-middle by design, and a few of its side-effects bite in
production rather than in the demo:

- **You have to buffer the command prefix before you can forward.** The ref commands sit in front of the
  pack, so policy can't run until you have read and held *that* much. You do not have to hold the whole
  pack in memory, though — once policy passes, stream or tee the pack to disk or object storage as it flows
  upstream. Either way, apply a size cap: an unbounded push, accidental or malicious, is a memory- and
  disk-exhaustion vector. This is buffering you are *adding* to the path; bound it deliberately.
- **Object ids are not always 40 hex characters.** Most parsers quietly assume SHA-1. A repository using
  the SHA-256 object format has 64-character ids, a different empty-pack size, and will be rejected as
  malformed by SHA-1-only code. Either handle both hash lengths or document the limitation loudly — a
  silent "malformed push" on a SHA-256 repo is a miserable thing to debug
  ([gitformat-pack](https://git-scm.com/docs/gitformat-pack)).
- **Signed pushes sign the heads, not the pack — so read them, never edit them.** `git push --signed`
  wraps the ref-update command list in a *push certificate* and GPG-signs it. The signature covers the
  affected heads — each `old-id new-id refname` update — plus the pusher identity, the destination URL and
  a server-issued nonce. It does **not** cover the pack: each `new-id` is a SHA, so signing the heads
  already certifies the objects by hash ([gitprotocol-pack](https://git-scm.com/docs/gitprotocol-pack)).
  The tempting conclusion is "then a proxy can never handle a signed push." Not quite. The proxy never
  needs to *touch* that list — it reads it and decides: forward the certificate byte-for-byte when every
  head is allowed, reject the whole push when one is not. Enforcement, capture and markers all survive,
  because none of them edit the signed bytes. What signed push removes are the edit-the-list shortcuts —
  remap an old id, inject an extra ref, strip a disallowed one — each of which stops the signature
  verifying. Two consequences are worth pinning down:
    - **Filtering is all-or-nothing.** You cannot quietly drop one disallowed ref from a multi-ref push;
      you forward it whole or reject it whole. Reject is the safe default, so the boundary still holds — you
      just lose the ability to *partially* allow a signed push.
    - **Relay the nonce untouched.** The nonce lives in the advertisement; when you inject `no-thin` there,
      keep the `push-cert` nonce intact, or the client's certificate will not verify upstream.

  This is also the deeper reason capture and markers stay strictly out of band: they must never appear in
  the signed command list, or they would invalidate the very push they are trying to record.
- **HTTP success is not git success.** Worth repeating because it is the easiest one to get wrong: a `200`
  from the server's git backend does not mean the objects were stored. The truth is in the `report-status`
  body. Gate every capture on it.

None of these are reasons not to build the proxy. They are the difference between one that works on your
laptop and one you can leave running in front of a fleet.

## Where This Leaves You

That is the whole proxy: intercept HTTPS, force a parseable pack, gate capture on the server's real answer,
pin the heads so nothing you captured gets collected, and respect the protocol's sharp edges — signed,
atomic, partial-success. None of it is exotic; it is mostly careful reading of the Git wire-protocol docs
linked below. The payoff is the thing Part 1 was after: you know exactly what every agent pushed, you can
recover it, and only the heads you allowed ever change upstream

One more reason to learn these internals now rather than wait: the substrate is being rebuilt. The
agent-first forges and next-generation version-control systems landing in 2026 — Cursor's
[Origin](https://explainx.ai/blog/cursor-origin-git-hosting-github-alternative-ai-agents-2026) and Epic's
[Lore](https://github.com/EpicGames/lore), both of which I touch on in
[Part 1]({% post_url blog/2026-06-20-auditing-git-for-ai-agents %}) — still move objects, still pack and
delta them, still have to tell you what an agent changed. The transport and the storage may shift under
you, but pkt-lines, packs, thin-vs-self-contained, and "snapshots, not diffs" are the vocabulary you carry
across all of it.

If you came straight here for the mechanics, the *why* — credential isolation, the lighter git-hooks
alternative, and how to choose between them — is in
[Part 1]({% post_url blog/2026-06-20-auditing-git-for-ai-agents %}).

And if your team is building this for real and wants a second pair of hands on the proxy or the capture
pipeline, this is exactly the kind of problem I enjoy. I am happy to **consult and help you build it** —
reach out on [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) and let's scope it together.

Given all the information -- my implementation we log all the pushes intercepted to a log file. We
assume the Git server will keep all objects (in our case it does) and run pinning job outside of
the main flow.

----

## Git Documentation Used in This Post

The proxy is mostly careful reading of the public Git wire-protocol and format docs:

- [gitprotocol-http](https://git-scm.com/docs/gitprotocol-http) — the smart HTTP transport
- [gitprotocol-common](https://git-scm.com/docs/gitprotocol-common) — pkt-line framing and limits
- [gitprotocol-capabilities](https://git-scm.com/docs/gitprotocol-capabilities) — `no-thin`, `report-status`
- [gitprotocol-pack](https://git-scm.com/docs/gitprotocol-pack) — the receive-pack exchange, status report, push certificate
- [gitformat-pack](https://git-scm.com/docs/gitformat-pack) — pack and thin-pack format, object hashing

For the deeper design notes, the Git project keeps a set of technical documents under
[Documentation/technical](https://github.com/git/git/tree/master/Documentation/technical) in the source
tree — the protocol and format docs themselves were promoted to the top-level `gitprotocol-*` and
`gitformat-pack` man pages linked above.

*Related reading on this blog:
[What Did the Agent Just Push? (Part 1)]({% post_url blog/2026-06-20-auditing-git-for-ai-agents %}),
[Git Fork Pattern]({% post_url blog/2026-02-02-git-fork-pattern %}), and
[Efficient Git Replication]({% post_url blog/2019-04-09-git-replication %}).*