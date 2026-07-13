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
        hours_since_chat = s.duration_context.get("hours_since_last_chat", 0)
        work_duration = s.duration_context.get("work_duration_hours", 0)

        CONFIDENT = ["自信","不错","挺好","清楚","明白","有进步","成长","做到了","成功",
                     "认可","称赞","肯定","鼓励","相信","我行","我可以","有能力"]
        DOUBT = ["迷茫","不行","没用","自卑","不确定","怀疑自己","我不行","我不好","不够好",
                 "失败","做不好","不如","比不上","差劲","自责","怪自己"]

        conf_hits = sum(1 for kw in CONFIDENT if kw in s.raw_input_text)
        doubt_hits = sum(1 for kw in DOUBT if kw in s.raw_input_text)

        esteem = 32.0
        esteem += conf_hits * 2.5 - doubt_hits * 3.5
        esteem += (2 if has_partner else 0) + (1.5 if has_family else 0)
        esteem -= (2.5 if has_stranger else 0)
        esteem -= max(0, hours_since_chat - 8) * 0.4
        esteem -= max(0, work_duration - 10) * 0.3  # 长期过劳侵蚀自我认同
        esteem = round(max(10.0, min(esteem, 45.0)), 1)
        stability = round(max(0.0, 1.0 - abs(esteem - 32) / 20), 2)

        return OrganState(
            organ_name="自我身份确认/存在感中枢",
            metrics={"esteem_score": esteem, "stability": stability,
                     "confident_signals": conf_hits, "doubt_signals": doubt_hits},
            activation_level=round(1.0 - esteem / 45, 2),
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        esteem = o.metrics["esteem_score"]
        stability = o.metrics["stability"]
        if esteem >= 32 and stability >= 0.8: return (0.7, Intensity.LOW, "自信安定，自我认知清晰，存在感充足")
        if esteem >= 26: return (0.2, Intensity.MEDIUM, "轻微自我怀疑，基本稳定")
        if esteem >= 22: return (-0.25, Intensity.MEDIUM, "自我认同偏低，迷茫易敏感，需正向肯定")
        if esteem >= 18: return (-0.55, Intensity.HIGH, "深度自我怀疑，持续内耗")
        return (-0.85, Intensity.EXTREME, "严重自卑，无归属感，人格动摇")
