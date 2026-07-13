"""D26 四季气象·昼夜节律 — 客观褪黑素标准节律 (含环境+季节+天气修正)"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D26_CONFIG = ObjDimConfig(dim_id=26, dim_key="seasonal_climate", category=ObjCategory.SPATIOTEMPORAL,
    label_cn="D26 四季气象·昼夜节律", medical_metric_name="褪黑素分泌量", medical_baseline=30.0,
    medical_unit="pg/mL", standard_range=(15, 50), sibling_dims=[21,22,23,24,25])

class D26SeasonalObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D26_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        time_of_day = temporal.get("time_of_day", "afternoon")
        curve = {"dawn": 15, "morning": 10, "noon": 8, "afternoon": 12,
                 "evening": 30, "night": 50, "late_night": 55}
        melatonin = curve.get(time_of_day, 20)
        season = temporal.get("season", "summer")
        if season == "winter": melatonin += 5
        # 环境修正: 恶劣天气→昼夜节律紊乱→褪黑素偏离正常曲线
        shift = duration.get("env_seasonal_shift", 0.0)
        melatonin += shift * 15  # 将系数转为褪黑素单位
        # 台风/雷暴→昼夜节律额外偏移
        weather = temporal.get("weather_raw", "") or temporal.get("weather", "")
        if weather in ("typhoon", "thunderstorm"):
            melatonin += 3 if time_of_day in ("night", "late_night") else -2
        return self.make_result(round(self.clamp(melatonin, 5, 60), 1),
            seasonal_shift=round(shift, 2))
