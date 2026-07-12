"""D9 自我认知·人格基底 — 客观标准自尊基线"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D9_CONFIG = ObjDimConfig(dim_id=9, dim_key="self_identity", category=ObjCategory.INNER_SPIRIT,
    label_cn="D9 自我认知·人格基底", medical_metric_name="自尊评分", medical_baseline=32.0,
    medical_unit="分", standard_range=(22, 40), sibling_dims=[10,11,12,13,14])

class D9SelfIdentityObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D9_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        return self.make_result(32.0)
