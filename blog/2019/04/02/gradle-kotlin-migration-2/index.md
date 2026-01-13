# Migrating to Gradle Kotlin DSL - Kotlin

**Date:** April 02, 2019  
**Author:** Eugene Petrenko  
**Tags:** gradle, gradle-kotlin, gradle-kts, gradle-groovy, kts, kotlin, groovy, build, refactoring

---

Are you using Kotlin in your project?
Let's use the Kotlin DSL to configure the builds of our project
with the [Gradle Kotlin DSL](https://gradle.org/kotlin).
In the post, we will cover several configuration tricks I found
very useful for my Kotlin projects in Gradle.

New to Gradle Kotlin DSL? Take a look at the 
[previous post]({% post_url blog/2019-03-04-gradle-kotlin-migration-1 %})
for practical recommendations on migrating from Groovy to Kotlin
build scripts.

## Enable Kotlin Plugin

The quickest way to enable Kotlin in your Gradle build is
```kotlin
plugins { 
  kotlin("jvm") version "1.3.21"
}
```

Gradle adds the `kotlin()` helper function to simplify your build scripts. The Kotlin standard
library dependencies can be configured in the same way with the help of different `kotlin` functions

```kotlin
repositories {
  mavenCentral()
}
dependencies {
  implementation(kotlin("stdlib"))
  implementation(kotlin("reflect"))
}
```

You don't need to include the Kotlin version dependencies. The Kotlin plugin for Gradle
configures the dependencies resolution, so every Kotlin standard library dependency
will use the same Kotlin version out of the box.  


## Configuring Kotlin Compilation Tasks

You can configure Kotlin in the Gradle scripts in Groovy. It will look something like this
```gradle
compileKotlin {
    kotlinOptions {
        // ...
        suppressWarnings = true
    }
}
```

Do you see the downside? Yes, you may have seen there are `compileKotlin` and `compileTestKotlin` tasks,
which means the second one is not configured. Let's fix it in the Kotlin script.

The code from above will unfortunately not work in a Kotlin Gradle DSL. We need to refer explicitly to
a task element of the `tasks` property of a `project`. Let's not forget to configure
all the Kotlin tasks for the project.

Here is what I found works for configuring all the Kotlin tasks in a Kotlin DSL in one fell swoop:
```kotlin
import org.jetbrains.kotlin.gradle.tasks.*

tasks.withType<KotlinCompile> {
  kotlinOptions {
    jvmTarget = "1.8"
    freeCompilerArgs = listOf("-progressive")
  }
}
```

The `asks.withType<T>` function will run the lambda for every existing and newly
added task of the given type.

## Kotlin Version in Dependencies

With transitive dependencies it could turn out that we use are using older libraries in our project.
Kotlin [guarantees compatibility](https://kotlinlang.org/docs/reference/evolution/components-stability.html),
but still, I'd make sure I am using the actual libraries when possible.

Let's check to make sure we are using the same version of the `kotlin-stdlib` and
the other `kotlin-*` libraries, like for instance, `kotlin-reflect`.

The following Gradle script works for this in Kotlin:
```kotlin
import org.jetbrains.kotlin.gradle.plugin.*
//https://youtrack.jetbrains.com/issue/KT-19788
val kotlinVersion by lazy {
  plugins.withType<KotlinBasePluginWrapper>().map { it.kotlinPluginVersion }.distinct().single()
}
configurations.forEach { config ->
  config.resolutionStrategy.eachDependency {
    if (requested.group == "org.jetbrains.kotlin" && requested.name.startsWith("kotlin-")) {
      useVersion(kotlinVersion)
    }
  }
}
```

You may be asking yourself, why do we need to use code trickery for the `kotlinVersion` variable?
The simple answer is, in Gradle we cannot use variables inside the `plugins{..}` block.
This means that it's impossible to share the Kotlin version as a variable between the `plugins{..}`
block and the rest of the script.

The ancient `buildscript{..}` block does allow it. I prefer the shorter and more explicit 
`plugins{..}` block instead to configure Gradle plugins in builds.

You may want to vote on this issue
[KT-19788](https://youtrack.jetbrains.com/issue/KT-19788)
to make the Gradle Kotlin plugin declare its version. 

## Kotlin-Dsl Plugin and buildSrc

There is yet another experimental plugin, maintained by Gradle, that helps us to
use Kotlin for build logic development in Gradle.
 
The plugin is called `kotlin-dsl`, you can find more details on it
in the
[documentation](https://docs.gradle.org/current/userguide/kotlin_dsl.html#sec:kotlin-dsl_plugin).

The plugin is an excellent choice for a `buildSrc` project. It simplifies the setup,
configures all the dependencies, including `kotlin-stdlib` and Gradle's own build script related
classes. We will discuss `buildSrc` projects and my findings in more detail in the next post.  

## Conclusion

[Kotlin](https://kotlinlang.org) as a statically typed programming language
seems to play well with writing Gradle build scripts.
Thanks to the static type inference, the Kotlin compiler detects errors earlier and
shows helpful compilation error messages and warnings.
Both the IDE and the compiler use information about types to infer
the available functions and properties in a given scope, even inside a 5th level
nested lambda with receivers. 

You may remember from the
[previous post]({% post_url blog/2019-03-04-gradle-kotlin-migration-1 %})
that our example project is written entirely in Kotlin, in that post we 
learned how to configure Kotlin compilation tasks and dependencies in
Kotlin.

I will cover more aspects in the coming posts, stay tuned!
Check out the: 
- [first post]({% post_url blog/2019-03-04-gradle-kotlin-migration-1 %}) - First steps of the migration
- [third post]({% post_url blog/2019-05-20-gradle-kotlin-migration-3 %}) - Diving deeper with plugins, extension, buildSrc
- [fourth post]({% post_url blog/2019-06-25-gradle-kotlin-migration-4 %}) - Groovy Closure and Kotlin DSL