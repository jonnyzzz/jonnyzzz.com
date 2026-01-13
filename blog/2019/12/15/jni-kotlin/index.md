# JNI with Kotlin/Native

**Date:** December 15, 2019  
**Author:** Eugene Petrenko  
**Tags:** jvm, java, kotlin, kotlin-native, jni, native

---

Calling native code from our cosy JVM environment was and is possible. JVM comes with
the magical JNI APIs layer to make that. In this post we show how to use the JNI
from a Kotlin/JVM program and how to implement the native
counter-part with Kotlin/Native. 

The example project contains several parts:
* The JVM part (define a native method, load native library, call the API)
* The Native part (build as shared library, register callback in the JVM, have fun)

## The JVM Side

Let's implement the JVM side in Kotlin. It will be enough to have the following code:

```kotlin
package org.jonnyzzz.jni.java

class NativeHost {
  external fun callInt(x: Int) : Int
}
```

The `external` keyword in Kotlin is the same as the `native` keyword in Java. Both mean
the implementation of the method comes from the native library.


## The Kotlin/Native Shared Library

The experiment was to use the same programming language to implement the native
part too. We use [Kotlin/Native](https://kotlinlang.org/docs/reference/native-overview.html)
for that. 

The second point to try Kotlin/Native is to use the
[Kotlin Multiplatform Programming](https://kotlinlang.org/docs/reference/multiplatform.html)
to share some code between Native and JVM worlds. I will omit examples of that
in the current post.

JVM looks for specific symbol names to resolve native methods. We may find 
[the full spec](https://docs.oracle.com/en/java/javase/11/docs/specs/jni/design.html#resolving-native-method-names)
in the documentation. The `callInt` function has the following symbol name:

```c
jint Java_org_jonnyzzz_jni_java_NativeHost_callInt(JNIEnv *env,
                                                   jobject obj, 
                                                   jint i);
```
The first two parameters are added for all JNI calls. The `JNIEnv` allows
accessing the JVM to say create an object or throw an exception. We do
not need these parameters for our example, but we have to keep them for
binary compatibility. The function name in our example is generated
as follows:
```
Java_<package name>_<class name>_<method_name>
```

That encoding does not work for overloaded functions (there is on support for
overloads in C). The
[JNI specification](https://docs.oracle.com/en/java/javase/11/docs/specs/jni/design.html#resolving-native-method-names)
defines how to create a longer names with mangling to overcome the limitation.

The following declaration in Kotlin/Native code
will implement it:

```kotlin
@CName("Java_org_jonnyzzz_jni_java_NativeHost_callInt")
fun callInt(env: CPointer<JNIEnvVar>, clazz: jclass, it: jint): jint {
  initRuntimeIfNeeded()
  Platform.isMemoryLeakCheckerActive = false

  println("Native function is executed with: $it")
  return it + 1
}
```

Here we use the `@CName` annotation to instruct
[the cinterop](https://kotlinlang.org/docs/reference/native/c_interop.html)
to export the function as a symbol of the shared library.

## The C interop Setup

The example above requires a project setup to work. 
We need to import the `jni.h` header into Kotlin/Native.
[The cinterop](https://kotlinlang.org/docs/reference/native/c_interop.html)
tool helps us to generate Kotlin code from a C library definitions. 

## The Project Setup

Before we jump into the native world, let's create a project. We'll use Gradle project,
written in Kotlin. You may [see the code](https://github.com/jonnyzzz/kotlin-jni-mix) from
my GitHub or create a new one from a scratch. It will the
[kotlin multiplatform](https://kotlinlang.org/docs/reference/building-mpp-with-gradle.html) plugin.

The initial project setup in a `build.gradle.kts` file could look like that:
```kotlin
plugins {
  kotlin("multiplatform") version "1.3.61"
}

repositories {
  mavenCentral()
}

kotlin {
  jvm()

  macosX64("native") {..} // see below

  sourceSets["jvmMain"].dependencies {
    implementation(kotlin("stdlib-jdk8"))
  }
}
```

The `macosX64` block defined the macOS shared library target. Rename it to
`mingwX64` for Windows, and `linuxX64` for Linux. Find more explanations on that
[in the tutorial](https://kotlinlang.org/docs/tutorials/native/dynamic-libraries.html)
for Kotlin/Native. We use [a script](https://twitter.com/jonnyzzz/status/1206242931058892802?s=20)
in the example repository to avoid manual configuration need.

We use the Kotlin/Native's `cinterop` tool to import the `jni.h` declarations to Kotlin, 
e.g  `JNIEnv` or `jint` symbols. The whole script looks like that:
```
  macosX64("native") { // use linuxX64 or mingwX64 on other OS
    binaries {
      sharedLib()
    }

    compilations["main"].cinterops.create("jni") {
      val javaHome = File(System.getProperty("java.home")!!)
      packageName = "org.jonnyzzz.jni"
      includeDirs(
              Callable { File(javaHome, "include") },
              Callable { File(javaHome, "include/darwin") },
              Callable { File(javaHome, "include/linux") },
              Callable { File(javaHome, "include/win32") }
      )
    }
  }
```

The `src/nativeInterop/cinterop/jni.def` file contains the definitions for the c interop, 
it should container the only one line to instruct the interop tool what headers to use: 
```
headers = jni.h
```

## Putting all Together

The example is ready. We use Kotlin/JVM to talk to Kotlin/Native in the same project.
The project sources are [on my GitHub](https://github.com/jonnyzzz/kotlin-jni-mix), 
try it, open in IntelliJ and have fun.  

You'll have the following code in the console:
```
➜  kotlin-jni-mix git:(master) ✗ ./gradlew run

> Configure project :
Kotlin Multiplatform Projects are an experimental feature.

> Task :linkDebugSharedNative
Produced library API in libkotlin_jni_mix_api.h

> Task :linkReleaseSharedNative
Produced library API in libkotlin_jni_mix_api.h

> Task :run
Native function is executed with: 42
ret from the native: 43
```