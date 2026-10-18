"""Evaluation and statistical analysis subpackage for APPS."""
from evaluation.bootstrap import boot_mean, boot_paired, boot_pooled_false_safe, upper_bound_zero_events
from evaluation.cluster_bootstrap import boot_clusters, boot_paired_clusters
from evaluation.fault_injection import depth_dropout, depth_nan, blackout, saturate, add_noise, stuck_frame, corrupt_bytes
from evaluation.failure_review import object_miss_rate, review_table
from evaluation.timing import time_stage
from evaluation.seeds import scene_seeds, check_disjoint, write_registry, wilson, n_for_halfwidth, n_for_paired_halfwidth, rule_of_three

__all__ = [
    "boot_mean", "boot_paired", "boot_pooled_false_safe", "upper_bound_zero_events",
    "boot_clusters", "boot_paired_clusters",
    "depth_dropout", "depth_nan", "blackout", "saturate", "add_noise", "stuck_frame", "corrupt_bytes",
    "object_miss_rate", "review_table", "time_stage",
    "scene_seeds", "check_disjoint", "write_registry", "wilson", "n_for_halfwidth", "n_for_paired_halfwidth", "rule_of_three"
]
