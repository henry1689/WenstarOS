"""D9 自我认知·人格基底维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D9_CONFIG = DimConfig(
    dim_id=9, dim_key="self_identity", category=ChannelCategory.INNER_SPIRIT, quadrant="自我内核",
    label_cn="D9 自我认知·人格基底", medical_metric_name="自尊评分", medical_baseline=32.0, medical_unit="分",
    sibling_dims=[10,11,12,13,14], danger_threshold_lower=20.0, risk_threshold_lower=22.0,
)

class D9SelfIdentityChannel(BaseChannel):
    def __init__(self): super().__init__(D9_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        has_partner = "partner" in s.interpersonal_labels
        has_family = "family" in s.interpersonal_labels
        has_stranger = "stranger" in s.interpersonal_labels
        positive_self = sum(1 for kw in ["自信","可以","我能","不错","挺好","清楚","明白","有进步"] if kw in s.raw_input_text)
        negative_self = sum(1 for kw in ["迷茫","不行","差","没用","不知道","怀疑","自卑","不确定"] if kw in s.raw_input_text)
        hours_since_chat = s.duration_context.get("hours_since_last_chat", 0)
        esteem = 32.0
        esteem += positive_self * 3 - negative_self * 4
        esteem += 2 if has_partner else 0
        esteem += 1.5 if has_family else 0
        esteem -= hours_since_chat * 0.5 if hours_since_chat > 8 else 0
        esteem -= 3 if has_stranger else 0
        esteem = round(max(10.0, min(esteem, 45.0)), 1)
        stability = round(1.0 - abs(esteem - 32) / 20, 2)
        return OrganState(organ_name="自我身份确认/存在感中枢", metrics={"esteem_score": esteem, "stability": max(0.0, stability)}, activation_level=round(1.0 - esteem/45, 2))

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        esteem = o.metrics["esteem_score"]
        stability = o.metrics["stability"]
        if esteem >= 30 and stability >= 0.8: return (0.7, Intensity.LOW, "自信安定,自我认知清晰,存在感充足")
        if esteem >= 25: return (0.2, Intensity.MEDIUM, "轻微自我怀疑,基本稳定")
        if esteem >= 20: return (-0.35, Intensity.HIGH, "自我认同偏低,迷茫易敏感")
        if esteem >= 15: return (-0.65, Intensity.HIGH, "深度自我怀疑,持续内耗")
        return (-0.9, Intensity.EXTREME, "严重自卑,无归属感,人格动摇")
