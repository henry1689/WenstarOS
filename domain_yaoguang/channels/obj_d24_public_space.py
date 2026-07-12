"""D24 公共场地·人流氛围 — 客观交感神经基线（低人流=35%）"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D24_CONFIG = ObjDimConfig(dim_id=24, dim_key="public_space", category=ObjCategory.SPATIOTEMPORAL,
    label_cn="D24 公共场地·人流氛围", medical_metric_name="嘈杂环境交感兴奋度", medical_baseline=35.0,
    medical_unit="%", standard_range=(25, 55), sibling_dims=[21,22,23,25,26])

class D24PublicSpaceObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D24_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        crowd = env.get("crowd_density", 0)
        noise = env.get("noise_db", 40)
        sns = 35.0 + crowd * 20 + max(0, noise - 50) * 0.6
        return self.make_result(round(self.clamp(sns, 25, 85), 1), crowd_density=crowd)
