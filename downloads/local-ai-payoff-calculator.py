#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Local AI Hardware vs. Cloud API: Payoff Calculator

All calculations for the blog post "The Cost Return of Local AI".
Run with: uv run payoff_calculator.py
"""

import json
import math
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Data definitions
# ---------------------------------------------------------------------------

@dataclass
class HardwareSetup:
    name: str
    short: str
    price_usd: float
    memory_gb: int
    bandwidth_gbs: float
    power_watts: float


@dataclass
class CloudModel:
    name: str
    provider: str
    input_per_mtok: float
    output_per_mtok: float


@dataclass
class LocalModel:
    name: str
    params: str
    q4_size_gb: float
    quality_tier: str


@dataclass
class Benchmark:
    setup: str          # short name of HardwareSetup
    model: str          # name of LocalModel
    tokens_per_sec: float  # 0 means "cannot fit"
    cloud_equivalent: str  # name of CloudModel


# ---------------------------------------------------------------------------
# Hardware setups
# ---------------------------------------------------------------------------

SETUPS = [
    HardwareSetup("Mac Studio M3 Ultra 512GB", "A", 9500, 512, 819, 200),
    HardwareSetup("Mac Studio M4 Max 128GB",   "B", 3500, 128, 546, 150),
    HardwareSetup("NVIDIA DGX Spark 128GB",    "C", 3999, 128, 273, 170),
    HardwareSetup("Dual RTX 3090 Workstation",  "D", 3600, 48,  936, 700),  # Updated from 3500 to 3600 (RTX 3090 @ $800 ea)
]
SETUP_MAP = {s.short: s for s in SETUPS}


# ---------------------------------------------------------------------------
# Cloud models
# ---------------------------------------------------------------------------

CLOUD_MODELS = [
    CloudModel("Haiku 4.5",   "Anthropic", 1.00,  5.00),
    CloudModel("Sonnet 4.5",  "Anthropic", 3.00, 15.00),
    CloudModel("Opus 4.5",    "Anthropic", 5.00, 25.00),
    CloudModel("GPT-4o",      "OpenAI",    2.50, 10.00),
    CloudModel("GPT-4o mini", "OpenAI",    0.15,  0.60),
    CloudModel("GPT-5.1",     "OpenAI",    1.25, 10.00),
]
CLOUD_MAP = {c.name: c for c in CLOUD_MODELS}


# ---------------------------------------------------------------------------
# Local models
# ---------------------------------------------------------------------------

LOCAL_MODELS = [
    LocalModel("LLaMA 3.1 8B",      "8B",   4.5,  "Entry-level"),
    LocalModel("Qwen3 30B",          "30B",  17,   "Mid-range"),
    LocalModel("LLaMA 3.1 70B",     "70B",  40,   "Sonnet-class"),
    LocalModel("GPT-OSS 120B",      "120B", 66,   "Opus-class (MoE)"),
    LocalModel("DeepSeek R1 671B",  "671B", 350,  "Frontier-class"),
]


# ---------------------------------------------------------------------------
# Benchmarks: (setup_short, model_name, tok/s, cloud_equivalent_name)
# 0 tok/s = cannot fit
# ---------------------------------------------------------------------------

BENCHMARKS = [
    Benchmark("A", "LLaMA 3.1 8B",      85,  "Haiku 4.5"),
    Benchmark("A", "Qwen3 30B",          30,  "Sonnet 4.5"),
    Benchmark("A", "LLaMA 3.1 70B",     14,  "Sonnet 4.5"),
    Benchmark("A", "GPT-OSS 120B",      20,  "Opus 4.5"),
    Benchmark("A", "DeepSeek R1 671B",  17,  "Opus 4.5"),  # Updated from 20 to 17 (fact-check: benchmarks show 16-18 t/s)

    Benchmark("B", "LLaMA 3.1 8B",      70,  "Haiku 4.5"),
    Benchmark("B", "Qwen3 30B",          22,  "GPT-4o"),
    Benchmark("B", "LLaMA 3.1 70B",      8,  "Sonnet 4.5"),
    Benchmark("B", "GPT-OSS 120B",      10,  "Opus 4.5"),
    Benchmark("B", "DeepSeek R1 671B",    0,  ""),  # cannot fit

    Benchmark("C", "LLaMA 3.1 8B",      38,  "Haiku 4.5"),  # Updated from 50 to 38 (NVIDIA blog)
    Benchmark("C", "Qwen3 30B",          20,  "Sonnet 4.5"),
    Benchmark("C", "LLaMA 3.1 70B",      6,  "Sonnet 4.5"),
    Benchmark("C", "GPT-OSS 120B",      50,  "Opus 4.5"),  # Updated from 38 to 50 (LMSYS/Ollama range)
    Benchmark("C", "DeepSeek R1 671B",    0,  ""),  # cannot fit

    Benchmark("D", "LLaMA 3.1 8B",     120,  "Haiku 4.5"),
    Benchmark("D", "Qwen3 30B",          35,  "Sonnet 4.5"),
    Benchmark("D", "LLaMA 3.1 70B",     13,  "Sonnet 4.5"),
    Benchmark("D", "GPT-OSS 120B",       0,  ""),  # cannot fit
    Benchmark("D", "DeepSeek R1 671B",    0,  ""),  # cannot fit
]


# ---------------------------------------------------------------------------
# Calculation constants
# ---------------------------------------------------------------------------

OUTPUT_RATIO = 0.70   # 70% of tokens are output tokens
INPUT_RATIO  = 0.30   # 30% are input tokens
HOURS_PER_DAY = 24
HOURS_PER_MONTH = 720  # 30 days
ELECTRICITY_RATE = 0.15  # $/kWh US average


# ---------------------------------------------------------------------------
# Core calculations
# ---------------------------------------------------------------------------

def weighted_price_per_mtok(cloud: CloudModel) -> float:
    """Weighted price per million tokens (70/30 output/input)."""
    return OUTPUT_RATIO * cloud.output_per_mtok + INPUT_RATIO * cloud.input_per_mtok


def tokens_per_hour(tok_sec: float) -> float:
    return tok_sec * 3600


def cloud_cost_per_hour(tok_hour: float, cloud: CloudModel) -> float:
    """Cloud cost per hour for the given throughput."""
    wp = weighted_price_per_mtok(cloud)
    return tok_hour * wp / 1_000_000


def payoff_hours(hw_cost: float, cloud_per_hour: float) -> float:
    if cloud_per_hour <= 0:
        return float('inf')
    return hw_cost / cloud_per_hour


def payoff_days(hours: float) -> float:
    return hours / HOURS_PER_DAY


def payoff_months(hours: float) -> float:
    return hours / HOURS_PER_MONTH


def electricity_cost_per_hour(watts: float) -> float:
    return (watts / 1000) * ELECTRICITY_RATE


# ---------------------------------------------------------------------------
# Risk-adjusted model (Section 8 of the post)
# ---------------------------------------------------------------------------

def monthly_multiplier(annual_decline_rate: float) -> float:
    """Monthly price multiplier given annual decline rate (e.g. 0.5 = 50%/yr)."""
    return (1 - annual_decline_rate) ** (1 / 12)


def cumulative_cloud_spend(c0_monthly: float, m: float, n_months: int) -> float:
    """Cumulative cloud spend over n months with price declining at rate m/month."""
    if abs(m - 1.0) < 1e-10:
        return c0_monthly * n_months
    return c0_monthly * (1 - m ** n_months) / (1 - m)


def max_lifetime_spend(c0_monthly: float, m: float) -> float:
    """Max total cloud spend avoided (infinite time horizon)."""
    if m >= 1.0:
        return float('inf')
    return c0_monthly / (1 - m)


def risk_adjusted_payoff_months(
    hw_cost: float,
    cloud_per_hour: float,
    annual_decline_rate: float,
    utilization: float = 1.0,
) -> float:
    """
    Find the number of months until cumulative cloud savings = hardware cost,
    given cloud price declines at annual_decline_rate and utilization factor.
    Returns float('inf') if it never pays back.
    """
    if cloud_per_hour <= 0 or utilization <= 0:
        return float('inf')

    c0_monthly = cloud_per_hour * HOURS_PER_MONTH * utilization
    m = monthly_multiplier(annual_decline_rate)

    # Check if hardware cost exceeds max possible savings
    max_savings = max_lifetime_spend(c0_monthly, m)
    if hw_cost >= max_savings:
        return float('inf')

    # Binary search for the month where cumulative >= hw_cost
    lo, hi = 0, 600  # up to 50 years
    for _ in range(100):
        mid = (lo + hi) / 2
        spent = cumulative_cloud_spend(c0_monthly, m, int(mid))
        if spent < hw_cost:
            lo = mid
        else:
            hi = mid
    return hi


# ---------------------------------------------------------------------------
# Output generators
# ---------------------------------------------------------------------------

def compute_all():
    """Compute all tables and return as structured data."""
    results = []

    for b in BENCHMARKS:
        if b.tokens_per_sec == 0:
            continue

        setup = SETUP_MAP[b.setup]
        cloud = CLOUD_MAP[b.cloud_equivalent]
        wp = weighted_price_per_mtok(cloud)
        tph = tokens_per_hour(b.tokens_per_sec)
        cph = cloud_cost_per_hour(tph, cloud)
        ph = payoff_hours(setup.price_usd, cph)
        pd = payoff_days(ph)
        pm = payoff_months(ph)
        elec = electricity_cost_per_hour(setup.power_watts)

        results.append({
            "setup_name": setup.name,
            "setup_short": setup.short,
            "model": b.model,
            "cloud_equivalent": cloud.name,
            "hardware_cost": setup.price_usd,
            "tokens_per_sec": b.tokens_per_sec,
            "tokens_per_hour": tph,
            "weighted_price_per_mtok": round(wp, 2),
            "cloud_cost_per_hour": round(cph, 4),
            "payoff_hours": round(ph, 0),
            "payoff_days": round(pd, 0),
            "payoff_months": round(pm, 1),
            "electricity_per_hour": round(elec, 4),
        })

    return results


def compute_risk_adjusted():
    """Compute risk-adjusted payoff for key scenarios."""
    scenarios = []
    decline_rates = [0.0, 0.25, 0.50, 0.80]
    utilizations = [1.0, 0.50, 0.25, 0.10]

    # Focus on key setups
    key_benchmarks = [
        b for b in BENCHMARKS
        if b.tokens_per_sec > 0
        and (
            (b.setup == "C" and b.model == "GPT-OSS 120B") or
            (b.setup == "B" and b.model == "Qwen3 30B") or
            (b.setup == "B" and b.model == "LLaMA 3.1 8B") or
            (b.setup == "D" and b.model == "LLaMA 3.1 8B") or
            (b.setup == "A" and b.model == "LLaMA 3.1 70B") or
            (b.setup == "A" and b.model == "DeepSeek R1 671B")
        )
    ]

    for b in key_benchmarks:
        setup = SETUP_MAP[b.setup]
        cloud = CLOUD_MAP[b.cloud_equivalent]
        tph = tokens_per_hour(b.tokens_per_sec)
        cph = cloud_cost_per_hour(tph, cloud)

        for dr in decline_rates:
            for util in utilizations:
                pm = risk_adjusted_payoff_months(
                    setup.price_usd, cph, dr, util
                )
                scenarios.append({
                    "setup": setup.name,
                    "setup_short": setup.short,
                    "model": b.model,
                    "cloud_equivalent": cloud.name,
                    "decline_rate_pct": int(dr * 100),
                    "utilization_pct": int(util * 100),
                    "payoff_months": round(pm, 1) if pm != float('inf') else "never",
                })

    return scenarios


def print_main_table(results):
    """Print the main payoff table in markdown."""
    print("\n## Main Payoff Table\n")
    print(
        "| Setup + Model | HW Cost | Tokens/hr | Cloud Equiv | "
        "Weighted $/MTok | Cloud $/hr | Payoff Hours | Payoff Days | "
        "Payoff Months |"
    )
    print(
        "|---|---|---|---|---|---|---|---|---|"
    )
    for r in results:
        print(
            f"| {r['setup_short']}: {r['setup_name'].split()[0]} + "
            f"{r['model']} | ${r['hardware_cost']:,.0f} | "
            f"{r['tokens_per_hour']:,.0f} | {r['cloud_equivalent']} | "
            f"${r['weighted_price_per_mtok']:.2f} | "
            f"${r['cloud_cost_per_hour']:.2f} | "
            f"{r['payoff_hours']:,.0f} | {r['payoff_days']:,.0f} | "
            f"**{r['payoff_months']:.1f}** |"
        )


def print_risk_table(scenarios):
    """Print a summary risk-adjusted table."""
    print("\n## Risk-Adjusted Payoff (months)\n")

    # Group by setup+model
    from itertools import groupby
    key_fn = lambda s: (s["setup_short"], s["model"])
    sorted_scenarios = sorted(scenarios, key=key_fn)

    for (short, model), group in groupby(sorted_scenarios, key=key_fn):
        items = list(group)
        setup_name = items[0]["setup"]
        cloud = items[0]["cloud_equivalent"]
        print(f"\n### {short}: {setup_name} + {model} (vs {cloud})\n")
        print("| Utilization | 0% decline | 25%/yr | 50%/yr | 80%/yr |")
        print("|---|---|---|---|---|")

        for util in [100, 50, 25, 10]:
            row = [f"{util}%"]
            for dr in [0, 25, 50, 80]:
                match = [
                    s for s in items
                    if s["decline_rate_pct"] == dr
                    and s["utilization_pct"] == util
                ]
                if match:
                    v = match[0]["payoff_months"]
                    row.append(str(v) if v != "never" else "never")
                else:
                    row.append("-")
            print(f"| {' | '.join(row)} |")


def print_electricity_impact(results):
    """Print electricity cost impact analysis."""
    print("\n## Electricity Cost Impact\n")
    print("| Setup | Power (W) | Elec $/hr | % of Cheapest Cloud $/hr |")
    print("|---|---|---|---|")

    seen = set()
    for r in results:
        if r["setup_short"] in seen:
            continue
        seen.add(r["setup_short"])
        setup = SETUP_MAP[r["setup_short"]]
        elec = electricity_cost_per_hour(setup.power_watts)
        # Find min cloud_cost_per_hour for this setup
        min_cph = min(
            x["cloud_cost_per_hour"]
            for x in results
            if x["setup_short"] == r["setup_short"]
        )
        pct = (elec / min_cph * 100) if min_cph > 0 else 0
        print(
            f"| {setup.name} | {setup.power_watts:.0f}W | "
            f"${elec:.3f} | {pct:.1f}% |"
        )


def main():
    print("=" * 80)
    print("LOCAL AI HARDWARE vs. CLOUD API: PAYOFF CALCULATOR")
    print("=" * 80)

    results = compute_all()
    print_main_table(results)

    print("\n" + "=" * 80)
    print("RISK-ADJUSTED SCENARIOS")
    print("=" * 80)

    scenarios = compute_risk_adjusted()
    print_risk_table(scenarios)

    print_electricity_impact(results)

    # Also output JSON for further processing
    output = {
        "main_results": results,
        "risk_adjusted": scenarios,
    }
    with open("payoff_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nJSON output written to payoff_results.json")

    # Summary statistics
    print("\n" + "=" * 80)
    print("KEY FINDINGS")
    print("=" * 80)

    sorted_results = sorted(results, key=lambda r: r["payoff_months"])
    print("\nTop 5 fastest payoff scenarios (100% utilization):")
    for i, r in enumerate(sorted_results[:5], 1):
        print(
            f"  {i}. {r['setup_short']}: {r['setup_name']} + {r['model']} "
            f"vs {r['cloud_equivalent']} -> "
            f"**{r['payoff_months']:.1f} months** "
            f"(${r['cloud_cost_per_hour']:.2f}/hr cloud cost)"
        )

    print("\nTop 5 slowest payoff scenarios:")
    for i, r in enumerate(sorted_results[-5:], 1):
        print(
            f"  {i}. {r['setup_short']}: {r['setup_name']} + {r['model']} "
            f"vs {r['cloud_equivalent']} -> "
            f"**{r['payoff_months']:.1f} months** "
            f"(${r['cloud_cost_per_hour']:.2f}/hr cloud cost)"
        )


if __name__ == "__main__":
    main()
