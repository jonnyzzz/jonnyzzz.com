# Undefined Symbol on macOS

**Date:** May 16, 2018  
**Author:** Eugene Petrenko  
**Tags:** mac, macOS, linker, kotlin, kotlin/native, curl

---

___isOSVersionAtLeast is undefined. How I spent several days compiling curl and linking it.


I use [Kotlin/Native](https://kotlinlang.org/docs/reference/native-overview.html) to create a 
tiny command line utility for Windows, Linux, and macOS. I believe the best app is the app without
dependencies, and thus without requirements and dependencies hassle. That is easier than 
baking os-specific packages or installers. 

[Curl](https://curl.haxx.se/) is one of my dependencies for this project. So I compiled it to 
`libcurl.a` and lined to [Kotlin/Native](https://github.com/JetBrains/kotlin-native/blob/master/INTEROP.md)
easily with a few lines of Gradle script.

It failed with something cryptic on my macOS 10.13.4 with Xcode 9.3.1. 

```
Undefined symbols for architecture x86_64:
  "___isOSVersionAtLeast", referenced from:
      _singleipconnect in libcurl.a(libcurl_la-connect.o)
      _darwinssl_connect_common in libcurl.a(libcurl_la-darwinssl.o)
      _darwinssl_version_from_curl in libcurl.a(libcurl_la-darwinssl.o)
ld: symbol(s) not found for architecture x86_64
```

Digging internet did not help. And that is mostly why I am blogging that one. Changing or patching the 
way I build curl was useless too. Nikolay suggested me to check target version of my binaries. That was it.
Kudos Nikolay!

I should have compiled the curl with `10.13` as min version for Mac. I did that by setting
`CFLAGS` environment variable to `-mmacosx-version-min=10.13` for `./configure` and `make` commands.  

Continue reading the [next part of the investigation]({% post_url blog/2018-06-05-link-error-2 %})