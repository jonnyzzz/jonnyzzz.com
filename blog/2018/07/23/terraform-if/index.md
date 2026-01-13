# Condition in Terraform and API Gateway

**Date:** July 23, 2018  
**Author:** Eugene Petrenko  
**Tags:** terraform, aws, api gateway, cloud, infrastructure

---

Create an AWS API Gateway resource based on conditions

You may know [Terraform](https://www.terraform.io/), the tool to create infrastructure
as a code. I use it for several [AWS](https://aws.amazon.com/) experiments, I do. 
It is declarative and uses HCL language to declare resources to create. Let's see how
one can create resources based on a condition.

## Introduction 

I wrote scripts to create [API Gateway](https://aws.amazon.com/api-gateway/) for my project.
The API Gateway service is tricky, and in Terraform one uses several resources to make it work.

You start with adding the
[aws_api_gateway_api](https://www.terraform.io/docs/providers/aws/r/api_gateway_rest_api.html)
resource, which defines the API Gateway itself. Handler paths are represented 
as a [tree structure](https://en.wikipedia.org/wiki/Tree_(data_structure)). The root of the 
tree matches to the empty path. The root node ID is returned from the `root_resource_id` output
parameter of the `aws_api_gateway_api` resource. 

I use Terraform [Modules](https://www.terraform.io/docs/modules/usage.html) in my scripts
to reduce complexity. Modules are the same as functions in other programming languages. 
It helps to reuse code and reduce duplicates. 

## The Need of a Condition 

I have a module to define API Gateway handlers. That module accepts a handler path and the 
`root_resource_id` parameter. In the module, I have to decide either
to create new resource 
[aws_api_gateway_resource](https://www.terraform.io/docs/providers/aws/r/api_gateway_resource.html),
for non-empty path, or to use the base `root_resource_id` instead, for the empty one.

In a pseudo-code the problem looks as follows:

{% highlight kotlin %}{% raw %}
  if (root_path == "") {
    root_resource_id
  } else { 
    (resource "aws_api_gateway_resource").id
  }
{% endraw %}{% endhighlight %}

## A Condition Implementation

I head that story from my friend Mikhail Kuzmin several years ago. I have no idea,
how I recalled that, but still. He told me something about the `count` parameter is helpful
to implement a condition in Terraform. 

Also, I found that in Terraform we have 
[ternary operator expression](https://www.terraform.io/docs/configuration/interpolation.html#conditionals),
aka `condition ? foo : bar`, which helps me to extract the right resource ID at the end.

The overall condition for a resource did not look trivial. I decided to extract it as a dedicated module
from the very beginning. That is what I created:

{% highlight text %}{% raw %}
variable "api_gateway_id" {}
variable "parent_resource_id" {}

variable "path_part" {
  description = "Resource path or empty string to use parent_resource_id"
}

resource "aws_api_gateway_resource" "handler" {
  parent_id   = "${var.parent_resource_id}"
  rest_api_id = "${var.api_gateway_id}"

  path_part   = "${var.path_part}"

  count       = "${var.path_part == "" ? 0 : 1 }"
}

output "handler_id" {
  value = "${
    var.path_part == ""
    ? var.parent_resource_id
    : element(concat(aws_api_gateway_resource.handler.*.id, list("")),0)
  }"
}

{% endraw %}{% endhighlight %}

I do several tricks in that module. The first trick is to set `count` for `aws_api_gateway_resource`
to zero when I need no resource created. Otherwise, I put `count = 1`, which is the default.

The second trick is in the `hardler_id` output parameters. I select
either the created ID or the `parent_resource_id` parameter. 

## Ternary Expression and Complexity

You may want to ask, why is it so complicated, me too. I started with the more 
trivial variant of the second condition: 

{% highlight text %}{% raw %}
output "handler_id" {
  value = "${
    var.path_part == ""
    ? var.parent_resource_id
    : element(aws_api_gateway_resource.handler.*.id,0)
  }"
}

{% endraw %}{% endhighlight %}

And then, I found out that Terraform computes both expressions in the ternary
expression. It differs from the semantics we got used from C-like languages. And so, 
I had to have a non-empty list in the second expression. I use the `concat` to 
join two lists, and `list("")` to create a new list with one element.
Finally, `concat(aws_api_gateway_resource.handler.*.id, list("")` does the trick 
making a list contain at least one element, even if the `count` was equal to `0`.

That is how I found the workable condition expression from the full example above.

## Avoiding Ternary Operator

I was speaking with a colleague on that, and realized, the code can be simplified. 
Instead of the conditional operator, 
now I join two lists and pick the first element:

{% highlight text %}{% raw %}
output "handler_id" {
  value = "${
    element(concat(aws_api_gateway_resource.handler.*.id, list(root_resource_id)), 0) 
  }"
}

{% endraw %}{% endhighlight %}

The `aws_api_gateway_resource.handler.*.id` gives me an empty list if `count = 0`.
That works the same way, but better and shorter. We have only one real condition in 
the code now.

## Recursive Creation

I got yet another crazy idea. What if I wish to support `long/path/to/create` in my module.
What shall I do? The idea was to call the same module recursively for all needed path parts
to build the resources tree.

I failed.

There are several problems, I came across. The first one. It is not possible to have a
`count` parameter on Terraform module usage.

https://github.com/hashicorp/terraform/issues/953

I tried to include the same module from itself. It turned out, Terraform does not
support such inclusion and starts an infinite resolution in `terraform init` call. 

What if I fix `source` attribute? 
It is not possible too. One is not allowed to use a non-constant expression for the `source` 
parameter of a module.

## Conclusion

I recalled and implemented the common pattern in Terraform to handle a conditional resources
creation and applied it for AWS API Gateway resources. It plays well for my project, 
and I hope it will help you too.

Note. It cost me hours of endless debugging. One needs to call
[api_gateway_deployment](https://www.terraform.io/docs/providers/aws/r/api_gateway_deployment.html)
after _any_ change in the API Gateway configuration is done. 
That is hard to code all dependencies in Terraform correctly for it. It is even harder
if you have modules around.

I code Terraform scripts in 
[IntelliJ IDEA](https://jetbrains.com/idea) with 
the fantastic plugin done by a friend of mine: 
[Terraform Support plugin](https://plugins.jetbrains.com/plugin/7808-hashicorp-terraform--hcl-language-support)