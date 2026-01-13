# Minimalistic C library and Kotlin/Native

**Date:** May 28, 2018  
**Author:** Eugene Petrenko  
**Tags:** mac, macOS, linker, kotlin, kotlin/native

---

The most trivial [Kotlin/Native](https://kotlinlang.org/docs/reference/native-overview.html) 
example of using `C` library

Some time ago I stuck linking a C binary into an executable with 
[___isOSVersionAtLeast is undefined]({% post_url blog/2018-05-16-link-error %}). 
And thus I decided to simplify things to localize the problem. I will write 
a dedicated post with the solution for `___isOSVersionAtLeast is undefined`. 

Let's focus on the most trivial library example. To start with, I assume 
you have [Kotlin/Native](https://kotlinlang.org/docs/reference/native-overview.html)
compiler in the OS Path. Have a look at 
[the main tutorial](https://kotlinlang.org/docs/tutorials/native/basic-kotlin-native-app.html#obtaining-the-compiler)
or merely download the compiler from [GitHub Releases page](https://github.com/JetBrains/kotlin-native/releases){:target="_blank"}.
Beware, the compiler will download the toolchain on the very first run.
The `konanc` and `cinterop` tools should be in the `PATH` of your terminal or console.

The rest of the post is created and tested on macOS. It should just work on Linux, but I did not check it. 
You shall have C/C++ toolchain installed too. On macOS, it is enough to install and run Xcode. 
 
C Library
---------

The `lib.h` file looks as follows
{% highlight c %}{% raw %}
#ifndef LIB2_H_INCLUDED
#define LIB2_H_INCLUDED

#ifdef __cplusplus
   extern “C” {
#endif

int foo();

#ifdef __cplusplus
   }
#endif
#endif //LIB2_H_INCLUDED
{% endraw %}{% endhighlight %}

The `extern "C"` block is not needed (unless you use C++) and left here 
for [C++ compatibility](https://stackoverflow.com/questions/1041866/what-is-the-effect-of-extern-c-in-c).
Thus you may shrink the file to `lib.h`:
{% highlight c %}{% raw %}
#ifndef LIB2_H_INCLUDED
#define LIB2_H_INCLUDED

int foo();

#endif //LIB2_H_INCLUDED
{% endraw %}{% endhighlight %}

[#include guards](https://stackoverflow.com/questions/1653958/why-are-ifndef-and-define-used-in-c-header-files)
in your `.h` files are a standard ritual. They are necessary for multiple `.h` files projects. 

The code above declares one function for export `int foo()`. We use the `.h` file later 
with Kotlin/Native `cinterop` tool import the function into Kotlin/Native.

Let's create a `lib.c` for implementation for the `foo` function in C:

{% highlight c %}{% raw %}
#include "lib.h"

int foo() {
  return 42;
}
{% endraw %}{% endhighlight %}

Now we compile the C sources into a C library. For that we call `gcc` to compile (and link)
the `.c` sources into a C static library:

{% highlight bash %}{% raw %}
gcc -c "-I$(pwd)" lib.c -o lib.o
ar rcs lib.a lib.o
{% endraw %}{% endhighlight %}

It will be a bit more complicated if you have several `.c` source files.

At that moment we have
- `lib.h` -- the header
- `lib.c` -- the implementation
- `lib.o` -- the intermediate object file
- `lib.a` -- the compiled static library


Importing to Kotlin/Native
--------------------------

We need to import the C library to be used with Kotlin/Native. It is as tricky as 
calling a `cinterop` tool.

The `cinterop` tool uses the definition file for my library `lib.def`:

{% highlight text %}{% raw %}
headers = lib.h
{% endraw %}{% endhighlight %}

The file helps to specify all necessary options for bigger libraries. 

Not it is the time to call the `cinterop` with the following options:

{% highlight bash %}{% raw %}

cinterop -def lib.def -compilerOpts "-I$(pwd)" -o lib.klib
{% endraw %}{% endhighlight %}

The result is a `lib.klib` file. A Kotlin/Native library file. It contains Kotlin APIs for 
our `lib.h`. It bridges C types and Kotlin/Native types (trivial `Int` in our case) and helps
to deal with memory management (not needed for our example).

At that moment we have
- `lib.h` -- the header
- `lib.c` -- the implementation
- `lib.o` -- the intermediate object file
- `lib.a` -- the compiled static library
- `lib.def` -- the definitions for `cinterop`, reference to `lib.h`
- `lib.klib` -- the compiled Kotlin/Native library to access API from `lib.h` 

Compiling with Kotlin/Native
----------------------------

We need an entry point and Kotlin sources. I created the `main.kt` file for that

{% highlight kotlin %}{% raw %}

fun main(args: Array<String>) {
  val z = lib.foo()
  println("The foo() from lib.h returned $z")
}
{% endraw %}{% endhighlight %}

And I compile it with the following command
{% highlight bash %}{% raw %}
konanc -l lib.klib main.kt -linkerOpts lib.a -o main.kexe
{% endraw %}{% endhighlight %}

and run the `./main.kexe` to see the resulting text is being printed:

```
./main.kexe
The foo() from lib.h returned 42

```

Conclusion
----------

That is a trivial C library linking case. For something real, you'll probably want to 
use [Gradle build](https://github.com/JetBrains/kotlin-native/blob/master/GRADLE_PLUGIN.md).
 
Take a look at the [Interop with C libraries](https://kotlinlang.org/docs/tutorials/native/interop-with-c.html) tutorial
or the list of [Platform libraries](https://github.com/JetBrains/kotlin-native/blob/master/PLATFORM_LIBS.md).

You may find it useful to check the 
[C Interop docs](https://github.com/JetBrains/kotlin-native/blob/master/LIBRARIES.md) 
or [Interop with Swift and Objective-C](https://github.com/JetBrains/kotlin-native/blob/master/OBJC_INTEROP.md) page.