"""
workflow_executor.py — 瑶光工作流执行器
=========================================
将三套 YAML 工作流映射到 32 维客观通道计算。

三工作流:
  wf_objective_env_sample   — 6D 环境快照（轻量通道）
  wf_location_fingerprint   — 标准化区位指纹（空间建模）
  wf_perception_filter      — 全 32 维客观参数快照（YaoguangUpstream 格式）

铁律（白皮书 §2.2）:
  - 仅输出纯量化客观参数，无主观情绪体感
  - 32 维向量分层生成，禁止 LLM 直接输出浮点
  - 有 dna_root_id + location_fingerprint 才输出
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from channels import create_all_objective_channels, ObjectiveResult


# ---------------------------------------------------------------------------
# 6D 环境快照
# ---------------------------------------------------------------------------

@dataclass
class Env6DSnapshot:
    temperature_c: float
    noise_db: float
    light_lux: float
    crowd_density: float
    urgency: float
    circadian_shift: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "temperature_c": self.temperature_c,
            "noise_db": self.noise_db,
            "light_lux": self.light_lux,
            "crowd_density": self.crowd_density,
            "urgency": self.urgency,
            "circadian_shift": self.circadian_shift,
        }


# ---------------------------------------------------------------------------
# 全 32 维快照
# ---------------------------------------------------------------------------

@dataclass
class YaoguangUpstreamSnapshot:
    dna_root_id: str
    timestamp_ms: int
    location_fingerprint: str
    env_6d: Env6DSnapshot
    objective: Dict[int, ObjectiveResult]  # dim_id → result
    crc32: str = ""

    def to_dict(self) -> Dict[str, Any]:
        obj_dict = {}
        for dim_id, r in sorted(self.objective.items()):
            obj_dict[f"d{dim_id}"] = {
                "standard_value": r.standard_value,
                "standard_unit": r.standard_unit,
                "standard_range": [r.standard_range_low, r.standard_range_high],
                "label": r.label_cn,
                "context": r.evidence_context,
            }
        return {
            "dna_root_id": self.dna_root_id,
            "timestamp_ms": self.timestamp_ms,
            "location_fingerprint": self.location_fingerprint,
            "env_6d": self.env_6d.to_dict(),
            "objective": obj_dict,
            "crc32": self.crc32,
        }


# ---------------------------------------------------------------------------
# 执行器
# ---------------------------------------------------------------------------

class YaoguangWorkflowExecutor:
    """瑶光三阶段工作流执行器。"""

    def __init__(self):
        self._channels = create_all_objective_channels()

    # ==================================================================
    # wf_objective_env_sample: 6D 环境快照
    # ==================================================================

    def run_env_sample(
        self,
        location_fingerprint: str = "",
        dna_root_id: str = "",
        timestamp_ms: Optional[int] = None,
        environmental_params: Optional[Dict[str, float]] = None,
        temporal_context: Optional[Dict[str, Any]] = None,
        duration_context: Optional[Dict[str, float]] = None,
    ) -> Env6DSnapshot:
        """执行 wf_objective_env_sample — 输出标准化 6D 环境感知快照。"""
        env = environmental_params or {}
        temporal = temporal_context or {}
        duration = duration_context or {}
        ts = timestamp_ms or int(time.time() * 1000)

        # D8 → temperature/noise/light
        d8 = self._channels[8].process(env, temporal, duration, [], dna_root_id, location_fingerprint, ts)
        # D24 → crowd_density
        d24 = self._channels[24].process(env, temporal, duration, [], dna_root_id, location_fingerprint, ts)
        # D25 → urgency
        d25 = self._channels[25].process(env, temporal, duration, [], dna_root_id, location_fingerprint, ts)
        # D26 → circadian_shift
        d26 = self._channels[26].process(env, temporal, duration, [], dna_root_id, location_fingerprint, ts)

        # circadian_shift: 正常=0, 夜间颠倒→负
        time_of_day = temporal.get("time_of_day", "afternoon")
        circadian_map = {"morning": 0.1, "noon": 0.05, "afternoon": 0.0, "evening": -0.1, "night": -0.2}
        circadian = circadian_map.get(time_of_day, 0.0)

        return Env6DSnapshot(
            temperature_c=d8.evidence_context.get("temperature", env.get("temperature", 22)),
            noise_db=env.get("noise_db", 40),
            light_lux=env.get("light_lux", 300),
            crowd_density=env.get("crowd_density", 0.0),
            urgency=d25.evidence_context.get("urgency", 0.0),
            circadian_shift=round(circadian, 2),
        )

    # ==================================================================
    # wf_location_fingerprint: 区位指纹
    # ==================================================================

    @staticmethod
    def run_location_fingerprint(
        scene_context: str = "",
        known_scene_id: str = "",
        known_sub_zone: str = "",
    ) -> Dict[str, Any]:
        """执行 wf_location_fingerprint — 输出标准化区位指纹。

        规则: 基于场景描述推断 scene_type + scene_id，
              编码为 {scene_type}:{scene_id}:{sub_zone}
        """
        # 简单规则推断（无 LLM）
        ctx_lower = scene_context.lower()

        if any(kw in ctx_lower for kw in ["卧室", "客厅", "厨房", "浴室", "阳台", "书房"]):
            scene_type = "home"
        elif any(kw in ctx_lower for kw in ["办公室", "工位", "会议室", "厂区", "车间"]):
            scene_type = "office"
        elif any(kw in ctx_lower for kw in ["公园", "山", "海滩", "街道", "广场", "户外"]):
            scene_type = "outdoor"
        elif any(kw in ctx_lower for kw in ["商场", "车站", "机场", "餐厅", "咖啡馆", "图书馆", "电影院"]):
            scene_type = "public"
        else:
            scene_type = "home"  # 默认

        scene_id = known_scene_id or "default"
        sub_zone = known_sub_zone or "default"
        fingerprint = f"{scene_type}:{scene_id}:{sub_zone}"

        return {
            "location_fingerprint": fingerprint,
            "scene_type": scene_type,
            "scene_id": scene_id,
            "sub_zone": sub_zone,
            "metadata": {
                "area_m2": {"home": 30, "office": 50, "outdoor": 500, "public": 200}.get(scene_type, 30),
                "crowd_baseline": {"home": 0.1, "office": 0.4, "outdoor": 0.3, "public": 0.7}.get(scene_type, 0.3),
                "noise_baseline_db": {"home": 35, "office": 50, "outdoor": 45, "public": 65}.get(scene_type, 45),
                "privacy_level": {"home": 1, "office": 2, "outdoor": 3, "public": 3}.get(scene_type, 3),
            },
        }

    # ==================================================================
    # wf_perception_filter: 全 32 维客观快照
    # ==================================================================

    def run_full_snapshot(
        self,
        dna_root_id: str,
        location_fingerprint: str = "",
        timestamp_ms: Optional[int] = None,
        environmental_params: Optional[Dict[str, float]] = None,
        temporal_context: Optional[Dict[str, Any]] = None,
        duration_context: Optional[Dict[str, float]] = None,
        interpersonal_labels: Optional[List[str]] = None,
    ) -> YaoguangUpstreamSnapshot:
        """执行 wf_perception_filter — 全 32 维客观参数快照。"""
        env = environmental_params or {}
        temporal = temporal_context or {}
        duration = duration_context or {}
        interpersonal = interpersonal_labels or []
        ts = timestamp_ms or int(time.time() * 1000)

        # 校验必填字段
        if not dna_root_id:
            raise ValueError("[瑶光] dna_root_id 必填 —— 无全局锚点拒绝输出")
        if not location_fingerprint:
            raise ValueError("[瑶光] location_fingerprint 必填 —— 无区位拒绝输出")

        # 6D 环境快照
        env_6d = self.run_env_sample(
            location_fingerprint=location_fingerprint,
            dna_root_id=dna_root_id,
            timestamp_ms=ts,
            environmental_params=env,
            temporal_context=temporal,
            duration_context=duration,
        )

        # 全 32 通道并行计算
        results: Dict[int, ObjectiveResult] = {}
        for dim_id in range(1, 33):
            results[dim_id] = self._channels[dim_id].process(
                env, temporal, duration, interpersonal,
                dna_root_id, location_fingerprint, ts,
            )

        # CRC32
        snapshot = YaoguangUpstreamSnapshot(
            dna_root_id=dna_root_id,
            timestamp_ms=ts,
            location_fingerprint=location_fingerprint,
            env_6d=env_6d,
            objective=results,
        )
        snapshot.crc32 = self._compute_crc32(snapshot)
        return snapshot

    @staticmethod
    def _compute_crc32(snapshot: YaoguangUpstreamSnapshot) -> str:
        payload = json.dumps({
            "dna": snapshot.dna_root_id,
            "ts": snapshot.timestamp_ms,
            "loc": snapshot.location_fingerprint,
            "dims": sorted(
                f"{dim_id}:{r.standard_value}"
                for dim_id, r in snapshot.objective.items()
            ),
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# 便捷入口
# ---------------------------------------------------------------------------

def run_env_snapshot(
    dna_root_id: str,
    location_fingerprint: str = "home.default.default",
    environmental_params: Optional[Dict[str, float]] = None,
    temporal_context: Optional[Dict[str, Any]] = None,
    duration_context: Optional[Dict[str, float]] = None,
    interpersonal_labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """一键执行瑶光全 32 维客观快照（含 6D 环境快照）。"""
    executor = YaoguangWorkflowExecutor()
    snapshot = executor.run_full_snapshot(
        dna_root_id=dna_root_id,
        location_fingerprint=location_fingerprint,
        environmental_params=environmental_params,
        temporal_context=temporal_context,
        duration_context=duration_context,
        interpersonal_labels=interpersonal_labels,
    )
    return snapshot.to_dict()
