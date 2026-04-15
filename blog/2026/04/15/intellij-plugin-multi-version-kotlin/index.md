# Building an IntelliJ Plugin That Works Across Multiple IDE Versions: 7 Approaches

**Date:** April 15, 2026  
**Author:** Eugene Petrenko  
**Tags:** intellij, kotlin, gradle, plugin-development, mcp-steroid, kotlin-coroutines, jvm, bytebuddy

---

I have been building [MCP Steroid](https://github.com/JetBrains/mcp-steroid) — an IntelliJ plugin
that gives AI Agents access to the full IntelliJ Platform API at runtime. The plugin needs to work
across IntelliJ 2025.3 (build 253), 2026.1 (build 261), and the upcoming 2026.2 EAP.

Right now the plugin uses a workaround: pin a specific Kotlin compiler version that happens to be
binary-compatible one IJ generation before and after the target. It works — but it becomes more
fragile with every Kotlin release, and with the K2.2 → K2.3 break between IJ 253 and 261,
it is reaching its limit.

I also cannot just drop support for IJ 253. That version family covers Android Studio forks.
Dropping it and then needing it back later is expensive — users do not return easily once they are
forced to an alternative. So 253 stays as the floor, and I need to support everything up through
the current EAP trunk.

That sounds like a `sinceBuild` / `untilBuild` problem. It is not.

When I started investigating, I found three separate, deeply entangled problems — and one of them
has no elegant solution in the current Gradle toolchain. This post is the story of those problems
and the seven approaches I explored. The PoC for approaches 1 + 5 is at
[github.com/jonnyzzz/ij-multi-version](https://github.com/jonnyzzz/ij-multi-version).

---

## Table of Contents

- [The Problem in Concrete Terms](#the-problem-in-concrete-terms)
- [The Seven Approaches](#the-seven-approaches)
  - [Option 1: Symlinks + Multiple Gradle Subprojects](#option-1-symlinks--multiple-gradle-subprojects)
  - [Option 2: Branch per IJ Version](#option-2-branch-per-ij-version)
  - [Option 3: Reflection](#option-3-reflection)
  - [Option 4: Shims / Typed Adapters](#option-4-shims--typed-adapters)
  - [Option 5: Template Build Scripts](#option-5-template-build-scripts)
  - [Option 6: Simplify IntelliJ's API Surface](#option-6-simplify-intellijs-api-surface)
  - [Option 7: Docker-based Build Compatibility Tests](#option-7-docker-based-build-compatibility-tests)
- [The Single-Invocation Approach: What JetBrains Uses Internally](#the-single-invocation-approach-what-jetbrains-uses-internally)
- [Build-time Verification: ClassFile Reference Checking](#build-time-verification-classfile-reference-checking)
- [Build Issues I Hit Along the Way](#build-issues-i-hit-along-the-way)
- [Scoring Summary](#scoring-summary)
- [What JetBrains Could Do Better](#what-jetbrains-could-do-better)
- [Where to Start](#where-to-start)
- [What I Am Doing for MCP Steroid](#what-i-am-doing-for-mcp-steroid)

---

## The Problem in Concrete Terms

### The Kotlin Version Coupling

IntelliJ is built with Kotlin and bundles Kotlin libraries. When your plugin runs inside
IJ, it uses the IDE's bundled Kotlin runtime — not the one you compiled against. A plugin
should try the best to avoid bundinng Kotlin libaries, which are present in the IDE classpath.
JetBrains documents the version mapping officially on the
[Configuring Kotlin Support](https://plugins.jetbrains.com/docs/intellij/using-kotlin.html) page:

| IJ Version   | Bundled Kotlin stdlib |
|--------------|-----------------------|
| 2026.1 (261) | 2.3.20                |
| 2025.3 (253) | 2.2.20                |
| 2025.2 (252) | 2.1.20                |
| 2025.1 (251) | 2.1.10                |
| 2024.3 (243) | 2.0.21                |
| 2024.2 (242) | 1.9.24                |

The 2.2.20 → 2.3.20 jump between 253 and 261 is not a routine version bump. JetBrains confirmed
directly on the platform forum:

> *"unfortunately it's indeed impossible to use kotlin 2.2.20 anymore for IJ 261.
> 2.3.0/2.3.10 should be used instead."*
> — Anna Kozlova (JetBrains), [IJ Platform Forum, Feb 2026](https://platform.jetbrains.com/t/kotlin-plugin-compiled-with-later-kotlin-version-in-261-21525-39-eap-snapshot/3734)

This matters specifically if your plugin uses Kotlin compiler APIs — PSI trees, the Analysis API,
anything from `org.jetbrains.kotlin.compiler.client.impl`. Binary metadata changed between K2.2
and K2.3 in a way that is not backward-compatible for compiler uses. 

Kotlin version dimension: not only must the plugin be compiled against the right Kotlin, but
the Kotlin compiler it invokes at runtime must also match the bundled version in the running IDE.
And the Kotlin libraries (such as Kotlin Coroutines) must be compatible.

For [MCP Steroid](https://mcp-steroid.jonnyzzz.com), which executes
Kotlin code snippets programmatically, we use the dedicated `kotlinc` compiler binary. 
The version of the compiler is selected specifically to support the 2.2 version in 253, 
and 2.4.0-beta in the recent versions of IntelliJ. 
Thanks to the binary backward/forward compatibility, that is possible, and it
simplifies the plugin's setup a lot. We are not using the embedded Kotlin compiler 
because it's not included in all IntelliJ-based IDEs, e.g., Rider, PyCharm.

The `PlatformKotlinVersions` map in the IJ Platform Gradle Plugin initially lacked a 261 entry,
silently defaulting to K2.2.20. This caused cryptic compile failures with no diagnostic. Fixed in
[IJPGP v2.12.0](https://github.com/JetBrains/intellij-platform-gradle-plugin/blob/main/CHANGELOG.md)
(released 2026-03-06), which mapped 261 → 2.3.10. The final IJ 2026.1 GA ships 2.3.20, as Kotlin
2.3.20 was released ten days after the IJPGP fix landed.

If your plugin does not use compiler APIs — only pure Kotlin language features — the situation is
less severe. The [intellij-rust](https://github.com/intellij-rust/intellij-rust) plugin handles
this by pinning `apiVersion.set(KotlinVersion.KOTLIN_1_8)` even when the IDE bundles 2.x,
trading access to newer language features for version-range freedom. A valid strategy if your
plugin does not need Kotlin 1.9+ features.

### You Cannot Parametrize the Kotlin Compiler in Gradle

This is the root cause of why all the "just add a flag" solutions fail.

In a standard Gradle build, the Kotlin compiler version is a global property — it comes from
`plugins { kotlin("jvm") version "X.Y.Z" }` in `build.gradle.kts`. There is no built-in
mechanism to compile one subproject with KGP 2.2.x and another with KGP 2.3.x in the same build
invocation. The IJ Platform Gradle Plugin resolves the target SDK classpath per subproject, but
the **Kotlin language and API version** is a property of the KGP loaded into Gradle's script
classloader — not of the SDK.

One Gradle invocation, one KGP version, period. This is the constraint that drives the entire
multi-subproject architecture. Any solution to the multi-version problem that requires different
Kotlin compiler versions *must* use separate Gradle invocations: separate subprojects,
separate CI jobs, or Docker containers.

Alternative – use different Kotlin plugin versions in different sibling projects, and
patent Gradle projects must not have KGP in the classpath. That makes setup even more complicated.

### Bundled Libraries Change Between IJ Versions

It is not just Kotlin. IntelliJ also bundles:

**`kotlinx.coroutines`**: Since IJ 2024.2, JetBrains ships a patched fork at
[github.com/JetBrains/intellij-deps-kotlinx.coroutines](https://github.com/JetBrains/intellij-deps-kotlinx.coroutines)
under the `org.jetbrains.intellij.deps.kotlinx` group. If your plugin bundles its own coroutines
version, you will hit `ClassCastException` at runtime when the bundled and shipped versions load
the same class name through different classloaders. The fix: declare coroutines as `compileOnly`
and set `kotlin.stdlib.default.dependency=false`. But that means compiling against the oldest
bundled version you support.

Pro-Tip: Set up the assertion to verify all the bundled libraries to your plugin. Verify that the
you are not re-packaging the same libraries into your plugin's lib folder.

Approximate bundled versions: IJ 252 → `kotlinx-coroutines 1.10.1-intellij-4`; IJ 261 →
`1.10.2-intellij-1` ([aws-toolkit-jetbrains PR #6331](https://github.com/aws/aws-toolkit-jetbrains/pull/6331)).
The IJ 253 version is not in the official docs table but follows the same pattern.

**Kotlin serialization** and other bundled libraries follow the same pattern.

### IJ Platform APIs Change Without a Stability SLA

JetBrains does not publish a formal API stability SLA. Per-API signals:

- `@ApiStatus.ScheduledForRemoval(inVersion="...")` — will be removed; the version attribute tells
  you when to act
- `@ApiStatus.Internal` — no compatibility promise; may break in a patch release
- `@ApiStatus.Experimental` — subject to change without notice

The [API changes list for 2026](https://plugins.jetbrains.com/docs/intellij/api-changes-list-2026.html)
documents what broke. Deprecated APIs are typically removed after 2–4 major versions. Plugin
Verifier warnings on EAP builds give 1–3 months of lead time — but only if you are running
Plugin Verifier against those EAP builds.

One concrete 2025.3 change: the unified IJ distribution merged Community and Ultimate, deprecating
`intellijIdeaCommunity()` in the Gradle plugin in favour of `intellijIdea()`. The EAP SNAPSHOT
artifacts still accept the old function call for now, but new plugin projects should use
`intellijIdea()` from the start.

---

## The Seven Approaches

### Option 1: Symlinks + Multiple Gradle Subprojects

Create one Gradle subproject per target IJ version. Each has its own `build.gradle.kts` with the
correct `kotlinLang` and `ijSdk` constants. Shared plugin sources live in `src-includes/`. Each
subproject includes the shared sources via **filesystem symlinks** into `src-symlink/`.

Why symlinks? IntelliJ IDEA requires that each source root has a unique physical path. Two modules
pointing to the same directory confuse IDEA's indexing. Symlinks give each module a unique path
that points to the same files.

> *"It creates quite a horrible setup on the IntelliJ side... because there is no standard way
> to mount the same sources for multiple modules."*

The source directory naming convention:

```
src-includes/main/
├── kotlin/          ← always compiled for all versions
├── java/            ← always compiled
├── resources/       ← always compiled
├── src-253/         ← only when ijMajor == 253
├── src-261/         ← only when ijMajor == 261
├── src-253-since/   ← when ijMajor >= 253
└── src-261-until/   ← when ijMajor <= 261
```

Each subproject resolves which directories to link via a regex:

```kotlin
fun folderMatchesMarker(folderName: String): Boolean {
    if (folderName in setOf("java", "kotlin", "resources")) return true
    val m = Regex("""src-(\d{3})(?:-(since|until))?""").matchEntire(folderName)
        ?: error("Unrecognized directory '$folderName' in src-includes/")
    val nnn = m.groupValues[1].toInt()
    return when (m.groupValues[2]) {
        "since" -> ijMajor >= nnn
        "until" -> ijMajor <= nnn
        else    -> ijMajor == nnn
    }
}
```

The PoC also includes a `checkVersionCoverage` task that validates there are no gaps in the
supported version range. It uses the IJ build-number formula — `(year − 2000) × 10 + quarter`,
with valid quarters 1–3 — to detect if, say, you support 253 and 261 but skipped 262 entirely
when 262 was required to be listed. Coverage gaps are caught at configuration time.

Adding a new version: create `ij-plugin/ij-NNN-kXY/build.gradle.kts` (copy from existing, change
three constants at the top), add to `gradle/ij-builds.properties`.

```properties
# gradle/ij-builds.properties
combinations=ij-253-k22,ij-261-k23
```

**Production precedent**: This approach is used in production with the IDE Services plugin, supporting
two years of IJ versions. It works.

**The advantage**: One `./gradlew build` compiles all versions. API breakages surface as compiler
errors immediately across the full version matrix. And the right-click on the selected `runIde`
task would start the debugger with the selected version in the Click.

**The cost**: The symlink layer is unfamiliar to most developers. IDEA's module tree grows with
the version count. Building all versions locally is slower than building one. Dependency
resolution will take more time, since you need more heavy IDE packages to download.
The versioned source folders appears to have more code, one must carefully design and authorize
and new code added to the folders like `src-251`.

**Verdict**: Best compile-time safety. Highest build complexity. Proven in production.

---

### Option 2: Branch per IJ Version

Maintain a separate Git branch per major IJ version. Build and deploy from the correct branch.

Every bug fix must be cherry-picked to all active branches. If you have three branches — `main`,
`253`, `252` — a single commit becomes three cherry-picks. Cherry-picks diverge. After six months
you have three codebases that are supposed to be the same plugin but differ in subtle ways you
cannot easily diff.

> *"The changes must be cherry-picked to all branches to make it work. And it's definitely
> quite easy to fail it. We did that before."*

JetBrains' SDK documentation acknowledges branches as a last resort: "In certain scenarios where
fundamental incompatibilities cannot be resolved through conditional logic, maintaining separate
branches for each major IDE version may be necessary." Last resort is the right framing.

**Verdict**: Simple per-branch build. Terrible long-term maintenance. Hard no.

**Agentic** That is easy to implement with AI Agent and clear instructions to follow. 

---

### Option 3: Reflection

Call version-dependent APIs via Java reflection. Detect the IJ version at startup and
`Method.invoke()` the right implementation.

```kotlin
// Do not do this
val method = try {
    WindowManager::class.java.getMethod("getAllProjectFrames")
} catch (e: NoSuchMethodException) {
    WindowManager::class.java.getMethod("getProjectFrameHelpers") // renamed in IJ 261
}
```

Reflection turns build-time errors into runtime errors. If JetBrains removes the API entirely,
you will not know until a user reports a `NoSuchMethodException` in production. The IDE cannot
help you — no autocomplete, no "find usages", no refactoring support.

> *"The reflection will hide all the potential problems in the future and will create a much more
> problematic approach."*

**Verdict**: Rejected. The ease of implementation does not justify losing compile-time safety.

---

### Option 4: Shims / Typed Adapters

Create a thin adapter layer — small modules, one per version-incompatible API surface. Each shim
implements a shared interface. A selector class picks the right implementation at runtime.

```kotlin
// Shared interface
interface WindowLister {
    fun listProjectWindows(): List<IdeFrame>
}

// shim-253 — compiled against IJ 253 SDK
class WindowLister253 : WindowLister {
    override fun listProjectWindows() =
        WindowManager.getInstance().getAllProjectFrames().toList()
}

// shim-261 — compiled against IJ 261 SDK
class WindowLister261 : WindowLister {
    override fun listProjectWindows() =
        WindowManager.getInstance().getProjectFrameHelpers().toList()
}

// Runtime selection
val lister: WindowLister = when {
    ApplicationInfo.getInstance().build.baselineVersion >= 261 -> WindowLister261()
    else -> WindowLister253()
}
```

The [bazelbuild/intellij](https://github.com/bazelbuild/intellij) Bazel plugin is the canonical
production example. They maintain `sdkcompat/v252/`, `sdkcompat/v253/`, `sdkcompat/v261/` —
supporting two stable versions simultaneously plus one under-development. Their three patterns:
**Compat** (static utility class), **Adapter** (superclass constructor changed), and **Wrapper**
(new interface in superclass constructor). Every compat change is marked `// #api252` to indicate
the last version requiring it — makes cleanup obvious when that version is dropped.

The [aws-toolkit-jetbrains](https://github.com/aws/aws-toolkit-jetbrains) uses a simpler variant:
versioned source directories `src-243-253/` and `src-261+/` within a single Gradle project.
When `PyAddSdkPanel` was removed in IJ 261, its usage moved to `src-243-253/` and the replacement
went into `src-261+/`.

**The critical discipline constraint**: all classes across version-specific directories must
expose the *same* public API surface. You can only change implementations, not add or remove
methods. This is hard to enforce without tooling and compounds in cost as the number of shimmed
APIs grows.

**What makes this better than reflection**: Shim implementations are compiled. API removal in a
shim generates a compile error, not a runtime exception. IDE tooling works normally inside shims.

**What makes this incomplete**: Main plugin code is still compiled against one SDK only. An API
removed in a newer IJ generates no compile error unless it is already behind a shim.

The [HaxeFoundation/intellij-haxe](https://github.com/HaxeFoundation/intellij-haxe) plugin tried
this pattern and eventually dropped it: *"maintaining a code base that can compile to multiple
versions is a lot of work."* They now track only the latest IJ version. The discipline required
is real, and for a small team it compounds quickly.

**Verdict**: Right tool for specific known API divergences. Not a whole-project strategy.
Apply reactively when Option 7 surfaces a specific API break.

---

### Option 5: Template Build Scripts

Each IJ version gets a fully self-contained `build.gradle.kts` with all version constants inlined.
No convention plugins. No shared `buildSrc` task classes. Each file can be read top-to-bottom
and the entire build is understandable.

```kotlin
// ── Version declarations ──────────────────────────────────────────────
val ijMajor      = 253                 // IJ major build number
val ijSdk        = "253-EAP-SNAPSHOT"  // SDK artifact version
val kotlinLang   = "2.2"               // Kotlin language/API level
val needsNightly = false               // true = requires JetBrains VPN
```

A configuration-time assertion catches obvious mismatches before SDK downloads:

```kotlin
run {
    fun String.toMajorMinor(): Pair<Int, Int> {
        val p = split(".")
        return (p.getOrNull(0)?.toIntOrNull() ?: 0) to (p.getOrNull(1)?.toIntOrNull() ?: 0)
    }
    val kgpVersion = extensions.getByType<KotlinJvmProjectExtension>().coreLibrariesVersion
    val (pMaj, pMin) = kgpVersion.toMajorMinor()
    val (lMaj, lMin) = kotlinLang.toMajorMinor()
    check(pMaj > lMaj || (pMaj == lMaj && pMin >= lMin)) {
        "[ij-$ijMajor] KGP $kgpVersion is older than declared language level $kotlinLang. " +
        "Raise kotlinJvmPluginVersion in gradle.properties."
    }
}
```

Adding a new version: copy the file, change the three constants. No convention-plugin archaeology.
New contributors can understand the entire build by reading one file.

This is really an organizational principle for Option 1 — or for the single-invocation CI
pattern — rather than a standalone multi-version strategy. But it is worth naming explicitly because getting the
build organization right makes all other options more maintainable.

**Verdict**: Essential organizational discipline. Use inside whichever multi-version strategy
you choose. Works especially well combined with Option 1.

---

### Option 6: Simplify IntelliJ's API Surface (Long-term)

For MCP Steroid, the IJ plugin ultimately does two things:

1. Execute code: run a Kotlin snippet against the IDE's JVM at the AI Agent's request
2. Show a confirmation dialogue when the Agent wants to do something irreversible

If these two APIs were built into IntelliJ Platform itself, the plugin would become trivial.
All real logic moves to the CLI side. The CLI deals with port discovery, plugin updates, and
versioning. The plugin just exposes two endpoints.

This is the direction MCP Steroid is already moving. The CLI gets richer; the plugin gets simpler.
Every feature that migrates from `ij-plugin/` to `kotlin-cli/` or `mcp-core/` removes one class
of API compatibility problem.

The platform's RPC layer (`com.intellij.platform.rpc`) became public in 2025.3 and 2026.1, but
it serves the IDE-internal frontend/backend split for remote development — not external CLI
delegation. There is no announced timeline for a public `POST /execute` API. Not before IJ 2026.2,
which is roughly a year away.

**Practical implication**: Architect for this direction now. Every refactoring that moves logic
out of the IJ plugin is a step in the right direction, regardless of whether Option 6 itself ships.

**Verdict**: Correct long-term direction. Not a solution for the next 12 months.

---

### Option 7: Docker-based Build Compatibility Tests

Keep the main build simple — one version per Gradle invocation, selected by a property. Add a
separate `test-integration` module with JUnit 5 tests that run
`./gradlew buildPlugin -Pmcp.platform.version=$version` inside a Docker container per target IJ version.

```kotlin
@Test
fun `build plugin with IntelliJ 2025_3`() = buildPluginWithVersion("2025.3")

@Test
fun `build plugin with IntelliJ 2026_1`() = buildPluginWithVersion("2026.1")

@Test
fun `build plugin with IntelliJ 2026_2 EAP`() = buildPluginWithVersion("262-EAP-SNAPSHOT")
```

EAP versions use the **3-digit build-number** format (`262-EAP-SNAPSHOT`, not `2026.2-EAP-SNAPSHOT`),
resolved from the public [`snapshots()`](https://github.com/JetBrains/intellij-platform-gradle-plugin/blob/12b993e2a56a66c6fdde72deb0bebb02a1635622/src/main/kotlin/org/jetbrains/intellij/platform/gradle/Constants.kt#L252)
Maven repo (`https://www.jetbrains.com/intellij-repository/snapshots`) via `useInstaller = false`.
Nightly builds (`262-SNAPSHOT`, or `LATEST-TRUNK-SNAPSHOT` for the rolling trunk tip) require the
[`nightly()`](https://github.com/JetBrains/intellij-platform-gradle-plugin/blob/12b993e2a56a66c6fdde72deb0bebb02a1635622/src/main/kotlin/org/jetbrains/intellij/platform/gradle/Constants.kt#L250)
repo (`https://www.jetbrains.com/intellij-repository/nightly`) and IJPGP ≥ 2.14.0.
Released versions (`"2025.3"`, `"2026.1"`) use the default installer mode.

`LATEST-TRUNK-SNAPSHOT` is particularly valuable: it automatically follows the current trunk
regardless of major version — when 262 ships and 263 trunk starts, it tracks 263. This gives
1–3 months of early warning before API breaks appear in a numbered EAP.

Each test:
1. Updates a bare git clone of the current repo into a cached workspace via `git fetch`
2. Syncs **uncommitted** local changes via `rsync --delete` — so local work in progress is
   tested, not just what is committed
3. Runs `./gradlew buildPlugin -Pmcp.platform.version=X` inside the container
4. Fails the JUnit test if the build fails

### The caching layer is what makes this practical

A cold Docker build downloads a full IJ SDK — roughly 3.3 GB extracted. Slow the first time.
Three-layer caching makes subsequent runs fast:

| Cache layer            | Host path                                  | What is stored                            |
|------------------------|--------------------------------------------|--------------------------------------------|
| Bare git clone         | `build/build-compat/repo-cache/`           | Updated via `git fetch`; fast local clone  |
| Per-version workspace  | `build/build-compat/workspace/<version>/`  | Gradle incremental state                   |
| Shared Gradle home     | `build/build-compat/gradle-cache/`         | IJ SDK JARs, dependency downloads          |

With warm caches: `rsync` copies only changed files, Gradle runs incrementally, the build
completes in minutes instead of the initial 10–20 minutes.

### Why this fits mcp-steroid best

- The single `ij-plugin/build.gradle.kts` already uses `-Pmcp.platform.version=2025.3`
- There is already a `test-integration` module
- Adding a new IJ version is one `@Test` method
- The main build stays fast — `./gradlew build` is one version, no Docker overhead
- API breaks surface as build failures in CI, at test time rather than local build time
- Parallelism is at the JUnit level — multiple containers can run simultaneously

**The tradeoff**: Compile errors only appear when running integration tests, not in `./gradlew build`.
For CI this is fine. For local development you rely on the IDE's inspections and Plugin Verifier.

**Key gap vs. Option 1**: Kotlin compiler version is still global. If IJ 261 requires K2.3 and
the build is configured for K2.2, the Docker test catches it — but not the main local build.
Mitigated by the `checkBundledKotlinCompatibility` task and explicitly pinning `kotlinVersion`
per target platform.

**Verdict**: Best fit for mcp-steroid today. Already implemented as a pending change.

---

## The Single-Invocation Approach: What JetBrains Uses Internally

Some JetBrains plugins use a simpler model: one Gradle invocation builds exactly one IJ version,
selected by a system property. CI runs N parallel jobs — one per version. This is probably the
most common internal approach at JetBrains for multi-version plugin builds.

### One version per Gradle invocation

```bash
./gradlew build -DplatformVersion=253
```

A version config data class carries all version-specific coordinates:

```kotlin
data class PluginVersionConfig(
    val id: String,          // "251", "252", "253", "261"
    val ideaVersion: String, // e.g. "253.27604" — exact build number
    val kotlinVersion: String,
    // ... other SDK/product version fields ...
)
```

CI runs N parallel jobs — one per version. No symlinks needed, because only one version is built
per Gradle invocation and IDEA only sees one set of source roots at a time.

### Source directory selection

```kotlin
private fun SourceDirectorySet.versionedSrcDirs(basePath: String) {
    when (getCurrentVersion().id) {
        "253" -> {
            srcDir("src-252-since/$basePath")
            srcDir("src-253-since/$basePath")
            srcDir("src-253/$basePath")
            srcDir("src-253-until/$basePath")
        }
        "261" -> {
            srcDir("src-252-since/$basePath")
            srcDir("src-253-since/$basePath")
            srcDir("src-261-since/$basePath")
            srcDir("src-261/$basePath")
        }
        else -> error("Unsupported IDE version: ${getCurrentVersion().id}")
    }
}
```

### How it compares to the multi-subproject PoC

| Aspect                          | Single-invocation approach                       | Multi-subproject PoC                        |
|---------------------------------|--------------------------------------------------|---------------------------------------------|
| Versions per Gradle invocation  | 1 (flag-selected)                                | All (one subproject each)                   |
| Symlinks needed                 | **No** — single invocation sees one source set   | Yes — IDEA needs unique paths per module    |
| Source dir matching             | Explicit `when` switch                           | Regex `src-(\d{3})(?:-(since\|until))?`   |
| Version data                    | 20+ fields per version                           | 3 fields: `ijMajor`, `ijSdk`, `kotlinLang`  |
| New version effort              | Add `when` branch + version config object        | Copy build file, change 3 constants         |
| Single-command full matrix      | Requires N parallel CI jobs                      | `./gradlew build`                           |

The intellij-rust plugin used a similar per-version properties file pattern:
`gradle-252.properties`, `gradle-253.properties`, etc., with CI passing
`-PplatformVersion=${{ matrix.platform-version }}` to select among them.

---

## Build-time Verification: ClassFile Reference Checking

Beyond compilation against the right SDK, there is a verification gap: do all the classes, methods,
and fields your plugin references actually exist on the IJ classpath at runtime?

The PoC implements a three-tier answer to this, built around a standalone `:check-class-refs`
Gradle application module that uses ByteBuddy's shaded ASM to inspect compiled bytecode.
Each tier catches a different category of API change.

### Tier 1 — `verifyClassRefs`: erased-descriptor existence check

Walks every `.class` file in the compiled plugin. For each method call site, extracts the
**owner class + method name + full JVM descriptor** (which encodes the erased return type and
parameter types). Checks that this exact `(owner, name, descriptor)` exists somewhere in the
owner class's hierarchy on the `compileClasspath`.

This catches:

- **Class removed**: `com.intellij.MissingClass` not on classpath → `NoClassDefFoundError`
- **Return type changed to a different class**: method `getFrame()` changed from returning
  `com.intellij.openapi.util.Pair` to `kotlin.Pair` — both classes exist, but the JVM
  descriptor changed from `()Lcom/intellij/openapi/util/Pair;` to `()Lkotlin/Pair;`, so
  the call site's `INVOKEVIRTUAL` finds no matching method → `NoSuchMethodError`
- **Parameter type changed**: same mechanism, different position in the descriptor

When a method is missing but a same-named method with a different descriptor is found, the
report shows the alternative:

```
[verifyClassRefs-261] 1 method(s) not found (descriptor mismatch or removed):
  - com.intellij.openapi.wm.WindowManager#getAllProjectFrames ()[Lcom/intellij/openapi/wm/IdeFrame;
      ↳ 'getAllProjectFrames' exists with different descriptor: ()Ljava/util/List;
```

### Tier 2 — `verifyApiSignatures`: generic signature comparison

The erased-descriptor check has a blind spot. Java/Kotlin generics are **erased** at bytecode
level: `List<OldType>` and `List<NewType>` both compile to `Ljava/util/List;`. The JVM links
the call successfully in both cases — but the caller may receive elements of an unexpected type
and get a `ClassCastException` later at the use site.

**Real-world case — [mcp-steroid#18](https://github.com/JetBrains/mcp-steroid/issues/18):**
`StatusBarEx.getBackgroundProcessModels()` changed its return type from
`List<com.intellij.openapi.util.Pair<TaskInfo, ProgressModel>>` to
`List<kotlin.Pair<TaskInfo, ProgressModel>>` between IJ 261 and IJ 262.
Both types erase to `()Ljava/util/List;` — identical JVM descriptor. The plugin compiled,
linked, and passed every standard check. At runtime on IJ 262, iterating the list and
accessing `.first`/`.second` on elements assumed to be `c.i.o.u.Pair` threw a
`ClassCastException`. **Plugin Verifier does not catch this** (confirmed from source at commit [`1d14a2b`](https://github.com/JetBrains/intellij-plugin-verifier/tree/1d14a2b114a8d04bc61b2b4a642ad7d8e48d07a5): it
resolves methods by erased descriptor only; `Signature` attributes are parsed for
display in error messages but never compared for compatibility).

The JVM class file format stores the un-erased generic type in a separate **`Signature`
attribute** alongside the descriptor. This attribute is what the Kotlin compiler uses to
reconstruct generic types for type checking, but the JVM itself ignores it for method
dispatch.

The solution is a two-phase workflow:

**Capture** (run once against the base IJ version, commit the result):

```bash
./gradlew :ij-plugin:ij-253-k22:captureApiSignatures
```

For every method and field call site in the plugin, this looks up the member in the IJ 253
SDK and records its `Signature` attribute into `ij-plugin/api-signatures.txt`:

```
METHOD  com.intellij.util.containers.ContainerUtil#map  (Ljava/util/Collection;...)Ljava/util/List;  (Ljava/util/Collection<TT;>;...)Ljava/util/List<TR;>;
FIELD   com.intellij.openapi.util.Pair#first             Ljava/lang/Object;                           NONE
```

`NONE` means no `Signature` attribute — a raw or primitive type, nothing to compare.

**Verify** (runs on every `./gradlew check` for all versions):

For each entry in the snapshot, looks up the same `(owner, name, erased-descriptor)` in the
current SDK and compares `Signature` attributes. A change that passes `verifyClassRefs`
(same erased descriptor) but changes the generic parameter is caught here:

```
[verifyApiSignatures-261] GENERIC SIGNATURE CHANGED:
  METHOD com.intellij.Foo#getItems ()Ljava/util/List;
    was : ()Ljava/util/List<Lcom/example/OldType;>;
    now : ()Ljava/util/List<Ljava/lang/String;>;
    → METHOD com.intellij.Foo#getItems ()Ljava/util/List;
```

The last line is the ready-to-paste entry for `signature-exceptions.txt` if you have
verified the change is safe at your call sites. Known-safe changes accumulate there over time;
everything else is a build failure.

The Gradle wiring in each version subproject:

```kotlin
// ij-NNN-kXY/build.gradle.kts
val snapshotFile   = parent!!.projectDir.resolve("api-signatures.txt")
val exceptionsFile = parent!!.projectDir.resolve("signature-exceptions.txt")
val compileCP      = configurations.named("compileClasspath")

val verifyApiSignatures by tasks.registering(JavaExec::class) {
    val reportOut = layout.buildDirectory.file("reports/verify-api-signatures-$ijMajor.txt")
    outputs.file(reportOut)
    argumentProviders.add(CommandLineArgumentProvider {
        buildList {
            add("--mode"); add("verify")
            compileCP.get().files.forEach { add("--classpath"); add(it.absolutePath) }
            add("--snapshot");   add(snapshotFile.absolutePath)
            if (exceptionsFile.exists()) { add("--exceptions"); add(exceptionsFile.absolutePath) }
            add("--report"); add(reportOut.get().asFile.absolutePath)
        }
    })
    onlyIf { snapshotFile.exists() }
}
tasks.named("check") { dependsOn(verifyClassRefs, verifyApiSignatures) }
```

**What this still cannot catch**: a `Signature` attribute that was `null` in both SDK versions
(method returning a raw `List` with no generics at all). There is nothing to compare. This is
not a regression — the call was already unchecked by the compiler. The only tool that would
catch such type changes is recompilation against the new SDK, which is exactly what the
multi-subproject build (Option 1) provides.

### Tier 3 — Plugin Verifier: full JLS binary compatibility

Plugin Verifier (`verifyPlugin` task from IJPGP) is the most thorough check. It verifies
binary compatibility against the full JVM specification: access modifiers, method overrides,
interface contracts, deprecated/removed members.

It covers cases the bytecode-ASM tiers do not:

- **Access narrowed**: a method changed from `public` to `protected` or `internal` — the
  erased descriptor is identical, the `Signature` attribute unchanged, but the JVM throws
  `IllegalAccessError` at the call site
- **Abstract method added to an interface your plugin implements**: the plugin class is now
  missing a required implementation — `AbstractMethodError` at runtime
- **`@ApiStatus.ScheduledForRemoval` warnings**: flags APIs your plugin uses that will be
  removed in a future IJ version, before they actually disappear

**What Plugin Verifier cannot catch — confirmed from source** (cloned at commit [`1d14a2b`](https://github.com/JetBrains/intellij-plugin-verifier/tree/1d14a2b114a8d04bc61b2b4a642ad7d8e48d07a5)):

[`MethodResolver.kt`](https://github.com/JetBrains/intellij-plugin-verifier/blob/1d14a2b114a8d04bc61b2b4a642ad7d8e48d07a5/intellij-plugin-verifier/verifier-core/src/main/java/com/jetbrains/pluginverifier/verifiers/resolution/MethodResolver.kt#L160) resolves every method call using `name + erased descriptor` only — the
matching predicate at every call site is `it.name == methodName && it.descriptor == methodDescriptor`
(lines [160](https://github.com/JetBrains/intellij-plugin-verifier/blob/1d14a2b114a8d04bc61b2b4a642ad7d8e48d07a5/intellij-plugin-verifier/verifier-core/src/main/java/com/jetbrains/pluginverifier/verifiers/resolution/MethodResolver.kt#L160), [172](https://github.com/JetBrains/intellij-plugin-verifier/blob/1d14a2b114a8d04bc61b2b4a642ad7d8e48d07a5/intellij-plugin-verifier/verifier-core/src/main/java/com/jetbrains/pluginverifier/verifiers/resolution/MethodResolver.kt#L172), [184](https://github.com/JetBrains/intellij-plugin-verifier/blob/1d14a2b114a8d04bc61b2b4a642ad7d8e48d07a5/intellij-plugin-verifier/verifier-core/src/main/java/com/jetbrains/pluginverifier/verifiers/resolution/MethodResolver.kt#L184), [216](https://github.com/JetBrains/intellij-plugin-verifier/blob/1d14a2b114a8d04bc61b2b4a642ad7d8e48d07a5/intellij-plugin-verifier/verifier-core/src/main/java/com/jetbrains/pluginverifier/verifiers/resolution/MethodResolver.kt#L216), [381](https://github.com/JetBrains/intellij-plugin-verifier/blob/1d14a2b114a8d04bc61b2b4a642ad7d8e48d07a5/intellij-plugin-verifier/verifier-core/src/main/java/com/jetbrains/pluginverifier/verifiers/resolution/MethodResolver.kt#L381), [391](https://github.com/JetBrains/intellij-plugin-verifier/blob/1d14a2b114a8d04bc61b2b4a642ad7d8e48d07a5/intellij-plugin-verifier/verifier-core/src/main/java/com/jetbrains/pluginverifier/verifiers/resolution/MethodResolver.kt#L391)). The JVM `Signature` attribute (which
carries the un-erased generic types) is exposed on the `Method` interface but **only ever read
in [`LocationsPresentation.kt`](https://github.com/JetBrains/intellij-plugin-verifier/blob/1d14a2b114a8d04bc61b2b4a642ad7d8e48d07a5/intellij-plugin-verifier/verifier-core/src/main/java/com/jetbrains/pluginverifier/results/presentation/LocationsPresentation.kt#L143)** — to produce human-readable error message text, never to detect
an incompatibility. [`TypeInstructionVerifier.kt`](https://github.com/JetBrains/intellij-plugin-verifier/blob/1d14a2b114a8d04bc61b2b4a642ad7d8e48d07a5/intellij-plugin-verifier/verifier-core/src/main/java/com/jetbrains/pluginverifier/verifiers/instruction/TypeInstructionVerifier.kt) handles `CHECKCAST` by resolving the target
class for existence only; there is no safety check on what the cast might actually receive.

The companion `ide-diff-builder` tool (which computes `@ApiStatus.AvailableSince` changelogs
between two IDE builds) has the same gap: [`ApiDiffBuilder.kt` line 48](https://github.com/JetBrains/intellij-plugin-verifier/blob/1d14a2b114a8d04bc61b2b4a642ad7d8e48d07a5/ide-diff-builder/src/main/java/org/jetbrains/ide/diff/builder/api/ApiDiffBuilder.kt#L48) keys methods on
`it.name + it.descriptor` — erased descriptor only. [`ApiSignature.MethodSignature`](https://github.com/JetBrains/intellij-plugin-verifier/blob/1d14a2b114a8d04bc61b2b4a642ad7d8e48d07a5/ide-diff-builder/src/main/java/org/jetbrains/ide/diff/builder/api/ApiSignature.kt#L28) stores the
generic `signature: String?` field, but no `ApiEvent` subclass for a signature change exists
([`ApiEvent.kt`](https://github.com/JetBrains/intellij-plugin-verifier/blob/1d14a2b114a8d04bc61b2b4a642ad7d8e48d07a5/ide-diff-builder/src/main/java/org/jetbrains/ide/diff/builder/api/ApiEvent.kt)),
and no code ever compares the field between old and new SDK.

Known pitfall with EAP builds: `pluginVerification { ides { recommended() } }` silently resolves to zero IDEs
when `sinceBuild` targets an unreleased platform. IJPGP v2.12.0
([issue #2090](https://github.com/JetBrains/intellij-platform-gradle-plugin/issues/2090))
added a warning, but the check is still skipped. Always verify that the resolved IDE list is
non-empty when running against EAP builds.

### Comparison

|                                               | `verifyClassRefs` | `verifyApiSignatures` | Plugin Verifier |
|-----------------------------------------------|:-----------------:|:---------------------:|:---------------:|
| Class removed                                 | ✓                 | ✓ (via snapshot MISSING) | ✓            |
| Method/field removed                          | ✓                 | ✓                     | ✓               |
| Return/param type changed (erased, e.g. `Pair`→`kotlin.Pair`) | ✓ | ✓          | ✓               |
| Generic param changed (`List<A>`→`List<B>`, same erased descriptor) | ✗ | ✓ ← unique value | ✗ (uses erased descriptors only; `Signature` attributes read for display, never compared) |
| Access modifier narrowed                      | ✗                 | ✗                     | ✓               |
| Abstract method added                         | ✗                 | ✗                     | ✓               |
| `@ScheduledForRemoval` warnings               | ✗                 | ✗                     | ✓               |
| Classpath source                              | Already-resolved `compileClasspath` | Already-resolved `compileClasspath` | `local(intellijPlatform.platformPath.toFile())` (no extra download) or downloads separate IDE |
| Wired to `./gradlew check`                    | **Yes**           | **Yes**               | **No** (requires explicit `tasks.check { dependsOn("verifyPlugin") }`) |
| Cold-start speed                              | Seconds           | Seconds               | ~5–15 s with local SDK; 10–20 min if downloading |
| Requires snapshot file                        | No                | Yes (run `captureApiSignatures` once against base SDK) | No |

The intended usage: `verifyClassRefs` and `verifyApiSignatures` run on every build as a fast
first gate. Plugin Verifier runs in CI pre-release (or on demand) as the thorough audit.
A failure in the fast gate is a definite bug. A clean fast gate with a Plugin Verifier failure
means an access or override issue — the rarer category.

> **[mcp-steroid#18](https://github.com/JetBrains/mcp-steroid/issues/18#issuecomment-4231291065)** is the concrete case that motivated Tier 2: `getBackgroundProcessModels()` changing from `List<c.i.o.u.Pair>` to `List<kotlin.Pair>` passes both `verifyClassRefs` and Plugin Verifier (same erased descriptor `()Ljava/util/List;`; cast target class still exists). `verifyApiSignatures` catches it by comparing `Signature` attributes — the unique capability verified against Plugin Verifier source code.

---

## Build Issues I Hit Along the Way

These affect any IJ plugin on IJPGP 2.x with Gradle 9.4. Worth knowing before you hit them.

**Missing `mavenCentral()` in `repositories {}`**

`intellijPlatform { defaultRepositories() }` adds JetBrains repositories only. KGP 2.3.0's
`kotlin-build-tools-compat` and `kotlin-build-tools-impl` live on Maven Central. Build fails
with a confusing message:

```
Could not resolve kotlin-build-tools-compat:2.3.0.
No repositories are defined for configuration ':ij-253-k22:compileClasspath'.
```

Fix: add `mavenCentral()` at the outer `repositories {}` level, not inside `intellijPlatform {}`:

```kotlin
repositories {
    maven { url = uri("https://cache-redirector.jetbrains.com/maven-central") }
    mavenCentral()
    intellijPlatform {
        defaultRepositories()
        snapshots()
    }
}
```

**`patchPluginXml` → `linkSources` dependency missing (Gradle 9.4 strict mode)**

The IJ Platform Gradle Plugin's `patchPluginXml` resolves `plugin.xml` from source roots that
are populated by `linkSources`. Gradle 9.4 strict task-dependency validation rejects this:

```
Task 'patchPluginXml' uses output of task 'linkSources' without declaring an explicit dependency.
```

Fix:
```kotlin
tasks.matching { it.name == "patchPluginXml" }.configureEach { dependsOn(linkSources) }
```

**`kotlin.stdlib.default.dependency=false` breaks filename-based stdlib detection**

This property prevents KGP from adding `kotlin-stdlib-X.Y.Z.jar` to `compileClasspath` as a
standalone artifact. It is required for IJ plugins (otherwise you bundle stdlib alongside the
bundled one), but it breaks any task that finds the Kotlin version by searching `compileClasspath`
for a file matching `kotlin-stdlib*.jar`. The stdlib lives inside the bundled Kotlin plugin JARs
in the IJ SDK — not as a recognizable standalone JAR.

Note: for standalone application modules that are NOT IJ plugins (like `check-class-refs`), you
need `implementation(kotlin("stdlib"))` explicitly, because this property applies globally and
those modules do need their own stdlib.

---

## Scoring Summary

| Approach                              | Compile Safety | Build Simplicity | CI Speed | Dev Speed | Maintenance | mcp-steroid fit | Total |
|---------------------------------------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| 1 — Multi-subproject + symlinks       | 5 | 2 | 3 | 3 | 3 | 2 | **18** |
| 2 — Branch per version                | 2 | 4 | 3 | 5 | 1 | 1 | **16** |
| 3 — Reflection                        | 1 | 5 | 5 | 5 | 2 | 1 | **19** ❌ |
| 4 — Shims / typed adapters            | 3 | 3 | 4 | 4 | 3 | 3 | **20** |
| 5 — Template build scripts            | 4 | 4 | 3 | 3 | 4 | 2 | **20** |
| 6 — HTTP API in IJ (long-term)        | 5 | 5 | 5 | 5 | 5 | 2 | **27** ⏳ |
| **7 — Docker compat tests**           | **3** | **5** | **3** | **5** | **5** | **5** | **26** ✅ |
| single-invocation (JetBrains internal) | 3 | 4 | 4 | 5 | 4 | 3 | **23** |

Dimensions scored 1–5: Compile-time safety (do API breakages surface at build time across all
supported versions?), Build simplicity (cognitive load to add a new IJ version), CI speed on warm
cache, Dev loop speed for `./gradlew build`, Maintenance per new IJ major, and fit for
MCP Steroid's current single-project structure.

---

## What JetBrains Could Do Better

**A prominent, versioned Kotlin compatibility matrix**: The information exists in IJPGP's
`PlatformKotlinVersions` map and on the
[using-kotlin.html](https://plugins.jetbrains.com/docs/intellij/using-kotlin.html) page, but
the map was missing 261 until IJPGP v2.12.0 — causing cryptic failures for everyone targeting
261 EAP. A prominently linked table that stays ahead of each EAP release would save many hours.

**A multi-version build template**: The
[IntelliJ Platform Plugin Template](https://github.com/JetBrains/intellij-platform-plugin-template)
is excellent for single-version plugins. A companion template showing the single-invocation approach or the Docker compat-test approach
would let teams start from a working multi-version structure rather than improvising from
scattered blog posts.

**Plugin Verifier wired to `check` by default**: Plugin Verifier is the most thorough binary compat
check available, but it requires explicit invocation. The silent failure of `recommended()` against
unreleased platforms — where verification appears to pass but zero IDEs were checked — means
many plugins ship without ever running the tool. Making it a default-on gate (with the
resolved-IDEs warning visible) would catch more regressions earlier.

---

## Where to Start

Different teams come to this problem from different starting points.

**Building a new plugin from scratch**: Start with Option 7 — Docker build compatibility tests.
Zero migration cost, CI coverage across your target versions from day one. When tests surface
a specific API divergence, add an Option 4 shim for that API only. Use Option 5 template build
scripts to keep each version's `build.gradle.kts` readable top-to-bottom.

**Existing single-version plugin expanding to additional IDE versions**: Option 7 is the
lowest-friction path. The main build stays unchanged — you are adding CI visibility, not
restructuring the project. Option 4 shims come next, reactively, as Docker tests fail.

**Already on a multi-subproject setup**: The PoC documents
specific gaps worth watching — the `checkVersionCoverage` task for version range completeness,
the ByteBuddy class-ref verifier as a fast `./gradlew check` gate, and the Gradle 9.4
strict-mode dependency issues that affect any multi-project build upgrading to Gradle 9.x.

---

## What I Am Doing for MCP Steroid

Short-term:

1. **Ship Option 7** — the Docker compat tests. Already implemented as a pending change. Zero
   migration cost; the main build stays fast; IJ 2025.3, 2026.1, and 2026.2 EAP are covered.

2. **Pin K2.3 for IJ 261 builds** — explicitly set `kotlinVersion = "2.3.20"` when
   `-Pmcp.platform.version=2026.1`. The `checkBundledKotlinCompatibility` task catches mismatches.

3. **Option 4 reactively** — if the Docker tests surface a specific API break, add a shim for that
   API only. `listProjectWindows` is the first candidate. No pre-built shims for hypothetical
   future breaks.

4. **Keep moving logic to the CLI** — every feature migrated from `ij-plugin/` to `kotlin-cli/`
   or `mcp-core/` removes a class of version-compatibility problem. The plugin becomes thinner;
   the version-sensitive surface shrinks. Option 6 is a year away, but the architectural direction
   is correct and every step toward it pays off now.

---

*The multi-version PoC is at [github.com/jonnyzzz/ij-multi-version](https://github.com/jonnyzzz/ij-multi-version).
MCP Steroid is at [github.com/JetBrains/mcp-steroid](https://github.com/JetBrains/mcp-steroid).*

*Building an IJ plugin that spans multiple major IDE versions? I hope this saves you some time.
Reach out on [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) or [GitHub](https://github.com/jonnyzzz)
if something here needs correcting, you need my help, or if you have found a better approach.*