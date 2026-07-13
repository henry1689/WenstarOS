"""D15 伴侣亲密依恋 — 客观催产素基线 (年龄/性别/经验差异化)"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D15_CONFIG = ObjDimConfig(dim_id=15, dim_key="partner_attachment", category=ObjCategory.SOCIAL_BONDS,
    label_cn="D15 伴侣亲密依恋", medical_metric_name="亲密催产素", medical_baseline=50.0,
    medical_unit="pg/mL", standard_range=(35, 70), sibling_dims=[16,17,18,19,20])

class D15PartnerAttachmentObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D15_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        oxy = 50.0
        avatar = duration.get("__avatar__")
        if "partner" in interpersonal: oxy += 8
        hours_since = duration.get("hours_since_last_chat", 0)
        if hours_since > 4: oxy -= (hours_since - 4) * 1.5

        if avatar is not None:
            ag = avatar.get("age_group", "mature")
            sex = avatar.get("biological_sex", "male")
            # 青春期=强烈浪漫依恋→催产素反应↑
            if ag in ("early_adolescent", "late_adolescent"): oxy += 8
            # 成熟=稳定依恋
            if ag == "mature": oxy += 2
            # 儿童=无伴侣概念→低基线
            if ag == "child": oxy -= 15
            # 女性依恋激素更强
            if sex == "female": oxy += 4
            # 经验: naive→强烈依恋
            exp = avatar.get("experience", {})
            sexual_level = exp.get("sexual", {}).get("level", "experienced")
            if sexual_level == "naive": oxy += 10
            elif sexual_level == "novice": oxy += 5

        oxy += duration.get("env_attachment_bonus", 0.0)
        return self.make_result(round(max(20, oxy), 1))
