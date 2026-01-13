# JVM Bytecode for Kotlin Object and Companion Object

**Date:** February 04, 2019  
**Author:** Eugene Petrenko  
**Tags:** kotlin, groovy, java, jvm, bytecode

---

There are two ways to declare ~~static~~ global objects in Kotlin. The first
one is called `object` and creates a singleton. The second one, which is
called `companion object`, declares global ~~static~~ functions and properties
within a class, that may have own constructor. You may want to
to walk through the documentation quickly:
- [object](https://kotlinlang.org/docs/reference/object-declarations.html#object-declarations)
- [companion object](https://kotlinlang.org/docs/reference/object-declarations.html#companion-objects)

Functions from both `object` and `companion object` are not compiled as 
`static` functions in JVM bytecode.
You may make your
`object` or `companion object` in Kotlin to inherit from a class or interface!
You may use `@JvmStatic` annotation to make these functions 
be `static` in JVM bytecode. 
 
My story for that post was as follows. I was trying to use Kotlin library
with both `object` and `companion object` declarations from Groovy. I was
upgrading my Gradle/Groovy script into Gradle/Kotlin script. Let's focus in that blog
post on how Kotlin `object` and `companion object` declarations are
visible from the JVM bytecode level, namely from Java and Groovy (and other) JVM languages.
I will be using Kotlin `1.3.20` in that post (and something may change in the future)

## object

Let's create the following code snippet in Kotlin.
```kotlin
object class X {
  fun cool(): Object {
    return this
  }
}
```

I use `Show Kotlin Bytecode` action in IntelliJ IDEA followed by the `Decompile` button click
to analyze JVM bytecode and to see it as Java decompiled code

![decompile bytecode image]({{ site.real_url }}/images/posts/2019-02-04-show-kotlin-bytecode2.png)

The class `X` contains an `INSTANCE` field that holds the only
possible instance of the class `X`. The Kotlin compiler will take care and allow
us calling methods directly on `X`. Form the JVM side, we will need to call
it through the `INSTANCE` filed, e.g. in Java:
```java
Object x = X.INSTANCE.cool();
```

One may use `@JvmStatic` annotation to have the annotated methods compiled
as static functions, and to make the assess from Java easier.

## companion object

Let's create the following code snippet in Kotlin.

```kotlin
class X {
  companion object {
    fun cool(): Object {
      return this
    }
  }
}  
```

That code will generate `X` and `X.Companion` classes in JVM bytecode. 
The `cool` function is declared in the `X.Companion`
class. Kotlin compiler will create the static field called `Companion` that will hold
the reference to the only possible instance of the `X.Companion` class. 
Again, in Kotlin, it will be transparent to use as `X.cool()`, but at the JVM bytecode
level these declarations are not `static`.
One will need to include the `.Companion` to access the `companion object`, e.g.
in Java:
```java
Object x = X.Companion.cool();
```

One may use `@JvmStatic` annotation to have the annotated methods compiled
as static functions, to make the assess from Java easier.

## named companion object

It is possible in Kotlin to name the companion object, e.g. 

```kotlin
class X {
  companion object QwE{
    fun cool(): Object {
      return this
    }
  }
}  
```

For that case, the Kotlin compiler creates the classes `X` and `X.QwE` and the static 
field in the class `X` named `QwE` to hold the only possible
reference to the `X.QwE` class instance.

In Java:
```java
Object x = X.QwE.cool();
```

## Java and Groovy

It is easy to use both classes from Groovy, Java or any other JVM language. 
You may consider `@JvmStatic` annotation to beauty your Kotlin library for Java or
JVM users, if you like.

### Names Clash and Groovy

There is name collision in a `companion object`: Kotlin compiler
generates both the nested static class and the static field with the same name --- `Companion`.
It works flawlessly in Java (or javac), and it is a bit tricky for Groovy (in my case,
it was Gradle/Groovy build script). Let's consider a standalone Java/Groovy example:

```groovy
class X {
    static final Y Y = new Y();
    
    static class Y {
        Object q() { return this; }
    }
}

/// does not work in Groovy
/// works in Java
Object x = X.Y.q()
``` 
I found the following workaround - use `[]` to access the field, with no type information:
```groovy
Object x = X["Y"].q()
```

The better reply came from by Twitter feed:
<blockquote class="twitter-tweet" data-cards="hidden" data-lang="en"><p lang="en" dir="ltr">Field vs Nested Object. The battle. Works on <a href="https://twitter.com/hashtag/java?src=hash&amp;ref_src=twsrc%5Etfw">#java</a>, fails in <a href="https://twitter.com/hashtag/groovy?src=hash&amp;ref_src=twsrc%5Etfw">#groovy</a> <a href="https://t.co/HTzNkYkfez">pic.twitter.com/HTzNkYkfez</a></p>&mdash; Eugene Petrenko (@jonnyzzz) <a href="https://twitter.com/jonnyzzz/status/1090980096637308928?ref_src=twsrc%5Etfw">January 31, 2019</a></blockquote>
<script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>


The best way I see so far is [that way](https://twitter.com/CedricChampeau/status/1090987640613158914)
```groovy
Object x = X.@Y.q()
```

Have fun! Write Kotlin!