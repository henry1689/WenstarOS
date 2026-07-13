"""D2 躯体疼痛·不适感知 — 客观标准基线 (年龄/性别/经验差异化)"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D2_CONFIG = ObjDimConfig(
    dim_id=2, dim_key="pain_level", category=ObjCategory.PHYSICAL_BODY,
    label_cn="D2 躯体疼痛·不适感知", medical_metric_name="VAS疼痛评分", medical_baseline=0,
    medical_unit="分(0-10)", standard_range=(0, 2), sibling_dims=[1,3,4,5,6,7,8],
)

class D2PainObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D2_CONFIG)

    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        avatar = duration.get("__avatar__")
        vas = 0.0

        if avatar is not None:
            ag = avatar.get("age_group", "mature")
            sex = avatar.get("biological_sex", "male")
            # 慢性疼痛基线: 中年后>0
            if ag in ("middle_age",): vas += 0.3
            # 女性略低痛阈 → 同等刺激下VAS偏高
            if sex == "female": vas += 0.1
            # 儿童痛阈更低
            if ag in ("child", "early_adolescent"): vas += 0.2

        # 有外部伤害事件时从 duration 读取
        injury = duration.get("pain_event_vas", 0)
        vas += injury

        return self.make_result(round(min(vas, 10.0), 1),
            age_group=avatar.get("age_group") if avatar else None,
            sex=avatar.get("biological_sex") if avatar else None)
