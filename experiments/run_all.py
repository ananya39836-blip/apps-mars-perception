"""Master reproducible driver script.
Regenerates trained model, evaluation, follow-up experiments, planner selection and runs tests.
Appendix O.2 (Part 3) & Chapter 46.
"""
import subprocess
import sys
import json
import hashlib
import pathlib
import time


STEPS = [
    ("Train APPS-0.1 and Run Evaluation", "python apps01.py 250"),
    ("Run Part 2 Follow-up Experiments", "python experiments.py"),
    ("Run Planner Selection (Task 2 & 22)", "python experiments/select_planner.py"),
    ("Run Full Pytest Test Suite", "python -m pytest tests/test_all.py -v"),
]


def sha256(path):
    p = pathlib.Path(path)
    if not p.exists():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(mode="full"):
    print("=" * 60)
    print("APPS: Automated Planetary Perception System - Pipeline Driver")
    print(f"Mode: {mode}")
    print("=" * 60)
    
    pathlib.Path("results").mkdir(exist_ok=True)
    manifest = dict(
        mode=mode,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        steps=[],
        config_sha=sha256("configs/cfg.yaml")
    )
    
    for name, cmd in STEPS:
        print(f"\n[STEP] Running: {name}")
        print(f"Command: {cmd}")
        t0 = time.time()
        rc = subprocess.call(cmd, shell=True)
        dur = round(time.time() - t0, 2)
        manifest["steps"].append(dict(name=name, command=cmd, returncode=rc, duration_s=dur))
        if rc != 0:
            print(f"ERROR: Step '{name}' failed with return code {rc}")
            break
        else:
            print(f"[OK] Completed '{name}' in {dur}s")

    manifest["model_sha256"] = sha256("apps01_model.pkl")
    manifest["evaluation_results_sha256"] = sha256("evaluation_results.json")
    manifest["experiments_results_sha256"] = sha256("experiments_results.json")
    
    with open("results/manifest.json", "w") as f:
        json.dump(manifest, f, indent=1)
        
    print("\n" + "=" * 60)
    print("Pipeline Execution Completed. Manifest saved to results/manifest.json")
    print("=" * 60)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "full")
