"""Level 1 Evaluation and Statistics subpackage."""
from level1.evaluation.stats import boot_clusters, boot_paired_clusters, wilson, rule_of_three, clusters_needed_zero_events
from level1.evaluation.audit_repo import audit_repo
from level1.evaluation.label_script import level1_label, release_gate, KEYS
from level1.evaluation.manifest import sha256_file, build_manifest, verify_manifest, prereg_hash
from level1.evaluation.report_generator import md_table, mission_metrics, false_safe_map

__all__ = [
    "boot_clusters", "boot_paired_clusters", "wilson", "rule_of_three", "clusters_needed_zero_events",
    "audit_repo", "level1_label", "release_gate", "KEYS",
    "sha256_file", "build_manifest", "verify_manifest", "prereg_hash",
    "md_table", "mission_metrics", "false_safe_map"
]
