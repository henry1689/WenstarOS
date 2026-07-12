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
        labels = s.interpersonal_labels
        has_partner = "partner" in labels
        has_family = "family" in labels
        # 汗液皮质醇相对浓度: 紧张↑/亲密↓/家庭↓
        sweat_cortisol = 0.0
        positive_aura = sum(1 for kw in ["温柔","安心","亲近","暖和","柔软","甜蜜"] if kw in s.raw_input_text)
        negative_aura = sum(1 for kw in ["冰冷","疏离","压抑","紧绷","陌生","冷淡"] if kw in s.raw_input_text)
        sweat_cortisol += negative_aura * 0.15 - positive_aura * 0.12
        sweat_cortisol -= 0.2 if has_partner else 0
        sweat_cortisol -= 0.1 if has_family else 0
        sweat_cortisol = round(max(0.0, min(sweat_cortisol, 1.0)), 2)
        # 亲和递质: 1.0 - 汗液皮质醇
        affinity = round(1.0 - sweat_cortisol, 2)
        return OrganState(organ_name="气息分泌/隐性氛围系统", metrics={"sweat_cortisol": sweat_cortisol, "affinity_neurotransmitter": affinity}, activation_level=sweat_cortisol)

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        affinity = o.metrics["affinity_neurotransmitter"]
        sc = o.metrics["sweat_cortisol"]
        if affinity >= 0.8: return (0.7, Intensity.LOW, "气场柔和温暖,亲近气息外放")
        if affinity >= 0.6: return (0.3, Intensity.LOW, "气场平稳自然")
        if affinity >= 0.4: return (-0.2, Intensity.MEDIUM, "压力气息偏重,略感疏离")
        if affinity >= 0.2: return (-0.55, Intensity.HIGH, "气场冷淡紧绷,人际隔阂感强")
        return (-0.85, Intensity.EXTREME, "极度压抑冰冷,长期紧绷无亲和力")
