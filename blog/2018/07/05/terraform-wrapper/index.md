# Terraform Wrapper

**Date:** July 05, 2018  
**Author:** Eugene Petrenko  
**Tags:** terraform, devops, aws, docker

---

Use Terraform without install


It is always a problem to have the right tools installed. Right versions often mean the
versions specific to a given project or branch. What if you need several at a time? 

I like to zero-configuration approach, where one does not change the global state
of the machine. And it plays nicely if you have several working machines too!

Here is what I do to use Terraform in `bash`, tested on macOS:

{% highlight bash %}{% raw %}

#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TERRAFORM_ROOT="$(cd "$DIR" && cd .. && pwd)"
AWS_ROOT="$(cd ~/.aws && pwd)"
TERRAFORM_VERSION=0.11.7

docker run \
          --rm \
          -it \
          --dns $(dig +short <YOUR DNS> | tail -1) \
          --volume "$TERRAFORM_ROOT:$TERRAFORM_ROOT" \
          --volume "$AWS_ROOT:/root/.aws:ro" \
          --workdir "$(pwd)"  \
          hashicorp/terraform:${TERRAFORM_VERSION} $*

{% endraw %}{% endhighlight %}


I code Terraform scripts in 
[IntelliJ IDEA](https://jetbrains.com/idea) with 
the amazing plugin done by a friend of mine: 
[Terraform Support plugin](https://plugins.jetbrains.com/plugin/7808-hashicorp-terraform--hcl-language-support)
.