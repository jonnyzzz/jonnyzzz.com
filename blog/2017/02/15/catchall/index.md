# Catching exceptions with less code in Kotlin

**Date:** February 15, 2017  
**Author:** Eugene Petrenko  
**Tags:** kotlin, kotlin-bytecode, jvm, tip

---

A tiny inline function for consise try/catch

In JVM every call can throw an exception. In Java language, we have dedicated declaration that a method is 
expected to throw some exception types. But still, some other (`Throwable`, `Error`, `RuntimeException`) exceptions 
may still be thrown. 

In Kotlin there are no checked exceptions (like, say in C#). Sill, one have to expect
any possible exception being thrown from any possible place. 

Most cases it's ok and one should not do anything specific about exceptions. Still, there are other places, 
where an exception may break code logic. In asynchronous applications (for example with RxJava, Netty, grpc-java) where 
most of the code is a callback, it may turn out necessary to make sure an exception is not breaking some 
outer login.
 
A trivial solution is to use `try/catch`. But it makes a code quite ugly when you have several statements to call. It 
may look like that

{% highlight kotlin %}{% raw %}
 try {
   callAction1()
 } catch(t : ExceptionType) {
   handleAction1Error()
 }
 try {
   callAction2()
 } catch(t : ExceptionType) {
   handleAction2Error()
 }
 /// ....
 try {
   callActionN()
 } catch(t : ExceptionType) {
   handleActionNError()
 }
{% endraw %}{% endhighlight %}

A good think here is that `try/catch` is expression in Kotlin, but still it is quite long to use.

In my application, I found that about 80% of such catches were done to 
log actual problem and to continue forking further. Meaning `handleActionNError()` functions in my case were 
calls to a `Logger`.

There is now equivalent way in Java to replace this long construction. Of course, it is possible to pass a 
lambda expression into a function like `catchAll`. But this would change a program and it would add extra 
object creation in most of the cases.

One can implement similar `catchAll` function in Kotlin too. Thanks to 
[inline functions](https://kotlinlang.org/docs/reference/inline-functions.html)
it has no overhead at all.

This is the function I use:
{% highlight kotlin %}{% raw %}
inline fun catchAll(LOG: Logger, message: String, action: () -> Unit) {
  try {
    action()
  } catch (t: Throwable) {
    LOG.warn("Failed to $message. ${t.message}", t)
  }
}
{% endraw %}{% endhighlight %}

So now I may rewrite the above example in a way consise fashion

{% highlight kotlin %}{% raw %}
 catchAll(LOG, "action1") {
   callAction1()
 }
 catchAll(LOG, "action2") {
   callAction2()
 }
 ///  ....
 catchAll(LOG, "actionN") {
   callActionN()
 }
{% endraw %}{% endhighlight %}

Every usage of the function `catchAll` is inlined by Kotlin compiler in to a caller method bodies. Kotlin compiler also
inlines the action anonymous function `action` too. There is no overhead! Let's consider the following
example:

{% highlight kotlin %}{% raw %}
fun main(args: Array<String>) {
  catchAll(LOG, "println") {
    println("Test console output")
  }
}
{% endraw %}{% endhighlight %}


The following bytecode is generated out of it. Note. I use IntelliJ IDEA 2017.1 EAP with Kotlin 1.0.6 plugin. The generated
bytecode may change with a future version of tools.


{% highlight text %}{% raw %}
public final static main([Ljava/lang/String;)V
    @Lorg/jetbrains/annotations/NotNull;() // invisible, parameter 0
    TRYCATCHBLOCK L0 L1 L2 java/lang/Throwable
   L3
    ALOAD 0
    LDC "args"
    INVOKESTATIC kotlin/jvm/internal/Intrinsics.checkParameterIsNotNull (Ljava/lang/Object;Ljava/lang/String;)V
   L4
    LINENUMBER 17 L4
    GETSTATIC LOG.INSTANCE : LLOG;
    CHECKCAST Logger
    ASTORE 1
    LDC "println"
    ASTORE 2
    NOP
   L5
    LINENUMBER 24 L5
   L6
   L0
    NOP
   L7
    LINENUMBER 25 L7
    NOP
   L8
    LINENUMBER 18 L8
    LDC "Test console output"
    ASTORE 3
    NOP
   L9
    GETSTATIC java/lang/System.out : Ljava/io/PrintStream;
    ALOAD 3
    INVOKEVIRTUAL java/io/PrintStream.println (Ljava/lang/Object;)V
   L10
   L11
    LINENUMBER 18 L11
   L12
    LINENUMBER 19 L12
   L13
    NOP
   L1
    GOTO L14
   L2
    LINENUMBER 26 L2
    ASTORE 3
   L15
    LINENUMBER 27 L15
    ALOAD 1
    NEW java/lang/StringBuilder
    DUP
    INVOKESPECIAL java/lang/StringBuilder.<init> ()V
    LDC "Failed to "
    INVOKEVIRTUAL java/lang/StringBuilder.append (Ljava/lang/String;)Ljava/lang/StringBuilder;
    ALOAD 2
    INVOKEVIRTUAL java/lang/StringBuilder.append (Ljava/lang/String;)Ljava/lang/StringBuilder;
    LDC ". "
    INVOKEVIRTUAL java/lang/StringBuilder.append (Ljava/lang/String;)Ljava/lang/StringBuilder;
    ALOAD 3
    INVOKEVIRTUAL java/lang/Throwable.getMessage ()Ljava/lang/String;
    INVOKEVIRTUAL java/lang/StringBuilder.append (Ljava/lang/String;)Ljava/lang/StringBuilder;
    INVOKEVIRTUAL java/lang/StringBuilder.toString ()Ljava/lang/String;
    ALOAD 3
    INVOKEVIRTUAL Logger.warn (Ljava/lang/String;Ljava/lang/Object;)V
   L16
    LINENUMBER 28 L16
   L14
    LINENUMBER 29 L14
   L17
   L18
    LINENUMBER 20 L18
    RETURN
   L19
    LOCALVARIABLE $i$a$1$catchAll I L8 L13 4
    LOCALVARIABLE t$iv Ljava/lang/Throwable; L2 L16 3
    LOCALVARIABLE LOG$iv LLogger; L5 L17 1
    LOCALVARIABLE message$iv Ljava/lang/String; L5 L17 2
    LOCALVARIABLE $i$f$catchAll I L5 L17 5
    LOCALVARIABLE args [Ljava/lang/String; L3 L19 0
    MAXSTACK = 3
    MAXLOCALS = 6
{% endraw %}{% endhighlight %}


As we see the `catchAll` function call is inlined. We have `println` call as-is, without any anonymous function 
wrappers. Any combination of `catchAll` calls generates similar bytecode with `try/catch` blocks. Once can easily combine 
such calls to make a program easier to read on some higher level.

Disclaimer. Checked or unchecked exceptions are meaningful. I'm not trying to promote the idea to catch all possible exceptions
in every possible statement. The goal is to show it is possible to create a tiny function that would help to recure a number
of similar code snippets and improve readability. It is up to you to decide if an error is OK to ignore or to log without propagation.