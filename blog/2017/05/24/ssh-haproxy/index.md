# Load Balancing SSH

**Date:** May 24, 2017  
**Author:** Eugene Petrenko  
**Tags:** ssh, haproxy, tcp, service, cloud, glb, load-balance

---

More SSH servers behind the same hostname

Say you have an SSH server on your premises. And say you have a huge load on that service. 

Example? Sure. Git repository. Any git 'server' is such a use-case. 

SSH backgrounds
===============

SSH acronym means `The Secure Shell`. More precisely, we'll be talking about SSH2 protocol, which is
a de-facto standard. This protocol is covered by the [RFC 4253](https://tools.ietf.org/html/rfc4253).

Barely (as simply as possible), the connection is done as follows. A client opens new TCP connection 
to the server. It checks server public key(s) (using the `known_hosts` file). Then server 
and client do key exchange, authentication and open channels to run commands or 
interactive sessions. 

More precisely, SSH protocol runs on top of TCP connection. This protocol is secure. We need 
to load balance TCP connections, aka [L4](https://en.wikipedia.org/wiki/OSI_model) level 
load balancing.

DNS Load Balancing
======================

We need to have several SSH server running. All IP addresses are registered in the DNS for the 
same hostname. The [DNS round-robin](https://en.wikipedia.org/wiki/Round-robin_DNS) will make
it play as load balancing. 

The problem here is in the DNS update latency. DNS is cached all over the place. And we 
are not able to have more (or less) servers fast. In practice, it may take days to propagate
the update.

Also, this approach requires as much IP addresses as we have SSH servers.  

HAProxy Approach
================

There are many balances, we consider [HAProxy](http://www.haproxy.org/) 
for [L4](https://www.quora.com/What-is-the-difference-between-layer-3-and-layer-4-load-balancing-Why-is-layer-7-LB-used-inspite-of-its-drawbacks-of-being-a-bottleneck)

The configuration is quite simple. 
{% highlight text %}{% raw %}

listen ssh 0.0.0.0:{{ app.ports.ssh.active }}
    mode tcp

    server <SERVER_NAME_1> <SERVER_HOST_1>:<SERVER_PORT_1> weight <WEIGHT_1>
    server <SERVER_NAME_2> <SERVER_HOST_2>:<SERVER_PORT_2> weight <WEIGHT_2>
    ...
    server <SERVER_NAME_N> <SERVER_HOST_N>:<SERVER_PORT_N> weight <WEIGHT_N>

{% endraw %}{% endhighlight %}

This configuration is enough to make HAProxy run in the L4 mode to route traffic from the main service IP(s)
to all backends. 

Running several HAProxy instances behind different IP addresses is possible for redundancy and throughput.

SSH Server Server Keys
=======================

It is necessary to have same server keys on all `SERVERN_1` ... `SERVER_N` family, otherwise an SSH client 
will warn a possible MIIM attach, as client likely to access any SSH server from the same IP. And the `known_hosts`
file stores server public key info for each known IP.

TCP Balancing Issues: Request IP
=================================

There are several differences between an HTTP-level (L7) balancing and TCP-level balancing. You are not able
to send request IP address that easy as via HTTP. The protocol is only about streams. There is no notion of headers,
where one is able to pass extra data, e.g. as in HTTP with `X-Forwarded-For`.

There is no solution in general, but one can use [HAProxy PROXY protocol](http://www.haproxy.org/download/1.8/doc/proxy-protocol.txt).
That is an extension to any TCP protocol that blindly sends a specific string with request/response information to the 
server. One has to have a server, supporting PROXY protocol on the other end. 

The PROXY protocol is used in a number of places and services, e.g. AWS ELB, HAProxy, Nginx, and much mode. 

Bad news. Open SSH server implementation does not support it out of the box, but one may apply patches to support that.
I created and shared patches for [Apache Mina SSHD](https://issues.apache.org/jira/browse/SSHD-656) library.

To enable the support, add `send-proxy` each server line. You may replace the line
{% highlight text %}{% raw %}
     server <SERVER_NAME_N> <SERVER_HOST_N>:<SERVER_PORT_N> check weight <WEIGHT_N>
{% endraw %}{% endhighlight %}

with
{% highlight text %}{% raw %}
     server <SERVER_NAME_N> <SERVER_HOST_N>:<SERVER_PORT_N> send-proxy weight <WEIGHT_N>
{% endraw %}{% endhighlight %}


Health Checks
==============

HAProxy supports automated health checks on TCP level. Ones a backend server is not able to reply on checks, 
the traffic is no longer send to an unhealthy host. 

I use the following configuration for that `tcp-check expect string SSH-2.0-`. The option instructs HAProxy
to run checks and to check if the remote end replies with a string that starts with `SSH-2.0-`. Such answer is 
the standard message required by the SSH2 protocol.

Overall we have the following configuration:
{% highlight text %}{% raw %}

listen ssh 0.0.0.0:{{ app.ports.ssh.active }}
    mode tcp
    
    tcp-check expect string SSH-2.0-

    ...
    server <SERVER_NAME_i> <SERVER_HOST_i>:<SERVER_PORT_i> check weight <WEIGHT_1>

{% endraw %}{% endhighlight %}

Usages
======

We use this approach mainly to implement
[Green-Blue deployments](https://martinfowler.com/bliki/BlueGreenDeployment.html). We route traffic 
to the active host. We can change the configuration dynamically or even have custom weights to implement A/B tests. 

An alternative is to use DNS. But with DNS you never know how much time will it take for client's and chain
of DNS servers to propagate the change. In the real world, it looks the best to combine DNS as more slow
and static entry level balancing. Next to use HAProxy (or similar) balancing to implement fast configuration
changes on the fly. 

Conclusion
==========

I showed how to easily load-balance SSH servers for fun and profit. Hope this helps you to 
build a highly available system.