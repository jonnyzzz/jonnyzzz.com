# Prefix or Null with Kotlin?

**Date:** January 31, 2021  
**Author:** Eugene Petrenko  
**Tags:** kotlin, java

---

Removing a prefix from a string, quite a common task, isn't it? 
Let's see how to mix with the `null`-safety in Kotlin for
clear, nicer and shorter code. 

Have a look at the following Kotlin code:

```kotlin
fun String.removePrefixOrNull(prefix: String) : String? = when {
    startsWith(prefix) -> substring(prefix.length)
    else -> null
}
```

This is an [extension function](https://kotlinlang.org/docs/reference/extensions.html).
One can use that as-if it's a member of a `String` class (but behind the
scenes it's an ordinary method that Kotlin compiler calls).

Usage is pretty easy:

```kotlin
"test 123".removePrefixOrNull("prefix") /// returns null
"test 123".removePrefixOrNull("test")   /// returns " 123"
```

The benefit could be in combining that with other operators, e.g.
```kotlin
arg.removePrefixOrNull("--text=")?.toLowerCase() ?: error("Incorrect param")
```

How would you process only a strings with a given prefix?
We may start with a Java solution:
```java
final List<String> result = new ArrayList<>();
for (String arg : args) {
    if (arg.startsWith(prefix)) {
        result.add(arg.substring(prefix.length()));
    }
}
```

The same we can do with Java Streams like that:

```java
args.stream()
    .filter(it -> it.startsWith(prefix))
    .map(it -> it.substring(prefix.length()))
    .collect(Collectors.toList());
```

Exactly the same code is possible in Kotlin:

```kotlin
args.stream()
    .filter { it.startsWith(prefix) }
    .map { it.substring(prefix.length) }
    .collect(Collectors.toList())
```

We can tune that a little more to make it more idiomatic,
moreover, we will use Kotlin operators on collections too.

```kotlin
args.filter { it.startsWith(prefix) }
    .map { it.substring(prefix.length) }
```

It is still too long and probably troublesome. I wish we could
have only open operator to cut the prefix and to keep only the
relevant strings. For example, we could do the following:

```java
args.stream()
    .map(it -> {
        if (it.startsWith(prefix)) {
            return it.substring(prefix.length());
        } else {
            return null;
        }
    })
    .filter(Objects::nonNull)
    .collect(Collectors.toList());
```

That is longer, quite similar to what we have in the very
first example. The same in Kotlin could look like that:

```kotlin
args.mapNotNull {
    if (it.startsWith(prefix)) {
        it.substring(prefix.length)
    } else {
        null
    }
}
```

The `mapNotNull` operator helps here much. We could also extract
the lambda into the dedicated function to make that shorter:

```kotlin
fun String.removePrefixOrNull(prefix: String) : String? = when {
    startsWith(prefix) -> substring(prefix.length)
    else -> null
}

args.mapNotNull { it.removePrefixOrNull(prefix) }
```

There are so many nice and elegant functions in Kotlin that
we could use to beautify and to shorten our code.
Let me know if you see or use something similar.