"""
yaoguang_fallback.py — 瑶光客观参数默认兜底表
===============================================
当瑶光 MCP (harris-g) 离线时，提供预设的客观环境参数。
每个场景包含: 温度/噪音/光照/天气/区位/人群密度/人际标签

数据来源: 瑶灵医学对标手册 (specs/02-*.md) + 场景推断逻辑
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ScenePreset:
    """单个场景的完整客观参数预设。"""
    scene_name: str
    scene_tags: List[str]
    environmental_params: Dict[str, float]
    temporal_context: Dict[str, Any]
    interpersonal_labels: List[str]
    duration_context: Dict[str, float]
    description: str


# ═══════════════════════════════════════════════════════════════
# 场景预设库
# ═══════════════════════════════════════════════════════════════

SCENE_PRESETS: Dict[str, ScenePreset] = {
    # ── 伴侣场景 ──
    "evening_bedroom_partner": ScenePreset(
        scene_name="晚间卧室伴侣陪伴",
        scene_tags=["home", "bedroom", "night", "relaxing", "intimate"],
        environmental_params={"temperature": 22, "noise_db": 35, "light_lux": 200, "crowd_density": 0},
        temporal_context={"time_of_day": "evening", "season": "summer", "weather": "clear", "location": "bedroom"},
        interpersonal_labels=["partner"],
        duration_context={"hours_sitting": 5, "work_duration_hours": 8, "sleep_hours": 7, "hours_since_last_chat": 2},
        description="晚间·卧室·伴侣陪伴·放松时光",
    ),

    # ── 工作场景 ──
    "daytime_office_work": ScenePreset(
        scene_name="日间办公室工作",
        scene_tags=["office", "work", "daytime"],
        environmental_params={"temperature": 25, "noise_db": 50, "light_lux": 500, "crowd_density": 0.3},
        temporal_context={"time_of_day": "afternoon", "season": "summer", "weather": "cloudy", "location": "office"},
        interpersonal_labels=["colleague"],
        duration_context={"hours_sitting": 6, "work_duration_hours": 8, "sleep_hours": 7, "hours_since_last_chat": 3},
        description="午后·办公室·日常工作",
    ),

    "night_office_overtime": ScenePreset(
        scene_name="深夜加班办公",
        scene_tags=["office", "night", "overtime", "stress"],
        environmental_params={"temperature": 26, "noise_db": 55, "light_lux": 500, "crowd_density": 0.1},
        temporal_context={"time_of_day": "night", "season": "summer", "weather": "rain", "location": "office"},
        interpersonal_labels=[],
        duration_context={"hours_sitting": 10, "work_duration_hours": 14, "sleep_hours": 5, "hours_since_last_chat": 10},
        description="深夜·办公室·高压加班·孤独",
    ),

    # ── 家庭场景 ──
    "afternoon_home_family": ScenePreset(
        scene_name="午后居家家庭陪伴",
        scene_tags=["home", "living_room", "daytime", "family"],
        environmental_params={"temperature": 24, "noise_db": 30, "light_lux": 400, "crowd_density": 0.1},
        temporal_context={"time_of_day": "afternoon", "season": "spring", "weather": "clear", "location": "living_room"},
        interpersonal_labels=["family"],
        duration_context={"hours_sitting": 2, "work_duration_hours": 3, "sleep_hours": 8, "hours_since_last_chat": 1},
        description="午后·客厅·家人陪伴·轻松",
    ),

    "evening_home_family_dinner": ScenePreset(
        scene_name="晚间家庭共进晚餐",
        scene_tags=["home", "dining", "evening", "family", "warm"],
        environmental_params={"temperature": 23, "noise_db": 35, "light_lux": 300, "crowd_density": 0.2},
        temporal_context={"time_of_day": "evening", "season": "autumn", "weather": "clear", "location": "home"},
        interpersonal_labels=["family"],
        duration_context={"hours_sitting": 3, "work_duration_hours": 6, "sleep_hours": 7.5, "hours_since_last_chat": 1},
        description="晚间·家庭·共餐·温馨",
    ),

    # ── 独处场景 ──
    "night_alone_bedroom": ScenePreset(
        scene_name="深夜独处卧室",
        scene_tags=["bedroom", "night", "alone"],
        environmental_params={"temperature": 20, "noise_db": 25, "light_lux": 100, "crowd_density": 0},
        temporal_context={"time_of_day": "night", "season": "winter", "weather": "clear", "location": "bedroom"},
        interpersonal_labels=[],
        duration_context={"hours_sitting": 3, "work_duration_hours": 6, "sleep_hours": 6, "hours_since_last_chat": 12},
        description="深夜·卧室·独处·失眠·孤独",
    ),

    "morning_alone_wakeup": ScenePreset(
        scene_name="清晨独处起床",
        scene_tags=["bedroom", "morning", "alone"],
        environmental_params={"temperature": 18, "noise_db": 25, "light_lux": 150, "crowd_density": 0},
        temporal_context={"time_of_day": "morning", "season": "spring", "weather": "clear", "location": "bedroom"},
        interpersonal_labels=[],
        duration_context={"hours_sitting": 0, "work_duration_hours": 0, "sleep_hours": 7, "hours_since_last_chat": 8},
        description="清晨·卧室·独处·苏醒",
    ),

    # ── 社交场景 ──
    "afternoon_outdoor_social": ScenePreset(
        scene_name="午后户外社交活动",
        scene_tags=["outdoor", "social", "daytime", "public"],
        environmental_params={"temperature": 28, "noise_db": 60, "light_lux": 2000, "crowd_density": 0.6},
        temporal_context={"time_of_day": "afternoon", "season": "summer", "weather": "clear", "location": "outdoor"},
        interpersonal_labels=["colleague"],
        duration_context={"hours_sitting": 1, "work_duration_hours": 0, "sleep_hours": 8, "hours_since_last_chat": 1},
        description="午后·户外·社交·热闹",
    ),

    "evening_public_transit": ScenePreset(
        scene_name="晚高峰通勤路上",
        scene_tags=["transit", "public", "evening", "commute"],
        environmental_params={"temperature": 28, "noise_db": 70, "light_lux": 400, "crowd_density": 0.8},
        temporal_context={"time_of_day": "evening", "season": "summer", "weather": "cloudy", "location": "transit"},
        interpersonal_labels=["stranger"],
        duration_context={"hours_sitting": 1, "work_duration_hours": 9, "sleep_hours": 7, "hours_since_last_chat": 2, "commute_hours": 1},
        description="傍晚·通勤·拥挤·疲惫",
    ),

    # ── 默认兜底 ──
    "default": ScenePreset(
        scene_name="默认场景",
        scene_tags=["unknown"],
        environmental_params={"temperature": 22, "noise_db": 40, "light_lux": 300, "crowd_density": 0.1},
        temporal_context={"time_of_day": "afternoon", "season": "summer", "weather": "clear", "location": "unknown"},
        interpersonal_labels=[],
        duration_context={"hours_sitting": 4, "work_duration_hours": 8, "sleep_hours": 7, "hours_since_last_chat": 2},
        description="默认兜底场景 · 无具体场景信号",
    ),
}


# ═══════════════════════════════════════════════════════════════
# 场景匹配逻辑
# ═══════════════════════════════════════════════════════════════

def match_scene(raw_text: str, user_context: Optional[Dict[str, Any]] = None) -> ScenePreset:
    """
    根据用户文本和上下文匹配最合适的场景预设。

    匹配优先级:
      1. 显式场景关键词 (如 "加班/熬夜/卧室/外面")
      2. 人际标签推断 (如 "女朋友→伴侣, 爸妈→家庭")
      3. 时间推断 (如 "凌晨→深夜独处, 下午→工作")
      4. 默认兜底
    """
    text = raw_text.lower() if raw_text else ""

    # ── 显式场景关键词 ──
    if any(kw in text for kw in ["加班", "赶工", "deadline", "通宵", "熬夜工作"]):
        return SCENE_PRESETS["night_office_overtime"]
    if any(kw in text for kw in ["办公室", "公司", "上班", "开会"]):
        return SCENE_PRESETS["daytime_office_work"]
    if any(kw in text for kw in ["卧室", "床上", "睡前", "躺", "被窝"]):
        if any(kw in text for kw in ["女朋友", "男朋友", "老公", "老婆", "伴侣", "对象"]):
            return SCENE_PRESETS["evening_bedroom_partner"]
        if any(kw in text for kw in ["一个人", "失眠", "睡不着", "熬夜"]):
            return SCENE_PRESETS["night_alone_bedroom"]
        return SCENE_PRESETS["evening_bedroom_partner"]
    if any(kw in text for kw in ["家", "回家", "客厅", "家里"]):
        if any(kw in text for kw in ["吃饭", "晚饭", "晚餐", "一起"]):
            return SCENE_PRESETS["evening_home_family_dinner"]
        return SCENE_PRESETS["afternoon_home_family"]
    if any(kw in text for kw in ["逛街", "聚会", "朋友", "外面", "出去"]):
        return SCENE_PRESETS["afternoon_outdoor_social"]
    if any(kw in text for kw in ["路上", "地铁", "公交", "开车", "通勤", "下班"]):
        return SCENE_PRESETS["evening_public_transit"]
    if any(kw in text for kw in ["早起", "早上", "清晨", "刚醒"]):
        return SCENE_PRESETS["morning_alone_wakeup"]

    # ── 人际标签推断 ──
    has_partner = any(kw in text for kw in ["女朋友", "男朋友", "老公", "老婆", "伴侣", "对象", "爱人"])
    has_family = any(kw in text for kw in ["爸妈", "父母", "孩子", "家人", "家庭", "回家"])
    has_alone = any(kw in text for kw in ["一个人", "独处", "孤独", "独自"])

    # ── 时间推断 ──
    is_night = any(kw in text for kw in ["深夜", "凌晨", "半夜", "熬夜", "通宵", "晚上"])
    is_evening = any(kw in text for kw in ["傍晚", "晚上", "晚饭", "下班"])
    is_morning = any(kw in text for kw in ["早上", "清晨", "早起", "晨"])

    if has_partner:
        if is_night: return SCENE_PRESETS["evening_bedroom_partner"]
        return SCENE_PRESETS["evening_bedroom_partner"]
    if has_family:
        if is_evening: return SCENE_PRESETS["evening_home_family_dinner"]
        return SCENE_PRESETS["afternoon_home_family"]
    if has_alone and is_night:
        return SCENE_PRESETS["night_alone_bedroom"]
    if is_morning:
        return SCENE_PRESETS["morning_alone_wakeup"]

    return SCENE_PRESETS["default"]


def get_fallback_params(raw_text: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    对外唯一接口: 返回完整的瑶光客观参数兜底包。

    返回格式与 MCP constraints 参数完全兼容，可直接传入 run_static_workflow。
    """
    scene = match_scene(raw_text, user_context)
    return {
        "source": "yaoguang_fallback",
        "scene_name": scene.scene_name,
        "scene_description": scene.description,
        "is_fallback": True,
        "fallback_reason": "瑶光 MCP (harris-g) 离线，使用预设客观参数",
        "scene_tags": scene.scene_tags,
        "environmental_params": scene.environmental_params,
        "temporal_context": scene.temporal_context,
        "interpersonal_labels": scene.interpersonal_labels,
        "duration_context": scene.duration_context,
    }
