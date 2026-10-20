# APPS Planetary Rover Autonomous Navigation System — Reproducibility & Execution Guide

**Document ID:** APPS-REP-TRL5-005  
**Target Maturity:** NASA TRL 5  
**Environment Requirements:** Python 3.10+ / 3.14 compatible, Windows / Linux / macOS.

---

## 1. Quick Start Commands

All experiments, benchmarks, unit tests, and the interactive Streamlit dashboard can be reproduced with single-line terminal commands.

### 1.1 Automated Full Test Suite (100% Pass)
```bash
# Execute complete unit test suite across all subsystems (200 tests)
python -m pytest tests -v
```

### 1.2 Master Validation Campaign (15 Scenarios + Baselines + Ablations)
```bash
# Runs full multi-seed campaign, comparative baselines, and ablation studies
python experiments/run_trl5_campaign.py
```
This script executes:
1. 15 standardized scenario classes $\times$ 3 seeds = 45 closed-loop trials.
2. 4 comparative baselines (Straight-Line, 2D Grid A*, Terrain A*, Proposed Kinodynamic Hybrid A*).
3. 5 ablation conditions (No slope cost, No dynamic obstacle map, No replanning, No EKF, Oracle).
4. Generates output JSON evidence in `results/trl5/`:
   - `results/trl5/campaign_summary.json`
   - `results/trl5/campaign_manifest.json`
   - `results/trl5/baseline_comparison.json`
   - `results/trl5/ablation_study.json`

### 1.3 Interactive Streamlit V&V Dashboard
```bash
# Launch interactive 3D mission control and verification dashboard
streamlit run apps_trl5_dashboard.py
```

---

## 2. Programmatic Python Execution

To execute an individual trial programmatically from Python:

```python
from trl5_navigation.experiments.campaign_runner import CampaignRunner

# Initialize runner
runner = CampaignRunner(output_dir="results/trl5")

# Run trial on moderate slopes with deterministic seed
trial = runner.run_single_trial("SC-02_moderate_slopes", seed=100)

print(f"Outcome: {trial['failure_reason']}")
print(f"Final Mode: {trial['final_operating_mode']}")
print(f"Collisions: {trial['collision_count']}")
print(f"Traverse Duration: {trial['sim_duration_s']} s")
print(f"Localization ATE RMSE: {trial['ate_rmse_m']:.3f} m")
print(f"Mean Planning Latency: {trial['mean_planning_latency_ms']:.2f} ms")
```

---

## 3. Deterministic Seed Schedule

To ensure bit-for-bit exact reproducibility across platforms:

| Trial Index | PRNG Seed | Scenario Classes Tested |
| :--- | :--- | :--- |
| Seed 1 | `100` | SC-01 through SC-15 |
| Seed 2 | `117` | SC-01 through SC-15 |
| Seed 3 | `134` | SC-01 through SC-15 |

All PRNG instances use NumPy's `np.random.default_rng(seed)` generator.
