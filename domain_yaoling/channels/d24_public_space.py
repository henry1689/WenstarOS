"""D24 公共场地·人流氛围维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D24_CONFIG = DimConfig(
    dim_id=24, dim_key="public_space", category=ChannelCategory.SPATIOTEMPORAL, quadrant="公共空间",
    label_cn="D24 公共场地·人流氛围", medical_metric_name="嘈杂环境交感兴奋度", medical_baseline=35.0, medical_unit="%",
    sibling_dims=[21,22,23,25,26], danger_threshold_upper=75.0, risk_threshold_upper=60.0,
)

class D24PublicSpaceChannel(BaseChannel):
    def __init__(self): super().__init__(D24_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        is_public = s.temporal_context.get("location", "") in ("outdoor", "public", "mall", "street", "transit")
        crowd = s.environmental_params.get("crowd_density", 0)  # 0-1
        noise = s.environmental_params.get("noise_db", 40)
        comfort_hits = sum(1 for kw in ["热闹","散步","逛街","户外","公园","新鲜","轻松"] if kw in s.raw_input_text)
        annoy_hits = sum(1 for kw in ["拥挤","嘈杂","吵","混乱","烦躁","人太多","闷"] if kw in s.raw_input_text)
        sns = 35.0
        if is_public:
            sns += crowd * 25 + max(0, noise - 45) * 0.8
            sns += annoy_hits * 5 - comfort_hits * 4
        sns = round(max(25.0, min(sns, 90.0)), 1)
        return OrganState(organ_name="嘈杂环境交感神经/人群应激系统", metrics={"sns_excitation_%": sns, "crowd_density": crowd}, activation_level=round(sns/100, 2))

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        sns = o.metrics["sns_excitation_%"]
        crowd = o.metrics["crowd_density"]
        if sns <= 45: return (0.5, Intensity.LOW, "公共环境舒适,轻松自在")
        if sns <= 55: return (0.1, Intensity.MEDIUM, "略拥挤,基本适应")
        if sns <= 65: return (-0.3, Intensity.MEDIUM, "拥挤嘈杂环境,心神消耗")
        if sns <= 78: return (-0.6, Intensity.HIGH, "频繁拥挤嘈杂,神经持续紧绷")
        return (-0.85, Intensity.EXTREME, "长期闹市高分贝,神经不堪重负")
