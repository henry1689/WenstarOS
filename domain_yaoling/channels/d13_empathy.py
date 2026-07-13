"""D13 共情·恻隐联动维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D13_CONFIG = DimConfig(
    dim_id=13, dim_key="empathy_resonance", category=ChannelCategory.INNER_SPIRIT, quadrant="共情恻隐",
    label_cn="D13 共情·恻隐联动", medical_metric_name="镜像神经元激活强度", medical_baseline=0.4, medical_unit="相对值",
    sibling_dims=[9,10,11,12,14], danger_threshold_upper=0.9, risk_threshold_upper=0.75,
)

class D13EmpathyChannel(BaseChannel):
    def __init__(self): super().__init__(D13_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        has_partner = "partner" in s.interpersonal_labels

        EMPATHY = ["心疼","揪心","难过","可怜","委屈","辛苦","不容易","难受","压抑",
                   "感同身受","理解你","体会","同情","心软","感动"]
        POSITIVE_EMPATHY = ["替你高兴","为你骄傲","真心祝福","欣慰","替他们开心"]
        DRAIN = ["被消耗","吸能量","烦","累心","不想管","管不了","太负面"]

        empathy_hits = sum(1 for kw in EMPATHY if kw in s.raw_input_text)
        pos_empathy_hits = sum(1 for kw in POSITIVE_EMPATHY if kw in s.raw_input_text)
        drain_hits = sum(1 for kw in DRAIN if kw in s.raw_input_text)

        mirror = 0.4 + empathy_hits * 0.07 + pos_empathy_hits * 0.04 - drain_hits * 0.05
        mirror += (0.10 if has_partner else 0)
        mirror = round(max(0.1, min(mirror, 1.0)), 2)
        overload = round(max(0.0, mirror - 0.55), 2)

        return OrganState(
            organ_name="镜像神经元/情绪共振系统",
            metrics={"mirror_neuron_activation": mirror, "emotional_drain": overload,
                     "empathy_signals": empathy_hits, "drain_signals": drain_hits},
            activation_level=mirror,
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        mirror = o.metrics["mirror_neuron_activation"]
        overload = o.metrics["emotional_drain"]
        if mirror <= 0.45: return (0.6, Intensity.LOW, "共情适度，温柔体贴不内耗")
        if mirror <= 0.60: return (0.2, Intensity.MEDIUM, "共情略高，轻度情绪消耗")
        if mirror <= 0.75: return (-0.25, Intensity.MEDIUM, "共情负荷偏高，易被他人情绪消耗")
        if mirror <= 0.88: return (-0.55, Intensity.HIGH, "过度心疼他人，自身压抑难受")
        return (-0.85, Intensity.EXTREME, "共情严重超载，持续内耗无法自拔")
