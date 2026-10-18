# APPS Master Prompt, Part 7

**Level 1, Volume 2 of 5: Perception and Data at Level 1: Mode A generator specification, Mode B dataset verification, feature and image pipelines, calibration under shift**

*Continues Part 6 (chapters 86 to 106, appendices AJ to AT). Chapters 107 to 127 and appendices AU to BE.*

> **Synthetic-data research prototype, not flight software.** Part 7 contains no new experimental results. "Level 1" is an internal project milestone, not a NASA classification, and nothing here implies NASA affiliation, endorsement, certification or flight qualification. Part 7 turns the perception and data requirements of Level 1 into formal engineering specifications, verification protocols, data cards, and evaluation criteria following the non-negotiable rules of Chapter 1.

---

## Chapter 107. Status, Scope and Reading Rules

### 107.1 Why Part 7 exists
Part 6 established the Level 1 mission loop, information boundary, route cost function, and initial repository audit. It identified that the perception layer is the primary safety bottleneck: if perception fails silently or claims high confidence on unfamiliar hazards, downstream planning and safety guards are bypassed. Part 7 provides the complete specification for the data sources, synthetic generator extensions (Mode A), real planetary imagery verification protocol (Mode B), feature representations, and calibration under domain shift.

### 107.2 Current state, restated from Part 6
- APPS-0.1 remains the reference baseline: an ensemble of five gradient boosting classifiers trained on procedural 96x96 synthetic scenes.
- Primary safety metric: False-safe rate (fraction of true hazard area marked safe) must remain below 2.0% on nominal scenes and below 3.0% on novel terrain.
- The 25% block fraction finding in Chapter 22 is an exploratory observation pending validation on fresh, unseen seed sequences.
- `navigation_ready` is locked to `False` by `PROTOTYPE_LOCK` in the readiness guard (Chapter 70 and Chapter 95). Part 7 does not unlock this guard.

### 107.3 Scope of Volume 2
- **Mode A Data**: Specification of the procedural generator difficulty ladder (D0 to D5), multi-scale terrain synthesis, multi-material novel patches (N1 to N4), lighting sweeps, and haze models.
- **Mode B Data**: Rigorous verification protocol for public planetary datasets (e.g., AI4MARS, PDS). No loader may be integrated without source verification, licence check, and explicit taxonomy mapping.
- **Perception Pipeline**: Feature extraction architecture, handling missing/corrupted depth channels, temperature scaling on validation pixels, and out-of-distribution (OOD) novelty scoring in feature space.
- **Calibration Protocol**: Expected Calibration Error (ECE) minimization, reliability diagrams, and evaluating miscalibration under environmental domain shift.

### 107.4 Rules inherited from Parts 1 to 6
1. *Measurable beats impressive.* Every perception feature must have a concrete metric (mIoU, pixel accuracy, false-safe rate, ECE, AUROC).
2. *Synthetic stays synthetic.* Synthetic data must never be cited as evidence of real-world Mars performance.
3. *Unknown is unsafe.* Ambiguous, occluded, or out-of-distribution regions must default to blocked.
4. *Detection is not mineral identification.* Photographic features describe candidate visual targets only; mineral composition cannot be established from camera images alone.

---

## Chapter 108. Task Register for Part 7

| Task | Deliverable | Primary Metric / Output to Report | Status |
|---|---|---|---|
| **51** | Mode A generator v2 with difficulty ladder (D0-D5) | Scene verification tests passing; per-split hazard fraction | Not started |
| **52** | Multi-material novel terrain generator (N1-N4) | Disjoint label verification; per-material area fraction | Not started |
| **53** | Sun elevation and atmospheric haze augmentation | IoU failure boundary vs sun angle and haze density | Not started |
| **54** | Mode B public dataset verification report | License audit, URL verification, label mismatch inventory | Not started |
| **55** | Taxonomy mapping document for Mode B | Complete class translation matrix with lossy/exact tags | Not started |
| **56** | Feature versioning & invariance unit tests | Feature count verification (16 columns), invariance tests | Not started |
| **57** | Missing depth & disparity dropout handler | False-safe rate under 10%, 30%, 50% depth dropout | Not started |
| **58** | Temperature scaling calibration driver | ECE before vs after scaling on validation set | Not started |
| **59** | Mahalanobis OOD feature distance scorer | Novelty detection AUROC on N1..N4 materials | Not started |
| **60** | Multi-cue perception gate (RankGate v2) | False-safe vs refusal trade-off curve across validation set | Not started |

---

## Chapter 109. Mode A: Procedural Terrain Synthesis (Difficulty Ladder D0–D5)

### 109.1 Purpose and Architectural Principles
Mode A provides fast, fully-labeled procedural scenes for controlled ablation and benchmark isolation. It allows independent manipulation of terrain geometry, surface albedo, micro-texture, lighting angles, and sensor noise.

### 109.2 Difficulty Levels
- **Level D0 (Open Field)**: Smooth lowland terrain, zero rock obstacles, zero steep slopes. Evaluates whether the planner can achieve a 100% arrival rate in hazard-free worlds.
- **Level D1 (Scattered Rocks)**: Flat terrain with 5 to 15 isolated rock boulders of equivalent diameters 10 to 30 cm. Tests semantic rock segmentation and outline precision.
- **Level D2 (Ridge & Slopes)**: Complex elevation with Gaussian ridges exceeding the rover safe slope gradient (> 0.35). Evaluates geometric slope estimation from noisy depth channels.
- **Level D3 (Narrow Passages)**: Pairs of rock clusters spaced 1 to 2 rover footprint widths apart. Tests whether coarse grid reductions close traversable corridors.
- **Level D4 (Cul-de-Sacs & Dead Ends)**: U-shaped rock and ridge formations. Evaluates whether closed-loop perception triggers backtrack replanning or enters entrapment.
- **Level D5 (Multi-Hazard & OOD Novel Patch)**: Full combination of steep ridges, scattered boulders, low sun angle (15°), and an unfamiliar surface patch (novel material N1..N4).

### 109.3 Height-Field Mathematical Formulation
The base elevation $H(x, y)$ is synthesized by multi-scale band-limited Gaussian smoothing:
$$H_0(x, y) = \text{noise}(\sigma=14, \text{amp}=3.0) + \text{noise}(\sigma=5, \text{amp}=0.9)$$
Ridges are added via directional anisotropic Gaussian profiles:
$$H_{ridge}(x, y) = \sum_{i=1}^{N_r} A_i \exp\left( -\left(\frac{(y - y_i)\cos\theta_i - (x - x_i)\sin\theta_i}{w_i}\right)^2 \right)$$
Rock boulders are modeled as truncated ellipsoids superimposed onto the terrain height:
$$H_{rock}(u, v) = m \cdot h_0 \cdot \sqrt{\max\left(0, 1 - \left(\frac{u}{r_x}\right)^2 - \left(\frac{v}{r_y}\right)^2\right)}$$

---

## Chapter 110. Multi-Material Novel Terrain Generation (Task 52)

### 110.1 Novel Terrain Specification
In APPS-0.1, novel terrain was restricted to a single dark bluish circular patch. A detector evaluated on one novel material can easily overfit to that specific color signature. Task 52 introduces four distinct novel materials:

| Identifier | Description | Albedo Vector $(R, G, B)$ | Micro-Texture Amplitude $\alpha$ | Physical Analogue |
|---|---|---|---|---|
| **N1** | Obvious chromatic shift | `(0.30, 0.33, 0.40)` | `0.05` | Blue-tinted basaltic crust |
| **N2** | Subtle sand look-alike | `(0.72, 0.53, 0.38)` | `0.15` | Sulfated cemented duricrust |
| **N3** | High-albedo bright patch | `(0.85, 0.82, 0.75)` | `0.01` | Highly reflective salt/evaporite deposit |
| **N4** | Dark flat rock-texture | `(0.25, 0.20, 0.18)` | `0.20` | Flat dark carbonaceous slag |

### 110.2 Generation Constraint
The label for all novel materials is strictly set to `4`. The perception training pipeline must never receive class `4` as a training target. Novel patches must be detected purely via predictive entropy, ensemble disagreement, or feature-space Mahalanobis distance.

---

## Chapter 111. Lighting, Shadow Masks, and Atmospheric Haze (Task 53)

### 111.1 Shading and Ray-March Shadow Model
Terrain surface normal $\mathbf{n}(x, y)$ is calculated from the gradient of the surface height $\nabla H$:
$$\mathbf{n} = \frac{[-\partial H/\partial x, -\partial H/\partial y, 1]^T}{\sqrt{1 + (\partial H/\partial x)^2 + (\partial H/\partial y)^2}}$$
Given sun azimuth $\theta_{az}$ and sun elevation $\phi_{el}$, the incident solar unit vector is:
$$\mathbf{s} = [\cos\theta_{az}\cos\phi_{el}, \sin\theta_{az}\cos\phi_{el}, \sin\phi_{el}]^T$$
Direct Lambertian shading:
$$I_{shade}(x, y) = \max(0, \mathbf{n} \cdot \mathbf{s}) \cdot 0.85 + 0.15$$
If ray-marching along $-\mathbf{s}$ reveals an intercept with terrain elevation higher than the line of sight, the cell is marked in cast shadow and attenuated by $0.35$.

### 111.2 Atmospheric Haze Model
Atmospheric scattering blurs contrast as an exponential function of perceived optical depth $z(x, y)$:
$$I_{haze}(x, y) = (1 - w(x, y)) \cdot I(x, y) + w(x, y) \cdot \mathbf{c}_{dust}$$
where:
$$w(x, y) = 1 - \exp(-\beta_{haze} \cdot (z(x, y) - z_{min}))$$
and $\mathbf{c}_{dust} = [0.82, 0.65, 0.45]$ represents Martian airborne reddish-yellow dust.

---

## Chapter 112. Data Hygiene and Split Integrity for Mode A

### 112.1 Non-Leakage Rules
1. Split by scene seed, never by spatial crop from the same scene.
2. Training seeds (`1..250`), validation seeds (`400..450`), and test seeds (`600..700`) must be mutually exclusive and verified by `check_disjoint()`.
3. Test sets must remain untouched during hyperparameter sweeps and threshold tuning.

---

## Chapter 113. Mode B: Real Planetary Dataset Verification Protocol (Task 54)

### 113.1 Mandatory Verification Requirements
Public planetary datasets (e.g., NASA AI4MARS, PDS rover navcam archives) cannot simply be downloaded and fed into the model. The engineer must verify and record:
- Official repository source URL and access date.
- Explicit copyright licence and data-redistribution permissions.
- Camera calibration model (focal length, baseline, radial distortion parameters).
- Ground truth labeling methodology (crowdsourced vs. science team expert adjudication).
- Inter-annotator agreement statistics (Fleiss' Kappa or mean intersection-over-union).

### 113.2 Dataset Card Specification for Mode B
Every prospective real-world dataset must be accompanied by a standardized YAML Dataset Card containing:
```yaml
dataset_name: "AI4MARS"
curator: "NASA Jet Propulsion Laboratory"
license: "CC0 / Public Domain (verified)"
modalities: ["greyscale navcam", "stereo disparity"]
resolution: [1024, 1024]
annotation_classes: ["soil", "bedrock", "sand", "big rock", "null"]
inter_annotator_agreement_kappa: 0.68
known_biases: ["heavily biased toward sand/soil; thin rock edges under-segmented"]
```

---

## Chapter 114. Taxonomy Mapping to Chapter 13 Standards (Task 55)

### 114.1 Mapping Table
External labels must be explicitly translated into the APPS Chapter 13 Taxonomy (`0: bedrock`, `1: sand`, `2: rock`, `3: steep_slope`, `4: unknown`):

| External Dataset Label | Target APPS Class | Mapping Justification | Mapping Class |
|---|---|---|---|
| `soil / flat terrain` | `0: bedrock & compact ground` | Represents benign compact ground passable without penalty | Approximate |
| `sand / dunes / ripples` | `1: sand & loose material` | High sinkage risk; penalized with costly traversability weight | Exact |
| `big rock / boulder` | `2: rock & boulder` | Non-traversable discrete obstacle; classified as blocked | Exact |
| `bedrock outcrop` | `0: bedrock & compact ground` | Structural solid outcrop | Exact |
| `unlabeled / shadow / sky` | `4: unknown / OOD` | Ambiguous; must default to blocked per safety rules | Strict |

---

## Chapter 115. Image & Depth Feature Extraction Pipeline (Task 56)

### 115.1 Handcrafted Feature Architecture
The 16-channel pixel feature representation $F(x, y)$ combines:
- Color channels: $R, G, B$ and color ratio $R / (B + 0.05)$ (4 channels).
- Multi-scale Gaussian smoothed intensity: $s \in \{1, 2, 4\}$ (3 channels).
- Multi-scale local standard deviation: window widths $w \in \{3, 7\}$ (2 channels).
- First-order gradient magnitude on intensity $\sqrt{(\partial I/\partial x)^2 + (\partial I/\partial y)^2}$ (1 channel).
- Laplacian of Gaussian on intensity (1 channel).
- High-pass texture contrast $I - \text{Gauss}_8(I)$ (1 channel).
- Depth gradient magnitudes at scales $s \in \{2, 3\}$ (2 channels).
- Laplacian of Gaussian on depth (1 channel).
- High-pass depth contrast $D - \text{Gauss}_6(D)$ (1 channel).

### 115.2 Feature Versioning Rule
`FEATURE_VERSION = "v1.0"` is hardcoded in `models/features.py`. Any addition, reordering, or parameter change bumps the version string, invalidates pickled models, and requires retraining.

---

## Chapter 116. Handling Missing Depth and Disparity Errors (Task 57)

### 116.1 Depth Quality Degradation Protocol
In stereo vision, depth values fail in regions of low texture (smooth sand) or specular glare. The pipeline must handle depth degradation gracefully:
- **Depth Dropout**: Random missing depth cells must be imputed with local median elevation rather than zero, and flagged in a binary `depth_missing` mask.
- **Slope Uncertainty Inflation**: When depth is missing, the predicted steep slope probability carries an automatic uncertainty override: $u(x, y) \leftarrow \max(u(x, y), 0.70)$.

---

## Chapter 117. Calibration Under Domain Shift (Task 58)

### 117.1 Expected Calibration Error (ECE)
Given $M$ confidence bins $B_m$, ECE is defined as:
$$\text{ECE} = \sum_{m=1}^M \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
A model that achieves $\text{ECE} \le 0.025$ on nominal synthetic scenes often exhibits $\text{ECE} \ge 0.15$ when subjected to novel terrain or atmospheric haze.

### 117.2 Temperature Scaling Formulation
Calibrated probabilities are obtained by dividing log-odds by scalar temperature $T > 0$:
$$q_k = \frac{\exp(\log(p_k + \epsilon) / T)}{\sum_j \exp(\log(p_j + \epsilon) / T)}$$
where $T$ is optimized on the held-out validation set to minimize Negative Log-Likelihood (NLL).

---

## Chapter 118. Feature-Space Novelty Detection (Task 59)

### 118.1 Mahalanobis Distance Metric
For pixel feature vector $\mathbf{x} \in \mathbb{R}^{16}$ and known class $k \in \{0, 1, 2, 3\}$ with mean $\boldsymbol{\mu}_k$ and shrunk covariance matrix $\mathbf{\Sigma}_k$:
$$d_M(\mathbf{x}) = \min_{k} \frac{1}{D} (\mathbf{x} - \boldsymbol{\mu}_k)^T \mathbf{\Sigma}_k^{-1} (\mathbf{x} - \boldsymbol{\mu}_k)$$
where Ledoit-Wolf shrinkage ensures numerical invertibility:
$$\mathbf{\Sigma}_k = (1 - \lambda) \mathbf{S}_k + \lambda \frac{\text{Tr}(\mathbf{S}_k)}{D} \mathbf{I}$$

---

## Chapter 119. Multi-Cue Uncertainty Combination (Task 60)

### 119.1 RankGate Formulation
Rather than using arbitrary linear weighting between entropy and disagreement, RankGate transforms each raw score into its empirical percentile relative to clean validation data:
$$\text{score}_{comb}(x) = \max \left( \Phi_{ent}(ent(x)), \Phi_{dis}(epi(x)), \Phi_{OOD}(d_M(x)) \right)$$
A cell is flagged uncertain if $\text{score}_{comb}(x) \ge 0.95$.

---

## Chapter 120. Perception Failure Modes and Safeguards

### 120.1 Perception Risk Catalogue
1. **P-01 (Albedo-Shadow Confound)**: Dark rocks misclassified as shadows on flat terrain. *Mitigation*: Depth gradient check.
2. **P-02 (Low Sun Saturation)**: Horizon glare washing out contrast. *Mitigation*: Dynamic histogram normalization and uncertainty elevation.
3. **P-03 (Thin Rock Grazing)**: Rocks smaller than cell resolution missed. *Mitigation*: Footprint expansion margin.

---

## Chapter 121. Statistical Sizing for Perception Benchmarks

- Scene count: at least 60 scenes per test condition (nominal, low-sun, haze, novel).
- Bootstrap: 2,000 resamples over scenes (never pixels) to compute 95% confidence intervals.
- Paired differences: $d_i = \text{FSR}_B(i) - \text{FSR}_C(i)$ must exclude zero to assert an improvement.

---

## Chapter 122. Verification Checklists for Perception Deliverables

- [ ] All training seeds derived from SeedSequence registry.
- [ ] No test scenes accessed during temperature fitting or gate threshold sweeps.
- [ ] Confusion matrix reported alongside mIoU and pixel accuracy.
- [ ] False-safe rate presented before accuracy.
- [ ] Plain-language caveats attached to every JSON observation record.

---

## Chapter 123. Reviewer Lenses for Perception Releases

- **Method Reviewer**: Verifies that covariance matrices and temperature $T$ were computed strictly on validation scenes.
- **Data Reviewer**: Confirms zero hash collisions between training and test scene caches.
- **Red-Team Reviewer**: Tests perception degradation against all-black, saturated, and inverted inputs to verify fail-safe behavior.

---

## Chapter 124. Session Protocols and Pushback Guidelines

- **Pushback 1**: If asked to report "accuracy only" without false-safe rate, refuse and present both.
- **Pushback 2**: If asked to test on real Mars images without verified ground truth, mark as qualitative demonstration only.
- **Pushback 3**: If asked to bypass uncertainty checks to lower the refusal rate, refuse and explain the safety-availability trade-off.

---

## Chapter 125. Mathematical Model Summary

$$\text{FSR} = \frac{\sum_{(x,y) \in \text{Hazards}} [1 - \text{Unsafe}(x,y)]}{\max(1, |\text{Hazards}|)}$$
$$\text{Unsafe}(x, y) = (p_{rock} + p_{steep} > \tau_{haz}) \lor (\text{Entropy} > \tau_{ent}) \lor (\text{Disagreement} > \tau_{epi})$$

---

## Chapter 126. Data Card Template for Mode A

```yaml
dataset_name: "APPS-ModeA-Synthetic"
generator_version: "2.0"
resolution: [96, 96]
channels: ["R", "G", "B", "Depth"]
classes: ["bedrock", "sand", "rock", "steep_slope", "novel"]
seed_ranges:
  train: [1, 250]
  val_nominal: [500, 539]
  val_novel: [540, 579]
  test_nominal: [600, 659]
  test_novel: [660, 719]
```

---

## Chapter 127. Closing Instruction for Part 7

Perception outputs are inputs to navigation, not final decisions. Work from the task register, compute intervals from scenes, and never declare an algorithm flight-ready.

---

## Appendices AU to BE (Technical Specifications & Skeletons)

### Appendix AU. Advanced Procedural Scene Generator Specification
Defines complete procedural logic for height synthesis, rock placement, shadow casting, and multi-novel material stamping (`make_scene_v2`).

### Appendix AV. Mode B Dataset Verification Protocol
Standardized audit checklist for inspecting candidate Mars rover imagery repositories.

### Appendix AW. Feature Extraction Pipeline Specification
16-channel pixel feature extraction implementation with feature versioning lock.

### Appendix AX. Temperature Scaling Engine
Grid-search NLL optimization and reliability diagram computation.

### Appendix AY. Mahalanobis Feature-Space Novelty Scorer
Class-conditional Gaussian clustering with Ledoit-Wolf covariance regularization.

### Appendix AZ. Cross-Sensor Consistency Estimator
Local gradient-to-curvature correlation and depth validity checker.

### Appendix BA. Perception Task Register & Deliverables
Tracking table for Tasks 51 through 60.

### Appendix BB. Perception Risk Register
Identified perceptual vulnerabilities and verified mitigations.

### Appendix BC. Perception Toy-Check Record
Documented unit test runs on synthetic input matrices.

### Appendix BD. Configuration Schema
YAML schema specification for all perception hyperparameters.

### Appendix BE. Glossary Additions
- **Domain Shift**: Statistical disparity between synthetic generator parameters and real Martian illumination.
- **ECE**: Expected Calibration Error across confidence bins.
- **OOD**: Out-of-Distribution terrain inputs.
