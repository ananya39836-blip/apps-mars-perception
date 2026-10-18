# APPS Safety and Failure Analysis Report (Task 48 / Task 81)

**Standard**: APPS Master Prompt Part 6 Chapter 99 & Part 10 Chapter 170  
**Disclaimer**: Synthetic-data research prototype, not flight software. Safeguards exist to make failures visible and explicit, not to ensure physical vehicle safety.

---

## 1. Consolidated Hazard Log (Hazards H1 to H17)

| Hazard ID | Failure Mode & Mechanism | Consequence in Simulation | Detection Mechanism | Verified Mitigation | Verification File / Test | Residual Risk Statement | Review Status |
|---|---|---|---|---|---|---|---|
| **H1** | Hazardous rock region marked safe | Rover collision | Observed-hazard false-safe; failure review | Multi-cue uncertainty gate + strict truth testing | `results/E13_results.json` | Boundary pixel label noise may cause edge clipping | Mitigated (Verified) |
| **H2** | Novel terrain marked safe | Collision on unfamiliar surface | Feature novelty score + disagreement | Mahalanobis OOD distance + RankGate | `results/E13_results.json` | High-albedo subtle novel materials may elude color contrast | Mitigated (Verified) |
| **H3** | Sensor fault produces confident safe output | Blind hazard entry | Validity checks; local correlation | Depth validity filter & consistency check | `results/E15_fault_results.json` | Flat glare patterns may mimic smooth safe terrain | Mitigated (Verified) |
| **H4** | Stale or mismatched model version loaded | Silent erroneous inference | Load-time version check | Feature and model version string assertions | `tests/test_level1.py::test_t1_terrain_reproducible` | Incompatible Python environment or unpickler drift | Mitigated (Verified) |
| **H5** | Downstream system misreads record | Control failure | Schema validator | Schema v2.0 validation rejecting unknown formats | `tests/test_all.py::test_schema_v2_and_guard` | Schema field semantics changed without version bump | Mitigated (Verified) |
| **H6** | Overclaiming in docs or demo interface | Operator misuse | Automated claim scan & independent review | Phrase linter and strict disclaimers | `docs/INITIAL_TECHNICAL_AUDIT.md` | Casual readers may ignore explicit research caveats | Mitigated (Verified) |
| **H7** | Steep slope under-costed from noisy depth | Tip-over / high roll | Elevation gradient checks | Hard slope cutoff and energy cost factor | `results/weight_ablation_E23.json` | Depth noise flattening steep terraced steps | Mitigated (Verified) |
| **H8** | Obstacle hidden outside sensor FOV | Collision | Unknown cell counts | Frontier planning rule: unknown cells hard blocked | `tests/test_level1.py::test_t5_information_boundary_mutation` | Occlusion blind spots in narrow passages | Mitigated (Verified) |
| **H9** | Localisation pose error smears map | Hazard graze | Pose error sweep | Footprint inflation ($r_{fp} \ge 1\text{ cell}$) | `results/E15_fault_results.json` | Persistent odometry bias drift over long traverses | Mitigated (Verified) |
| **H10** | Map corruption / permanent false alarm lock | Route refusal | Discrepancy counts | Watchdog replanning & scan behavior | `results/stale_map_test.json` | Permanent union fusion retaining transient sensor spikes | Mitigated (Verified) |
| **H11** | Uncalibrated predictive probabilities | Mis-set decision gates | Reliability diagram & ECE under shift | Temperature scaling fitted on validation | `results/perception_run.json` | Calibration degradation under unmodeled dust storms | Mitigated (Verified) |
| **H12** | Invalid/NaN/Corrupt sensor data stream | Unhandled crash | Exception trap | Safe-by-default failure record with degraded status | `results/E15_fault_results.json` | Corrupted buffer passing partial numeric checks | Mitigated (Verified) |
| **H13** | Computation timeout | Rover moves on stale map | 95th percentile latency monitor | Bounded node budget & step-level timing | `results/manifest.json` | Processor load spikes under dense obstacle clutter | Mitigated (Verified) |
| **H14** | Planner finds no route | Deadlock / stall | Explicit planner status | Return status `no_path` / `safe_stop`; no guessing | `results/outcome_tests.json` | Rover unable to complete traverse in dense maze worlds | Mitigated (Verified) |
| **H15** | Replan oscillation trap | Timeout / battery drain | Replan counter & stall detector | Watchdog replan budget & stall detection | `tests/test_level1.py::test_t10_watchdog_monitors` | Conservative halting in zig-zag rocky corridors | Mitigated (Verified) |
| **H16** | Operation outside validated envelope | Untrusted behavior | Model card envelope table | Input parameter bounds checks | `configs/cfg.yaml` | User manually overriding operational bounds | Mitigated (Verified) |
| **H17** | `allow_unknown` enabled in configuration | Rover enters unobserved cells | Config hash verification | Default locked to `False`; flagged as exploratory | `tests/test_level1.py::test_t5_information_boundary_mutation` | Intentional user override bypassing unknown blockage | Mitigated (Verified) |

---

## 2. Review and Verification Sign-Off
- **Total Hazards Identified**: 17
- **Total Hazards Mitigated with Documented Tests/Results**: 17
- **Open / Unmitigated Hazards**: 0
- **Independent Safety Posture**: Verified simulation prototype only; residual risks remain active for real planetary deployment.
