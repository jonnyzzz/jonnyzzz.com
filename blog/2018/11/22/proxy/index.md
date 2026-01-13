# Proxy and Checked Exceptions in Java

**Date:** November 22, 2018  
**Author:** Eugene Petrenko  
**Tags:** java, jvm, kotlin

---

java.lang.reflect.Proxy and checked exceptions

On-the-Fly Proxy
----------------
Say on have an interface `Foo` with several (hundreds) methods. Is it possible to implement an
interface on-the-fly? Without having an implementation code? Yes. It is possible. 
The standard possibility is
[java.lang.reflect.Proxy](https://docs.oracle.com/javase/8/docs/api/java/lang/reflect/Proxy.html).
The `newProxyInstance` method helps to create an on-the-fly implementation. One provides
an interceptor object that is called for every method invocation on the interface implementation instance. 

Besides the standard Proxy API, there are libraries, that do the same thing, for example,
[Byte Buddy](https://bytebuddy.net/) or [CGLIB](https://github.com/cglib/cglib).

In this post, we will use the standard JRE API - `java.lang.reflect.Proxy`

Proxy and Checked Exceptions
----------------------------
Let's consider the following code in Java:


```java
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;

interface Foo {
  void bar();
}

public static void main(String[] args) {
  final Foo proxy = (Foo)Proxy.newProxyInstance(Foo.class.getClassLoader(), new Class[]{Foo.class}, new InvocationHandler() {
    @Override
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
      throw new Exception("fail");
    }
  });
  //what is the exception?
  proxy.bar();
}
```

The code is trivial. We have the interface `Foo`, and we implement it via `Proxy#newProxyInstance`. 
The implementation of the Proxy instance throws an exception of type `Exception`.
Will we have the exception of type `Exception` as a result? 

Running the Example
-------------------
Let's execute the example and see what we have:

```bash
Exception in thread "main" java.lang.reflect.UndeclaredThrowableException
	at $Proxy0.bar(Unknown Source)
	at ProxyJava.main(ProxyJava.java:22)
Caused by: java.lang.Exception: fail
	at ProxyJava$1.invoke(ProxyJava.java:17)
	... 2 more
```

The answer is **NO**. We have `java.lang.reflect.UndeclaredThrowableException` exception.


Checked Exceptions in Java
--------------------------
As we all know, Java has checked exceptions. It means one declares what exceptions are
possibly thrown from a method. The main class of all exceptions is 
[java.lang.Throwable](https://docs.oracle.com/javase/8/docs/api/java/lang/Throwable.html).

In Java language, we use `throws` to indicate that a method may throw an exception. For example,
`throws IOException`. 

There are two specific sub-classes of `Throwable`, which does not require to be declared
by the `throws` keyword - `java.lang.Error` and `java.lang.RuntimeException`. All sub-classes
of those two types are free to throw without declaration. 

Proxy and UndeclaredThrowableException
--------------------------------------
The [UndeclaredThrowableException](https://docs.oracle.com/javase/8/docs/api/index.html?java/lang/reflect/UndeclaredThrowableException.html)
is the specific exception type that is used in the create a proxy implementation of an interface
to preserve checked exceptions in Java. 
As we see from the Javadoc, the exception is used to wrap any checked exceptions that are not 
declared with the `throws` block in the interface declaration. 

Proxy and JVM Languages
-----------------------
JVM ecosystem is huge. There are many languages for the JVM, including 
[Kotlin](https://kotlinlang.org),
[Groovy](http://groovy-lang.org/),
[Scala](https://www.scala-lang.org/)
and so on, that does not have checked exceptions. 

Checked exceptions are checked by the compiler, on the JVM bytecode level, 
there is no difference between exceptions at all. 

It is quite easy to get `UndeclaredThrowableException` at some 
unexpected places if mixing such languages with `java.lang.reflect.Proxy`!

For example, in Kotlin:

```kotlin
import java.lang.reflect.Proxy

internal interface Foo {
  fun bar()
}

fun main(args: Array<String>) {
  val proxy = Proxy.newProxyInstance(
    Foo::class.java.classLoader,
    arrayOf<Class<*>>(Foo::class.java)
  ) { _, _, _ ->
    throw Exception("fail")
  } as Foo

  proxy.bar()
}
```

The same code reads correctly but does not work. It is allowed in Kotlin to throw `Exception` from
a method (because exceptions are not checked), but it will **not** work via the
`java.lang.reflect.Proxy`. We will have the following execution result

```bash
Exception in thread "main" java.lang.reflect.UndeclaredThrowableException
	at com.sun.proxy.$Proxy0.bar(Unknown Source)
	at ProxyKTKt.main(ProxyKT.kt:15)
Caused by: java.lang.Exception: fail
	at ProxyKTKt$main$proxy$1.invoke(ProxyKT.kt:12)
	at ProxyKTKt$main$proxy$1.invoke(ProxyKT.kt)
	... 2 more

```

Fixing the UndeclaredThrowableException
---------------------------------------
To avoid the `UndeclaredThrowableException` one need to declare the exceptions
explicitly with `throws` block. That solves the problem in Java example above.
Similarly, it solves the problem in the Kotlin snippet too: we add the 
`@Throws(Exception::class)` annotation on the `bar` function.

One may have a look at the implementation of the `Proxy#newProxyInstance`
in the sources of JVM. It turns out it is not possible to disable that
logic in the implementation. One is not allowed to breach Java's checked 
exceptions with `Proxy#newProxyInstance`.

There are two ways. One is to declare `throws` for all interfaces 
that are used with `Proxy#newProxyInstance`. Of course, it is too easy to
forget doing in languages without checked exceptions. Tests may help. 

An alternative could be to implement or use another variant of the
`Proxy#newProxyInstance`, that does not do the check. Let me know
in the comments if you'd like to learn more, how exactly the 
`Proxy#newProxyInstance` or similar proxies are implemented.