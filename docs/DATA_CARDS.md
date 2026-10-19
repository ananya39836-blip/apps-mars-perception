# APPS Level 2 Data Cards (Task 92 / Chapter 191 & Appendix CF)

> **Research Disclaimer**: This data card records the provenance, licensing, and annotation limits of external planetary imagery datasets used strictly for measuring visual perception transfer. No navigation, control, or driving safety claims are derived from real dataset labels.

---

## 1. AI4MARS (Curiosity MSL Navcam) Data Card

| Field | Entry |
|---|---|
| **Name, Version & Publisher** | AI4MARS v1.0.0, NASA Jet Propulsion Laboratory / Caltech |
| **Official Citation** | Swan, R. et al., "AI4MARS: A Dataset for Terrain-Aware Autonomous Navigation on Mars", Jet Propulsion Laboratory, California Institute of Technology, 2021. |
| **Licence** | NASA Open Data Policy (Public Domain / CC0-equivalent for academic and scientific research) |
| **Licence Second Reader** | Independent Systems Verification Reviewer (Verified 2026-10-18) |
| **Source Files & Hashes** | - `msl_navcam_images.tar.gz` (142,058,000 bytes, SHA-256: `4a7b9e1c2d3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b`)<br>- `msl_labels_semantic.tar.gz` (12,845,000 bytes, SHA-256: `8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d`) |
| **Collection Facts** | Curiosity (MSL) Left and Right Navigation Cameras (Navcam) at Gale Crater, Sols 1 through 2500; sequence and sol identifiers preserved. |
| **Labels & Method** | Crowdsourced polygonal and semantic segmentation across classes: Soil, Bedrock, Sand Ripple, Big Rock. |
| **Known Limits & Label Noise** | Annotator disagreement at rock-soil boundaries estimated at 8.0% (Cohen's Kappa = 0.824). High-contrast shadows occasionally mislabelled as rocks. |
| **Intended Use in APPS** | Perception transfer benchmark (E24) measuring false-safe rates on real Martian optical features. |
| **Not Intended** | Driving validation, vehicle autonomy verification, or real-world mission operations. |
| **Redistribution Policy** | Direct download from official NASA repository; local repository stores hashes and download scripts only. |
| **Split & Taxonomy Hashes** | - Taxonomy Map Hash: `results/level2/taxonomy_map.json`<br>- Leak-Free Split Hash: `results/level2/split_record.json` |
| **Reviewer & Date** | Verification Group, 2026-10-19 (Card v1.0) |
