# OAuth2-Bro: Building Authentication with AI Agents

**Date:** September 13, 2025  
**Author:** Eugene Petrenko  
**Tags:** oauth2, authentication, ai-coding, go, ide-services, docker, kubernetes

---

OAuth2 server with implicit IP-based authentication in Go, with integration tests for JetBrains IDE Services

A few months ago, I started getting recurring questions from JetBrains IDE Services customers about
IP-based authentication scenarios. Universities with shared computers, remote development servers, 
internal microservices behind firewalls – all needed OAuth2 integration without the complexity of managing 
client credentials. The pattern was clear, but the existing solutions weren't quite right.

So I built [OAuth2-bro](https://github.com/jonnyzzz/oauth2-bro) – an OAuth2 server that authenticates
users based on their IP address. No client credentials to manage, no passwords to rotate, just straightforward
network-based identity. The name? Inspired by Orwell's Big Brother, but instead of watching you, this
one just checks your IP address. The Brother knows who you are given your network address at the corporate network.

## The Problem

In JetBrains IDE Services, we help companies manage AI and Developer Tools at
scale –- AI Enterprise, License Vault, IDE Provisioner, Code With Me Enterprise. A common integration
challenge kept surfacing: customers needed OAuth2 endpoints for their internal tooling,
but traditional OAuth2 flows created friction in specific environments, or a customer does not maintain
a compatible authentication system.

Think about a university classroom where students rotate through shared workstations.
Or development servers accessed through a secure VPN where the network itself provides
authentication. These scenarios don't map well to traditional OAuth2 patterns. You don't
want to provision credentials for every possible client. You don't want users managing
API keys for internal services.

The solution needed to be simple: if you're on the right network, you're authenticated.
OAuth2-bro implements standard OAuth2 flows but derives identity from network location
rather than client credentials.

## The Architecture

OAuth2-bro operates in two modes. In *Bro Mode*, it runs as a standalone OAuth2 provider
with standard `/login`, `/token`, and `/jwks` endpoints. In *Proxy Mode*, it acts as a sidecar
container that intercepts requests and injects JWT tokens automatically.

The implementation is straightforward Go -– RSA-signed JWTs, CIDR-based IP validation,
optional HTTPS with separate ports for internal/external access.
It handles authorization codes, refresh tokens, and access tokens with configurable
lifetimes. For production deployments across multiple nodes, you bring your own RSA
keys to keep JWKS stable.

What makes it useful is what it doesn't do. No user database, no credential storage,
no persistent state. Just stateless authentication based on network topology. Deploy
it as a Docker container or as a Go binary executable, configure your IP ranges, and you're done.

## Building with AI Coding Tools

Here's where things get interesting. I built OAuth2-bro almost entirely with AI coding agents.
This wasn't a toy project – it's production-ready code with integration tests, unit tests, 
proper error handling, and comprehensive documentation. The experience taught me a lot about
how we'll be building software in the near future. And that future is already here!

In the experiment I used JetBrains Goland, JetBrains Junie, Claude Code, Aider,
Cursor, Copilot, AI Assistant, MCPs, and probably a few more tools.

### The Workflow and the Spec

My approach was simple but effective: specs first, then AI execution. For every feature, I would:
1. Write a detailed design document describing the behavior, edge cases, and integration points
2. Specify the testing requirements – what needs to work, what should fail gracefully
3. Feed this to an AI coding agent and let it implement
4. Review the generated code, run tests, iterate

I experimented with nearly every major AI coding tool available. Cursor and GitHub Copilot in various IDEs.
JetBrains' AI Assistant and the upcoming Junie. Claude Code both in Goland and standalone. VSCode with
different AI extensions. Each has strengths, and I ended up using all of them at different stages.

What surprised me was how well this workflow scaled. The project has proper OAuth2 compliance,
handles edge cases correctly, and includes both HTTP and HTTPS server implementations with comprehensive
testing. Most of this code was written by AI agents following specifications. Some specifications
were improved with AI.

### What Worked

The key was being specific in the specs. When I wrote "implement OAuth2 authorization code flow with
5-second expiration and RSA signature verification," the AI produced working code. When I said
"make this work," it guessed wrong.

Integration tests were crucial. OAuth2 has well-defined behavior –- authorization codes expire,
refresh tokens work across sessions, JWKS endpoints return proper public keys. Tests caught the
places where AI-generated code deviated from the specification.

Code review remained essential. AI agents are excellent at translating specifications into code,
but they make subtle mistakes. They might use the wrong cryptographic primitive, mishandle an error
case, or implement OAuth2 flow slightly wrongly. Having tests helped catch these, but human review was
the final safeguard.

The combination worked remarkably well: human judgment on architecture and specifications, AI execution
on implementation, automated tests for correctness, and human review for subtleties.

### What I Learned

Working with AI coding agents reveals patterns about software development itself. Good specifications
matter more than ever. When you can't rely on an experienced developer to "know what you mean," you need
to be explicit. This discipline improves code quality.

Testing becomes even more critical. You can't assume the implementation matches your mental
model –- you need tests that verify actual behavior. AI-generated code often works for happy paths
but fails on edge cases unless you specify them.

The role of the developer shifts. Instead of writing every line, you're architecting systems, writing
specifications, designing tests, and reviewing implementations. It's closer to being a technical lead
who happens to have a swift team that needs detailed guidance.

Never let a part of the system or tests be implemented without your control. That is so easy to
give up reviewing, say on integration tests. And if that happens, it's much cheaper to ask
an AI agent to re-write these tests in a more digestible manner, instead of manually refactoring
that code again. With the current tools, code-generation turns out to be very inexpensive, and the main
problem is to get the right code written.

## The Vision Forward

OAuth2-bro works today for real production scenarios. You can run it in your Kubernetes cluster,
configure it for your network topology, and integrate it with your services. The code is
Apache 2.0 licensed -– fork it, extend it, use it however you need. I will appreciate you letting me know
or/and pull requests with your improvements.

But there's a bigger point here. This project demonstrates a new development workflow. Specifications
drive implementation. AI agents handle the mechanical work. Tests verify correctness. 
Humans provide judgment and architecture.

We're at an inflection point in software development. The tools are good enough to be genuinely
useful, but they still require careful guidance. The developers who succeed in this new environment
will be those who excel at system design, clear communication, and rigorous testing.

AI coding tools won't replace developers. They'll amplify developers who know how to use them
effectively. The key skills shift from typing code to architecting systems, from implementing
algorithms to specifying behavior, from debugging line by line to designing comprehensive test suites.

# An Invitation

I want to make this educational. The OAuth2-bro codebase is publicly available 
at [github.com/jonnyzzz/oauth2-bro](https://github.com/jonnyzzz/oauth2-bro). Most of it was written 
with AI assistance. Some of it probably contains subtle bugs that an AI agent introduced because
my specification wasn't quite right.

**Here's a challenge**: dive into the code and find AI-generated bugs. Look for places where the
OAuth2 spec isn't quite followed correctly. Find edge cases that aren't handled. 
Spot security issues that slipped through.

Open issues. Submit PRs. Let's learn together about what AI coding agents get right and where they
still struggle. This is how we'll collectively figure out how to build robust software in an AI-assisted world.

The future of development isn't about whether to use AI tools. It's about learning to
use them well. OAuth2-bro is one experiment in that direction. What patterns will you discover?

Star the repository, try it in your environment, and share your findings. Together, we're
figuring out how to build better software faster.*

# Misc

OAuth2-bro was created to support customer requests at JetBrains IDE Services, focusing
on management, security, and governance of AI and Developer Tools at scale. The project
is not an official JetBrains product.

# Next Steps

I plan to experiment with
[Extension Grants](https://www.jetbrains.com/help/youtrack/devportal/extension-grants.html#reference-to-standard-extension-grant)
and the idea to chain OAuth2 providers together allowing an admin to use their authentication,
while letting other regular users follow the IP-based rules logic. Stay tuned, and let's hack together.