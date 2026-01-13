# Migrating to Gradle Kotlin DSL - Groovy Closure

**Date:** June 25, 2019  
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
we cover Kotlin tasks setup on Gradle Kotlin DSL scripts. Few more findings of mine
towards `buildSrc`, plugins and extensions are presented in the 
[third post]({% post_url blog/2019-05-20-gradle-kotlin-migration-3 %}).

In that post, I'll share my findings for the
migrating a Groovy Closure to Gradle Kotlin DSL. In that post
you'll learn how to step-by-step migrate a Gradle script with Groovy
closure usages into Kotlin DSL.

## Dependencies

I've seen many times in different Gradle projects an attempt to
list all dependencies in some file in the root project and fix versions of all
used libraries in one place so that only a library name is used in a dependency
and its version written only once for the whole project. It helps one to avoid an unexpected library
version clashes in a multi-project Gradle project. For example, how many
different versions of say `OkHttp` or `Jackson` do you have in your project?
Of course, another version of the same dependency may come from
transitive dependencies, it is another story, we will not cover it
in that blog post.

I've implemented a similar pattern to list all dependencies in the root Gradle project.
Let's see how I migrated my Groovy solution to Kotlin.

## Groovy Script Dependencies 

Let's assume we need to add a dependency to `OkHttp` library in a sub-project. We'd like to
use common library definition for all sub-projects. I found it elegant to create a Groovy
closure in the root project for such a definition: 
```groovy
ext {
  dependency_okhttp = { Project project ->
     project.dependencies { 
        compile 'com.squareup.okhttp3:okhttp:3.12.1'
     }  
  }
}
``` 

Do not ask me, why do I have the `Project` parameter in that function/closure. Technically, it is not
needed, but I was lazy to remove it from the code. Now it is time to finally do that (and convert to
Kotlin DSL)! 

Meanwhile, the usage in Groovy was easy and strait forward:
```groovy
ext.dependency_okhttp(project)
```

## Gradle Kotlin DSL

To follow the [one-by-one migration strategy]({% post_url blog/2019-03-04-gradle-kotlin-migration-1 %})
we need the way to call the same code from Kotlin DSL.
I found the following code for it:
```kotlin
(project.extensions.extraProperties["dependency_okhttp"] as Closure<*>).call(project)
```

The code is indeed problematic. When I migrate the `dependency_okhttp` property
definition to Kotlin, I will have to fix every usage of it and replace the cast 
to `Closure<*>` with a cast to, say, `Function1<Project,*>` or something different

## Moving ext to buildSrc and Kotlin

The better place for all extensions in Kotlin (also in Groovy) is `buildSrc`.
We've [covered it]({% post_url blog/2019-05-20-gradle-kotlin-migration-3 %}) in the
previous post. Let's move the definition of the `dependency_okhttp` function into Kotlin code 
and place the code under the `buildSrc` folder. For that, I created a Kotlin file and added the
following function there:

```kotlin
package x.y.z
fun DependencyHandlerScope.dependency_okhttp() {
  "implementation"("com.squareup.okhttp3:okhttp:3.12.1")
}
```

Now we can use the function in Gradle/Kotlin directly in the `dependencies{..}` block:
```kotlin
import x.y.z.*
dependencies {
  dependency_okhttp()
}  
```

The usage is now clean and short, which is great. The only price for that is the `import` statement. 
We need to import the package, where our declaration is to all our `build.gradle.kts` project files.
I wish it were possible to tell Gradle to implicitly import several
more packages into Kotlin DSL script execution context.  

The `DependencyHandlerScope` type is the receiver type of the lambda behind the `dependencies{}` function.
There is yet another issue --- we cannot use `implementation` inside `dependencies{}` block
in the `buildSrc` code. Instead, we may to use `"implementation"` string.
I'm [looking for the answer](https://gradle-community.slack.com/archives/CAD95CR62/p1549364199106400)
to that. It seems the `implementation` function is
generated on the fly by Gradle's Kotlin scripts runtime, and it is not included into the 
`buildSrc` evaluation environment.

## Calling Kotlin buildSrc from Groovy

To start with, do not forget to use the `new` operator to create objects in Groovy. It is
so easy to forget after dealing with Kotlin. I paid about a dozen minutes debugging that.

By that moment, we have all the extension function `DependencyHandlerScope.dependency_okhttp`
declared in Kotlin DSL under the `buildSrc`. Let's see how to call the function from
`build.gradle` files and Groovy. In other words, it is the challenge to re-implement
the older Groovy `ext` closures in all original gradle scripts. 

Our goal is to call the `DependencyHandlerScope.dependency_okhttp` function from Groovy.
We only need an instance of the `DependencyHandlerScope`, which is only used on Kotlin DSL, to make
the call to our Kotlin extension function.
The `DependencyHandlerScope` class has the `of` factory function in its
`companion object`, but it is not a _static_ function, it misses the `@JvmStatic` annotation! 

## Kotlin to JVM Interop 

Global functions (such as `dependency_okhttp`) are compiled by the Kotlin/JVM compiler
to a `FilenameKt` class static member functions. We need to `import static` that
class when calling Kotlin functions from Groovy or Java. The short solution, but
it took several dozen minutes for me to figure out.

To simplify, we may just add a global `import static <package>.<KotlinFileName>Kt.*;` to our Groovy
scripts and then call all our Kotlin global functions without a qualifier. That also applies
to the `dependency_okhttp()` function that we have under `buildSrc`.

One more thing is that the `dependency_okhttp()` function is an _extension function_.
How can we call it from Groovy? 

Kotlin extension functions have the receiver parameter as the very first parameter at the JVM bytecode level.
We may call extension functions from Groovy or Java as an ordinary method passing the receiver object instance
as the first parameter. 

Accessing functions from `object` or `companion object` is in general a bit more tricky. 
Use the following syntax to access Kotlin declarations from Groovy:
- `@JvmStatic` annotation is present --- Call as a static function
- Kotlin `object` --- use `TypeName.INSTANCE.functionName`
- Kotlin `companion object` --- use `TypeName.@Companion.functionName`
 
You may find more details in the
[JVM bytecode for Kotlin Object and Companion Object]({% post_url blog/2019-02-04-companion-and-object %})
declarations post. Frankly, I was happy to find the possibility to write `@Companion` in Groovy.

## Calling Kotlin from Groovy

The `dependency_okhttp` function is declared in the `dependencies.kt` file under the
`buildSrc` project in my codebase. It is visible to Groovy as a member of the `DependenciesKt` class.
We use the `.@Companion.` trick to access the `.of` function of the `DependencyHandlerScope`
class from Gradle.
We have the following Groovy code to call our extension function declared in Kotlin from Groovy:
```gradle
import static x.y.z.DependenciesKt.*
ext {
  dependency_okhttp = { Project project ->
    dependency_okhttp(DependencyHandlerScope.@Companion.of(project.dependencies))
  }
}
```

That code is stable, and it is unlikely to break if we change something code under `buildSrc`.
The Kotlin version is easy to use from Kotlin DSL, and the Groovy version is only needed
for the time of the migration from Gradle to Kotlin. We've covered the migration plan
in the very [first post]({% post_url blog/2019-03-04-gradle-kotlin-migration-1 %})
of this series. 

## Conclusion

In the post we've seen how to deal with Groovy closures on Kotlin and
how to move from `ext` properties to Kotlin extension functions declared in `buildSrc`.

[Kotlin](https://kotlinlang.org) as a statically typed programming language
seems to play well with writing Gradle build scripts.
Thanks to the static type inference, the Kotlin compiler detects errors earlier and
shows helpful compilation error messages and warnings.
Both the IDE and the compiler use information about types to infer
the available functions and properties in a given scope, even inside a 5th level
nested lambda with receivers. 

I will cover more aspects in the coming posts, stay tuned!
Check out the 
- [first post]({% post_url blog/2019-03-04-gradle-kotlin-migration-1 %}) --- First steps of the migration
- [second post]({% post_url blog/2019-04-02-gradle-kotlin-migration-2 %}) --- Kotlin tasks in Gradle Kotlin DSL,
- [third post]({% post_url blog/2019-05-20-gradle-kotlin-migration-3 %}) --- a `buildSrc` project with Kotlin, ad-hoc plugins and extensions