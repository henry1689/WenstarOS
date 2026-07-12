"""D30 精神文娱·修养成长 — 客观血清素基线（充足=0%下降）"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D30_CONFIG = ObjDimConfig(dim_id=30, dim_key="spiritual_growth", category=ObjCategory.DYNAMIC_GROWTH,
    label_cn="D30 精神文娱·修养成长", medical_metric_name="精神愉悦血清素下降率", medical_baseline=0.0,
    medical_unit="%下降", standard_range=(0, 25), sibling_dims=[27,28,29,31,32])

class D30SpiritualGrowthObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D30_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        return self.make_result(0.0)  # 文娱/学习资源充足时基线=0
