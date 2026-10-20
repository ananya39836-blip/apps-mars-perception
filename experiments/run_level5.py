"""Master Driver Script for APPS Level 5 Verification Pipeline.
Executes Level 4 backward regression, Level 5 evidence pipeline,
full 103-test automated assurance suite, and computes final Level 5 designation.
Seals output in results/level5/manifest_level5.json with SHA-256 signatures.
"""
import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from level1.evaluation.manifest import sha256_file
from level5.evaluation.label_script_l5 import release_gate_l5, level5_label, KEYS_L5


def run_pipeline_l5(smoke: bool = False):
    print("=" * 80)
    mode_str = "SMOKE TEST MODE (Fast)" if smoke else "FULL VERIFICATION MODE"
    print(f"APPS LEVEL 5: MASTER VERIFICATION PIPELINE [{mode_str}]")
    print("=" * 80)

    os.makedirs("results/level5", exist_ok=True)
    os.makedirs("docs", exist_ok=True)

    steps = [
        ("Step 1: Level 4 Milestone Backward Regression Audit", "python tools/assess_level4.py"),
        ("Step 2: Level 5 Evidence Generation Pipeline", "python tools/run_level5_evidence.py"),
        ("Step 3: Level 5 Automated Unit & Integration Tests (22 Tests)", "python -m pytest tests/test_level5.py -q"),
        ("Step 4: Master Regression & Multi-Level Test Suite (103 Tests)", "python -m pytest tests/ -q"),
        ("Step 5: Master Level 5 Evidence Assessment Engine", "python tools/assess_level5.py")
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

    # Build Level 5 manifest
    l5_files = [
        "results/level5/swarm_consensus_results.json",
        "results/level5/subsurface_cave_results.json",
        "results/level5/cryobot_ocean_results.json",
        "results/level5/astrobiology_biosignature_results.json",
        "results/level5/reconfigurable_robotics_results.json",
        "results/level5/isru_regolith_results.json",
        "results/level5/lasercom_dtn_results.json",
        "results/level5/quantum_enclave_results.json",
        "results/level5/continual_learning_results.json",
        "results/level5/planetary_protection_results.json",
        "results/level5/assessment_l5.json"
    ]
    manifest = {
        "pipeline": "run_level5",
        "mode": "smoke" if smoke else "full",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_duration_s": total_dur,
        "all_passed": all_passed,
        "steps": steps_log,
        "files_sealed": {}
    }

    for fpath in l5_files:
        if os.path.exists(fpath):
            manifest["files_sealed"][fpath] = {
                "sha256": sha256_file(fpath),
                "bytes": os.path.getsize(fpath)
            }

    # Verify release gate status
    with open("results/level5/assessment_l5.json") as fp:
        l5_assess = json.load(fp)

    gate_checks = {k: l5_assess["evidence"][k]["passed"] for k in KEYS_L5 if k in l5_assess["evidence"]}
    gate_status, unpassed = release_gate_l5(gate_checks)
    manifest["release_gate"] = gate_status
    manifest["unpassed_keys"] = unpassed
    manifest["level5_designation"] = l5_assess.get("computed_label", "L5-not-met")

    with open("results/level5/manifest_level5.json", "w") as fp:
        json.dump(manifest, fp, indent=2)

    print("\n" + "=" * 80)
    print(f">> Level 5 Pipeline Sealed Manifest Generated: results/level5/manifest_level5.json")
    print(f">> Total Verification Duration: {total_dur}s")
    print(f">> Release Gate: {gate_status.upper()}")
    print(f">> Final Milestone Designation: {manifest['level5_designation']}")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master APPS Level 5 Pipeline Runner")
    parser.add_argument("--smoke", action="store_true", help="Run fast verification mode")
    args = parser.parse_args()
    run_pipeline_l5(smoke=args.smoke)
