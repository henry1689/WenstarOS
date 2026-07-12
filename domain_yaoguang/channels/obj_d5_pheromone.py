"""D5 信息素·气息氛围 — 客观中性基线"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D5_CONFIG = ObjDimConfig(
    dim_id=5, dim_key="pheromone", category=ObjCategory.PHYSICAL_BODY,
    label_cn="D5 信息素·气息氛围", medical_metric_name="汗液皮质醇浓度", medical_baseline=0.0,
    medical_unit="低/正常/高", standard_range=(0, 1), sibling_dims=[1,2,3,4,6,7,8],
)

class D5PheromoneObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D5_CONFIG)

    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        return self.make_result(0.0)  # 中性基线——无压力汗液
