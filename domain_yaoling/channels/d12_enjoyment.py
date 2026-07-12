"""D12 享受·松弛·幸福感维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D12_CONFIG = DimConfig(
    dim_id=12, dim_key="enjoyment_happiness", category=ChannelCategory.INNER_SPIRIT, quadrant="幸福愉悦",
    label_cn="D12 享受·松弛·幸福感", medical_metric_name="催产素", medical_baseline=45.0, medical_unit="pg/mL",
    sibling_dims=[9,10,11,13,14], danger_threshold_lower=20.0, risk_threshold_lower=25.0,
)

class D12EnjoymentChannel(BaseChannel):
    def __init__(self): super().__init__(D12_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        comfort_hits = sum(1 for kw in ["幸福","享受","舒服","治愈","美好","开心","满足","踏实","温柔","甜蜜","放松","松弛","珍视","陪伴"] if kw in s.raw_input_text)
        empty_hits = sum(1 for kw in ["空虚","无聊","枯燥","没意思","不满足","无味","空白"] if kw in s.raw_input_text)
        has_partner = "partner" in s.interpersonal_labels
        has_family = "family" in s.interpersonal_labels
        oxytocin = 45.0
        oxytocin += comfort_hits * 6 + (8 if has_partner else 0) + (4 if has_family else 0)
        oxytocin -= empty_hits * 7
        oxytocin = round(max(10.0, min(oxytocin, 80.0)), 1)
        # 血清素
        serotonin = 110.0 + comfort_hits * 8 - empty_hits * 8
        serotonin = round(max(20.0, min(serotonin, 180.0)), 1)
        fulfillment = round((oxytocin/45 + serotonin/110) / 2, 2)
        return OrganState(organ_name="愉悦中枢/全身松弛系统", metrics={"oxytocin": oxytocin, "serotonin": serotonin, "fulfillment_index": fulfillment}, activation_level=round(1.0 - fulfillment, 2))

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        fi = o.metrics["fulfillment_index"]
        oxy = o.metrics["oxytocin"]
        if fi >= 0.9: return (0.8, Intensity.LOW, "治愈幸福,踏实享受当下,内心充盈")
        if fi >= 0.7: return (0.3, Intensity.MEDIUM, "基本满足,心境平和")
        if fi >= 0.5: return (-0.2, Intensity.MEDIUM, "内心空虚缺少治愈感")
        if fi >= 0.3: return (-0.55, Intensity.HIGH, "愉悦安抚激素不足,长期低落")
        return (-0.85, Intensity.EXTREME, "催产素严重不足,情绪贫瘠麻木")
