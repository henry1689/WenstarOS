"""safety/ — 瑶灵安全阈值校验模块"""

from .threshold_registry import (
    THRESHOLD_REGISTRY, D32_VITAL_THRESHOLDS, DimensionThreshold,
    VitalSignThreshold, ThresholdLevel, get_threshold, get_vital_threshold,
    all_thresholds,
)
from .guard_evaluator import (
    GuardAction, Violation, SafetyVerdict,
    evaluate_dimension, evaluate_d32_vital_sign,
    evaluate_all_dimensions, build_reject_report,
)

__all__ = [
    "THRESHOLD_REGISTRY", "D32_VITAL_THRESHOLDS", "DimensionThreshold",
    "VitalSignThreshold", "ThresholdLevel", "get_threshold", "get_vital_threshold",
    "all_thresholds",
    "GuardAction", "Violation", "SafetyVerdict",
    "evaluate_dimension", "evaluate_d32_vital_sign",
    "evaluate_all_dimensions", "build_reject_report",
]
