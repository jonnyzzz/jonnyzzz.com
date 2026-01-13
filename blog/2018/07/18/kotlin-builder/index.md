# Java Builders with Kotlin

**Date:** July 18, 2018  
**Author:** Eugene Petrenko  
**Tags:** kotlin, java, builder, dsl

---

A higher order function to simplify Java builders usage


I was working with [auth0](https://auth0.com/)'s [java library](https://github.com/auth0/java-jwt)
to issue and verify [JWT](https://tools.ietf.org/html/rfc7519) tokens. The library
is [easy to use and pretty strait-forward](https://twitter.com/jonnyzzz/status/1016575537257607168).
At some point, I had a Kotlin code to issue a JWT token: 

{% highlight kotlin %}{% raw %}
var builder = JWT
       .create()
       .withIssuer(ISSUER)

val userId = principal.userId
if (userId != null) {
  builder = builder.withClaim("userId", userId)
}

val serviceId = principal.serviceId
if (serviceId != null) {
  builder = builder.withClaim("serviceId", serviceId)
}

return builder.sign(algorithm())
{% endraw %}{% endhighlight %}


The code is trivial. I create a new JWT token and fill claims with some data.
I put a claim only if a respective data is not `null`. 
The code above is long and hard to read. Typically, one writes it with a copy-paste
approach. I'm not an exception here too. I even did a typoe copying 
things: `"userId"` is used twice:

<blockquote class="twitter-tweet" data-conversation="none" data-lang="en"><p lang="en" dir="ltr">And that I had before <a href="https://t.co/2grxbvpKnP">pic.twitter.com/2grxbvpKnP</a></p>&mdash; Eugene Petrenko (@jonnyzzz) <a href="https://twitter.com/jonnyzzz/status/1016602927102820352?ref_src=twsrc%5Etfw">July 10, 2018</a></blockquote>
<script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>

# Immutability 

The best programs, so far, are immutable programs. Let's make the `builder` variable immutable.
Here is the trick I like in Kotlin. Usually, a builder function returns a builder instance, e.g.
{% highlight kotlin %}{% raw %}
  fun withSomething(x: Something) : Builder { ... }
{% endraw %}{% endhighlight %}

You never know, if a returned `Builder` is the same as the `Builder` you call a `with*()` 
method on. As of `Builder` implementation, it is hard to return a new instance of a
builder every time. People tend
to `return this` from builder functions, it is just easier and does not require tricks.

I see the dilemma here. Do we assume the `Builder` is mutable or not? 

Kotlin [data classes](https://kotlinlang.org/docs/reference/data-classes.html) and `copy(...)` function
makes it easier, no you know it. 

## Mutable Builder

Let's assume the `Builder` returns `this` from `with*(...)` methods.
And trivially, we may turn the `builder` variable to be immutable 
and call `with*(...)` methods:
  
{% highlight kotlin %}{% raw %}
...
if (userId != null) {
  builder.withClaim("userId", userId)
}
...
{% endraw %}{% endhighlight %}

 
I do not like that assumption. A sudden change of the builder 
implementation will introduce a hard to find a bug in the code.


## Immutable or Mutable Builder 

Now, let's assume we have no assumptions on `Builder` implementation. It is 
allowed and not forced to return same `this` from a `with*()` functions. We still need either 
a mutable variable `builder` or a longer expression.

## Expression and Extension Functions

But, here we need a function call that takes `Builder` as the receiver, 
aka [extension function](https://kotlinlang.org/docs/reference/extensions.html),
and the function should check and call something in the builder.

I created the following function: 

{% highlight kotlin %}{% raw %}
fun <B : Any, Y : Any> B.withX(obj: Y?, ƒ: B.(Y) -> B): B
        = if (obj != null) ƒ(obj) else this
{% endraw %}{% endhighlight %}

That one allows me to turn the whole method into:

{% highlight kotlin %}{% raw %}
    return JWT.create()
            .withIssuer(ISSUER)
            .withX(principal.userId) { withClaim("userId", it)}
            .withX(principal.serviceId) { withClaim("serviceId", it) }
            .sign(algorithm())
{% endraw %}{% endhighlight %}

I like that one. It is shorted and read better!

## Reflection and Callable References

I got the question from my friend on Twitter
> Is it possible to get rid of strings, too?

<blockquote class="twitter-tweet" data-lang="en"><p lang="en" dir="ltr">Is it possible to get rid of strings, too?</p>&mdash; Eugeny Schepotiev (@zeckson) <a href="https://twitter.com/zeckson/status/1016965146424426496?ref_src=twsrc%5Etfw">July 11, 2018</a></blockquote>
<script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>

It is possible, for that, you use
[property references](https://kotlinlang.org/docs/reference/reflection.html#property-references)
and [KProperty](https://kotlinlang.org/api/latest/jvm/stdlib/kotlin.reflect/-k-property/index.html)
to grab property name at the runtime:

{% highlight kotlin %}{% raw %}
fun Builder.withClaim(p: KProperty0<String?>): Builder
        = p.getter()?.let { withClaim(p.name, it) } ?: this

return JWT.create()
        .withIssuer(ISSUER)
        .withClaim(principal::userId)
        .withClaim(principal::serviceId)
        .sign(algorithm())
        
{% endraw %}{% endhighlight %}

Here I use `principal::userId` and `principal::serviceId` to pass both the property name 
and the function to get the property value. It makes the code shorter.
We do not have the explicit names anymore. 

One should understand the *risk*. A sudden
refactoring and rename of `userId` or `serviceId` properties of the `principal` class 
will change the names we use in the builder. It may
cause trouble on a production. Several unit 
tests (or integration tests) will help to preserve the API. 

The same trick with [callable references](https://kotlinlang.org/docs/reference/reflection.html#callable-references)
works for functions too. You might check the whole documentation page on
[reflection in Kotlin](https://kotlinlang.org/docs/reference/reflection.html).

I checked, and it is not required (at least with Kotlin/JVM v1.2.51) to have `kotlin-reflect` library to make the example above
work.