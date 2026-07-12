"""D6 生理周期·代谢生命周期维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D6_CONFIG = DimConfig(
    dim_id=6, dim_key="metabolic_cycle", category=ChannelCategory.PHYSICAL_BODY, quadrant="生理周期",
    label_cn="D6 生理周期·代谢生命周期", medical_metric_name="代谢下降幅度", medical_baseline=0.0, medical_unit="%",
    sibling_dims=[1,2,3,4,5,7,8], danger_threshold_upper=30.0, risk_threshold_upper=20.0,
)

class D6MetabolismChannel(BaseChannel):
    def __init__(self): super().__init__(D6_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        hours_sitting = s.duration_context.get("hours_sitting", 0)
        sleep_hours = s.duration_context.get("sleep_hours", 7)
        work_duration = s.duration_context.get("work_duration_hours", 0)

        VITAL = [
            "精力充沛","活力","元气","精神好","有劲","状态好",
            "代谢快","消化好","吃得香","吸收好","营养","补",
            "运动","锻炼","健身","跑步","散步","活动",
        ]
        DECLINE = [
            "虚弱","乏力","无力","没劲","提不起劲","虚","蔫",
            "呆滞","迟缓","慢","没精神","疲惫","累","乏","困",
            "不消化","胃不好","吃不下","没胃口","食欲不振",
        ]
        vital_hits = sum(1 for kw in VITAL if kw in s.raw_input_text)
        decline_hits = sum(1 for kw in DECLINE if kw in s.raw_input_text)

        # BMR下降% = 久坐×1.5 + 睡眠赤字×2.5 + 劳作×1.0 + 负向词×2.5 - 正向词×3.5 - 运动
        bmr_decline = hours_sitting * 1.5 + max(0, 7 - sleep_hours) * 2.5 + work_duration * 1.0
        bmr_decline += decline_hits * 2.5 - vital_hits * 3.5
        activity_minutes = s.duration_context.get("activity_minutes", 0)
        bmr_decline -= activity_minutes * 0.03
        bmr_decline = round(max(0.0, min(bmr_decline, 50.0)), 1)
        vitality = round(max(0.0, 1.0 - bmr_decline / 100), 2)

        return OrganState(
            organ_name="整套人体生理运转体系/基础代谢/营养吸收",
            metrics={"bmr_decline_%": bmr_decline, "vitality_index": vitality,
                     "nutrition_efficiency_%": round(100 - bmr_decline * 1.2, 1),
                     "vital_signals": vital_hits, "decline_signals": decline_hits},
            activation_level=round(bmr_decline / 50, 2),
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        vi = o.metrics["vitality_index"]
        decline = o.metrics["bmr_decline_%"]
        if decline <= 5: return (0.65, Intensity.LOW, "代谢顺畅，身体鲜活饱满，生命力旺盛")
        if decline <= 12: return (0.2, Intensity.MEDIUM, "代谢略微放缓，基本充沛")
        if decline <= 22: return (-0.1, Intensity.MEDIUM, "基础代谢偏低，营养吸收不足，体虚乏力")
        if decline <= 35: return (-0.45, Intensity.HIGH, "代谢明显下降，长期虚弱，需休养滋养")
        return (-0.80, Intensity.EXTREME, "代谢严重迟缓，身体沉重，养分严重不足")
