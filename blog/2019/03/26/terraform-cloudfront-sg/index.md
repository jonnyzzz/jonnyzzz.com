# Security Group for CloudFront

**Date:** March 26, 2019  
**Author:** Eugene Petrenko  
**Tags:** aws, security-group, infrastructure, terraform, devops, clouds

---

Have you ever tried to set up a Security Group
to allow access only from CloudFront IP
addresses? One Security Group will not be enough.
We'll see how to use [Terraform](https://www.terraform.io/)
to solve and to automate this task.
 
## The Application

We have a traditional application on [AWS](https://aws.amazon.com), where
a [CloudFront](https://aws.amazon.com/cloudfront/) distribution handles
the incoming traffic.
Behind it, we have static pages on
[S3](https://aws.amazon.com/s3) and API endpoints
behind [Application Load Balancer](https://aws.amazon.com/elasticloadbalancing/) (ALB).
I use [Terraform](https://www.terraform.io/) to manage
production and staging environments.

Let's say the project is new, and we are not ready to open it to the public.
We allow access to the project only from specific IP addresses.
[WAF](https://aws.amazon.com/waf/) helps us to limit access
only for specific IP addresses with CloudFront.
The last step to set up
[Security Group](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html)
for our API endpoint's ALB to allow connections only from CloudFront IP addresses.

## Security Groups

We use 
[Security Groups](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html)
to limit traffic coming to the ALB by IP addresses.
Right now we need to include CloudFront IP addresses
to the list. 

AWS Security Group has the
[limit](https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html)
for the number of ingress/egress rules, e.g. IP addresses.
You may need to create several security groups
to list all addresses, if you have more than 60 (state 2019-02-09).
You may guess, that there are more than 60 CloudFront IP addresses.

## CloudFront IP Addresses

AWS has the endpoint that
[lists all IP addresses](https://docs.aws.amazon.com/general/latest/gr/aws-ip-ranges.html)
of their services. Terraform has the command to access the list:

```terrafrom
data "aws_ip_ranges" "cloudfront" {
    services = ["cloudfront"]
}
```

The only downside --- we will need to re-run the deployment to make sure we
have the correct configuration to make sure a new IP address may not be included
in the settings, and the service
may not be accessible for some customers. I have no idea, how frequent the
list may change, probably not too frequent. Let's assume we run the deployment
frequent enough. A [CI](https://jetbrains.com/teamcity) can be used to automate it. 

## Settings up Security Groups

Let's create several security groups to overcome the
[limit](https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html).

Terraform has necessary functions for that. Here we use the `chunklist`
function to split the full list of CloudFront IP addresses into
a list of lists. We specify the number of elements, e.g. `30` and the function
returns us the a list, where every element of it is a list of not more than `30`
elements. Let's use the following code in Terraform to split IP addresses by
future security groups:

```terraform
locals {
    chunks_v4 = ["${chunklist(data.aws_ip_ranges.cloudfront.cidr_blocks, 30)}"]
}
```

## Creating Security Groups

We need to instruct Terraform to create several
Security Groups for us to reach the goal. We use `count`
[attribute](https://www.terraform.io/docs/configuration/resources.html)
in Terraform to instruct it to create several resources with
one declaration:

```
resource "aws_security_group" "cloudfront" {
    count = "${length(local.chunks_v4)}"
    
    //...
    
    ingress {
        from_port = 443
        to_port   = 443
        protocol  = "tcp"
        cidr_blocks = ["${local.chunks_v4[count.index]}"]
    }

    egress {
        from_port = 0
        to_port   = 0
        protocol  = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

    lifecycle {
        create_before_destroy = true
    }
}
```

Terraform creates `count` resources for us, for every resource,
the `count.index` expression returns the current index (from 0 to `count - 1`).
In [the corner case]({% post_url blog/2018-07-23-terraform-if %}), when `count = 0`, it does not
create resources at all.

We need to create `count = length(local.chunks_v4)` Security Groups.
The `local.chunks_v4[count.index]` selects the next chunk of CloudFront
IP addresses to fill into the next security group.

## Conclusion

We found an easy way to configure IP addresses filter for an Application Load Balancer
to allow incoming traffic only from CloudFront IP addresses. We made Terraform to create
and maintain several Security Groups to overcome the limits.

You may also want to read my previous post on how to implement
[an If Statement]({% post_url blog/2018-07-23-terraform-if %})
analog in Terraform.