"""D2 躯体疼痛·不适感知维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D2_CONFIG = DimConfig(
    dim_id=2, dim_key="pain_perception", category=ChannelCategory.PHYSICAL_BODY, quadrant="躯体感知",
    label_cn="D2 躯体疼痛·不适感知", medical_metric_name="VAS疼痛评分", medical_baseline=0.0, medical_unit="分",
    sibling_dims=[1,3,4,5,6,7,8], danger_threshold_upper=6.0, risk_threshold_upper=4.0,
)

class D2PainChannel(BaseChannel):
    def __init__(self): super().__init__(D2_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        hours_sitting = s.duration_context.get("hours_sitting", 0)
        work_duration = s.duration_context.get("work_duration_hours", 0)
        sleep_hours = s.duration_context.get("sleep_hours", 7)

        # 疼痛关键词——分三级权重
        SEVERE = ["剧痛","撕裂","断裂","骨折","绞痛","刺骨","钻心","抽搐","痉挛","撕裂感"]
        MODERATE = ["酸痛","胀痛","闷痛","刺痛","隐痛","压痛","阵痛","灼痛","牵拉痛"]
        MILD = ["酸","胀","麻","僵","不适","难受","发紧","发沉","不舒服","不太舒服"]
        RELIEF = ["不痛","不疼","轻松","舒服","舒畅","缓解","好转","消退","恢复","好多了","没事"]

        severe_hits = sum(1 for kw in SEVERE if kw in s.raw_input_text)
        moderate_hits = sum(1 for kw in MODERATE if kw in s.raw_input_text)
        mild_hits = sum(1 for kw in MILD if kw in s.raw_input_text)
        relief_hits = sum(1 for kw in RELIEF if kw in s.raw_input_text)

        # VAS = 三级加权 + 久坐×0.15/h + 劳作×0.2/h - 睡眠×0.3/h(>6h) - 缓解词×0.5
        vas = severe_hits * 3.0 + moderate_hits * 1.5 + mild_hits * 0.6
        vas += hours_sitting * 0.15 + work_duration * 0.20
        vas -= max(0, (sleep_hours - 6)) * 0.3 + relief_hits * 0.5
        # 疼痛有上限但允许为0
        vas = round(max(0.0, min(vas, 10.0)), 1)

        return OrganState(
            organ_name="全身痛觉神经/筋膜感受器",
            metrics={"vas_score": vas, "severe_count": severe_hits, "moderate_count": moderate_hits, "mild_count": mild_hits},
            activation_level=round(vas / 10, 2),
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        vas = o.metrics["vas_score"]
        severe = o.metrics["severe_count"]
        if vas == 0: return (1.0, Intensity.LOW, "全身轻松，毫无疼痛不适")
        if vas <= 1.5: return (0.4, Intensity.LOW, "偶有轻微不适，近乎无感")
        if vas <= 3.0: return (0.0, Intensity.MEDIUM, "轻度酸胀不适，尚可忍受")
        if vas <= 5.0: return (-0.35, Intensity.MEDIUM, "中度疼痛不适，身体发出警告")
        if vas <= 7.0: return (-0.60, Intensity.HIGH, f"持续疼痛，身体强烈抗拒休息" + ("，存在剧痛信号" if severe > 0 else ""))
        return (-0.90, Intensity.EXTREME, "剧烈疼痛，急需停下手头事务休息")
