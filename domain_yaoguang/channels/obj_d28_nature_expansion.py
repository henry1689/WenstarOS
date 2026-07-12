"""D28 自然世界拓展感知 — 客观探索多巴胺基线（定期新场景=充足）"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D28_CONFIG = ObjDimConfig(dim_id=28, dim_key="nature_expansion", category=ObjCategory.DYNAMIC_GROWTH,
    label_cn="D28 自然世界拓展感知", medical_metric_name="探索多巴胺下降率", medical_baseline=0.0,
    medical_unit="%下降", standard_range=(0, 20), sibling_dims=[27,29,30,31,32])

class D28NatureExpansionObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D28_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        return self.make_result(0.0)  # 定期新场景→多巴胺基线充足
