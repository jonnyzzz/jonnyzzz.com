# Kotlin DSL for Test Data

**Date:** November 02, 2017  
**Author:** Eugene Petrenko  
**Tags:** gradle, java9, opensource, plugin, java9c, kotlin, dsl

---

Kotlin DSLs can be used to replace a boring test data strings with correct and an easy to read a code.

That time I was working on [java9c]({% post_url blog/2017-10-18-java9c %}) plugin for Gradle, I created
integration tests. In my case all those tests were of the following pattern: create sample Gradle
project, execute it, check results. I decided to run a fun experiment and replace boring string
constants with a Gradle-looking DSL. 

Namely, instead of (and many Gradle plugin integration tests have similar)

{% highlight kotlin %}{% raw %}
generateDSL(
        "apply plugin: 'java-library'\n" +
        "repositories {\n" +
        "  mavenCentral()\n" +
        "}\n" +
        "\n" +
        "dependencies {\n" +
        "  implementation 'junit:junit:4.12'\n" +
        "}\n"
)
{% endraw %}{% endhighlight %}

I created a tiny DSL that looks (and parses) like a Gradle script. 
The DSL generates test-data files for me. Kotlin compiler and IDE 
helps to prevent errors before a test is executed. Code completion 
makes a new test authoring easier. Here is the DSL usage example:

{% highlight kotlin %}{% raw %}
generateDSL {
  `apply plugin`("java-library")

  repositories {
    mavenCentral()
  }

  dependencies {
    implementation(Text("junit:junit:4.12"))
  }
}
{% endraw %}{% endhighlight %}

More examples are on [GitHub](https://github.com/jonnyzzz/gradle-java9c) in `java9c` plugin test sources.

The example looks like a Gradle script. There was no goal to make it 100% same looking. Also, 
there is an amazing [project](https://github.com/gradle/kotlin-dsl) run by Gradle to support
Kotlin DSLs in Gradle, natively. That DSL is not 100% same looking to a Gradle-Groovy scripts too.

The implementation of that my magic DSL fits in 
[one file](https://github.com/jonnyzzz/gradle-java9c/blob/master/test-common/src/main/java/org/jonnyzzz/gradle/java9c/files.kt),
and it's about 150 lines. 

Next, I'll explain how one can create similar DSLs for their own needs. With Kotlin you may target 
JVM, Android, JS, and Native, reusing same pure-Kotlin code.

DSL Basics
==========

We need to create a text generator DSL. The primary decision if either to generate a bare text or to use an API of a library. 
You may consider [XML DOM](https://www.w3.org/DOM/) or [Jackson](https://github.com/FasterXML/jackson). 
There are [kotlinpoet](https://github.com/square/kotlinpoet) or [javapoet](https://github.com/square/javapoet)
to generate Kotlin or Java code via an API. I bet there are many other libraries. 
[Nebula Gradle Lint Plugin](https://github.com/nebula-plugins/gradle-lint-plugin) can read/write 
Gradle scripts too.

There is a trade-off. Dealing with a library may be complicated and time-consuming, but way more stable. 

For the sake of [java9c]({% post_url blog/2017-10-18-java9c %}) tests, I decided to implement the generator 
based on bare text output. And it'd be me who covers all risks and bugs from the implementation. 
It is only about 150 lines (now) of 
[code](https://github.com/jonnyzzz/gradle-java9c/blob/master/test-common/src/main/java/org/jonnyzzz/gradle/java9c/files.kt).   

Writer Interface
----------------

I started with a line writer interface:
{% highlight kotlin %}{% raw %}
interface LineWriter {
  operator fun String.unaryMinus()
}
{% endraw %}{% endhighlight %}

Inside the interface, I use unary minus, e.g., `-"foo"` as the function to write a line. It reads better in DSLs, e.g.

{% highlight kotlin %}{% raw %}
lineWriter.apply {
  -"line of text"
}
{% endraw %}{% endhighlight %}

Well, you may decide to have a `fun line(text: String)` instead. That does not change the rest, so, please
feel free to use a function instead of an operator. Alternatively, you may use `String.unaryPlus`, so that
you'd have `+"foo"`.

See [Operator Overloading](https://kotlinlang.org/docs/reference/operator-overloading.html) documentation
or ask me, if you need to clarify the trick.

A Trivial Writer Implementation
-------------------------------

The implementation of the interface could be something trivial, e.g. 

{% highlight kotlin %}{% raw %}
fun generateDSL(builder: LineWriter.() -> Unit) : String {
  val result = StringBuilder()
  object : LineWriter {
    override fun String.unaryMinis() {
       result.appendln(this)
    }
  }.builder() 
  return result.toString() 
}
{% endraw %}{% endhighlight %}

The usage could be:
{% highlight kotlin %}{% raw %}
val text : String = generateDSL {
  -"line of text"
}
{% endraw %}{% endhighlight %}

The `generateDSL` receives a [lambda with receiver](https://kotlinlang.org/docs/reference/lambdas.html#function-literals-with-receiver)
and returns resulting string. It is the implementation detail to pass the instance of 
`LineWriter` to the lambda. Inside the lambda, the receiver is `LineWriter`, it means, that `this` keyword 
resolves to an instance of `LineWriter`. Of course, `this.` can be omitted and all methods are resolved
against `LineWriter` instance. It follows that `- "foo"` calls resolves to `String.unaryMinus()` function
of `LineWriter` inside the lambda scope.  

For short, we may compact the `generateDSL` function to the following:
{% highlight kotlin %}{% raw %}
fun generateDSL(builder: LineWriter.() -> Unit) = buildString {
  object : LineWriter {
    override fun String.unaryMinis() {
       appendln(this)
    }
  }.builder()  
}
{% endraw %}{% endhighlight %}

Here I use a `fun buildString(builderAction: StringBuilder.() -> Unit): String` function from the Kotlin standard library. 
It receives yet another [lambda with receiver](https://kotlinlang.org/docs/reference/lambdas.html#function-literals-with-receiver) 
on `StringBuilder` type so that `appendln` is a function from it. 

Theoretically, you may have several different entry point functions (e.g., `generateDSL`)
to, say, generate a string, a file or something else. The rest does not depend on a particular 
`generate*` function.


Indenting and Blocks
====================

Text generation for languages like Gradle requires indenting. We have blocks, and it's nice
to simplify blocks generation. At first, I created an `offset` function for it:

{% highlight kotlin %}{% raw %}
fun LineWriter.offset(): LineWriter {
  val outer = this
  return object : LineWriter {
    override fun String.unaryMinus() {
      val s = this
      outer.apply { 
        -("  " + s) 
      }
    }
  }
}
{% endraw %}{% endhighlight %}

The function is an [extension function](https://kotlinlang.org/docs/reference/extensions.html). It makes
no need to change the original `LineWriter` interface, but it still reads as a method call.

The `block` function is as follows:

{% highlight kotlin %}{% raw %}
fun LineWriter.block(name : String, builder: LineWriter.() -> Unit) {
  -"$name {"
  offset().builder()
  -"}"
  -""
}
{% endraw %}{% endhighlight %}

Here I use [string interpolation](https://kotlinlang.org/docs/reference/idioms.html#string-interpolation)
to simplify code of the first line. 


At that point I can write the DSL snippets like that:
{% highlight kotlin %}{% raw %}
generateDSL {
  block("jonnyzzz") {
    -"test"
  }
}  
{% endraw %}{% endhighlight %}

And it yields 
{% highlight text %}{% raw %}
jonnyzzz {
  test
}  
{% endraw %}{% endhighlight %}

Nice, isn't it?

Gradle Specific Constructs
==========================

With `block` function one can create all necessary functions to generate blocks like `repositories`, `dependencies` and so on. 
Now it is time to implement specific parts of the DSL and allow some constructs only inside other constructs. 

Repositories
------------

Let's consider `repositories` block. Inside we have pre-defined functions for `mavenCentral()` and `jcenter()`.

First, we need a builder interface and implementation. It can be done as follows:
{% highlight text %}{% raw %}
interface RepositoriesWriter : LineWriter {
  fun mavenCentral() { -"mavenCentral()" }
  fun mavenLocal() { -"mavenLocal()" }
  fun jcenter() { -"jcenter()" }
}

fun RepositoriesHolder.repositories(builder: RepositoriesWriter.() -> Unit) =
        block("repositories") {
          object : RepositoriesWriter, LineWriter by it {
          }.builder()
        }
{% endraw %}{% endhighlight %}

We define an interface `RepositoriesWriter` to play as the scope of the generation. In the interface,
we have `mavenLocal` and other functions with trivial implementations. Those functions can be alternatively 
implemented as extension functions of inside the `repositories` function. That is up to the author. 

In the `repositories` function, I use [class delegation](https://kotlinlang.org/docs/reference/delegation.html) aka `by`
keyword to implement `LineWriter` from `RepositoriesWriter` to delegate to another instance of `LineWriter`. 
So short to write and powerful!

As the result, we can have 
{% highlight text %}{% raw %}
generateDSL {
  repositories {
     mavenCentral()
     -"// another line"
  }
}   
{% endraw %}{% endhighlight %}

The same way I created the whole bunch of functions to support the subset of Gradle scripts I 
was using in my tests. You may take a look 
[here for more details](https://github.com/jonnyzzz/gradle-java9c/blob/master/test/src/test/java/org/jonnyzzz/gradle/java9c/test-4.2.1.kt). 


Specific DSL Alternatives
-------------------------

It was another design decision to allow `LineWriter` functions and extension functions (e.g., `block`) 
of the scope of `RepositoriesWriter` lambda. We might have decided opposite. In the case, we would need
[DslMarker](https://kotlinlang.org/docs/reference/type-safe-builders.html#scope-control-dslmarker-since-11)
annotation to make sure `LineWriter` functions and extension functions are not resolved to the 
outer scope. We probably have a `generateDSL` function call on the top.

 
Wrapping Up
===========

DSLs are nice. In the post, I presented the DSL building pattern. 
Use it to create your DSLs. Ask me if you have questions. 
You may also check [this](https://kotlinlang.org/docs/reference/type-safe-builders.html) article from Kotlin 
documentation or [a video of a talk by Hadi](https://www.youtube.com/watch?v=BnTtjywqAX8).