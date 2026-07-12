"""
sensation_decoder.py — 瑶灵体感解码器
======================================
将太虚境下发的调控指令或历史 SpineSnapshot 解码为通道可读的内部状态。

用途:
  - 天权下发调控指令 → 解码为各维度的目标参数
  - 历史 32D 快照回放 → 解码为 SensationResult 列表供分析

规格依据:
  - YAOLING_DOMAIN_SPEC.md §5.2 下行通道协议
  - 工程蓝皮书 §7 Transcoder 序列化层
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from channels.base_channel import (
    SensationResult,
    Intensity,
    HealthLevel,
    ChannelCategory,
    OrganState,
)


# ---------------------------------------------------------------------------
# 下行指令结构 (对应 §5.2)
# ---------------------------------------------------------------------------


@dataclass
class DownstreamCommand:
    """
    太虚 → 瑶灵的下行调控指令。

    指令类型:
      - hormone_adjust:   调整 D4 激素分泌参数
      - emotion_modulate: 情绪基调调控 (D9-D14)
      - cycle_reset:      生理周期重置 (D6)
      - repair_boost:     自愈加速指令 (D7)
      - safety_override:  安全阈值临时调整 (需双密钥，暂不实现)
    """
    cmd: str
    target_dims: List[int]
    params: Dict[str, float]
    dna_root_id: str = ""
    priority: int = 0  # 越小越高优
    ttl_seconds: int = 300  # 指令有效期


@dataclass
class HistorySnapshot:
    """
    从 SpineSnapshot 解码的历史快照。

    用于:
      - 记忆回溯时的体感重现
      - 月度体检表生成
      - 跨维度一致性审计
    """
    dna_root_id: str
    timestamp: str
    location_fingerprint: str
    results: Dict[int, SensationResult] = field(default_factory=dict)
    vital_signs: Dict[str, float] = field(default_factory=dict)
    overall_health_level: str = ""


# ---------------------------------------------------------------------------
# 解码器
# ---------------------------------------------------------------------------


class SensationDecoder:
    """
    将 Protobuf dict / SpineSnapshot / 下行指令解码为通道可用的内部格式。
    """

    # ------------------------------------------------------------------
    # 快照解码: SpineSnapshot → HistorySnapshot
    # ------------------------------------------------------------------

    @staticmethod
    def decode_snapshot(protobuf_dict: Dict[str, Any]) -> HistorySnapshot:
        """
        从 Protobuf 就绪的 dict（spine.proto 格式）解码为 HistorySnapshot。

        用于太虚境返回历史快照时还原体感数据。
        """
        results: Dict[int, SensationResult] = {}

        for entry_raw in protobuf_dict.get("entries", []):
            dim_id = entry_raw["dim_id"]
            results[dim_id] = SensationResult(
                dim_id=dim_id,
                dim_key=entry_raw.get("dim_key", f"dim_{dim_id}"),
                category=ChannelCategory(entry_raw.get("category", "dynamic_growth")),
                value_raw=entry_raw.get("value_raw", 0.0),
                intensity=Intensity(entry_raw.get("intensity", "low")),
                sensation_label=entry_raw.get("sensation_label", ""),
                medical_metric_name=entry_raw.get("medical_metric_name", ""),
                medical_value=entry_raw.get("medical_value", 0.0),
                medical_unit=entry_raw.get("medical_unit", ""),
                medical_baseline=entry_raw.get("medical_baseline", 0.0),
                deviation=entry_raw.get("deviation", 0.0),
                health_level=HealthLevel(entry_raw.get("health_level", "sub_healthy")),
                evidence_text=entry_raw.get("evidence_text", ""),
                organ_state=OrganState(
                    organ_name=entry_raw.get("organ_name", ""),
                    metrics=entry_raw.get("organ_metrics", {}),
                ),
                sibling_dims=entry_raw.get("sibling_dims", []),
                timestamp=protobuf_dict.get("timestamp", ""),
                dna_root_id=protobuf_dict.get("dna_root_id", ""),
            )

        return HistorySnapshot(
            dna_root_id=protobuf_dict.get("dna_root_id", ""),
            timestamp=protobuf_dict.get("timestamp", ""),
            location_fingerprint=protobuf_dict.get("location_fingerprint", ""),
            results=results,
            vital_signs=protobuf_dict.get("vital_signs", {}),
            overall_health_level=protobuf_dict.get("overall_health_level", ""),
        )

    # ------------------------------------------------------------------
    # 指令解码: 下行指令 → 各维度目标参数
    # ------------------------------------------------------------------

    @staticmethod
    def decode_command(command: DownstreamCommand) -> Dict[int, Dict[str, float]]:
        """
        将天权下行指令解码为各维度的目标调整参数。

        Returns:
          {dim_id: {param_name: target_value, ...}}

        Example:
          command = DownstreamCommand(
              cmd="hormone_adjust",
              target_dims=[4],
              params={"cortisol_target": 14.0, "dopamine_target": 120.0}
          )
          → {4: {"cortisol_target": 14.0, "dopamine_target": 120.0}}
        """
        targets: Dict[int, Dict[str, float]] = {}

        for dim_id in command.target_dims:
            targets[dim_id] = dict(command.params)

        return targets

    # ------------------------------------------------------------------
    # 安全阈值覆盖解码 (双密钥验证，暂为占位)
    # ------------------------------------------------------------------

    @staticmethod
    def decode_safety_override(
        command: DownstreamCommand,
        key_a: str = "",
        key_b: str = "",
    ) -> Optional[Dict[int, Dict[str, float]]]:
        """
        解码安全阈值临时调整指令（需双密钥）。

        当前为占位实现 —— 始终返回 None 表示不支持。
        工程蓝皮书 §12.3: 五级闸门不可关闭。
        瑶灵域安全阈值同样不可运行时修改（threshold_registry 为 frozen dataclass）。
        """
        return None


# ---------------------------------------------------------------------------
# 便捷函数
# ---------------------------------------------------------------------------


def decode_history_snapshot(protobuf_dict: Dict[str, Any]) -> HistorySnapshot:
    """快捷解码历史快照。"""
    return SensationDecoder.decode_snapshot(protobuf_dict)


def decode_downstream_cmd(command: DownstreamCommand) -> Dict[int, Dict[str, float]]:
    """快捷解码下行指令。"""
    return SensationDecoder.decode_command(command)
