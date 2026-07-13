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
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# 确保可以从 domain_yaoguang 目录导入 channels
#   方案: 把父目录加到 sys.path 以便 from common.xxx import
#         但 channels 用直接导入（同目录子包），避免依赖 domain_yaoguang 包名
_HERE = Path(__file__).resolve().parent
_PARENT = _HERE.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from channels import create_all_objective_channels, ObjectiveResult
from scene_registry import (
    SCENE_REGISTRY, get_scene, list_scenes, LOCATION_FINGERPRINT_ALIASES,
)


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

        优先级:
          1. 别名快捷映射 (如 "家" → home:xinghai_mingcheng:living_sofa)
          2. 已知场景注册表 (scene_id 精确匹配)
          3. 场景上下文关键词推断
          4. 默认兜底
        """
        ctx_lower = scene_context.lower().strip()

        # ── 第1优先级: 别名映射 ──
        alias_fp = LOCATION_FINGERPRINT_ALIASES.get(ctx_lower) or LOCATION_FINGERPRINT_ALIASES.get(
            scene_context.strip()
        )
        if alias_fp:
            parts = alias_fp.split(":", 2)
            scene_type, scene_id, sub_zone = parts[0], parts[1], parts[2] if len(parts) > 2 else "default"
            scene = get_scene(scene_id)
            if scene:
                return _build_fingerprint_result(scene, sub_zone)

        # ── 第2优先级: known_scene_id 精确匹配 ──
        if known_scene_id:
            scene = get_scene(known_scene_id)
            if scene:
                sub_zone = known_sub_zone or (scene.sub_zones[0].sub_zone_id if scene.sub_zones else "default")
                return _build_fingerprint_result(scene, sub_zone)

        # ── 第3优先级: 场景上下文关键词 ──
        # 先尝试在已知场景的 label/description 中搜索
        if ctx_lower:
            for s in SCENE_REGISTRY.values():
                if (ctx_lower in s.label_cn or ctx_lower in s.address or
                    any(kw in ctx_lower for kw in s.community_features) or
                    any(kw in s.label_cn for kw in ["星海名城", "前海", "光明", "凤凰", "花卉", "公园"])):
                    # 匹配到已知场景
                    pass  # 继续走关键词逻辑

        # 关键词推断 scene_type
        HOME_KW = ["卧室", "客厅", "厨房", "浴室", "阳台", "书房", "家", "房间",
                    "床", "沙发", "厕所", "卫生间", "鞋柜", "餐厅", "餐桌", "玄关",
                    "星海名城", "前海"]
        OFFICE_KW = ["办公室", "工位", "会议室", "厂区", "车间", "公司", "上班",
                     "茶水间", "前台", "光明", "凤凰街道"]
        OUTDOOR_KW = ["公园", "山", "海滩", "街道", "广场", "户外", "小溪", "树林",
                      "跑步", "散步", "健身器械", "喷泉", "假山", "花卉", "通勤",
                      "开车", "高速"]
        PUBLIC_KW = ["商场", "车站", "机场", "餐厅", "咖啡馆", "图书馆", "电影院",
                     "地铁站", "小镇"]

        if any(kw in ctx_lower for kw in HOME_KW):
            scene_type = "home"
            # 进一步推断是哪个 home
            if any(kw in ctx_lower for kw in ["光明", "公寓", "小溪"]):
                scene_id = "guangming_apartment"
            elif any(kw in ctx_lower for kw in ["星海", "前海", "三室", "鞋柜"]):
                scene_id = "xinghai_mingcheng"
            else:
                scene_id = "xinghai_mingcheng"  # 默认家
        elif any(kw in ctx_lower for kw in OFFICE_KW):
            scene_type = "office"
            scene_id = "guangming_office"
        elif any(kw in ctx_lower for kw in OUTDOOR_KW):
            scene_type = "outdoor"
            if any(kw in ctx_lower for kw in ["通勤", "开车", "高速", "堵车"]):
                scene_id = "commute_home_office"
            elif any(kw in ctx_lower for kw in ["前海公园", "前海"]):
                scene_id = "qianhai_park"
            else:
                scene_id = "default_outdoor"
        elif any(kw in ctx_lower for kw in PUBLIC_KW):
            scene_type = "public"
            scene_id = "flower_town" if "花卉" in ctx_lower else "default_public"
        else:
            scene_type = "home"
            scene_id = "xinghai_mingcheng"

        sub_zone = known_sub_zone or "default"

        # ── 第4优先级: 从场景注册表获取元数据 ──
        scene = get_scene(scene_id)
        if scene:
            if not known_sub_zone and scene.sub_zones:
                sub_zone = scene.sub_zones[0].sub_zone_id
            return _build_fingerprint_result(scene, sub_zone)

        # 兜底
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
        activity_context: Optional[Dict[str, Any]] = None,
    ) -> YaoguangUpstreamSnapshot:
        """执行 wf_perception_filter — 全 32 维客观参数快照。

        activity_context 可选字段:
          use_apartment: bool     — True=公寓步行上班, False=开车通勤
          work_hours: float       — 当日工作时长
          commute_traffic: str    — free_flow/light/moderate/heavy/severe
          weather: str            — clear/rain_light/rain_heavy/typhoon/fog
          evening_walk: bool      — 晚间是否散步
          sleep_hours: float      — 前夜睡眠时长
        """
        from activity_model import (
            build_typical_workday, compute_daily_fatigue,
            TrafficCondition, WeatherImpact, DRIVE_ROUTES,
        )

        env = environmental_params or {}
        temporal = temporal_context or {}
        duration = dict(duration_context or {})
        interpersonal = interpersonal_labels or []
        ts = timestamp_ms or int(time.time() * 1000)

        if not dna_root_id:
            raise ValueError("[瑶光] dna_root_id 必填")
        if not location_fingerprint:
            raise ValueError("[瑶光] location_fingerprint 必填")

        # ── 活动模型计算（如果传入了 activity_context）──
        if activity_context:
            use_apt = activity_context.get("use_apartment", False)
            work_h = activity_context.get("work_hours", 9.0)
            traffic_str = activity_context.get("commute_traffic", "moderate")
            weather_str = activity_context.get("weather", "clear")
            evening_walk = activity_context.get("evening_walk", True)
            sleep_h = activity_context.get("sleep_hours",
                duration.get("sleep_hours", 7.0))

            traffic = TrafficCondition(traffic_str)
            weather = WeatherImpact(weather_str)

            # 构建典型工作日活动
            activities, drives, walks = build_typical_workday(
                work_hours=work_h,
                commute_traffic=traffic,
                weather=weather,
                evening_walk=evening_walk,
                use_apartment=use_apt,
            )
            fatigue = compute_daily_fatigue(
                activities, drives, walks, sleep_hours=sleep_h,
            )

            # 注入到 duration context，供各通道使用
            duration["lactate_mmol_l"] = fatigue.lactate_estimate
            duration["fatigue_composite"] = fatigue.composite_fatigue
            duration["physical_fatigue"] = fatigue.physical_fatigue
            duration["drive_fatigue"] = fatigue.driving_fatigue
            duration["mental_fatigue"] = fatigue.mental_fatigue
            duration["total_energy_kcal"] = fatigue.total_energy_kcal
            duration["recommended_rest_min"] = fatigue.recommended_rest_min
            duration["sleep_hours"] = sleep_h
            duration["work_duration_hours"] = work_h

            # 通勤数据注入 D25
            if not use_apt:
                dr = DRIVE_ROUTES.get("home→office")
                if dr:
                    duration["commute_distance_km"] = dr.distance_km
                    duration["commute_time_min"] = dr.drive_time_min(traffic, weather)
                    duration["buffer_min"] = activity_context.get("buffer_min", 30)

            # 环境参数: 如果没手动指定，从场景环境基线推算
            from activity_model import SCENE_ENV_BASELINES, SceneEnvBaseline
            if "temperature" not in env:
                scene_part = location_fingerprint.split(":")[1] if ":" in location_fingerprint else ""
                se = SCENE_ENV_BASELINES.get(scene_part)
                if se:
                    tod = temporal.get("time_of_day", "afternoon")
                    temp_map = {"morning": se.morning_temp, "afternoon": se.afternoon_temp,
                                "evening": se.evening_temp, "night": se.night_temp}
                    lux_map = {"morning": se.morning_lux, "afternoon": se.afternoon_lux,
                               "evening": se.evening_lux, "night": se.night_lux}
                    env.setdefault("temperature", temp_map.get(tod, 26))
                    env.setdefault("noise_db", se.noise_db)
                    env.setdefault("light_lux", lux_map.get(tod, 300))
                    env.setdefault("crowd_density", se.crowd_density)

        env_6d = self.run_env_sample(
            location_fingerprint=location_fingerprint,
            dna_root_id=dna_root_id,
            timestamp_ms=ts,
            environmental_params=env,
            temporal_context=temporal,
            duration_context=duration,
        )

        results: Dict[int, ObjectiveResult] = {}
        for dim_id in range(1, 33):
            results[dim_id] = self._channels[dim_id].process(
                env, temporal, duration, interpersonal,
                dna_root_id, location_fingerprint, ts,
            )

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
# 辅助函数
# ---------------------------------------------------------------------------


def _build_fingerprint_result(scene, sub_zone: str) -> Dict[str, Any]:
    """从 KnownScene 构建标准 fingerprint 返回结构。"""
    from scene_registry import KnownScene, SubZone

    fingerprint = f"{scene.scene_type}:{scene.scene_id}:{sub_zone}"

    sz_detail = None
    for sz in scene.sub_zones:
        if sz.sub_zone_id == sub_zone:
            sz_detail = {
                "label": sz.label_cn,
                "description": sz.description,
                "props": sz.props,
                "tags": sz.tags,
            }
            break

    return {
        "location_fingerprint": fingerprint,
        "scene_type": scene.scene_type,
        "scene_id": scene.scene_id,
        "sub_zone": sub_zone,
        "sub_zone_detail": sz_detail,
        "label_cn": scene.label_cn,
        "address": scene.address,
        "city": scene.city,
        "district": scene.district,
        "rooms": scene.rooms,
        "sub_zones_available": [sz.sub_zone_id for sz in scene.sub_zones],
        "metadata": {
            "area_m2": scene.area_m2,
            "crowd_baseline": scene.crowd_baseline,
            "noise_baseline_db": scene.noise_baseline_db,
            "privacy_level": scene.privacy_level,
        },
        "community_features": scene.community_features,
        "nearby_pois": scene.nearby_pois,
        "commute": {
            "from_home_km": scene.commute_from_home_km,
            "from_home_min": scene.commute_from_home_min,
            "note": scene.commute_note,
        } if scene.commute_from_home_km > 0 else None,
    }


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
