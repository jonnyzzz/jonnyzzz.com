# Migrating to Gradle Kotlin DSL - Basics

**Date:** March 04, 2019  
**Author:** Eugene Petrenko  
**Tags:** gradle, gradle-kotlin, gradle-kts, gradle-groovy, kts, kotlin, groovy, build, refactoring

---

> The only way to learn a new programming language is by writing programs in it  
>    --- by [Dennis Ritchie](https://en.wikipedia.org/wiki/Dennis_Ritchie)

Do you use the same principle to learn a new programming language? I do, and
I often put this quote into my [talks](/talks) to encourage people to learn
[Kotlin](https://kotlinlang.org)
programming language through practice, or by
[writing programs](https://kotlinlang.org/docs/tutorials/edu-tools-learner.html)
in it. We're going to look at how to apply the
same tactic to learning and practicing [Gradle Kotlin DSL](https://gradle.org/kotlin).

"*Hello World*" projects are not complicated enough for us. Instead, I have decided
to convert an existing Gradle project from Groovy to Kotlin. 
The project I found is a server-side JVM application, written in Kotlin. 
It has 16 Gradle sub-projects and covers enough real-life non-trivial edge cases to make it quite interesting.

While migrating the real-life project's Gradle build from Groovy to Kotlin,
I collected some useful recommendations, code snippets, and explanations.
Throughout the post series, I will share my findings with you. We will together learn how to
convert to Gradle Kotlin DSL faster and easier.

## The Migration Plan

Where do you even start when converting a big Gradle project to Kotlin?
Well, to start with, I do not recommend converting the whole project in one go.
The chances are you will get stuck somewhere in the middle with completely broken scripts.
It may eat away at too much of your time to go in and fix them to complete the migration. It may also be
too hard for you to learn so many different Gradle Kotlin DSL features so quickly, and you may not be able to test your changes, because of the broken project.

I suggest splitting the conversion into a set of small incremental changes.
We will have to go through and update all the build script files one-by-one.
Let's start with the smallest project files, learn the basic features, and slowly
proceed to the most complex build script files.

It is essential to test the build script is not broken after any small change.
You may run any task to execute a Gradle *configuration* phase, which will
likely detect errors in your code. I prefer running the `testClasses` task 
on the root project for that.

For bigger Gradle project files it is even recommended to convert them as
smaller parts. Gradle supports mixtures of Kotlin and Groovy scripts in the same project, so
the `apply(from="file.gradle")` function can include scripts written in
any of the languages. 

It is time to start the migration!

## First Steps of the Migration

Let's start the migration from the smallest Gradle sub-project. For each
project, we need to rename
the `build.gradle` project file into the `build.gradle.kts`.
No surprises there, the result will not work. The file will have 
lots of errors. Let's fix the most common ones first:

First, we need to replace single quotes with double quotes. Groovy supports both quotes
for strings, while Kotlin only supports `"` for strings. 
In [IntelliJ IDEA](https://jetbrains.com/idea) you can use 
the *Convert long character literal to string* quick fix,
multiple carets, or the standard search and replace dialog

![quick fix]({{ site.real_url }}/images/posts/2019-03-04-gradle-kotlin-migration-1-quotes2.png)

String templates like `"$foo.bar.baz"` work differently in Groovy and Kotlin. 
In Kotlin, braces are needed after `$` to call methods or properties, e.g. `"${foo.bar.baz}"`.
Groovy does not support templates on single quoted strings, so you may need to escape the `$` sign as `\$` too.

We replace Groovy lists, with the `listOf` function, 
for example `["foo", "bar"]` is converted to `listOf("foo", "bar")`.

At this point, our build file should contain far fewer errors.
Let's have a look at how other Gradle objects are represented in Kotlin.

## Repositories

The `repositories{..}` block in Kotlin DSL has the same functions for well-known repositories, e.g. `mavenCentral()`.
You may need to know how to convert a custom Maven repository definition like this: 
```gradle
repositories {
  maven { url 'https://dl.bintray.com/palantir/releases' }
}
```

The `maven{..}` function is defined in Kotlin DSL too. The builder
has the `url` property, but the type of it is `java.net.URI` and not `String`.
I do not like to create a `URI` class instance in my Gradle scripts manually.
There is an overloaded function called `maven()` that takes a `String` parameter with name `url`
for the URL. So the Kotlin code looks like this:

```gradle
repositories {
  maven(url = "https://dl.bintray.com/palantir/releases")
}
```

## Dependencies

Let's say we have a dependency definition in Groovy, for example:
```gradle
dependencies {
  implementation 'this.library:name:1.0.0'
}
```

The `dependencies{..}` block is different in Kotlin DSL. We need to add extra
brackets after the configuration name and double quotes for the string:
```kotlin
dependencies {
  implementation("this.library:name:1.0.0")
}
```
I recommend using [multiple cursors](https://stackoverflow.com/questions/1262737/intellij-idea-way-of-editing-multiple-lines)
to fix all the dependencies at the same time in [IntelliJ IDEA](https://jetbrains.com/idea).

Kotlin DSL provides generated helper functions
for the registered project configuration names including `compile`, `testCompile`,
`api`, and `testImplementation`. 
There are several cases that I have come across, where you may not have the generated helper functions in your scripts.
Gradle [does not include](https://gradle-community.slack.com/archives/CAD95CR62/p1549363654105200)
these helper functions to the script files that you include with
the `apply(from="some-file.gradle.kts")` function.
You 
[cannot add](https://gradle-community.slack.com/archives/CAD95CR62/p1549363654105200)
these functions into a [buildSrc](https://docs.gradle.org/current/userguide/organizing_gradle_projects.html#sec:build_sources)
project either. Fear not, I have several workarounds for this.

The first workaround is to use a configuration name as a`String`, e.g. 
```kotlin
dependencies {
  "implementation"("this.library:name:1.0.0")
}
```

A better approach is to refer to the configuration via a delegated property, the following
declaration solves it:
```kotlin
val implementation by configurations
dependencies {
  implementation("this.library:name:1.0.0")
}
```

The code fails if the configuration does not exist. 
The last workaround is to declare the `String` variable with the same name and value,
e.g. `val implementation = "implementation"`. Now
the code can be used in a `build.gradle.kts` file too.

## Gradle Plugins

The `plugins{..}` block in Gradle is similar to the one in Kotlin.
You should add brackets around the plugin ID in the code, e.g.:
```kotlin
plugins {
  id("plugin.id") version "1.2.4"
}
```

The Javadoc comment in the `org.gradle.plugin.use.PluginDependenciesSpec` class
from Gradle sources is
misleading for Kotlin DSL users. It is probably written for the Groovy DSL and has been re-used. 
You can use the code from the snippet above.

## Applying Gradle Plugins to Sub-Projects

There are two ways to apply Gradle plugins to sub-projects. The first one is
to add the `apply(plugin = "plugin.id")` call in the build script file. 
Use the function in the `subprojects{..}` block to enable a plugin for sub-projects.

The second syntax to apply a plugin is to use the shorter version of the `plugins{..}` block, e.g.:
```kotlin
plugins {
  id("plugin.id")
}
```
This syntax isn't allowed in a `subprojects{..}` or `allproject{..}` block.

There is a third option which is to call the `apply<PluginClassName>()` function, where the 
`PluginClassName` is the class name of the plugin main class. 
The `apply<>()` function works well for [ad-hoc plugins]({% post_url blog/2018-08-07-ad-hoc-gradle %}).
I do not like this approach for external plugins,
because the plugin class name, which is not same as the plugin ID, is a part of
the plugin implementation details and it is something that may be changed in the future by
plugin authors.

I found a strange side-effect which was generated by the
Gradle Kotlin DSL engine helper functions for the applied plugins.
Helper declarations may not be visible, depending on the way you apply plugins.

The
[Kotlin Multiplatform](https://kotlinlang.org/docs/reference/building-mpp-with-gradle.html)
plugin (e.g. `1.3.21`) registers the `kotlin{..}` function into the project, where it
is applied. Let's consider two sub-project definitions, one of which does not work:   

*Project A* in the `project-a/build.gradle.kts` file: 
```kotlin
apply(plugin = "org.jetbrains.kotlin.multiplatform")

kotlin { }
```

And *Project B* in the `project-b/build.gradle.kts` file:
```kotlin
plugins { 
  id("org.jetbrains.kotlin.multiplatform") 
}

kotlin { }
```

The *Project B* works and the `kotlin{..}` block is resolved, but the `Project A` does
not work because of the unresolved `kotlin` function.

We should use the `plugins{..}` block to have accessors generated in
[Gradle](https://docs.gradle.org/current/userguide/kotlin_dsl.html#type-safe-accessors).  

## Configuring Tasks

A task configuration is easy to do in Groovy for well-known tasks, 
the task name can be used as the shortcut syntax. The `run` task from the 
[Application](https://docs.gradle.org/current/userguide/application_plugin.html)
Gradle plugin can be configured in Groovy simply as:
```gradle
run {
  args = "--foo", "bar
}
``` 

The same does not work in Kotlin. 
First, we need to find the task from the `tasks` container. 
Then, the explicit task type is required to set task parameters to it. 

The are many functions in the `tasks` object to define or find a task. 
I use the
[reified generic](https://kotlinlang.org/docs/reference/inline-functions.html#reified-type-parameters)
function `tasks.getByName<T>(name: String, action: T.() -> Unit)` to find a task
and to configure it with the same call.

What is the type of task? You can check out the documentation for the plugin, 
the plugin sources, or you can add a debug line like `println(tasks.task_name)`
to your Groovy script to find this out.

Since the `run` task from the Gradle [Application](https://docs.gradle.org/current/userguide/application_plugin.html)
plugin has the type `JavaExec`, we can use the following code in Kotlin to set it up:
```kotlin
tasks.getByName<JavaExec>("run") {
  args = listOf("--foo", "bar)
}
```

We [should](https://docs.gradle.org/current/userguide/kotlin_dsl.html#type-safe-accessors)
use the `plugins{..}` block syntax to enable a plugin to have all generated accessors
available. So we may have the following code:

```kotlin
plugins {
  application
}

application {
  mainClassName = "org.jonnyzzz.example.MainKt`
}

(tasks.run) {
  args = listOf("--foo", "bar)
}
```

In the example, we have the clash between Kotlin
[run](https://kotlinlang.org/api/latest/jvm/stdlib/kotlin/run.html)
function and the generated `run` task accessor's 
[invoke](https://kotlinlang.org/docs/reference/operator-overloading.html#invoke)
overloaded operator. To solve it, I added brackets. The workaround 
is not needed for other tasks, where we do not have such a name clash.

## Troubleshooting

It can be easy to get stuck when working on build scripts. It may be unclear why something
does not work. There are several useful tricks from me that can be done to overcome the
complexity.

Try finding the root cause of the problem in your changes. It can be a tiny
change in one file that yields an error in the other file. Use the version control
or [Local History](https://www.jetbrains.com/help/idea/local-history.html)
to check the recent changes, try reverting them to see if it helps. 

Search the Gradle Documentation for a keyword or task name. There are several links for Gradle Kotlin DSL
I have often used to find helpful hints to solve my issues:
- [Migrating Build Logic from Groovy to Kotlin](https://guides.gradle.org/migrating-build-logic-from-groovy-to-kotlin/)
- [Gradle Kotlin DSL User Guide](https://docs.gradle.org/current/userguide/kotlin_dsl.html)
- [Kotlin DSL Samples](https://github.com/gradle/kotlin-dsl/tree/master/samples)

Read the source code of Gradle or the third-party plugins that you use.
The easiest is to navigate to the problematic declarations from [IntelliJ IDEA](https://jetbrains.com/idea)
and just directly to Gradle or plugin sources. 
I solved some of the problems by checking the source code. I hope it will help you too.

In addition to that, you may find Gradle source code is on [GitHub](https://github.com/gradle/).
Most of the Gradle plugins have their source code published on GitHub or somewhere else.

Try debugging Gradle. The last and the hardest tip to troubleshot your script issues.
The old school debugging technique with `println()` statements often worked quite well here
to print type names or task names to something similar to help to navigate to the
source code and Javadoc comments. Should you need
too many runs to debug the root cause of the problem?
A JVM debugger can be a faster option. [IntelliJ IDEA](https://jetbrains.com/idea) supports Gradle debugging, 
click the *Debug ...* action on the task. 


### Gradle Source Code in IntelliJ Project

[Gradle Wrapper](https://docs.gradle.org/current/userguide/gradle_wrapper.html)
does not download Gradle sources by default.
You may notice a yellow warning in IntelliJ IDEA suggesting to change that too.
Make sure you have the `-all.zip` suffix in the download URL from the
`gradle/wrapper/gradle-wrapper.properties` file in your project:
```properties
distributionUrl=https\://services.gradle.org/distributions/gradle-5.2.1-all.zip
```

Gradle `wrapper` task has an option to prefer the full packages by default. You may
configure it to make sure you don't accidentally switch to the default package with the
next Gradle upgrade. The following Kotlin code sets this up in a root Gradle project:
```kotlin
tasks.wrapper {
    distributionType = Wrapper.DistributionType.ALL
}
```


## Conclusion

[Kotlin](https://kotlinlang.org) as a statically typed programming language
seems to play well for writing Gradle build scripts.
Thanks to static type inference, the Kotlin compiler detects errors earlier and
shows helpful compilation error messages and warnings.
Both the IDE and the compiler use the information about types to infer
available functions and properties in a given scope, even inside a 5th level
nested lambda with receivers. 
  
In this post, we covered the first steps of migrating to Kotlin. We defined
the migration strategy and listed the set of recommendations
to tackle the migration from Groovy to Kotlin quickly.
I will cover more aspects in the coming posts, stay tuned!

Thanks to Hadi, Paul, and David for your help, time and feedback!

Check out the 
- [second post]({% post_url blog/2019-04-02-gradle-kotlin-migration-2 %}) - Kotlin tasks in Gradle Kotlin DSL,
- [third post]({% post_url  blog/2019-05-20-gradle-kotlin-migration-3 %}) - Diving deeper with plugins, extension, buildSrc
- [fourth post]({% post_url blog/2019-06-25-gradle-kotlin-migration-4 %}) - Groovy Closure and Kotlin DSL