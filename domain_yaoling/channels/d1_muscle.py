"""D1 骨骼肌肉·体能负荷维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, HealthLevel, ChannelCategory

D1_CONFIG = DimConfig(
    dim_id=1, dim_key="muscle_load", category=ChannelCategory.PHYSICAL_BODY, quadrant="骨骼运动",
    label_cn="D1 骨骼肌肉·体能负荷", medical_metric_name="血乳酸堆积值", medical_baseline=1.0, medical_unit="mmol/L",
    sibling_dims=[2,3,4,5,6,7,8], danger_threshold_upper=2.5, risk_threshold_upper=1.6,
)

class D1MuscleChannel(BaseChannel):
    def __init__(self): super().__init__(D1_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        hours_sitting = s.duration_context.get("hours_sitting", 0)
        activity_minutes = s.duration_context.get("activity_minutes", 0)
        work_duration = s.duration_context.get("work_duration_hours", 0)
        time_of_day = s.temporal_context.get("time_of_day", "afternoon")

        POS = [  # 正向/舒缓关键词——降低乳酸，提升肌力
            "开心","抱","舒服","放松","好","爱","温暖","休息","舒展","拉伸",
            "运动","跑步","散步","健身","锻炼","瑜伽","走路","游泳",
            "按摩","泡澡","热水","躺","伸懒腰","活动","走动",
            "轻松","舒适","柔软","松弛","释放","缓解",
        ]
        NEG = [  # 负向/疲劳关键词——升高乳酸，降低肌力
            "酸","痛","僵","麻","胀","累","乏","困","无力","疲惫",
            "劳损","透支","紧绷","沉重","抬不起来","动不了",
            "久坐","不动","熬夜","通宵","加班",
        ]
        pos_hits = sum(1 for kw in POS if kw in s.raw_input_text)
        neg_hits = sum(1 for kw in NEG if kw in s.raw_input_text)

        # 乳酸 = 1.0(基线) + 久坐×0.04/h + 劳作×0.05/h + 负向×0.08/词 - 运动×0.005/min - 正向×0.06/词 - 晚间调整
        lactate = 1.0 + hours_sitting * 0.04 + work_duration * 0.05 + neg_hits * 0.08
        lactate -= activity_minutes * 0.005 + pos_hits * 0.06
        if time_of_day == "evening": lactate -= 0.10
        elif time_of_day == "night": lactate -= 0.15
        lactate = round(max(0.3, min(lactate, 4.0)), 2)

        # 肌力储备 = 60(基线) - 久坐×1.5%/h - 劳作×2.5%/h - 负向×2%/词 + 运动×0.08%/min + 正向×1.5%/词 + 睡眠修正
        sleep_hours = s.duration_context.get("sleep_hours", 7)
        sleep_boost = max(0, (sleep_hours - 6)) * 3.0  # 充足睡眠提升肌力
        muscle_reserve = 60.0 - hours_sitting * 1.5 - work_duration * 2.5 - neg_hits * 2.0
        muscle_reserve += activity_minutes * 0.08 + pos_hits * 1.5 + sleep_boost
        muscle_reserve = round(max(10.0, min(muscle_reserve, 95.0)), 1)

        fatigue = round((lactate - 1.0) / 3.0, 2)  # 0-1
        return OrganState(
            organ_name="骨骼肌/关节/筋膜",
            metrics={"lactate": lactate, "muscle_reserve_%": muscle_reserve, "fatigue_index": fatigue},
            activation_level=round(fatigue, 2),
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        fatigue = o.metrics["fatigue_index"]
        mr = o.metrics["muscle_reserve_%"]
        if fatigue <= 0.15: return (0.6 + mr / 200, Intensity.LOW, "身体舒展通透，肌力充沛")
        if fatigue <= 0.30: return (0.2 + mr / 300, Intensity.MEDIUM, "肌肉略有紧张，整体尚佳")
        if fatigue <= 0.45: return (-0.1, Intensity.MEDIUM, "肌肉僵硬，轻度酸痛")
        if fatigue <= 0.60: return (-0.35, Intensity.HIGH, "肌肉明显酸痛，肢体乏力劳损")
        if fatigue <= 0.80: return (-0.65, Intensity.HIGH, "肌肉严重透支，全身紧绷无力")
        return (-0.90, Intensity.EXTREME, "肌肉即将崩溃，乳酸严重堆积")
