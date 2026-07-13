"""
closed_loop.py — 瑶灵三体通信闭环编排器
=========================================
执行固定的六步闭环流程:
  1. 解析用户消息 → 提取场景参数
  2. 瑶灵 32D 体感流水线
  3. 发送 32D 上下文给瑶光解锁客观世界 (不可用时默认兜底)
  4. 瑶灵整合双路数据 (主观体感 + 客观参数)
  5. 上传太虚境天权 (不可用时本地缓存)
  6. 用户友好输出

使用:
  loop = ClosedLoopOrchestrator()
  result = loop.run("用户消息文本", dna_root_id="...")
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 路径
_SELF = Path(__file__).resolve()
_DOMAIN = _SELF.parent
if str(_DOMAIN.parent) not in sys.path:
    sys.path.insert(0, str(_DOMAIN.parent))
if str(_DOMAIN) not in sys.path:
    sys.path.insert(0, str(_DOMAIN))

from yaoguang_fallback import get_fallback_params, match_scene, SCENE_PRESETS
from tianquan_cache import get_cache, TianquanCache


# ═══════════════════════════════════════════════════════════════
# 闭环结果
# ═══════════════════════════════════════════════════════════════


class TriBodyStatus:
    """三体通信状态标记。"""
    YAOLING_OK = "yaoling_ok"
    YAOLING_ERROR = "yaoling_error"
    YAOGUANG_LIVE = "yaoguang_live"
    YAOGUANG_FALLBACK = "yaoguang_fallback"
    TIANQUAN_LIVE = "tianquan_live"
    TIANQUAN_OFFLINE = "tianquan_offline"


@dataclass
class ClosedLoopResult:
    """六步闭环完整结果。"""
    dna_root_id: str
    location_fingerprint: str
    timestamp: str
    # 步骤结果
    scene_params: Dict[str, Any]
    pipeline_result: Dict[str, Any]
    yaoguang_source: str          # "live" | "fallback"
    yaoguang_params: Dict[str, Any]
    tianquan_status: str          # "live" | "offline_cached"
    tianquan_msg_id: str
    # 健康摘要
    vital_signs: Dict[str, float]
    overall_health: str
    danger_count: int
    # 错误
    errors: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# 闭环编排器
# ═══════════════════════════════════════════════════════════════

class ClosedLoopOrchestrator:
    """
    瑶灵三体通信闭环编排器。

    每次调用 run() 执行完整的六步流程。
    瑶光和天权 MCP 的调用通过回调注入（方便测试和离线运行）。
    """

    def __init__(self):
        self._cache = get_cache()
        self._seq_counter = 0
        # 外部注入的 MCP 调用回调 (用于跨域通信)
        self._yaoguang_caller: Optional[callable] = None
        self._tianquan_caller: Optional[callable] = None
        # 瑶灵 MCP 回调 (直接调本地流水线)
        self._yaoling_caller: Optional[callable] = None

    # ═══════════════════════════════════════════════════════════
    # 公共入口
    # ═══════════════════════════════════════════════════════════

    def run(
        self,
        raw_text: str,
        dna_root_id: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> ClosedLoopResult:
        """
        执行完整六步闭环。

        Args:
            raw_text: 用户消息原文
            dna_root_id: DNA 时序锚点 (不传则自动生成)
            user_context: 额外上下文 (如已知的 location, time_of_day 等)
        """
        if dna_root_id is None:
            dna_root_id = self._generate_dna_root_id()
        errors: List[str] = []

        # ── 第一步: 解析场景参数 ──
        scene_params = self._step1_parse_scene(raw_text, user_context)

        # ── 第二步: 瑶灵 32D 体感 ──
        pipeline_result = self._step2_yaoling_sensation(raw_text, dna_root_id, scene_params)
        if pipeline_result.get("code", 0) != 0:
            errors.append(f"瑶灵体感异常: code={pipeline_result.get('code')}")

        # ── 第三步: 瑶光客观参数 ──
        yaoguang_params, yaoguang_source = self._step3_yaoguang_unlock(
            raw_text, dna_root_id, pipeline_result
        )

        # ── 第四步: 整合双路数据 ──
        merged = self._step4_merge(pipeline_result, yaoguang_params, yaoguang_source)

        # ── 第五步: 上传太虚境 ──
        tianquan_status, tianquan_msg_id = self._step5_tianquan_upload(
            dna_root_id, scene_params["location_fingerprint"], merged, yaoguang_source
        )

        # ── 第六步: 构建结果 ──
        vs = pipeline_result.get("snapshot", {}).get("vital_signs", {})

        return ClosedLoopResult(
            dna_root_id=dna_root_id,
            location_fingerprint=scene_params.get("location_fingerprint", "unknown"),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
            scene_params=scene_params,
            pipeline_result=pipeline_result,
            yaoguang_source=yaoguang_source,
            yaoguang_params=yaoguang_params,
            tianquan_status=tianquan_status,
            tianquan_msg_id=tianquan_msg_id,
            vital_signs={
                "heart_rate": vs.get("heart_rate", 0),
                "blood_pressure_sys": vs.get("blood_pressure_sys", 0),
                "blood_pressure_dia": vs.get("blood_pressure_dia", 0),
                "cortisol_avg": vs.get("cortisol_avg", 0),
                "pleasure_hormone_avg": vs.get("pleasure_hormone_avg", 0),
            },
            overall_health=pipeline_result.get("snapshot", {}).get("overall_health", "unknown"),
            danger_count=pipeline_result.get("danger_count", 0),
            errors=errors,
        )

    # ═══════════════════════════════════════════════════════════
    # 第一步: 场景解析
    # ═══════════════════════════════════════════════════════════

    def _step1_parse_scene(
        self, raw_text: str, user_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """解析用户消息，提取场景参数。"""
        # 先用瑶光兜底表匹配场景
        fallback = get_fallback_params(raw_text, user_context)

        params = {
            "location_fingerprint": fallback.get("temporal_context", {}).get("location", "unknown")
                                    + "." + fallback.get("scene_name", "default").replace(" ", "_"),
            "scene_tags": fallback.get("scene_tags", []),
            "interpersonal_labels": fallback.get("interpersonal_labels", []),
            "environmental_params": fallback.get("environmental_params", {}),
            "temporal_context": fallback.get("temporal_context", {}),
            "duration_context": fallback.get("duration_context", {}),
            "raw_input_text": raw_text,
            "source_channel": "yaoguang_snapshot",
            "medical_baseline_version": "YAOGUANG-MED-001",
        }

        # 用户显式提供的上下文覆盖自动推断
        if user_context:
            for key in ("location_fingerprint", "interpersonal_labels", "temporal_context",
                        "environmental_params", "duration_context"):
                if key in user_context:
                    params[key] = user_context[key]

        return params

    # ═══════════════════════════════════════════════════════════
    # 第二步: 瑶灵 32D 体感
    # ═══════════════════════════════════════════════════════════

    def _step2_yaoling_sensation(
        self, raw_text: str, dna_root_id: str, scene_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行瑶灵 32D 体感流水线。"""
        try:
            from workflow_executor import run_pipeline as _run_pipeline

            result = _run_pipeline(
                raw_text=raw_text,
                dna_root_id=dna_root_id,
                location_fingerprint=scene_params["location_fingerprint"],
                source_channel=scene_params.get("source_channel", "yaoguang_snapshot"),
                scene_tags=scene_params.get("scene_tags", []),
                interpersonal_labels=scene_params.get("interpersonal_labels", []),
                environmental_params=scene_params.get("environmental_params"),
                temporal_context=scene_params.get("temporal_context"),
                duration_context=scene_params.get("duration_context"),
            )
            return result
        except Exception as e:
            return {"code": -99, "error": str(e), "phase": "sensation_pipeline"}

    # ═══════════════════════════════════════════════════════════
    # 第三步: 瑶光客观参数
    # ═══════════════════════════════════════════════════════════

    def _step3_yaoguang_unlock(
        self, raw_text: str, dna_root_id: str, pipeline_result: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], str]:
        """
        尝试调用瑶光 MCP 获取实时客观参数。
        不可用时使用默认兜底表。
        """
        # 先尝试瑶光 MCP
        if self._yaoguang_caller:
            try:
                live_params = self._yaoguang_caller({
                    "dna_root_id": dna_root_id,
                    "yaoling_32d_context": pipeline_result.get("snapshot", {}),
                    "raw_input_text": raw_text,
                })
                if live_params and live_params.get("code") == 0:
                    return live_params.get("data", {}), TriBodyStatus.YAOGUANG_LIVE
            except Exception:
                pass

        # 兜底
        fallback = get_fallback_params(raw_text)
        return fallback, TriBodyStatus.YAOGUANG_FALLBACK

    # ═══════════════════════════════════════════════════════════
    # 第四步: 整合双路数据
    # ═══════════════════════════════════════════════════════════

    def _step4_merge(
        self,
        pipeline_result: Dict[str, Any],
        yaoguang_params: Dict[str, Any],
        yaoguang_source: str,
    ) -> Dict[str, Any]:
        """合并瑶灵主观体感 + 瑶光客观参数。"""
        vs = pipeline_result.get("snapshot", {}).get("vital_signs", {})
        return {
            "dna_root_id": pipeline_result.get("dna_root_id", ""),
            "overall_health": pipeline_result.get("snapshot", {}).get("overall_health", "unknown"),
            "vital_signs": vs,
            "danger_count": pipeline_result.get("danger_count", 0),
            "safety_reject": pipeline_result.get("safety_reject", False),
            "phase": pipeline_result.get("phase", "?"),
            "yaoguang_source": yaoguang_source,
            "yaoguang_scene": yaoguang_params.get("scene_name", "unknown"),
            "yaoguang_is_fallback": yaoguang_params.get("is_fallback", True),
            "protobuf_dict": pipeline_result.get("protobuf_dict", {}),
            "protobuf_ready": pipeline_result.get("protobuf_ready", False),
        }

    # ═══════════════════════════════════════════════════════════
    # 第五步: 上传太虚境
    # ═══════════════════════════════════════════════════════════

    def _step5_tianquan_upload(
        self,
        dna_root_id: str,
        location_fingerprint: str,
        merged: Dict[str, Any],
        yaoguang_source: str,
    ) -> Tuple[str, str]:
        """
        尝试上传快照到太虚境天权。
        不可用时存入本地缓存。
        """
        msg_id = ""

        # 尝试天权 MCP
        if self._tianquan_caller:
            try:
                resp = self._tianquan_caller({
                    "dna_root_id": dna_root_id,
                    "yaoling_32d_snapshot": merged.get("protobuf_dict", {}),
                    "yaoguang_params": {"source": yaoguang_source},
                })
                if resp and resp.get("code") == 0:
                    msg_id = resp.get("msg_id", "tianquan_ack")
                    return TriBodyStatus.TIANQUAN_LIVE, msg_id
            except Exception:
                pass

        # 本地缓存
        snapshot_summary = {
            "overall_health": merged.get("overall_health"),
            "vital_signs": merged.get("vital_signs"),
            "danger_count": merged.get("danger_count"),
        }
        self._cache.store(
            dna_root_id=dna_root_id,
            location_fingerprint=location_fingerprint,
            snapshot_summary=snapshot_summary,
            protobuf_dict=merged.get("protobuf_dict", {}),
            yaoguang_source=yaoguang_source,
        )
        msg_id = f"cache:{self._cache.count_unsynced()}"
        return TriBodyStatus.TIANQUAN_OFFLINE, msg_id

    # ═══════════════════════════════════════════════════════════
    # 工具
    # ═══════════════════════════════════════════════════════════

    def _generate_dna_root_id(self) -> str:
        self._seq_counter += 1
        date_str = time.strftime("%Y%m%d", time.localtime())
        time_str = time.strftime("%H%M", time.localtime())
        return f"DNA-{date_str}-{time_str}-{self._seq_counter:03d}"

    def set_yaoguang_caller(self, caller: callable) -> None:
        self._yaoguang_caller = caller

    def set_tianquan_caller(self, caller: callable) -> None:
        self._tianquan_caller = caller

    @property
    def cache(self) -> TianquanCache:
        return self._cache


# ═══════════════════════════════════════════════════════════════
# 格式化输出 (第六步)
# ═══════════════════════════════════════════════════════════════

def format_closed_loop_output(result: ClosedLoopResult) -> str:
    """将闭环结果格式化为用户友好文本。"""
    vs = result.vital_signs
    hr = vs.get("heart_rate", 0)
    bp_s = vs.get("blood_pressure_sys", 0)
    bp_d = vs.get("blood_pressure_dia", 0)
    cort = vs.get("cortisol_avg", 0)
    pleas = vs.get("pleasure_hormone_avg", 0)
    danger = result.danger_count
    rejected = result.pipeline_result.get("safety_reject", False)
    scene = result.scene_params.get("temporal_context", {}).get("location", "unknown")

    yaoguang_label = "瑶光实时" if result.yaoguang_source == TriBodyStatus.YAOGUANG_LIVE else "瑶光默认兜底"
    tianquan_label = "太虚在线" if result.tianquan_status == TriBodyStatus.TIANQUAN_LIVE else "太虚离线缓存"

    lines = [
        "",
        "=" * 60,
        f"  Yaoling 32D Somatic Response",
        f"  DNA: {result.dna_root_id}",
        f"  Scene: {scene}",
        "=" * 60,
        "",
        "  VITAL SIGNS",
        f"  HR: {hr:.0f} bpm  |  BP: {bp_s:.0f}/{bp_d:.0f} mmHg",
        f"  Cortisol: {cort:.1f} ug/dL  |  Pleasure: {pleas:.0f} pg/mL",
        f"  Health: {result.overall_health}  |  Danger dims: {danger}",
        "",
        f"  Tri-Body: Yaoling OK | {yaoguang_label} | {tianquan_label}",
        f"  Status: {'REJECTED' if rejected else 'PASSED'} | Protobuf: {'ready' if result.pipeline_result.get('protobuf_ready') else 'pending'}",
        "",
        "=" * 60,
    ]

    if result.errors:
        lines.append(f"  WARNINGS: {', '.join(result.errors)}")
        lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════

def run_closed_loop(raw_text: str, dna_root_id: Optional[str] = None) -> ClosedLoopResult:
    """一键执行六步闭环。"""
    loop = ClosedLoopOrchestrator()
    return loop.run(raw_text, dna_root_id=dna_root_id)
