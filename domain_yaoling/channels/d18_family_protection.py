"""D18 家庭整体守护维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D18_CONFIG = DimConfig(
    dim_id=18, dim_key="family_protection", category=ChannelCategory.SOCIAL_BONDS, quadrant="家庭守护",
    label_cn="D18 家庭整体守护", medical_metric_name="家庭应激皮质醇", medical_baseline=14.0, medical_unit="μg/dL",
    sibling_dims=[15,16,17,19,20], danger_threshold_upper=25.0, risk_threshold_upper=22.0,
)

class D18FamilyProtectionChannel(BaseChannel):
    def __init__(self): super().__init__(D18_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        has_family = "family" in s.interpersonal_labels
        concern_hits = sum(1 for kw in ["担心","负担","辛苦","压力","风险","安全","照顾","责任","守护","保护","扛","撑"] if kw in s.raw_input_text)
        cortisol = 14.0
        burden = 0.0
        if has_family or concern_hits > 0:
            cortisol += concern_hits * 2.0
            burden = concern_hits * 0.12
        cortisol = round(max(10.0, min(cortisol, 30.0)), 1)
        burden = round(min(burden, 1.0), 2)
        return OrganState(organ_name="家庭责任感/守护本能中枢", metrics={"cortisol": cortisol, "burden_index": burden, "tension": round(cortisol/30, 2)}, activation_level=round(cortisol/30, 2))

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        burden = o.metrics["burden_index"]
        if burden <= 0.2: return (0.5, Intensity.LOW, "家庭安稳无忧,踏实担当")
        if burden <= 0.4: return (0.1, Intensity.MEDIUM, "略牵挂家人,轻度担忧")
        if burden <= 0.6: return (-0.3, Intensity.MEDIUM, "家庭压力偏高,长期牵挂内耗")
        if burden <= 0.8: return (-0.6, Intensity.HIGH, "心事过重,持续焦虑不安")
        return (-0.85, Intensity.EXTREME, "家庭危机感强烈,守护欲透支身心")
