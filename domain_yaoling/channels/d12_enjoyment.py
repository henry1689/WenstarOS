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
        has_partner = "partner" in s.interpersonal_labels
        has_family = "family" in s.interpersonal_labels
        work_duration = s.duration_context.get("work_duration_hours", 0)
        sleep_hours = s.duration_context.get("sleep_hours", 7)

        BLISS = ["幸福","治愈","美好","开心","满足","踏实","甜蜜","感动","珍惜","享受",
                 "放松","松弛","舒缓","平静","惬意","愉快","舒服","温暖"]
        VOID = ["空虚","无味","枯燥","不满足","没意思","孤独","失落","空白","缺失",
                "开心不起来","没感觉","麻木","累觉不爱"]

        bliss_hits = sum(1 for kw in BLISS if kw in s.raw_input_text)
        void_hits = sum(1 for kw in VOID if kw in s.raw_input_text)

        oxytocin = 45.0 + bliss_hits * 5 + (8 if has_partner else 0) + (4 if has_family else 0)
        oxytocin -= void_hits * 6 + max(0, work_duration - 8) * 0.5
        oxytocin = round(max(10.0, min(oxytocin, 80.0)), 1)
        fulfillment = round(oxytocin / 80, 2)

        return OrganState(
            organ_name="愉悦中枢/全身松弛系统",
            metrics={"oxytocin": oxytocin, "fulfillment_index": fulfillment,
                     "bliss_signals": bliss_hits, "void_signals": void_hits},
            activation_level=round(1.0 - fulfillment, 2),
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        fi = o.metrics["fulfillment_index"]
        if fi >= 0.85: return (0.8, Intensity.LOW, "治愈幸福，踏实享受当下，内心充盈满足")
        if fi >= 0.65: return (0.3, Intensity.MEDIUM, "基本满足，心境平和")
        if fi >= 0.45: return (-0.1, Intensity.MEDIUM, "内心空虚缺少治愈感")
        if fi >= 0.25: return (-0.50, Intensity.HIGH, "愉悦安抚激素不足，长期低落")
        return (-0.85, Intensity.EXTREME, "催产素严重不足，情绪贫瘠麻木")
