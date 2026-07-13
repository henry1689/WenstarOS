"""
activity_model.py — 瑶光客观世界·活动-体力-疲劳物理模型
========================================================
基于真人运动生理学和交通工程参数，对以下客观量进行规则化计算：
  - 步行距离 / 步行时间 / 步行消耗
  - 驾车距离 / 驾车时间（含时段/天气修正）/ 驾驶疲劳
  - 静坐 / 站立 / 家务 / 运动 代谢当量 (MET)
  - 日累计体力消耗与疲劳指数

全部规则公式，禁止 LLM 生成浮点值。
铁律: 仅输出纯量化客观参数，无主观体感。

参考标准:
  - 步行速度: 5.0 km/h (日常) / 4.0 km/h (疲劳) / 6.0 km/h (快走)
  - MET: 静坐=1.3 / 站立=1.8 / 步行(5km/h)=3.5 / 驾车=1.5 / 家务=2.8 / 跑步(8km/h)=8.0
  - 1 MET = 1 kcal/kg/h ≈ 70 kcal/h (成人标准体重70kg)
  - 驾驶注意力: 城市道路≈中等负荷, 高速≈中高负荷, 堵车≈高负荷
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import math


# ---------------------------------------------------------------------------
# 枚举
# ---------------------------------------------------------------------------

class TrafficCondition(str, Enum):
    FREE_FLOW = "free_flow"       # 畅通 (+0%)
    LIGHT = "light"                # 轻度 (+15%)
    MODERATE = "moderate"          # 中度拥堵 (+35%)
    HEAVY = "heavy"                # 重度拥堵 (+60%)
    SEVERE = "severe"              # 严重/事故 (+100%)


class WeatherImpact(str, Enum):
    CLEAR = "clear"               # 晴天 (+0%)
    RAIN_LIGHT = "rain_light"     # 小雨 (+10%)
    RAIN_HEAVY = "rain_heavy"     # 大雨 (+25%)
    TYPHOON = "typhoon"           # 台风/暴雨 (+50%)
    FOG = "fog"                   # 雾 (+15%)


class ActivityType(str, Enum):
    SITTING = "sitting"
    STANDING = "standing"
    WALKING = "walking"
    WALKING_FAST = "walking_fast"
    DRIVING = "driving"
    DRIVING_TRAFFIC = "driving_traffic"  # 堵车驾驶，注意力消耗更高
    COOKING = "cooking"
    CLEANING = "cleaning"
    EXERCISE_LIGHT = "exercise_light"    # 健身器械/拉伸
    EXERCISE_MODERATE = "exercise_moderate"  # 慢跑
    SLEEPING = "sleeping"


# ---------------------------------------------------------------------------
# 活动代谢表
# ---------------------------------------------------------------------------

# MET (Metabolic Equivalent of Task) 值
ACTIVITY_MET: Dict[ActivityType, float] = {
    ActivityType.SITTING:          1.3,
    ActivityType.STANDING:         1.8,
    ActivityType.WALKING:          3.5,
    ActivityType.WALKING_FAST:     5.0,
    ActivityType.DRIVING:          1.5,
    ActivityType.DRIVING_TRAFFIC:  1.8,  # 堵车时精神紧张+微操，代谢略高
    ActivityType.COOKING:          2.5,
    ActivityType.CLEANING:         3.0,
    ActivityType.EXERCISE_LIGHT:   4.0,
    ActivityType.EXERCISE_MODERATE: 8.0,
    ActivityType.SLEEPING:         0.9,
}

# 注意力负荷系数 (0-1, 用于驾驶疲劳计算)
ACTIVITY_ATTENTION: Dict[ActivityType, float] = {
    ActivityType.DRIVING:          0.45,
    ActivityType.DRIVING_TRAFFIC:  0.75,
    ActivityType.SITTING:          0.15,
    ActivityType.WALKING:          0.25,
    ActivityType.COOKING:          0.35,
}

# 标准体重 (kg) — 用于热量换算
STD_WEIGHT_KG = 70.0
KCAL_PER_MET_HOUR = STD_WEIGHT_KG * 1.0  # 70 kcal/h per MET


# ===================================================================
# 年龄分层生理参数
# ===================================================================

def get_age_stratified_params(age_group: str = "mature") -> Dict[str, float]:
    """返回某年龄组的体力/代谢/恢复基线参数。

    age_group: child / early_adolescent / late_adolescent / young_adult / mature / middle_age
    """
    params = {
        "child": {
            "max_hr_bpm": 200, "rest_hr_bpm": 80, "vo2max_factor": 1.1,
            "lactate_threshold_mmol": 1.5, "recovery_rate_factor": 1.4,
            "muscle_endurance_factor": 0.7, "metabolic_rate_factor": 1.15,
            "joint_flexibility_factor": 1.2,
        },
        "early_adolescent": {
            "max_hr_bpm": 195, "rest_hr_bpm": 72, "vo2max_factor": 1.05,
            "lactate_threshold_mmol": 1.4, "recovery_rate_factor": 1.25,
            "muscle_endurance_factor": 0.8, "metabolic_rate_factor": 1.10,
            "joint_flexibility_factor": 1.15,
        },
        "late_adolescent": {
            "max_hr_bpm": 195, "rest_hr_bpm": 68, "vo2max_factor": 1.0,
            "lactate_threshold_mmol": 1.35, "recovery_rate_factor": 1.15,
            "muscle_endurance_factor": 0.9, "metabolic_rate_factor": 1.05,
            "joint_flexibility_factor": 1.1,
        },
        "young_adult": {
            "max_hr_bpm": 190, "rest_hr_bpm": 68, "vo2max_factor": 1.0,
            "lactate_threshold_mmol": 1.3, "recovery_rate_factor": 1.05,
            "muscle_endurance_factor": 1.0, "metabolic_rate_factor": 1.0,
            "joint_flexibility_factor": 1.0,
        },
        "mature": {
            "max_hr_bpm": 180, "rest_hr_bpm": 66, "vo2max_factor": 0.95,
            "lactate_threshold_mmol": 1.2, "recovery_rate_factor": 0.95,
            "muscle_endurance_factor": 0.95, "metabolic_rate_factor": 0.95,
            "joint_flexibility_factor": 0.9,
        },
        "middle_age": {
            "max_hr_bpm": 165, "rest_hr_bpm": 68, "vo2max_factor": 0.80,
            "lactate_threshold_mmol": 1.0, "recovery_rate_factor": 0.75,
            "muscle_endurance_factor": 0.80, "metabolic_rate_factor": 0.85,
            "joint_flexibility_factor": 0.75,
        },
    }
    return params.get(age_group, params["mature"])


# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------

@dataclass
class WalkRoute:
    """步行路线客观参数。"""
    from_location: str         # 起点 scene_id
    to_location: str           # 终点 scene_id 或 POI 名称
    distance_m: float          # 距离 (米)
    has_uphill: bool = False   # 是否有上坡
    has_stairs: bool = False   # 是否有楼梯
    surface: str = "paved"     # 路面类型: paved/gravel/trail/indoor
    shade_coverage: float = 0.5  # 树荫覆盖率 0-1

    @property
    def walk_time_min(self) -> float:
        """步行时间 (分钟) — 标准步速 5.0 km/h = 83.3 m/min"""
        speed_m_per_min = 83.3
        if self.has_uphill:
            speed_m_per_min *= 0.85
        if self.has_stairs:
            speed_m_per_min *= 0.70
        return round(self.distance_m / speed_m_per_min, 1)

    @property
    def energy_kcal(self) -> float:
        """步行消耗 (kcal) — MET 3.5 × 体重70kg × 时间h"""
        hours = self.walk_time_min / 60.0
        return round(ACTIVITY_MET[ActivityType.WALKING] * KCAL_PER_MET_HOUR * hours, 1)

    @property
    def step_count(self) -> int:
        """估算步数 — 约0.75m/步"""
        return int(self.distance_m / 0.75)


@dataclass
class DriveRoute:
    """驾车路线客观参数。"""
    from_location: str
    to_location: str
    distance_km: float
    normal_time_min: float         # 畅通时驾驶时间
    highway_ratio: float = 0.6     # 高速占比 0-1
    urban_ratio: float = 0.4       # 城市道路占比 0-1
    typical_peak_delay_min: float = 15.0  # 典型高峰期额外耗时

    def drive_time_min(
        self,
        traffic: TrafficCondition = TrafficCondition.FREE_FLOW,
        weather: WeatherImpact = WeatherImpact.CLEAR,
    ) -> float:
        """
        驾车时间 (分钟) — 基础时间 × 交通系数 × 天气系数。

        交通系数: free_flow=1.0, light=1.15, moderate=1.35, heavy=1.60, severe=2.0
        天气系数: clear=1.0, rain_light=1.10, rain_heavy=1.25, typhoon=1.50, fog=1.15
        """
        traffic_mult = {
            TrafficCondition.FREE_FLOW: 1.00,
            TrafficCondition.LIGHT:     1.15,
            TrafficCondition.MODERATE:  1.35,
            TrafficCondition.HEAVY:     1.60,
            TrafficCondition.SEVERE:    2.00,
        }
        weather_mult = {
            WeatherImpact.CLEAR:       1.00,
            WeatherImpact.RAIN_LIGHT:  1.10,
            WeatherImpact.RAIN_HEAVY:  1.25,
            WeatherImpact.TYPHOON:     1.50,
            WeatherImpact.FOG:          1.15,
        }
        base = self.normal_time_min * traffic_mult.get(traffic, 1.0) * weather_mult.get(weather, 1.0)
        return round(base, 1)

    @property
    def energy_kcal(self) -> float:
        """驾车消耗 (kcal) — MET 1.5 × 体重 × 正常时间"""
        hours = self.normal_time_min / 60.0
        return round(ACTIVITY_MET[ActivityType.DRIVING] * KCAL_PER_MET_HOUR * hours, 1)

    def fatigue_index(self, traffic: TrafficCondition = TrafficCondition.FREE_FLOW) -> float:
        """
        驾驶疲劳指数 (0-1)。

        公式: 基础疲劳 = 0.08/10km + 交通系数加成 + 注意力衰减
        拥堵时注意力持续高负荷，疲劳加速累积。
        """
        base = self.distance_km * 0.008  # 每10km≈0.08
        traffic_bonus = {
            TrafficCondition.FREE_FLOW: 0.0,
            TrafficCondition.LIGHT:     0.05,
            TrafficCondition.MODERATE:  0.12,
            TrafficCondition.HEAVY:     0.25,
            TrafficCondition.SEVERE:    0.40,
        }.get(traffic, 0.0)
        attention_load = self.drive_time_min(traffic) / 60.0 * ACTIVITY_ATTENTION[ActivityType.DRIVING]
        raw = base + traffic_bonus + attention_load * 0.3
        return round(min(raw, 1.0), 2)


@dataclass
class DailyActivity:
    """单日活动条目。"""
    activity_type: ActivityType
    duration_min: float
    description: str = ""
    met_override: Optional[float] = None  # 自定义 MET

    @property
    def energy_kcal(self) -> float:
        met = self.met_override or ACTIVITY_MET.get(self.activity_type, 1.5)
        return round(met * KCAL_PER_MET_HOUR * self.duration_min / 60.0, 1)

    @property
    def attention_cost(self) -> float:
        """注意力消耗 (0-1)，用于疲劳累积。"""
        base = ACTIVITY_ATTENTION.get(self.activity_type, 0.1)
        return round(base * self.duration_min / 60.0, 2)


@dataclass
class FatigueEstimate:
    """疲劳估算结果 (纯客观参数)。"""
    total_energy_kcal: float
    total_attention_hours: float
    driving_fatigue: float          # 0-1
    physical_fatigue: float         # 0-1 (来自肌肉活动)
    mental_fatigue: float           # 0-1 (来自注意力消耗)
    composite_fatigue: float        # 0-1 综合疲劳指数
    recommended_rest_min: float     # 建议休息时长
    lactate_estimate: float         # 估算乳酸 mmol/L (仅体力活动)


# ---------------------------------------------------------------------------
# 活动-疲劳计算引擎
# ---------------------------------------------------------------------------

def compute_daily_fatigue(
    activities: List[DailyActivity],
    drive_routes: Optional[List[Tuple[DriveRoute, TrafficCondition]]] = None,
    walk_routes: Optional[List[WalkRoute]] = None,
    sleep_hours: float = 7.0,
    base_lactate: float = 1.0,
) -> FatigueEstimate:
    """
    根据当日活动列表计算综合疲劳度。

    Args:
        activities: 当日活动条目
        drive_routes: 驾车路线+路况
        walk_routes: 步行路线
        sleep_hours: 睡眠时长
        base_lactate: 基础乳酸值

    Returns:
        FatigueEstimate 纯客观疲劳参数
    """
    total_energy = 0.0
    total_attention = 0.0
    lactate = base_lactate

    for a in activities:
        total_energy += a.energy_kcal
        total_attention += a.attention_cost

    drive_fatigue = 0.0
    if drive_routes:
        for route, traffic in drive_routes:
            drive_fatigue = max(drive_fatigue, route.fatigue_index(traffic))
            total_energy += route.energy_kcal
            total_attention += route.drive_time_min(traffic) / 60.0 * ACTIVITY_ATTENTION[
                ActivityType.DRIVING_TRAFFIC if traffic in (TrafficCondition.HEAVY, TrafficCondition.SEVERE)
                else ActivityType.DRIVING
            ]

    if walk_routes:
        for wr in walk_routes:
            total_energy += wr.energy_kcal
            # 步行乳酸增量: 每10分钟步行≈+0.05mmol/L
            lactate += wr.walk_time_min / 10.0 * 0.05

    # 体力疲劳: 基于 MET-hours 和乳酸
    met_hours = total_energy / KCAL_PER_MET_HOUR
    physical_fatigue = min(met_hours / 12.0 + (lactate - base_lactate) * 0.3, 1.0)  # 12 MET-hours≈很累
    physical_fatigue = round(max(0.0, physical_fatigue), 2)

    # 精神疲劳: 基于注意力消耗小时数
    mental_fatigue = round(min(total_attention / 8.0, 1.0), 2)  # 8h 高注意力≈精神耗尽

    # 驾驶疲劳单独计
    drive_fatigue = round(drive_fatigue, 2)

    # 综合: 加权平均
    composite = round(physical_fatigue * 0.35 + mental_fatigue * 0.35 + drive_fatigue * 0.30, 2)
    composite = min(composite, 1.0)

    # 推荐休息: 基于综合疲劳
    rest = round(composite * 60.0, 0)  # 疲劳度0→0min, 1→60min

    # 睡眠修正
    sleep_deficit = max(0.0, 7.5 - sleep_hours)
    composite *= (1.0 + sleep_deficit * 0.15)  # 每缺1h睡眠→15%疲劳加成
    composite = round(min(composite, 1.0), 2)

    return FatigueEstimate(
        total_energy_kcal=round(total_energy, 0),
        total_attention_hours=round(total_attention, 1),
        driving_fatigue=drive_fatigue,
        physical_fatigue=physical_fatigue,
        mental_fatigue=mental_fatigue,
        composite_fatigue=composite,
        recommended_rest_min=rest,
        lactate_estimate=round(lactate, 2),
    )


def estimate_lactate_clearance(
    current_lactate: float,
    rest_minutes: float,
    sleep_hours: float = 7.0,
) -> float:
    """
    估算休息后乳酸清除量。

    标准清除速率: 1.2 mmol/h (D7 基线)
    睡眠不足时清除速率下降。
    """
    rate = 1.2 - max(0, 7.5 - sleep_hours) * 0.15  # 缺觉→清除慢
    rate = max(0.3, rate)  # 最低不低于 0.3
    cleared = rate * rest_minutes / 60.0
    return round(max(0.3, current_lactate - cleared), 2)


# ===================================================================
# 用户真实场景的物理数据
# ===================================================================

# ── 步行路线库 ──

WALK_ROUTES: Dict[str, WalkRoute] = {}

def _reg_walk(route: WalkRoute) -> None:
    WALK_ROUTES[f"{route.from_location}→{route.to_location}"] = route

# 星海名城 → 周边 POI
_reg_walk(WalkRoute("xinghai_mingcheng", "荷兰花卉小镇", 500, shade_coverage=0.4))
_reg_walk(WalkRoute("xinghai_mingcheng", "前海公园", 500, shade_coverage=0.6))
_reg_walk(WalkRoute("xinghai_mingcheng", "前海地铁站", 800, shade_coverage=0.3))
_reg_walk(WalkRoute("xinghai_mingcheng", "社区健身器械区", 100, shade_coverage=0.7))
_reg_walk(WalkRoute("xinghai_mingcheng", "社区喷泉", 80, shade_coverage=0.5))
_reg_walk(WalkRoute("xinghai_mingcheng", "社区假山", 120, shade_coverage=0.5, has_uphill=True))

# 公寓 → 周边
_reg_walk(WalkRoute("guangming_apartment", "公司办公楼", 200, shade_coverage=0.5))
_reg_walk(WalkRoute("guangming_apartment", "街边公园", 50, shade_coverage=0.8))
_reg_walk(WalkRoute("guangming_apartment", "小溪步道", 80, shade_coverage=0.7))
_reg_walk(WalkRoute("guangming_apartment", "凤凰街道商圈", 800, shade_coverage=0.3))

# 办公室 → 周边
_reg_walk(WalkRoute("guangming_office", "园区食堂", 150, shade_coverage=0.2))
_reg_walk(WalkRoute("guangming_office", "公司公寓", 200, shade_coverage=0.5))


# ── 驾车路线 ──

DRIVE_ROUTES: Dict[str, DriveRoute] = {}

DRIVE_ROUTES["home→office"] = DriveRoute(
    from_location="xinghai_mingcheng",
    to_location="guangming_office",
    distance_km=30.0,
    normal_time_min=45.0,
    highway_ratio=0.65,
    urban_ratio=0.35,
    typical_peak_delay_min=20.0,
)

DRIVE_ROUTES["office→home"] = DriveRoute(
    from_location="guangming_office",
    to_location="xinghai_mingcheng",
    distance_km=30.0,
    normal_time_min=45.0,
    highway_ratio=0.65,
    urban_ratio=0.35,
    typical_peak_delay_min=22.0,  # 晚高峰略重于早高峰
)


# ── 典型日模板 ──

def build_typical_workday(
    work_hours: float = 9.0,
    lunch_break_min: float = 60.0,
    commute_traffic: TrafficCondition = TrafficCondition.MODERATE,
    weather: WeatherImpact = WeatherImpact.CLEAR,
    evening_walk: bool = True,
    use_apartment: bool = False,
) -> Tuple[List[DailyActivity], List[Tuple[DriveRoute, TrafficCondition]], List[WalkRoute]]:
    """
    构建一个典型工作日的活动/驾驶/步行列表。

    场景 A: 从星海名城开车去公司（use_apartment=False）
    场景 B: 从公司公寓步行去公司（use_apartment=True）
    """
    activities: List[DailyActivity] = []
    drives: List[Tuple[DriveRoute, TrafficCondition]] = []
    walks: List[WalkRoute] = []

    if use_apartment:
        # 场景 B: 公寓 → 步行上班
        route_walk = WALK_ROUTES.get("guangming_apartment→公司办公楼")
        if route_walk:
            walks.append(route_walk)
            walks.append(route_walk)  # 往返
    else:
        # 场景 A: 星海名城 → 开车上班
        dr = DRIVE_ROUTES.get("home→office")
        if dr:
            drives.append((dr, commute_traffic))
        dr_back = DRIVE_ROUTES.get("office→home")
        if dr_back:
            drives.append((dr_back, commute_traffic))

    # 工作时间
    activities.append(DailyActivity(ActivityType.SITTING, work_hours * 60, "办公"))

    # 午休
    activities.append(DailyActivity(ActivityType.WALKING, 10, "步行去食堂"))
    activities.append(DailyActivity(ActivityType.SITTING, lunch_break_min - 10, "午餐"))

    # 晚间活动
    if evening_walk:
        route_evening = WALK_ROUTES.get(
            "xinghai_mingcheng→社区健身器械区" if not use_apartment else "guangming_apartment→街边公园"
        )
        if route_evening:
            walks.append(route_evening)
        activities.append(DailyActivity(ActivityType.EXERCISE_LIGHT, 20, "健身器械/散步"))

    activities.append(DailyActivity(ActivityType.SITTING, 120, "晚间休闲"))
    activities.append(DailyActivity(ActivityType.SLEEPING, 7.5 * 60, "睡眠"))

    return activities, drives, walks


# ── 场景环境基线参数库 ──

@dataclass
class SceneEnvBaseline:
    """场景环境客观基线 — 用于 D8/D21-D26 通道计算的默认输入。"""
    scene_id: str
    # 不同时段的环境参数
    morning_temp: float = 24.0
    afternoon_temp: float = 28.0
    evening_temp: float = 26.0
    night_temp: float = 25.0
    noise_db: float = 40.0
    # 光照
    morning_lux: float = 5000
    afternoon_lux: float = 30000
    evening_lux: float = 300
    night_lux: float = 50
    # 空间
    crowd_density: float = 0.1
    has_ac: bool = True       # 是否有空调
    has_elevator: bool = True
    floor_level: int = 1       # 楼层 (1=地面)


SCENE_ENV_BASELINES: Dict[str, SceneEnvBaseline] = {
    "xinghai_mingcheng": SceneEnvBaseline(
        scene_id="xinghai_mingcheng",
        morning_temp=25.0, afternoon_temp=29.0, evening_temp=27.0, night_temp=26.0,
        noise_db=32.0,
        morning_lux=3000, afternoon_lux=25000, evening_lux=200, night_lux=30,
        crowd_density=0.05,
        has_ac=True, has_elevator=True, floor_level=8,
    ),
    "guangming_office": SceneEnvBaseline(
        scene_id="guangming_office",
        morning_temp=23.0, afternoon_temp=25.0, evening_temp=24.0, night_temp=23.0,
        noise_db=50.0,
        morning_lux=8000, afternoon_lux=15000, evening_lux=500, night_lux=100,
        crowd_density=0.35,
        has_ac=True, has_elevator=True, floor_level=3,
    ),
    "guangming_apartment": SceneEnvBaseline(
        scene_id="guangming_apartment",
        morning_temp=23.0, afternoon_temp=26.0, evening_temp=25.0, night_temp=24.0,
        noise_db=30.0,
        morning_lux=4000, afternoon_lux=20000, evening_lux=250, night_lux=40,
        crowd_density=0.03,
        has_ac=True, has_elevator=True, floor_level=5,
    ),
}
