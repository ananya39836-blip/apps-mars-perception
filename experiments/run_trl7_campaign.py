"""TRL 7 Operational Validation Campaign Execution Script.

Executes standardized Monte-Carlo experiments across operational scenarios,
performs ablation comparisons, and produces reproducible evidence packages
in results/trl7/.
"""
from __future__ import annotations
import os
import sys
import json
import time

# Ensure repository root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from trl7_navigation.experiments.campaign_runner import CampaignRunner
from trl7_navigation.experiments.ablations import AblationStudyRunner


def main() -> None:
    print("================================================================================")
    print("   APPS: AUTOMATED PLANETARY PERCEPTION SYSTEM (TRL 7 VALIDATION CAMPAIGN)")
    print("================================================================================")
    out_dir = os.path.join(os.path.dirname(__file__), "..", "results", "trl7")
    os.makedirs(out_dir, exist_ok=True)

    runner = CampaignRunner(output_dir=out_dir)

    # Execute validation campaign across all 20 standardized scenario classes
    print("\n[Phase 1/2] Executing 20-Scenario Monte-Carlo Validation Campaign...")
    summary = runner.run_full_campaign(seeds=[42, 101], verbose=True)

    # Execute ablation benchmark
    print("\n[Phase 2/2] Executing Ablation Benchmarks...")
    ablation_res = AblationStudyRunner.run_ablation_comparison("SC-02_moderate_slopes", seed=42)
    ablation_path = os.path.join(out_dir, "ablation_study.json")
    with open(ablation_path, "w", encoding="utf-8") as f:
        json.dump(ablation_res, f, indent=2)
    print(f"Ablation study saved to {ablation_path}")

    print("\n================================================================================")
    print(f" CAMPAIGN COMPLETE: Overall Success Rate = {summary['overall_success_rate']*100:.1f}%")
    print(f" 95% Wilson Confidence Interval: [{summary['overall_wilson_ci_95'][0]*100:.1f}% - {summary['overall_wilson_ci_95'][1]*100:.1f}%]")
    print(f" Total Simulation Runs: {summary['total_runs']}")
    print(f" Output Artifacts: {out_dir}")
    print("================================================================================")


if __name__ == "__main__":
    main()
