# Hints in Stack Traces on the JVM

**Date:** April 12, 2017  
**Author:** Eugene Petrenko  
**Tags:** jvm, debug, trace, library, opensource, stacktrace, frame, stack, java, named-stack-frames

---

Encode context in a thread dump or an exception stack trace for the JVM.

Remember a production application stack trace or thread dump? Were you able to understand 
what a thread was downing? Why was a thread idling/hanging/waiting? What was the context of it? 
What a command was it? Or, say you were digging the roots of a NullPointerException stack trace? 

Most time it's hard. 

There is a simple remedy. One may call `Threads.setName` to set/unset thread
name to indicate current activity and/or to add more information.

Hey, be aware of the `Threads.setName`. Some other code may also use it in their way.
Please, do not spoil it, if you can

Unfortunately, exception stack trace does not container thread name. So the fragile context is
lost if an exception is thrown. The only hope it is logged correctly, and logger includes
a thread name. Surprise! The full thread name. 


What else? Why cannot we include the information locally and so that it is not 
lost in an exception or in a logger message? Can we make it more context-aware and readable?

An example
==========

Consider an application, which runs a request for a given, say, `userId`. And it crashes with code like
{% highlight text %}{% raw %}
Exception in thread "main" com.jonnyzzz.blog.example.wtf.RemoteCrashServiceTimeOutException
	at com.jonnyzzz.blog.example.wtf.RemoteCrashMicroServiceAccessImpl.itWillNotCrash(crash.kt:5)
	at com.jonnyzzz.blog.example.logic.business.BusinessLogic.mightyMethod(BusinessLogic.kt:7)
	at com.jonnyzzz.blog.example.db.transaction.internals.InternalsForSure.transaction(InternalsForSure.kt:9)
	at com.jonnyzzz.blog.example.db.transaction.internals.InternalsForSure.transaction(InternalsForSure.kt:7)
	at com.jonnyzzz.blog.example.db.transaction.internals.InternalsForSure.transaction(InternalsForSure.kt:7)
	at com.jonnyzzz.blog.example.db.transaction.internals.InternalsForSure.transaction(InternalsForSure.kt:7)
	at com.jonnyzzz.blog.example.db.transaction.internals.InternalsForSure.transaction(InternalsForSure.kt:7)
	at com.jonnyzzz.blog.example.db.vendor.fun.AmazingDBSupport.runThisCodeFinally(AmazingDBSupport.kt:7)
	at com.jonnyzzz.blog.example.tansaction.meta.JokingTransaction.crzTr(JokingTransaction.kt:7)
	at com.jonnyzzz.blog.example.tansaction.Transaction.transaction(Transaction.kt:7)
	at com.jonnyzzz.blog.example.system.SystemInvariant.promoteB(SystemInvariant.kt:7)
	at com.jonnyzzz.blog.example.Ent.processA(Ent.kt:7)
	at com.jonnyzzz.blog.example.web.Controller.executeRequest(Controller.kt:10)
	at com.jonnyzzz.blog.example.EnterpriseAppKt.main(EnterpriseApp.kt:13)
{% endraw %}{% endhighlight %}


What was the context of the failure above? Does it somehow related to parameters that were around? 


Named Frames
============

I created the [Named Frames](https://github.com/jonnyzzz/named-java-frames)
library, which aims to help by including an additional information as *method calls*.

Let's now update the code and include `userId` and RemoteCrashMicroService backend URL into the thread
dump. That is done be wrapping method calls with code like that: 

{% highlight java %}{% raw %}
NamedStackFrame.global().forName("YOUR TEXT HERE").run(() -> {
    // it is called from a method, which contains 'YOUR TEXT HERE' in the full name
});
{% endraw %}{% endhighlight %}


The updated thread dump from the exception is now the following

{% highlight text %}{% raw %}
Exception in thread "main" com.jonnyzzz.blog.example.wtf.RemoteCrashServiceTimeOutException
	at com.jonnyzzz.blog.example.wtf.RemoteCrashMicroServiceAccessImpl$itWillNotCrash$1.call(crash.kt:8)
	at com.jonnyzzz.blog.example.wtf.RemoteCrashMicroServiceAccessImpl$itWillNotCrash$1.call(crash.kt:5)

	at __. service = backend-452 .__.call(JavaGeneratorTemplate.java:39)

	at com.jonnyzzz.blog.example.wtf.RemoteCrashMicroServiceAccessImpl.itWillNotCrash(crash.kt:7)
	at com.jonnyzzz.blog.example.logic.business.BusinessLogic.mightyMethod(BusinessLogic.kt:7)
	at com.jonnyzzz.blog.example.db.transaction.internals.InternalsForSure.transaction(InternalsForSure.kt:9)
	at com.jonnyzzz.blog.example.db.transaction.internals.InternalsForSure.transaction(InternalsForSure.kt:7)
	at com.jonnyzzz.blog.example.db.transaction.internals.InternalsForSure.transaction(InternalsForSure.kt:7)
	at com.jonnyzzz.blog.example.db.transaction.internals.InternalsForSure.transaction(InternalsForSure.kt:7)
	at com.jonnyzzz.blog.example.db.transaction.internals.InternalsForSure.transaction(InternalsForSure.kt:7)
	at com.jonnyzzz.blog.example.db.vendor.fun.AmazingDBSupport.runThisCodeFinally(AmazingDBSupport.kt:7)
	at com.jonnyzzz.blog.example.tansaction.meta.JokingTransaction.crzTr(JokingTransaction.kt:7)
	at com.jonnyzzz.blog.example.tansaction.Transaction.transaction(Transaction.kt:7)
	at com.jonnyzzz.blog.example.system.SystemInvariant.promoteB(SystemInvariant.kt:7)
	at com.jonnyzzz.blog.example.Ent.processA(Ent.kt:7)
	at com.jonnyzzz.blog.example.web.Controller$executeRequest$1.call(Controller.kt:12)
	at com.jonnyzzz.blog.example.web.Controller$executeRequest$1.call(Controller.kt:7)

	at __. user = jonnyzzz .__.call(JavaGeneratorTemplate.java:39)

	at com.jonnyzzz.blog.example.web.Controller.executeRequest(Controller.kt:11)
	at com.jonnyzzz.blog.example.EnterpriseAppKt.main(EnterpriseApp.kt:13)
{% endraw %}{% endhighlight %}

This one now includes the sensible information (as service name and userId)
which can be used to debug the original problem.


API
===

Named stack frames API is easy and flexible. 
The main entry point is `org.jonnyzzz.stack.NamedStackFrame`. There you may use either `#global()` method to access 
statically cached factory of named framed. 
The better is to use `#newInstance()` method to have an instance of the factory to explicitly control the lifetime. 

Both methods return an instance of `org.jonnyzzz.stack.NamedExecutor` interface, which contains all possible methods to wrap
a call with a named frame.


Implementation
==============

The implementation is covered in [the older post]({% post_url blog/2014-04-26-named-stack-frames-for-jvm %}). Note, the
API is slightly changed in 0.2.x.

The idea is to on-the-fly generate classes for every given name. All generated classes are loaded with a dedicated
classloader and cached. 

We implement our own class file weaver to avoid external dependencies from other libraries and thus to
simplify adoption of this library in your project. 

The library attempts to escape some _bad_ symbols from names you pass. All such symbols are replaced with '_'.


NamedStackFrame Costs
=====================

Custom information in stack traces is not free. We create and load classes to implement it. This means, 
it's your responsibility to make sure you will not consume all JVM memory on that. 

Practically, you should understand the number of possible names is limited and fits in the memory. That's it. 


Profiler Grouping of Calls
==========================

Do you use a profiler to monitor your application? A profiler presents such named 
methods (just like ordinary methods) as different method calls. That means you'll see a distribution of calls.

You'll see a distribution of time spent by each name: a distribution by `userId`, `action type` or `serviceId`
for the example above.

 
Android Support
===============

All the time I was wondering if it's helpful for Android applications as well. Do you like the idea?
Please contribute!
 

License
=======

The library is [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0)

Download
========

Sources are on [GitHub](https://github.com/jonnyzzz/named-java-frames)

Binaries are on JCenter / Bintray

[ ![Download](https://api.bintray.com/packages/jonnyzzz/maven/named-frames/images/download.svg) ](https://bintray.com/jonnyzzz/maven/named-frames/_latestVersion) [ ![Build Status](https://travis-ci.org/jonnyzzz/named-java-frames.svg?branch=master)](https://travis-ci.org/jonnyzzz/named-java-frames)


In Gradle, just add
```
repositories {
  jcenter()
}

dependencies {
  compile 'org.jonnyzzz.named-frames:named-frames:<LATEST VERSION>'
}
```

Issues
======

On [GitHub](https://github.com/jonnyzzz/named-java-frames)