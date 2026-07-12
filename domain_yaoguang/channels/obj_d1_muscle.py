"""D1 骨骼肌肉·体能负荷 — 客观标准基线"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D1_CONFIG = ObjDimConfig(
    dim_id=1, dim_key="muscle_load", category=ObjCategory.PHYSICAL_BODY,
    label_cn="D1 骨骼肌肉·体能负荷", medical_metric_name="血乳酸", medical_baseline=1.0,
    medical_unit="mmol/L", standard_range=(0.5, 1.6), sibling_dims=[2,3,4,5,6,7,8],
)

class D1MuscleObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D1_CONFIG)

    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        activity_min = duration.get("activity_minutes", 0)
        time_of_day = temporal.get("time_of_day", "afternoon")
        lactate = 1.0
        if time_of_day in ("evening", "night"): lactate -= 0.10
        if activity_min > 30: lactate += 0.15
        return self.make_result(round(lactate, 2))
