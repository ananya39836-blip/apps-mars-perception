# APPS Label Taxonomy Document (v1.0)

This document extracts Chapter 13 into a versioned specification for training, evaluation, and annotation.

## Version & Changelog
- **Version**: taxonomy v1.0
- **Corresponds to**: APPS Master Prompt Part 1, Chapter 13
- **Rule**: Any change bumps the version, triggers retraining, and marks older results as belonging to the previous version.

---

### Class 0: Bedrock and Compact Ground
- **Definition**: Firm, relatively flat ground with a visible granular or fractured texture, including pavement-like outcrop surfaces.
- **Typical appearance**: Medium brightness, reddish brown, moderate fine-scale texture.
- **Counter example**: A smooth, bright, fine-grained patch is more likely sand.
- **Ambiguous cases**: Ground covered by a thin dust layer. *Rule*: label by dominant visible texture and mark pixel as low confidence in annotation metadata.
- **Traversability default**: Free, subject to slope limits.

---

### Class 1: Sand and Loose Material
- **Definition**: Fine-grained, smooth, wind-formed or loose material, including ripples and drifts.
- **Typical appearance**: Brighter, low texture contrast, rippled shading.
- **Counter example**: A dust-covered flat rock can look smooth. *Rule*: if rock edges or cracks are visible, label rock or bedrock.
- **Traversability default**: Costly. Sand can trap wheels, and an image alone cannot tell how deep or soft it is. Sinkage is not estimated.

---

### Class 2: Rock and Boulder
- **Definition**: An isolated, raised block of rock distinguishable from its surroundings by outline, shadow or shading.
- **Typical appearance**: Darker, strong local texture, casts a shadow.
- **Counter example**: A shadow on flat ground has no raised outline.
- **Ambiguous cases**: Partially buried rocks. *Rule*: label the visible part.
- **Size bands**: Small below 10 cm equivalent, medium 10 to 30 cm, large above 30 cm.
- **Traversability default**: Blocked when height exceeds rover step limit, otherwise costly.

---

### Class 3: Steep Slope
- **Definition**: Terrain whose gradient exceeds rover safe slope. Depends on geometry, not appearance; image-only systems report with high uncertainty.
- **Traversability default**: Blocked above safe slope, costly in transition band.

---

### Class 4: Unknown or Unclassified Terrain (OOD)
- **Definition**: Any region the annotator or system cannot assign to above classes with confidence, including novel materials, deep shadow, saturated pixels and occluded regions.
- **Rule**: Never used as training target for a confident predictor. Flagged by the uncertainty layer.
- **Traversability default**: Blocked.
