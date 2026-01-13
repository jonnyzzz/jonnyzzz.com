# Understanding isOSVersionAtLeast on macOS

**Date:** June 13, 2018  
**Author:** Eugene Petrenko  
**Tags:** mac, macOS, linker, kotlin, kotlin/native, curl

---

Understanding ___isOSVersionAtLeast on macOS is not defined

Include
-------

I came across with the linker problem. My application was not able to link with the
[___isOSVersionAtLeast symbol is undefined]({% post_url blog/2018-05-16-link-error %}) error.
It was the problem linking `curl` with a
[Kotlin/Native](https://kotlinlang.org/docs/reference/native-overview.html)
app. I did a tiny project to [reproduce the linker error](https://github.com/jonnyzzz/demo-static-lib).
As a side effect, here is a [Minimalistic C library and Kotlin/Native]({% post_url blog/2018-05-28-minimalistic-kn %})
example. And finally, the main [rant and investigation post]({% post_url blog/2018-06-05-link-error-2 %}). The good part
is I got a suggestion to try. 


Use clang not ld
----------------

The suggestion I got (and I say thank you for that) was to use `clang` command, not the `ld` one:
{% highlight bash %}{% raw %}
clang -mmacosx-version-min=10.10 -lc main.o lib.a
{% endraw %}{% endhighlight %}

It did work. It was able to link. Next, we may try `-v` switch to see how it works inside, 
with arguments split per lines and long paths simplified:
 
{% highlight text %}{% raw %}
> clang -mmacosx-version-min=10.10 -lc main.o lib.a -v

Apple LLVM version 9.1.0 (clang-902.0.39.2)
Target: x86_64-apple-darwin17.6.0
Thread model: posix
InstalledDir: /Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin

/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/ld 
    -demangle 
    -lto_library /Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/lib/libLTO.dylib 
    -dynamic 
    -arch x86_64 
    -macosx_version_min 10.10.0 
    -o a.out 
    -lc 
    main.o 
    lib.a 
    -lSystem 
    /Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/lib/clang/9.1.0/lib/darwin/libclang_rt.osx.a
    
{% endraw %}{% endhighlight %}
 
The right path (and I did it wrong in the [previous post]({% post_url blog/2018-06-05-link-error-2 %})) is 
```
/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/lib/clang/9.1.0/lib/darwin/libclang_rt.osx.a
```

Still, the best way to use that commandline is to have no such commandline in the build. 

The Linker Error Solution
-------------------------

The answer here is to use `clang` command instead of `ld` command. Note, that
command line options are different, and `clang` calls
(specify `-v` key to see that) `ld` with additional arguments.


Linking with Kotlin/Native
==========================

At that point, we have a workable `inc.sh` script to compile and link the static library with the executable
[in the repository on GitHub](https://github.com/jonnyzzz/demo-static-lib). Time to fix `in.sh` that links
the static C library with a [Kotlin/Native](https://kotlinlang.org/docs/reference/native-overview.html)
executable. You may want to have a look at the introductory post
[here]({% post_url blog/2018-05-28-minimalistic-kn %}).

A Dumb Approach
---------------

The very first (and dump) fix is to include the `libclang_rt.osx.a` path (see above) into the `konanc` call with
the `-linkerOpts <path>/libclang_rt.osx.a`. It make the code compile and run. 


Right Approach
--------------

Let's debug how Kotlin/Native executes the linker first. You pass the `--verbose linker` to see the verbose output 
from the linking phase (use `konanc --list_phases` to learn all phases). The output on my machine is as follows, 
with arguments split per lines and long paths simplified:

{% highlight text %}{% raw %}
> konanc -l lib.klib main.kt -linkerOpts  lib.a  -linkerOpts $L -o main.kexe --verbose linker

/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/ld \
    -demangle
    -object_path_lto temporary.o 
    -lto_library /Users/jonnyzzz/.konan/dependencies/clang-llvm-5.0.0-darwin-macos/lib/libLTO.dylib 
    -dynamic 
    -arch x86_64 
    -macosx_version_min 10.11.0 
    -syslibroot /Applications/Xcode.app/<...>/SDKs/MacOSX10.13.sdk 
    -o <target folder>/main.kexe 
    <temp folder>/combined.o 
    -S 
    -lc++ 
    -lobjc 
    -framework Foundation 
    -lSystem <Konan Toolchaing path>/libffi.a 
    -alias _Konan_main _main 
    lib.a 
    <our hack path to>/libclang_rt.osx.a

{% endraw %}{% endhighlight %}

Let's compare the commands. The linker executable is selected right from both sides. The sensible difference
is we miss `libclang_rt.osx.a` from the Kotlin/Native command. There are two ways to go:
- link the `libclang_rt.osx.a` with `lib.a` before the final linking
- infer path to `libclang_rt.osx.a` and include it into the linker command

Checking `clang --help` and I found the `-print-libgcc-file-name` argument. It does provide hints, 
but it is not enough just now. 

The Outcome
===========

Frankly, I do not like linking with `libclang_rt` explicitly. The library is a part
of toolchain internals. It will make builds too fragile or not incorrect.
The hack will not worth it in the long run. 

The right way, as I see it, is to fix the original library build to make 
sure it is pre-linked with all necessary internals.
That matches with the encapsulation principle. It simplifies the rest. 
The backup plan is to call `clang` with `-v` key, parse the command output
to get the path to the `libclang_rt`, and use it as an explicit library.

Building Curl
-------------

A pre-history. I first saw the missing `___isOSVersionAtLeast` symbol error
while 
[building and static linking]({% post_url blog/2018-05-16-link-error %})
the [libcurl](https://curl.haxx.se). My goal is to have a
self-contained static library out of it. 

I used the wrong artifact and build it incorrectly. I see the right static library 
is somewhere under `curl` build directory. 
I did that wrong. Do that right. Respect the privacy and build internals. 
 
The right way is 
- to set install prefix path in `./configure`
- to call `make install`
- use artifacts for the prefix path
- deliver the `libclang_rt` as dependency (or [merge it in?](https://stackoverflow.com/questions/3821916/how-to-merge-two-ar-static-libraries-into-one))

The library under the prefix do contain reference to our 
favorite `___isOSVersionAtLeast` symbol. The `make install` package
looks reusable and reduces hard-coded build hacks, still.