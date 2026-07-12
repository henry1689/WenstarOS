"""
test_threshold_guard.py — 安全阈值守门器单元测试
==================================================
验证 threshold_registry 和 guard_evaluator 的正确性。
"""

import sys
from pathlib import Path
_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from safety.threshold_registry import THRESHOLD_REGISTRY, D32_VITAL_THRESHOLDS, get_threshold, get_vital_threshold, ThresholdLevel
from safety.guard_evaluator import evaluate_dimension, evaluate_d32_vital_sign, evaluate_all_dimensions, build_reject_report, GuardAction


def test_all_32_dimensions_have_thresholds():
    """验证全部32维都有阈值定义。"""
    for dim_id in range(1, 33):
        assert dim_id in THRESHOLD_REGISTRY, f"缺失 D{dim_id} 阈值"
    print("OK  32 维阈值全部定义")


def test_danger_thresholds_reject():
    """验证危险阈值触发拒绝。"""
    # D4 皮质醇 > 25 → DENY
    action, msg, violation = evaluate_dimension(4, 26.0)
    assert action == GuardAction.DENY, f"D4 26μg/dL 应拒绝, 实际: {action}"
    assert violation is not None
    assert violation.threshold_level == ThresholdLevel.DANGER
    print("OK  D4 皮质醇 26μg/dL → 正确拒绝")

    # D32 心率 95 (>90) → DENY（通过D32生命体征）
    action, msg, violation = evaluate_d32_vital_sign("heart_rate", 95)
    assert action == GuardAction.DENY, f"D32 心率95应拒绝, 实际: {action}"
    print("OK  D32 心率 95bpm → 正确拒绝")

    # D32 心率 50 (<55) → DENY
    action, msg, violation = evaluate_d32_vital_sign("heart_rate", 50)
    assert action == GuardAction.DENY, f"D32 心率50应拒绝, 实际: {action}"
    print("OK  D32 心率 50bpm → 正确拒绝")

    # D32 血压 145 (>140) → DENY
    action, msg, violation = evaluate_d32_vital_sign("blood_pressure_sys", 145)
    assert action == GuardAction.DENY, f"D32 高压145应拒绝, 实际: {action}"
    print("OK  D32 高压 145mmHg → 正确拒绝")


def test_healthy_values_pass():
    """验证健康值通过。"""
    # D4 皮质醇 14 → ALLOW
    action, msg, violation = evaluate_dimension(4, 14.0)
    assert action == GuardAction.ALLOW
    print("OK  D4 皮质醇 14μg/dL → 正确放行")

    # D32 心率 66 → ALLOW
    action, msg, violation = evaluate_d32_vital_sign("heart_rate", 66)
    assert action == GuardAction.ALLOW
    print("OK  D32 心率 66bpm → 正确放行")


def test_batch_evaluation():
    """验证批量评估。"""
    states = {i: get_threshold(i).medical_baseline for i in range(1, 33)}
    # 手动插入危险值
    states[4] = 26.0
    vitals = {"heart_rate": 95, "blood_pressure_sys": 118, "blood_pressure_dia": 75, "cortisol_avg": 14, "pleasure_hormone_avg": 120}
    verdict = evaluate_all_dimensions(states, vitals, "DNA-20260711-0000-001")
    assert not verdict.passed
    assert verdict.danger_count >= 2  # D4 + D32心率
    report = build_reject_report(verdict, "DNA-20260711-0000-001")
    assert report["code"] == -99
    assert report["reject_reason"] == "SAFETY_THRESHOLD_EXCEEDED"
    print(f"OK  批量评估: danger={verdict.danger_count}, passed={verdict.passed}")


def test_d32_all_vital_signs():
    """验证 D32 五项生命体征全部有阈值。"""
    expected = {"heart_rate", "blood_pressure_sys", "blood_pressure_dia", "cortisol_avg", "pleasure_hormone_avg"}
    actual = {vt.metric for vt in D32_VITAL_THRESHOLDS}
    assert actual == expected, f"生命体征不匹配: {actual}"
    print("OK  D32 五项核心生命体征完整")


if __name__ == "__main__":
    test_all_32_dimensions_have_thresholds()
    test_danger_thresholds_reject()
    test_healthy_values_pass()
    test_batch_evaluation()
    test_d32_all_vital_signs()
    print("\nPASS  全部安全阈值测试通过")
