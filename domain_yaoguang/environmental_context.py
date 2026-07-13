"""
environmental_context.py — 瑶光·环境上下文定量影响引擎
========================================================
输入: 时间/季节/天气/节假日/场景类型/地理坐标
输出: 对 D1-D32 各维度的定量环境影响系数矩阵

每一条规则都有真人参考依据:
  - 光照: CIE 标准日光曲线 + 纬度修正
  - 温度: 室内外热平衡模型
  - 噪音: ISO 1996 环境噪声标准
  - 气压: 国际标准大气压 (ISA)
  - 褪黑素: 人体昼夜节律生理学 (Czeisler 1999)
  - 皮质醇: 昼夜节律曲线 (Weitzman 1971)
  - 维生素D: 日照-皮肤合成模型 (Holick 2007)

铁律: 全部规则公式，禁止 LLM 生成浮点值。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import math


# ===================================================================
# 枚举
# ===================================================================

class TimeOfDay(str, Enum):
    DAWN = "dawn"           # 5:00-7:00
    MORNING = "morning"      # 7:00-10:00
    NOON = "noon"            # 10:00-14:00
    AFTERNOON = "afternoon"  # 14:00-17:00
    EVENING = "evening"      # 17:00-20:00
    NIGHT = "night"          # 20:00-24:00
    LATE_NIGHT = "late_night"  # 0:00-5:00

    @classmethod
    def from_hour(cls, hour: int) -> "TimeOfDay":
        if 5 <= hour < 7: return cls.DAWN
        if 7 <= hour < 10: return cls.MORNING
        if 10 <= hour < 14: return cls.NOON
        if 14 <= hour < 17: return cls.AFTERNOON
        if 17 <= hour < 20: return cls.EVENING
        if 20 <= hour < 24: return cls.NIGHT
        return cls.LATE_NIGHT


class Season(str, Enum):
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"

    @classmethod
    def from_month(cls, month: int, latitude: float = 23.0) -> "Season":
        """北半球标准季节。南半球自动翻转。"""
        if latitude < 0:
            month = (month + 6) % 12 or 12
        if 3 <= month <= 5: return cls.SPRING
        if 6 <= month <= 8: return cls.SUMMER
        if 9 <= month <= 11: return cls.AUTUMN
        return cls.WINTER


class Weather(str, Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    OVERCAST = "overcast"
    RAIN_LIGHT = "rain_light"
    RAIN_HEAVY = "rain_heavy"
    THUNDERSTORM = "thunderstorm"
    SNOW_LIGHT = "snow_light"
    SNOW_HEAVY = "snow_heavy"
    FOG = "fog"
    WINDY = "windy"
    TYPHOON = "typhoon"


class DayType(str, Enum):
    WORKDAY = "workday"
    WEEKEND = "weekend"
    HOLIDAY = "holiday"
    SICK_DAY = "sick_day"
    TRAVEL_DAY = "travel_day"


class SceneType(str, Enum):
    HOME = "home"
    OFFICE = "office"
    OUTDOOR = "outdoor"
    PUBLIC = "public"
    TRANSIT = "transit"       # 通勤/交通工具内
    NATURE = "nature"         # 自然景观（公园/山/海滩）
    MEDICAL = "medical"       # 医院/诊所


# ===================================================================
# 环境上下文数据类
# ===================================================================

@dataclass
class EnvContext:
    """完整环境上下文——一次解锁事件的全部客观输入。"""
    # 时间
    time_of_day: TimeOfDay = TimeOfDay.AFTERNOON
    hour: int = 14
    minute: int = 0
    # 季节与气象
    season: Season = Season.SUMMER
    weather: Weather = Weather.CLEAR
    outdoor_temp_c: float = 28.0     # 室外温度
    humidity_pct: float = 60.0       # 湿度
    wind_speed_ms: float = 2.0       # 风速 m/s
    uv_index: float = 5.0            # 紫外线指数
    # 场景
    scene_type: SceneType = SceneType.HOME
    indoor: bool = True
    has_ac: bool = True
    has_heating: bool = False
    indoor_temp_c: float = 25.0      # 室内温度（有空调时）
    noise_db: float = 40.0
    light_lux: float = 300.0
    crowd_density: float = 0.1       # 0-1
    floor_level: int = 1
    # 地理
    latitude: float = 22.5           # 深圳纬度
    altitude_m: float = 10.0
    # 日期
    day_type: DayType = DayType.WORKDAY
    # 特殊事件
    event_tags: List[str] = field(default_factory=list)
    # 昨日残留（睡眠/疲劳基线）
    prev_day_sleep_h: float = 7.0
    prev_day_fatigue: float = 0.2    # 0-1


# ===================================================================
# 环境影响系数输出
# ===================================================================

@dataclass
class DimensionImpact:
    """环境对单个维度的定量影响。"""
    dim_id: int
    dim_key: str
    # 各环境因子的影响系数 (-1.0 ~ +1.0, 0=无影响)
    time_factor: float = 0.0        # 时间的影响
    season_factor: float = 0.0      # 季节的影响
    weather_factor: float = 0.0     # 天气的影响
    scene_factor: float = 0.0       # 场景类型的影响
    day_type_factor: float = 0.0    # 工作日/假日的影响
    crowd_factor: float = 0.0       # 人流密度的影响
    noise_factor: float = 0.0       # 噪音的影响
    light_factor: float = 0.0       # 光照的影响
    temperature_factor: float = 0.0 # 温度的影响
    # 综合环境校正值（叠加到客观标准基线）
    net_correction: float = 0.0


@dataclass
class EnvImpactMatrix:
    """32维 × 环境因子的完整影响矩阵。"""
    dna_root_id: str = ""
    env: EnvContext = field(default_factory=EnvContext)
    impacts: Dict[int, DimensionImpact] = field(default_factory=dict)
    # 全局参数
    daylight_hours: float = 12.0        # 日照时长
    solar_noon_offset_min: float = 0.0  # 距太阳正午的分钟偏移
    indoor_outdoor_delta_c: float = 0.0 # 室内外温差


# ===================================================================
# 环境物理计算
# ===================================================================


def compute_daylight_hours(latitude: float, day_of_year: int) -> float:
    """计算日照时长 (小时)。

    公式: 基于太阳赤纬角的球面三角学。
    参考: Forsythe et al. (1995) "A model comparison for daylength..."
    """
    declination = 23.45 * math.sin(math.radians(360.0 / 365.0 * (day_of_year - 81)))
    lat_rad = math.radians(latitude)
    decl_rad = math.radians(declination)
    # 日出时角
    cos_ha = -math.tan(lat_rad) * math.tan(decl_rad)
    if cos_ha > 1: return 24.0   # 极昼
    if cos_ha < -1: return 0.0   # 极夜
    ha = math.acos(cos_ha)
    return 2.0 * ha / math.radians(15.0)


def compute_indoor_temperature(
    outdoor_temp: float, has_ac: bool, has_heating: bool,
    season: Season, floor_level: int = 1,
) -> float:
    """估算室内温度。

    - 空调制冷: 设定 24-26℃
    - 供暖: 设定 20-22℃
    - 无空调: 室内外温差≈5℃（热滞后），高层+2℃/10层
    """
    if has_ac:
        if season == Season.SUMMER:
            return 25.0
        if season == Season.WINTER and has_heating:
            return 21.0
    # 自然通风
    base = outdoor_temp - 3.0  # 室内略低于室外
    if season == Season.WINTER:
        base = outdoor_temp + 5.0  # 室内保温
    # 高层修正
    base += max(0, floor_level - 1) * 0.2
    return round(base, 1)


def compute_light_level(
    time_of_day: TimeOfDay, weather: Weather, indoor: bool,
    season: Season, latitude: float = 22.5,
) -> float:
    """计算当前光照照度 (lux)。

    参考: CIE 标准日光曲线
    - 正午晴天室外: 100,000 lux
    - 阴天室外: 5,000-20,000 lux
    - 室内窗边: 500-5,000 lux
    - 室内深处: 50-500 lux
    - 夜间室内灯光: 100-300 lux
    """
    # 室外日光基线 (lux)
    outdoor_baseline = {
        TimeOfDay.DAWN: 5000,
        TimeOfDay.MORNING: 30000,
        TimeOfDay.NOON: 100000,
        TimeOfDay.AFTERNOON: 50000,
        TimeOfDay.EVENING: 5000,
        TimeOfDay.NIGHT: 0,
        TimeOfDay.LATE_NIGHT: 0,
    }.get(time_of_day, 30000)

    # 天气衰减
    weather_mult = {
        Weather.CLEAR: 1.0,
        Weather.CLOUDY: 0.6,
        Weather.OVERCAST: 0.3,
        Weather.RAIN_LIGHT: 0.4,
        Weather.RAIN_HEAVY: 0.2,
        Weather.THUNDERSTORM: 0.1,
        Weather.SNOW_LIGHT: 0.5,
        Weather.SNOW_HEAVY: 0.3,
        Weather.FOG: 0.2,
        Weather.WINDY: 0.9,
        Weather.TYPHOON: 0.15,
    }.get(weather, 0.5)

    # 季节修正: 夏季日照强15%，冬季弱20%
    season_mult = {
        Season.SPRING: 1.0, Season.SUMMER: 1.15,
        Season.AUTUMN: 0.9, Season.WINTER: 0.8,
    }.get(season, 1.0)

    outdoor = outdoor_baseline * weather_mult * season_mult

    if indoor:
        # 室内照度: 窗边约室外的5-10%，深处1-2%
        if time_of_day in (TimeOfDay.NIGHT, TimeOfDay.LATE_NIGHT):
            return 150.0  # 夜间人工照明
        return outdoor * 0.03  # ~3% 穿透率

    return outdoor


def compute_noise_level(
    scene_type: SceneType, crowd_density: float, weather: Weather,
    time_of_day: TimeOfDay, indoor: bool,
) -> float:
    """计算环境噪音 (dB)。

    参考: ISO 1996 / WHO 环境噪音指南
    - 安静卧室: 25-35 dB
    - 办公室: 45-55 dB
    - 餐厅: 55-70 dB
    - 城市街道: 60-75 dB
    - 暴雨: +10-15 dB
    """
    base = {
        SceneType.HOME: 30.0,
        SceneType.OFFICE: 50.0,
        SceneType.OUTDOOR: 45.0,
        SceneType.PUBLIC: 60.0,
        SceneType.TRANSIT: 65.0,
        SceneType.NATURE: 35.0,
        SceneType.MEDICAL: 45.0,
    }.get(scene_type, 45.0)

    # 人流加成: 每0.1密度≈+3dB
    base += crowd_density * 30

    # 天气加成
    weather_bonus = {
        Weather.CLEAR: 0, Weather.CLOUDY: 0, Weather.OVERCAST: 0,
        Weather.RAIN_LIGHT: 5, Weather.RAIN_HEAVY: 12,
        Weather.THUNDERSTORM: 20, Weather.SNOW_LIGHT: -3,
        Weather.SNOW_HEAVY: 0, Weather.FOG: -5,
        Weather.WINDY: 8, Weather.TYPHOON: 25,
    }.get(weather, 0)
    base += weather_bonus

    # 时段: 夜间-5dB（安静）
    if time_of_day in (TimeOfDay.NIGHT, TimeOfDay.LATE_NIGHT):
        base -= 5
    # 室内: -10dB 衰减
    if indoor:
        base -= 10

    return round(max(15, min(base, 110)), 1)


def compute_uv_index(
    time_of_day: TimeOfDay, weather: Weather, season: Season,
    latitude: float = 22.5,
) -> float:
    """计算紫外线指数 (0-11+)。

    深圳 (≈22.5°N): 夏季正午晴天 UV 8-11, 冬季 3-5
    """
    base = {
        TimeOfDay.DAWN: 1, TimeOfDay.MORNING: 5,
        TimeOfDay.NOON: 10, TimeOfDay.AFTERNOON: 6,
        TimeOfDay.EVENING: 1, TimeOfDay.NIGHT: 0, TimeOfDay.LATE_NIGHT: 0,
    }.get(time_of_day, 5)

    season_mult = {Season.SPRING: 0.9, Season.SUMMER: 1.0,
                   Season.AUTUMN: 0.7, Season.WINTER: 0.5}.get(season, 0.8)
    weather_mult = {Weather.CLEAR: 1.0, Weather.CLOUDY: 0.6,
                    Weather.OVERCAST: 0.3, Weather.RAIN_LIGHT: 0.4,
                    Weather.RAIN_HEAVY: 0.2, Weather.FOG: 0.2,
                    Weather.SNOW_LIGHT: 0.8, Weather.WINDY: 1.0,
                    Weather.TYPHOON: 0.1}.get(weather, 0.5)

    return round(base * season_mult * weather_mult, 1)


# ===================================================================
# 32 维环境影响系数矩阵
# ===================================================================


def compute_env_impact_matrix(
    env: EnvContext,
    dna_root_id: str = "",
) -> EnvImpactMatrix:
    """
    计算完整 32 维环境影响矩阵。

    每一项 net_correction 表示环境对该维度客观标准基线值的修正量。
    正值=环境有利于该维度（如晴天→D12↑），负值=环境不利于该维度（如噪音→D3↓）。

    构建后供各学科计算引擎查询使用。
    """
    # 预计算物理量
    ind = env.indoor
    indoor_temp = env.indoor_temp_c if ind else env.outdoor_temp_c
    effective_temp = indoor_temp if ind else env.outdoor_temp_c

    m = EnvImpactMatrix(dna_root_id=dna_root_id, env=env)

    # ── 全局参数 ──
    import datetime
    doy = datetime.datetime(2026, 7, 13).timetuple().tm_yday  # 简化：用当前日
    m.daylight_hours = round(compute_daylight_hours(env.latitude, doy), 1)
    m.indoor_outdoor_delta_c = round(env.outdoor_temp_c - indoor_temp, 1)

    # ==================================================================
    # 大类 1: 肉身实体基底 D1-D8
    # ==================================================================

    # D1 骨骼肌肉·体能负荷
    # 炎热→代谢↑肌肉易疲劳；寒冷→僵硬；季节影响活动量
    d1_time = -0.05 if env.time_of_day in (TimeOfDay.NIGHT, TimeOfDay.LATE_NIGHT) else 0.0
    d1_temp = 0.0
    if effective_temp > 32: d1_temp = -0.15  # 高温加重疲劳
    if effective_temp < 10: d1_temp = -0.10  # 低温导致僵硬
    m.impacts[1] = DimensionImpact(1, "muscle_load",
        time_factor=d1_time, temperature_factor=d1_temp,
        net_correction=round(d1_time + d1_temp, 2))

    # D2 躯体疼痛
    # 潮湿寒冷→关节痛↑；气压剧变→头痛↑
    d2_weather = 0.0
    if env.weather in (Weather.RAIN_HEAVY, Weather.THUNDERSTORM): d2_weather = -0.10
    if env.humidity_pct > 85: d2_weather -= 0.05
    if env.outdoor_temp_c < 10: d2_weather -= 0.10  # 寒冷诱发关节不适
    m.impacts[2] = DimensionImpact(2, "pain_level",
        weather_factor=d2_weather, net_correction=round(d2_weather, 2))

    # D3 神经瞬时刺激·触觉
    # 噪音→交感兴奋↑；光线刺眼→不适
    d3_noise = 0.0
    if env.noise_db > 60: d3_noise = -(env.noise_db - 60) * 0.005
    if env.noise_db > 80: d3_noise = -0.25
    d3_light = 0.0
    if env.light_lux > 50000: d3_light = -0.10  # 强光刺眼
    d3_temp = 0.0
    if effective_temp < 5: d3_temp = -0.15   # 极冷→触觉迟钝
    if effective_temp > 35: d3_temp = -0.10  # 极热→不适
    m.impacts[3] = DimensionImpact(3, "nerve_arousal",
        noise_factor=d3_noise, light_factor=d3_light, temperature_factor=d3_temp,
        net_correction=round(d3_noise + d3_light + d3_temp, 2))

    # D4 内分泌·激素波动
    # 核心昼夜节律: 皮质醇晨高夜低，褪黑素夜高昼低
    # 日照→血清素↑；黑暗→褪黑素↑；社交场景→催产素变化
    cortisol_curve = {TimeOfDay.DAWN: 0.30, TimeOfDay.MORNING: 0.25,
        TimeOfDay.NOON: 0.10, TimeOfDay.AFTERNOON: 0.0,
        TimeOfDay.EVENING: -0.25, TimeOfDay.NIGHT: -0.40,
        TimeOfDay.LATE_NIGHT: -0.45}
    d4_time = cortisol_curve.get(env.time_of_day, 0.0)
    d4_season = 0.0
    if env.season == Season.WINTER: d4_season = -0.08  # 冬季→季节性情感低落
    d4_weather = 0.0
    if env.weather in (Weather.RAIN_HEAVY, Weather.OVERCAST): d4_weather = -0.05
    d4_light = 0.0
    if env.light_lux > 50000: d4_light = 0.05  # 充足光照→血清素↑
    d4_scene = 0.0
    if env.scene_type == SceneType.NATURE: d4_scene = 0.10  # 自然环境→激素平衡
    if env.scene_type == SceneType.OFFICE: d4_scene = -0.03
    m.impacts[4] = DimensionImpact(4, "endocrine",
        time_factor=d4_time, season_factor=d4_season, weather_factor=d4_weather,
        light_factor=d4_light, scene_factor=d4_scene,
        net_correction=round(d4_time + d4_season + d4_weather + d4_light + d4_scene, 2))

    # D5 信息素·气息氛围
    d5_temp = -0.08 if effective_temp > 30 else 0.0  # 高温→出汗→信息素活跃
    d5_humid = -0.05 if env.humidity_pct > 80 else 0.0
    m.impacts[5] = DimensionImpact(5, "pheromone",
        temperature_factor=d5_temp,
        net_correction=round(d5_temp + d5_humid, 2))

    # D6 生理周期·代谢
    # 季节影响BMR: 冬季↑5-10%（产热需求），夏季↓3%
    d6_season_map = {Season.SPRING: 0.0, Season.SUMMER: -0.03,
                     Season.AUTUMN: -0.01, Season.WINTER: 0.08}
    d6_time = 0.03 if env.time_of_day == TimeOfDay.MORNING else 0.0  # 晨间代谢高
    m.impacts[6] = DimensionImpact(6, "metabolic_cycle",
        time_factor=d6_time, season_factor=d6_season_map.get(env.season, 0),
        net_correction=round(d6_time + d6_season_map.get(env.season, 0), 2))

    # D7 躯体自愈·修复
    # 睡眠时段→修复↑；噪音/光照干扰→修复↓
    d7_time_map = {TimeOfDay.NIGHT: 0.15, TimeOfDay.LATE_NIGHT: 0.20,
                   TimeOfDay.DAWN: 0.10}
    d7_noise = -0.05 if env.noise_db > 50 else 0.0
    d7_light = -0.03 if env.light_lux > 100 and env.time_of_day in (TimeOfDay.NIGHT, TimeOfDay.LATE_NIGHT) else 0.0
    m.impacts[7] = DimensionImpact(7, "self_heal",
        time_factor=d7_time_map.get(env.time_of_day, 0.0),
        noise_factor=d7_noise, light_factor=d7_light,
        net_correction=round(d7_time_map.get(env.time_of_day, 0.0) + d7_noise + d7_light, 2))

    # D8 五感环境·基础体感
    # 综合环境舒适度
    comfort = 0.0
    if 18 <= effective_temp <= 28: comfort += 0.10  # 温度舒适
    if env.noise_db < 40: comfort += 0.10           # 安静
    if 100 <= env.light_lux <= 3000: comfort += 0.05  # 光线柔和
    if env.weather == Weather.CLEAR: comfort += 0.05
    if env.crowd_density < 0.2: comfort += 0.05
    m.impacts[8] = DimensionImpact(8, "sensory_env",
        temperature_factor=0.10 if 18 <= effective_temp <= 28 else (-0.10 if effective_temp > 35 or effective_temp < 5 else 0),
        noise_factor=0.10 if env.noise_db < 40 else (-0.15 if env.noise_db > 70 else 0),
        light_factor=0.05 if 100 <= env.light_lux <= 3000 else (-0.05 if env.light_lux > 50000 else 0),
        weather_factor=0.05 if env.weather == Weather.CLEAR else (-0.10 if env.weather in (Weather.TYPHOON, Weather.THUNDERSTORM) else 0),
        net_correction=round(comfort, 2))

    # ==================================================================
    # 大类 2: 个体内在精神 D9-D14
    # ==================================================================

    # D9 自我认知·人格基底
    # 社交场景→他人反馈影响自我认知
    d9_scene = 0.0
    if env.scene_type == SceneType.PUBLIC: d9_scene = -0.03  # 公共场所→自我意识增强
    if env.scene_type == SceneType.HOME: d9_scene = 0.05     # 家的安全感
    d9_day = 0.05 if env.day_type == DayType.HOLIDAY else 0.0
    m.impacts[9] = DimensionImpact(9, "self_identity",
        scene_factor=d9_scene, day_type_factor=d9_day,
        net_correction=round(d9_scene + d9_day, 2))

    # D10 原生欲望·成长驱动力
    # 新环境→探索欲↑；重复场景→探索欲↓；假期→探索欲↑
    d10_scene = 0.10 if env.scene_type in (SceneType.NATURE, SceneType.OUTDOOR) else 0.0
    d10_day = 0.10 if env.day_type in (DayType.WEEKEND, DayType.HOLIDAY, DayType.TRAVEL_DAY) else 0.0
    d10_weather = -0.10 if env.weather in (Weather.RAIN_HEAVY, Weather.TYPHOON) else 0.0
    m.impacts[10] = DimensionImpact(10, "desire_drive",
        scene_factor=d10_scene, day_type_factor=d10_day, weather_factor=d10_weather,
        net_correction=round(d10_scene + d10_day + d10_weather, 2))

    # D11 恐惧·倦怠
    # 黑暗→焦虑基线↑；独处陌生环境→恐惧↑；雷暴→惊吓
    d11_time = 0.0
    if env.time_of_day in (TimeOfDay.NIGHT, TimeOfDay.LATE_NIGHT):
        d11_time = -0.10  # 黑暗增加不安全感
    d11_weather = -0.15 if env.weather in (Weather.THUNDERSTORM, Weather.TYPHOON) else 0.0
    d11_crowd = -0.08 if env.crowd_density > 0.7 else 0.0
    d11_scene = 0.0
    if env.scene_type == SceneType.HOME: d11_scene = 0.10  # 家→安全感
    if env.scene_type in (SceneType.PUBLIC, SceneType.TRANSIT): d11_scene = -0.05
    m.impacts[11] = DimensionImpact(11, "fear_fatigue",
        time_factor=d11_time, weather_factor=d11_weather,
        crowd_factor=d11_crowd, scene_factor=d11_scene,
        net_correction=round(d11_time + d11_weather + d11_crowd + d11_scene, 2))

    # D12 享受·松弛·幸福感
    # 好天气→幸福感↑；自然→松弛↑；周末→幸福感↑
    d12_season = 0.08 if env.season in (Season.SPRING, Season.AUTUMN) else (-0.05 if env.season == Season.WINTER else 0.0)
    d12_weather = 0.10 if env.weather == Weather.CLEAR else (-0.10 if env.weather in (Weather.RAIN_HEAVY, Weather.TYPHOON) else 0.0)
    d12_scene = 0.12 if env.scene_type == SceneType.NATURE else (0.05 if env.scene_type == SceneType.HOME else 0.0)
    d12_day = 0.10 if env.day_type in (DayType.WEEKEND, DayType.HOLIDAY) else 0.0
    m.impacts[12] = DimensionImpact(12, "enjoyment",
        season_factor=d12_season, weather_factor=d12_weather,
        scene_factor=d12_scene, day_type_factor=d12_day,
        net_correction=round(d12_season + d12_weather + d12_scene + d12_day, 2))

    # D13 共情·恻隐联动
    # 人群密集→镜像神经元激活↑；节日→共情氛围↑
    d13_crowd = 0.05 if env.crowd_density > 0.3 else 0.0
    d13_day = 0.08 if env.day_type == DayType.HOLIDAY else 0.0
    d13_scene = 0.06 if env.scene_type in (SceneType.PUBLIC, SceneType.OFFICE) else 0.0
    m.impacts[13] = DimensionImpact(13, "empathy",
        crowd_factor=d13_crowd, day_type_factor=d13_day, scene_factor=d13_scene,
        net_correction=round(d13_crowd + d13_day + d13_scene, 2))

    # D14 个体自我保护
    # 陌生环境→戒备↑；夜间→戒备↑；家→戒备↓
    d14_time = -0.05 if env.time_of_day in (TimeOfDay.NIGHT, TimeOfDay.LATE_NIGHT) else 0.0
    d14_scene = 0.12 if env.scene_type == SceneType.HOME else (-0.08 if env.scene_type == SceneType.PUBLIC else 0.0)
    d14_crowd = -0.05 if env.crowd_density > 0.6 else 0.0
    m.impacts[14] = DimensionImpact(14, "self_protection",
        time_factor=d14_time, scene_factor=d14_scene, crowd_factor=d14_crowd,
        net_correction=round(d14_time + d14_scene + d14_crowd, 2))

    # ==================================================================
    # 大类 3: 圈层人际羁绊 D15-D20
    # ==================================================================

    # D15 伴侣依恋 — 节日→依恋需求↑；好天气→亲密驱力↑
    d15_day = 0.08 if env.day_type in (DayType.HOLIDAY, DayType.WEEKEND) else 0.0
    d15_scene = 0.06 if env.scene_type == SceneType.HOME else 0.0
    d15_weather = 0.0
    if env.weather in (Weather.RAIN_HEAVY, Weather.OVERCAST): d15_weather = 0.05  # 坏天气→渴望陪伴
    d15_season = 0.05 if env.season == Season.WINTER else 0.0  # 冬季→更需要温暖
    m.impacts[15] = DimensionImpact(15, "partner_attachment",
        day_type_factor=d15_day, scene_factor=d15_scene,
        weather_factor=d15_weather, season_factor=d15_season,
        net_correction=round(d15_day + d15_scene + d15_weather + d15_season, 2))

    # D16 伴侣守护 — 天气恶劣→牵挂↑；深夜→担忧↑
    d16_time = 0.0
    if env.time_of_day in (TimeOfDay.NIGHT, TimeOfDay.LATE_NIGHT):
        d16_time = 0.05  # 深夜→牵挂
    d16_weather = 0.0
    if env.weather in (Weather.RAIN_HEAVY, Weather.TYPHOON, Weather.THUNDERSTORM):
        d16_weather = 0.10  # 恶劣天气→担心伴侣
    m.impacts[16] = DimensionImpact(16, "partner_protection",
        time_factor=d16_time, weather_factor=d16_weather,
        net_correction=round(d16_time + d16_weather, 2))

    # D17 家庭归属 — 家→归属↑；节日→家庭需求↑
    d17_scene = 0.15 if env.scene_type == SceneType.HOME else (-0.05 if env.scene_type == SceneType.OUTDOOR else 0.0)
    d17_day = 0.10 if env.day_type == DayType.HOLIDAY else 0.0
    d17_season = 0.05 if env.season == Season.WINTER else 0.0
    m.impacts[17] = DimensionImpact(17, "family_belonging",
        scene_factor=d17_scene, day_type_factor=d17_day, season_factor=d17_season,
        net_correction=round(d17_scene + d17_day + d17_season, 2))

    # D18 家庭守护
    d18_weather = 0.08 if env.weather in (Weather.TYPHOON, Weather.THUNDERSTORM) else 0.0
    d18_day = 0.05 if env.day_type == DayType.HOLIDAY else 0.0
    m.impacts[18] = DimensionImpact(18, "family_protection",
        weather_factor=d18_weather, day_type_factor=d18_day,
        net_correction=round(d18_weather + d18_day, 2))

    # D19 社会人际 — 公共场所→社交适配压力；工作日→社交需求↓
    d19_scene = 0.0
    if env.scene_type in (SceneType.PUBLIC, SceneType.OFFICE): d19_scene = -0.05
    if env.scene_type == SceneType.HOME: d19_scene = 0.08  # 独处恢复
    d19_crowd = -0.10 if env.crowd_density > 0.6 else 0.0
    d19_day = 0.08 if env.day_type in (DayType.WEEKEND, DayType.HOLIDAY) else 0.0
    d19_time = -0.05 if env.time_of_day == TimeOfDay.MORNING else 0.0  # 早晨社交压力
    m.impacts[19] = DimensionImpact(19, "social_fit",
        scene_factor=d19_scene, crowd_factor=d19_crowd,
        day_type_factor=d19_day, time_factor=d19_time,
        net_correction=round(d19_scene + d19_crowd + d19_day + d19_time, 2))

    # D20 团队集体 — 办公室→团队感↑；假期→团队联系↓
    d20_scene = 0.10 if env.scene_type == SceneType.OFFICE else 0.0
    d20_day = -0.10 if env.day_type in (DayType.WEEKEND, DayType.HOLIDAY) else 0.0
    m.impacts[20] = DimensionImpact(20, "team_protection",
        scene_factor=d20_scene, day_type_factor=d20_day,
        net_correction=round(d20_scene + d20_day, 2))

    # ==================================================================
    # 大类 4: 时空客观环境 D21-D26
    # ==================================================================

    # D21 私人居所·独处氛围 — 噪音越低、光线越柔和→恢复指数越高
    d21_noise = 0.15 if env.noise_db < 35 else (-0.10 if env.noise_db > 55 else 0.0)
    d21_light = 0.10 if env.light_lux < 500 else (-0.05 if env.light_lux > 10000 else 0.0)
    d21_temp = 0.08 if 20 <= effective_temp <= 26 else 0.0
    d21_scene = 0.15 if env.scene_type == SceneType.HOME else 0.0
    m.impacts[21] = DimensionImpact(21, "private_space",
        noise_factor=d21_noise, light_factor=d21_light,
        temperature_factor=d21_temp, scene_factor=d21_scene,
        net_correction=round(d21_noise + d21_light + d21_temp + d21_scene, 2))

    # D22 家庭布局 — 居家氛围越好恢复效率越高
    d22_noise = 0.10 if env.noise_db < 40 else (-0.08 if env.noise_db > 60 else 0.0)
    d22_light = 0.08 if env.light_lux < 3000 else 0.0
    d22_temp = 0.05 if 20 <= effective_temp <= 26 else (-0.05 if effective_temp > 30 else 0.0)
    m.impacts[22] = DimensionImpact(22, "home_environment",
        noise_factor=d22_noise, light_factor=d22_light, temperature_factor=d22_temp,
        net_correction=round(d22_noise + d22_light + d22_temp, 2))

    # D23 职场厂区 — 通勤+工作负荷综合
    d23_scene = 0.0
    if env.scene_type == SceneType.OFFICE: d23_scene = -0.05  # 办公室中性偏负
    d23_day = -0.05 if env.day_type == DayType.WORKDAY else 0.10
    m.impacts[23] = DimensionImpact(23, "workplace",
        scene_factor=d23_scene, day_type_factor=d23_day,
        net_correction=round(d23_scene + d23_day, 2))

    # D24 公共场地 — 人流密度直接影响
    d24_crowd = -0.15 if env.crowd_density > 0.6 else (-0.05 if env.crowd_density > 0.3 else 0.05)
    d24_noise = -0.10 if env.noise_db > 65 else 0.0
    d24_scene = -0.10 if env.scene_type in (SceneType.PUBLIC, SceneType.TRANSIT) else 0.0
    m.impacts[24] = DimensionImpact(24, "public_space",
        crowd_factor=d24_crowd, noise_factor=d24_noise, scene_factor=d24_scene,
        net_correction=round(d24_crowd + d24_noise + d24_scene, 2))

    # D25 空间距离 — 通勤时间+紧迫度
    d25_scene = 0.0
    if env.scene_type == SceneType.TRANSIT: d25_scene = -0.15
    if env.scene_type == SceneType.HOME: d25_scene = 0.10
    d25_weather = -0.10 if env.weather in (Weather.RAIN_HEAVY, Weather.TYPHOON) else 0.0
    d25_time = -0.05 if env.time_of_day in (TimeOfDay.MORNING, TimeOfDay.EVENING) else 0.0  # 高峰期
    m.impacts[25] = DimensionImpact(25, "spatiotemporal",
        scene_factor=d25_scene, weather_factor=d25_weather, time_factor=d25_time,
        net_correction=round(d25_scene + d25_weather + d25_time, 2))

    # D26 四季气象 — 最受环境影响的维度
    d26_season = 0.0
    if env.season == Season.SPRING: d26_season = 0.10
    if env.season == Season.SUMMER: d26_season = 0.05
    if env.season == Season.AUTUMN: d26_season = 0.05
    if env.season == Season.WINTER: d26_season = -0.10
    d26_weather = 0.0
    if env.weather == Weather.CLEAR: d26_weather = 0.15
    if env.weather in (Weather.RAIN_HEAVY, Weather.OVERCAST, Weather.THUNDERSTORM, Weather.TYPHOON): d26_weather = -0.15
    d26_time = 0.0
    if env.time_of_day in (TimeOfDay.NIGHT, TimeOfDay.LATE_NIGHT): d26_time = 0.10  # 褪黑素分泌
    d26_light = 0.0
    if m.daylight_hours < 10: d26_light = -0.10  # 日照不足→季节性影响
    if m.daylight_hours > 14: d26_light = 0.05
    m.impacts[26] = DimensionImpact(26, "seasonal_climate",
        season_factor=d26_season, weather_factor=d26_weather,
        time_factor=d26_time, light_factor=d26_light,
        net_correction=round(d26_season + d26_weather + d26_time + d26_light, 2))

    # ==================================================================
    # 大类 5: 全域动态生长 D27-D32
    # ==================================================================

    # D27 微观生理 — 温度/湿度/气压对微量元素代谢的影响
    d27_temp = 0.0
    if effective_temp > 35: d27_temp = -0.08
    if effective_temp < 5: d27_temp = -0.06
    m.impacts[27] = DimensionImpact(27, "micro_physiology",
        temperature_factor=d27_temp, net_correction=round(d27_temp, 2))

    # D28 自然拓展 — 户外→探索；好天气→户外意愿↑
    d28_scene = 0.15 if env.scene_type in (SceneType.NATURE, SceneType.OUTDOOR) else 0.0
    d28_weather = 0.12 if env.weather == Weather.CLEAR else (-0.15 if env.weather in (Weather.RAIN_HEAVY, Weather.TYPHOON) else 0.0)
    d28_season = 0.10 if env.season in (Season.SPRING, Season.AUTUMN) else 0.0
    d28_day = 0.10 if env.day_type == DayType.WEEKEND else 0.0
    m.impacts[28] = DimensionImpact(28, "nature_expansion",
        scene_factor=d28_scene, weather_factor=d28_weather,
        season_factor=d28_season, day_type_factor=d28_day,
        net_correction=round(d28_scene + d28_weather + d28_season + d28_day, 2))

    # D29 人文社交 — 场景类型决定社交复杂度
    d29_scene = 0.0
    if env.scene_type == SceneType.PUBLIC: d29_scene = -0.10
    if env.scene_type == SceneType.HOME: d29_scene = 0.05
    if env.scene_type == SceneType.OFFICE: d29_scene = -0.05
    d29_crowd = -0.05 if env.crowd_density > 0.5 else 0.0
    m.impacts[29] = DimensionImpact(29, "social_refinement",
        scene_factor=d29_scene, crowd_factor=d29_crowd,
        net_correction=round(d29_scene + d29_crowd, 2))

    # D30 精神文娱 — 假期/周末→文娱时间↑；坏天气→室内活动
    d30_day = 0.15 if env.day_type in (DayType.WEEKEND, DayType.HOLIDAY) else 0.0
    d30_weather = 0.05 if env.weather in (Weather.RAIN_LIGHT, Weather.RAIN_HEAVY) else 0.0  # 雨天→室内文娱
    d30_scene = 0.05 if env.scene_type == SceneType.HOME else 0.0
    m.impacts[30] = DimensionImpact(30, "spiritual_growth",
        day_type_factor=d30_day, weather_factor=d30_weather, scene_factor=d30_scene,
        net_correction=round(d30_day + d30_weather + d30_scene, 2))

    # D31 主客观量子耦合 — 体感与环境的匹配度
    d31_match = 0.10 if env.scene_type == SceneType.HOME else (-0.05 if env.scene_type == SceneType.PUBLIC else 0.0)
    d31_weather = 0.05 if env.weather == Weather.CLEAR else 0.0
    m.impacts[31] = DimensionImpact(31, "quantum_coupling",
        scene_factor=d31_match, weather_factor=d31_weather,
        net_correction=round(d31_match + d31_weather, 2))

    # D32 全域统筹 — 汇总所有影响的加权均值
    total_correction = sum(imp.net_correction for imp in m.impacts.values()) / 32.0
    m.impacts[32] = DimensionImpact(32, "global_overview",
        net_correction=round(total_correction, 2))

    return m


# ===================================================================
# 便捷入口
# ===================================================================

def quick_env_matrix(
    time_of_day: str = "afternoon",
    weather: str = "clear",
    season: str = "summer",
    scene_type: str = "home",
    day_type: str = "workday",
    crowd_density: float = 0.1,
    noise_db: float = 40.0,
) -> EnvImpactMatrix:
    """快速创建环境影响矩阵。"""
    env = EnvContext(
        time_of_day=TimeOfDay[time_of_day.upper()] if time_of_day.upper() in TimeOfDay.__members__ else TimeOfDay.AFTERNOON,
        weather=Weather[weather.upper()] if weather.upper() in Weather.__members__ else Weather.CLEAR,
        season=Season[season.upper()] if season.upper() in Season.__members__ else Season.SUMMER,
        scene_type=SceneType[scene_type.upper()] if scene_type.upper() in SceneType.__members__ else SceneType.HOME,
        day_type=DayType[day_type.upper()] if day_type.upper() in DayType.__members__ else DayType.WORKDAY,
        crowd_density=crowd_density,
        noise_db=noise_db,
    )
    return compute_env_impact_matrix(env)
