"""Master Driver Script for APPS Level 6 Verification Pipeline.
Executes Level 5 backward regression, Level 6 evidence pipeline,
full 125-test automated assurance suite, and computes final Level 6 designation.
Seals output in results/level6/manifest_level6.json with SHA-256 signatures.
"""
import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from level1.evaluation.manifest import sha256_file
from level6.evaluation.label_script_l6 import release_gate_l6, level6_label, KEYS_L6


def run_pipeline_l6(smoke: bool = False):
    print("=" * 80)
    mode_str = "SMOKE TEST MODE (Fast)" if smoke else "FULL VERIFICATION MODE"
    print(f"APPS LEVEL 6: MASTER VERIFICATION PIPELINE [{mode_str}]")
    print("=" * 80)

    os.makedirs("results/level6", exist_ok=True)
    os.makedirs("docs", exist_ok=True)

    steps = [
        ("Step 1: Level 5 Milestone Backward Regression Audit", "python tools/assess_level5.py"),
        ("Step 2: Level 6 Evidence Generation Pipeline", "python tools/run_level6_evidence.py"),
        ("Step 3: Level 6 Automated Unit & Integration Tests (22 Tests)", "python -m pytest tests/test_level6.py -q"),
        ("Step 4: Master Regression & Multi-Level Test Suite (125 Tests)", "python -m pytest tests/ -q"),
        ("Step 5: Master Level 6 Evidence Assessment Engine", "python tools/assess_level6.py")
    ]

    t_start = time.time()
    steps_log = []
    all_passed = True

    for name, cmd in steps:
        print(f"\n>> [EXECUTING] {name}")
        t0 = time.time()
        res = subprocess.run(cmd, shell=True)
        dur = round(time.time() - t0, 2)
        passed = (res.returncode == 0)
        steps_log.append({
            "name": name,
            "command": cmd,
            "returncode": res.returncode,
            "duration_s": dur,
            "passed": passed
        })
        if not passed:
            print(f"[FAIL] {name} failed with exit code {res.returncode}")
            all_passed = False
            sys.exit(res.returncode)
        else:
            print(f"[PASS] {name} completed successfully in {dur}s")

    total_dur = round(time.time() - t_start, 2)

    # Build Level 6 manifest
    l6_files = [
        "results/level6/interplanetary_nav_results.json",
        "results/level6/lunar_infrastructure_results.json",
        "results/level6/titan_nautical_results.json",
        "results/level6/deep_drilling_results.json",
        "results/level6/venus_avionics_results.json",
        "results/level6/asteroid_defense_results.json",
        "results/level6/biohybrid_sensor_results.json",
        "results/level6/quantum_comm_results.json",
        "results/level6/self_replication_results.json",
        "results/level6/galactic_biosecurity_results.json",
        "results/level6/assessment_l6.json"
    ]
    manifest = {
        "pipeline": "run_level6",
        "mode": "smoke" if smoke else "full",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_duration_s": total_dur,
        "all_passed": all_passed,
        "steps": steps_log,
        "files_sealed": {}
    }

    for fpath in l6_files:
        if os.path.exists(fpath):
            manifest["files_sealed"][fpath] = {
                "sha256": sha256_file(fpath),
                "bytes": os.path.getsize(fpath)
            }

    # Verify release gate status
    with open("results/level6/assessment_l6.json") as fp:
        l6_assess = json.load(fp)

    gate_checks = {k: l6_assess["evidence"][k]["passed"] for k in KEYS_L6 if k in l6_assess["evidence"]}
    gate_status, unpassed = release_gate_l6(gate_checks)
    manifest["release_gate"] = gate_status
    manifest["unpassed_keys"] = unpassed
    manifest["level6_designation"] = l6_assess.get("computed_label", "L6-not-met")

    with open("results/level6/manifest_level6.json", "w") as fp:
        json.dump(manifest, fp, indent=2)

    print("\n" + "=" * 80)
    print(f">> Level 6 Pipeline Sealed Manifest Generated: results/level6/manifest_level6.json")
    print(f">> Total Verification Duration: {total_dur}s")
    print(f">> Release Gate: {gate_status.upper()}")
    print(f">> Final Milestone Designation: {manifest['level6_designation']}")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master APPS Level 6 Pipeline Runner")
    parser.add_argument("--smoke", action="store_true", help="Run fast verification mode")
    args = parser.parse_args()
    run_pipeline_l6(smoke=args.smoke)
