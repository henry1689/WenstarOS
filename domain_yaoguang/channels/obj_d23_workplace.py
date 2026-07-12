"""D23 职场厂区·工作环境 — 客观工作负荷耐受标准"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D23_CONFIG = ObjDimConfig(dim_id=23, dim_key="workplace", category=ObjCategory.SPATIOTEMPORAL,
    label_cn="D23 职场厂区·工作环境", medical_metric_name="工作皮质醇", medical_baseline=14.0,
    medical_unit="μg/dL", standard_range=(8, 22), sibling_dims=[21,22,24,25,26])

class D23WorkplaceObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D23_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        work_h = duration.get("work_duration_hours", 0)
        cortisol = 14.0 + max(0, work_h - 6) * 0.8  # 超6h后每h+0.8
        return self.make_result(round(min(cortisol, 25), 1))
