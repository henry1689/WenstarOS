"""D16 伴侣专属守护 — 客观牵挂基线（平稳）"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D16_CONFIG = ObjDimConfig(dim_id=16, dim_key="partner_protection", category=ObjCategory.SOCIAL_BONDS,
    label_cn="D16 伴侣专属守护意识", medical_metric_name="牵挂焦虑皮质醇", medical_baseline=14.0,
    medical_unit="μg/dL", standard_range=(5, 25), sibling_dims=[15,17,18,19,20])

class D16PartnerProtectionObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D16_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        cortisol = 14.0
        if "partner" in interpersonal: cortisol += 2  # 有伴侣时有轻度牵挂
        return self.make_result(round(cortisol, 1))
