"""D19 社会人际·社交适配 — 客观社交后皮质醇上升基线（无明显上升=0）"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D19_CONFIG = ObjDimConfig(dim_id=19, dim_key="social_fit", category=ObjCategory.SOCIAL_BONDS,
    label_cn="D19 社会人际·社交适配", medical_metric_name="社交后皮质醇上升值", medical_baseline=0.0,
    medical_unit="μg/dL", standard_range=(0, 8), sibling_dims=[15,16,17,18,20])

class D19SocialObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D19_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        rise = 0.0
        if "stranger" in interpersonal: rise += 3
        crowd = env.get("crowd_density", 0)
        if crowd > 0.6: rise += 2
        return self.make_result(round(rise, 1))
