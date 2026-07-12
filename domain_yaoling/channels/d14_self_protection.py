"""D14 个体自我保护维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D14_CONFIG = DimConfig(
    dim_id=14, dim_key="self_protection", category=ChannelCategory.INNER_SPIRIT, quadrant="自我保护",
    label_cn="D14 个体自我保护", medical_metric_name="交感神经戒备基线", medical_baseline=0.2, medical_unit="相对值",
    sibling_dims=[9,10,11,12,13], danger_threshold_upper=0.8, risk_threshold_upper=0.6,
)

class D14SelfProtectionChannel(BaseChannel):
    def __init__(self): super().__init__(D14_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        has_stranger = "stranger" in s.interpersonal_labels
        has_partner = "partner" in s.interpersonal_labels
        has_family = "family" in s.interpersonal_labels
        work_duration = s.duration_context.get("work_duration_hours", 0)
        sleep_hours = s.duration_context.get("sleep_hours", 7)
        location = s.temporal_context.get("location", "unknown")

        THREAT = [
            "危险","伤害","攻击","威胁","不安全","侵犯","可怕","暴力",
            "恶意","敌意","陷阱","骗","害","害人","坑","陷害",
            "暗","黑","深夜","偏僻","无人","陌生地方",
        ]
        VIGILANT = [
            "警惕","小心","防备","防范","戒备","提防","留意","注意安全",
            "谨慎","戒备心","防着","防","盯着",
        ]
        SAFE = [
            "安全","安心","放心","踏实","保护","守护","有保障",
            "没事","不怕","没关系","没问题","好好的",
            "在家","家里","熟悉","习惯了","自己人",
        ]
        threat_hits = sum(1 for kw in THREAT if kw in s.raw_input_text)
        vigilant_hits = sum(1 for kw in VIGILANT if kw in s.raw_input_text)
        safe_hits = sum(1 for kw in SAFE if kw in s.raw_input_text)

        alert = 0.2
        alert += threat_hits * 0.10 + vigilant_hits * 0.06
        alert += (0.18 if has_stranger else 0) - (0.10 if has_partner else 0) - (0.08 if has_family else 0)
        alert += max(0, work_duration - 8) * 0.02  # 长时间工作→戒备↑
        alert += max(0, 7 - sleep_hours) * 0.03  # 睡眠不足→戒备↑
        alert += (0.08 if location in ("outdoor", "public", "transit") else 0)
        alert -= safe_hits * 0.10
        alert = round(max(0.0, min(alert, 1.0)), 2)
        safety = round(1.0 - alert, 2)

        return OrganState(
            organ_name="戒备/退缩/规避防御系统",
            metrics={"alertness_baseline": alert, "safety_level": safety,
                     "defense_intensity": round(min(alert * 1.1, 1.0), 2),
                     "threat_signals": threat_hits, "safe_signals": safe_hits},
            activation_level=alert,
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        safety = o.metrics["safety_level"]
        alert = o.metrics["alertness_baseline"]
        threat = o.metrics["threat_signals"]

        if alert <= 0.25: return (0.7, Intensity.LOW, "安全感充足，身心完全放松无戒备")
        if alert <= 0.40: return (0.25, Intensity.MEDIUM, "轻微戒备，基本放松，偶有警觉")
        if alert <= 0.55: return (-0.15, Intensity.MEDIUM, "安全感不足，神经处于轻度戒备状态")
        if alert <= 0.70: return (-0.45, Intensity.HIGH, "高度防御，时刻紧绷" + ("，存在威胁信号" if threat > 0 else ""))
        if alert <= 0.85: return (-0.70, Intensity.HIGH, "极度不安，防御系统全面激活，无法放松")
        return (-0.90, Intensity.EXTREME, "严重不安全感，防御完全开启，时刻处于应激状态")
