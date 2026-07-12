"""D11 恐惧·倦怠·制衡心理 — 客观 SAS 焦虑量表基线 <30"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D11_CONFIG = ObjDimConfig(dim_id=11, dim_key="fear_fatigue", category=ObjCategory.INNER_SPIRIT,
    label_cn="D11 恐惧·倦怠·制衡心理", medical_metric_name="SAS焦虑分值", medical_baseline=30.0,
    medical_unit="分", standard_range=(20, 49), sibling_dims=[9,10,12,13,14])

class D11FearObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D11_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        work_h = duration.get("work_duration_hours", 0)
        sas = 30.0 + max(0, work_h - 8) * 1.5  # 超时工作→客观应激升高
        return self.make_result(round(min(sas, 50), 0))
