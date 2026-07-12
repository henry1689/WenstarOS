"""
workflow_executor.py — 瑶灵工作流执行器
=========================================
将三套 YAML 工作流的每个 AgentNode 映射到可执行 Python 函数。
作为 HarrisOrchestrator.run() 的 node_executor 回调。

三阶段流水线:
  wf_sensation_pipeline → wf_safety_gate → wf_yaoling_snapshot

共享状态通过 WorkflowContext.artifacts 传递。
"""

from __future__ import annotations

import json
import sys
import time
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

_SELF = Path(__file__).resolve()
_PARENT = _SELF.parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from domain_yaoling.channels import create_all_channels, SignalInput, get_channel
from domain_yaoling.channels.base_channel import SensationResult, OrganState, HealthLevel, Intensity
from domain_yaoling.safety.threshold_registry import THRESHOLD_REGISTRY, D32_VITAL_THRESHOLDS, ThresholdLevel
from domain_yaoling.safety.guard_evaluator import (
    evaluate_dimension, evaluate_d32_vital_sign,
    evaluate_all_dimensions, build_reject_report,
    SafetyVerdict, Violation, GuardAction,
)
from domain_yaoling.codec.sensation_encoder import SensationEncoder, SpineSnapshot, to_protobuf_dict
from domain_yaoling.codec.sensation_decoder import SensationDecoder

# ---------------------------------------------------------------------------
# 共享状态 Key 常量
# ---------------------------------------------------------------------------

class ArtifactKeys:
    SIGNAL_INPUT = "signal_input"
    SCENE_CONTEXT = "scene_context"
    CHANNEL_RESULTS = "channel_results"       # Dict[int, SensationResult]
    D32_ORGAN_STATE = "d32_organ_state"       # OrganState from compute_holistic
    MEDICAL_VALUES = "medical_values"         # Dict[int, float] — organ_state clinical values
    SAFETY_VERDICT = "safety_verdict"         # SafetyVerdict
    SNAPSHOT = "spine_snapshot"              # SpineSnapshot
    PROTOBUF_DICT = "protobuf_dict"           # Dict ready for Transcoder
    REJECT_REPORT = "reject_report"           # Dict from build_reject_report
    EMISSION_LOG = "emission_log"            # List of emission records
    DNA_ROOT_ID = "dna_root_id"
    LOCATION_FINGERPRINT = "location_fingerprint"
    BASELINE_VERSION = "baseline_version"

# ---------------------------------------------------------------------------
# 执行器
# ---------------------------------------------------------------------------

class YaolingWorkflowExecutor:
    """
    瑶灵三阶段工作流执行器。

    用法:
        executor = YaolingWorkflowExecutor()
        result = executor.run_full_pipeline(
            signal_input=SignalInput(...),
            dna_root_id="DNA-20260711-2300-001",
            location_fingerprint="home.bedroom.night",
        )
    """

    def __init__(self):
        self._channels = create_all_channels()
        self._encoder = SensationEncoder()
        self._emission_log: List[Dict[str, Any]] = []

    # ==================================================================
    # 顶层入口: 完整三阶段
    # ==================================================================

    def run_full_pipeline(
        self,
        signal_input: SignalInput,
        dna_root_id: str,
        location_fingerprint: str = "",
        dialog_group_id: str = "",
        medical_baseline_version: str = "YAOGUANG-MED-001",
    ) -> Dict[str, Any]:
        """
        执行完整三阶段流水线，返回最终结果。

        返回值:
          {"code": 0/-99, "snapshot": ..., "safety_verdict": ..., "vital_signs": ...}
        """
        ctx: Dict[str, Any] = {
            ArtifactKeys.SIGNAL_INPUT: signal_input,
            ArtifactKeys.DNA_ROOT_ID: dna_root_id,
            ArtifactKeys.LOCATION_FINGERPRINT: location_fingerprint,
            ArtifactKeys.BASELINE_VERSION: medical_baseline_version,
        }
        ctx["dialog_group_id"] = dialog_group_id

        # ── P1: 体感流水线 ──
        p1_result = self._execute_sensation_pipeline(ctx)
        if p1_result.get("code", 0) != 0:
            return p1_result

        # ── P2: 安全守门 ──
        p2_result = self._execute_safety_gate(ctx)
        # ── P3: 快照发射（即使被拒也输出快照用于诊断）──
        p3_result = self._execute_snapshot_pipeline(ctx)
        if p2_result.get("code", 0) != 0:
            p3_result["code"] = -99
            p3_result["safety_reject"] = True
            p3_result["danger_count"] = p2_result.get("danger_count", 0)
            p3_result["reject_reason"] = p2_result.get("reject_reason", "")
        return p3_result

    # ==================================================================
    # P1: 体感流水线
    # ==================================================================

    def _execute_sensation_pipeline(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """执行 wf_sensation_pipeline 全部节点。"""
        signal: SignalInput = ctx[ArtifactKeys.SIGNAL_INPUT]

        # n1: 信号接收与校验
        self._validate_signal(signal, ctx)

        # n2: 提取场景上下文
        scene = self._extract_scene_context(signal)
        ctx[ArtifactKeys.SCENE_CONTEXT] = scene

        # n3: 校验输入参数（检查医学基准）
        self._validate_input_against_baseline(signal, ctx)

        # n4-n8: 32通道器官响应（五大类并行，但 Python 层面串行执行）
        results: Dict[int, SensationResult] = {}

        # 大类1: D1-D8 肉身实体基底
        for dim_id in range(1, 9):
            results[dim_id] = self._channels[dim_id].process(signal)

        # 大类2: D9-D14 精神内核
        for dim_id in range(9, 15):
            results[dim_id] = self._channels[dim_id].process(signal)

        # 大类3: D15-D20 人际羁绊
        for dim_id in range(15, 21):
            results[dim_id] = self._channels[dim_id].process(signal)

        # 大类4: D21-D26 时空环境
        for dim_id in range(21, 27):
            results[dim_id] = self._channels[dim_id].process(signal)

        # 大类5: D27-D32 动态生长（D32 特殊处理）
        for dim_id in range(27, 32):
            results[dim_id] = self._channels[dim_id].process(signal)

        # D32 汇总
        d32_state = self._channels[32].compute_holistic(results)
        ctx[ArtifactKeys.D32_ORGAN_STATE] = d32_state
        # D32 sensation 仍然走 process（但 _organ_response 是空壳，需手动设）
        d32_result = self._channels[32].process(signal)
        # 用 compute_holistic 的 organ_state 覆盖
        d32_result.organ_state = d32_state
        d32_result.health_level = HealthLevel.from_deviation(
            d32_state.metrics.get("health_index", 75) - 75
        )
        results[32] = d32_result

        ctx[ArtifactKeys.CHANNEL_RESULTS] = results

        # n9: 计算偏移（deviation 已在 process 中计算，这里提取 medical_values）
        medical_values: Dict[int, float] = {}
        for dim_id, r in results.items():
            # 使用 organ_state 中的核心临床指标而非 generic medical_value
            metrics = r.organ_state.metrics
            if dim_id == 1:
                medical_values[dim_id] = metrics.get("lactate", 1.0)
            elif dim_id == 2:
                medical_values[dim_id] = metrics.get("vas_score", 0.0)
            elif dim_id == 3:
                medical_values[dim_id] = metrics.get("sns_excitation_%", 35.0)
            elif dim_id == 4:
                medical_values[dim_id] = metrics.get("cortisol", 14.0)
            elif dim_id == 5:
                medical_values[dim_id] = metrics.get("sweat_cortisol", 0.0)
            elif dim_id == 6:
                medical_values[dim_id] = metrics.get("bmr_decline_%", 0.0)
            elif dim_id == 7:
                medical_values[dim_id] = metrics.get("lactate_clearance", 1.2)
            elif dim_id == 8:
                medical_values[dim_id] = metrics.get("noise_db", 40.0)
            elif dim_id == 9:
                medical_values[dim_id] = metrics.get("esteem_score", 32.0)
            elif dim_id == 10:
                medical_values[dim_id] = metrics.get("neurotransmitter_decline_%", 0.0)
            elif dim_id == 11:
                medical_values[dim_id] = metrics.get("sas_score", 30.0)
            elif dim_id == 12:
                medical_values[dim_id] = metrics.get("oxytocin", 45.0)
            elif dim_id == 13:
                medical_values[dim_id] = metrics.get("mirror_neuron_activation", 0.4)
            elif dim_id == 14:
                medical_values[dim_id] = metrics.get("alertness_baseline", 0.2)
            elif dim_id == 15:
                medical_values[dim_id] = metrics.get("oxytocin", 50.0)
            elif dim_id == 16:
                medical_values[dim_id] = metrics.get("cortisol", 14.0)
            elif dim_id == 17:
                medical_values[dim_id] = metrics.get("security_score", 35.0)
            elif dim_id == 18:
                medical_values[dim_id] = metrics.get("cortisol", 14.0)
            elif dim_id == 19:
                medical_values[dim_id] = metrics.get("cortisol_rise", 0.0)
            elif dim_id == 20:
                medical_values[dim_id] = metrics.get("stress_hormone", 0.0)
            elif dim_id == 21:
                medical_values[dim_id] = metrics.get("cortisol_drop", 5.0)
            elif dim_id == 22:
                medical_values[dim_id] = metrics.get("recovery_efficiency_%", 80.0)
            elif dim_id == 23:
                medical_values[dim_id] = metrics.get("cortisol", 14.0)
            elif dim_id == 24:
                medical_values[dim_id] = metrics.get("sns_excitation_%", 35.0)
            elif dim_id == 25:
                medical_values[dim_id] = metrics.get("cortisol", 14.0)
            elif dim_id == 26:
                medical_values[dim_id] = metrics.get("melatonin", 30.0)
            elif dim_id == 27:
                medical_values[dim_id] = metrics.get("fluctuation_amplitude", 0.0)
            elif dim_id == 28:
                medical_values[dim_id] = metrics.get("dopamine_decline_%", 0.0)
            elif dim_id == 29:
                medical_values[dim_id] = metrics.get("neurotransmitter_decline_%", 0.0)
            elif dim_id == 30:
                medical_values[dim_id] = metrics.get("serotonin_decline_%", 0.0)
            elif dim_id == 31:
                medical_values[dim_id] = metrics.get("harmony_score", 40.0)
            elif dim_id == 32:
                medical_values[dim_id] = metrics.get("health_index", 75.0)

        ctx[ArtifactKeys.MEDICAL_VALUES] = medical_values

        return {"code": 0, "phase": "sensation_pipeline", "dimensions_processed": len(results)}

    # ==================================================================
    # P2: 安全守门
    # ==================================================================

    def _execute_safety_gate(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """执行 wf_safety_gate 全部节点。"""
        dna_root_id = ctx[ArtifactKeys.DNA_ROOT_ID]
        medical_values = ctx.get(ArtifactKeys.MEDICAL_VALUES, {})
        d32_state: Optional[OrganState] = ctx.get(ArtifactKeys.D32_ORGAN_STATE)

        # n1-n2: 加载阈值注册表（已在模块级别导入，无需重复加载）
        # n3-n7: 逐维校验
        d32_vitals = {}
        if d32_state:
            m = d32_state.metrics
            d32_vitals = {
                "heart_rate": m.get("heart_rate", 66),
                "blood_pressure_sys": m.get("blood_pressure_sys", 115),
                "blood_pressure_dia": m.get("blood_pressure_dia", 73),
                "cortisol_avg": m.get("cortisol_avg", 14),
                "pleasure_hormone_avg": m.get("pleasure_hormone_avg", 110),
            }

        # n8: 批量评估
        verdict = evaluate_all_dimensions(medical_values, d32_vitals, dna_root_id)
        ctx[ArtifactKeys.SAFETY_VERDICT] = verdict

        # n9: 最终判定
        if not verdict.passed:
            report = build_reject_report(verdict, dna_root_id)
            ctx[ArtifactKeys.REJECT_REPORT] = report
            self._emit_global_alert(report, ctx)
            return {"code": -99, "phase": "safety_gate", "reject_reason": verdict.reject_reason, "danger_count": verdict.danger_count}

        return {"code": 0, "phase": "safety_gate", "verdict": verdict.overall_level.value}

    # ==================================================================
    # P3: 快照发射
    # ==================================================================

    def _execute_snapshot_pipeline(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """执行 wf_yaoling_snapshot 全部节点。"""
        results = ctx[ArtifactKeys.CHANNEL_RESULTS]
        dna_root_id = ctx[ArtifactKeys.DNA_ROOT_ID]
        location_fingerprint = ctx.get(ArtifactKeys.LOCATION_FINGERPRINT, "")
        dialog_group_id = ctx.get("dialog_group_id", "")
        signal: SignalInput = ctx[ArtifactKeys.SIGNAL_INPUT]
        safety_verdict: SafetyVerdict = ctx.get(ArtifactKeys.SAFETY_VERDICT, None)

        # n1: 收集通道状态（results 已就绪）
        # n2: 跨维度一致性校验
        warnings = self._cross_dimension_check(results)

        # n3: D32 已在上游计算
        d32_state = ctx.get(ArtifactKeys.D32_ORGAN_STATE)

        # n4: 构建快照对象
        snapshot = self._encoder.encode(
            results=results,
            dna_root_id=dna_root_id,
            location_fingerprint=location_fingerprint,
            dialog_group_id=dialog_group_id,
            scene_tags=signal.scene_tags,
            cross_dimension_warnings=warnings,
            safety_verdict={
                "passed": safety_verdict.passed if safety_verdict else True,
                "danger_count": safety_verdict.danger_count if safety_verdict else 0,
                "overall_level": safety_verdict.overall_level.value if safety_verdict else "healthy",
            } if safety_verdict else None,
        )
        ctx[ArtifactKeys.SNAPSHOT] = snapshot

        # n5: 计算 CRC32
        crc = self._compute_crc32(snapshot)
        snapshot.crc32 = crc

        # n6: Protobuf 就绪
        proto_dict = to_protobuf_dict(snapshot)
        proto_dict["crc32"] = crc
        ctx[ArtifactKeys.PROTOBUF_DICT] = proto_dict

        # n7: 发射（占位 — GlobalBus 未跨进程实现，记录到日志）
        emission = {
            "msg_id": f"yaoling:{int(time.time()*1000)}",
            "channel": "tianquan_snapshot",
            "cmd": "yaoling_32d_snapshot_push",
            "target_domain": "t",
            "timestamp": snapshot.timestamp,
            "dna_root_id": dna_root_id,
        }
        self._emission_log.append(emission)

        # n8: 记录发射日志
        ctx[ArtifactKeys.EMISSION_LOG] = list(self._emission_log)

        return {
            "code": 0,
            "phase": "snapshot_pipeline",
            "snapshot": {
                "dna_root_id": dna_root_id,
                "entries": len(snapshot.entries),
                "overall_health": snapshot.overall_health_level,
                "vital_signs": snapshot.vital_signs,
                "crc32": crc,
            },
            "emission": emission,
            "protobuf_ready": True,
        }

    # ==================================================================
    # 节点实现: p1 信号处理
    # ==================================================================

    def _validate_signal(self, signal: SignalInput, ctx: Dict[str, Any]) -> None:
        """n1: 信号接收与校验。"""
        if not signal.source_channel:
            raise ValueError("信号 source_channel 为空")
        if signal.source_channel not in ("tianquan_snapshot", "yaoguang_snapshot"):
            raise ValueError(f"信号来源不合法: {signal.source_channel}")

        dna_root_id = ctx.get(ArtifactKeys.DNA_ROOT_ID, "")
        if not dna_root_id:
            raise ValueError("缺少 dna_root_id")

        # 校验 dna_root_id 格式: DNA-{YYYYMMDD}-{HHmm}-{seq}
        import re
        if not re.match(r"^DNA-\d{8}-\d{4}-[A-Za-z0-9\-]+$", dna_root_id):
            raise ValueError(f"dna_root_id 格式不合法: {dna_root_id}")

        location = ctx.get(ArtifactKeys.LOCATION_FINGERPRINT, "")
        if not location:
            raise ValueError("缺少 location_fingerprint")

    def _extract_scene_context(self, signal: SignalInput) -> Dict[str, Any]:
        """n2: 提取场景上下文。"""
        return {
            "scene_tags": signal.scene_tags,
            "interpersonal_labels": signal.interpersonal_labels,
            "environmental_params": signal.environmental_params,
            "temporal_context": signal.temporal_context,
            "location": signal.temporal_context.get("location", "unknown"),
            "time_of_day": signal.temporal_context.get("time_of_day", "unknown"),
            "season": signal.temporal_context.get("season", "unknown"),
        }

    def _validate_input_against_baseline(self, signal: SignalInput, ctx: Dict[str, Any]) -> None:
        """n3: 校验输入参数是否在合法区间。"""
        # 检查温度/噪音等环境参数是否在物理可行范围内
        temp = signal.environmental_params.get("temperature", 22)
        if temp < -50 or temp > 60:
            raise ValueError(f"环境温度不合法: {temp}℃")
        noise = signal.environmental_params.get("noise_db", 40)
        if noise < 0 or noise > 200:
            raise ValueError(f"环境噪音不合法: {noise}dB")
        work_hours = signal.duration_context.get("work_duration_hours", 0)
        if work_hours < 0 or work_hours > 24:
            raise ValueError(f"工作时长不合法: {work_hours}h")

    # ==================================================================
    # 节点实现: p2 安全守门辅助
    # ==================================================================

    def _emit_global_alert(self, report: Dict[str, Any], ctx: Dict[str, Any]) -> None:
        """发送全局告警（占位 — GlobalBus 跨进程实现后对接）。"""
        dna_root_id = ctx.get(ArtifactKeys.DNA_ROOT_ID, "")
        alert = {
            "channel": "global_alert",
            "cmd": "yaoling_safety_reject",
            "target_domain": "",  # 广播给 t 和 g
            "payload": report,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        }
        self._emission_log.append({"type": "global_alert", **alert})
        print(f"[GLOBAL_ALERT] Yaoling safety gate REJECT | dna={dna_root_id} | danger={report.get('danger_count',0)}")

    # ==================================================================
    # 节点实现: p3 快照辅助
    # ==================================================================

    def _cross_dimension_check(self, results: Dict[int, SensationResult]) -> List[Dict[str, Any]]:
        """n2: 跨维度一致性校验。"""
        warnings = []

        def _metric(dim_id: int, key: str, default: float = 0.0) -> float:
            r = results.get(dim_id)
            return r.organ_state.metrics.get(key, default) if r else default

        # D4 皮质醇 vs D11 SAS — 正相关
        d4_cortisol = _metric(4, "cortisol", 14)
        d11_sas = _metric(11, "sas_score", 30)
        if d4_cortisol > 20 and d11_sas < 35:
            warnings.append({"type": "inconsistency", "dims": [4, 11], "detail": "高皮质醇+低SAS，疑似不一致"})

        # D4 多巴胺 vs D10 驱动力 — 正相关
        d4_dopamine = _metric(4, "dopamine", 120)
        d10_decline = _metric(10, "neurotransmitter_decline_%", 0)
        if d4_dopamine > 130 and d10_decline > 30:
            warnings.append({"type": "inconsistency", "dims": [4, 10], "detail": "高多巴胺+高递质下降，疑似不一致"})

        # D12 催产素 vs D15 伴侣依恋 — 正相关
        d12_oxy = _metric(12, "oxytocin", 45)
        d15_oxy = _metric(15, "oxytocin", 50)
        if abs(d12_oxy - d15_oxy) > 30:
            warnings.append({"type": "inconsistency", "dims": [12, 15], "detail": f"D12催产素{d12_oxy}与D15催产素{d15_oxy}偏差>30"})

        return warnings

    @staticmethod
    def _compute_crc32(snapshot: SpineSnapshot) -> str:
        """n5: 计算 CRC32。"""
        payload = json.dumps({
            "dna_root_id": snapshot.dna_root_id,
            "timestamp": snapshot.timestamp,
            "entries": [
                {"dim_id": e.dim_id, "value_raw": e.value_raw, "medical_value": e.medical_value}
                for e in snapshot.entries
            ],
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]  # 用 SHA256 前16位替代 CRC32

    # ==================================================================
    # Harris node_executor 适配器
    # ==================================================================

    def as_node_executor(self) -> Callable:
        """
        返回符合 HarrisOrchestrator.run(node_executor=...) 签名的回调。

        在 common/harris_core.py 中，AgentNode.execute() 签名为:
            async def execute(self, ctx, executor=None)
        其中 executor 接收 (node, ctx) → result dict。
        """
        async def _executor(node, ctx) -> Dict[str, Any]:
            node_id = getattr(node, "node_id", "")
            return {"status": "executed", "node_id": node_id, "by": "YaolingWorkflowExecutor"}

        return _executor


# ---------------------------------------------------------------------------
# 便捷入口
# ---------------------------------------------------------------------------

def run_pipeline(
    raw_text: str,
    dna_root_id: str,
    location_fingerprint: str = "home.bedroom.night",
    source_channel: str = "yaoguang_snapshot",
    scene_tags: Optional[List[str]] = None,
    interpersonal_labels: Optional[List[str]] = None,
    environmental_params: Optional[Dict[str, float]] = None,
    temporal_context: Optional[Dict[str, Any]] = None,
    duration_context: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    一键执行瑶灵三阶段流水线。

    Args:
        raw_text: 用户原始输入文本
        dna_root_id: DNA 时序锚点
        location_fingerprint: 空间区位指纹
        其余参数: 传递给 SignalInput

    Returns:
        {"code": 0/-99, "snapshot": ..., "safety_verdict": ..., "vital_signs": ...}
    """
    signal = SignalInput(
        source_channel=source_channel,
        scene_tags=scene_tags or [],
        interpersonal_labels=interpersonal_labels or [],
        environmental_params=environmental_params or {"temperature": 22, "noise_db": 40, "light_lux": 300},
        temporal_context=temporal_context or {"time_of_day": "afternoon", "season": "summer", "weather": "clear"},
        raw_input_text=raw_text,
        duration_context=duration_context or {"hours_sitting": 4, "work_duration_hours": 8, "sleep_hours": 7, "hours_since_last_chat": 2},
    )
    executor = YaolingWorkflowExecutor()
    return executor.run_full_pipeline(
        signal_input=signal,
        dna_root_id=dna_root_id,
        location_fingerprint=location_fingerprint,
    )
