"""D15 伴侣亲密依恋 — 客观催产素基线"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D15_CONFIG = ObjDimConfig(dim_id=15, dim_key="partner_attachment", category=ObjCategory.SOCIAL_BONDS,
    label_cn="D15 伴侣亲密依恋", medical_metric_name="亲密催产素", medical_baseline=50.0,
    medical_unit="pg/mL", standard_range=(35, 70), sibling_dims=[16,17,18,19,20])

class D15PartnerAttachmentObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D15_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        oxy = 50.0
        if "partner" in interpersonal: oxy += 8
        hours_since = duration.get("hours_since_last_chat", 0)
        if hours_since > 4: oxy -= (hours_since - 4) * 1.5  # 分离→客观催产素需求上升（标准值下降表示需要补充）
        return self.make_result(round(max(20, oxy), 1))
