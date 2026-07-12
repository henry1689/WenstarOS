"""D20 团队集体保护 — 客观集体应激基线"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D20_CONFIG = ObjDimConfig(dim_id=20, dim_key="team_protection", category=ObjCategory.SOCIAL_BONDS,
    label_cn="D20 团队集体保护", medical_metric_name="集体应激激素", medical_baseline=0.0,
    medical_unit="0-1", standard_range=(0, 0.4), sibling_dims=[15,16,17,18,19])

class D20TeamObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D20_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        return self.make_result(0.0)
