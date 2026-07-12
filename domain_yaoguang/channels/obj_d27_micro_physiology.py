"""D27 人体微观生理细化 — 客观微量内分泌波动基线（平稳=0）"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D27_CONFIG = ObjDimConfig(dim_id=27, dim_key="micro_physiology", category=ObjCategory.DYNAMIC_GROWTH,
    label_cn="D27 人体微观生理细化", medical_metric_name="微量激素波动幅度", medical_baseline=0.0,
    medical_unit="0-1", standard_range=(0, 0.3), sibling_dims=[28,29,30,31,32])

class D27MicroPhysiologyObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D27_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        sleep_h = duration.get("sleep_hours", 7)
        fluct = max(0, (7 - sleep_h) * 0.05)  # 睡眠不足→微观波动
        return self.make_result(round(min(fluct, 0.5), 2))
