"""D4 内分泌·激素波动维度（核心真人生理指标）"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D4_CONFIG = DimConfig(
    dim_id=4, dim_key="endocrine_hormones", category=ChannelCategory.PHYSICAL_BODY, quadrant="内分泌",
    label_cn="D4 内分泌·激素波动", medical_metric_name="晨间皮质醇", medical_baseline=14.0, medical_unit="μg/dL",
    sibling_dims=[1,2,3,5,6,7,8], danger_threshold_upper=25.0, risk_threshold_upper=22.0,
)

class D4EndocrineChannel(BaseChannel):
    def __init__(self): super().__init__(D4_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        labels = s.interpersonal_labels
        has_partner = "partner" in labels
        has_family = "family" in labels
        has_stranger = "stranger" in labels
        time_of_day = s.temporal_context.get("time_of_day", "afternoon")
        work_duration = s.duration_context.get("work_duration_hours", 0)
        hours_since_chat = s.duration_context.get("hours_since_last_chat", 0)
        sleep_hours = s.duration_context.get("sleep_hours", 7)

        # ── 关键词分层 ──
        STRESS_HIGH = ["崩溃","绝望","活不下去","受不了","撑不住","极度","要死了","完蛋","崩塌"]
        STRESS_MED = ["焦虑","烦躁","压抑","压力","紧张","担心","害怕","不安","烦躁","抓狂","崩溃边缘","累死了"]
        STRESS_LOW = ["累","烦","困","乏","疲惫","倦","没精神","提不起劲","不想动"]
        COMFORT_HIGH = ["幸福","温馨","甜","治愈","温暖","安心","满足","美好","爱","开心","快乐","感动"]
        COMFORT_MED = ["舒服","放松","舒缓","平静","悠闲","自在","轻松","愉快","好","不错"]
        JOY = ["惊喜","兴奋","激动","期待","渴望","迫不及待","太棒","好极了"]

        stress_h = sum(1 for kw in STRESS_HIGH if kw in s.raw_input_text)
        stress_m = sum(1 for kw in STRESS_MED if kw in s.raw_input_text)
        stress_l = sum(1 for kw in STRESS_LOW if kw in s.raw_input_text)
        comfort_h = sum(1 for kw in COMFORT_HIGH if kw in s.raw_input_text)
        comfort_m = sum(1 for kw in COMFORT_MED if kw in s.raw_input_text)
        joy_hits = sum(1 for kw in JOY if kw in s.raw_input_text)

        # ═══════════════════════════════════════════════
        # 皮质醇 (μg/dL) — 真实生理范围 5~35 μg/dL
        # ═══════════════════════════════════════════════
        cortisol = 14.0  # 晨间基准
        # 工作负荷: 8h→+2.0, 12h→+3.0, 14h→+3.5
        cortisol += work_duration * 0.25
        # 睡眠赤字: 每缺1h +1.5
        cortisol += max(0, 7 - sleep_hours) * 1.5
        # 孤独/分离: >4h开始 ↑, >8h加速 ↑
        if hours_since_chat > 8:
            cortisol += 2.0 + (hours_since_chat - 8) * 0.5
        elif hours_since_chat > 4:
            cortisol += (hours_since_chat - 4) * 0.3
        # 关键词: 高压力+3/词, 中压力+1.5, 低压力+0.5
        cortisol += stress_h * 3.0 + stress_m * 1.5 + stress_l * 0.5
        # 安抚: 高安抚-2, 中安抚-1, 喜悦-1.5
        cortisol -= comfort_h * 2.0 + comfort_m * 1.0 + joy_hits * 1.5
        # 社交: 伴侣-2, 家庭-1, 陌生人+2
        cortisol += (2.0 if has_stranger else 0) - (2.0 if has_partner else 0) - (1.0 if has_family else 0)
        # 昼夜节律: 午后-2, 傍晚-4, 夜间-5 (自然下降)
        if time_of_day == "noon": cortisol -= 1
        elif time_of_day == "afternoon": cortisol -= 2
        elif time_of_day == "evening": cortisol -= 4
        elif time_of_day == "night": cortisol -= 5
        cortisol = round(max(5.0, min(cortisol, 35.0)), 1)

        # ═══════════════════════════════════════════════
        # 多巴胺 (pg/mL) — 真实范围 30~200 pg/mL
        # ═══════════════════════════════════════════════
        dopamine = 120.0
        NOVELTY = ["新","探索","好奇","惊喜","第一次","学习","有趣","冒险","挑战","改变","未知","尝试"]
        ACHIEVE = ["完成","成功","进步","成长","突破","做到","掌握","学会","达成","好了"]
        APATHY = ["无聊","没意思","麻木","无所谓","随便","随便吧","都一样","空虚","懈怠","停滞","重复","一成不变"]

        novelty_hits = sum(1 for kw in NOVELTY if kw in s.raw_input_text)
        achieve_hits = sum(1 for kw in ACHIEVE if kw in s.raw_input_text)
        apathy_hits = sum(1 for kw in APATHY if kw in s.raw_input_text)

        dopamine += novelty_hits * 6 + achieve_hits * 5 + joy_hits * 4
        dopamine += (6 if has_partner else 0)  # 伴侣陪伴→多巴胺 ↑
        dopamine -= apathy_hits * 7 + work_duration * 2  # 工作消耗多巴胺
        dopamine = round(max(30.0, min(dopamine, 200.0)), 1)

        # ═══════════════════════════════════════════════
        # 血清素 (ng/mL) — 真实范围 20~180 ng/mL
        # ═══════════════════════════════════════════════
        serotonin = 110.0
        SERENITY = ["安心","安稳","平静","踏实","满足","感恩","珍惜","美好","宁静","祥和","知足"]
        BELONGING = ["家","回家","在一起","陪伴","团聚","团圆","属于","归属","归宿"]
        DISCONTENT = ["空虚","不满足","缺失","缺","少","不够","不足","遗憾","可惜"]

        serenity_hits = sum(1 for kw in SERENITY if kw in s.raw_input_text)
        belong_hits = sum(1 for kw in BELONGING if kw in s.raw_input_text)
        discontent_hits = sum(1 for kw in DISCONTENT if kw in s.raw_input_text)

        serotonin += (serenity_hits * 6 + belong_hits * 5 + comfort_h * 4 + comfort_m * 2)
        serotonin += (5 if has_family else 0) + (4 if has_partner else 0)
        serotonin -= (discontent_hits * 5 + work_duration * 2 + stress_m * 3)
        # 光照修正: 白天+3, 夜间-3
        if time_of_day in ("morning", "noon", "afternoon"): serotonin += 3
        elif time_of_day in ("night",): serotonin -= 3
        serotonin = round(max(20.0, min(serotonin, 180.0)), 1)

        # 激素平衡指数
        balance = round((dopamine / 120 + serotonin / 110) / 2, 2)

        return OrganState(
            organ_name="全身内分泌系统/腺体/激素中枢",
            metrics={
                "cortisol": cortisol, "dopamine": dopamine, "serotonin": serotonin,
                "hormone_balance": balance,
                "stress_level": round(cortisol / 35, 2),
                "cortisol_deviation": round(cortisol - 14, 1),
            },
            activation_level=round(cortisol / 35, 2),
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        balance = o.metrics["hormone_balance"]
        cortisol = o.metrics["cortisol"]
        if balance >= 0.95 and cortisol <= 16:
            return (0.7, Intensity.LOW, "激素平衡，情绪安静愉悦")
        if balance >= 0.80:
            return (0.3, Intensity.LOW, "激素基本平稳，情绪底色偏正向")
        if balance >= 0.60:
            return (0.0, Intensity.MEDIUM, "轻度波动，偶有烦躁疲惫")
        if balance >= 0.40:
            return (-0.30, Intensity.MEDIUM, "压力激素偏高，亢奋与低落交替")
        if balance >= 0.25:
            return (-0.55, Intensity.HIGH, "皮质醇超标，疲惫压抑感明显")
        return (-0.85, Intensity.EXTREME, "激素严重失衡，长期焦虑或麻木")
