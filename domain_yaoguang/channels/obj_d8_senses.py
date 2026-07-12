"""D8 五感环境·基础体感 — 客观环境参数标准"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D8_CONFIG = ObjDimConfig(
    dim_id=8, dim_key="sensory_env", category=ObjCategory.PHYSICAL_BODY,
    label_cn="D8 五感环境·基础体感", medical_metric_name="环境噪音", medical_baseline=40.0,
    medical_unit="dB", standard_range=(25, 60), sibling_dims=[1,2,3,4,5,6,7],
)

class D8SensesObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D8_CONFIG)

    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        return self.make_result(
            env.get("noise_db", 40),
            temperature=env.get("temperature", 22),
            light_lux=env.get("light_lux", 300),
        )
