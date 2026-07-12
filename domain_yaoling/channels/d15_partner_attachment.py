"""D15 伴侣亲密依恋维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D15_CONFIG = DimConfig(
    dim_id=15, dim_key="partner_attachment", category=ChannelCategory.SOCIAL_BONDS, quadrant="伴侣亲密",
    label_cn="D15 伴侣亲密依恋", medical_metric_name="亲密催产素", medical_baseline=50.0, medical_unit="pg/mL",
    sibling_dims=[16,17,18,19,20], danger_threshold_lower=18.0, risk_threshold_lower=28.0,
)

class D15PartnerAttachmentChannel(BaseChannel):
    def __init__(self): super().__init__(D15_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        has_partner = "partner" in s.interpersonal_labels
        intimate_hits = sum(1 for kw in ["爱你","想你","抱","亲","陪伴","一起","温暖","甜蜜","心动","幸福","依恋","离不开","需要你","在一起"] if kw in s.raw_input_text)
        lonely_hits = sum(1 for kw in ["孤单","失落","疏离","冷落","分开","一个人","遥远","不在"] if kw in s.raw_input_text)
        hours_since_chat = s.duration_context.get("hours_since_last_chat", 0)
        oxytocin = 50.0
        if has_partner:
            oxytocin += intimate_hits * 5 - lonely_hits * 6
            oxytocin -= max(0, hours_since_chat - 2) * 1.5
        else:
            oxytocin -= 10  # 无伴侣在场时略低
        oxytocin = round(max(8.0, min(oxytocin, 80.0)), 1)
        attachment_strength = round(oxytocin / 80, 2)
        return OrganState(organ_name="亲密激素/依恋神经中枢", metrics={"oxytocin": oxytocin, "attachment_strength": attachment_strength, "partner_present": 1 if has_partner else 0}, activation_level=round(1.0 - attachment_strength, 2))

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        oxy = o.metrics["oxytocin"]
        strength = o.metrics["attachment_strength"]
        if strength >= 0.7: return (0.8, Intensity.LOW, "心动治愈,依恋饱满甜蜜,亲密满足")
        if strength >= 0.5: return (0.3, Intensity.MEDIUM, "依恋基本满足,偶尔思念")
        if strength >= 0.3: return (-0.3, Intensity.HIGH, "孤单失落感明显,缺少亲密安抚")
        if strength >= 0.15: return (-0.6, Intensity.HIGH, "深度情感饥渴,被冷落感强烈")
        return (-0.9, Intensity.EXTREME, "亲密催产素严重不足,深度情感空虚")
