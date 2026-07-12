"""D22 家庭布局·共处氛围 — 客观居家情绪恢复效率基线 80%"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D22_CONFIG = ObjDimConfig(dim_id=22, dim_key="home_environment", category=ObjCategory.SPATIOTEMPORAL,
    label_cn="D22 家庭布局·共处氛围", medical_metric_name="居家情绪恢复效率", medical_baseline=80.0,
    medical_unit="%", standard_range=(60, 95), sibling_dims=[21,23,24,25,26])

class D22HomeEnvironmentObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D22_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        eff = 80.0
        light = env.get("light_lux", 300)
        noise = env.get("noise_db", 40)
        if light < 100: eff -= 10  # 昏暗→恢复效率降
        if noise > 55: eff -= 8
        if "family" in interpersonal: eff += 5
        return self.make_result(round(self.clamp(eff, 30, 100), 1))
