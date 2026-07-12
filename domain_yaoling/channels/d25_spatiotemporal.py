"""D25 空间距离·时差流逝维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D25_CONFIG = DimConfig(
    dim_id=25, dim_key="spatiotemporal", category=ChannelCategory.SPATIOTEMPORAL, quadrant="时空感知",
    label_cn="D25 空间距离·时差流逝", medical_metric_name="时间紧迫应激皮质醇", medical_baseline=14.0, medical_unit="μg/dL",
    sibling_dims=[21,22,23,24,26], danger_threshold_upper=25.0, risk_threshold_upper=20.0,
)

class D25SpatiotemporalChannel(BaseChannel):
    def __init__(self): super().__init__(D25_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        rush_hits = sum(1 for kw in ["赶","急","迟到","来不及","快点","忙","赶路","行程","排满","紧凑","时间不够"] if kw in s.raw_input_text)
        relaxed_hits = sum(1 for kw in ["悠闲","从容","慢慢","不急","宽松","休息","度假","不赶"] if kw in s.raw_input_text)
        commute_hours = s.duration_context.get("commute_hours", 0)
        cortisol = 14.0 + rush_hits * 2.5 + commute_hours * 1.5 - relaxed_hits * 3.0
        cortisol = round(max(10.0, min(cortisol, 28.0)), 1)
        relaxation = round(1.0 - (cortisol - 10) / 18, 2)
        return OrganState(organ_name="时间紧迫应激/出行疲劳系统", metrics={"cortisol": cortisol, "relaxation_index": max(0.0, relaxation), "time_pressure": round(cortisol/28, 2)}, activation_level=round(cortisol/28, 2))

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        ri = o.metrics["relaxation_index"]
        tp = o.metrics["time_pressure"]
        if tp <= 0.4: return (0.6, Intensity.LOW, "行程从容悠闲,时空松弛自在")
        if tp <= 0.55: return (0.15, Intensity.MEDIUM, "略感紧迫,基本可控")
        if tp <= 0.7: return (-0.3, Intensity.MEDIUM, "频繁赶路,长期处于紧张状态")
        if tp <= 0.85: return (-0.6, Intensity.HIGH, "日程排满无缓冲,持续性紧迫焦虑")
        return (-0.85, Intensity.EXTREME, "时空高度压缩,长期喘息不得")
