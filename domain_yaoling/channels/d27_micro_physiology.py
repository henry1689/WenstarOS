"""D27 人体微观生理细化感知维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D27_CONFIG = DimConfig(
    dim_id=27, dim_key="micro_physiology", category=ChannelCategory.DYNAMIC_GROWTH, quadrant="微观生理",
    label_cn="D27 人体微观生理细化", medical_metric_name="微量激素波动幅度", medical_baseline=0.0, medical_unit="相对值",
    sibling_dims=[28,29,30,31,32], danger_threshold_upper=0.8, risk_threshold_upper=0.55,
)

class D27MicroPhysiologyChannel(BaseChannel):
    def __init__(self): super().__init__(D27_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        hours_sitting = s.duration_context.get("hours_sitting", 0)
        sleep_hours = s.duration_context.get("sleep_hours", 7)
        work_duration = s.duration_context.get("work_duration_hours", 0)
        has_partner = "partner" in s.interpersonal_labels

        # 微观不适的精细信号
        SUBTLE_NEG = [
            "隐隐","发虚","说不清","不对劲","微妙","轻微","不太舒服",
            "有点闷","有点胀","有点酸","有点麻","有点疼",
            "忽冷忽热","冒汗","发冷","发热","起鸡皮疙瘩","哆嗦",
            "头晕","眼花","耳鸣","心慌","气短","胸闷","恶心",
            "发抖","颤抖","手抖","腿软","站不稳",
        ]
        SUBTLE_POS = [
            "神清气爽","精力充沛","活力","精神饱满","元气",
            "舒畅","通畅","通透","清爽","轻盈",
            "红光满面","气色好","精神好",
        ]
        subtle_neg = sum(1 for kw in SUBTLE_NEG if kw in s.raw_input_text)
        subtle_pos = sum(1 for kw in SUBTLE_POS if kw in s.raw_input_text)

        # 波动幅度 = 负向信号 + 久坐/劳作累积 + 睡眠赤字 - 正向 - 伴侣安抚
        fluctuation = subtle_neg * 0.08 + hours_sitting * 0.02 + work_duration * 0.03
        fluctuation += max(0, 7 - sleep_hours) * 0.06
        fluctuation -= subtle_pos * 0.10 + (0.10 if has_partner else 0)
        fluctuation = round(max(0.0, min(fluctuation, 1.0)), 2)

        return OrganState(
            organ_name="微量内分泌/细胞修复微观感知系统",
            metrics={"fluctuation_amplitude": fluctuation, "micro_sensitivity": round(fluctuation, 2),
                     "subtle_neg_count": subtle_neg, "subtle_pos_count": subtle_pos},
            activation_level=fluctuation,
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        fl = o.metrics["fluctuation_amplitude"]
        if fl <= 0.15: return (0.6, Intensity.LOW, "微观生理平稳，无任何不适")
        if fl <= 0.30: return (0.2, Intensity.MEDIUM, "偶有细微波动，整体平稳")
        if fl <= 0.45: return (-0.15, Intensity.MEDIUM, "微观内分泌轻微失衡，需留意调养")
        if fl <= 0.65: return (-0.45, Intensity.HIGH, "多类微量激素波动，持续性隐性虚弱")
        if fl <= 0.85: return (-0.70, Intensity.HIGH, "微观生理系统明显紊乱")
        return (-0.90, Intensity.EXTREME, "微观生理全面失衡，隐性虚弱严重")
