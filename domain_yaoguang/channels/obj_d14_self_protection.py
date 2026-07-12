"""D14 个体自我保护 — 客观戒备基线（平稳）"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D14_CONFIG = ObjDimConfig(dim_id=14, dim_key="self_protection", category=ObjCategory.INNER_SPIRIT,
    label_cn="D14 个体自我保护", medical_metric_name="戒备基线等级", medical_baseline=0.2,
    medical_unit="0-1", standard_range=(0.1, 0.5), sibling_dims=[9,10,11,12,13])

class D14SelfProtectionObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D14_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        alert = 0.2
        if "stranger" in interpersonal: alert += 0.2
        noise = env.get("noise_db", 40)
        if noise > 70: alert += 0.15
        return self.make_result(round(min(alert, 1.0), 2))
