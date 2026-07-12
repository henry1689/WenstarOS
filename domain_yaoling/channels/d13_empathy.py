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
        empathy_hits = sum(1 for kw in ["心疼","揪心","难过","可怜","委屈","辛苦","不容易","难受","压抑","担忧","同情","体会","理解你","感同身受"] if kw in s.raw_input_text)
        other_emotion_hits = sum(1 for kw in ["他","她","他们","伴侣","家人","朋友","同事"] if kw in s.raw_input_text)
        has_partner = "partner" in s.interpersonal_labels
        mirror = 0.4 + empathy_hits * 0.08 + other_emotion_hits * 0.05
        mirror += 0.15 if has_partner else 0
        mirror = round(max(0.1, min(mirror, 1.0)), 2)
        drain = round(mirror * empathy_hits * 0.1, 2)
        return OrganState(organ_name="镜像神经元/情绪共振系统", metrics={"mirror_neuron_activation": mirror, "emotional_drain": drain, "empathy_overload": round(max(0.0, mirror - 0.6), 2)}, activation_level=mirror)

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        mirror = o.metrics["mirror_neuron_activation"]
        overload = o.metrics["empathy_overload"]
        if mirror <= 0.5: return (0.6, Intensity.LOW, "共情适度,温柔体贴不内耗")
        if mirror <= 0.65: return (0.2, Intensity.MEDIUM, "共情略高,轻度情绪消耗")
        if mirror <= 0.8: return (-0.3, Intensity.HIGH, "共情负荷过高,易被他人情绪消耗")
        if mirror <= 0.9: return (-0.6, Intensity.HIGH, "过度心疼他人,自身压抑难受")
        return (-0.85, Intensity.EXTREME, "共情严重超载,持续内耗无法自拔")
