"""D2 躯体疼痛·不适感知 — 客观标准基线（无伤害事件时默认 VAS=0）"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D2_CONFIG = ObjDimConfig(
    dim_id=2, dim_key="pain_level", category=ObjCategory.PHYSICAL_BODY,
    label_cn="D2 躯体疼痛·不适感知", medical_metric_name="VAS疼痛评分", medical_baseline=0,
    medical_unit="分(0-10)", standard_range=(0, 2), sibling_dims=[1,3,4,5,6,7,8],
)

class D2PainObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D2_CONFIG)

    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        return self.make_result(0.0)  # 无外部伤害事件时标准 VAS=0
