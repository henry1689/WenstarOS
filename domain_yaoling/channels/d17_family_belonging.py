"""D17 家庭归属·陪伴维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D17_CONFIG = DimConfig(
    dim_id=17, dim_key="family_belonging", category=ChannelCategory.SOCIAL_BONDS, quadrant="家庭归属",
    label_cn="D17 家庭归属·陪伴", medical_metric_name="家庭安全感分值", medical_baseline=35.0, medical_unit="分",
    sibling_dims=[15,16,18,19,20], danger_threshold_lower=14.0, risk_threshold_lower=20.0,
)

class D17FamilyBelongingChannel(BaseChannel):
    def __init__(self): super().__init__(D17_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        has_family = "family" in s.interpersonal_labels
        family_hits = sum(1 for kw in ["家","家人","回家","团圆","温暖","亲情","陪伴","在一起","归","归属","安心","踏实"] if kw in s.raw_input_text)
        lonely_hits = sum(1 for kw in ["冷清","孤单","疏离","一个人","不在","离开","远","没有家","漂泊"] if kw in s.raw_input_text)
        hours_since_chat = s.duration_context.get("hours_since_last_chat", 0)
        score = 35.0
        score += family_hits * 4 + (8 if has_family else 0) - lonely_hits * 5
        score -= max(0, hours_since_chat - 6) * 1.0
        score = round(max(5.0, min(score, 50.0)), 1)
        belonging = round(score / 50, 2)
        return OrganState(organ_name="安定血清素/归属感中枢", metrics={"security_score": score, "belonging_index": belonging, "family_present": 1 if has_family else 0}, activation_level=round(1.0 - belonging, 2))

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        bi = o.metrics["belonging_index"]
        if bi >= 0.75: return (0.75, Intensity.LOW, "家庭温暖安稳,归属感充足踏实")
        if bi >= 0.55: return (0.25, Intensity.MEDIUM, "居家基本安稳,偶尔冷清")
        if bi >= 0.35: return (-0.25, Intensity.MEDIUM, "家庭陪伴不足,缺少归属感")
        if bi >= 0.2: return (-0.6, Intensity.HIGH, "居家冷清孤单,疏离感强烈")
        return (-0.85, Intensity.EXTREME, "极度缺乏家庭归属,漂泊无依")
