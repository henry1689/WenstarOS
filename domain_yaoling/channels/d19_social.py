"""D19 社会人际·社交适配维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D19_CONFIG = DimConfig(
    dim_id=19, dim_key="social_adaptation", category=ChannelCategory.SOCIAL_BONDS, quadrant="社交适配",
    label_cn="D19 社会人际·社交适配", medical_metric_name="社交后皮质醇升幅", medical_baseline=0.0, medical_unit="μg/dL Δ",
    sibling_dims=[15,16,17,18,20], danger_threshold_upper=8.0, risk_threshold_upper=6.0,
)

class D19SocialChannel(BaseChannel):
    def __init__(self): super().__init__(D19_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        has_colleague = "colleague" in s.interpersonal_labels
        has_stranger = "stranger" in s.interpersonal_labels
        social_hits = sum(1 for kw in ["同事","朋友","聚会","社交","见面","聊","人情","往来","应酬"] if kw in s.raw_input_text)
        fatigue_hits = sum(1 for kw in ["拘谨","紧张","压力","疲惫","应付","不想","排斥","麻烦"] if kw in s.raw_input_text)
        cortisol_rise = 0.0
        if has_stranger: cortisol_rise += 3.0
        if has_colleague: cortisol_rise += 2.0
        cortisol_rise += social_hits * 0.8 + fatigue_hits * 1.5
        cortisol_rise = round(max(0.0, min(cortisol_rise, 12.0)), 1)
        comfort = round(1.0 - cortisol_rise / 12, 2)
        return OrganState(organ_name="社交应激/适配调节系统", metrics={"cortisol_rise": cortisol_rise, "social_comfort": comfort, "fatigue": round(fatigue_hits * 0.2, 2)}, activation_level=round(cortisol_rise/12, 2))

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        comfort = o.metrics["social_comfort"]
        rise = o.metrics["cortisol_rise"]
        if rise <= 1: return (0.6, Intensity.LOW, "社交从容自然,舒适自在")
        if rise <= 3: return (0.2, Intensity.MEDIUM, "社交后略疲惫,大体舒适")
        if rise <= 6: return (-0.3, Intensity.MEDIUM, "社交负荷偏高,人际往来消耗心神")
        if rise <= 9: return (-0.6, Intensity.HIGH, "社交严重消耗,排斥人际接触")
        return (-0.85, Intensity.EXTREME, "社交后皮质醇飙升,人际恐惧")
