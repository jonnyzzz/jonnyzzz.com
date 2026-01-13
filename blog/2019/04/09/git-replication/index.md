# Efficient Git Replication

**Date:** April 09, 2019  
**Author:** Eugene Petrenko  
**Tags:** git, sync, devops, clouds

---

How do we deliver new commits to a bunch of copies of the same
Git repository on different machines? The naive way is to run `git fetch` (or `git pull`)
on every copy. That works, but it repeats the Git protocol negotiation,
SHA hash computations, delta application, and disk I/O on every CI agent
and on every developer laptop.

I want the same commits to arrive with less CPU and less waiting.
Let me describe the replication pattern that works for me.

Why bother?
- Faster clean checkouts on CI (and for demos).
- Lower load on the main Git server.
- Fewer random pauses in IDE Git operations for a whole team.
- Works with any Git hosting (GitHub, GitLab, bare).

Default: everyone hits Git directly:

```text
--------                               -----------
| Git  |  <---------------------  N *  | Clients |
--------                               -----------
```

The protocol is efficient, but the server still has to negotiate
with every client, recompute deltas, and send a unique `.pack`
file per request. Each client then verifies and indexes that pack.

Let's add a middle-man:

```text
--------        ---------              -----------
| Git  |  <---  | Proxy |  <----  N *  | Clients |
--------        ---------              -----------
```

`Git` is the main remote (GitHub.com or similar). The `Proxy`
is a bare mirror that lives closer to clients or CI machines.
We will reuse its pack files and a prebuilt checkout instead of
asking the main server to stream packs for every request.

## Setting up the Proxy

The proxy is just a bare clone:

```
git clone --mirror <main-url> proxy.git
```

Keep it up to date. Two options:
- Push notifications (webhook) from the main server that runs
  `git fetch --all --prune --keep` in `proxy.git`.
- A cron job that runs the same command every few minutes.

In many setups you already have such a clone: a CI server that
needs the repository, or a code review server. Reuse it.

Avoid running `git gc` on every client. 
Run GC on the proxy first,
then resync clients from it.

## Clean checkout once, reuse everywhere

A fresh clone is the slowest operation on a CI farm. We generate
two cached artifacts on the proxy after every fetch:
- A tarball of `.git/objects/pack` (no negotiation required).
- An optional `git archive` of a default branch for the working tree.

Both artifacts can be served over HTTP (a CDN works great).

Client steps for a clean checkout:
1. Download the packed objects tarball and unpack it into `.git/objects/pack`.
2. Download the working tree archive (if you care about files), unpack it.
3. Run `git reset --hard <commit>` to put the working tree at the exact
   commit you need. If the archive lags behind, do a quick `git fetch`
   from the proxy to fix heads; no objects will be downloaded because
   they are already on disk.

Why is it faster? We download static archives instead of asking Git to
compute and stream a new pack per client. SHA checksums and delta
resolution were already done once on the proxy.

## Incremental updates without negotiation

For regular updates we reuse pack files again. Each client stores a
`last-sync` timestamp. To update:
1. Copy new `.pack` and `.idx` files from `proxy.git/objects/pack`
   that are newer than the timestamp (HTTP, rsync, or a shared disk).
2. Update the timestamp.
3. Fix references:
   - Simplest: run `git fetch --all --prune --keep proxy`. It will be
     a reference-only update because all objects are already present.
   - If you already know the commit (CI build trigger), skip negotiation
     entirely and call `git update-ref` for the branch or detached HEAD.

The Git protocol still runs in step 3, but it does not need to send
a pack file, so the cost is tiny compared to a full fetch.

## What can go wrong?

- Not distributed. We trade some Git decentralization for speed. If
  the proxy is down, clients can always fall back to the main remote.
- Garbage collection. A GC on the proxy may drop objects still needed
  by a client. Prefer to rebuild the client from a fresh proxy snapshot
  instead of running GC locally.
- Thin packs. If a proxy receives a thin pack and we copy only new
  files, a client may miss a base object. Verify with
  `git verify-pack` and fall back to copying the full `objects/pack`
  directory or to a normal `git fetch` when needed.
- Integrity. Copying files is simple, but still check them. An
  occasional `git fsck` on the proxy helps to avoid surprises.

Bitmap indexes? They are nice to speed up proxy repacks
(`git repack -adb --write-bitmap-index`) but are not required
on the clients.

## Why this works

`git fetch` normally:
- Lists local heads and remote heads.
- Negotiates common commits.
- Asks the server to build a `.pack` with missing objects.
- Downloads the pack, verifies hashes, writes `.idx`, updates refs.

We still rely on Git for the last step (ref updates) but reuse the
already-built pack files from the proxy. That removes the CPU and disk
cost of building and indexing a new pack for every client.

This pattern works well for CI farms and for IDEs that keep their own
hidden clones. It is also a cheap way to host a Git mirror in a local
network. Give it a try and let me know how it works for you.