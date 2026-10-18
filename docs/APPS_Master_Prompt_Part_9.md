# APPS Master Prompt, Part 9

**Level 1, Volume 4 of 5: Experiments E13 onward: pre-registrations, sizing, statistics, report generation from files**

*Continues Part 8 (chapters 128 to 148, appendices BF to BP). Chapters 149 to 169 and appendices BQ to CA.*

> **Synthetic-data research prototype, not flight software.** Part 9 contains no new experimental results. "Level 1" is an internal project milestone, not a NASA classification, and nothing here implies NASA affiliation, endorsement, certification or flight qualification. Part 9 establishes the formal experimental protocols, sample sizing power calculations, seed management, pre-registration notes, and automated report generation engines for Level 1 benchmarks.

---

## Chapter 149. Status, Scope and Reading Rules

### 149.1 Why Part 9 exists
A machine learning experiment without statistical rigor produces misleading claims. When a system records zero collisions over 40 trials, the true underlying collision rate could easily be as high as 7.5% (Rule of Three). Part 9 operationalizes statistical discipline across all Level 1 experiments: it provides sample sizing rules, cryptographic pre-registration mechanisms, cluster bootstrap procedures for non-independent episodes, and automated script-driven report generation to prevent human transcription drift.

### 149.2 Current state, restated from Part 8
- Benchmark systems are formalized: Fixed-route (F), Oracle (O), Known-map (K0/K1), Classical (A), Standard ML (B), and APPS Proposed (C).
- Simulator and rover models are isolated behind the Chapter 91 Information Boundary.
- The unit of analysis is established: the scene is the cluster; multiple episodes originating from the same terrain are non-independent.

### 149.3 Scope of Volume 4
- **Experiment E13**: Closed-loop multi-system baseline comparison under varying terrain difficulties (D0 to D5).
- **Experiment E14**: Full systematic ablation program isolating cost terms ($w_r, w_u, w_e$), footprint inflation ($r_{fp}$), and fusion mechanisms.
- **Experiment E15**: Mission-level fault injection campaign (sensor outages, pose error sweeps, depth dropout).
- **Experiment E16 & E17**: Perception calibration transfer study and terrain difficulty ladder benchmarking.
- **Statistical Procedures**: Cluster bootstrap resampling, Wilson score confidence intervals, paired per-episode differences, and automated table generation.

---

## Chapter 150. Task Register for Part 9

| Task | Deliverable | Primary Metric / Output to Report | Status |
|---|---|---|---|
| **71** | Seed Registry v2 generator & disjointness validator | Unique seed count per split; 0 hash collisions | Not started |
| **72** | Sample sizing power calculator script | Required sample size $N$ for target interval half-widths | Not started |
| **73** | Pre-registration note compiler & hash locker | Pre-registration note SHA-256 committed prior to run | Not started |
| **74** | Experiment E13 master driver script | Full baseline table with cluster bootstrap 95% CIs | Not started |
| **75** | Experiment E14 ablation suite driver | Ablation table isolating weights, footprint, and gates | Not started |
| **76** | Experiment E15 fault injection campaign driver | Fault impact matrix (outage, pose error, blackout) | Not started |
| **77** | Cluster bootstrap & paired statistical engine | Mean, lower bound, upper bound, win/loss/tie counts | Not started |
| **78** | Wilson score & Rule-of-Three estimator for rare events | Upper bound estimates for zero-event outcomes | Not started |
| **79** | Automated LaTeX & Markdown report table builder | Generated report tables directly from raw JSON files | Not started |
| **80** | Results file integrity and verification harness | Checksum verification of all raw experiment JSON records | Not started |

---

## Chapter 151. Statistical Power and Sample Sizing (Task 71 & 72)

### 151.1 The Unit of Analysis: The Scene
Pixels within a single scene are spatially auto-correlated, and multiple navigation runs on the same terrain share identical topography. Therefore, the scene is the fundamental cluster unit. Resampling must occur across scenes, never across individual episodes or pixels.

### 151.2 Sizing Formula for Binary Rates
To bound the half-width $w$ of a 95% confidence interval for a binary success or refusal rate near $p = 0.5$:
$$N \ge \left\lceil \frac{z^2 \cdot p(1 - p)}{w^2} \right\rceil = \left\lceil \frac{1.96^2 \cdot 0.25}{w^2} \right\rceil \approx \left\lceil \frac{0.96}{w^2} \right\rceil$$
- Target half-width $w = 0.05$ (5 percentage points) $\implies N \approx 385\text{ scenes}$.
- Target half-width $w = 0.07$ (7 percentage points) $\implies N \approx 200\text{ scenes}$.
- Target half-width $w = 0.10$ (10 percentage points) $\implies N \approx 97\text{ scenes}$.

### 151.3 Bounding Zero-Event Rates (Rule of Three)
When zero collisions are observed across $N$ independent scenes:
$$\text{Upper 95\% Bound} \approx \frac{3}{N}$$
For $N = 60\text{ scenes}$, zero collisions implies the true rate is bounded only below $5.0\%$. For $N = 200\text{ scenes}$, the bound tightens to $1.5\%$. Statements claiming "zero collisions proves safety" are mathematically false and strictly forbidden.

---

## Chapter 152. Seed Registry v2 and Provenance (Task 71)

### 152.1 Hierarchical Seed Derivation
To prevent subtle test set leakage across experiments, all seeds are derived cryptographically from a master root seed using NumPy `SeedSequence`:
$$\text{seed}_i = \text{SeedSequence}(\text{root}, \text{purpose\_string}).\text{spawn}(N)[i]$$

### 152.2 Registry Allocation Table
```json
{
  "root": 20261018,
  "purposes": {
    "train_v2": 250,
    "val_nominal_v2": 100,
    "val_novel_v2": 100,
    "test_nominal_v2": 200,
    "test_novel_v2": 200,
    "fault_injection_v2": 100,
    "ablation_v2": 100
  }
}
```

---

## Chapter 153. Pre-Registration Framework (Task 73)

### 153.1 Immutability Protocol
Before any test script touches a test seed range:
1. The research team drafts a `PRE_REGISTRATION_NOTE.md` specifying the hypothesis, candidate models, frozen parameters, sample size, primary metrics, and outcome branches.
2. The file is committed to git and its SHA-256 hash is computed.
3. The test runner checks the file hash against the committed repository state. If the hash differs or uncommitted changes exist, the test script aborts.

### 153.2 Outcome Branches (A through E)
- **Branch A**: System C maintains zero collisions with significantly reduced refusal rates ($p < 0.05$). *Allowed Claim*: Uncertainty-aware planning improves availability without sacrificing safety on synthetic terrain.
- **Branch B**: Availability improves but collisions appear. *Allowed Claim*: Higher block fractions relax ground-truth hazard bounds and induce safety failures.
- **Branch C**: Availability fails to improve. *Allowed Claim*: Planner refusals are driven by intrinsic terrain density rather than perceptual conservatism.
- **Branch D**: Feasibility filtering skips > 30% of scenes. *Allowed Claim*: Benchmark environment is excessively cluttered; findings apply only to feasible sub-domain.
- **Branch E**: No candidate configuration meets the collision constraint on validation. *Allowed Claim*: Operating point selection failed; Level 1 milestone is not met.

---

## Chapter 154. Experiment E13: Closed-Loop Baseline Comparison (Task 74)

### 154.1 Objective
Quantify the navigation performance and safety benefits of APPS System C relative to baselines (F, O, K0, K1, A, B) across Difficulty Levels D0 to D5.

### 154.2 Protocol
- Scene count: 200 nominal scenes, 200 novel-terrain scenes.
- 3 random start rows per scene $\implies 600$ attempted episodes per system per condition.
- Clustering: Standard errors clustered at the scene level using `boot_clusters()`.

---

## Chapter 155. Experiment E14: Systematic Ablation Program (Task 75)

### 155.1 Component Isolation Matrix
Each ablation run modifies exactly one parameter from the frozen System C baseline:

| Ablation ID | Component Varied | Alternative Setting | Primary Evaluated Effect |
|---|---|---|---|
| **E14-01** | Risk weight $w_r$ | $w_r = 0$ (no risk cost) | Path clearance from obstacle margins |
| **E14-02** | Uncertainty weight $w_u$ | $w_u = 0$ (no uncertainty cost) | Traversal through unfamiliar terrain |
| **E14-03** | Route rejection $p_{budget}$ | Disabled ($p_{budget} = \infty$) | Mission arrival vs collision rate |
| **E14-04** | Footprint radius $r_{fp}$ | $r_{fp} = 0$ (point robot) | Grazing collisions on rock boundaries |
| **E14-05** | Map Fusion Rule | `latest` frame instead of `union` | Susceptibility to late perceptual misses |
| **E14-06** | Frontier Fallback | Disabled (stop at pocket) | Rate of `safe_stop` in dead-end terrain |
| **E14-07** | Energy proxy $w_e, k_s$ | $w_e = 0$ (ignore slope gradient) | Hazard entry on steep slopes |

---

## Chapter 156. Experiment E15: Fault Injection Campaign (Task 76)

### 156.1 Fault Categories and Test Scenarios
1. **Sensor Blackout**: Sensor returns completely black/empty frames starting at step $t=10$. Rover must initiate controlled `safe_stop` via watchdog within 3 steps.
2. **Frozen Frame (Stuck Sensor)**: Camera repeats the same image for 20 steps while rover moves. Tests whether accumulator falsely reinforces stale ground.
3. **Severe Noise Burst**: Gaussian noise with $\sigma = 0.50$ injected into pixel values. Tests whether entropy gate immediately elevates uncertainty.
4. **Odometry Drift**: Pose error variance $\sigma_{pose} \in \{0.5, 1.0, 2.0\}$ cells. Evaluates whether footprint inflation absorbs localization error.

---

## Chapter 157. Statistical Resampling Engine (Task 77 & 78)

### 157.1 Clustered Bootstrap Algorithm
```python
def boot_clusters(values, groups, n_resamples=2000, seed=0):
    # Groups represent scene IDs; values represent episode metrics
    unique_scenes = np.unique(groups)
    rng = np.random.default_rng(seed)
    bootstrap_means = []
    for _ in range(n_resamples):
        sampled_scenes = rng.choice(unique_scenes, len(unique_scenes), replace=True)
        resampled_vals = np.concatenate([values[groups == s] for s in sampled_scenes])
        bootstrap_means.append(resampled_vals.mean())
    return float(values.mean()), float(np.percentile(bootstrap_means, 2.5)), float(np.percentile(bootstrap_means, 97.5))
```

---

## Chapter 158. Automated Report & Table Generation (Task 79)

### 158.1 Prose-Table Drift Mitigation
To guarantee that figures in the final report cannot diverge from experimental truth:
1. No table may be typed by hand.
2. An automated report generation script reads raw results JSON files and writes formatted LaTeX and Markdown tables directly.
3. Each generated table includes the source filename, generation timestamp, and code commit hash in a footer note.

---

## Chapter 159. Failure Review Protocol for Test Outliers

For every experiment, the 20 worst missions (ranked by hazard entry count or proximity to failure) are automatically extracted into `results/failure_cases_E13.csv`. The engineering mentor and student must review each scene overlay and categorize root causes into:
- Segmentation boundary ambiguity.
- Depth dropouts in low-texture pockets.
- Discretization corner-cutting.
- Watchdog premature termination.

---

## Chapter 160. Quality Gates for Experimental Release

- **Gate G-01**: Seed disjointness verified by automated test.
- **Gate G-02**: Pre-registration committed before unmasking test results.
- **Gate G-03**: All 95% confidence intervals computed via cluster bootstrap with at least 2,000 resamples.
- **Gate G-04**: Manifest checksum matches all raw result files.

---

## Chapter 161. Session Pushback Rules for Experiments

- **Pushback 1**: If asked to report "only the best 3 random seeds", refuse: cherry-picking invalidates confidence intervals.
- **Pushback 2**: If asked to calculate confidence intervals treating episodes as independent, refuse and enforce scene-level clustering.
- **Pushback 3**: If asked to omit negative ablation results where APPS was beaten by a baseline, refuse: negative results are primary scientific findings.

---

## Chapter 162. Master Results Table Template

| System | Condition | Attempted Episodes | Success Rate [95% CI] | Collision Rate [95% CI] | Refusal Rate [95% CI] | Mean Path Cost |
|---|---|---|---|---|---|---|
| **Oracle** | Nominal | 600 (200 scenes) | `[..]` | `[..]` | `[..]` | `[..]` |
| **K0** | Stale Prior | 600 (200 scenes) | `[..]` | `[..]` | `[..]` | `[..]` |
| **K1** | Stale + Sense | 600 (200 scenes) | `[..]` | `[..]` | `[..]` | `[..]` |
| **System A** | Nominal | 600 (200 scenes) | `[..]` | `[..]` | `[..]` | `[..]` |
| **System B** | Nominal | 600 (200 scenes) | `[..]` | `[..]` | `[..]` | `[..]` |
| **System C** | Nominal | 600 (200 scenes) | `[..]` | `[..]` | `[..]` | `[..]` |

---

## Chapter 163. Reproducibility Manifest Specification

Every experiment output directory must contain a signed `manifest.json`:
```json
{
  "experiment_id": "E13_closed_loop_baseline",
  "commit_hash": "a1b2c3d4e5f6",
  "python_version": "3.14.8",
  "config_sha256": "5a25ae49f293ec58a67fc873e3ae52913232524e2a5f1e5b76cebd1b3984ae75",
  "pre_registration_sha256": "8f3e1a...",
  "seeds_used": "seed_registry_v2.json",
  "total_runtime_seconds": 342.18
}
```

---

## Chapter 164. Verification of Statistical Code

The statistical helpers (`boot_clusters`, `boot_paired_clusters`, `wilson`, `rule_of_three`) must be verified against known analytical test cases in `tests/test_all.py` before executing large-scale sweeps.

---

## Chapter 165. Closing Instruction for Part 9

Experiments must be designed to discover the limits of the system, not to flatter it. Never adjust a threshold after viewing test outcomes. Record results exactly as measured.

---

## Appendices BQ to CA (Technical Specifications & Skeletons)

### Appendix BQ. Pre-Registration Note Template
Formal Markdown template with required sections for hypothesis, metrics, and frozen hashes.

### Appendix BR. Cluster Bootstrap Engine Specification
Mathematical algorithms and test cases for scene-clustered resampling.

### Appendix BS. Experiment E13 Runner Specification
Automated batch execution harness for multi-system baseline comparisons.

### Appendix BT. Experiment E14 Systematic Ablation Runner
Automated batch script iterating through component isolation configurations.

### Appendix BU. Fault Injection Campaign Driver
Execution framework for simulating sensor degradations and evaluating watchdog responses.

### Appendix BV. Difficulty Ladder Benchmarking Driver
Execution pipeline evaluating systems across difficulty levels D0 to D5.

### Appendix BW. Automated Report Table Compiler
Script parsing JSON outputs into publication-ready LaTeX and Markdown tables.

### Appendix BX. Seed Registry v2 Manifest
Complete seed mapping table for training, validation, and test splits.

### Appendix BY. Experiment Task Register & Status
Progress tracking table for Tasks 71 through 80.

### Appendix BZ. Toy-Tested Statistical Validation Suite
Unit tests verifying cluster bootstrap intervals against synthetic distributions.

### Appendix CA. Glossary Additions
- **Cluster Bootstrap**: Resampling technique preserving group dependencies among episodes.
- **Rule of Three**: Conservative statistical bound for zero observed failure events.
- **Pre-Registration**: Cryptographically timestamped specification committed before testing.
