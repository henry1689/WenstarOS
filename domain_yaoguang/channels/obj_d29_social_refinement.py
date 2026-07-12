"""D29 人文社交规则细化 — 客观人际适配基线（多圈层=平稳）"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D29_CONFIG = ObjDimConfig(dim_id=29, dim_key="social_refinement", category=ObjCategory.DYNAMIC_GROWTH,
    label_cn="D29 人文社交规则细化", medical_metric_name="包容递质下降率", medical_baseline=0.0,
    medical_unit="%下降", standard_range=(0, 20), sibling_dims=[27,28,30,31,32])

class D29SocialRefinementObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D29_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        decline = 0.0
        if len(interpersonal) == 1: decline += 5  # 单一社交圈→轻度下降
        return self.make_result(round(decline, 1))
