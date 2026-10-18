"""Task 42: Information Boundary Mutation Tests.
Enforces Chapter 91 Information Boundary and saves results to results/boundary_tests.json.
"""
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from level1.mission.simulator import Simulator
from level1.mission.loop import run_mission


def run_mutation_tests():
    # 1. Base world: 16x16 with vertical obstacle barrier at col 8
    n = 16
    truth = np.zeros((n, n), bool)
    truth[4:12, 8] = True  # barrier with passages top and bottom
    
    cfg = dict(
        sense=True,
        sensor=dict(fov_deg=90.0, range=8.0, miss0=0.0, miss_slope=0.0, false_alarm=0.0),
        w=dict(d=1.0, r=3.0, u=1.0, r_block=0.3, u_block=0.35, p_budget=0.50),
        h_weight=1.5,
        fuse="union"
    )
    
    # Run unmutated mission
    sim_base = Simulator(truth)
    res_base = run_mission(sim_base, cfg, np.random.default_rng(101), start=(0, 0), max_steps=50)
    base_trace = [step["pos"] for step in res_base["log"]]
    
    # 2. Mutate UNSEEN cells (far corner (15, 0) and (15, 1))
    truth_unseen = truth.copy()
    truth_unseen[15, 0] = True
    truth_unseen[15, 1] = True
    sim_unseen = Simulator(truth_unseen)
    res_unseen = run_mission(sim_unseen, cfg, np.random.default_rng(101), start=(0, 0), max_steps=50)
    unseen_trace = [step["pos"] for step in res_unseen["log"]]
    
    # Invariant 1: Unseen mutation must produce 100% identical trajectory and outcome
    unseen_identical = (
        (res_base["outcome"] == res_unseen["outcome"]) and
        (res_base["steps"] == res_unseen["steps"]) and
        (base_trace == unseen_trace)
    )
    
    # 3. Mutate ON-ROUTE cell (step 3 of base path)
    on_route_cell = base_trace[3]
    truth_on_route = truth.copy()
    truth_on_route[on_route_cell[0], on_route_cell[1]] = True
    sim_on_route = Simulator(truth_on_route)
    res_on_route = run_mission(sim_on_route, cfg, np.random.default_rng(101), start=(0, 0), max_steps=50)
    on_route_trace = [step["pos"] for step in res_on_route["log"]]
    
    # Invariant 2: On-route mutation must alter trajectory or cause discovery replan
    on_route_different = (base_trace != on_route_trace) or (res_on_route["discovered"] > 0)
    
    results = dict(
        test_id="T17_information_boundary_mutation",
        unseen_mutation_identical=bool(unseen_identical),
        on_route_mutation_diverged=bool(on_route_different),
        base_steps=res_base["steps"],
        base_outcome=res_base["outcome"],
        unseen_steps=res_unseen["steps"],
        unseen_outcome=res_unseen["outcome"],
        on_route_steps=res_on_route["steps"],
        on_route_outcome=res_on_route["outcome"],
        status="passed" if (unseen_identical and on_route_different) else "failed"
    )
    
    os.makedirs("results", exist_ok=True)
    out_file = "results/boundary_tests.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=1)
        
    print(f"Boundary mutation test complete: status={results['status']}. Written to {out_file}", flush=True)
    return results


if __name__ == "__main__":
    run_mutation_tests()
