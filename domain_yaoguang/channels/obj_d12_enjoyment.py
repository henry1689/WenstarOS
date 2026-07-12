"""D12 享受·松弛·幸福感 — 客观催产素基线 45 pg/mL"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D12_CONFIG = ObjDimConfig(dim_id=12, dim_key="enjoyment", category=ObjCategory.INNER_SPIRIT,
    label_cn="D12 享受·松弛·幸福感", medical_metric_name="催产素", medical_baseline=45.0,
    medical_unit="pg/mL", standard_range=(25, 65), sibling_dims=[9,10,11,13,14])

class D12EnjoymentObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D12_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        oxytocin = 45.0
        if "partner" in interpersonal: oxytocin += 5
        if "family" in interpersonal: oxytocin += 3
        return self.make_result(round(oxytocin, 1))
