"""D7 躯体自愈·修复 — 客观标准乳酸清除速率 (年龄/性别差异化)"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D7_CONFIG = ObjDimConfig(
    dim_id=7, dim_key="self_heal", category=ObjCategory.PHYSICAL_BODY,
    label_cn="D7 躯体自愈·修复维度", medical_metric_name="乳酸清除速率", medical_baseline=1.2,
    medical_unit="mmol/h", standard_range=(0.8, 1.5), sibling_dims=[1,2,3,4,5,6,8],
)

class D7RecoveryObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D7_CONFIG)

    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        sleep_h = duration.get("sleep_hours", 7)
        current_lactate = duration.get("lactate_mmol_l", 1.0)
        avatar = duration.get("__avatar__")
        clearance = 1.2

        # 睡眠修正
        clearance -= max(0, 7.5 - sleep_h) * 0.15
        # 乳酸堆积→清除系统激活
        if current_lactate > 1.5: clearance += 0.15
        if current_lactate > 2.0: clearance += 0.10

        if avatar is not None:
            ag = avatar.get("age_group", "mature")
            # 儿童清除最快, 中年最慢
            age_mult = {"child": 1.25, "early_adolescent": 1.15, "late_adolescent": 1.10,
                        "young_adult": 1.05, "mature": 1.0, "middle_age": 0.75}
            clearance *= age_mult.get(ag, 1.0)

        clearance = round(self.clamp(clearance, 0.3, 2.5), 2)
        return self.make_result(clearance, current_lactate=current_lactate, sleep_hours=sleep_h)
