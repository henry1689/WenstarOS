"""D26 四季气象·昼夜节律 — 客观褪黑素标准节律"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D26_CONFIG = ObjDimConfig(dim_id=26, dim_key="seasonal_climate", category=ObjCategory.SPATIOTEMPORAL,
    label_cn="D26 四季气象·昼夜节律", medical_metric_name="褪黑素分泌量", medical_baseline=30.0,
    medical_unit="pg/mL", standard_range=(15, 50), sibling_dims=[21,22,23,24,25])

class D26SeasonalObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D26_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        time_of_day = temporal.get("time_of_day", "afternoon")
        # 褪黑素: 白天低 夜间高
        curve = {"morning": 10, "noon": 8, "afternoon": 12, "evening": 30, "night": 50}
        melatonin = curve.get(time_of_day, 20)
        season = temporal.get("season", "summer")
        if season == "winter": melatonin += 5  # 冬季日照短，褪黑素略高
        return self.make_result(round(melatonin, 1))
