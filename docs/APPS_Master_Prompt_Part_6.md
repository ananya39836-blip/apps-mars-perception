# APPS Master Prompt, Part 6

**Level 1, Volume 1 of 5: Audit, definitions, information boundary, uncertainty-aware route cost, closed-loop mission loop, safety analysis and traceability**

*Continues Part 5 (chapters 68 to 85, appendices AA to AI). Chapters 86 to 106 and appendices AJ to AT.*

> **Synthetic-data research prototype, not flight software.** Part 6 contains no new experimental results. "Level 1" is an internal project milestone, not a NASA classification, and nothing here implies NASA affiliation, endorsement, certification or flight qualification. Part 6 turns the supplied "Level 1" brief into the conventions of Parts 1 to 5.

---

## Chapter 86. Status, Scope and Reading Rules

### 86.1 Why Part 6 exists
Parts 1 to 5 specify a perception prototype, its experiments, its output contract and a small closed-loop simulator. A separate "Level 1" brief asks for something broader: a repeatable perception-to-navigation pipeline in simulation, in which the rover sees only what its sensor model allows, updates its own map, replans when the world disagrees with that map, and is scored on whether it actually arrives. Part 6 converts that brief into tasks, definitions, tests and listings that obey the non-negotiable rules of Chapter 1.

### 86.2 The Level 1 volume plan (indicative)
- **Volume 1 (Part 6)**: Audit protocol, Level 1 definition, information boundary, sensor and rover model, route cost, mission loop, safety analysis, test plan, traceability method, toy-tested listings.
- **Volume 2 (Part 7)**: Perception and data at Level 1: Mode A generator specification, Mode B dataset verification, feature and image pipelines, calibration under shift.
- **Volume 3 (Part 8)**: Navigation and loop: planner comparisons, replanning studies, fault injection inside the loop, footprint and slope handling.
- **Volume 4 (Part 9)**: Experiments E13 onward: pre-registrations, sizing, statistics, report generation from files.
- **Volume 5 (Part 10)**: Assurance and release: hazard log review, traceability evidence, demo, final verification report.

### 86.3 Current state, restated
- No task of Parts 3, 4 or 5 has been completed. All registers read "not started" and no new result exists. The measured numbers are still those of Part 2: synthetic, one trained ensemble.
- `navigation_ready` is false in every record and stays false. The lock of Chapter 70 (Part 5) is untouched.
- The five earlier prompts are specifications. Reading them does not execute them; no experiment of Parts 2 to 5 has been run on their account.

### 86.4 Task register for Part 6
- Task 41: Repository audit and `docs/INITIAL_TECHNICAL_AUDIT.md`.
- Task 42: Sensor model, rover state and information-boundary tests.
- Task 43: Uncertainty-aware route cost $J$, A* baseline, rejection rule.
- Task 44: Closed-loop mission loop with monitors (extends Task 35).
- Task 45: Level 1 generator extension, difficulty ladder, split registry.
- Task 46: Mode B dataset investigation note.
- Task 47: E13 closed-loop baseline comparison.
- Task 48: `docs/SAFETY_AND_FAILURE_ANALYSIS.md` and hazard log update.
- Task 49: Test suite execution record and `docs/VALIDATION_REPORT.md`.
- Task 50: Demo, documentation set, traceability table, Level 1 designation check.

---

## Chapter 87. Reconciling the Level 1 Brief with the Master Prompt

Where the Level 1 brief conflicts with rules of Part 1, the Master Prompt wins:
- "Autonomous planetary intelligence" $\to$ Use "closed-loop navigation prototype in simulation".
- "NASA-style systems engineer" $\to$ Use "systems engineering practice", avoid comparisons implying agency equivalence.
- "Level 1 complete" $\to$ Computed strictly from evidence files via Appendix AO: `L1-not-met`, `L1-partial`, `L1-met (internal)`.
- Retain A* $\to$ Dijkstra is A* with a zero heuristic; baseline K uses A* with an admissible heuristic.
- Success must mean arrival $\to$ True position must reach the goal column without entering a hazard cell.

---

## Chapter 88. Review of Part 5: Findings Before Building on It

- **F1**: The guard of Appendix AB indexed `bounds["unsafe_max"]` directly, raising `KeyError` if missing. Patched in Appendix AQ.
- **F2**: Appendix AC loop lacked orientation, FOV, pose error, and outages. Addressed in Rung 1.5 loop (Appendices AJ to AM).
- **F3**: "Newly discovered obstacle" redefined as a new observation that invalidates the current planned route.
- **F4**: `run_episode` checked `truth[pos]` only after a move; generator must guarantee a hazard-free start cell.
- **F5**: Information boundary enforced mechanically: simulator and rover separated.

---

## Chapter 89. Level 1: Definition, Designation and Evidence

- **Designation**: APPS Level 1: Validated Planetary Perception and Closed-Loop Navigation Prototype (internal milestone).
- **Three labels**: `L1-not-met` (missing evidence file), `L1-partial` (unexecuted or failing evidence), `L1-met (internal)` (all 14 requirements verified and passing).
- **The 14 Requirements**: `audit`, `modular`, `partial_obs`, `perception`, `risk_in_nav`, `mission_sim`, `replan`, `explicit_failure`, `baselines`, `metrics_from_trials`, `tests_executed`, `failures_recorded`, `docs_match`, `traceability`.

---

## Chapter 90. Task 41: Repository Audit (Phase 1)
Establish from code what the repository implements, what it only describes, and what is wrong. Output: `docs/INITIAL_TECHNICAL_AUDIT.md`.

---

## Chapter 91. The Information Boundary
The rover side reads only its own observations, believed pose, configuration, and declared prior map. The simulator side holds truth and uses it only for producing observations and scoring outcomes. Verified via mutation tests.

---

## Chapter 92. Task 42: Sensor Model and Rover State
Defines sector field-of-view, range-dependent miss probability, per-cell uncertainty, pose noise, and sensor outages.

---

## Chapter 93. Perception at Level 1: Five Quantities Not to Confuse
1. **Classification confidence**: Largest class probability.
2. **Predictive uncertainty**: Entropy of mean probabilities; ensemble disagreement.
3. **Out-of-distribution score**: Feature-space Mahalanobis distance.
4. **Physical terrain risk $r \in [0, 1]$**: Calibrated hazard probability combined with slope.
5. **Navigation feasibility**: Planner status (`ok`, `no_path`, `rejected`).

---

## Chapter 94. Task 43: Uncertainty-Aware Route Cost
$$c(\mathbf{x}) = w_d + w_r \cdot r(\mathbf{x}) + w_u \cdot u(\mathbf{x}) + w_e \cdot (1 + k_s \cdot s(\mathbf{x}))$$
$$J(P) = \sum_{k=1}^m L_k \cdot \frac{c(\mathbf{x}_{k-1}) + c(\mathbf{x}_k)}{2}$$
Includes hard constraints ($r_{block}, u_{block}$) and route risk budget rejection ($p_{proxy} > p_{budget}$).

---

## Chapter 95. Task 44: The Closed-Loop Mission
Step-by-step decision cycle: observe $\to$ register $\to$ fuse $\to$ plan $\to$ audit $\to$ watchdog $\to$ move $\to$ score. Outcomes: `success`, `collision`, `no_path`, `rejected`, `safe_stop`, `timeout`.

---

## Chapter 96. Task 45: Level 1 Terrain Generation and Splits (Mode A)
Difficulty ladder D0 (open field) through D5 (multi-hazard & novel material), feasibility filtering, and disjoint seed registries.

---

## Chapter 97. Task 46: Mode B, Real Planetary Data Investigation
Verification protocol for public rover datasets (AI4MARS, PDS). Verification before loader integration.

---

## Chapter 98. Task 47: E13 Closed-Loop Baseline Comparison
Benchmarking systems F, O, K0, K1, A, B, and C with cluster bootstrap intervals over scenes.

---

## Chapter 99. Task 48: Safety and Failure Analysis
Consolidated hazard log tracking Hazards H7 through H17 with explicit mitigations and evidence links.

---

## Chapter 100. Task 49: Test Plan and Execution Record
Test suite covering T1 through T22, boundary mutation tests, and fuzz smoke testing.

---

## Chapter 101. Task 50: Demonstration and Documentation Set
Side-by-side ground truth vs rover belief panels, interactive obstacle injection, and README claims matching.

---

## Chapter 102. Traceability to Public NASA and JPL Engineering Practice
Five-level claim hierarchy mapping practices to SP-2016-6105, NPR 7150.2, and NASA-STD-8739.8.

---

## Chapter 103. Phases, Definition of Done and FAQ
Ten project phases, gates, and pushback guidelines.

---

## Chapter 104. Configuration, Logging and Repository Layout
Package separation: `config`, `terrain`, `simulator`, `sensing`, `perception`, `mapping`, `risk`, `navigation`, `mission`, `evaluation`.

---

## Chapter 105. Level 1 Ablations, Red Team and Review
Ablation program E14 isolating weights, gates, footprint, and fusion rules.

---

## Chapter 106. Session Prompts and Push-Back Rules for Level 1
Kickoff prompts, code request templates, and pushback examples.

---

## Appendices AJ to AT (Level 1 Technical Specifications & Skeletons)
- **AJ**: Sensor Model, Field of View and Pose Error
- **AK**: Route Cost, Blocking and Planner with Rejection
- **AL**: Discrepancy, Route Audit and Watchdog
- **AM**: Closed-Loop Mission Loop
- **AN**: Mission Metrics with Stated Denominators
- **AO**: Level 1 Evidence Checklist (`assess()`)
- **AP**: Repository Scan for Technical Audit
- **AQ**: Patch for navigation_ready Guard
- **AR**: Toy-Check Verification Record
- **AS**: Configuration Template & Mission Record Schema
- **AT**: Glossary Additions and Closing Instruction
