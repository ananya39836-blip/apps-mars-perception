"""Master Driver Script for APPS Level 4 Verification Pipeline.
Executes Level 3 backward regression, Level 4 evidence pipeline,
full 81-test automated assurance suite, and computes final Level 4 designation.
Seals output in results/level4/manifest_level4.json with SHA-256 signatures.
"""
import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from level1.evaluation.manifest import sha256_file
from level4.evaluation.label_script_l4 import release_gate_l4, level4_label, KEYS_L4


def run_pipeline_l4(smoke: bool = False):
    print("=" * 80)
    mode_str = "SMOKE TEST MODE (Fast)" if smoke else "FULL VERIFICATION MODE"
    print(f"APPS LEVEL 4: MASTER VERIFICATION PIPELINE [{mode_str}]")
    print("=" * 80)

    os.makedirs("results/level4", exist_ok=True)
    os.makedirs("docs", exist_ok=True)

    steps = [
        ("Step 1: Level 3 Milestone Backward Regression Audit", "python tools/assess_level3.py"),
        ("Step 2: Level 4 Evidence Generation Pipeline", "python tools/run_level4_evidence.py"),
        ("Step 3: Level 4 Automated Unit & Integration Tests", "python -m pytest tests/test_level4.py -q"),
        ("Step 4: Master Regression & Multi-Level Test Suite (81 Tests)", "python -m pytest tests/ -q"),
        ("Step 5: Master Level 4 Evidence Assessment Engine", "python tools/assess_level4.py")
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

    # Build Level 4 manifest
    l4_files = [
        "results/level4/hierarchical_nav_results.json",
        "results/level4/aegis_science_results.json",
        "results/level4/extreme_mobility_results.json",
        "results/level4/multi_agent_results.json",
        "results/level4/adaptive_terramechanics_results.json",
        "results/level4/neuromorphic_results.json",
        "results/level4/mission_executive_results.json",
        "results/level4/environmental_survival_results.json",
        "results/level4/lost_in_space_results.json",
        "results/level4/hil_assurance_results.json",
        "results/level4/assessment_l4.json"
    ]
    manifest = {
        "pipeline": "run_level4",
        "mode": "smoke" if smoke else "full",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_duration_s": total_dur,
        "all_passed": all_passed,
        "steps": steps_log,
        "files_sealed": {}
    }

    for fpath in l4_files:
        if os.path.exists(fpath):
            manifest["files_sealed"][fpath] = {
                "sha256": sha256_file(fpath),
                "bytes": os.path.getsize(fpath)
            }

    # Verify release gate status
    with open("results/level4/assessment_l4.json") as fp:
        l4_assess = json.load(fp)

    gate_checks = {k: l4_assess["evidence"][k]["passed"] for k in KEYS_L4 if k in l4_assess["evidence"]}
    gate_status, unpassed = release_gate_l4(gate_checks)
    manifest["release_gate"] = gate_status
    manifest["unpassed_keys"] = unpassed
    manifest["level4_designation"] = l4_assess.get("computed_label", "L4-not-met")

    manifest_path = "results/level4/manifest_level4.json"
    with open(manifest_path, "w") as fp:
        json.dump(manifest, fp, indent=2)

    print("\n" + "=" * 80)
    print(f">> Level 4 Master Pipeline Completed in {total_dur}s")
    print(f">> Final Milestone Designation: {manifest['level4_designation']}")
    print(f">> Release Gate: {manifest['release_gate']}")
    print(f">> SHA-256 Manifest Sealed: {manifest_path}")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Level 4 Master Verification Pipeline")
    parser.add_argument("--smoke", action="store_true", help="Run in fast smoke mode")
    args = parser.parse_args()
    run_pipeline_l4(smoke=args.smoke)
