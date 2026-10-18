"""Master Driver Script for APPS Level 1 Verification Pipeline.
Supports both --smoke and --full modes.
Ensures exit code is 0 on successful verification.
Task 50 / Task 88.
"""
import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from level1.evaluation.manifest import sha256_file, build_manifest


def run_pipeline(smoke: bool = False):
    print("=" * 70)
    mode_str = "SMOKE TEST MODE (Fast)" if smoke else "FULL VERIFICATION MODE"
    print(f"APPS LEVEL 1: MASTER VERIFICATION PIPELINE [{mode_str}]")
    print("=" * 70)

    os.makedirs("results", exist_ok=True)
    os.makedirs("results/level1", exist_ok=True)
    os.makedirs("docs", exist_ok=True)

    steps = [
        ("Phase 1: Repository Audit & README Claims", "python tools/run_audit.py"),
        ("Phase 1: Mechanical Information Boundary Mutation Test", "python tools/run_boundary_tests.py"),
        ("Phase 2: Uncertainty-Aware Cost Map & Mission Loop (E23/Watchdogs)", "python tools/run_phase2.py"),
        ("Phase 3: E13 Baseline Benchmark & Statistical Discipline", "python tools/run_phase3_e13.py"),
        ("Phase 4: Worst-Case Failure Analysis (20 Scenes)", "python tools/generate_failure_review.py"),
        ("Phase 5: Automated Unit & Integration Test Suite", "python -m pytest tests/test_level1.py tests/test_all.py -q"),
    ]

    pipeline_log = {
        "pipeline": "run_level1",
        "mode": "smoke" if smoke else "full",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "steps": [],
        "all_passed": True
    }

    t_start = time.time()
    for name, cmd in steps:
        print(f"\n>> [EXECUTING] {name}")
        t0 = time.time()
        res = subprocess.run(cmd, shell=True, capture_output=False)
        dur = round(time.time() - t0, 2)
        passed = (res.returncode == 0)
        pipeline_log["steps"].append({
            "name": name,
            "command": cmd,
            "returncode": res.returncode,
            "duration_s": dur,
            "passed": passed
        })
        if not passed:
            print(f"[FAIL] {name} failed with exit code {res.returncode}")
            pipeline_log["all_passed"] = False
            sys.exit(res.returncode)
        else:
            print(f"[PASS] {name} completed successfully in {dur}s")

    total_time = round(time.time() - t_start, 2)
    pipeline_log["total_duration_s"] = total_time

    # Record execution log for requirement 11 ('tests_executed')
    with open("results/test_execution.log", "w") as f:
        f.write(f"APPS Level 1 Pipeline Execution Log\n")
        f.write(f"Timestamp: {pipeline_log['timestamp']}\n")
        f.write(f"Mode: {pipeline_log['mode']}\n")
        f.write(f"Total Duration: {total_time}s\n")
        f.write(f"All Steps Passed: {pipeline_log['all_passed']}\n")
        for step in pipeline_log["steps"]:
            f.write(f" - {step['name']}: ReturnCode={step['returncode']} ({step['duration_s']}s)\n")

    # Update manifest
    manifest_files = [
        "docs/INITIAL_TECHNICAL_AUDIT.md",
        "docs/README_CLAIMS.md",
        "docs/SAFETY_AND_FAILURE_ANALYSIS.md",
        "docs/FAILURE_REVIEW.md",
        "docs/TRACEABILITY.md",
        "results/boundary_tests.json",
        "results/weight_ablation_E23.json",
        "results/mission_traces.json",
        "results/stale_map_test.json",
        "results/outcome_tests.json",
        "results/perception_run.json",
        "results/E13_results.json",
        "results/failure_review.json",
        "results/test_execution.log"
    ]
    manifest = {
        "pipeline_version": "1.0-level1",
        "timestamp": pipeline_log["timestamp"],
        "checksums": {}
    }
    for mf in manifest_files:
        if os.path.exists(mf):
            manifest["checksums"][mf] = sha256_file(mf)
    with open("results/manifest.json", "w") as f:
        json.dump(manifest, f, indent=1)

    print("\n" + "=" * 70)
    print(f">> MASTER PIPELINE SUCCESSFUL (Duration: {total_time}s)")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run APPS Level 1 Verification Pipeline")
    parser.add_argument("--smoke", "-s", action="store_true", help="Run in smoke test mode")
    parser.add_argument("--mode", type=str, default="full", choices=["smoke", "full"], help="Pipeline execution mode")
    args = parser.parse_args()
    
    is_smoke = args.smoke or (args.mode == "smoke")
    rc = run_pipeline(smoke=is_smoke)
    sys.exit(rc)
