# Kotlin DSLs in 2026: Patterns That Stood the Test of Time

**Date:** January 19, 2026  
**Author:** Eugene Petrenko  
**Tags:** kotlin, java, dsl

---

Eight years ago, I wrote about using Kotlin higher-order functions to simplify Java builders. 
Around the same time, I explored ad-hoc Gradle plugins and "The DSL Way"--replacing configuration 
files with type-safe Kotlin code. Looking back from 2026, these patterns have not only survived 
but have become fundamental to how we build modern JVM applications.

## The Core Idea That Never Changed

The fundamental insight remains: Kotlin's language features--extension functions, lambdas 
with receivers, and operator overloading--turn any API into a potential DSL.

Consider the classic Java builder problem:

```kotlin
// Traditional Java builder usage - verbose and error-prone
val token = JWT.create()
    .withIssuer(ISSUER)
    .withClaim("userId", userId)
    .withClaim("serviceId", serviceId)  // Easy to copy-paste errors!
    .sign(algorithm)
```

The solution I proposed in 2018 still works perfectly:

```kotlin
fun <B : Any, Y : Any> B.withX(obj: Y?, f: B.(Y) -> B): B =
    if (obj != null) f(obj) else this

val token = JWT.create()
    .withIssuer(ISSUER)
    .withX(userId) { withClaim("userId", it) }
    .withX(serviceId) { withClaim("serviceId", it) }
    .sign(algorithm)
```

## What Has Evolved: Scope Control

Kotlin introduced `@DslMarker` for better scope control in DSLs:

```kotlin
@DslMarker
annotation class ConfigDsl

@ConfigDsl
class ServerConfig {
    var name: String = ""
    lateinit var database: DatabaseConfig
    
    fun database(block: DatabaseConfig.() -> Unit) {
        database = DatabaseConfig().apply(block)
    }
}

fun server(block: ServerConfig.() -> Unit): ServerConfig =
    ServerConfig().apply(block)
```

The `@DslMarker` annotation prevents accidentally calling outer scope functions from inner blocks.

## Build Systems: Gradle Kotlin DSL Matured

The patterns for ad-hoc plugins and code reuse have become standard:

```kotlin
// buildSrc/src/main/kotlin/service-conventions.gradle.kts
plugins {
    kotlin("jvm")
    application
}

dependencies {
    implementation(platform("org.jetbrains.kotlin:kotlin-bom"))
    implementation("io.ktor:ktor-server-core:2.3.0")
}
```

The trick of using `$id:$id.gradle.plugin:$version` to include plugin dependencies 
in `buildSrc` remains the key insight for sharing complex build logic.

## Configuration as Code: The DSL Way

The concept of transforming configuration files into executable Kotlin code has proven durable:

1. Parse the original format (properties, YAML, XML)
2. Generate readable Kotlin DSL code
3. Execute the DSL to produce the original format

```kotlin
// Instead of log4j.properties
log4j {
    val console = appender<ConsoleAppender>("console") {
        layout<PatternLayout> {
            conversionPattern = "%d{ISO8601} [%t] %-5p %c - %m%n"
        }
    }
    
    rootLogger {
        level = ERROR
        appenders += console
    }
}
```

Variable references enable find-usages and rename refactoring. The type system catches invalid configurations at compile time.

## Modern Use Cases

Beyond build systems, Kotlin DSLs have found homes in:

- **API Client Generation**: Ktor uses DSLs for routing and request handling
- **Infrastructure as Code**: Kotlin DSLs for Terraform or Pulumi
- **Data Pipelines**: Spark and Flink wrappers
- **UI Frameworks**: Compose is fundamentally a Kotlin DSL

## Practical Guidelines for DSL Design

1. **Start with the usage site**: Write how you want the DSL to look first
2. **Use `@DslMarker`**: Always add scope control
3. **Prefer extension functions**: Keep core interfaces clean
4. **Make illegal states unrepresentable**: Use the type system
5. **Provide escape hatches**: Sometimes users need the underlying API

## Conclusion

Kotlin DSLs have moved from a clever technique to an essential tool in the JVM ecosystem. 
The patterns established years ago remain the foundation. What has changed is the tooling
maturity and breadth of applications.

If you are still writing verbose Java builder code or maintaining error-prone configuration 
files, consider whether a thin Kotlin DSL layer could transform your development experience.

The best programs remain immutable programs. And the best configurations are the ones that fail
at compile time, not in production.