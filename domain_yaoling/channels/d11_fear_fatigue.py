"""D11 恐惧·倦怠·制衡心理维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D11_CONFIG = DimConfig(
    dim_id=11, dim_key="fear_fatigue", category=ChannelCategory.INNER_SPIRIT, quadrant="恐惧制衡",
    label_cn="D11 恐惧·倦怠·制衡心理", medical_metric_name="SAS焦虑量表分值", medical_baseline=30.0, medical_unit="分",
    sibling_dims=[9,10,12,13,14], danger_threshold_upper=50.0, risk_threshold_upper=49.0,
)

class D11FearFatigueChannel(BaseChannel):
    def __init__(self): super().__init__(D11_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        work_duration = s.duration_context.get("work_duration_hours", 0)
        hours_since_chat = s.duration_context.get("hours_since_last_chat", 0)
        sleep_hours = s.duration_context.get("sleep_hours", 7)
        has_partner = "partner" in s.interpersonal_labels
        has_family = "family" in s.interpersonal_labels
        has_stranger = "stranger" in s.interpersonal_labels

        # ── 恐惧/焦虑/逃避关键词 ──
        FEAR_HIGH = ["恐惧","绝望","崩溃","末日","无路可走","活不下去","全完了","彻底","毁灭"]
        FEAR_MED = ["害怕","焦虑","不安","紧张","恐慌","担心","忧虑","揪心","慌张","发慌","心惊"]
        FEAR_LOW = ["有点怕","不太确定","没把握","底气不足","隐隐不安","略慌"]

        FATIGUE_HIGH = ["倦怠","麻木","枯竭","油尽灯枯","撑不住","不想继续","放弃算了","彻底累垮"]
        FATIGUE_MED = ["逃避","不想动","不想面对","算了","放弃","没力","动不了","瘫","躺平","摆烂"]
        FATIGUE_LOW = ["累","困","乏","疲惫","提不起劲","不想","懒","没精神"]

        ESCAPE = ["离开","逃离","躲避","回避","不见","不接","不回","躲","逃","消失"]

        SAFETY = ["安全","安心","没事","别怕","放心","保护","守护","陪伴","在一起","有我","不用怕","没关系"]
        CALM = ["平静","从容","松弛","淡定","不急","慢慢来","没关系","无所谓","放松","放宽心"]

        fear_h = sum(1 for kw in FEAR_HIGH if kw in s.raw_input_text)
        fear_m = sum(1 for kw in FEAR_MED if kw in s.raw_input_text)
        fear_l = sum(1 for kw in FEAR_LOW if kw in s.raw_input_text)
        fatigue_h = sum(1 for kw in FATIGUE_HIGH if kw in s.raw_input_text)
        fatigue_m = sum(1 for kw in FATIGUE_MED if kw in s.raw_input_text)
        fatigue_l = sum(1 for kw in FATIGUE_LOW if kw in s.raw_input_text)
        escape_hits = sum(1 for kw in ESCAPE if kw in s.raw_input_text)
        safety_hits = sum(1 for kw in SAFETY if kw in s.raw_input_text)
        calm_hits = sum(1 for kw in CALM if kw in s.raw_input_text)

        # SAS = 30(基线) + 恐惧三级 + 倦怠三级 + 逃离 + 工作疲劳 + 孤独 + 陌生人
        #       - 安全感词 - 平静词 - 伴侣 - 家庭 - 充足睡眠
        sas = 30.0
        sas += fear_h * 6.0 + fear_m * 3.0 + fear_l * 1.5
        sas += fatigue_h * 5.0 + fatigue_m * 2.5 + fatigue_l * 1.0
        sas += escape_hits * 2.0
        sas += work_duration * 0.8  # 长期工作累积焦虑
        sas += max(0, hours_since_chat - 4) * 0.6  # 孤独焦虑
        sas += max(0, 7 - sleep_hours) * 2.0  # 睡眠不足加剧焦虑
        sas += (3.0 if has_stranger else 0)
        sas -= safety_hits * 4.0 + calm_hits * 3.0
        sas -= (4.0 if has_partner else 0) + (2.0 if has_family else 0)
        sas = round(max(20.0, min(sas, 70.0)), 1)

        return OrganState(
            organ_name="警觉/退缩/抗拒/疲惫制动系统",
            metrics={
                "sas_score": sas,
                "fear_intensity": round((fear_h * 3 + fear_m * 1.5 + fear_l * 0.5) / 10, 2),
                "fatigue_level": round((fatigue_h * 3 + fatigue_m * 1.5 + fatigue_l * 0.5) / 10, 2),
                "escape_tendency": round(escape_hits * 0.15, 2),
                "psychological_brake": round(sas / 70, 2),
            },
            activation_level=round(sas / 70, 2),
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        sas = o.metrics["sas_score"]
        escape = o.metrics["escape_tendency"]
        fear = o.metrics["fear_intensity"]
        fatigue = o.metrics["fatigue_level"]

        if sas <= 32: return (0.7, Intensity.LOW, "无恐惧焦虑，松弛从容，心理稳定")
        if sas <= 38: return (0.25, Intensity.MEDIUM, "轻度焦虑疲惫，基本可控")
        if sas <= 45: return (-0.15, Intensity.MEDIUM, "焦虑分值升高，身心持续紧绷")
        if sas <= 52: return (-0.45, Intensity.HIGH, "持续性焦虑，逃避冲动增强，疲惫累积")
        if sas <= 60: return (-0.70, Intensity.HIGH, "深度焦虑恐惧，心理制动全面触发")
        return (-0.90, Intensity.EXTREME, "极度恐惧或彻底枯竭，接近心理崩溃")
