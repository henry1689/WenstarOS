"""D29 人文社交规则细化维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D29_CONFIG = DimConfig(
    dim_id=29, dim_key="social_refinement", category=ChannelCategory.DYNAMIC_GROWTH, quadrant="人文社交",
    label_cn="D29 人文社交规则细化", medical_metric_name="共情包容递质下降幅度", medical_baseline=0.0, medical_unit="%",
    sibling_dims=[27,28,30,31,32], danger_threshold_upper=45.0, risk_threshold_upper=30.0,
)

class D29SocialRefinementChannel(BaseChannel):
    def __init__(self): super().__init__(D29_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        has_stranger = "stranger" in s.interpersonal_labels
        has_colleague = "colleague" in s.interpersonal_labels

        OPEN = [
            "新朋友","新圈子","新人","不同","多样","多元","丰富",
            "融入","接纳","包容","理解","尊重","欣赏","认同",
            "拓展","扩大","认识","接触","交流","沟通",
            "学习","成长","进步","成熟","提升",
        ]
        RIGID = [
            "一成不变","固定","封闭","排斥","不习惯","厌烦","难沟通","不合",
            "看不惯","受不了","讨厌","烦","不喜欢","无法接受",
            "偏见","固有","老派","守旧","固执",
            "只有","总是","从来","永远","都是","就是",
        ]
        CONFLICT = [
            "争吵","吵架","冲突","矛盾","不和","冷战","误解","误会",
            "不理","不睬","回避","躲","僵","尴尬",
        ]
        open_hits = sum(1 for kw in OPEN if kw in s.raw_input_text)
        rigid_hits = sum(1 for kw in RIGID if kw in s.raw_input_text)
        conflict_hits = sum(1 for kw in CONFLICT if kw in s.raw_input_text)

        decline = rigid_hits * 6 + conflict_hits * 5 - open_hits * 8
        decline += (4 if has_stranger else 0)  # 陌生人环境 → 考验包容递质
        decline -= (3 if has_colleague else 0)  # 同事 → 日常社交锻炼
        decline = round(max(0.0, min(decline, 55.0)), 1)
        openness = round(max(0.0, 1.0 - decline / 55), 2)

        return OrganState(
            organ_name="共情包容/人情适配递质系统",
            metrics={"neurotransmitter_decline_%": decline, "openness_index": openness,
                     "rigid_signals": rigid_hits, "conflict_signals": conflict_hits},
            activation_level=round(decline / 55, 2),
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        oi = o.metrics["openness_index"]
        decline = o.metrics["neurotransmitter_decline_%"]
        conflict = o.metrics["conflict_signals"]

        if decline <= 8: return (0.55, Intensity.LOW, "多圈层人际适配平稳，包容开放心态充盈")
        if decline <= 18: return (0.15, Intensity.MEDIUM, "社交圈稳定，包容递质略有下降")
        if decline <= 30: return (-0.15, Intensity.MEDIUM, "社交圈层趋窄，人情认知成长放缓")
        if decline <= 42: return (-0.45, Intensity.HIGH, "固化人际模式，待人处事易内耗" + ("，存在冲突信号" if conflict > 0 else ""))
        return (-0.85, Intensity.EXTREME, "人际认知严重僵化，无法共情包容他人")
