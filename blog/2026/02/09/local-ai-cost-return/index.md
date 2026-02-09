# The Cost Return of Local AI: When Does Your Hardware Pay for Itself?

**Date:** February 09, 2026  
**Author:** Eugene Petrenko  
**Tags:** local-ai, ai-agents, hardware, ai-coding, llm, cost-analysis

---

Should you buy Local AI hardware or rent cloud tokens? I've been running local models on an
[NVIDIA DGX Spark][spark-post] and a MacBook Pro M4 Max with 128GB, orchestrating fleets of
[AI Agents][agents-post] against them. The analysis below also covers Mac Studio configurations
and dual-GPU workstations for comparison. The obvious question: **does it actually save money
compared to Anthropic and OpenAI APIs?**

We analyzed four popular setups, drawing from published benchmarks and community testing. Then
we modeled what happens when cloud prices keep falling. The answer is more nuanced -- and more
interesting -- than I expected.

**Key finding:** At full utilization, mid-range setups (Mac Studio M4 Max 128GB, DGX Spark)
can pay for themselves in **1.6--8 months** when replacing Opus/Sonnet-class API usage -- the
DGX Spark running GPT-OSS 120B breaks even in **under 2 months**. But cloud API prices are
falling so fast that your spreadsheet might be wrong before your hardware arrives.

All calculations below are reproducible. [Grab the Python calculator][calculator] and run it
yourself with `uv run local-ai-payoff-calculator.py`.

---

## The Four Setups

We selected four configurations representing different price-performance tiers. All suitable
for Local AI inference in a desktop/office environment. Prices reflect Apple.com configurator
and NVIDIA retail as of Q1 2026. Electricity costs are **explicitly excluded** (we address
them separately below).

### Setup A: Mac Studio M3 Ultra -- 512GB

| Spec         | Detail                                                              |
|--------------|---------------------------------------------------------------------|
| **Chip**     | Apple M3 Ultra, 32-core CPU, 80-core GPU, 32-core Neural Engine    |
| **Memory**   | 512GB unified (819 GB/s bandwidth)                                  |
| **Price**    | **~$9,500** (base $3,999 + chip upgrade + 512GB RAM)                |

*Pricing source: [Apple Mac Studio configurator][apple-studio]*

The M3 Ultra's 819 GB/s memory bandwidth is its killer feature. Token generation speed is
almost entirely memory-bandwidth bound. This is the only desktop-class machine that can run
600B+ parameter models (like DeepSeek R1 671B) entirely in memory.

### Setup B: Mac Studio M4 Max -- 128GB

| Spec         | Detail                                                              |
|--------------|---------------------------------------------------------------------|
| **Chip**     | Apple M4 Max, 16-core CPU, 40-core GPU, 16-core Neural Engine      |
| **Memory**   | 128GB unified (546 GB/s bandwidth)                                  |
| **Price**    | **~$3,500** (base $1,999 + chip and memory upgrades)                |

*Pricing source: [Apple Mac Studio configurator][apple-studio]*

Best single-core performance of any Apple chip. Its 546 GB/s bandwidth and 128GB handle
quantized 70B models comfortably.

### Setup C: NVIDIA DGX Spark -- 128GB

| Spec          | Detail                                                             |
|---------------|--------------------------------------------------------------------|
| **Chip**      | NVIDIA GB10 Grace Blackwell Superchip                              |
| **Memory**    | 128GB LPDDR5x unified (273 GB/s bandwidth)                        |
| **AI Compute**| 1 PFLOP FP4                                                       |
| **Price**     | **$3,999**                                                         |

*Pricing source: [NVIDIA DGX Spark product page][nvidia-spark]*

Excels at prompt processing (prefill) thanks to Blackwell tensor cores and FP4/NVFP4 support.
Its relatively lower memory bandwidth (273 GB/s) limits token generation speed, but its
[MoE performance is a standout][spark-post].

### Setup D: Dual RTX 3090 Workstation

| Spec              | Detail                                                        |
|-------------------|---------------------------------------------------------------|
| **GPUs**          | 2x NVIDIA RTX 3090 (24GB VRAM each = 48GB total)             |
| **GPU Bandwidth** | 936 GB/s per card                                             |
| **Price**         | **~$3,600** (used 3090s ~$800 each + rest of system)          |

The price-performance champion for pure inference throughput within its 48GB VRAM limit.
Models must fit within GPU VRAM; larger models fall back to CPU offloading with severe
performance penalties.

---

## Models and Benchmarks

All benchmarks use 4-bit quantization (Q4_K_M for GGUF, NVFP4 where available) -- the
practical sweet spot for quality vs. performance. Token generation speed is single-user,
interactive decode using llama.cpp or MLX.

### Token Generation Speed (tokens/second)

| Model                    | A: M3 Ultra | B: M4 Max | C: DGX Spark | D: 2x 3090 |
|--------------------------|-------------|-----------|--------------|-------------|
| **LLaMA 3.1 8B Q4**     | ~85         | ~70       | ~38          | ~120        |
| **Qwen3 30B Q4**        | ~30         | ~22       | ~20          | ~35         |
| **LLaMA 3.1 70B Q4**   | ~14         | ~8        | ~6           | ~13         |
| **GPT-OSS 120B Q4**    | ~20         | ~10       | ~50          | Cannot fit  |
| **DeepSeek R1 671B Q4** | ~17         | --        | --           | --          |

The DGX Spark's GPT-OSS 120B number stands out: **50 t/s on a $3,999 box**. This is the MoE
(Mixture of Experts) sweet spot -- only ~20B parameters active per token, but the NVFP4
tensor cores eat it for breakfast.

*Sources: [llama.cpp Apple Silicon discussion #4167][llamacpp-4167],
[LMSYS DGX Spark review][lmsys-spark], [hardware-corner.net benchmarks][hardware-corner],
[LMSYS GPT-OSS on DGX Spark][lmsys-gpt-oss]*

---

## Cloud API Pricing

We map each local model to a comparable cloud API tier. This mapping is inherently approximate
-- a local LLaMA 70B Q4 doesn't match Claude Sonnet 4.5 quality. But they serve similar use
cases at roughly comparable quality levels.

### Output Token Pricing (as of Q1 2026)

| Provider                        | Model                                | Input $/MTok | Output $/MTok | Comparable Local Model    |
|---------------------------------|--------------------------------------|--------------|---------------|---------------------------|
| [**Anthropic**][anthropic-pricing] | [Claude Haiku 4.5][anthropic-pricing]  | $1.00        | $5.00         | LLaMA 3.1 8B              |
| [**Anthropic**][anthropic-pricing] | [Claude Sonnet 4.5][anthropic-pricing] | $3.00        | $15.00        | LLaMA 3.1 70B, Qwen3 30B |
| [**Anthropic**][anthropic-pricing] | [Claude Opus 4.5][anthropic-pricing]   | $5.00        | $25.00        | DeepSeek R1 671B, GPT-OSS |
| [**OpenAI**][openai-pricing]       | [GPT-4o][openai-pricing]            | $2.50        | $10.00        | LLaMA 3.1 70B, Qwen3 30B |
| [**OpenAI**][openai-pricing]       | [GPT-4o mini][openai-pricing]       | $0.15        | $0.60         | LLaMA 3.1 8B              |
| [**OpenAI**][openai-pricing]       | [GPT-5.1][openai-pricing]           | $1.25        | $10.00        | GPT-OSS 120B              |

*Sources: [Anthropic API pricing][anthropic-pricing], [OpenAI pricing][openai-pricing],
[MetaCTO analysis (Dec 2025)][metacto]*

---

## The Payoff Table

**Payoff = Hardware Cost / Cloud Cost Per Hour**

We assume a 70/30 output/input token ratio (typical for interactive use). Weighted price per
million tokens = 0.7 x output + 0.3 x input. Tokens per hour = tokens/sec x 3600.

| Setup + Model                           | HW Cost | Cloud $/hr | **Payoff Months** |
|-----------------------------------------|---------|------------|-------------------|
| **C: DGX Spark + GPT-OSS 120B**        | $3,999  | $3.42      | **1.6**           |
| **D: 2x3090 + LLaMA 8B**              | $3,600  | $1.64      | **3.0**           |
| **D: 2x3090 + Qwen3 30B**             | $3,600  | $1.44      | **3.5**           |
| **B: M4 Max + LLaMA 8B**              | $3,500  | $0.96      | **5.1**           |
| **C: DGX Spark + Qwen3 30B**          | $3,999  | $0.82      | **6.8**           |
| **B: M4 Max + GPT-OSS 120B**          | $3,500  | $0.68      | **7.1**           |
| **B: M4 Max + Qwen3 30B**             | $3,500  | $0.61      | **7.9**           |
| **D: 2x3090 + LLaMA 70B**             | $3,600  | $0.53      | **9.4**           |
| **A: M3 Ultra + GPT-OSS 120B**        | $9,500  | $1.37      | **9.6**           |
| **A: M3 Ultra + DeepSeek R1 671B**    | $9,500  | $1.16      | **11.3**          |
| **A: M3 Ultra + Qwen3 30B**           | $9,500  | $1.23      | **10.7**          |
| **C: DGX Spark + LLaMA 8B**           | $3,999  | $0.52      | **10.7**          |
| **A: M3 Ultra + LLaMA 8B**            | $9,500  | $1.16      | **11.3**          |
| **B: M4 Max + LLaMA 70B**             | $3,500  | $0.33      | **14.8**          |
| **C: DGX Spark + LLaMA 70B**          | $3,999  | $0.25      | **22.6**          |
| **A: M3 Ultra + LLaMA 70B**           | $9,500  | $0.57      | **23.0**          |

These numbers assume **100% utilization, 24/7**. Multiply by 2x for 12hr/day usage, 4x for
6hr/day, 10x for occasional use.

---

## The Sweet Spot

Three scenarios stand out:

1. **DGX Spark + GPT-OSS 120B vs Opus-class pricing: ~1.6 months.** The Blackwell tensor cores
   combined with MoE efficiency and NVFP4 quantization make this the fastest payoff. At 50%
   utilization it's 4 months. This is the standout finding -- **under 2 months at full
   utilization**.

2. **Dual RTX 3090 + small/medium models: 3--3.5 months.** Highest raw throughput on models
   that fit in 48GB VRAM. The used GPU market makes this the cheapest entry point.

3. **M4 Max 128GB + 8B/30B models: 5--8 months.** The best balance of price, ecosystem
   (MLX), silence, and capability for a single developer.

The M3 Ultra 512GB shows **11.3 months** payoff for DeepSeek R1 671B (~17 t/s), making it
competitive with other mid-range scenarios. It's the only desktop that runs these frontier-scale
models entirely in memory.

---

## But Wait -- Cloud Prices Keep Falling

Here's where the story gets uncomfortable. The payoff table above treats cloud prices as
**constant**. They are not.

According to [Epoch AI research (March 2025)][epoch-ai], LLM inference prices have fallen
between 9x and 900x per year depending on the benchmark, with a median decline of **50x per
year**. After January 2024, the median rate accelerated to **200x per year**. The [Stanford
HAI AI Index][stanford-hai] puts it starkly: GPT-3.5-level performance cost fell from $20 per
1M tokens (November 2022) to $0.07 (October 2024) -- **280x in 18 months**.

What does that do to our payoff math?

### Risk-Adjusted Payoff (months)

Here's the DGX Spark + GPT-OSS 120B (the best scenario) under different cloud price decline
rates and utilization levels:

| Utilization | Constant price | 25%/yr decline | 50%/yr decline | 80%/yr decline |
|-------------|----------------|----------------|----------------|----------------|
| 100% (24/7) | 2              | 2              | 2              | 2              |
| 50% (12h/d) | 4              | 4              | 4              | 4              |
| 25% (6h/d)  | 7              | 7              | 8              | 13             |
| 10% (2.4h/d)| 17             | 21             | 42             | never          |

And the M4 Max + Qwen3 30B (a more typical developer scenario):

| Utilization | Constant price | 25%/yr decline | 50%/yr decline | 80%/yr decline |
|-------------|----------------|----------------|----------------|----------------|
| 100% (24/7) | 8              | 9              | 11             | 39             |
| 50% (12h/d) | 16             | 20             | 39             | never          |
| 25% (6h/d)  | 32             | 58             | never          | never          |
| 10% (2.4h/d)| 80             | never          | never          | never          |

**"Never" means the hardware never pays for itself** -- cumulative cloud savings converge to
a finite amount that's less than the hardware cost. Mathematically:

> Max lifetime savings = C0 / (1 - m), where m = (1 - annual_decline_rate)^(1/12)
>
> If hardware_cost > max_lifetime_savings, payoff = never.

This is the most dangerous finding: **at 80% annual cloud price decline and less than 25%
utilization, most setups never break even on token economics alone.**

---

## Seven Trends Shaping the Next 18 Months

I track these because they directly affect whether buying Local AI hardware today is smart
or premature:

### 1. API Price Deflation -- The Biggest Threat

OpenAI moved from GPT-4 ($30/$60 per MTok) to GPT-4 Turbo ($10/$30), then to GPT-4o
($2.50/$10) -- an 83% decline from GPT-4 to GPT-4o. DeepSeek V3.2 hit $0.28/$0.42 per
MTok -- 90% below GPT-4.1. Gartner forecasts that by 2026, AI services cost will become a
chief competitive factor.

**Impact:** A payoff period of 8 months today becomes 80 months if prices drop 10x.

### 2. Open-Source Quality -- The Biggest Tailwind

According to [WhatLLM.org][whatllm] (January 2026), the gap between best open-source and
proprietary models has narrowed significantly -- down from 20+ points in late 2024 to
single digits in early 2026. Open-source models now win on specific benchmarks outright.

**Impact:** Closes the "quality discount" in our calculations. A local 30B running in 2026
might genuinely match GPT-4o quality.

### 3. Hardware Depreciation -- The Clock Is Ticking

Apple M5 launched October 2025 with 30% bandwidth improvement. M5 Ultra **rumored** for mid-2026
at ~1,100 GB/s (unconfirmed, no official announcement). RTX 5090 ships at $1,999 MSRP and shows
significant throughput improvements over RTX 4090 in early community benchmarks.

**Impact:** A $9,500 M3 Ultra bought today will be outperformed by an M5 Ultra at similar
price within 6--9 months.

### 4. Model Efficiency -- Smaller Gets Smarter

Model distillation techniques continue advancing rapidly. Smaller models (8B-30B range) are
increasingly matching or approaching the quality of previous-generation 70B+ models through
better training and distillation methods.

**Impact:** Your hardware gets more capable over time through software alone. The M4 Max
becomes a better machine next year without changing anything.

### 5. Agentic AI -- The Utilization Multiplier

[CB Insights tracks 170+ AI Agent startups][cbinsights-agents] with billions in funding.
Gartner forecasts 40% of enterprise apps will have task-specific AI Agents by end of 2026. When I run
[fleets of AI Agents][agents-post], utilization jumps from 25% to 60--80%. That transforms
the payoff math.

**Impact:** The catch is that local models still struggle with reliable tool calling in
agentic contexts. Until that matures, the highest-value workloads stay on cloud.

**OpenClaw and Personal AI Assistants:** One compelling agentic use case is running personal
AI assistant bots like [OpenClaw][openclaw] (formerly ClawdBot/Moltbot). OpenClaw runs locally,
integrates with messaging services (Signal, Telegram, Discord, WhatsApp), and connects to either
cloud APIs or local LLMs via Ollama. With [147,000+ GitHub stars and 2 million visitors in a
week][openclaw-dev], it represents the "2026 year of personal agents" trend. Running these bots
24/7 on local hardware makes the utilization economics much more attractive -- a DGX Spark or Mac
Studio running OpenClaw with a local 70B model is generating value around the clock, not just
during active coding sessions.

### 6. Privacy and Compliance -- The Non-Financial ROI

For regulated industries, a single data breach can cost millions. That makes the $3,500--$9,500
hardware investment trivially justified regardless of the break-even math.

### 7. Distributed Clustering -- EXO Labs Changes Everything

[EXO 1.0][exo-github] with RDMA over Thunderbolt 5 (macOS 26.2) lets multiple Macs pool
memory. [Jeff Geerling's benchmarks][geerling-cluster] on a 4x M3 Ultra cluster (1.5TB total):

| Model                      | 1 Node (t/s) | 4 Nodes EXO+RDMA (t/s) |
|----------------------------|--------------|------------------------|
| Qwen3 235B (8-bit)         | 19.5         | **31.9** (+64%)        |
| DeepSeek V3.1 671B (8-bit) | 21.1         | **32.5** (+54%)        |

Without RDMA, adding nodes actually **decreased** performance. With RDMA, latency drops from
~300us to <50us. This means you can start with one $3,500 M4 Max, prove utilization, then add
machines incrementally -- instead of betting $9,500 on a single box.

---

## The Decision Framework

Combining all trends:

| Factor                    | Direction          | Net Effect on Local ROI    |
|---------------------------|--------------------|----------------------------|
| API price deflation       | Hurts local case   | **Strong negative**        |
| Open-source quality gains | Helps local case   | **Strong positive**        |
| Hardware depreciation     | Hurts local case   | **Moderate negative**      |
| Model efficiency          | Helps local case   | **Strong positive**        |
| Agentic utilization       | Helps local case   | **Conditional positive**   |
| Privacy/compliance value  | Helps local case   | **Strong positive**        |
| Distributed clustering    | Helps local case   | **Strong positive**        |

The two strongest forces -- API price deflation and open-source quality gains -- partially
cancel each other out. The decisive variable remains **utilization**: local hardware wins when
it runs consistently, and AI Agent fleets may be the catalyst that makes consistent utilization
the norm.

### The Practical Rule

- If your setup pays back in **<6 months** even under 50%/yr cloud price decline + realistic
  utilization: **buy it**.
- If payback is **>18 months** in the base case: treat local as a bet on **non-price value**
  (privacy, reliability, independence) -- not pure ROI.
- If your workload is compatible with cheap/batched/cached cloud: **local ROI risk increases
  substantially**.

### My Recommendation

**Start with the lowest viable hardware** -- M4 Max at $3,500 or DGX Spark at $3,999. Aim
for break-even within 6 months at realistic utilization. **Scale by clustering** -- add a
second machine via EXO/RDMA when utilization proves out, rather than buying the most expensive
single box upfront.

Reserve the M3 Ultra 512GB for teams that have already proven sustained utilization on smaller
hardware and need frontier-scale models that cannot run elsewhere.

---

## The Calculator

All the numbers in this post come from a single Python program that you can run, modify, and
extend. It's a [uv-compatible script][calculator] -- no dependencies, just:

```bash
uv run local-ai-payoff-calculator.py
```

It computes:
- Main payoff table (all setup x model combinations)
- Risk-adjusted scenarios (with cloud price decline modeling)
- Electricity cost impact analysis
- JSON output for further processing

[Download the calculator][calculator] and plug in your own hardware costs, throughput numbers,
and cloud pricing. The numbers will be different by the time you read this -- that's the point.

---

## Methodology Notes

A few things we explicitly chose to exclude or simplify:

1. **Electricity excluded**: The dual RTX 3090 at 700W costs ~$0.105/hr -- adds 20% to the
   cheapest cloud equivalent. Mac Studio at 200W adds ~5%. Not nothing, but not the main
   driver.

2. **Quality mapping is approximate**: A quantized 70B model is not Claude Sonnet 4.5.
   Cloud frontier models maintain a quality advantage for many tasks. This analysis assumes
   "good enough" for your use case.

3. **Single-user inference**: Batched inference (multiple users) changes economics
   dramatically in favor of CUDA hardware.

4. **Maintenance and depreciation excluded**: Hardware lasts 3--5 years. Resale value not
   factored in.

5. **Benchmark data sources**: Token speeds are composites from llama.cpp, MLX, Ollama, NVIDIA
   official benchmarks, and Geerling's repository. Numbers represent typical single-stream
   decode speeds as of Q1 2026. Actual performance varies with context length, quantization
   method, and framework version.

---

## Sources and References

### Hardware Pricing
- [Apple.com Mac Studio configurator][apple-studio]
- [NVIDIA DGX Spark marketplace ($3,999 MSRP)][nvidia-spark]
- [Micro Center DGX Spark listing][microcenter-spark]

### Inference Benchmarks
- [llama.cpp Apple Silicon discussion #4167][llamacpp-4167]
- [llama.cpp DGX Spark discussion #16578][llamacpp-16578]
- [LMSYS DGX Spark in-depth review (October 2025)][lmsys-spark]
- [LMSYS GPT-OSS on DGX Spark (November 2025)][lmsys-gpt-oss]
- [hardware-corner.net DGX Spark benchmarks][hardware-corner]
- [AIMultiple DGX Spark analysis][aimultiple-spark]
- [Jeff Geerling: Mac Studio RDMA cluster][geerling-cluster]
- [NVIDIA Developer Blog: DGX Spark Performance][nvidia-spark-blog]
- [Ollama DGX Spark Performance Analysis][ollama-spark]

### Cloud API Pricing
- [Anthropic API pricing][anthropic-pricing]
- [OpenAI API pricing][openai-pricing]
- [MetaCTO Claude pricing guide (December 2025)][metacto]
- [CostGoat Claude API calculator][costgoat-claude]

### Future Trends
- [Epoch AI: LLM inference price trends][epoch-ai]
- [Stanford HAI AI Index 2025][stanford-hai]
- [Jeff Geerling: 1.5TB VRAM Mac Studio cluster (December 2025)][geerling-cluster]
- [EXO Labs GitHub][exo-github]
- [WhatLLM.org model quality analysis][whatllm]
- [SOSP'25 Aegaeon paper: token-level GPU pooling][aegaeon]

### Comparative Guides
- [Introl.com: Local LLM Hardware Guide 2025][introl-guide]
- [ikangai.com: Complete Guide to Running LLMs Locally][ikangai-guide]

---

*This analysis should be refreshed quarterly -- hardware (M5 Ultra expected mid-2026), API
pricing (trending sharply downward), and open-source model quality (trending sharply upward)
are all moving targets.*

*Disclaimer: Based on publicly available benchmark data and pricing as of Q1 2026. Actual
performance varies. No financial relationship with any hardware or cloud provider. Not
financial advice.*

*Have questions or corrections? Reach out on
[LinkedIn](https://www.linkedin.com/in/jonnyzzz/) or
[Twitter/X](https://x.com/jonnyzzz). Let's compare notes.*

[spark-post]: {% post_url blog/2025-11-26-junie-cage-spark %}
[agents-post]: {% post_url blog/2026-02-06-run-agent-multi-agent-orchestration %}
[calculator]: {{ site.url }}/downloads/local-ai-payoff-calculator.py
[openclaw]: https://openclaw.ai/
[openclaw-dev]: https://dev.to/mechcloud_academy/unleashing-openclaw-the-ultimate-guide-to-local-ai-agents-for-developers-in-2026-3k0h

[apple-studio]: https://www.apple.com/shop/buy-mac/mac-studio
[nvidia-spark]: https://marketplace.nvidia.com/en-us/enterprise/personal-ai-supercomputers/dgx-spark/
[microcenter-spark]: https://www.microcenter.com/product/699008/nvidia-dgx-spark

[llamacpp-4167]: https://github.com/ggml-org/llama.cpp/discussions/4167
[llamacpp-16578]: https://github.com/ggml-org/llama.cpp/discussions/16578
[lmsys-spark]: https://lmsys.org/blog/2025-10-13-nvidia-dgx-spark/
[lmsys-gpt-oss]: https://lmsys.org/blog/2025-11-03-gpt-oss-on-nvidia-dgx-spark/
[hardware-corner]: https://www.hardware-corner.net/first-dgx-spark-llm-benchmarks/
[aimultiple-spark]: https://research.aimultiple.com/dgx-spark-alternatives/
[nvidia-spark-blog]: https://developer.nvidia.com/blog/how-nvidia-dgx-sparks-performance-enables-intensive-ai-tasks/
[ollama-spark]: https://ollama.com/blog/nvidia-spark-performance

[anthropic-pricing]: https://platform.claude.com/docs/en/about-claude/pricing
[openai-pricing]: https://openai.com/api/pricing/
[metacto]: https://www.metacto.com/blogs/anthropic-api-pricing-a-full-breakdown-of-costs-and-integration
[costgoat-claude]: https://costgoat.com/pricing/claude-api

[epoch-ai]: https://epoch.ai/data-insights/llm-inference-price-trends
[stanford-hai]: https://aiindex.stanford.edu/report/
[geerling-cluster]: https://www.jeffgeerling.com/blog/2025/15-tb-vram-on-mac-studio-rdma-over-thunderbolt-5/
[exo-github]: https://github.com/exo-explore/exo
[whatllm]: https://whatllm.org
[aegaeon]: https://arxiv.org/html/2511.23455v1
[cbinsights-agents]: https://www.cbinsights.com/research/ai-agent-market-map-2025/

[introl-guide]: https://introl.com/blog/inference-unit-economics-true-cost-per-million-tokens-guide
[ikangai-guide]: https://www.ikangai.com/the-complete-guide-to-running-llms-locally-hardware-software-and-performance-essentials/