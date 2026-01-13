# Stevedore DynDNS: Dynamic DNS and HTTPS for Your Homelab

**Date:** January 02, 2026  
**Author:** Eugene Petrenko  
**Tags:** stevedore, dyndns, cloudflare, caddy, self-hosting, homelab

---

Stevedore gives me the GitOps loop I wanted on a Raspberry Pi. The next problem was
ingress: my home IP changes, certificates expire, and a hand-written reverse proxy
config does not stay boring for long.

So I built **stevedore-dyndns**. It is a companion service that runs as another
Stevedore deployment and keeps DNS, HTTPS, and routing in sync for the rest of your
services.

## Series: Stevedore on a Raspberry Pi

- [Stevedore: GitOps for your Raspberry Pi]({% post_url blog/2025-12-24-introducing-stevedore %})
- [Under the Hood: How Stevedore Works]({% post_url blog/2025-12-24-stevedore-architecture %})
- [Tutorial: Deploying Your First App with Stevedore]({% post_url blog/2025-12-24-getting-started-with-stevedore %})
- [Production Notes: Deploying Stevedore on a Raspberry Pi]({% post_url blog/2026-01-01-production-raspberry-pi-deployment %})
- [Stevedore DynDNS: Dynamic DNS and HTTPS for Your Homelab]({% post_url blog/2026-01-02-stevedore-dyndns %})

## What stevedore-dyndns does

It is a single container that combines a few boring building blocks:

- **Dynamic DNS**: In direct mode it updates root + wildcard A/AAAA records when your public IP changes; in proxy mode it maintains per-service A records for active subdomains (no AAAA).
- **HTTPS termination**: Caddy obtains and renews wildcard certificates via DNS-01.
- **Reverse proxy**: Subdomains route to internal services automatically (from Stevedore ingress or `mappings.yaml`; discovered services must publish ports to the host).
- **Service discovery**: Stevedore provides a token so dyndns can query ingress-enabled services (labels or ingress config).

The result is simple: `https://myapp.example.com` keeps working even if your ISP
changes your IP overnight.

> I wanted a boring ingress story that works on one small box, without Kubernetes
> and without clicking around in DNS dashboards.

## Two modes: direct or proxied

By default, stevedore-dyndns runs in **direct mode**: Cloudflare DNS points straight
to your host, and Caddy handles TLS.

For public services, I often enable **Cloudflare proxy mode**:

```bash
stevedore param set dyndns CLOUDFLARE_PROXY true
stevedore param set dyndns SUBDOMAIN_PREFIX true
```

That keeps the origin IP hidden and adds mTLS between Cloudflare and Caddy; dyndns
tries to set SSL mode to Full and enable Authenticated Origin Pull, but your API
token needs zone settings permissions (otherwise enable it manually), and Caddy
trusts `/etc/cloudflare/origin-pull-ca.pem`.
It is still free-tier friendly, which was one of my constraints.

Note: `SUBDOMAIN_PREFIX` changes hostnames to `app-zone.example.com` and is only needed when your `DOMAIN` is itself a subdomain (Cloudflare Universal SSL limitation).

## Quick setup

There is a guided script:

```bash
git clone git@github.com:jonnyzzz/stevedore-dyndns.git
cd stevedore-dyndns
./scripts/stevedore-setup.sh
```

It wires the repo into Stevedore, asks for Cloudflare credentials, and deploys the
service. Manual steps are documented in the project repo as well.

## What is still rough

This is intentionally single-node and Cloudflare-centric. If you need multi-region
failover or a vendor-agnostic DNS provider, this is not it (yet). The goal is to be
predictable and easy to reason about.

The project is here: [github.com/jonnyzzz/stevedore-dyndns](https://github.com/jonnyzzz/stevedore-dyndns)

<iframe src="https://www.linkedin.com/embed/feed/update/urn:li:activity:7416481232449863680" height="520" width="504" frameborder="0" allowfullscreen="" title="Embedded post"></iframe>