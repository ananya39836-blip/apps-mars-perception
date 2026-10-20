"""Online Adaptive Terramechanics & Dynamic Bayesian Regolith Identification.
Level 4: Part 22 (Chapters 310 to 319).

Implements online learning and parameter estimation for planetary soil:
1. Online Recursive Bayesian Parameter Estimation: Estimates soil cohesion (c), friction angle (phi), and sinkage modulus (n).
2. Dynamic Regolith Classification: Posterior probability distribution across Martian soil classes.
3. Predictive Slip Anticipation Sentinel: Detects upcoming entrapment risks before vehicle stalls.
"""
import math
from typing import Dict, List, Tuple
import numpy as np


class OnlineBayesianTerramechanics:
    """Recursive Bayesian filter estimating Martian regolith properties in real time."""
    def __init__(self):
        # Soil classes and their prior probabilities
        self.soil_classes = ["bedrock", "medium_sand", "drift_sand", "loose_dust"]
        self.priors = {
            "bedrock": 0.25,
            "medium_sand": 0.50,
            "drift_sand": 0.15,
            "loose_dust": 0.10
        }
        # Nominal parameters for reference classes
        self.class_profiles = {
            "bedrock": {"c_kPa": 50.0, "phi_deg": 40.0, "n": 1.2, "expected_sinkage_cm": 0.1},
            "medium_sand": {"c_kPa": 0.8, "phi_deg": 35.0, "n": 0.9, "expected_sinkage_cm": 1.2},
            "drift_sand": {"c_kPa": 0.2, "phi_deg": 28.0, "n": 0.7, "expected_sinkage_cm": 3.8},
            "loose_dust": {"c_kPa": 0.05, "phi_deg": 22.0, "n": 0.5, "expected_sinkage_cm": 6.5}
        }
        # Filter posterior state
        self.posteriors = dict(self.priors)
        self.estimated_cohesion_kPa = 1.0
        self.estimated_friction_deg = 32.0
        self.update_count = 0

    def update_with_measurement(
        self,
        measured_sinkage_cm: float,
        measured_slip_ratio: float,
        wheel_torque_Nm: float
    ) -> Dict:
        """Updates Bayesian soil posteriors given current drive telemetry."""
        self.update_count += 1
        likelihoods = {}
        
        for sc, prof in self.class_profiles.items():
            # Likelihood based on sinkage observation
            exp_z = prof["expected_sinkage_cm"]
            z_sigma = 0.8 + 0.3 * exp_z
            sinkage_likelihood = math.exp(-0.5 * ((measured_sinkage_cm - exp_z) / z_sigma)**2) / (z_sigma * math.sqrt(2 * math.pi))
            
            # Likelihood based on slip ratio
            # High slip is more consistent with drift sand or loose dust
            if sc in ("drift_sand", "loose_dust"):
                slip_likelihood = 1.0 if measured_slip_ratio > 0.20 else 0.3
            else:
                slip_likelihood = 1.0 if measured_slip_ratio <= 0.20 else 0.1
                
            likelihoods[sc] = sinkage_likelihood * slip_likelihood + 1e-6
            
        # Bayesian update: P(class|data) ~ P(data|class) * P(class)
        unnorm_posteriors = {sc: likelihoods[sc] * self.posteriors[sc] for sc in self.soil_classes}
        total = sum(unnorm_posteriors.values())
        self.posteriors = {sc: val / total for sc, val in unnorm_posteriors.items()}
        
        # Continuous parameter expectations
        self.estimated_cohesion_kPa = float(sum(
            self.posteriors[sc] * self.class_profiles[sc]["c_kPa"] for sc in self.soil_classes
        ))
        self.estimated_friction_deg = float(sum(
            self.posteriors[sc] * self.class_profiles[sc]["phi_deg"] for sc in self.soil_classes
        ))
        
        # Most probable soil classification
        dominant_class = max(self.posteriors, key=self.posteriors.get)
        
        return {
            'update_count': self.update_count,
            'dominant_soil_class': dominant_class,
            'dominant_probability': round(self.posteriors[dominant_class], 4),
            'posteriors': {k: round(v, 4) for k, v in self.posteriors.items()},
            'estimated_cohesion_kPa': round(self.estimated_cohesion_kPa, 3),
            'estimated_friction_deg': round(self.estimated_friction_deg, 2)
        }


class SlipAnticipationSentinel:
    """Predictive watchdog alerting autonomy to upcoming immobilization traps."""
    def __init__(self, critical_slip_threshold: float = 0.40):
        self.critical_slip = critical_slip_threshold

    def evaluate_predictive_risk(
        self,
        current_slip: float,
        bayesian_soil: Dict,
        upcoming_slope_deg: float
    ) -> Dict:
        """Evaluates whether current trajectory will lead to entrapment."""
        drift_sand_prob = bayesian_soil.get('posteriors', {}).get('drift_sand', 0.0)
        loose_dust_prob = bayesian_soil.get('posteriors', {}).get('loose_dust', 0.0)
        soft_soil_risk = drift_sand_prob + loose_dust_prob
        
        # Projected slip = current_slip + slope_factor * soft_soil_risk
        slope_factor = math.sin(math.radians(max(0.0, upcoming_slope_deg)))
        predicted_slip = current_slip + 0.85 * slope_factor * soft_soil_risk
        predicted_slip = float(np.clip(predicted_slip, 0.0, 1.0))
        
        is_warning = (predicted_slip >= self.critical_slip)
        action_recommended = (
            "EMERGENCY_HALT" if predicted_slip > 0.60
            else ("ENGAGE_WHEEL_WALKING" if is_warning else "NOMINAL_PROCEED")
        )
        
        return {
            'current_slip': round(current_slip, 3),
            'predicted_slip': round(predicted_slip, 3),
            'soft_soil_probability': round(soft_soil_risk, 3),
            'is_anticipation_warning': is_warning,
            'recommended_action': action_recommended
        }
