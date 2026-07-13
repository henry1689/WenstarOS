"""D1 骨骼肌肉·体能负荷 — 客观标准基线（接入活动模型乳酸值）"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D1_CONFIG = ObjDimConfig(
    dim_id=1, dim_key="muscle_load", category=ObjCategory.PHYSICAL_BODY,
    label_cn="D1 骨骼肌肉·体能负荷", medical_metric_name="血乳酸", medical_baseline=1.0,
    medical_unit="mmol/L", standard_range=(0.5, 1.6), sibling_dims=[2,3,4,5,6,7,8],
)

class D1MuscleObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D1_CONFIG)

    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        # 优先从 duration 中取活动模型计算好的乳酸值
        lactate = duration.get("lactate_mmol_l", 0)
        if lactate <= 0:
            # fallback: 简单估算
            activity_min = duration.get("activity_minutes", 0)
            sitting_h = duration.get("hours_sitting", duration.get("work_duration_hours", 0))
            time_of_day = temporal.get("time_of_day", "afternoon")
            lactate = 1.0 + sitting_h * 0.04 + activity_min * 0.003
            if time_of_day in ("evening", "night"): lactate -= 0.10

        muscle_reserve = duration.get("muscle_reserve_pct", 60.0)
        fatigue_index = duration.get("fatigue_composite", 0.0)

        return self.make_result(round(self.clamp(lactate, 0.3, 4.0), 2),
            muscle_reserve_pct=muscle_reserve,
            fatigue_index=round(fatigue_index, 2))
