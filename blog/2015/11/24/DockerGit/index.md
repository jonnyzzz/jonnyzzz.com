# Git in Docker

**Date:** November 24, 2015  
**Author:** Eugene Petrenko  
**Tags:** docker, git, integration tests, ci

---

Some uses [Docker](https://docker.com) to run builds inside.
 
 
Some uses it to run tests inside. 
Today I gonna cover my case, where I implement a command that runs inside a Docker container 
and call it thousands of times during [CI](https://en.wikipedia.org/wiki/Continuous_integration) 
integration tests build. 

Problem Statement
-----------------
A project I work on uses [Git client](http://git-scm.com). 
There are a number of Git client 
version available. My need was to create integration tests 
to make sure project works with a given Git client versions. 

Tests has to be implemented for Windows and Linux. Popular Git client 
versions should be covered.
For Windows I simply download binaries.
For Linux this did not worked well. Too tricky to use public packages. 
Let's compile Git from sources. 


Building Git Client
-------------------
Git client is easy to checkout and compile. I use the following
snippet for that

{% highlight bash %}{% raw %}
  
git_version=<a version of Git client to use>
git_sources="/gitz/src/git-${git_version}"
git_bin="/gitz/bin/git-${git_version}"
git_sh="/git-${git_version}.sh"

mkdir -p ${git_sources}
mkdir -p ${git_bin}

wget -O ${git_sources}/git.tar.gz https://www.kernel.org/pub/software/scm/git/git-${git_version}.tar.gz
tar xzf ${git_sources}/git.tar.gz -C ${git_sources}

pushd ${git_sources}/git-${git_version}
make prefix=${git_bin} all && make prefix=${git_bin} install
popd

echo '#!/bin/bash' > ${git_sh}
echo "GIT_EXEC_PATH=${git_bin}/libexec/git-core PATH=${git_bin}/bin:\$PATH GITPERLLIB=${git_bin}/perl/blib/lib ${git_bin}/bin/git \"\$@\"" > ${git_sh}
chmod a+rx ${git_sh}

{% endraw %}
{% endhighlight %}

The code above generates a starter script for Git client (e.g. `/git-1.7.2.sh`) 

Git build also requires a set of packages to be installed on the OS (for my case on CentOS) 

{% highlight bash %}
{% raw %}

yum update -y
yum groupinstall -y "Development tools"
yum install -y tar wget m4
yum install -y autoconf
yum install -y gcc
yum install -y perl-ExtUtils-MakeMaker
yum install -y curl-devel expat-devel gettext-devel openssl-devel zlib-devel
yum clean all

{% endraw %}
{% endhighlight %}

Well, building Git client

* takes time
* resources waste to re-build
* requires 
  * OS package install permissions    
    => (aka `root` access to build machine),    
    or
  * pre-configured CI build machines   
    => (aka eternal pain to update machine packages)

How can we re-use Git binaries and have Git client available with no
extra packages, build machined pre-configuration and other maintenance 
activities? 

Build Git Client in Docker Container
------------------------------------
What if I use Docker to build Git from binaries for all version I need?

Well, benefits of Docker image and process are

* isolation
* recoverable configuration
* no side-effects 
* no infrastructure maintenance costs
* repeatable configuration
* the only one requirement to have Docker installed on the CI machine
* nearly no root access required (effectively Docker command means root access)
* no dependency on CI machine packages / environment
* binaries re-use via Docker image

I created a `Dockerfile` where I compile selected versions of Git client 
from sources and prepare bootstrap scripts (as shown above). All building 
tasks were put in one `RUN` command to avoid too many 
[layers](https://github.com/docker/docker/issues/1171).

The Docker image I build is only updated to include new version of Git client.
This is done quite rarely. The only requirement for CI machine is Docker. 

Now in my CI builds I can start a Docker container form a pre-built image 
with required Git client version. This is the way to run repeatable
integration tests. 

But, now I need to make my tests run inside the same container. This 
is complicated...  
and there are some packages were (not yet) installed in the container...

Calling Docker Container from a Script
------------------------------------
The only requirement from integration tests is to have `git` command of given version in `PATH`.
Let's wrap Docker container call into a bash script than!

First of I created a script like that (see [docker run docs](https://docs.docker.com/engine/reference/run/))

{% highlight bash %}
{% raw %}

docker run GIT_CLIENT_IMAGES $@

{% endraw %}
{% endhighlight %}

Well, it did not work, so I added volume with current directory: `-v $(pwd):/$(pwd)` and switched working 
directory in Docker to it via `-w /$(pwd)`.  
NOTE. This will not work if our `git` command is executed from non repository checkout root.

Included `--rm` to avoid garbage from finished containers. 

Added `-i` to have the command run interactively.

The only issue now was that all files changed or created in container were owned by root
(because in Docker container I was running it under root and owners and permissions are transparent here)

There are two solutions for that

* run `chown` after each call 
* use same user in container

Running `chown` is at least starting another process, dealing with exit codes and errors. I preferred 
the second option. The _same user_ means a user that has same [UID](https://en.wikipedia.org/wiki/User_identifier) 
and [GID](https://en.wikipedia.org/wiki/Group_identifier). 
I added `-u $(id -u):$(id -g)` arguments. 

Finally, I implemented version selector as environment variable. There are also a number 
of [Git specific environment variables](https://git-scm.com/book/en/v2/Git-Internals-Environment-Variables)
that are to be sent to the container. This is done via `--env` arguments of Docker run command.

Now I have 

* a pre-built Docker image with all Git clients
* a script that pretends to be `git` command and delegates calls into a Docker container

Having one dependency is better that having two. Let's put it all together...

Putting all together
--------------------
It's clear the start script depends on container. I put the script inside container. 
Default container command prints the `git` script to STDOUT. 

The Git client setup bash script turned to be as follows:

{% highlight bash %}
{% raw %}

docker pull GIT_CLIENT_IMAGE
docker run --rm GIT_CLIENT_IMAGE 2>/dev/null >git
chmod +x git
PATH=$(pwd)/git:$PATH
export PATH

GIT_VERSION=<a version of Git client to use>
export GIT_VERSION

#call integration tests
{% endraw %}
{% endhighlight %}

Wrapping Up
-----------

* Host-OS independent way to run integration tests with different Git client versions. 
* It builds each Git client version only once. 
* Integration tests environment is not polluted with Git client build dependencies.
* Can easily switch Linux distributive
* Minimum overhead
* Constant time Git client switch

How it finally works. Custom `git` script is added to `PATH`. 
For every call the script starts a fresh Docker container to perform
the call. Git client of specified version is executed in it.
STD streams and signals are bound transparently.
Container is terminated and disposed at the end. 
Integration tests calls `git` command hundreds times.


Real Life
---------
I implemented the following infrastructure for my project. I use in-house 
Docker registry to host latest Git clients image. It uses default Linux build machine
image and it does not require specific permissions or packages, but Docker. 

Initial implementation was done in beginning of 2015, in the blog post I omitted 
some implementation details that are now seems to be done easier. 

Currently I run tests for up to 10 versions of Git client. My observations 
shows the slowdown about 2x in comparison with fully native Git client on Linux.
Frankly, I have not yet tried to optimize performance of my scripts.

Containerize with Pleasure!