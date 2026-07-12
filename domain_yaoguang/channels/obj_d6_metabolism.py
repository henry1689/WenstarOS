"""D6 生理周期·代谢 — 客观标准 BMR + 28天周期"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D6_CONFIG = ObjDimConfig(
    dim_id=6, dim_key="metabolic_cycle", category=ObjCategory.PHYSICAL_BODY,
    label_cn="D6 生理周期·代谢生命周期", medical_metric_name="BMR基础代谢率", medical_baseline=0.0,
    medical_unit="%偏移", standard_range=(-10, 10), sibling_dims=[1,2,3,4,5,7,8],
)

class D6MetabolismObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D6_CONFIG)

    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        sleep_h = duration.get("sleep_hours", 7)
        bmr_shift = max(-15, (7 - sleep_h) * 2)  # 睡眠不足→代谢微降
        return self.make_result(round(bmr_shift, 1), cycle_day=14, cycle_phase="稳定期")
