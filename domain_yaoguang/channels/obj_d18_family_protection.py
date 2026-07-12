"""D18 家庭整体守护 — 客观家庭应激皮质醇基线"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D18_CONFIG = ObjDimConfig(dim_id=18, dim_key="family_protection", category=ObjCategory.SOCIAL_BONDS,
    label_cn="D18 家庭整体守护", medical_metric_name="家庭应激皮质醇", medical_baseline=14.0,
    medical_unit="μg/dL", standard_range=(5, 25), sibling_dims=[15,16,17,19,20])

class D18FamilyProtectionObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D18_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        return self.make_result(14.0)
