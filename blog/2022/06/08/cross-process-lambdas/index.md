# Cross-process Lambdas

**Date:** June 08, 2022  
**Author:** Eugene Petrenko  
**Tags:** kotlin, java, jvm, lambda, serialization, bytecode, kotlin-bytecode, groovy

---

## Introduction

I've been working to invent a black-box integration test
framework for our plugin which does the following:
* creates an environment in the first JVM
* starts the second JVM process with the plugin
* makes some action inside the started JVM
* checks the expected effects from outside the application

Essentially, my problem was — how to create a lambda in one JVM
and execute it in the other JVM. In the post, I discuss approaches
to create integration tests like that:

```kotlin
@Test
fun exampleTest() {
  setupEnvironmentForTestion()
  startProcessAndRun {
    weDoThatInTheExternalProcess()
    toMakeTestScenario()
  }
  checkExpectations()  
}
```

Ideally, the solution should allow using captured variables
between processes too.
For example:

```kotlin
@Test
fun exampleTest() {
  val capturedVariable = setupEnvironmentForTestion()
  startProcessAndRun {
    weDoThatInTheExternalProcess(capturedVariable)
    toMakeTestScenario()
  }
  checkExpectations()  
}
```

In this post, we'll explore several ways to create a lambda in one JVM
and execute it in the other JVM processes.

## Whole Class Approach

The very first approach could be to have the whole `exampleTest`
function execute in the second JVM. We may need to replace
`setupEnvironmentForTestion()` and `checkExpectations()` implementations
on the second JVM with empty stubs for that. It is hard to
pass data between processes. Finally, a code may look like:

```kotlin
@Test
fun exampleTest() {
  runInHost {
    setupEnvironmentForTestion()
  }
  startProcessAndRun {
    weDoThatInTheExternalProcess()
    toMakeTestScenario()
  }
  runInHost {
    checkExpectations()
  }  
}
```

It is a powerful approach from one side, but it is more constrained. 
It is quite hard to pass parameters between processes, for example.

So far, that scenario is hard to apply for my use-case.
Let's cover more lambda-specific approaches.

## Dealing with Lambdas

I've a set of
[test cases](https://github.com/jonnyzzz/serialized-lambda)
to see how lambdas behave
in different contexts.
Each test has two examples just like we've had above:
 - a lambda with no captured parameters
 - a lambda with a captured local variable

This pattern is repeated many times in Java and in Kotlin to
try different approaches to the lambda:
 - lambda implementing `Runnable` (Java and Kotlin)
 - lambda implementing custom interface (Java and Kotlin)
 - Kotlin lambda for a Kotlin functional type
 - Kotlin inline functions with inline lambda

In addition to that, we try wrapping a lambda with a higher order function
which returns another lambda. 

Grab the [project](https://github.com/jonnyzzz/serialized-lambda) from
GitHub and give it a try. We are getting to analyze the results of it

## Using Lambda Constructors

The very first approach is to check if a generated lambda class
has a default constructor. We could use the constructor to create
an instance of that lambda in the second JVM process.

![Test Run Result: Lambda constructors]({{ site.real_url }}/images/posts/2022-06-08-lambda-ctor.png)

Lambdas in Kotlin and in Java do not have default constructors, 
that is hot hard to check via an example application. Apparently, there is
a trick that works well. We can implicitly create a class and an object for
every lambda via 
[Kotlin Inline functions](https://kotlinlang.org/docs/inline-functions.html).

The following code makes Kotlin compiler generate a default constructor for an inlined lambda:

```kotlin
inline fun lambdaToClass(crossinline action: () -> Unit) {
  val holder = object : Runnable {
    override fun run() {
      action()
    }
  }
  doSomethingWithTheClass(holder.javaClass)
}
```

Each call of the function `lambdaToClass` is inlined by the compiler, 
so we will have a dedicated class for each function call site. 
The lambda, which we pass as a parameter, is inlined into the generated
anonymous class. We are free to make the anonymous class, extend a
specific class or implement some interfaces.

NOTE. This approach is based on the side effects of Kotlin compiler.
Future versions of Kotlin compiler may behave differently and break
that solution.

The generated anonymous class has a default contractor with no parameters,
when there are no captured variables. The constructor will have more parameters
for captured variables. So far, that solution works, but it is not
flexible enough. Let's see if serialization can be used instead. 

## Using Lambda Serialization

For this series of experiments, we will be using JDK's standard
`ObjectInputStream` and `ObjectOutputStream` to serialize a lambda in
one process and to load the serialized one on the other JVM process.
The following code is used to save and load the lambda:

```kotlin
val bytes = ByteArrayOutputStream().use { bos ->
  ObjectOutputStream(bos).use { it.writeObject(obj) }
  bos.toByteArray()
}

val reloaded = bytes.inputStream().use { bis ->
  ObjectInputStream(bis).readObject()
}
```

Now it's time to run all the experiments and see the outcomes:

![Test Run Result: Lambda constructors]({{ site.real_url }}/images/posts/2022-06-08-lambda-serialized.png)

We see the following from the [tests](https://github.com/jonnyzzz/serialized-lambda):
- Java's lambdas are serializable when the respective functional interface implements `java.io.Serializable`
- Kotlin (from 1.5) generates serializable lambdas for Java serializable functional interfaces
- Kotlin's lambdas for Kotlin functional types (e.g. `() -> Unit`) are implicitly serializable
- Kotlin's inlined lambdas can be made serializable if we inline them into a serializable object declaration

In Java, we can make a lambda be `Serializable` by extending a `java.io.Serializable` from
a functional interface that we use. The same works both in Java and in Kotlin:

```java
interface SerializableRunnable extends Serializable, Runnable { } 

SerializableRunnable serializableLambda = () -> { };
```

In Kotlin, we can just create a lambda, and it will be serializable:
```kotlin
val serializableLambda = { }
```

In addition to that, we may apply the same trick with inline function as above,
but we will not be using the anonymous class directly:

```kotlin
inline fun lambdaToClass(crossinline action: () -> Unit) {
  val holder = object : Runnable, Serializable {
    override fun run() {
      action()
    }
  }
  serializeMe(holder)
}
```

There are several more interesting fasts:
- Lambda in Java are implemented via `invokedynamic` and
  JDK's [LambdaMetafactory](https://docs.oracle.com/javase/8/docs/api/java/lang/invoke/LambdaMetafactory.html#metafactory-java.lang.invoke.MethodHandles.Lookup-java.lang.String-java.lang.invoke.MethodType-java.lang.invoke.MethodType-java.lang.invoke.MethodHandle-java.lang.invoke.MethodType-)
  whose class names are like `Simple$$Lambda$55/0x0000000800180040`
- Deserialized Java lambda may have another type name
- Lambdas for Kotlin functional types implicitly implement Serializable and are now complied as ordinary classes 

Starting from [Kotlin 1.5](https://kotlinlang.org/docs/whatsnew15.html#sam-adapters-via-invokedynamic),
the compiler uses the `invokedynamic`
and JDK's
[LambdaMetafactory](https://docs.oracle.com/javase/8/docs/api/java/lang/invoke/LambdaMetafactory.html#metafactory-java.lang.invoke.MethodHandles.Lookup-java.lang.String-java.lang.invoke.MethodType-java.lang.invoke.MethodType-java.lang.invoke.MethodHandle-java.lang.invoke.MethodType-)
to implement lambdas for Java-declared
functional interfaces and `fun interface` Kotlin declarations.
Future [versions](https://youtrack.jetbrains.com/issue/KT-45375/Generate-all-Kotlin-lambdas-via-invokedynamic-LambdaMetafactory-by-default)
will use `invokedynamic` all lambdas. 

We see from the [experiments](https://github.com/jonnyzzz/serialized-lambda) that
the easiest way to pass a lambda between JVM processes is to use serialization. 

## The Classpath

Running an arbitrary code in the second JVM process is easy if we have
the same classpath.  

My scenario was different, I was only able to execute a Groovy script
in the second JVM Process. The classpath was totally unrelated, and
I had to start with classloading. We generate a Groovy script with
all necessary parameters inlined. It includes:
* classpath of the first process
* serialized lambda as Base64
* helper entrypoint classname

Putting everything together, I've got:

```groovy
URL[] cp = [
  ///INSTERT CLASSPATH HERE
  /// new File("<PATH GOES HERE>").toURI().toURL(),
]
classBase64State = '<PUT SERIALIZED STATE HERE>'
class X{}
cl = new URLClassLoader(cp, X.class.classLoader)
clazz = cl.loadClass('OurEntryPointClass')
loader = clazz.newInstance()
loader.execute(classBase64State)
```

We use yet another class named `OurEntryPointClass` to move
as much code as possible from the Groovy script. The classloader,
which we use to load our classes from the first JVM,
delegates to the parent loader first, so we have to be
careful with different versions of the same libraries that we use
in both processes.

```kotlin
class OurEntryPointClass { 
  fun execute(text: String) {
    val oldLoader = Thread.currentThread().contextClassLoader
    Thread.currentThread().contextClassLoader = javaClass.classLoader
    try {
      val loadedLambda = Base64.getDecoder()
        .decode(text).inputStream()
        .let(::ObjectInputStream)
        .readObject() as? Runnable
        ?: error("Failed to load Consumer<Project> from the lambda")
      loadedLambda.run()
    } finally {
      Thread.currentThread().contextClassLoader = oldLoader
    }
  }
```


## Conclusion

Passing a lambda between JVM processes is not hard. There are multiple ways
to solve that goal. Serialization works greatly for that!
I hope my examples will help you to solve your problem
in the future. I'd be grateful [to know](https://twitter.com/jonnyzzz) your
use-cases too.