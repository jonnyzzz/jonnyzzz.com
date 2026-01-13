# A Kotlin Coroutine for an OutputStream Filtering

**Date:** June 21, 2017  
**Author:** Eugene Petrenko  
**Tags:** kotlin, coroutine

---

Kotlin coroutines for OutputStream.

In this post, we consider a low-level implementation for specific 
coroutines that are used to process streams in a server-side Java application. 
There is an existing code that writes the output to a given `OutputStream` object. 
One may write it in Java as:

{% highlight java %}{% raw %}
interface ExistingService {
  void callExistingCode(OutputStream resultOutput)
}
{% endraw %}{% endhighlight %}

We need to intercept the output that is bing written by the `#callExistingCode` function. 

Example
=======
Say the `ExistingService` replies with an HTML, and the goal is to extract some part of it, say a `<div>`
with a given `id`.
Or an `ExistingService` may be returning a ZIP archive, and the goal can be to add a file in it.

There are many similar cases, where an `OutputStream` post processing can be necessary.

Problem Statement
=================
Suppose the `ExistingService` writes output in the following format:

{% highlight text %}{% raw %}
(<SIZE><CHANNEL-ID><DATA>)*
{% endraw %}{% endhighlight %}

Where `<SIZE>` is 4 bytes length message. `<CHANNEL-ID>` is a one-byte message. `<DATA>` is a 
byte sequence of given size.

The such or similar format is widely used to send several streams within one connection. For example,
it is used in [SSH-2](https://www.ietf.org/rfc/rfc4251.txt), [HTTP/2](https://tools.ietf.org/html/rfc7540)
or [Git](https://github.com/git/git/blob/master/Documentation/technical/pack-protocol.txt).

Out goal is to include additional messages to the stream on the fly, while it is being generated 
by the call to an `ExistingService`.
We just need to implement the method:

{% highlight java %}{% raw %}
OutputStream weaveStream(OutputStream target);
{% endraw %}{% endhighlight %}

A Trivial Java Implementation
=============================

In Java we have `PipedOutputStream`/`PipedInputStream` classes that may turn an OutputStream 
into an `InputStream`. Next, the processing can be done easily. 

We have a thread, that reads data from an `InputStream`, e.g. 
{% highlight java %}{% raw %}
OutputStream weaveStream(OutputStream target) throws IOException {
  PipedOutputStream pos = new PipeOutputStream();
  PipedInputStream pis = new PipedInputStream(pos);
  
  runInThread(() -> weaveStream(pis, target));
  return pos;
}

void weaveStream(InputStream source, OutputStream target) throws IOException {
    while (true) {
      //omitted error processing here
      int size = extractSize(source.read(), source.read(), source.read(), source.read());
      if (isLastBlock(size)) return;

      int ch = extractChannelId(source.read());

      writeHeader(target, size, ch);
      copyBlock(target, size, source);
    }
}
{% endraw %}{% endhighlight %}

The cost here is high. We need an additional thread to implement that. Additionally, 
the whole data is copied to a buffer from which a `PipedInputStream` is reading. 
Finally, piped streams implementation uses a level of synchronization to wait for 
next data portion to arrive. That can be problematic for some loads. 

A Smart Java Implementation
===========================

One can do a smarter implementation. Directly implement the `OutputStream` and do the processing
and patching the output in there. 

What we do here is to add a state to our `OutputStream` implementation. Each call to `write` method
yields an update of the state. 

A *State Machine*. That is what the code from here is about. It is up to programmer if to have a state
explicitly or not. Think about maintainability of such code first. 

The implementation here can be quite complex. As an example, I show a byte-by-byte 
processing. In real cases, it can be way more efficient to implement 
`write(byte[], int, int)` method.

{% highlight java %}{% raw %}
OutputStream weaveStream(OutputStream target) throws IOException {
  return new OutputStream() {
    @Override
    public void write(int b) throws IOException {
      if (isReadingSize()) {
       readMoreSize(b); 
      } else if (isReadingChannelId()) {
        readMoreChannelId(b);
      } else if (isProcessingData()) {
        processModeData(b);
      } else {
        throw new IOException("Unexpected state");
      }
    }
  };
}
{% endraw %}{% endhighlight %}

The benefit here is that we no longer need an extra thread to pipe the output as input. Sill, code 
is getting more complex. 

A Coroutine State Machine
=========================

In Kotlin 1.1 we have [coroutines](http://kotlinlang.org/docs/reference/coroutines.html). The alternative way 
to implement a state machine with the help of compiler, with way more readable, linear-looking code.

First, we need to declare an interface with `suspend` functions, e.g.

{% highlight java %}{% raw %}
interface DataReader {
  suspend fun read() : Int
  
  suspend fun pipe(sz : Int, to: OutputStream)
}
{% endraw %}{% endhighlight %}

Also, we need an implementation of the `OutputStream` that allows us to use the `DataReader`. That is 
the function `inverseRead`. We'll turn back to the implementation a bit later.

{% highlight java %}{% raw %}
fun inverseRead(reader: suspend DataReader.() -> Unit) : OutputStream { ... }
{% endraw %}{% endhighlight %}

Finally, we are able to implement the data processing:
{% highlight java %}{% raw %}
fun weaveStream(target: OutputStream): OutputStream {
  return inverseRead { reader ->
    readStream(reader, target)
  }
}

suspend fun readStream(source: DataReader, target: OutputStream) {
  while(true) {
    val sz = extractSize(source.read(), source.read(), source.read(), source.read())

    if (isLastBlock(sz)) return
    val ch = extractChannelId(source.read())

    writeHeader(target, sz, ch)
    source.pipe(sz, target)
  }
}
{% endraw %}{% endhighlight %}

Check the code above. It is quite similar to what we had in _A Trivial Java Implementation_. The difference
is huge. Every call to `suspend` function pauses the execution of a method, so the execution turns to
the `write` method implementation of `OutputStream` in `inverseRead`. We are able now to write
a linear looking code, that is executed in a piece-by-piece manner.

Implementation of the Coroutine
===============================

The only missing part is the `inverseRead`. We follow the [coroutines documentation](http://kotlinlang.org/docs/reference/coroutines.html)
to implement that. Great is there are many examples too.

We implement `DataReader#read` and `DataReader#pipe` functions to suspend execution until there is enough data
send to `OutputStream#write` method. We have the following state object for that:

{% highlight kotlin %}{% raw %}
class DataReaderState {
  var readByteContinuation = null as Continuation<Int>?

  var pipeContinuation = null as Continuation<Unit>?
  var pipeTarget = null as OutputStream?
  var pipeSizeToWrite = 0
}
{% endraw %}{% endhighlight %}

Next, we are able to implement the `DataReader` interface in the following way:

{% highlight kotlin %}{% raw %}
class DataReaderImpl(val state: DataReaderState) : DataReader {
  suspend override fun pipe(sz: Int, to: OutputStream): Unit = suspendCoroutine<Unit> { c ->
    state.pipeContinuation = c
    state.pipeSizeToWrite = sz
    state.pipeTarget = to
  }

  suspend override fun read(): Int = suspendCoroutine { c ->
    state.readByteContinuation = c
  }
}
{% endraw %}{% endhighlight %}

All we have here is a call to the specific `suspendCoroutine` function in Kotlin, which does the suspend. I decided
to omit for simplicity a defensive asserts that one may have in both `pipe` and `read` function implementation.  

The `OutputStream` implementation in the example is executing next suspended function in a loop. The current
implementation does not check the state at the end of data too. The straightforward implementation is as follows:

{% highlight kotlin %}{% raw %}
class DataReaderOutputStreamImpl(val state: DataReaderState) : OutputStream() {
  override fun write(b: Int) = write(byteArrayOf(b.toByte()))

  override tailrec fun write(b: ByteArray, off: Int, len: Int) {
    if (len <= 0) return

    val readOneByte = state.readByteContinuation
    if (readOneByte != null) {
      readOneByte.resume(b[off].toInt())
      return write(b, off+1, len-1)
    }

    val pipe = state.pipeContinuation
    if (pipe != null) {
      val toPipe = Math.min(len, state.pipeSizeToWrite)
      state.pipeTarget!!.write(b, off, toPipe)
      return write(b, off+toPipe, len - toPipe)
    }

    throw Error("Illegal state")
  }
}
{% endraw %}{% endhighlight %}

At that moment we are ready to implement the `inverseRead` function.

{% highlight kotlin %}{% raw %}
fun inverseRead(reader: suspend (DataReader) -> Unit) : OutputStream {
  val state = DataReaderState()
  val outputStream = DataReaderOutputStreamImpl(state)
  val dataReader = DataReaderImpl(state)
  val continuation = DataReaderContinuation(state)

  reader.createCoroutine(dataReader,continuation).resume(Unit)
  return outputStream
}
{% endraw %}{% endhighlight %}

Coroutine vs State Machine
==========================

It turned out we still needed to implement a state machine (via `DataReaderState` class). It 
was necessary to add a state for each `suspend` function of `DataReader` interface. That was 
the code we need to write as building block (and there 
are [amazing libraries](https://github.com/Kotlin/kotlinx.coroutines) for most 
of the cases)

The good part is that the rest part of the code, where we do the actual data decoding (the `readStream` function)
now free from an explicit state machine style programming. One can have code written as easy
as possible. It's easier to understand and to check. And, for example, we may use loops, try-catches 
and any other code constructs we like using for ordinary programs. 

In other words, with the help of Kotlin suspend functions we may minimize the number of complex functions and
concentrate on the actual development.

For more information on coroutines power in Kotlin, you may refer to 
[GeekOut Talk by Roman Elizarov](https://vimeo.com/221264980/b3ac7f9001)
or to [the documentation](http://kotlinlang.org/docs/reference/coroutines.html)