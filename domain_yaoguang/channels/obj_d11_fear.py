"""D11 恐惧·倦怠·制衡心理 — 客观 SAS 焦虑基线 (年龄/性别/经验差异化)"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D11_CONFIG = ObjDimConfig(dim_id=11, dim_key="fear_fatigue", category=ObjCategory.INNER_SPIRIT,
    label_cn="D11 恐惧·倦怠·制衡心理", medical_metric_name="SAS焦虑分值", medical_baseline=30.0,
    medical_unit="分", standard_range=(20, 49), sibling_dims=[9,10,12,13,14])

class D11FearObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D11_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        work_h = duration.get("work_duration_hours", 0)
        avatar = duration.get("__avatar__")
        sas = 30.0 + max(0, work_h - 8) * 1.5

        if avatar is not None:
            ag = avatar.get("age_group", "mature")
            sex = avatar.get("biological_sex", "male")
            # 青春期社交焦虑基线↑
            if ag in ("early_adolescent", "late_adolescent"):
                sas += 5
            # 儿童想象力丰富→夜间恐惧↑
            if ag == "child":
                sas += 3
            # 成熟期最低
            if ag == "mature":
                sas -= 2
            # 女性焦虑基线略高
            if sex == "female":
                sas += 2
            # 经验: naive→高焦虑
            exp = avatar.get("experience", {})
            for domain, info in exp.items():
                if info.get("level") == "naive":
                    sas += 3
                    break

        sas += duration.get("env_sas_penalty", 0.0)
        sas += max(0, env.get("noise_db", 40) - 55) * 0.3
        if env.get("crowd_density", 0) < 0.1:
            sas -= 2
        return self.make_result(round(min(sas, 55), 0))
