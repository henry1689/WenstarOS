"""D7 躯体自愈·修复 — 客观标准乳酸清除速率 1.2 mmol/h"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D7_CONFIG = ObjDimConfig(
    dim_id=7, dim_key="self_heal", category=ObjCategory.PHYSICAL_BODY,
    label_cn="D7 躯体自愈·修复维度", medical_metric_name="乳酸清除速率", medical_baseline=1.2,
    medical_unit="mmol/h", standard_range=(0.8, 1.5), sibling_dims=[1,2,3,4,5,6,8],
)

class D7RecoveryObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D7_CONFIG)

    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        sleep_h = duration.get("sleep_hours", 7)
        rate = 1.2 + max(0, sleep_h - 6) * 0.05  # 充足睡眠→修复加速
        return self.make_result(round(rate, 2))
