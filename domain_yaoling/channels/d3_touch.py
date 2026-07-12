"""D3 神经瞬时刺激·触觉维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D3_CONFIG = DimConfig(
    dim_id=3, dim_key="neural_touch", category=ChannelCategory.PHYSICAL_BODY, quadrant="神经感知",
    label_cn="D3 神经瞬时刺激·触觉", medical_metric_name="交感神经兴奋度", medical_baseline=35.0, medical_unit="%",
    sibling_dims=[1,2,4,5,6,7,8], danger_threshold_upper=80.0, risk_threshold_upper=70.0,
)

class D3TouchChannel(BaseChannel):
    def __init__(self): super().__init__(D3_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        has_partner = "partner" in s.interpersonal_labels
        has_stranger = "stranger" in s.interpersonal_labels
        temp = s.environmental_params.get("temperature", 22)
        noise = s.environmental_params.get("noise_db", 40)
        sleep_hours = s.duration_context.get("sleep_hours", 7)

        SOOTHE = [
            "拥抱","触碰","贴近","温暖","柔软","抚摸","牵手","靠","依偎",
            "轻抚","抚摸","按摩","揉","按","捏","拍",
            "舒服","治愈","放松","安心","酥松","柔软","顺滑",
            "温柔","轻轻","缓缓","慢慢","柔",
        ]
        IRRITATE = [
            "刺","扎","麻","痒","冷","冰","烫","粗糙","硬","扎手",
            "刺痛","发麻","紧绷","冰冷","陌生触碰","毛骨悚然",
            "鸡皮疙瘩","汗毛竖起","不适","敏感","碰不得",
        ]
        STARTLE = [
            "吓","惊","跳","突然","猛地","猛","吓一跳","吓死","猝不及防",
            "惊叫","尖叫","啊",
        ]
        soothe_hits = sum(1 for kw in SOOTHE if kw in s.raw_input_text)
        irritate_hits = sum(1 for kw in IRRITATE if kw in s.raw_input_text)
        startle_hits = sum(1 for kw in STARTLE if kw in s.raw_input_text)

        sns = 35.0  # 副交感主导的放松基线
        sns += (12.0 if has_stranger else 0)  # 陌生人→交感 ↑
        sns -= (8.0 if has_partner else 0)  # 伴侣→副交感 ↑
        sns += abs(temp - 22) * 0.5  # 温度偏离
        sns += max(0, noise - 45) * 0.3  # 噪音
        sns += soothe_hits * (-4.0) + irritate_hits * 5.0 + startle_hits * 4.0
        sns += max(0, 7 - sleep_hours) * 2.0  # 睡眠不足→交感 ↑
        sns = round(max(10.0, min(sns, 95.0)), 1)

        return OrganState(
            organ_name="全身表皮神经/末梢神经/敏感神经丛",
            metrics={"sns_excitation_%": sns, "relaxation_%": round(100 - sns, 1),
                     "soothe_signals": soothe_hits, "irritate_signals": irritate_hits},
            activation_level=round(sns / 100, 2),
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        sns = o.metrics["sns_excitation_%"]
        relax = o.metrics["relaxation_%"]
        irritate = o.metrics["irritate_signals"]

        if sns <= 38: return (0.7, Intensity.LOW, "神经松弛，触感舒适治愈，如沐春风")
        if sns <= 50: return (0.3, Intensity.LOW, "神经平稳放松，触感自然")
        if sns <= 62: return (-0.15, Intensity.MEDIUM, "神经略紧绷敏感，易紧张")
        if sns <= 75: return (-0.45, Intensity.HIGH, "交感兴奋偏高，心神不宁易受惊")
        if sns <= 85: return (-0.70, Intensity.HIGH, "极度紧绷，极易受惊心慌" + ("，有刺激信号" if irritate > 0 else ""))
        return (-0.90, Intensity.EXTREME, "交感神经系统超载，惊跳反射持续触发")
