"""
guard_evaluator.py — 瑶灵安全守门评估器
=========================================
规格依据: YAOLING_DOMAIN_SPEC.md §3（安全阈值与拒绝执行规则）
执行模式: STRICT — danger 级直接拒绝，不可降级
使用方: wf_safety_gate.yaml 各节点的守门规则回调

每个 evaluate_* 函数返回 (GuardAction, 消息)，
与 Harris 工作流引擎的 WorkflowGuard.evaluate_all() 完全兼容。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from .threshold_registry import (
    THRESHOLD_REGISTRY,
    D32_VITAL_THRESHOLDS,
    DimensionThreshold,
    ThresholdLevel,
    VitalSignThreshold,
    get_threshold,
    get_vital_threshold,
)


# ---------------------------------------------------------------------------
# 评估结果
# ---------------------------------------------------------------------------


class GuardAction(Enum):
    """与 Harris core 的 GuardAction 语义对齐。"""
    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"
    DEFER = "defer"


@dataclass
class Violation:
    """单条违规记录。"""
    dim_id: int
    dim_key: str
    medical_metric: str
    current_value: float
    threshold_level: ThresholdLevel
    threshold_range: str
    tip: str


@dataclass
class SafetyVerdict:
    """安全评估最终判定。"""
    passed: bool                               # 全部通过
    danger_count: int
    risk_count: int
    sub_healthy_count: int
    healthy_count: int
    violations: List[Violation] = field(default_factory=list)
    overall_level: ThresholdLevel = ThresholdLevel.HEALTHY
    d32_vital_violations: List[Violation] = field(default_factory=list)
    reject_reason: str = ""                     # danger 级拒绝原因摘要


# ---------------------------------------------------------------------------
# 核心评估函数
# ---------------------------------------------------------------------------


def evaluate_dimension(
    dim_id: int,
    medical_value: float,
    dna_root_id: str = "",
) -> Tuple[GuardAction, str, Optional[Violation]]:
    """
    对单个维度执行安全阈值评估。

    Returns:
      - (ALLOW, msg, None)        — 通过
      - (WARN, msg, Violation)    — 亚健康/风险
      - (DENY, msg, Violation)    — 危险 → 拒绝
    """
    threshold = get_threshold(dim_id)
    level = threshold.evaluate(medical_value)
    tip = threshold.get_tip(level)

    violation = Violation(
        dim_id=dim_id,
        dim_key=threshold.dim_key,
        medical_metric=threshold.medical_metric,
        current_value=medical_value,
        threshold_level=level,
        threshold_range=_range_str(threshold, level),
        tip=tip,
    )

    dna_tag = f" [{dna_root_id}]" if dna_root_id else ""

    if level == ThresholdLevel.DANGER:
        return (
            GuardAction.DENY,
            f"🔴 D{dim_id} {threshold.label_cn} | {threshold.medical_metric}={medical_value}{threshold.medical_unit} "
            f"| 危险阈值{_range_str(threshold, level)} | {tip}{dna_tag}",
            violation,
        )

    if level == ThresholdLevel.RISK:
        return (
            GuardAction.WARN,
            f"🟡 D{dim_id} {threshold.label_cn} | {threshold.medical_metric}={medical_value}{threshold.medical_unit} "
            f"| 风险区间{_range_str(threshold, level)} | {tip}{dna_tag}",
            violation,
        )

    if level == ThresholdLevel.SUB_HEALTHY:
        return (
            GuardAction.ALLOW,
            f"🟢 D{dim_id} {threshold.label_cn} | {threshold.medical_metric}={medical_value}{threshold.medical_unit} "
            f"| 亚健康{_range_str(threshold, level)} | {tip}{dna_tag}",
            violation,
        )

    return (
        GuardAction.ALLOW,
        f"✅ D{dim_id} {threshold.label_cn} | {threshold.medical_metric}={medical_value}{threshold.medical_unit} | 健康正常{dna_tag}",
        None,
    )


def evaluate_d32_vital_sign(
    metric: str,
    current_value: float,
    dna_root_id: str = "",
) -> Tuple[GuardAction, str, Optional[Violation]]:
    """
    对 D32 核心生命体征单独评估（心率/血压/皮质醇均值/愉悦激素均值）。

    与 evaluate_dimension 的区别：
      D32 的核心生命体征有独立阈值（VitalSignThreshold），
      不通过统一的 DimensionThreshold 体系——因为 D32 的 medical_metric 是"综合健康指数"，
      而心率/血压/皮质醇均值是它的子指标。
    """
    vt = get_vital_threshold(metric)
    dna_tag = f" [{dna_root_id}]" if dna_root_id else ""

    # danger 判定
    danger = False
    if vt.danger_lo is not None and current_value <= vt.danger_lo:
        danger = True
    if vt.danger_hi is not None and current_value >= vt.danger_hi:
        danger = True

    if danger:
        violation = Violation(
            dim_id=32,
            dim_key="holistic_state",
            medical_metric=f"D32.{metric}",
            current_value=current_value,
            threshold_level=ThresholdLevel.DANGER,
            threshold_range=f"危险: <{vt.danger_lo}" if vt.danger_lo else f"危险: >{vt.danger_hi}",
            tip=f"⚠️ {vt.label_cn} 触达危险阈值",
        )
        return (
            GuardAction.DENY,
            f"🔴 D32 核心生命体征 | {vt.label_cn}={current_value}{vt.unit} "
            f"| 危险阈值 | 健康参考 {vt.healthy_lo}-{vt.healthy_hi}{vt.unit}{dna_tag}",
            violation,
        )

    # warning 判定
    if current_value < vt.healthy_lo or current_value > vt.healthy_hi:
        violation = Violation(
            dim_id=32,
            dim_key="holistic_state",
            medical_metric=f"D32.{metric}",
            current_value=current_value,
            threshold_level=ThresholdLevel.SUB_HEALTHY,
            threshold_range=f"健康: {vt.healthy_lo}-{vt.healthy_hi}",
            tip=f"{vt.label_cn} 偏离健康区间",
        )
        return (
            GuardAction.WARN,
            f"🟡 D32 核心生命体征 | {vt.label_cn}={current_value}{vt.unit} "
            f"| 偏离健康区间({vt.healthy_lo}-{vt.healthy_hi}){dna_tag}",
            violation,
        )

    return (GuardAction.ALLOW, f"✅ D32 {vt.label_cn}={current_value}{vt.unit} | 正常{dna_tag}", None)


def evaluate_all_dimensions(
    channel_states: Dict[int, float],
    d32_vitals: Optional[Dict[str, float]] = None,
    dna_root_id: str = "",
) -> SafetyVerdict:
    """
    对全部 32 维执行批量安全评估。

    Args:
        channel_states: {dim_id: medical_value} 字典
        d32_vitals: {"heart_rate": 72, "blood_pressure_sys": 118, ...}
        dna_root_id: DNA时序锚点

    Returns:
        SafetyVerdict — 包含完整的违规列表和最终判定
    """
    violations: List[Violation] = []
    danger_count = 0
    risk_count = 0
    sub_healthy_count = 0
    healthy_count = 0

    for dim_id in range(1, 33):
        if dim_id not in channel_states:
            # 缺失维度视为 risk（不完整快照不应通过）
            risk_count += 1
            violations.append(Violation(
                dim_id=dim_id, dim_key="unknown", medical_metric="缺失",
                current_value=float("nan"), threshold_level=ThresholdLevel.RISK,
                threshold_range="N/A", tip=f"D{dim_id} 通道数据缺失",
            ))
            continue

        action, msg, violation = evaluate_dimension(
            dim_id, channel_states[dim_id], dna_root_id
        )

        if action == GuardAction.DENY:
            danger_count += 1
            if violation:
                violations.append(violation)
        elif violation and violation.threshold_level == ThresholdLevel.RISK:
            risk_count += 1
            violations.append(violation)
        elif violation and violation.threshold_level == ThresholdLevel.SUB_HEALTHY:
            sub_healthy_count += 1
        else:
            healthy_count += 1

    # D32 核心生命体征独立校验
    d32_vital_violations: List[Violation] = []
    if d32_vitals:
        for vt in D32_VITAL_THRESHOLDS:
            if vt.metric not in d32_vitals:
                continue
            action, msg, violation = evaluate_d32_vital_sign(
                vt.metric, d32_vitals[vt.metric], dna_root_id
            )
            if action == GuardAction.DENY:
                danger_count += 1
                if violation:
                    d32_vital_violations.append(violation)
            elif violation:
                d32_vital_violations.append(violation)

    # 汇总
    passed = danger_count == 0
    overall = ThresholdLevel.HEALTHY
    reject_reason = ""

    if danger_count > 0:
        overall = ThresholdLevel.DANGER
        reject_reason = (
            f"安全守门拒绝: {danger_count} 个维度触达危险阈值。"
            f"违规维度: {[v.dim_id for v in violations if v.threshold_level == ThresholdLevel.DANGER]} "
            f"+ D32 核心生命体征违规: {[v.medical_metric for v in d32_vital_violations if v.threshold_level == ThresholdLevel.DANGER]}"
        )
    elif risk_count > 0:
        overall = ThresholdLevel.RISK

    return SafetyVerdict(
        passed=passed,
        danger_count=danger_count,
        risk_count=risk_count,
        sub_healthy_count=sub_healthy_count,
        healthy_count=healthy_count,
        violations=violations,
        overall_level=overall,
        d32_vital_violations=d32_vital_violations,
        reject_reason=reject_reason,
    )


def build_reject_report(verdict: SafetyVerdict, dna_root_id: str) -> Dict[str, Any]:
    """
    生成符合规范 §3.5 的 REJECT_REPORT。

    在 wf_safety_gate.yaml 的 n9_final_verdict 节点中调用。
    """
    danger_violations = [
        {
            "dim_id": v.dim_id,
            "dim_key": v.dim_key,
            "medical_metric": v.medical_metric,
            "current_value": v.current_value,
            "threshold_range": v.threshold_range,
            "tip": v.tip,
        }
        for v in verdict.violations
        if v.threshold_level == ThresholdLevel.DANGER
    ] + [
        {
            "dim_id": 32,
            "medical_metric": v.medical_metric,
            "current_value": v.current_value,
            "threshold_range": v.threshold_range,
            "tip": v.tip,
        }
        for v in verdict.d32_vital_violations
        if v.threshold_level == ThresholdLevel.DANGER
    ]

    return {
        "code": -99,
        "reject_reason": "SAFETY_THRESHOLD_EXCEEDED",
        "dna_root_id": dna_root_id,
        "danger_count": verdict.danger_count,
        "danger_violations": danger_violations,
        "overall_level": verdict.overall_level.value,
        "recommended_action": "立即停止当前交互，触发 global_alert，等待天权调控指令",
    }


# ---------------------------------------------------------------------------
# Harris 守门回调工厂 — 生成符合 WorkflowGuard 格式的回调函数
# ---------------------------------------------------------------------------


def make_threshold_callback(dim_id: int, max_value: Optional[float] = None, min_value: Optional[float] = None):
    """
    生成 Harris 守门规则的回调函数。

    用法（在 YAML guard 中）:
        checker: make_threshold_callback(4, max_value=25.0)  # D4 皮质醇不得 > 25
    """
    def checker(ctx):
        # ctx.artifacts 中查找该维度的 medical_value
        artifacts = getattr(ctx, "artifacts", {})
        key = f"d{dim_id}_result"
        if key in artifacts:
            value = artifacts[key].medical_value
            if max_value is not None and value > max_value:
                return (GuardAction.DENY, f"D{dim_id}值{value}超过危险上限{max_value}")
            if min_value is not None and value < min_value:
                return (GuardAction.DENY, f"D{dim_id}值{value}低于危险下限{min_value}")
        return (GuardAction.ALLOW, "")
    return checker


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------


def _range_str(threshold: DimensionThreshold, level: ThresholdLevel) -> str:
    """生成人类可读的阈值区间字符串。"""
    lo, hi = getattr(threshold, f"{level.value}_range")
    unit = threshold.medical_unit
    if lo is not None and hi is not None:
        return f"[{lo}-{hi}{unit}]"
    if lo is not None:
        return f"[≤{lo}{unit}]"
    if hi is not None:
        return f"[≥{hi}{unit}]"
    return "[N/A]"
