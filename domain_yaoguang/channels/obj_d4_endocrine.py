"""D4 内分泌·激素波动 — 客观标准昼夜曲线"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D4_CONFIG = ObjDimConfig(
    dim_id=4, dim_key="endocrine_hormones", category=ObjCategory.PHYSICAL_BODY,
    label_cn="D4 内分泌·激素波动", medical_metric_name="晨间皮质醇", medical_baseline=14.0,
    medical_unit="μg/dL", standard_range=(5, 25), sibling_dims=[1,2,3,5,6,7,8],
)

class D4EndocrineObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D4_CONFIG)

    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        time_of_day = temporal.get("time_of_day", "afternoon")
        # 标准昼夜皮质醇曲线: 晨14 → 午8 → 晚5
        curve = {"morning": 14.0, "noon": 10.0, "afternoon": 8.0, "evening": 5.5, "night": 4.0}
        cortisol = curve.get(time_of_day, 8.0)
        dopamine = 120.0  # pg/mL, 稳定基线
        serotonin = 110.0  # ng/mL, 稳定基线
        return self.make_result(round(cortisol, 1),
            dopamine=dopamine, serotonin=serotonin)
