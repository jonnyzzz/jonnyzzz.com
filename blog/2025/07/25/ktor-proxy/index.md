# Reverse Proxy in Ktor

**Date:** July 25, 2025  
**Author:** Eugene Petrenko  
**Tags:** kotlin, ktor, reverse proxy, proxy, design, components, dependencies

---

# Building a Streaming HTTP Reverse Proxy with Ktor

I've been looking into Ktor documentation to find something similar to nginx [proxy_pass](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
or Go's [httputil.NewSingleHostReverseProxy(target)](https://pkg.go.dev/net/http/httputil#ReverseProxy). 

Could you please share if we have a similar util in Ktor? Ktor gives you *primitives* that compose. You build exactly what you need, no more, no less.

## The Naive Approach (Don't Do This)

A first instinct might be:

```kotlin
val response = client.get("http://backend$uri")
call.respondText(response.bodyAsText())
```

This works for toy examples. It fails spectacularly in production because:
1. **It buffers everything** -- Say 10-minute Ollama SSE response? All in memory.
2. **SSE doesn't stream** -- Events arrive in one big chunk at the end
3. **No WebSocket support** -- Those upgrade headers? Lost.

## The Streaming Solution

Here's the insight: Ktor's HTTP client has `prepareRequest().execute { }` for streaming responses. This is like nginx `proxy_pass`:

```kotlin
client.prepareRequest(targetUrl) {
    method = call.request.httpMethod
    // Copy headers (excluding hop-by-hop)
    headers {
        call.request.headers.forEach { name, values ->
            if (!isHopByHop(name)) appendAll(name, values)
        }
    }
    if (bodyBytes != null) setBody(bodyBytes)
}.execute { response ->
    // Stream happens HERE, not after
    call.respond(streamingContent(response))
}
```

The `execute` block receives the response **as it arrives**, not after it completes. This is critical for SSE.

## The Streaming Content Challenge

Now we need to forward that streaming response. Ktor's `respondBytesWriter` seems perfect, but there's a trap -
it might buffer internally. The nuclear option is `OutgoingContent.WriteChannelContent()`:

```kotlin
call.respond(object : OutgoingContent.WriteChannelContent() {
    override val status = response.status
    override val contentType = response.contentType()

    override suspend fun writeTo(channel: ByteWriteChannel) {
        val responseBody = response.bodyAsChannel()
        val buffer = ByteArray(256)

        while (!responseBody.isClosedForRead) {
            if (responseBody.availableForRead == 0) {
                if (!responseBody.awaitContent()) break
            }
            val bytesRead = responseBody.readAvailable(buffer, 0, buffer.size)
            if (bytesRead <= 0) break

            channel.writeFully(buffer, 0, bytesRead)
            channel.flush() // CRITICAL to stream SSE and avoid buffers
        }
    }
})
```

That `flush()` call? That's what makes SSE actually stream. Without it, chunks get buffered by Netty.

The small buffer size (256 bytes) is deliberate - lower latency for streaming responses.

## WebSocket: A Different Beast

WebSockets can't use HTTP streaming -- they need a bidirectional tunnel:

```kotlin
webSocket("{...}") {
    val serverSession = this
    client.webSocket(targetHost, targetPort, call.request.uri) {
        val clientSession = this
        coroutineScope {
            launch { // client -> target
                for (frame in serverSession.incoming) {
                    clientSession.send(frame.copy())
                }
            }
            launch { // target -> client
                for (frame in clientSession.incoming) {
                    serverSession.send(frame.copy())
                }
            }
        }
    }
}
```

Two coroutines, one for each direction. When either side closes, the scope cancels and both connections close. Idiomatic Kotlin structured concurrency.

## The Header Dance

Don't blindly copy all headers. RFC 2616 defines "hop-by-hop" headers that must be filtered:

```kotlin
val hopByHopHeaders = setOf(
    HttpHeaders.Connection,
    HttpHeaders.TransferEncoding,
    HttpHeaders.Upgrade,
    "Keep-Alive",
    "Proxy-Authorization"
)
```

Forwarding these breaks proxying in subtle ways. `Connection: keep-alive` tells proxy to keep *its* connection alive,
not to forward that instruction.

## Why Netty Backend Matters

Use Netty for the server, not CIO:

```kotlin
embeddedServer(Netty, port = 1984) { ... }
```

CIO is great for clients, but Netty handles production traffic better -- it's battle-tested with millions of connections.

## Testing Streaming (The Hard Part)

```kotlin
// WRONG - buffers everything
val response = client.get(url)
val channel = response.bodyAsChannel()

// RIGHT - streams as received
client.prepareGet(url).execute { response ->
    val channel = response.bodyAsChannel()
    // Read immediately
}
```

We learned this the hard way. Tests showed perfect streaming for WebSockets but buffered SSE --
because we used `.get()` instead of `.prepareGet().execute { }`.

## The Architecture Pipeline

Proxy request flow:

1. `intercept(ApplicationCallPipeline.Call)` - Catch all HTTP
2. `webSocket("{...}")` - Catch WebSocket upgrades first
3. Check `Upgrade: websocket` header to disambiguate
4. Stream with `prepareRequest().execute { }`
5. Flush aggressively with `WriteChannelContent`

This gives us nginx-level proxying with full control and ~200 lines of code.

## What We Actually Get

A reverse proxy that:
- Streams SSE events as they arrive (critical for Ollama/OpenAI)
- Proxies WebSocket connections bidirectionally
- Handles regular HTTP requests
- Lets us log/modify/inspect anything
- Uses ~10MB RAM regardless of response size
- Compiles to a 15MB JAR with no external dependencies

No nginx, no configuration files, no `proxy_pass`. Just Kotlin.

## The Ktor Philosophy

Ktor doesn't give us a `proxyRequest()` function because proxying is *context-dependent*. Do we need:
- Request/response logging?
- Authentication injection?
- Response transformation?
- Connection pooling config?
- Timeout customization?
- Header filtering rules?

Instead of one inflexible function, Ktor gives `ByteReadChannel`, `ByteWriteChannel`, `HttpStatement`, 
and `OutgoingContent`. We compose them for our exact needs.

This is harder initially. But when we need to debug why SSE streaming isn't working,
we *own the code*. We're not fighting someone else's abstraction.

## More Examples
You may see some examples
- [https://github.com/Shaposhnikov-Alexey/http-proxy/blob/main/src/main/kotlin/main.kt](https://github.com/Shaposhnikov-Alexey/http-proxy/blob/main/src/main/kotlin/main.kt)
- [https://github.com/jonnyzzz/devrig.dev/blob/junie-cage/junie-cage/app/src/main/kotlin/ProxyServer.kt#L94](https://github.com/jonnyzzz/devrig.dev/blob/junie-cage/junie-cage/app/src/main/kotlin/ProxyServer.kt#L94)

Cover the logic with tests (just run yet another ktor as the test server). Share your cases and setups