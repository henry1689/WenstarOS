"""D32 全域统筹总控汇总 — 客观核心生命体征标准"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D32_CONFIG = ObjDimConfig(dim_id=32, dim_key="global_overview", category=ObjCategory.DYNAMIC_GROWTH,
    label_cn="D32 全域统筹总控汇总", medical_metric_name="综合健康指数", medical_baseline=75.0,
    medical_unit="分", standard_range=(60, 90), sibling_dims=[27,28,29,30,31])

class D32HolisticObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D32_CONFIG)

    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        time_of_day = temporal.get("time_of_day", "afternoon")
        # 昼夜心率标准
        hr_curve = {"morning": 66, "noon": 68, "afternoon": 70, "evening": 65, "night": 60}
        heart_rate = hr_curve.get(time_of_day, 66)
        bp_sys = 115  # mmHg 标准
        bp_dia = 73
        cortisol_curve = {"morning": 14, "noon": 10, "afternoon": 8, "evening": 5.5, "night": 4}
        cortisol = cortisol_curve.get(time_of_day, 8)
        return self.make_result(75.0,
            heart_rate=round(heart_rate, 0),
            blood_pressure_sys=bp_sys,
            blood_pressure_dia=bp_dia,
            cortisol_daily_avg=round(cortisol, 1),
            joy_hormone_avg=115.0,
        )
