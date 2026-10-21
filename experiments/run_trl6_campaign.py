"""Master NASA TRL 6 Planetary Rover Validation Campaign Runner.

Executes:
1. 20 Standardized Scenario Classes across deterministic multi-seed Monte Carlo trials
2. Comparative Baselines (Straight-Line, 2D Grid A*, Terrain A*, Kinodynamic Hybrid A*)
3. Algorithmic Ablation Studies (Slope, Dynamic Updates, Replanning, Sensor Fusion)
4. Telemetry packaging into machine-readable JSON manifests in results/trl6/
"""
from __future__ import annotations
import os
import sys
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from trl6_navigation import PROTOTYPE_LOCK, NAVIGATION_READY, SCENARIO_CLASSES
from trl6_navigation.experiments.campaign_runner import CampaignRunner
from trl6_navigation.experiments.baselines import ComparativeBaselinesRunner
from trl6_navigation.experiments.ablations import AblationRunner


def main() -> None:
    print("=" * 80)
    print("APPS NASA TRL 6 INTEGRATED PLANETARY ROVER VALIDATION CAMPAIGN")
    print(f"Operational Lock: PROTOTYPE_LOCK = {PROTOTYPE_LOCK} | Navigation: READY = {NAVIGATION_READY}")
    print("=" * 80)

    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "results", "trl6"))
    os.makedirs(output_dir, exist_ok=True)

    # 1. Standardized 20-Scenario Campaign
    print(f"\n[1/3] Executing {len(SCENARIO_CLASSES)} Standardized Scenario Classes (3 seeds/scenario = 60 closed-loop trials)...")
    runner = CampaignRunner(output_dir=output_dir, seeds_count=3, base_seed=100)
    campaign_res = runner.run_full_campaign()

    print("\n" + "-" * 80)
    print(f"{'Scenario ID':<30} | {'Runs':<5} | {'Pass Rate':<10} | {'95% CI':<15} | {'Collisions':<10} | {'ATE (m)':<8}")
    print("-" * 80)
    for sc_id, summary in campaign_res["summaries"].items():
        ci_str = f"[{summary['wilson_ci_95'][0]}%, {summary['wilson_ci_95'][1]}%]"
        print(f"{sc_id:<30} | {summary['total_runs']:<5} | {summary['success_rate_pct']:<8} % | {ci_str:<15} | {summary['total_collisions']:<10} | {summary['mean_ate_rmse_m']:<8}")
    print("-" * 80)

    # 2. Comparative Baselines
    print("\n[2/3] Executing Comparative Baselines...")
    base_runner = ComparativeBaselinesRunner(output_dir=output_dir)
    base_res = base_runner.run_comparative_benchmark(seed=100)
    print("\n" + "=" * 80)
    print("RUNNING COMPARATIVE BASELINES BENCHMARK (SC-04 Dense Obstacle Field)")
    print("=" * 80)
    for name, data in base_res["baselines"].items():
        print(f" - {name:<35} : Success={data['success']}, Collisions={data['collisions']}, Length={data['path_length_m']}m, Latency={data['latency_ms']}ms")

    # 3. Ablation Studies
    print("\n[3/3] Executing Ablation Studies...")
    abl_runner = AblationRunner(output_dir=output_dir)
    abl_res = abl_runner.run_all_ablations(seed=100)
    print("\n" + "=" * 80)
    print("RUNNING ABLATION STUDIES (SC-04 Dense Obstacle Field)")
    print("=" * 80)
    for name, data in abl_res.items():
        print(f" - {name:<35} : Success={data['success']}, Reason={data['failure_reason']}, Collisions={data['collision_count']}, ATE={data['ate_rmse_m']}m")

    print("\n" + "=" * 80)
    print(f"TRL 6 VALIDATION CAMPAIGN COMPLETE — EVIDENCE PACKAGED IN {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
