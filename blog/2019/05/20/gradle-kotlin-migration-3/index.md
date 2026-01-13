# Migrating to Gradle Kotlin DSL - Extensions and buildSrc

**Date:** May 20, 2019  
**Author:** Eugene Petrenko  
**Tags:** gradle, gradle/groovy, gradle/kotlin, kts, kotlin, groovy, build

---

While migrating the real-life project's Gradle build from Groovy to Kotlin,
I collected some useful recommendations, code snippets, and explanations.
Throughout the post series, we will together learn how to
convert to Gradle Kotlin DSL faster and easier.

New to Gradle Kotlin DSL? Take a look at the 
[first post]({% post_url blog/2019-03-04-gradle-kotlin-migration-1 %})
for practical recommendations on migrating from Groovy to Kotlin
build scripts. In the [second post]({% post_url blog/2019-04-02-gradle-kotlin-migration-2 %}),
we cover Kotlin tasks setup on Gradle Kotlin DSL scripts. 

In that post, I'm proud to share my findings for the code
reuse in Gradle: extensions, plugins,
and `buildSrc` scripts. It will be the next chapter for the
[Ad-hoc Plugins with Gradle]({% post_url blog/2018-08-07-ad-hoc-gradle %})
post, but we'll be using Gradle Kotlin DSL.

## Project Extensions

The real-life project that I converted to Kotlin DSL contains
several micro-services, each uses the `Application` plugin to create an executable, 
and `jib` plugin is used to generate Docker images.
We reuse the code via a Gradle ad-hoc
plugin to avoid duplicating scripts. 
The [pattern]({% post_url blog/2018-08-07-ad-hoc-gradle %})
helps to reuse the same Gradle (Groovy) code, the usage of which
for every micro-service is like:

```gradle
'some-service' {
  diImplClassName = 'some-class'
}
```

The ad-hoc plugin is applied via a `project.subprojects.forEach{..}` call
in the parent project.
The only line per micro-service is enough to have a command-line application, docker
container, logging configuration, several common dependencies,
test classpath, and tests included for every micro-service project.

The same code does not work in Kotlin DSL. Instead, 
in Kotlin DSL one calls a strongly typed version of it via
the `configure<T>{..}` block, where `T` is the type of 
the extension or convention to configure. We need to know the
extension type to work with it, for example:
```kotlin
configure<MicroPluginSetup> {
  diImplClassName = "some-class"
}
```

In general, we may try the following steps to convert an extension or convention setup
into Kotlin. Gradle generates accessors for conventions and extensions for plugins that
are enabled via `plugins{..}` block.
If it is not generated (like in my case), we may check the documentation
or source code to see the type name of the extension. 
Try a short debugging in Groovy or Kotlin by printing the 
`project.extensions` map entries with a `println()` function
to see the actual project extensions and their types.

There is yet another way to deal with shared code in Gradle. It is called `buildSrc`.
I decided to use that approach together with statically typed Kotlin DSL. All declarations
from the `buildSrc` path should be visible in every `build.gradle.kts` files of my project,
with types information, error highlighting, code navigation, IDE support.
Let's see how it works 

## The buildSrc Project

It is a [good practice](https://docs.gradle.org/current/userguide/organizing_gradle_projects.html#sec:build_sources)
in Gradle to move utility classes or functions under the `buildSrc` project. 
[Ad Hoc Plugins with Gradle]({% post_url blog/2018-08-07-ad-hoc-gradle %}) post
describes for more ways of reusing code with Gradle.

By the convention, Gradle checks the `buildSrc` folder for build sources project. The runtime classpath
of that project will be included in every sub-projects `build.gradle.kts` and `build.gradle` build script classpaths, 
We will be able to use our code, utilities, and classes directly from other build files of the
root project, both Gradle/Groovy and Gradle/Kotlin.

The following Gradle/Kotlin script for the `buildSrc` project is enough to start, it is normally
placed it to the `buildSrc/build.gradle.kts` file under the project root directory:
```kotlin
plugins {
  `kotlin-dsl`
}
repositories {
  gradlePluginPortal()
  mavenCentral()
}
kotlinDslPluginOptions {
  experimentalWarning.set(false)
}
```

The project is ready to go. You may need to click to refresh your Gradle project in IntelliJ IDEA to continue. 
Let's create a helper function as an example. For that, we need to create a `buildSrc/src/main/kotlin/file-op.kt`
file with the following contents:
```kotlin
operator fun File.div(s: String) = File(this, s)
```

It is my favorite operator for builds. It defines the `/` 
[overloaded operator](https://kotlinlang.org/docs/reference/operator-overloading.html)
for `File` and `String` types. So that we may use `/` to combine paths, e.g., we can write
the following to create new `File` object for a child path:  
```kotlin
buildScript / "aaa" / "jonnyzzz.txt"
```

We spoke about the `/` operator with some members of the Gradle team
back at [KotlinConf](https://kotlinconf.com) 2018. In addition to that, I've noticed the 
similar operator somewhere in the
[Gradle sources](https://github.com/gradle/gradle/blob/5c327a8/buildSrc/subprojects/kotlin-dsl/src/main/kotlin/org/gradle/kotlin/dsl/kotlin-dsl-upstream-candidates.kt#L16)
too :)

Now it is the time to convert the Groovy Ad-Hoc plugin into Kotlin DSL under `buildSrc`. Let's rock!

## Ad-Hoc Gradle Plugins

My scripts were written in a Groovy as an ad-hoc plugin class in a parent project file. 
For more details on that setup, please see the explanation in the
[ad hoc Gradle plugins]({% post_url blog/2018-08-07-ad-hoc-gradle %}) post.
To start with the `buildSrc` folder, we move the plugin code into the `buildSrc` folder.
Several conversions steps needed to turn Groovy script into Kotlin DSL. You may check out the
[first post]({% post_url blog/2019-03-04-gradle-kotlin-migration-1 %}) of the series for
more insights. We'll have the following Kotlin code for it now:
```kotlin
package theBuildSrcPackage

fun applyMicroPlugin() {
  apply<MicroPlugin>()
}

open class MicroPlugin : Plugin<Project> { ... }
open class MicroPluginSetup { ... }
```

The `applyMicroPlugin()` is a nice shortcut to simplify the way we deal with the plugin.
Thanks to the code completion in the `build.gradle.kts` files, it is now easier to apply the
plugin via the function call, instead of calling the longer `apply<>()` variant.  

The usage of the ad-hoc plugin in Kotlin DSL is now look as follows:
```kotlin
import theBuildSrcPackage.*

applyMicroPlugin()
configure<MicroPluginSetup> {
  diImplClassName = "some-class"
}
```

It is similar to what we have before. We apply the plugin first and pass the configuration of it
as the second step. It is a good point to realize that we use a too long API to achieve the
goal. Let's try to make the API more expressive and short. Check out my [talk](/talks#australia2019)
on Expressive APIs in Kotlin for more hints. We do not need to repeat the intent to enable a
Gradle plugin more than once. It means all other types and configuration parameters should be
included implicitly. Let's add the following helper function for that:
```kotlin
fun applyMicroPlugin(action: MicroPluginSetup.() -> Unit) {
  apply<MicroPlugin>()
  configure<MicroPluginSetup>(action)
}
```

The code above hides all implementation details from us, so we may apply and configure the
plugin as easy as:
```kotlin
applyMicroPlugin {
  diImplClassName = "some-class"
}
```

Such code us easy to read and understand. It is now clear what we do. It is no longer possible
to enable the plugin without passing a configuration to it. Hopefully, it will help others from my
team to deal with Gradle scripting faster. 


## Conclusion

In the post we've seen how to convert an 
[ad-hoc plugin]({% post_url blog/2018-08-07-ad-hoc-gradle %})
to Gradle/Kotlin. It is easier to re-use Gradle code that way.

[Kotlin](https://kotlinlang.org) as a statically typed programming language
seems to play well with writing Gradle build scripts.
Thanks to the static type inference, the Kotlin compiler detects errors earlier and
shows helpful compilation error messages and warnings.
Both the IDE and the compiler use information about types to infer
the available functions and properties in a given scope, even inside a 5th level
nested lambda with receivers. 

I will cover more aspects in the coming posts, stay tuned!
Check out the 
- [first post]({% post_url blog/2019-03-04-gradle-kotlin-migration-1 %}) - First steps of the migration
- [second post]({% post_url blog/2019-04-02-gradle-kotlin-migration-2 %}) - Kotlin tasks in Gradle Kotlin DSL,
- [fourth post]({% post_url blog/2019-06-25-gradle-kotlin-migration-4 %}) - Groovy Closure and Kotlin DSL