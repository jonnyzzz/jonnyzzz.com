# IP Whitelist for WAF Rules and Security Groups

**Date:** April 29, 2019  
**Author:** Eugene Petrenko  
**Tags:** aws, waf, security-group, infrastructure, terraform, devops, clouds

---

Have you ever tried to set up CloudFront WAF rules and Security Groups
to allow access _only_ from specific IP
addresses? Having the list of these specific IP addresses coded only once. 
We'll see how to use [Terraform](https://www.terraform.io/)
to solve and to automate this task.
 
## The Application

We have a traditional application on [AWS](https://aws.amazon.com), where
a [CloudFront](https://aws.amazon.com/cloudfront/) distribution handles
the incoming traffic.
Behind it, we have static pages on
[S3](https://aws.amazon.com/s3) and API endpoints
behind [Application Load Balancer](https://aws.amazon.com/elasticloadbalancing/) (ALB).
We use [Terraform](https://www.terraform.io/) to manage
production and staging environments, `v0.11.11` in our case.

The project is new and not yet public.
We allow access to the project only from specific IP addresses of developers and offices.
We set up IP filtering at both
[Cloud Front](https://aws.amazon.com/cloudfront/) (WAF rules) and 
[Security Groups](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html)
levels, depending on the AWS entities. 

# IP Whitelist Module

Terraform [Module](https://www.terraform.io/docs/modules/index.html)
is the standard way to avoid code duplicates in the infrastructure code. 
I have the module called `ip-whitelist` (in the `ip-whitelist` folder) to
hold and export the list of whitelisted IPv4 addresses. It is used everywhere 
in the code instead to avoid hard-coded IP addresses (which are subject to change). 

Let's create a module that exports all IP addresses for the white list.
The following `.tf` file in `ip-whitelist` folder makes it:
```terraform
output "cidr" {
  value = [
    "1.2.3.4/32",
    "5.6.7.8/32",
    //...
  ]
}
```

# Security Groups

There are many entities, that we create in Terraform. There are
several places in an infrastructure, where one uses security 
groups. Let's follow an easy strategy:
 - create a unique security group per usage
 - do not duplicate code

Both statements of the strategy comes from the programming background.
The fewer dependencies between modules one has, the easier it will be to update
or refactor the scripts in the future. We tend to extract common parts of
our programs to avoid duplicates and improve maintainability of the code.

What is the common part of all of those AWS service? Yes, 
[Security Groups](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html).
There are Security Groups in a [VPC](https://aws.amazon.com/vpc/) and without a VPC.
In both we'd like to reuse the same IP addresses filter list.
Security Groups are easy to create with the module above, for example with the following code
The module is easy to call from other places of the project:

```terraform
module "ip-whitelist" {
  source = "<relative path to module>ip-whitelist"
}

resource "aws_security_group" "name" {
  ingress {
    from_port = 22
    to_port   = 22
    protocol  = "tcp"
    cidr_blocks = ["${module.ip-whitelist.cidr}"]
  }
  //...
}
```

Let's switch to the Cloud Front, where WAF rules are used to implement IP whitelists

# Cloud Front WAF Rules

[CloudFront](https://aws.amazon.com/cloudfront/) distribution uses 
[Web Application Firewall](https://aws.amazon.com/waf/) (WAF)
to limit the access. 
The main part of WAF configuration in Terraform uses the
[aws_waf_ipset](https://www.terraform.io/docs/providers/aws/r/waf_ipset.html) resource:

```terraform
resource "aws_waf_ipset" "ipset" {
  name = "tfIPSet"

  ip_set_descriptors {
    type  = "IPV4"
    value = "192.0.7.0/24"
  }

  ip_set_descriptors {
    type  = "IPV4"
    value = "10.16.16.0/16"
  }
}
```

The following few more resources configures Web Application Firewall (WAF) to allow connections
only from our whitelisted IP addresses:

```terraform
resource "aws_waf_rule" "wafrule" {
  depends_on  = ["aws_waf_ipset.ipset"]

  name        = "${local.cf_waf_rule}"
  metric_name = "${local.cf_waf_rule}"

  predicates {
    data_id = "${aws_waf_ipset.ipset.id}"
    negated = false
    type    = "IPMatch"
  }
}

resource "aws_waf_web_acl" "waf_acl" {
  depends_on  = ["aws_waf_ipset.ipset", "aws_waf_rule.wafrule"]

  name        = "${local.cf_waf_acl}"
  metric_name = "${local.cf_waf_acl}"

  default_action {
    type = "BLOCK"
  }

  rules {
    action {
      type = "ALLOW"
    }
    
    priority = 1
    rule_id  = "${aws_waf_rule.wafrule.id}"
    type     = "REGULAR"
  }
}
``` 

As we see, `ip_set_descriptors` parameter has type `list`, 
each element of which is a map with two keys: `type` and `value`.
The format is different from one we use in the `ip-whitelist` module, 
Let's see how we may avoid duplication

## List to List of Maps
First idea - let's convert the existing list of IP addresses into
WAF rules in Terraform by turning every entry
of `cidr` list into a map. 

Please do not try that way, it does not work, I suppose that the
[problem](https://github.com/hashicorp/terraform/issues/9814) in Terraform `0.11.11`
does not make it work. As far as I see, Terraform loses the fact a list item was a map. 
An attempt to implement that may fail with an error like that:
```
Error: module.staging.aws_waf_ipset.name: "ip_set_descriptors.0.type": required field is not set
Error: module.staging.aws_waf_ipset.name: "ip_set_descriptors.0.value": required field is not set
```

## Map of Lists to List

The second approach it to update the
format in my `ip-whitelist` module. IP addresses are now written in the 
`aws_waf_ipset` format, aka as a list of maps. The only missing part - we need the opposite conversion
to implement `cidr` output value: We need to convert that list of maps back to
a plain list of CIDR blocks (for Security Groups).

It works! I use the following code:
```terraform

locals {
  wafs = [
    { type = "IPV4", value = "1.2.3.4/32"},
    { type = "IPV4", value = "5.6.7.8/32" },
    // ...
  ]
}

resource "null_resource" "ipv4" {
  count = "${length(local.wafs)}"

  triggers {
    cidr = "${
    lookup(local.wafs[count.index], "type") == "IPV4"
    ? lookup(local.wafs[count.index], "value")
    : ""
    }"
  }
}

output "cidr" {
  value = ["${compact(null_resource.ipv4.*.triggers.cidr)}"]
}

output "waf" {
  value = ["${local.wafs}"]
}

```

The module exports `waf` variable with WAF ipset rules, and the `cidr`
variable with IPv4 security groups. IPv6 list can be added similarly.
The conversion from `list` of `map` to `list` I do via `null_resource` and `count`
[attribute](https://www.terraform.io/docs/configuration/resources.html).
The `cidr` block is only IPv4 elements, we need to filter `waf` elements.

Let's take a look at the expression:
```
 lookup(local.wafs[count.index], "type") == "IPV4"
        ? lookup(local.wafs[count.index], "value")
        : ""
```

We replace incorrect elements with empty strings. Terraform has the
`compact` function to remove empty strings from a list. 

There is no direct loop function in Terraform 0.11.11.
The `null_resource` resource with `count` attribute works as the loop.
The last expression `null_resource.ipv4.*.triggers.cidr` selects the addresses
as a list.

## Conclusion

All sources from the post are available on the [GitHub](https://github.com/jonnyzzz/terraform-ip-whitelist)
repository. You'll find a live example and templates to use it in your projects
easily.

We've seen how to create and share the list of IP addresses between
different security groups and WAF rules. It helps to avoid duplicates
in the deployment code. Should something change in the company infrastructure,
we could easily change only one file in the deployments code to replicate it.

Do you use WAF? Check out [the previous post]({% post_url blog/2019-03-26-terraform-cloudfront-sg %})
to see how to configure a Security Group to allow access only from
CloudFront IP addresses.
Sometimes, one needs a `if` statement in Terraform. We discuss
[the workaround]({% post_url blog/2018-07-23-terraform-if %}) in an older post too.
 
I code Terraform scripts in
[IntelliJ IDEA](https://jetbrains.com/idea) with
the fantastic plugin done by a friend of mine:
[Terraform Support plugin](https://plugins.jetbrains.com/plugin/7808-hashicorp-terraform--hcl-language-support).