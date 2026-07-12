"""D10 原生欲望·成长驱动力维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D10_CONFIG = DimConfig(
    dim_id=10, dim_key="desire_drive", category=ChannelCategory.INNER_SPIRIT, quadrant="欲望动力",
    label_cn="D10 原生欲望·成长驱动力", medical_metric_name="探索递质下降幅度", medical_baseline=0.0, medical_unit="%",
    sibling_dims=[9,11,12,13,14], danger_threshold_upper=50.0, risk_threshold_upper=40.0,
)

class D10DesireDriveChannel(BaseChannel):
    def __init__(self): super().__init__(D10_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        novelty_hits = sum(1 for kw in ["新","探索","学","好奇","想试试","第一次","挑战","进步","变强","成长"] if kw in s.raw_input_text)
        stagnation_hits = sum(1 for kw in ["无聊","没意思","懈怠","麻木","停滞","不想动","重复"] if kw in s.raw_input_text)
        hours_sitting = s.duration_context.get("hours_sitting", 0)
        work_duration = s.duration_context.get("work_duration_hours", 0)
        # 探索递质下降%
        decline = stagnation_hits * 8 + hours_sitting * 2 + work_duration * 1.5 - novelty_hits * 10
        decline = round(max(0.0, min(decline, 70.0)), 1)
        drive_index = round(1.0 - decline / 100, 2)
        return OrganState(organ_name="求知欲/变强欲/探索欲激活中枢", metrics={"neurotransmitter_decline_%": decline, "drive_index": max(0.0, drive_index)}, activation_level=round(decline/70, 2))

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        di = o.metrics["drive_index"]
        decline = o.metrics["neurotransmitter_decline_%"]
        if decline <= 10: return (0.7, Intensity.LOW, "生命活力充沛,积极渴望成长探索")
        if decline <= 25: return (0.2, Intensity.MEDIUM, "动力略降,轻度懈怠")
        if decline <= 40: return (-0.3, Intensity.MEDIUM, "动力激素偏低,缺少新鲜感易倦怠")
        if decline <= 55: return (-0.6, Intensity.HIGH, "麻木无追求,成长停滞")
        return (-0.85, Intensity.EXTREME, "动力几乎枯竭,无欲无求")
