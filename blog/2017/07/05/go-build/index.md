# Building Go Project

**Date:** July 05, 2017  
**Author:** Eugene Petrenko  
**Tags:** shell, bash, ci, go, build

---

No Silver-Go-Bullet. Yet another ad-hoc build.

I was doing a small Go command line tool project. All the time I was starting Go codebase, I looking for 
the proper way to setup project and to build it. 

The right build to me is the build which is reproducible. Such build is likely to be isolated 
from a machine where you run it. Be it Linux, Mac or Windows. 
Also, the right build should have all dependencies fixed. Otherwise, we have merely no chances
to recreated it in the future. 

As the very first example, I decided to use the approach from [Consul Template](https://github.com/hashicorp/consul-template).
That time (May 2017) it was a `make` based build which was using the official Docker container to run.
It was great! I was able to kick-start the project and to focus on development. But, it was crazy slow. 
It took seconds to compile a tiny project. It was also unable to run on Windows.

I did research. Found several approaches to building Go with Gradle. I decided to try 
[Gogradle](https://github.com/gogradle/gogradle). Also, there is [gradle-golang-plugin](https://github.com/echocat/gradle-golang-plugin).
Overall, the story did not play well because some issues I came across. And again, the solution was heavy!

Isolation. Docker. Cool stuff. But, the best stuff, it to think Docker, and event avoid it. The Go itself 
is amazing in that sense. The go binaries have zero dependencies. And this means we are able to zero-copy
dependencies. 

Finally, I created the following script. A still waiting for something better, and easier to use.

{% highlight bash %}{% raw %}
#!/bin/bash

cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
set -e -x -u

GOVERSION=1.8.1

LOCAL_DIST="$(pwd)/dist"
LOCAL_GO_HOME="$LOCAL_DIST/go-$(uname)-$GOVERSION"
if [ ! -f $LOCAL_GO_HOME/bin/go ]; then
  GO_PKG=$LOCAL_DIST/go-pkg-$GOVERSION/go-binary.tar.gz
  GO_UNPACK=$LOCAL_DIST/go-pkg-$GOVERSION/unpack

  rm -rf   $GO_UNPACK || true
  mkdir -p $GO_UNPACK || true

  if [[ "$( uname )" =~ .*[Dd]arwin.* ]]; then
    curl -o $GO_PKG https://storage.googleapis.com/golang/go${GOVERSION}.darwin-amd64.tar.gz
  else
    curl -o $GO_PKG https://storage.googleapis.com/golang/go${GOVERSION}.linux-amd64.tar.gz
  fi

  tar -xf $GO_PKG -C $GO_UNPACK

  rm -rf $LOCAL_GO_HOME || true
  mkdir -p $LOCAL_GO_HOME || true
  mv $GO_UNPACK/go/** $LOCAL_GO_HOME/

  rm -f $GO_PKG
fi

PATH="$LOCAL_GO_HOME/bin:$PATH"
GOROOT=$LOCAL_GO_HOME
GOPATH=$(pwd)

export PATH
export GOROOT
export GOPATH
export CGO_ENABLED=0

if [[ "$(which go)" != "$LOCAL_GO_HOME/bin/go" ]]; then
  echo "Incorrect go binary is still used: $(which go)"
  exit 1
fi

if [[ ! "$(go version)" =~ "go${GOVERSION} " ]]; then
  echo "Failed to install required Go version. "
  exit 1
fi
{% endraw %}{% endhighlight %}


The script downloads Go binaries for Mac or Linux to a build folder. It does not update the folder if
there is Go already. 

You may find the actual version on GitHub. [https://github.com/jonnyzzz/go-build-script](https://github.com/jonnyzzz/go-build-script)
And let me know if you know the better way to Go.