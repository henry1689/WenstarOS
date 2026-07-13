"""D4 内分泌·激素波动 — 客观标准昼夜曲线 (年龄/性别/经验差异化)"""
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
        avatar = duration.get("__avatar__")
        curve = {"morning": 14.0, "noon": 10.0, "afternoon": 8.0, "evening": 5.5, "night": 4.0,
                 "late_night": 3.5, "dawn": 12.0}
        cortisol = curve.get(time_of_day, 8.0)
        dopamine = 120.0
        serotonin = 110.0

        if avatar is not None:
            ag = avatar.get("age_group", "mature")
            sex = avatar.get("biological_sex", "male")
            # 青春期激素波动→皮质醇基线偏高
            if ag in ("early_adolescent", "late_adolescent"):
                cortisol += 1.5
                dopamine += 10  # 青春期多巴胺系统活跃
            # 中年性激素下降→皮质醇代偿↑
            if ag == "middle_age":
                cortisol += 1.0
                dopamine -= 10
            # 女性周期波动
            if sex == "female":
                cortisol += 0.5
                serotonin -= 5
            # 儿童=低皮质醇基线
            if ag == "child":
                cortisol -= 2.0
                dopamine += 15  # 儿童天生高多巴胺
            # 经验修正: naive→高皮质醇
            exp = avatar.get("experience", {})
            sexual_exp = exp.get("sexual", {}).get("level", "experienced")
            if sexual_exp == "naive":
                cortisol += 2.0
                dopamine += 15  # 新奇高多巴胺
            elif sexual_exp == "habituated":
                cortisol -= 1.0

        # 环境修正
        cortisol += duration.get("d4_time_factor", 0.0) * 10
        return self.make_result(round(max(2, min(cortisol, 30)), 1),
            dopamine=round(max(30, min(dopamine, 200)), 1),
            serotonin=round(max(20, min(serotonin, 180)), 1))
