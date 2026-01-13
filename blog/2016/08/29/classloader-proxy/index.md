# Proxy calls between classloaders

**Date:** August 29, 2016  
**Author:** Eugene Petrenko  
**Tags:** java, jvm, classloaders

---

There are so many tricky stories around on classloaders in Java. Classloading is a powerful technique from the 
one hand. From the other it's the place where it so easy to make mistakes. Some are simply afraid using them. 

I solved a simple puzzle with isolating classes I want to share.

Backgrounds
===========

There are integration tests in a project. Those integration tests starts several web applications, 
bind them together and to some black-box tests. 
The vital part of such tests is to provide a classpath isolation between test classes and classes 
of applications that are running. 

To start each of those web servers I use Jetty Embedded. Well, I load Jetty classes for each 
web application I start within a separate classloaders hierarchy. I like Jetty, but I want to 
isolate any side effects, thus loading it several times, thanks it's tiny, is the way to go. 

All helper classes to start/stop/configure web applications forms an API that helps for a tests run. 

It turns out to be tricky to isolate those runner classes from a test classpath. From one hand we'd 
like to have an APIs available for test class to use, from the other hand, it is still required 
to make sure the classpath of web application, hence Jetty Embedded it not polluted with test module 
dependencies.

The Problem
===========

Say we have and `API.jar` and `IMPL.jar`. We are looking on how to load the `IMPL.jar` with a clean
classpath and still have a change to bind it to the `API.jar` that is a part of some other huge classpath.

The goal is to the following: 

- Test framework uses `API.jar`
- IMPL.jar also uses `API.jar`, but it does not see any test-related classes
 
The problem is that it is test framework / test runner that loading test classes. We are unlikely to change that.
Otherwise we have to take care of test runners, IDEs, CI, debugging.

Obvious solutions
=================
Load all classes within one JVM. This violates the task, but may be the easiest way. The future issue here 
can be a jar hell, if one has different libraries used in the application / tests or the loader.

Another solution could be in using OSGi. It's a complicated framework that uses security manager to isolate
classes visibility. 

Future solution with Java 9 modules is also a way to go. But for now, it's too early.

Just Classloading
=================

The most simple solution is to load classes with *child-first* classloader. This is **NOT** the way
to isolate dependencies, but at least this is the way to have IMPL.jar dependencies win on classloading.

There are at least two things to take case of

Case 1 : JVM classes
------------------
Child first classloaders should still load JVM classes first.
 
It may turn out the classpath contains some classes that are now included into JVM. Those classes are 
still included into a package to provide a compatibility with older JVM versions. Those classes are 
simply ignored by the JVM when default classloading is used.

It may generate tricky issues when child first classloader attempts to load wrong classes since 
those classes will likely register themselves in the OS.

The solution here is the following. We crete a classloader:
{% highlight java %}{% raw %}
  val jvmClassLoaderDelegate = URLClassLoader(new URL[0], null)
{% endraw %}{% endhighlight %}

This classloader is the first one to check in the child classloader implementation. It is the easiest way I know
to delegate to the system classloader. The Classloader itself uses native method in order to delegate to it.


Case 2: Resources
-----------------

It's so easy to implement child first classloader. It is also so easy to forget about resources. The child first
strategy must be implemented for resources too. Otherwise, it may break some libraries which uses resources.

Finally classloading with child first delegation does not solve the initial problem. It does not allow to 
fully isolate test classes (e.g. test framework) from `IMPL.jar` classes 


The Proxy Trick
================

The idea is to load `API.jar` twice and than use to `java.lang.reflect.Proxy` to bind interfaces part from 
tests classspath to implementations.

A trick is to have yet another classloader with `null` as parent. The loader classpath includes 
only `API.jar`, `IMPL.jar` and dependencies of `IMPL.jar`. 

Next we create a `java.lang.reflect.Proxy` to create an instance of an API interface that delegates
to the implementation class that is loaded by the other classloader. We are not able to cast here,
since we have `API.jar` loaded twice. 

Unfortunately, this will only work when API interface methods uses JVM classes as parameters 
and return types. There are no common 
classloaders between `IMPL.jar` and tests, thus ClassCastException will be thrown for other types.
 
Recursive Proxy Trick
=====================

The last limitation can be solved by a bit more complicated trick of 3 steps

- Create a proxy for API interface
- In the implementation, check all parameter types and proxy every parameter with non system classloader
- In the implementation, proxy return values in opposite way
- Apply the following proxies recursively if `API.jar` interfaces are complex
 
This approach allows to use JVM classes and `API.jar` interfaces between the bound. It will not work 
with classes, since it is the limitation of `java.lang.reflect.Proxy`. 

The overall trick is implemented as follows

{% highlight java %}{% raw %}
/*
 * creates a proxy for an object obj loaded in sourceLoader hierarchy 
 * that is visible in destLoader as destClass interface
 * assuming all methods of destClass are implemented in obj
 * exactly with same signature
*/
Object proxy(final Object obj,
             final ClassLoader sourceLoader,
             final ClassLoader destLoader,
             final Class<?> destClass) {

  return Proxy.newProxyInstance(destLoader, new Class<?>[]{destClass},
          (proxy, method, args) ->
                  threadClassLoader(sourceLoader, () -> {
                    final Class<?>[] mappedArgTypes = new Class<?>[args == null ? 0 : args.length];
                    final Object[] mappedArgs = new Object[mappedArgTypes.length];
                    final Class<?>[] sourceTypes = method.getParameterTypes();
                    
                    for (int i = 0; args != null && i < mappedArgTypes.length; i++) {
                      if (sourceTypes[i].getClassLoader() == null) {
                        mappedArgTypes[i] = sourceTypes[i];
                        mappedArgs[i] = args[i];
                      } else {
                        mappedArgTypes[i] = sourceLoader.loadClass(sourceTypes[i].getName());
                        mappedArgs[i] = proxy(args[i], destLoader, sourceLoader, mappedArgTypes[i]);
                      }
                    }

                    final Method realMethod = obj.getClass().getMethod(method.getName(), mappedArgTypes);
                    final Object result = realMethod.invoke(obj, mappedArgs);
                    if (method.getReturnType().getClassLoader() == null) {
                      return result;
                    }
                    return proxy(result, sourceLoader, destLoader, method.getReturnType());
                  }));
  }
{% endraw %}{% endhighlight %}

Limitations
===========

Current implementation works only with API interfaces. It does not allow sharing classes or enums. 
Enums from `API.jar` can be easily supported be adding an explicit checking. 
Classes cannot be mapped this way. At least because it is not allowed in `java.lang.reflect.Proxy`. 
From the other hand, it's not clear how class state can be transferred at all.

Side Note
==========

It may be necessary to change `Thread#contextClassloader` to the right one before calling a 
method from different classloader. This trick makes dynamic classloading in libraries work 
correctly for some cases. Otherwise, there is a possibility that a class from another classpath
is created from `IMPL.jar` code (say, via `Class#forName` call)

Conclusion 
==========

I used the approach to implement integration tests that are running several web application 
instances within one JVM. All instances are now isolated from each other and from tests classpath.

Running everything within one JVM helps to avoid issues with leaked processes or applications as well as
allows one to debug every application or even all applications easily!