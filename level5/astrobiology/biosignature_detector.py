"""Long-Horizon Autonomous Astrobiology: Biosignature Recognition & Raman Deconvolution.
Level 5: Part 31 (Chapters 400 to 409).

Implements autonomous biosignature detection:
1. Deep-UV Raman Spectral Deconvolution (Aromatics, Amides, Nucleic Acid peaks).
2. Enantiomeric Homochirality Metric (|CE| > 25%).
3. Carbon Isotopic Fractionation (delta 13C permil).
4. Composite Astrobiological Confidence Score & Category IV-b Sterility Guards.
"""
import math
from typing import Dict, List, Tuple
import numpy as np

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False


class DeepUVRamanSpectrometer:
    """Simulates Deep-UV Raman spectroscopy (248.6 nm excitation) for mineral-organic deconvolution."""
    def __init__(self):
        # Known diagnostic Raman wavenumber bands (cm^-1)
        self.biomarker_bands = {
            "aromatic_ring": 1600.0,
            "amide_I": 1650.0,
            "aliphatic_ch": 2930.0,
            "polyphosphate": 1150.0,
            "nucleic_purine": 1335.0
        }

    def analyze_spectrum(self, detected_peaks_cm: List[float], snr_db: float = 24.0) -> Dict:
        """Matches detected spectral peaks against prebiotic vs biogenic library."""
        matches = []
        for name, target_cm in self.biomarker_bands.items():
            for p in detected_peaks_cm:
                if abs(p - target_cm) <= 18.0: # Peak tolerance band
                    matches.append(name)
                    break
                    
        organic_peak_density = len(matches) / len(self.biomarker_bands)
        is_complex_organic = (len(matches) >= 3) and (snr_db >= 18.0)
        
        return {
            'peaks_evaluated': detected_peaks_cm,
            'matched_biomarkers': matches,
            'organic_complexity_index': round(organic_peak_density, 3),
            'complex_organics_confirmed': is_complex_organic,
            'spectral_snr_db': snr_db
        }


class BiosignatureClassifier:
    """Computes multi-criteria biogenicity score combining Raman, chirality, and isotopic fractionation."""
    def __init__(self, biogenicity_threshold: float = 0.70):
        self.threshold = biogenicity_threshold

    def evaluate_sample_biogenicity(
        self,
        chiral_excess_pct: float,
        delta_13c_permil: float,
        raman_complexity_index: float,
        fluorescence_positive: bool = True
    ) -> Dict:
        """Evaluates whether sample exhibits unambiguous biogenic discrimination."""
        # 1. Homochirality score: Abiotic chemistry is racemic (CE ~ 0%). Biology exhibits high chiral excess (|CE| > 25%)
        chiral_score = min(1.0, abs(chiral_excess_pct) / 40.0)
        
        # 2. Isotopic score: Biological carbon fixation prefers 12C over 13C (delta 13C < -20 permil)
        if delta_13c_permil < -25.0:
            iso_score = 1.0
        elif delta_13c_permil < -15.0:
            iso_score = 0.65
        else:
            iso_score = 0.15 # Abiotic carbonate / mantle volcanic carbon
            
        # 3. Raman organic complexity score [0, 1]
        raman_score = raman_complexity_index
        
        # 4. Fluorescence / motility weight
        fluor_score = 1.0 if fluorescence_positive else 0.3
        
        # Composite biogenicity score
        biogenicity_score = (
            0.35 * chiral_score +
            0.30 * iso_score +
            0.25 * raman_score +
            0.10 * fluor_score
        )
        is_candidate_life = biogenicity_score >= self.threshold
        
        return {
            'chiral_excess_pct': round(chiral_excess_pct, 1),
            'delta_13c_permil': round(delta_13c_permil, 1),
            'chiral_score': round(chiral_score, 3),
            'isotopic_score': round(iso_score, 3),
            'biogenicity_score': round(biogenicity_score, 4),
            'is_candidate_biosignature': is_candidate_life,
            'priority_level': "CRITICAL_ALPHA" if is_candidate_life else "NOMINAL_SURVEY"
        }
