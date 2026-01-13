# Int ptr in Kotlin/Native

**Date:** January 14, 2019  
**Author:** Eugene Petrenko  
**Tags:** kotlin, kotlin/native, c

---

Passing int* to C from Kotlin/Native


Today, suddenly, a friend of mine gave me an easy question - how can one pass an int pointer 
to a C function from Kotlin/Native. To my shame, I did not have the answer.
Now I do

## The Short Answer

```kotlin
memScoped {
  val q = alloc<IntVar>()
  q.value = 123
  function_from_c(q.ptr)
}
```

## The Long Answer

We need several files for the demo project. We will
use [Gradle Multiplatform Project](https://kotlinlang.org/docs/reference/building-mpp-with-gradle.html)
with Kotlin 1.3.11 and IntelliJ IDEA. Yes, it will be enough to work with (!) Kotlin/Native

### C Interop

It's enough to create only a `file.def` file with C code inside (after `---` line):
```c

---
int function_from_c(int* x) {
  return *x = *x + 10;
}
```

The `cinterop` tool generates the following Kotlin code interop from it:
```kotlin
fun function_from_c(x: CValuesRef<IntVar>?): Int
```

Right here we have a question - how to create an object of `CValuesRef<IntVar>` type?  

### The Solution

- Use `CPointer<IntVar>`, which is subtype of `CValuesRef<IntVar>`
- Call the `.ptr` extension property on the `IntVar` to get a `CPointer<IntVar>` instance 
- Create a `IntVar` instance via the `alloc<T>` extension function on a `NativePlacement` instance 
- Get a `NativePlacement` instance from the `memScoped { ... }` block receiver
- Use the `.value` property on `IntVar` to get/set `Int` value   

Full code of the `main.kt` is as follows. Mind the imports from `kotlinx.cinterop`:
```kotlin
import file.function_from_c
import kotlinx.cinterop.IntVar
import kotlinx.cinterop.alloc
import kotlinx.cinterop.memScoped
import kotlinx.cinterop.ptr
import kotlinx.cinterop.value

fun main(args: Array<String>) {
  println("Hello!")
  memScoped {
    val q: IntVar = alloc<IntVar>()
    q.value = 123
    val z = function_from_c(q.ptr)
    println(z)        // return value, C int 
    println(q.value)  // updated int* from C
  }
}
``` 

### Gradle Project Setup

Let's create a demo project with Gradle for IntelliJ IDEA. You need an empty Gradle 
project to start. I called `gradle init` command from console to get it in a new folder
(it was Gradle 5.1 in my case).
As an alternative, you may create a project with `File | New | Project...` menu too.

Next, paste the following to the `build.gradle`:

```gradle
plugins {
  id 'org.jetbrains.kotlin.multiplatform' version '1.3.11'
}
kotlin {
  targets {
    /// use presets.mingwX64 for Windows
    /// use presets.linuxX64 for Linux
    fromPreset(presets.macosX64, 'native') {
      compilations.main {
        outputKinds 'executable'
        cinterops {
          myInterop {
            defFile project.file("src/native/file.def")
          }
        }
      }
    }
  }
  sourceSets {
    nativeMain {
      kotlin.srcDir('src/native')
    }
  }
}
```

Place the `main.kt` and `file.def` files into the `src/native` folder. Now you may open the project in IntelliJ IDEA
by pointing it to the `build.gradle` file (use Java 1.8 in the Gradle Import dialog).

I use [Kotlin Multiplatform Project](https://kotlinlang.org/docs/reference/building-mpp-with-gradle.html).
You may find in the demo sources
[on my GitHub](https://github.com/jonnyzzz/kotlin-native-demo/commit/2a3b1d09e1d38205278b83058c31b42fdc770004).

Take a look to the [C Interop](https://kotlinlang.org/docs/reference/native/c_interop.html) article
for more information on the Kotlin/Native interop with C.
An [Interop With C](https://kotlinlang.org/docs/tutorials/native/mapping-primitive-data-types-from-c.html)
tutorials are a good read to see how other types are mapped between C and Kotlin/Native.

Have fun!