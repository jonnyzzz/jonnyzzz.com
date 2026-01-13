# Magic Cable for Nvidia Spark

**Date:** November 26, 2025  
**Author:** Eugene Petrenko  
**Tags:** ai, ollama, gpt-oss, intellij, hardware, ai agent

---

# Plugging an AI Supercomputer into IntelliJ: Our DGX Spark Story

A small, heavy box arrived at the desk.

<iframe src="https://www.linkedin.com/embed/feed/update/urn:li:share:7397746344335048704" height="703" width="504" frameborder="0" allowfullscreen="" title="Embedded post"></iframe>

Inside: an NVIDIA DGX Spark — a desktop AI box that looks like a PC, and behaves like a tiny datacenter. The obvious question for us was:

> How do we make this thing feel *invisible* from inside IntelliJ?

This post is about the path we took to connect DGX Spark and IntelliJ in a way that:

* keeps everything **local** and **offline-friendly**,
* keeps security teams **relaxed**,
* and keeps developers in **flow**, not in network manuals.

There is also a tiny hardware trick involved! And the shiny user experience we are fighting for!

I am going to demo the device, the magic cable (JetCable) at **AWS re:Invent**,
come visit **JetBrains booth** for the real demo!

## Why Local AI Matters for IDE Workflows

Cloud AI is amazing — until the first security review. And of course, there are many of us 
who are happy to use the frontier models (e.g. Anthropic, OpenAI, Google, xAI, ...).
There is a way to many regulated businesses, where it's not yet possible or profitable. 

Many teams live under constraints like:
* strict compliance rules
* code and data that must never leave the corporate network
* air-gapped or tightly segmented infrastructure
* flat usage plans (you own the hardware, you use it 100% of the time)

For those teams, “send code to an external model endpoint” is not an option.  
[Nvidia DGX Spark](https://www.nvidia.com/en-us/products/workstations/dgx-spark/) gives a different model:
* AI hardware is **on the desk** or **on-prem**
* the box can be configured with **no direct internet access**
* all prompts, code, embeddings, and models stay **inside the company perimeter**

From the local development perspective, we want:
* AI assistance and heavy compute for code
* minimal configuration
* and strong guarantees that the bits never leave the building

The integration story started from a simple goal:

> Treat DGX Spark as a local development tool, not “another cloud”.

## Step Zero: “Just Put It on the Network”

The first obvious attempt followed the official playbook:
1. Plug DGX Spark into the corporate network (Wi-Fi or Ethernet).
2. Finish OS setup, accounts, security.
3. Connect from dev machines over the LAN.
4. Install agents, tools, and talk to the device via IP.

On paper, this is fine.

In real corporate networks, we hit the usual obstacles:

* VLANs and firewalls.
* Ports that work in one environment and disappear in another.
* VPNs that break discovery.
* “Networking changes” with lead times measured in sprints.
* Broken flow (instead of trying, you're configuring and rebuilding for hours)

We want a different experience:
1. We unbox Nvidia DGX Spark.
2. We connect one cable.
3. IntelliJ quietly detects a device and offers to use it for AI and heavy tasks.

No manuals, no “Which IP did DHCP assign this time?”, no ticket to “open port 12345”.
So we decided to remove the corporate network from the diagram.

## Attempt #1: USB Gadget Magic

The natural idea for a direct link is USB-C. Modern devices can expose, over USB:
* a network interface
* a serial/COM port
* or a custom vendor protocol

The experiment:
* make DGX Spark pretend its USB-C is a **network adapter**;
* let it run a small **DHCP server**, assign an IP to the dev machine;
* expose a small API / SSH / custom protocol over this private point-to-point link.

On Linux, gadget drivers make this possible. Early tests were promising.
Then we remembered a detail: this needs to work on **Windows, macOS, and Linux** developer machines.

That implies:
* custom drivers
* code signing and OS-specific packaging
* keeping up with random OS updates
* debugging strange USB behaviour on a random laptop the night before a release

Technically, possible and feasible. As a product, not something we want to base everything on.
We stepped back and asked a simpler question:

> What is the most boring piece of hardware that all OSes already understand?

Answer: **a regular network adapter**.

## The Final Trick: Two NICs and a Tiny Cable

The design we ended up with is almost disappointingly simple:

> Use two standard Ethernet adapters connected by a short cable, one on the
> Nvidia DGX Spark side, one on the developer machine. Both go into USB-C.

Diagram version:

```text
[IntelliJ laptop]
    |
    | USB-C
    |
    v                 
[USB-Ethernet #1] == short cable == [USB-Ethernet #2]
                                           ^
                                           |
                                         USB-C
                                           |
                                           v
                                  [NVidia DGX Spark]
```

<iframe src="https://www.linkedin.com/embed/feed/update/urn:li:share:7398855051676471296" height="639" width="504" frameborder="0" allowfullscreen="" title="Embedded post"></iframe>

And this setup is working greatly! We make the Nvidia DGX Spark run as DHCP and DNS for the network interface,
so it means it will assign the developer machine the specific IP address. The software (say an IntelliJ plugin)
will know about the port, or it will even look up it via DNS or either way. 

## Current State

We are running vLLM on the box, JetBrains AI Assistant can connect and use it, 
we're experimenting to let JetBrains Junie use the box as the primary model too. 
So far it's the demo phase to show what we can do and what's coming next!

From the product standpoint, we take an assumption that there will be more
powerful LLM models with open weights and the hardware to run the inference
as fast as possible. We are experimenting with the "tool" product to make
software development much more pleasurable and still more productive.

Stay tuned!

<blockquote class="instagram-media" data-instgrm-permalink="https://www.instagram.com/p/DRhfcEQjBBi/?utm_source=ig_embed&amp;utm_campaign=loading" data-instgrm-version="14" style=" background:#FFF; border:0; border-radius:3px; box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:540px; min-width:326px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);"><div style="padding:16px;"> <a href="https://www.instagram.com/p/DRhfcEQjBBi/?utm_source=ig_embed&amp;utm_campaign=loading" style=" background:#FFFFFF; line-height:0; padding:0 0; text-align:center; text-decoration:none; width:100%;" target="_blank"> <div style=" display: flex; flex-direction: row; align-items: center;"> <div style="background-color: #F4F4F4; border-radius: 50%; flex-grow: 0; height: 40px; margin-right: 14px; width: 40px;"></div> <div style="display: flex; flex-direction: column; flex-grow: 1; justify-content: center;"> <div style=" background-color: #F4F4F4; border-radius: 4px; flex-grow: 0; height: 14px; margin-bottom: 6px; width: 100px;"></div> <div style=" background-color: #F4F4F4; border-radius: 4px; flex-grow: 0; height: 14px; width: 60px;"></div></div></div><div style="padding: 19% 0;"></div> <div style="display:block; height:50px; margin:0 auto 12px; width:50px;"><svg width="50px" height="50px" viewBox="0 0 60 60" version="1.1" xmlns="https://www.w3.org/2000/svg" xmlns:xlink="https://www.w3.org/1999/xlink"><g stroke="none" stroke-width="1" fill="none" fill-rule="evenodd"><g transform="translate(-511.000000, -20.000000)" fill="#000000"><g><path d="M556.869,30.41 C554.814,30.41 553.148,32.076 553.148,34.131 C553.148,36.186 554.814,37.852 556.869,37.852 C558.924,37.852 560.59,36.186 560.59,34.131 C560.59,32.076 558.924,30.41 556.869,30.41 M541,60.657 C535.114,60.657 530.342,55.887 530.342,50 C530.342,44.114 535.114,39.342 541,39.342 C546.887,39.342 551.658,44.114 551.658,50 C551.658,55.887 546.887,60.657 541,60.657 M541,33.886 C532.1,33.886 524.886,41.1 524.886,50 C524.886,58.899 532.1,66.113 541,66.113 C549.9,66.113 557.115,58.899 557.115,50 C557.115,41.1 549.9,33.886 541,33.886 M565.378,62.101 C565.244,65.022 564.756,66.606 564.346,67.663 C563.803,69.06 563.154,70.057 562.106,71.106 C561.058,72.155 560.06,72.803 558.662,73.347 C557.607,73.757 556.021,74.244 553.102,74.378 C549.944,74.521 548.997,74.552 541,74.552 C533.003,74.552 532.056,74.521 528.898,74.378 C525.979,74.244 524.393,73.757 523.338,73.347 C521.94,72.803 520.942,72.155 519.894,71.106 C518.846,70.057 518.197,69.06 517.654,67.663 C517.244,66.606 516.755,65.022 516.623,62.101 C516.479,58.943 516.448,57.996 516.448,50 C516.448,42.003 516.479,41.056 516.623,37.899 C516.755,34.978 517.244,33.391 517.654,32.338 C518.197,30.938 518.846,29.942 519.894,28.894 C520.942,27.846 521.94,27.196 523.338,26.654 C524.393,26.244 525.979,25.756 528.898,25.623 C532.057,25.479 533.004,25.448 541,25.448 C548.997,25.448 549.943,25.479 553.102,25.623 C556.021,25.756 557.607,26.244 558.662,26.654 C560.06,27.196 561.058,27.846 562.106,28.894 C563.154,29.942 563.803,30.938 564.346,32.338 C564.756,33.391 565.244,34.978 565.378,37.899 C565.522,41.056 565.552,42.003 565.552,50 C565.552,57.996 565.522,58.943 565.378,62.101 M570.82,37.631 C570.674,34.438 570.167,32.258 569.425,30.349 C568.659,28.377 567.633,26.702 565.965,25.035 C564.297,23.368 562.623,22.342 560.652,21.575 C558.743,20.834 556.562,20.326 553.369,20.18 C550.169,20.033 549.148,20 541,20 C532.853,20 531.831,20.033 528.631,20.18 C525.438,20.326 523.257,20.834 521.349,21.575 C519.376,22.342 517.703,23.368 516.035,25.035 C514.368,26.702 513.342,28.377 512.574,30.349 C511.834,32.258 511.326,34.438 511.181,37.631 C511.035,40.831 511,41.851 511,50 C511,58.147 511.035,59.17 511.181,62.369 C511.326,65.562 511.834,67.743 512.574,69.651 C513.342,71.625 514.368,73.296 516.035,74.965 C517.703,76.634 519.376,77.658 521.349,78.425 C523.257,79.167 525.438,79.673 528.631,79.82 C531.831,79.965 532.853,80.001 541,80.001 C549.148,80.001 550.169,79.965 553.369,79.82 C556.562,79.673 558.743,79.167 560.652,78.425 C562.623,77.658 564.297,76.634 565.965,74.965 C567.633,73.296 568.659,71.625 569.425,69.651 C570.167,67.743 570.674,65.562 570.82,62.369 C570.966,59.17 571,58.147 571,50 C571,41.851 570.966,40.831 570.82,37.631"></path></g></g></g></svg></div><div style="padding-top: 8px;"> <div style=" color:#3897f0; font-family:Arial,sans-serif; font-size:14px; font-style:normal; font-weight:550; line-height:18px;">View this post on Instagram</div></div><div style="padding: 12.5% 0;"></div> <div style="display: flex; flex-direction: row; margin-bottom: 14px; align-items: center;"><div> <div style="background-color: #F4F4F4; border-radius: 50%; height: 12.5px; width: 12.5px; transform: translateX(0px) translateY(7px);"></div> <div style="background-color: #F4F4F4; height: 12.5px; transform: rotate(-45deg) translateX(3px) translateY(1px); width: 12.5px; flex-grow: 0; margin-right: 14px; margin-left: 2px;"></div> <div style="background-color: #F4F4F4; border-radius: 50%; height: 12.5px; width: 12.5px; transform: translateX(9px) translateY(-18px);"></div></div><div style="margin-left: 8px;"> <div style=" background-color: #F4F4F4; border-radius: 50%; flex-grow: 0; height: 20px; width: 20px;"></div> <div style=" width: 0; height: 0; border-top: 2px solid transparent; border-left: 6px solid #f4f4f4; border-bottom: 2px solid transparent; transform: translateX(16px) translateY(-4px) rotate(30deg)"></div></div><div style="margin-left: auto;"> <div style=" width: 0px; border-top: 8px solid #F4F4F4; border-right: 8px solid transparent; transform: translateY(16px);"></div> <div style=" background-color: #F4F4F4; flex-grow: 0; height: 12px; width: 16px; transform: translateY(-4px);"></div> <div style=" width: 0; height: 0; border-top: 8px solid #F4F4F4; border-left: 8px solid transparent; transform: translateY(-4px) translateX(8px);"></div></div></div> <div style="display: flex; flex-direction: column; flex-grow: 1; justify-content: center; margin-bottom: 24px;"> <div style=" background-color: #F4F4F4; border-radius: 4px; flex-grow: 0; height: 14px; margin-bottom: 6px; width: 224px;"></div> <div style=" background-color: #F4F4F4; border-radius: 4px; flex-grow: 0; height: 14px; width: 144px;"></div></div></a><p style=" color:#c9c8cd; font-family:Arial,sans-serif; font-size:14px; line-height:17px; margin-bottom:0; margin-top:8px; overflow:hidden; padding:8px 0 7px; text-align:center; text-overflow:ellipsis; white-space:nowrap;"><a href="https://www.instagram.com/p/DRhfcEQjBBi/?utm_source=ig_embed&amp;utm_campaign=loading" style=" color:#c9c8cd; font-family:Arial,sans-serif; font-size:14px; font-style:normal; font-weight:normal; line-height:17px; text-decoration:none;" target="_blank">A post shared by Eugene Petrenko (@jonnyzzz)</a></p></div></blockquote>
<script async src="//www.instagram.com/embed.js"></script>


## Related Work

There are many areas were we definitely need to look in at, for example
* NVIDIA Sync tool
* SSH tunneling to connect to the NVIDIA Spark
* Using JetBrains cloud service to activate the device and let it with offline afterward
* Automatic configuration and pre-population of the software and AI model images
* Running AI Assistant, Junie, and JetBrains Mellum on the solution
* Making the solution distribute licenses
* Running local RAG's in the device or near-by
* Making the cable smarter to support us with all of that

The magic cable itself appears to have much of the potential, I'm looking forward
to sharing more with you. We are going to post more, stay tuned, or reach
out in DMs for more details.

# New World & AWS re:Invent 2025

There are so many ideas that we have and found working on this project, stay tuned,
and let me know (via LinkedIn) what you think or would expect from us. I will update. 

**I'll be deming the solution, the JetCable at AWS re:Invent this year,
stop by at JetBrains booth, and let's talk about the local AI. See ya!**
Drop me align via [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) or [Twitter](https://x.com/jonnyzzz) to stay in touch.

<blockquote class="twitter-tweet"><p lang="en" dir="ltr">Gearing up for Las Vegas? ✈️<br><br>I’ll be at AWS re:Invent next week, and I&#39;m looking forward to connecting with you and discussing the future trends. Passionate about Local LLMs, AI, Coding Agents, Developer Experience, and JetBrains&#39; new products?<br><br>Stop by the JetBrains booth to… <a href="https://t.co/JAPiDcux6m">pic.twitter.com/JAPiDcux6m</a></p>&mdash; Eugene Petrenko (@jonnyzzz) <a href="https://twitter.com/jonnyzzz/status/1993702449450713154?ref_src=twsrc%5Etfw">November 26, 2025</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>