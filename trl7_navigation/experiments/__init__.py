"""Experiments, campaign runner, baselines, and ablation studies package for TRL 7 operational prototype."""
from trl7_navigation.experiments.baselines import PureOdometryBaseline, GeometricGridAStar
from trl7_navigation.experiments.ablations import AblationStudyRunner
from trl7_navigation.experiments.campaign_runner import CampaignRunner, compute_wilson_ci

__all__ = [
    "PureOdometryBaseline",
    "GeometricGridAStar",
    "AblationStudyRunner",
    "CampaignRunner",
    "compute_wilson_ci",
]
