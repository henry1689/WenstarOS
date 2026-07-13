"""D5 信息素·气息氛围维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D5_CONFIG = DimConfig(
    dim_id=5, dim_key="pheromone_aura", category=ChannelCategory.PHYSICAL_BODY, quadrant="气息氛围",
    label_cn="D5 信息素·气息氛围", medical_metric_name="情绪性汗液皮质醇", medical_baseline=0.0, medical_unit="相对浓度",
    sibling_dims=[1,2,3,4,6,7,8], danger_threshold_upper=0.8, risk_threshold_upper=0.55,
)

class D5PheromoneChannel(BaseChannel):
    def __init__(self): super().__init__(D5_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        has_partner = "partner" in s.interpersonal_labels
        has_family = "family" in s.interpersonal_labels
        has_stranger = "stranger" in s.interpersonal_labels
        work_duration = s.duration_context.get("work_duration_hours", 0)
        hours_since_chat = s.duration_context.get("hours_since_last_chat", 0)

        WARM = ["温柔","安心","亲近","暖和","柔软","甜蜜","温馨","暖","爱","依偎","靠","贴",
                "香","清香","芬芳","好闻","熟悉","舒适","放松"]
        COLD = ["冰冷","疏离","压抑","紧绷","陌生","冷淡","冷漠","抗拒","距离","隔阂",
                "汗味","臭味","异味","难闻","刺鼻","闷","不透气"]

        warm_hits = sum(1 for kw in WARM if kw in s.raw_input_text)
        cold_hits = sum(1 for kw in COLD if kw in s.raw_input_text)

        sweat_cortisol = 0.0
        sweat_cortisol += cold_hits * 0.12 - warm_hits * 0.10
        sweat_cortisol += (0.15 if has_stranger else 0) + work_duration * 0.01
        sweat_cortisol -= (0.20 if has_partner else 0) + (0.10 if has_family else 0)
        sweat_cortisol += max(0, hours_since_chat - 6) * 0.02  # 长期独处→气息冷
        sweat_cortisol = round(max(0.0, min(sweat_cortisol, 1.0)), 2)
        affinity = round(1.0 - sweat_cortisol, 2)

        return OrganState(
            organ_name="气息分泌/隐性氛围释放系统",
            metrics={"sweat_cortisol": sweat_cortisol, "affinity_neurotransmitter": affinity,
                     "warm_signals": warm_hits, "cold_signals": cold_hits},
            activation_level=sweat_cortisol,
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        affinity = o.metrics["affinity_neurotransmitter"]
        if affinity >= 0.85: return (0.7, Intensity.LOW, "气场柔和温暖，亲近气息自然外放")
        if affinity >= 0.65: return (0.25, Intensity.MEDIUM, "气场平稳自然")
        if affinity >= 0.45: return (-0.1, Intensity.MEDIUM, "压力气息偏重，人际略感隔阂")
        if affinity >= 0.25: return (-0.45, Intensity.HIGH, "气场冷淡紧绷，人际相处易感到距离")
        return (-0.80, Intensity.EXTREME, "极度压抑冰冷，长期紧绷无亲和力")
