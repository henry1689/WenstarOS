"""D21 私人居所·独处氛围 — 客观独处恢复指数基线"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D21_CONFIG = ObjDimConfig(dim_id=21, dim_key="private_space", category=ObjCategory.SPATIOTEMPORAL,
    label_cn="D21 私人居所·独处氛围", medical_metric_name="独处皮质醇下降幅度", medical_baseline=5.0,
    medical_unit="μg/dL", standard_range=(2, 10), sibling_dims=[22,23,24,25,26])

class D21PrivateSpaceObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D21_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        noise = env.get("noise_db", 40)
        drop = 5.0 - max(0, noise - 45) * 0.1  # 安静→更大下降幅度
        return self.make_result(round(max(1, drop), 1))
