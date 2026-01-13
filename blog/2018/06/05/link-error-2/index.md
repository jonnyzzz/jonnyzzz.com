# Undefined isOSVersionAtLeast on macOS

**Date:** June 05, 2018  
**Author:** Eugene Petrenko  
**Tags:** mac, macOS, linker, kotlin, kotlin/native

---

Solving ___isOSVersionAtLeast is undefined or CLang intrinsics.


A few weeks ago I wrote about [___isOSVersionAtLeast is undefined]({% post_url blog/2018-05-16-link-error %}) problem.
At some point I realized I did NOT find a solution.

That time I focused on reproducing the problem with a tiny library of only a 
few code lines. I did that. A tiny static library.
It wrote details in the recent post
[Minimalistic C library and Kotlin/Native]({% post_url blog/2018-05-28-minimalistic-kn %}).
Now I can check the linking either with 
[Kotlin/Native](https://kotlinlang.org/docs/reference/native-overview.html) 
or with a plain C.

The `main.c`:
{% highlight c %}{% raw %}
#include "lib.h"
#include <stdio.h>

int main(int arg, char** argv) {
  int z  = foo();
  printf("The result is %d", z);
}
{% endraw %}{% endhighlight %}

I call the following to compile and link `main.c` with my `lib.a` 
[library]({% post_url blog/2018-05-28-minimalistic-kn %}):
{% highlight bash %}{% raw %}
gcc -c  main.c -o main.o
ld -macosx_version_min 10.10  -lc  main.o lib.a
{% endraw %}{% endhighlight %}

I do the on macOS 10.13.3 with Xcode 9.3.1 and macOS 10.13.5, Xcode 9.4. 

The Linkage Error
-----------------

It was an assumption of mine to check for 
[Clang Language Extensions](https://clang.llvm.org/docs/LanguageExtensions.html),
and finally, I was able to reproduce the linkage error with 
only the following code in `lib.c` targeting macOS `10.10`, but not macOS `10.13`:

{% highlight c %}{% raw %}
int foo() {
  /// that is a CLang extension
  if(__builtin_available(macOS 10.12, iOS 9.0, tvOS 9.0, watchOS 2.0, *)) {
    return 256;
  }

  return 42;
}
{% endraw %}{% endhighlight %}

And the linker error:

{% highlight text %}{% raw %}
Undefined symbols for architecture x86_64:
  "___isOSVersionAtLeast", referenced from:
      _foo in lib.a(lib.o)
{% endraw %}{% endhighlight %}

I ran the `ld` command with `-macosx_version_min 10.10` to target macOS `10.10`. The 
argument specifies the minimal version of macOS the created binary supports.

More experiments with arguments help me to find that CLang is smart to optimize that 
code if the check makes no sense.
For example, CLang optimizes the call `__builtin_available(macOS 10.12,*)` when I target
`10.12` or `10.13`. It also means no linkage error. 
The call `__builtin_available(macOS 10.14,*)` is never optimized, as long as I cannot target
`10.14` yet.

My [linkage problem]({% post_url blog/2018-05-16-link-error %}) was not in the target version 
specification at all. Otherwise, the problem was with a missing library. I was missing the 
compiler-runtime library in my `ld` call.
I found the hacky path (on [my machine](https://www.google.de/search?q=works+on+my+machine){:target="_blank"}) 
to solve the linker error: 

```
/Library/Developer/CommandLineTools/usr/lib/clang/9.1.0/lib/darwin/libclang_rt.osx.a
```

That one defines the symbol I was missing. The only problem is the path hard-codes 
too many internals. It is too internal to be used directly from a build. It seems to 
be a part of Xcode 9.1.0, which is too old. 

compiler-rt
-----------

[LLVM "compiler-rt"](https://compiler-rt.llvm.org/) that is the place with the documentation
of the LLVM and CLang features, that requires a runtime. It includes nice and helpful 
features inside. There is still no answer with the correct linker options.
I have no plans to build my own toolchain.

The right fix
-------------

The best fix for `___isOSVersionAtLeast` undefined symbol so far is to include the missing 
runtime library to an `ld` command. It only needs a path to the static library with no other
arguments. Shall a build tool help here? I do not know yet.

The worst here is one needs to generate the path manually. One need to know the Xcode (aka toolchain)
version to do that. And the trickiest is to make sure the path is updated once Xcode or something
else is updated. 

I am looking to find the best way to include the `compiler-rt`. If you know something, 
please comment below. 

Continue reading the [next part of the investigation]({% post_url blog/2018-06-13-link-error-3 %})