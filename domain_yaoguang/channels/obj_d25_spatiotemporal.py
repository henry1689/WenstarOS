"""D25 空间距离·时差流逝 — 客观时间紧迫度基线"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D25_CONFIG = ObjDimConfig(dim_id=25, dim_key="spatiotemporal", category=ObjCategory.SPATIOTEMPORAL,
    label_cn="D25 空间距离·时差流逝", medical_metric_name="时间紧迫应激皮质醇", medical_baseline=14.0,
    medical_unit="μg/dL", standard_range=(8, 22), sibling_dims=[21,22,23,24,26])

class D25SpatiotemporalObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D25_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        buffer_min = duration.get("buffer_min", 60)
        urgency = max(0, 1 - buffer_min / 120)  # 缓冲时间越少越紧迫
        cortisol = 14.0 + urgency * 6
        return self.make_result(round(min(cortisol, 24), 1), urgency=round(urgency, 2))
