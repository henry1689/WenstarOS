"""D17 家庭归属·陪伴 — 客观安全感基线"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D17_CONFIG = ObjDimConfig(dim_id=17, dim_key="family_belonging", category=ObjCategory.SOCIAL_BONDS,
    label_cn="D17 家庭归属·陪伴", medical_metric_name="安全感分值", medical_baseline=35.0,
    medical_unit="分", standard_range=(25, 45), sibling_dims=[15,16,18,19,20])

class D17FamilyBelongingObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D17_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        score = 35.0
        if "family" in interpersonal: score += 5
        return self.make_result(round(score, 1))
