"""D16 伴侣专属守护意识维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D16_CONFIG = DimConfig(
    dim_id=16, dim_key="partner_protection", category=ChannelCategory.SOCIAL_BONDS, quadrant="伴侣守护",
    label_cn="D16 伴侣专属守护意识", medical_metric_name="牵挂焦虑皮质醇", medical_baseline=14.0, medical_unit="μg/dL",
    sibling_dims=[15,17,18,19,20], danger_threshold_upper=25.0, risk_threshold_upper=22.0,
)

class D16PartnerProtectionChannel(BaseChannel):
    def __init__(self): super().__init__(D16_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        has_partner = "partner" in s.interpersonal_labels
        distress_hits = sum(1 for kw in ["低落","辛苦","委屈","脆弱","受伤","难过","累","压力","不开心","担心你","心疼","保护","守护","照顾","呵护"] if kw in s.raw_input_text)
        cortisol = 14.0
        protection_desire = 0.0
        if has_partner or distress_hits > 0:
            cortisol += distress_hits * 2.5
            protection_desire = 0.3 + distress_hits * 0.12
        cortisol = round(max(10.0, min(cortisol, 30.0)), 1)
        protection_desire = round(min(protection_desire, 1.0), 2)
        return OrganState(organ_name="关怀神经递质/守护本能中枢", metrics={"cortisol": cortisol, "protection_desire": protection_desire, "concern_level": round(cortisol/30, 2)}, activation_level=round(cortisol/30, 2))

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        pd_val = o.metrics["protection_desire"]
        cortisol = o.metrics["cortisol"]
        if pd_val <= 0.2: return (0.5, Intensity.LOW, "守护意识平稳,无过度牵挂")
        if pd_val <= 0.4: return (0.1, Intensity.MEDIUM, "略担心伴侣,责任感温柔上涨")
        if pd_val <= 0.6: return (-0.25, Intensity.MEDIUM, "因伴侣状态牵挂焦虑,皮质醇升高")
        if pd_val <= 0.8: return (-0.55, Intensity.HIGH, "持续重度担忧,心疼难忍")
        return (-0.8, Intensity.EXTREME, "过度牵挂内耗,无能为力感强烈")
