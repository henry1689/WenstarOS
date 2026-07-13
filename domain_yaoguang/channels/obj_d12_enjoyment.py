"""D12 享受·松弛·幸福感 — 客观催产素基线 (年龄/性别/经验差异化)"""
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
        oxytocin += duration.get("env_oxytocin_bonus", 0.0)
        season = temporal.get("season", "summer")
        if season in ("spring", "autumn"): oxytocin += 3
        if season == "winter": oxytocin -= 3
        oxytocin -= max(0, env.get("noise_db", 40) - 60) * 0.2

        avatar = duration.get("__avatar__")
        if avatar is not None:
            ag = avatar.get("age_group", "mature")
            sex = avatar.get("biological_sex", "female" if avatar.get("biological_sex") == "female" else "male")
            # 儿童纯真→高基线
            if ag == "child": oxytocin += 5
            # 青春期情绪起伏→基线略低
            if ag in ("early_adolescent", "late_adolescent"): oxytocin -= 3
            # 中年后U型回升
            if ag == "middle_age": oxytocin += 3
            # 女性催产素基线略高
            if sex == "female": oxytocin += 3
            # 经验: naive新奇→高
            exp = avatar.get("experience", {})
            if exp.get("sexual", {}).get("level") in ("naive", "novice"):
                oxytocin += 5  # 新奇幸福

        return self.make_result(round(self.clamp(oxytocin, 20, 75), 1))
