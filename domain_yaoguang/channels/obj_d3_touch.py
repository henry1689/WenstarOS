"""D3 神经瞬时刺激·触觉 — 客观标准基线（标准放松态 35%）"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D3_CONFIG = ObjDimConfig(
    dim_id=3, dim_key="nerve_arousal", category=ObjCategory.PHYSICAL_BODY,
    label_cn="D3 神经瞬时刺激·触觉", medical_metric_name="交感神经兴奋度", medical_baseline=35.0,
    medical_unit="%", standard_range=(25, 55), sibling_dims=[1,2,4,5,6,7,8],
)

class D3TouchObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D3_CONFIG)

    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        noise = env.get("noise_db", 40)
        light = env.get("light_lux", 300)
        temp = env.get("temperature", 22)
        sns = 35.0
        if noise > 60: sns += (noise - 60) * 0.5
        if light > 5000: sns += 5
        if temp > 32 or temp < 10: sns += 8
        return self.make_result(round(self.clamp(sns, 20, 90), 1))
