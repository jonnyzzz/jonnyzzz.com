# libcurl and Kotlin/Native on Windows

**Date:** October 29, 2018  
**Author:** Eugene Petrenko  
**Tags:** curl, libcurl, windows, kotlin, kotlin/native

---

Building libcurl on Windows and using it from Kotlin/Native


Once upon a time, I decided to answer a question on
[StackOverflow](https://stackoverflow.com/questions/52871078/kotlin-native-libcurl-example-on-windows/52872429?noredirect=1#comment92694725_52872429)
to explain how to use `libcurl` with Kotlin/Native. Now it turned out I will cover a
more detailed instruction here. How [@shanselman](https://twitter.com/shanselman) once told in his talk - if
a reply is big enough it should go to a documentation of a blog post.

Building Curl and Libcurl on Windows
====================================

The first step is to open the https://curl.haxx.se/libcurl/ page and read it.
Let's download sources from https://curl.haxx.se/download.html. In my case,
I downloaded the [curl-7.61.1.zip](https://curl.haxx.se/download/curl-7.61.1.zip).
There is also a sources mirror on GitHub: https://github.com/curl/curl.

Of course, we need a Windows machine or a VM to build it and use it from Windows.

Let's extract the downloaded sources. There will be the `curl-7.61.1` folder. 
Let's assume the extracted `curl` sources directory
is the current working directory.

I open the `VS2015 x64 Native Command Prompt` shell on my machine. That one comes from
Microsoft Visual Studio 2015. There might be another shortcut to run the shell 
from a newer or older version of Visual Studio.   

It is a useful file under [winbuild/BUILD.WINDOWS.txt](https://github.com/curl/curl/blob/master/winbuild/BUILD.WINDOWS.txt)

Execute the command

```
cd winbuild
nmake /f Makefile.vc mode=dll
```

The command above build `curl` and `libcurl` for us. The build generates static library 
that uses some default dependencies from the system to run. For example, it uses
[Windows SSPI](https://docs.microsoft.com/en-us/windows/desktop/secauthn/sspi)
as the implementation of the SSL and TLS. Check out more options on `curl` building in the
[winbuild/BUILD.WINDOWS.txt](https://github.com/curl/curl/blob/master/winbuild/BUILD.WINDOWS.txt).

The compiled binaries are found under the `builds` folder. The contest should be as follows:
```
dir builds
...
10/29/2018  09:48 PM    <DIR>          .
10/29/2018  09:48 PM    <DIR>          ..
10/29/2018  09:48 PM    <DIR>          libcurl-vc-x64-release-dll-ipv6-sspi-winssl
10/29/2018  09:48 PM    <DIR>          libcurl-vc-x64-release-dll-ipv6-sspi-winssl-obj-curl
10/29/2018  09:48 PM    <DIR>          libcurl-vc-x64-release-dll-ipv6-sspi-winssl-obj-lib
...
```
We have our dynamic `curl` library and include files directory under 
the `builds/libcurl-vc-x64-release-dll-ipv6-sspi-winssl` folder.


Importing libcurl into Kotlin/Native
====================================

Let's use the [curl sample](https://github.com/JetBrains/kotlin-native/tree/master/samples/curl)
and the [libcurl sample](https://github.com/JetBrains/kotlin-native/tree/master/samples/libcurl) 
from the Kotlin/Native repository and adapt them to work on Windows too.

The first step is to create the `.def` file to import the native `libcurl` library into Kotlin. 
More details on that are explained in the 
[Interop with C Libraries](http://kotlinlang.org/docs/tutorials/native/interop-with-c.html)
tutorial.

Let's add the following `libcurl.def` file:
```
headers = curl/curl.h
headerFilter = curl/*
```

Now we may call the `cinteop` tool from Kotlin/Native from a parent folder, where we extracted `curl` sources:
```
cinterop -def libcurl.def -compilerOpts -Icurl-7.61.1\builds\libcurl-vc-x64-release-dll-ipv6-sspi-winssl\include -o libcurl
```

We assume here that we have Kotlin/Native compiler installed and registered in the system PATH. For more information, 
please refer to the 
[A Basic Kotlin Application](http://kotlinlang.org/docs/tutorials/native/basic-kotlin-native-app.html#obtaining-the-compiler).
Let's assume, we have a console, where the `kotlinc-native`, `cinterop`, and `klib` commands are available.

The call to `cinterop` generates the `libcurl.klib` file for us. Let's use it from the Kotlin/Native sources!

 
Using libcurl from Kotlin/Native
================================

It is time to follow the example from the [curl sample](https://github.com/JetBrains/kotlin-native/tree/master/samples/curl)
and create our first `curl` application in Windows. 

Let's create the file `curl.kt` with the following contents:

{% highlight kotlin %}{% raw %}
import libcurl.*
import kotlinx.cinterop.*

fun main(args: Array<String>) {
    val curl = curl_easy_init()
    if (curl != null) {
        curl_easy_setopt(curl, CURLOPT_URL, "http://jonnyzzz.com")
        curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L)
        val res = curl_easy_perform(curl)
        if (res != CURLE_OK) {
            println("curl_easy_perform() failed ${curl_easy_strerror(res)?.toKString()}")
        }
        curl_easy_cleanup(curl)
    }
}
{% endraw %}{% endhighlight %}

Now we call the command to build the executable with Kotlin/Native:
```
kotlinc-native curl.kt -l libcurl -linker-options "curl-7.61.1\builds\libcurl-vc-x64-release-dll-ipv6-sspi-winssl\lib\libcurl.lib"  -o kurl
```

The application `kurl.exe` is ready to go. The only thing it requires is the `libcurl.dll`. The file you may find under the
`curl-7.61.1\builds\libcurl-vc-x64-release-dll-ipv6-sspi-winssl\bin\libcurl.dll` path. You may try running it. 


Static Linking
==============

It is not too nice to have a requirement to have the `libcurl.dll` included and located near the executable we
create. Static linking, in theory, allows having only one solid binary, that contains everything.
One may easily change the `curl` build to `mode=static`. The result will be the static library `libcurl_a.lib`.
Linking it with Kotlin/Native binary turned out to be tricky. To start, Kotlin/Native uses MinGW environment and 
the `libcurl_a.lib` is compiled to use dynamic MSVCRT. Theoretically, it should be possible to make it work, if you
know the answer - just let me know!

It is also a good [comment for the original StackOverflow thread](https://stackoverflow.com/a/52872980/49811)
to use MinGW specific build of curl.