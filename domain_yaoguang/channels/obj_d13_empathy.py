"""D13 共情·恻隐联动 — 客观镜像神经元激活基线（适中，不内耗）"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D13_CONFIG = ObjDimConfig(dim_id=13, dim_key="empathy", category=ObjCategory.INNER_SPIRIT,
    label_cn="D13 共情·恻隐联动", medical_metric_name="镜像神经元激活强度", medical_baseline=0.4,
    medical_unit="0-1", standard_range=(0.2, 0.6), sibling_dims=[9,10,11,12,14])

class D13EmpathyObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D13_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        return self.make_result(0.4)  # 适中基线
