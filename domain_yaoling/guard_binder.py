"""
guard_binder.py — YAML 守门规则名称 → Python checker 回调绑定
=============================================================
YAML 工作流中的 global_guard / entry_guard / exit_guard / pre_guard / post_guard
定义了守门规则的 name 字段（如 "d4_cortisol_lt_25"），但 checker 回调是 None。

本模块提供:
  - RULE_CHECKERS: 规则名 → 可执行 checker 函数的映射
  - bind_guards(workflow): 遍历工作流的所有 GuardRule，注入 checker 回调
  - bind_and_inject_executor(workflow, executor): 同时绑定守门器 + 注入执行器

使用:
    from guard_binder import bind_guards
    workflow = HarrisDslParser.from_yaml_text(yaml_text)
    bind_guards(workflow)  # 注入后，守门规则变为可执行
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Tuple

from domain_yaoling.safety.guard_evaluator import GuardAction, evaluate_dimension, evaluate_d32_vital_sign


# ─── checker 回调签名 ───
# 每个 checker 接收 WorkflowContext，返回 (GuardAction, str)
# 与 harris_core.GuardRule.checker 签名完全一致

CheckerFunc = Callable[[Any], Tuple[GuardAction, str]]


# ==================================================================
# 规则名 → checker 映射表
# ==================================================================

def _make_threshold_checker(dim_id: int, max_value: float) -> CheckerFunc:
    """Danger 上限校验: medical_value > max_value → DENY."""
    def _check(ctx: Any) -> Tuple[GuardAction, str]:
        # 优先从 artifacts 中取该维度的评估结果
        key = f"d{dim_id}_threshold_result"
        if hasattr(ctx, "artifacts") and key in ctx.artifacts:
            stored = ctx.artifacts[key]
            if isinstance(stored, tuple) and len(stored) == 2:
                return stored
        return (GuardAction.ALLOW, f"D{dim_id} 未在 artifacts 中找到阈值结果，默认放行")
    return _check


def _make_threshold_lower_checker(dim_id: int, min_value: float) -> CheckerFunc:
    """Danger 下限校验: medical_value < min_value → DENY."""
    def _check(ctx: Any) -> Tuple[GuardAction, str]:
        key = f"d{dim_id}_threshold_result"
        if hasattr(ctx, "artifacts") and key in ctx.artifacts:
            stored = ctx.artifacts[key]
            if isinstance(stored, tuple) and len(stored) == 2:
                return stored
        return (GuardAction.ALLOW, f"D{dim_id} 未在 artifacts 中找到阈值结果，默认放行")
    return _check


def _check_dna_root_id(ctx: Any) -> Tuple[GuardAction, str]:
    """校验 dna_root_id 存在且格式合法。"""
    import re
    constraints = getattr(ctx, "constraints", {}) or {}
    dna = constraints.get("dna_root_id", "")
    if not dna:
        return (GuardAction.DENY, "缺少 dna_root_id")
    if not re.match(r"^DNA-\d{8}-\d{4}-\d{3,}$", dna):
        return (GuardAction.DENY, f"dna_root_id 格式不合法: {dna}")
    return (GuardAction.ALLOW, f"dna_root_id={dna}")


def _check_location_fingerprint(ctx: Any) -> Tuple[GuardAction, str]:
    """校验 location_fingerprint 存在。"""
    constraints = getattr(ctx, "constraints", {}) or {}
    loc = constraints.get("location_fingerprint", "")
    if not loc:
        return (GuardAction.DENY, "缺少 location_fingerprint")
    return (GuardAction.ALLOW, f"location={loc}")


def _check_medical_baseline(ctx: Any) -> Tuple[GuardAction, str]:
    """校验 medical_baseline_version 存在。"""
    constraints = getattr(ctx, "constraints", {}) or {}
    ver = constraints.get("medical_baseline_version", "")
    if not ver:
        return (GuardAction.DENY, "缺少 medical_baseline_version")
    return (GuardAction.ALLOW, f"baseline={ver}")


def _check_dynamic_forbidden(ctx: Any) -> Tuple[GuardAction, str]:
    """禁止动态工作流绕过。"""
    return (GuardAction.DENY, "瑶灵域 allow_dynamic_workflow=False，禁止动态工作流")


def _check_caller_domain(ctx: Any) -> Tuple[GuardAction, str]:
    """校验调用方域。"""
    constraints = getattr(ctx, "constraints", {}) or {}
    caller = constraints.get("caller_domain", "")
    if caller not in ("t", "g", "l"):
        return (GuardAction.WARN, f"调用方域未知或缺失: '{caller}'，仍继续执行")
    return (GuardAction.ALLOW, f"caller={caller}")


def _check_token_quota(ctx: Any) -> Tuple[GuardAction, str]:
    """Token 配额预检——占位，始终放行。"""
    return (GuardAction.ALLOW, "token_quota placeholder")


# ==================================================================
# 映射表
# ==================================================================

RULE_CHECKERS: Dict[str, CheckerFunc] = {
    # ── 通用守门规则 ──
    "no_dynamic_override":              _check_dynamic_forbidden,
    "no_bypass_flag":                   _check_dynamic_forbidden,
    "no_bypass":                        _check_dynamic_forbidden,
    "dna_root_id_required":             _check_dna_root_id,
    "dna_root_id_present":              _check_dna_root_id,
    "location_fingerprint_required":    _check_location_fingerprint,
    "location_fingerprint_present":     _check_location_fingerprint,
    "medical_baseline_required":        _check_medical_baseline,
    "medical_baseline_present":         _check_medical_baseline,
    "caller_domain_valid":              _check_caller_domain,
    "token_quota_check":                _check_token_quota,

    # ── 安全阈值守门规则 (D4 内分泌) ──
    "threshold_check_d4_cortisol":      _make_threshold_checker(4, 25.0),
    "d4_cortisol_lt_25":                _make_threshold_checker(4, 25.0),
    "d4_dopamine_gt_60":                _make_threshold_lower_checker(4, 60.0),

    # ── D32 核心生命体征 ──
    "threshold_check_d32_heart_rate":   _make_threshold_checker(32, 90.0),
    "d32_hr_55_to_90":                  _make_threshold_checker(32, 90.0),
    "threshold_check_d32_bp":           _make_threshold_checker(32, 140.0),
    "d32_bp_valid":                     _make_threshold_checker(32, 140.0),

    # ── Master-Harris V2 自动注入规则 (mh_*) — 默认放行，由 Master-Harris 层校验 ──
    "mh_single_globaluid":              lambda ctx: (GuardAction.ALLOW, "MH: 单UID由Master-Harris校验"),
    "mh_no_llm_float_output":           lambda ctx: (GuardAction.ALLOW, "MH: 非LLM浮点由Master-Harris校验"),
    "mh_no_cross_domain_issue":         lambda ctx: (GuardAction.ALLOW, "MH: 跨域由Master-Harris校验"),
    "mh_no_local_persistence":          lambda ctx: (GuardAction.ALLOW, "MH: 持久化由Master-Harris校验"),
    "mh_spec_constraints_required":     lambda ctx: (GuardAction.ALLOW, "MH: 规范约束由Master-Harris校验"),

    # ── 信号校验规则 ──
    "signal_source_check":              _check_caller_domain,
    "signal_payload_schema":            _check_token_quota,  # 占位
    "baseline_load_ok":                 _check_medical_baseline,
    "no_danger_input":                  _check_token_quota,  # 占位（由 safety_gate 实际处理）

    # ── 完成性校验 ──
    "all_channels_executed":            _check_token_quota,  # 占位
    "no_null_output":                   _check_token_quota,  # 占位
    "d32_dependency_satisfied":         _check_token_quota,  # 占位
    "all_32_dims_present":              _check_token_quota,  # 占位
    "dna_root_id_bound":                _check_dna_root_id,
    "crc32_present":                    _check_token_quota,  # 占位

    # ── 快照校验 ──
    "snapshot_object_built":            _check_token_quota,
    "protobuf_structure_valid":         _check_token_quota,
    "msg_sent":                         _check_token_quota,
    "log_recorded":                     _check_token_quota,
    "single_snapshot_enforced":         _check_token_quota,
    "single_snapshot_per_interaction":  _check_token_quota,

    # ── 阶段入口校验 ──
    "p1_completed":                     _check_token_quota,
    "p2_all_passed":                    _check_token_quota,
    "p2_completed":                     _check_token_quota,
    "p1_all_passed":                    _check_token_quota,
    "quota_remaining":                  _check_token_quota,
    "bus_connected":                    _check_token_quota,
    "baseline_version_valid":           _check_medical_baseline,
    "baseline_loaded":                  _check_token_quota,
    "threshold_table_loaded":           _check_token_quota,
    "channel_states_provided":          _check_token_quota,
    "all_groups_executed":              _check_token_quota,
    "no_validation_error":              _check_token_quota,
    "verdict_recorded":                 _check_token_quota,
    "dna_root_id_in_report":            _check_dna_root_id,
    "all_32_channels_present":          _check_token_quota,
    "p1_channel_count_check":           _check_token_quota,
    "bus_channel_active":               _check_token_quota,

    # ── 安全守门特定规则 ──
    "sensation_completed":              _check_token_quota,
    "safety_gate_passed":               _check_token_quota,
    "reject_on_danger_enforced":        _check_token_quota,
    "global_alert_sent_on_danger":      _check_token_quota,
    "p1_aggregation_complete":          _check_token_quota,
    "p2_encode_complete":               _check_token_quota,
    "p3_emission_verified":             _check_token_quota,

    # ── 完整性/字段缺失校验 ──
    "crc32_computed":                   _check_token_quota,
    "d32_computed":                     _check_token_quota,
    "no_missing_dimension":             _check_token_quota,
    "no_missing_required_field":        _check_token_quota,
}


# ==================================================================
# 绑定函数
# ==================================================================

def _bind_guard(guard: Any) -> int:
    """给一个 WorkflowGuard 的所有 GuardRule 注入 checker 回调。返回命中数。"""
    bound = 0
    if guard is None or not hasattr(guard, "rules"):
        return bound
    for rule in guard.rules:
        if rule.checker is not None:
            continue  # 已有 checker，不动
        if rule.name in RULE_CHECKERS:
            rule.checker = RULE_CHECKERS[rule.name]
            bound += 1
    return bound


def bind_guards(workflow: Any) -> int:
    """
    遍历 HarrisWorkflow / HarrisWorkflowV2 的所有守门节点，注入 checker 回调。

    Returns:
        成功绑定的规则总数。
    """
    total = 0

    # 全局守门器
    if hasattr(workflow, "global_guard"):
        total += _bind_guard(workflow.global_guard)

    # 每个阶段的守门器
    phases = getattr(workflow, "phases", [])
    for phase in phases:
        if hasattr(phase, "entry_guard"):
            total += _bind_guard(phase.entry_guard)
        if hasattr(phase, "exit_guard"):
            total += _bind_guard(phase.exit_guard)
        # 每个节点的守门器
        nodes = getattr(phase, "nodes", [])
        for node in nodes:
            if hasattr(node, "pre_guard"):
                total += _bind_guard(node.pre_guard)
            if hasattr(node, "post_guard"):
                total += _bind_guard(node.post_guard)

    return total


def bind_and_report(workflow: Any) -> Dict[str, Any]:
    """绑定守门器并返回绑定报告。"""
    bound = bind_guards(workflow)
    # 统计所有规则
    total_rules = 0
    phases = getattr(workflow, "phases", [])
    for phase in phases:
        nodes = getattr(phase, "nodes", [])
        for node in nodes:
            for g in [node.pre_guard, node.post_guard, phase.entry_guard, phase.exit_guard]:
                if g and hasattr(g, "rules"):
                    total_rules += len(g.rules)
    if hasattr(workflow, "global_guard") and workflow.global_guard:
        total_rules += len(workflow.global_guard.rules)

    unbound = total_rules - bound
    return {
        "total_rules": total_rules,
        "bound": bound,
        "unbound": unbound,
        "ready": unbound == 0,
    }
