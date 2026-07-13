"""
unlock_dispatcher.py — 瑶光·世界解锁事件调度器
================================================
接收瑶灵或用户的解锁请求 → 解析事件类型 → 映射受影响维度 →
分发到各学科计算引擎 → 组装完整32D客观参数快照 → 上行太虚。

解锁事件类型:
  - scene_unlock:    新场景解锁（首次进入某空间）
  - weather_change:  天气突变（晴→暴雨/降温/台风）
  - time_shift:      时段切换（清晨→正午→傍晚→深夜）
  - seasonal_shift:  季节更替
  - holiday_event:   节假日事件
  - commute_mode:    通勤模式切换（开车→步行/地铁）
  - social_event:    社交场景变化（独处→聚会/会议/约会）
  - env_explore:     周边环境探索（新POI/户外活动）
  - health_event:    健康相关事件（生病/康复/运动）

铁律:
  - 全部规则公式，禁止 LLM 生成浮点
  - 每次解锁返回完整 YaoguangUpstream 32D 快照
  - dna_root_id 必填
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from channels import create_all_objective_channels, ObjectiveResult
from environmental_context import (
    EnvContext, EnvImpactMatrix, DimensionImpact,
    TimeOfDay, Season, Weather, DayType, SceneType,
    compute_env_impact_matrix, quick_env_matrix,
    compute_light_level, compute_noise_level, compute_uv_index,
    compute_indoor_temperature, compute_daylight_hours,
)
from activity_model import (
    WalkRoute, DriveRoute, TrafficCondition, WeatherImpact,
    compute_daily_fatigue, build_typical_workday,
    WALK_ROUTES, DRIVE_ROUTES, SCENE_ENV_BASELINES,
    ActivityType, DailyActivity,
)
from scene_registry import (
    SCENE_REGISTRY, get_scene, list_scenes, LOCATION_FINGERPRINT_ALIASES,
    KnownScene,
)


# ===================================================================
# 解锁事件类型
# ===================================================================

class UnlockEventType(str, Enum):
    SCENE_UNLOCK = "scene_unlock"         # 新场景
    WEATHER_CHANGE = "weather_change"     # 天气突变
    TIME_SHIFT = "time_shift"            # 时段切换
    SEASONAL_SHIFT = "seasonal_shift"    # 季节更替
    HOLIDAY = "holiday"                  # 节假日
    COMMUTE_MODE = "commute_mode"         # 通勤模式
    SOCIAL_EVENT = "social_event"        # 社交事件
    ENV_EXPLORE = "env_explore"          # 环境探索
    HEALTH_EVENT = "health_event"        # 健康事件
    CUSTOM = "custom"                    # 自定义复合事件


# ===================================================================
# 解锁请求与响应
# ===================================================================

@dataclass
class UnlockRequest:
    """瑶灵/用户发来的解锁请求。"""
    event_type: UnlockEventType
    dna_root_id: str
    event_description: str              # 事件自然语言描述
    # 场景参数
    location_fingerprint: str = ""
    scene_type: str = "home"            # home/office/outdoor/public/nature/transit/medical
    # 时间
    time_of_day: str = "afternoon"
    hour: int = 14
    # 气象
    weather: str = "clear"
    season: str = "summer"
    outdoor_temp_c: float = 28.0
    # 日期
    day_type: str = "workday"
    # 人群
    crowd_density: float = 0.1
    noise_db_override: Optional[float] = None
    # 人际
    interpersonal_labels: List[str] = field(default_factory=list)
    # 活动
    activity_context: Optional[Dict[str, Any]] = None
    # 扩展参数（事件特定的额外数据）
    extra_params: Dict[str, Any] = field(default_factory=dict)
    # 生物画像
    avatar_key: str = "mature_m"  # 预设avatar键名 或 "custom"
    avatar_custom: Optional[Dict[str, Any]] = None  # 自定义avatar参数
    effort_level: float = 0.5  # 0.0~1.0 付出/努力程度


@dataclass
class UnlockResponse:
    """解锁响应——包含完整 32D 客观参数快照。"""
    dna_root_id: str
    event_type: str
    timestamp_ms: int
    location_fingerprint: str
    # 环境基础
    env_context: Dict[str, Any]
    # 6D 环境快照
    env_6d: Dict[str, float]
    # 环境影响摘要
    env_impact_summary: Dict[str, float]  # dim_id → net_correction
    # 完整 32D
    objective: Dict[str, Any]  # d1...d32
    # 活动模型（如有）
    activity_report: Optional[Dict[str, Any]] = None
    # 校验
    crc32: str = ""


# ===================================================================
# 解锁调度器
# ===================================================================

class UnlockDispatcher:
    """
    世界解锁事件调度器。

    解析事件 → 构建 EnvContext → 计算环境影响矩阵 →
    调用 32 通道（传入 env correction）→ 可选活动模型 →
    组装 UnlockResponse。

    这是瑶光域对外提供的核心"世界解锁"能力，
    瑶灵或用户通过 send_cross_domain_command 调用。
    """

    def __init__(self):
        self._channels = create_all_objective_channels()

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------

    def dispatch(self, req: UnlockRequest) -> UnlockResponse:
        """
        处理一次解锁事件，返回完整 32D 客观参数快照。

        处理流程:
          1. 构建 EnvContext
          2. 计算环境影响矩阵
          3. 根据事件类型额外处理（通勤/社交/健康…）
          4. 运行全部 32 通道（传入 env correction + activity data）
          5. 组装响应
        """
        ts = int(time.time() * 1000)

        # ── 1. 构建环境上下文 ──
        env = self._build_env_context(req)

        # ── 2. 环境影响矩阵 ──
        impact = compute_env_impact_matrix(env, dna_root_id=req.dna_root_id)

        # ── 3. 事件特定处理 ──
        duration_extra: Dict[str, float] = {}
        activity_report: Optional[Dict[str, Any]] = None

        # 解析 avatar
        from avatar_profile import PRESET_AVATARS, AvatarProfile, AgeGroup, BiologicalSex, ExperienceTracker, ExperienceDomain, ExperienceLevel, PhysicalTraits
        avatar: Optional[AvatarProfile] = None
        if req.avatar_key == "custom" and req.avatar_custom:
            avatar = AvatarProfile(
                age_group=AgeGroup(req.avatar_custom.get("age_group","mature")),
                biological_sex=BiologicalSex(req.avatar_custom.get("biological_sex","male")),
                physical=PhysicalTraits(**req.avatar_custom.get("physical",{})),
            )
            if req.avatar_custom.get("experience"):
                for domain_key, info in req.avatar_custom["experience"].items():
                    avatar.experience.records[ExperienceDomain(domain_key)] = (
                        ExperienceLevel(info["level"]), info.get("count",0), info.get("last_ts",0))
        elif req.avatar_key in PRESET_AVATARS:
            avatar = PRESET_AVATARS[req.avatar_key]

        avatar_ctx = avatar.to_context_dict() if avatar else {}
        effort = req.effort_level

        if req.event_type in (UnlockEventType.COMMUTE_MODE, UnlockEventType.SCENE_UNLOCK):
            activity_report, duration_extra = self._handle_activity_event(req, env)
        elif req.event_type == UnlockEventType.SOCIAL_EVENT:
            duration_extra = self._handle_social_event(req, env)
        elif req.event_type == UnlockEventType.HEALTH_EVENT:
            duration_extra = self._handle_health_event(req, env)

        # ── 4. 准备通道输入参数基 ──
        temporal = {
            "time_of_day": req.time_of_day,
            "season": req.season,
            "weather": req.weather,
            "hour": req.hour,
            "day_type": req.day_type,
        }
        env_params = {
            "temperature": env.indoor_temp_c if env.indoor else env.outdoor_temp_c or 22,
            "noise_db": env.noise_db,
            "light_lux": env.light_lux,
            "crowd_density": env.crowd_density,
            "humidity_pct": env.humidity_pct,
            "uv_index": env.uv_index,
            "wind_speed_ms": env.wind_speed_ms,
        }
        duration = {
            "sleep_hours": req.extra_params.get("sleep_hours",
                req.activity_context.get("sleep_hours", 7.0) if req.activity_context else 7.0),
            "work_duration_hours": req.extra_params.get("work_hours",
                req.activity_context.get("work_hours", 8.0) if req.activity_context else 0.0),
            "hours_sitting": req.extra_params.get("hours_sitting", 4.0),
            "buffer_min": req.extra_params.get("buffer_min", 60.0),
            "hours_since_last_chat": req.extra_params.get("hours_since_last_chat", 2.0),
            # 生物画像注入（所有通道通过 __avatar__ 读取）
            "__avatar__": avatar_ctx,
            # 事件特定数据
            **duration_extra,
        }

        # ── 4b. 将环境影响转译为通道可消费的具名参数 ──
        imp = impact.impacts
        temporal["d4_time_factor"] = imp[4].net_correction
        temporal["weather_raw"] = req.weather
        if imp[8].net_correction < -0.1:
            env_params["comfort_penalty"] = abs(imp[8].net_correction)
        if imp[11].net_correction < 0:
            duration["env_sas_penalty"] = abs(imp[11].net_correction) * 20
        if imp[12].net_correction != 0:
            duration["env_oxytocin_bonus"] = imp[12].net_correction * 15
        duration["env_attachment_bonus"] = imp[15].net_correction * 10
        duration["env_belonging_bonus"] = imp[17].net_correction * 10
        if imp[23].net_correction < 0:
            duration["env_work_stress"] = abs(imp[23].net_correction) * 10
        duration["env_seasonal_shift"] = imp[26].net_correction
        duration["env_global_correction"] = imp[32].net_correction
        # Avatar 年龄/经验修正注入
        if avatar is not None:
            for dim_id in range(1, 33):
                age_mod = avatar.get_dimension_age_modifier(dim_id)
                exp_mod = 0.0
                for dom in ExperienceDomain:
                    m = avatar.get_experience_modifier(dim_id, dom)
                    if abs(m) > abs(exp_mod): exp_mod = m  # 取最大效应
                eff_mod = avatar.get_effort_modifier(dim_id, effort)
                if abs(age_mod) > 0.01 or abs(exp_mod) > 0.01 or abs(eff_mod) > 0.01:
                    key = f"avatar_d{dim_id}_mod"
                    duration[key] = round(age_mod + exp_mod + eff_mod, 2)
            # 性行为专项修正
            sex_mods = avatar.get_sexual_response_modifiers()
            for dim_id, mod in sex_mods.items():
                if abs(mod) > 0.01:
                    duration[f"sexual_d{dim_id}_mod"] = mod
        # 补注 env_impact_net 到 duration
        duration["env_impact_net"] = {dim_id: i.net_correction for dim_id, i in imp.items()}

        results: Dict[int, ObjectiveResult] = {}
        for dim_id in range(1, 33):
            # 将环境影响融入计算：通道基类 process 会使用 env/temporal/duration
            # 此处 extra 中的 env_impact_net 供通道内部查询
            results[dim_id] = self._channels[dim_id].process(
                env_params, temporal, duration,
                req.interpersonal_labels,
                dna_root_id=req.dna_root_id,
                location_fingerprint=req.location_fingerprint,
                timestamp_ms=ts,
            )

        # ── 6. 组装响应 ──
        obj_dict: Dict[str, Any] = {}
        for dim_id in range(1, 33):
            r = results[dim_id]
            obj_dict[f"d{dim_id}"] = {
                "standard_value": r.standard_value,
                "standard_unit": r.standard_unit,
                "standard_range": [r.standard_range_low, r.standard_range_high],
                "label": r.label_cn,
                "context": r.evidence_context,
                "env_impact": impact.impacts.get(dim_id, DimensionImpact(dim_id, "")).net_correction,
            }

        # 6D 轻量快照
        env_6d = {
            "temperature_c": env.outdoor_temp_c if not env.indoor else env.indoor_temp_c,
            "noise_db": env.noise_db,
            "light_lux": env.light_lux,
            "crowd_density": env.crowd_density,
            "urgency": duration_extra.get("urgency", 0.0),
            "circadian_shift": {
                "morning": 0.1, "noon": 0.05, "afternoon": 0.0,
                "evening": -0.1, "night": -0.2, "late_night": -0.3,
                "dawn": 0.15,
            }.get(req.time_of_day, 0.0),
        }

        response = UnlockResponse(
            dna_root_id=req.dna_root_id,
            event_type=req.event_type.value,
            timestamp_ms=ts,
            location_fingerprint=req.location_fingerprint,
            env_context={
                "time_of_day": req.time_of_day,
                "season": req.season,
                "weather": req.weather,
                "scene_type": req.scene_type,
                "day_type": req.day_type,
                "indoor": env.indoor,
                "outdoor_temp_c": env.outdoor_temp_c,
                "indoor_temp_c": env.indoor_temp_c,
                "humidity_pct": env.humidity_pct,
                "noise_db": env.noise_db,
                "daylight_hours": impact.daylight_hours,
                "uv_index": env.uv_index,
                "wind_speed_ms": env.wind_speed_ms,
            },
            env_6d=env_6d,
            env_impact_summary={
                f"d{dim_id}": imp.net_correction
                for dim_id, imp in sorted(impact.impacts.items())
            },
            objective=obj_dict,
            activity_report=activity_report,
        )
        response.crc32 = self._compute_crc32(response)
        return response

    # ------------------------------------------------------------------
    # 环境上下文构建
    # ------------------------------------------------------------------

    def _build_env_context(self, req: UnlockRequest) -> EnvContext:
        """从 UnlockRequest 构建 EnvContext，自动补全缺失参数。"""
        # 场景类型映射
        scene_type_map = {
            "home": SceneType.HOME, "office": SceneType.OFFICE,
            "outdoor": SceneType.OUTDOOR, "public": SceneType.PUBLIC,
            "transit": SceneType.TRANSIT, "nature": SceneType.NATURE,
            "medical": SceneType.MEDICAL,
        }
        st = scene_type_map.get(req.scene_type, SceneType.HOME)
        indoor = st in (SceneType.HOME, SceneType.OFFICE, SceneType.MEDICAL)

        # 如果 location_fingerprint 指向已知场景，从 scene_registry 补全
        noise_db = req.noise_db_override
        if noise_db is None and ":" in req.location_fingerprint:
            parts = req.location_fingerprint.split(":")
            scene = get_scene(parts[1]) if len(parts) >= 2 else None
            if scene:
                if noise_db is None:
                    noise_db = scene.noise_baseline_db
                if req.crowd_density <= 0:
                    req.crowd_density = scene.crowd_baseline

        # 预计算 Enum 成员（大小写容错）
        tod_str = req.time_of_day.upper() if req.time_of_day else "AFTERNOON"
        sea_str = req.season.upper() if req.season else "SUMMER"
        wea_str = req.weather.upper() if req.weather else "CLEAR"
        day_str = req.day_type.upper() if req.day_type else "WORKDAY"
        tod_enum = TimeOfDay[tod_str] if tod_str in TimeOfDay.__members__ else TimeOfDay.AFTERNOON
        sea_enum = Season[sea_str] if sea_str in Season.__members__ else Season.SUMMER
        wea_enum = Weather[wea_str] if wea_str in Weather.__members__ else Weather.CLEAR

        if noise_db is None:
            noise_db = compute_noise_level(st, req.crowd_density, wea_enum, tod_enum, indoor)

        indoor_temp = compute_indoor_temperature(
            req.outdoor_temp_c,
            has_ac=True,
            has_heating=req.season.lower() == "winter",
            season=sea_enum,
        ) if indoor else req.outdoor_temp_c

        light_lux = compute_light_level(tod_enum, wea_enum, indoor, sea_enum)
        uv = compute_uv_index(tod_enum, wea_enum, sea_enum)
        return EnvContext(
            time_of_day=tod_enum, hour=req.hour,
            season=sea_enum, weather=wea_enum,
            outdoor_temp_c=req.outdoor_temp_c,
            humidity_pct=req.extra_params.get("humidity_pct", 60.0),
            wind_speed_ms=req.extra_params.get("wind_speed_ms", 2.0),
            uv_index=uv,
            scene_type=st,
            indoor=indoor,
            indoor_temp_c=indoor_temp if indoor else req.outdoor_temp_c,
            noise_db=noise_db,
            light_lux=light_lux,
            crowd_density=req.crowd_density,
            day_type=DayType[day_str] if day_str in DayType.__members__ else DayType.WORKDAY,
            event_tags=[req.event_type.value],
            prev_day_sleep_h=req.extra_params.get("sleep_hours", 7.0),
            prev_day_fatigue=req.extra_params.get("prev_day_fatigue", 0.2),
        )

    # ------------------------------------------------------------------
    # 事件处理
    # ------------------------------------------------------------------

    def _handle_activity_event(
        self, req: UnlockRequest, env: EnvContext
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, float]]:
        """处理需要活动模型计算的事件（通勤/场景切换）。"""
        if not req.activity_context:
            return None, {}

        from activity_model import TrafficCondition as TC, WeatherImpact as WI

        use_apt = req.activity_context.get("use_apartment", False)
        work_h = req.activity_context.get("work_hours", 9.0)
        traffic_str = req.activity_context.get("commute_traffic", "moderate")
        weather_str = req.activity_context.get("weather", req.weather)

        # 映射字符串到枚举
        traffic_map = {"free_flow": TC.FREE_FLOW, "light": TC.LIGHT,
                       "moderate": TC.MODERATE, "heavy": TC.HEAVY, "severe": TC.SEVERE}
        weather_impact_map = {"clear": WI.CLEAR, "rain_light": WI.RAIN_LIGHT,
                              "rain_heavy": WI.RAIN_HEAVY, "typhoon": WI.TYPHOON, "fog": WI.FOG}

        traffic = traffic_map.get(traffic_str, TC.MODERATE)
        w_impact = weather_impact_map.get(weather_str, WI.CLEAR)

        acts, drives, walks = build_typical_workday(
            work_hours=work_h,
            commute_traffic=traffic,
            weather=w_impact,
            evening_walk=req.activity_context.get("evening_walk", True),
            use_apartment=use_apt,
        )
        sleep_h = req.activity_context.get("sleep_hours", 7.0)
        fatigue = compute_daily_fatigue(acts, drives, walks, sleep_hours=sleep_h)

        duration_extra = {
            "lactate_mmol_l": fatigue.lactate_estimate,
            "fatigue_composite": fatigue.composite_fatigue,
            "physical_fatigue": fatigue.physical_fatigue,
            "drive_fatigue": fatigue.driving_fatigue,
            "mental_fatigue": fatigue.mental_fatigue,
            "total_energy_kcal": fatigue.total_energy_kcal,
            "recommended_rest_min": fatigue.recommended_rest_min,
            "sleep_hours": sleep_h,
            "work_duration_hours": work_h,
        }

        if not use_apt:
            dr = DRIVE_ROUTES.get("home→office")
            if dr:
                duration_extra["commute_distance_km"] = dr.distance_km
                duration_extra["commute_time_min"] = dr.drive_time_min(traffic, w_impact)

        report = {
            "activities_count": len(acts),
            "drive_routes_count": len(drives),
            "walk_routes_count": len(walks),
            "total_energy_kcal": fatigue.total_energy_kcal,
            "composite_fatigue": fatigue.composite_fatigue,
            "driving_fatigue": fatigue.driving_fatigue,
            "physical_fatigue": fatigue.physical_fatigue,
            "mental_fatigue": fatigue.mental_fatigue,
            "recommended_rest_min": fatigue.recommended_rest_min,
            "lactate_estimate": fatigue.lactate_estimate,
        }

        return report, duration_extra

    def _handle_social_event(
        self, req: UnlockRequest, env: EnvContext
    ) -> Dict[str, float]:
        """处理社交事件的客观影响。"""
        extra: Dict[str, float] = {}
        social_type = req.extra_params.get("social_type", "")
        crowd = req.crowd_density

        if social_type == "meeting":
            extra["work_duration_hours"] = req.extra_params.get("meeting_duration_h", 1.0)
            extra["hours_sitting"] = req.extra_params.get("meeting_duration_h", 1.0)
        elif social_type == "party":
            extra["hours_sitting"] = 0.0
            extra["activity_minutes"] = req.extra_params.get("duration_min", 120)
        elif social_type == "date":
            extra["hours_since_last_chat"] = 0.0  # 正在约会

        if crowd > 0.5:
            extra["fatigue_composite"] = extra.get("fatigue_composite", 0.0) + crowd * 0.15

        return extra

    def _handle_health_event(
        self, req: UnlockRequest, env: EnvContext
    ) -> Dict[str, float]:
        """处理健康事件的客观参数。"""
        extra: Dict[str, float] = {}
        health_type = req.extra_params.get("health_type", "")

        if health_type == "sick":
            # 生病: 乳酸清除↓, 皮质醇↑, 代谢↓
            extra["lactate_mmol_l"] = 1.5
            extra["fatigue_composite"] = 0.7
            extra["sleep_hours"] = req.extra_params.get("sleep_hours", 9.0)
        elif health_type == "exercise":
            # 运动后: 乳酸↑, 恢复中, 多巴胺↑
            extra["lactate_mmol_l"] = req.extra_params.get("lactate_mmol_l", 2.0)
            extra["activity_minutes"] = req.extra_params.get("exercise_duration_min", 60)
            extra["fatigue_composite"] = 0.4
        elif health_type == "recovery":
            extra["lactate_mmol_l"] = req.extra_params.get("lactate_mmol_l", 0.8)
            extra["fatigue_composite"] = 0.1

        return extra

    # ------------------------------------------------------------------
    # CRC32
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_crc32(resp: UnlockResponse) -> str:
        payload = json.dumps({
            "dna": resp.dna_root_id,
            "ts": resp.timestamp_ms,
            "event": resp.event_type,
            "loc": resp.location_fingerprint,
            "dims": sorted(
                f"{k}:{v['standard_value']}" for k, v in resp.objective.items()
            ),
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


# ===================================================================
# 便捷入口
# ===================================================================

_unlock_dispatcher: Optional[UnlockDispatcher] = None


def get_dispatcher() -> UnlockDispatcher:
    global _unlock_dispatcher
    if _unlock_dispatcher is None:
        _unlock_dispatcher = UnlockDispatcher()
    return _unlock_dispatcher


def handle_unlock_event(
    event_type: str,
    dna_root_id: str,
    event_description: str = "",
    **kwargs,
) -> Dict[str, Any]:
    """
    通用解锁事件处理入口。

    Yaoling 或用户调用此函数请求瑶光对某事件进行客观世界计算。

    Example:
        handle_unlock_event(
            event_type="weather_change",
            dna_root_id="DNA-20260714-1500-001",
            event_description="暴雨突降，气温骤降到22度",
            weather="rain_heavy",
            outdoor_temp_c=22.0,
            location_fingerprint="office:guangming_office:desk_a2",
        )
    """
    event_upper = event_type.upper()
    et = UnlockEventType[event_upper] if event_upper in UnlockEventType.__members__ else UnlockEventType.CUSTOM
    req = UnlockRequest(
        event_type=et,
        dna_root_id=dna_root_id,
        event_description=event_description,
        location_fingerprint=kwargs.get("location_fingerprint", "home:xinghai_mingcheng:living_sofa"),
        scene_type=kwargs.get("scene_type", "home"),
        time_of_day=kwargs.get("time_of_day", "afternoon"),
        hour=kwargs.get("hour", 14),
        weather=kwargs.get("weather", "clear"),
        season=kwargs.get("season", "summer"),
        outdoor_temp_c=kwargs.get("outdoor_temp_c", 28.0),
        day_type=kwargs.get("day_type", "workday"),
        crowd_density=kwargs.get("crowd_density", 0.1),
        noise_db_override=kwargs.get("noise_db_override"),
        interpersonal_labels=kwargs.get("interpersonal_labels", []),
        activity_context=kwargs.get("activity_context"),
        extra_params=kwargs.get("extra_params", {}),
        avatar_key=kwargs.get("avatar_key", "mature_m"),
        avatar_custom=kwargs.get("avatar_custom"),
        effort_level=kwargs.get("effort_level", 0.5),
    )

    dispatcher = get_dispatcher()
    response = dispatcher.dispatch(req)

    return {
        "code": 0,
        "dna_root_id": response.dna_root_id,
        "event_type": response.event_type,
        "timestamp_ms": response.timestamp_ms,
        "location_fingerprint": response.location_fingerprint,
        "env_context": response.env_context,
        "env_6d": response.env_6d,
        "env_impact_summary": response.env_impact_summary,
        "objective": response.objective,
        "activity_report": response.activity_report,
        "crc32": response.crc32,
    }
