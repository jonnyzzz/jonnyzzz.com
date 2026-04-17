# IntelliJ Plugin Hot-Reload: HTTP 413

**Date:** April 17, 2026  
**Author:** Eugene Petrenko  
**Tags:** intellij, plugins, netty, hot-reload, mcp-steroid

---

185 MB. That's where my IntelliJ plugin stopped hot-reloading.

I've been working on [MCP Steroid](https://github.com/jonnyzzz/mcp-steroid), an IntelliJ plugin
that exposes IDE APIs to LLM agents via an MCP server. It bundles a Kotlin compiler, an OCR
engine, and enough other dependencies to reach **185 MB** as a ZIP.

That size mattered because MCP Steroid changes fast. An agent tries a skill, hits an edge case, I
fix the handler, redeploy, and the agent tries again. Restarting the IDE for every build kills
that feedback loop. That is why I built
[intellij-plugin-hot-reload](https://github.com/jonnyzzz/intellij-plugin-hot-reload)
([background post]({% post_url blog/2026-01-05-intellij-plugin-hot-reload %})): an HTTP endpoint
on IntelliJ's built-in server on port 63342 that deploys plugins without a restart. My Gradle
`deployPlugin` task finds running IDEs via marker files, POSTs the ZIP, and the IDE reloads
the plugin on the fly.

Then I got this:

```
→ http://localhost:63342/api/plugin-hot-reload
  ✗ HTTP 413
```

## The Investigation

I first assumed the bug was in my handler. It wasn't. IntelliJ returned 413 before my code ever
ran. `curl -v` showed the same thing:

```bash
curl -v -X POST "http://localhost:63342/api/plugin-hot-reload" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/octet-stream" \
  --data-binary "@mcp-steroid-185mb.zip"
```

```
> Content-Length: 194059789
> Expect: 100-continue
>
< HTTP/1.1 413 Request Entity Too Large
< content-length: 0
```

An empty body. No hint. Just 413.

IntelliJ's built-in HTTP server uses Netty. The
[`HttpRequestHandler`](https://github.com/JetBrains/intellij-community/blob/master/platform/platform-util-netty/src/org/jetbrains/ide/HttpRequestHandler.kt#L80-L87)
extension point receives a `FullHttpRequest`. That word matters. Netty's
`HttpObjectAggregator` builds the full request body before the handler runs, and it returns 413
when the request exceeds its limit.

The aggregator is added in
[`NettyUtil.addHttpServerCodec()`](https://github.com/JetBrains/intellij-community/blob/master/platform/platform-util-netty/src/org/jetbrains/io/NettyUtil.java#L107-L109):

```java
pipeline.addLast("httpObjectAggregator", new HttpObjectAggregator(MAX_CONTENT_LENGTH));
```

And `MAX_CONTENT_LENGTH` comes from
[`NettyUtil.java`](https://github.com/JetBrains/intellij-community/blob/master/platform/platform-util-netty/src/org/jetbrains/io/NettyUtil.java#L34-L43):

```java
public static final int MAX_CONTENT_LENGTH;

static {
  int maxContentLength = 180;
  try {
    maxContentLength = Integer.parseInt(
      System.getProperty("ide.netty.max.frame.size.in.mb", "180")
    ) * 1024 * 1024;
  } catch (NumberFormatException ignore) {
  }
  MAX_CONTENT_LENGTH = maxContentLength;
}
```

**180 MB. My ZIP is 185 MB.**

The pipeline is wired in
[`PortUnificationServerHandler`](https://github.com/JetBrains/intellij-community/blob/master/platform/built-in-server/src/org/jetbrains/io/PortUnificationServerHandler.java#L100-L102):

```java
else if (isHttp(magic1, magic2)) {
  NettyUtil.addHttpServerCodec(pipeline);
  pipeline.addLast("delegatingHttpHandler", delegatingHttpRequestHandler);
}
```

Every request on IntelliJ's built-in server goes through that path. There is no per-handler
override. Once I saw that, the shape of the problem changed: fight the limit, or stop uploading
the body.

## First Idea: Another HTTP Server

My first workaround was obvious: spin up a separate Netty or Ktor server with a larger body limit.
**It was the idea that my AI Agent suggested as a too straightforward solution that I rejected. Too much
work for that simple use-case.** 

It would work, but it would also mean:

- Managing a second server lifecycle, plus port allocation and conflicts
- Teaching every client a second endpoint convention
- Debugging one more moving part when reload fails
- Reimplementing authentication, TLS, and shutdown concerns the built-in server already handles

I rejected building it. Then I ask to find a better solution.

## Better Solution: Pass a Local Path

The hot-reload plugin and the Gradle build run on the same machine. The ZIP already exists on
disk. I was uploading 185 MB over loopback so the server could write it to a temp file and hand
that path to `PluginInstaller.installAndLoadDynamicPlugin()`.

The file was already local. I only needed to pass the path.

On the server side, the handler checks a query parameter before touching the request body:

```kotlin
val localDiskFile = urlDecoder.parameters()["local-disk-file"]?.firstOrNull()
if (localDiskFile != null) {
  val file = Path.of(localDiskFile)
  if (!Files.exists(file)) {
    return sendError(
      context,
      request,
      HttpResponseStatus.BAD_REQUEST,
      "File not found: $localDiskFile"
    )
  }

  return executeReload(context) { reloadService, progress ->
    reloadService.reloadPluginFromZipFile(file, progress)
  }
}
```

`reloadPluginFromZipFile` reads the ZIP from disk, extracts the plugin ID, and passes the path to
IntelliJ's `installAndLoadDynamicPlugin()`. My code never creates a 185 MB byte array.

On the client side, the Gradle task got smaller too:

```kotlin
val encodedPath = URLEncoder.encode(zip.absolutePath, Charsets.UTF_8)
val conn = (
  URI("$url?local-disk-file=$encodedPath").toURL().openConnection() as HttpURLConnection
).apply {
  requestMethod = "POST"
  doOutput = false
  doInput = true
  setRequestProperty("Authorization", token)
  connectTimeout = 5_000
  readTimeout = 300_000
}

check(conn.responseCode in 200..299) { "HTTP ${conn.responseCode}" }
conn.inputStream.bufferedReader().lineSequence().forEach { println("  $it") }
```

No body. No `Content-Type`. Just a short authenticated POST with a local path.

## Why This Is Better

This wasn't just a workaround. It was the design I should've used from the start.

The body-upload path forces Netty to aggregate the entire ZIP before my handler runs. At 185 MB,
that's a large allocation even on the happy path. If someone gets the Bearer token, it is also an
easy memory amplifier.

The file-path flow avoids that:

- No 185 MB buffer. The HTTP layer sees an empty body and hands a `Path` to the plugin installer.
- The ZIP stays on disk instead of moving through a socket and an in-memory aggregator.
- The handler can verify existence, size, and, if needed, a checksum before the reload starts.
- More secure: you need a plugin file on the disk, even if you can reach the localhost-bound web-server and somehow know the token.

This is not a dramatic security boundary change. The caller is already authenticated and trusted
to supply a local path. But it replaces "accept arbitrary bytes over the network" with
"read this specific file." That's a better default.

I kept the body-upload path for plugins under 180 MB and for the rare case where client and
server do not share a filesystem. Backward compatibility was just an early `if` in the handler.

## The Result

```
→ http://localhost:63342/api/plugin-hot-reload?local-disk-file=%2Fpath%2Fto%2Fplugin.zip
  Authorization: Bearer $TOKEN
  Starting plugin hot reload, zip size: 193,995,401 bytes
  Plugin ID: com.jonnyzzz.mcp-steroid
  Unloading existing plugin: MCP Steroid
  Plugin unloaded successfully
  Installing and loading plugin: MCP Steroid (0.92.0)
  Plugin MCP Steroid reloaded successfully
  SUCCESS
```

185 MB plugin. Zero bytes in the request body. Full hot reload in under 10 seconds. Better security.

## Takeaways

1. **When an error is opaque, read the source.** The 413 had zero diagnostic information. Reading
   IntelliJ's
   [NettyUtil.java](https://github.com/JetBrains/intellij-community/blob/master/platform/platform-util-netty/src/org/jetbrains/io/NettyUtil.java#L34-L43)
   made the limit obvious.

2. **Question the transport, not just the limit.** My first instinct was "make the limit bigger."
   The better question was "why am I transferring this data at all?"

3. **Localhost is still a network hop.** Even loopback HTTP goes through TCP, Netty codecs, and
   aggregation. A local path skips that entire stack.

4. **Global system properties are not a great API.**
   `ide.netty.max.frame.size.in.mb` is global and resolved at class load time. Not something I
   want users editing in `idea.vmoptions`.

The hot-reload plugin with `?local-disk-file=` support is at
[jonnyzzz/intellij-plugin-hot-reload](https://github.com/jonnyzzz/intellij-plugin-hot-reload)
(v1.0.0). If your IntelliJ plugin is creeping toward 180 MB — or you just want a tighter
plugin development loop — give it a try.

---

I'm looking forward to seeing that functionality supported natively in IntelliJ and IntelliJ SDK.
That will make IntelliJ plugin development much easier. Promote that post, and I'll be happy to
contribute the fixes.

Related posts: [Agentic Experience and Tools]({% post_url blog/2026-03-24-agentic-experience-and-tools %}),
[MCP Steroid Is Now Open Source]({% post_url blog/2026-04-07-mcp-steroid-open-source %}), and
[IntelliJ as a Skill Factory]({% post_url blog/2026-04-08-mcp-steroid-skill-factory %}).