"""
sensation_encoder.py — 瑶灵体感编码器
======================================
将 32 通道的 SensationResult 列表编码为标准化 32D 数据包（Protobuf 就绪结构）。

规格依据:
  - YAOLING_DOMAIN_SPEC.md §2.2 输出数据包格式
  - 工程蓝皮书 §7 Transcoder 序列化层 (spine.proto 对齐)
  - 工程蓝皮书 §12.9: 单次交互仅生成一颗完整 32D 海胆

注意: 瑶灵只负责产出 Protobuf 就绪的 Python dict 结构，
      实际二进制 Protobuf 编码由太虚境 Transcoder 统一执行。
      CRC32 由上游 (wf_yaoling_snapshot) 在组装时计算。
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from domain_yaoling.channels.base_channel import SensationResult, HealthLevel, Intensity, ChannelCategory


# ---------------------------------------------------------------------------
# 编码输出结构（→ spine.proto SpineSnapshot）
# ---------------------------------------------------------------------------


@dataclass
class SpineEntry:
    """单维度条目 — 对应 spine.proto 的 SpineEntry message。"""
    dim_id: int
    dim_key: str
    category: str                  # ChannelCategory.value
    # 主观体感
    value_raw: float
    intensity: str                 # Intensity.value
    sensation_label: str
    # 医学对标
    medical_metric_name: str
    medical_value: float
    medical_unit: str
    medical_baseline: float
    deviation: float
    health_level: str              # HealthLevel.value
    # 器官状态
    organ_name: str
    organ_metrics: Dict[str, float] = field(default_factory=dict)
    # 证据
    evidence_text: str = ""
    sibling_dims: List[int] = field(default_factory=list)


@dataclass
class SpineSnapshot:
    """
    完整 32D 海胆快照 — 对应 spine.proto 的 SpineSnapshot message。

    工程蓝皮书 §12.9: 单次交互仅生成一颗完整 32D 海胆。
    """
    dna_root_id: str
    dialog_group_id: str = ""
    location_fingerprint: str = ""
    timestamp: str = ""              # ISO8601
    scene_tags: List[str] = field(default_factory=list)
    entries: List[SpineEntry] = field(default_factory=list)  # 32 entries
    cross_dimension_warnings: List[Dict[str, Any]] = field(default_factory=list)
    safety_verdict: Optional[Dict[str, Any]] = None
    # D32 核心生命体征快照
    vital_signs: Dict[str, float] = field(default_factory=dict)
    overall_health_level: str = ""
    overall_deviation: float = 0.0
    # 校验
    crc32: str = ""
    encoder_version: str = "YAOLING-ENCODER-1.0"


# ---------------------------------------------------------------------------
# 编码器
# ---------------------------------------------------------------------------


class SensationEncoder:
    """
    将 32 个 SensationResult 编码为 SpineSnapshot。

    用法:
        encoder = SensationEncoder()
        snapshot = encoder.encode(results, dna_root_id, location_fingerprint)

    编码规则:
      - 所有浮点四舍五入到 4 位小数
      - 枚举字段使用 .value 字符串
      - 缺失维度标记为 data_missing（health_level=risk）
      - 维度按 dim_id 升序排列
    """

    def __init__(self) -> None:
        self._version = "YAOLING-ENCODER-1.0"

    # ------------------------------------------------------------------
    def encode(
        self,
        results: Dict[int, SensationResult],
        dna_root_id: str,
        location_fingerprint: str = "",
        dialog_group_id: str = "",
        scene_tags: Optional[List[str]] = None,
        cross_dimension_warnings: Optional[List[Dict[str, Any]]] = None,
        safety_verdict: Optional[Dict[str, Any]] = None,
    ) -> SpineSnapshot:
        """
        将 32 通道结果编码为完整 SpineSnapshot。

        Args:
            results: {dim_id: SensationResult} 字典，必须覆盖 D1-D32
            dna_root_id: DNA 时序锚点
            location_fingerprint: 空间区位指纹
            dialog_group_id: 对话组 ID
            scene_tags: 场景标签
            cross_dimension_warnings: 跨维度一致性告警（来自 wf_yaoling_snapshot n2）
            safety_verdict: 安全校验结果（来自 wf_safety_gate）
        """
        if not dna_root_id:
            raise ValueError("编码失败: dna_root_id 为空")

        entries: List[SpineEntry] = []

        for dim_id in range(1, 33):
            result = results.get(dim_id)
            if result is None:
                # 缺失维度 — 生成占位条目
                entries.append(self._missing_entry(dim_id))
                continue
            entries.append(self._result_to_entry(result))

        # 提取 D32 核心生命体征
        vital_signs: Dict[str, float] = {}
        overall_health = HealthLevel.HEALTHY.value
        overall_dev = 0.0

        d32 = results.get(32)
        if d32 is not None and hasattr(d32, "organ_state"):
            vital_signs = dict(d32.organ_state.metrics)
            overall_health = d32.health_level.value
            overall_dev = d32.deviation

        snapshot = SpineSnapshot(
            dna_root_id=dna_root_id,
            dialog_group_id=dialog_group_id,
            location_fingerprint=location_fingerprint,
            timestamp=self._now_iso(),
            scene_tags=scene_tags or [],
            entries=entries,
            cross_dimension_warnings=cross_dimension_warnings or [],
            safety_verdict=safety_verdict,
            vital_signs=vital_signs,
            overall_health_level=overall_health,
            overall_deviation=round(overall_dev, 2),
            encoder_version=self._version,
        )
        return snapshot

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _result_to_entry(self, r: SensationResult) -> SpineEntry:
        return SpineEntry(
            dim_id=r.dim_id,
            dim_key=r.dim_key,
            category=r.category.value,
            value_raw=r.value_raw,
            intensity=r.intensity.value,
            sensation_label=r.sensation_label,
            medical_metric_name=r.medical_metric_name,
            medical_value=r.medical_value,
            medical_unit=r.medical_unit,
            medical_baseline=r.medical_baseline,
            deviation=r.deviation,
            health_level=r.health_level.value,
            organ_name=r.organ_state.organ_name,
            organ_metrics=dict(r.organ_state.metrics),
            evidence_text=r.evidence_text,
            sibling_dims=list(r.sibling_dims),
        )

    def _missing_entry(self, dim_id: int) -> SpineEntry:
        """缺失维度的占位条目。"""
        return SpineEntry(
            dim_id=dim_id,
            dim_key=f"dim_{dim_id}",
            category="unknown",
            value_raw=0.0,
            intensity=Intensity.LOW.value,
            sensation_label="数据缺失",
            medical_metric_name="未知",
            medical_value=0.0,
            medical_unit="N/A",
            medical_baseline=0.0,
            deviation=0.0,
            health_level=HealthLevel.RISK.value,
            organ_name="未知",
            evidence_text="[DIM_DATA_MISSING]",
        )

    @staticmethod
    def _now_iso() -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


# ---------------------------------------------------------------------------
# 便捷函数
# ---------------------------------------------------------------------------


def encode_snapshot(
    results: Dict[int, SensationResult],
    dna_root_id: str,
    location_fingerprint: str = "",
    **kwargs,
) -> SpineSnapshot:
    """快捷编码函数。"""
    return SensationEncoder().encode(
        results, dna_root_id, location_fingerprint, **kwargs
    )


def to_protobuf_dict(snapshot: SpineSnapshot) -> Dict[str, Any]:
    """
    将 SpineSnapshot 转换为 Protobuf 兼容的纯字典。

    此函数模拟 Transcoder.encode() 的输入格式，
    供 wf_yaoling_snapshot 的 n6_serialize_protobuf_ready 节点调用。

    工程蓝皮书 §7: 序列化由太虚境 Transcoder 统一执行。
    瑶灵只负责结构就绪（输出此 dict）。
    """
    entries_list = []
    for e in snapshot.entries:
        entries_list.append({
            "dim_id": e.dim_id,
            "dim_key": e.dim_key,
            "category": e.category,
            "value_raw": e.value_raw,
            "intensity": e.intensity,
            "sensation_label": e.sensation_label,
            "medical_metric_name": e.medical_metric_name,
            "medical_value": e.medical_value,
            "medical_unit": e.medical_unit,
            "medical_baseline": e.medical_baseline,
            "deviation": e.deviation,
            "health_level": e.health_level,
            "organ_name": e.organ_name,
            "organ_metrics": e.organ_metrics,
            "evidence_text": e.evidence_text,
            "sibling_dims": e.sibling_dims,
        })

    return {
        "dna_root_id": snapshot.dna_root_id,
        "dialog_group_id": snapshot.dialog_group_id,
        "location_fingerprint": snapshot.location_fingerprint,
        "timestamp": snapshot.timestamp,
        "scene_tags": snapshot.scene_tags,
        "entries": entries_list,
        "cross_dimension_warnings": snapshot.cross_dimension_warnings,
        "safety_verdict": snapshot.safety_verdict,
        "vital_signs": snapshot.vital_signs,
        "overall_health_level": snapshot.overall_health_level,
        "overall_deviation": snapshot.overall_deviation,
        "crc32": snapshot.crc32,
        "encoder_version": snapshot.encoder_version,
    }
