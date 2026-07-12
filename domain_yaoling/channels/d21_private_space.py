"""D21 私人居所·独处氛围维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D21_CONFIG = DimConfig(
    dim_id=21, dim_key="private_space", category=ChannelCategory.SPATIOTEMPORAL, quadrant="私人空间",
    label_cn="D21 私人居所·独处氛围", medical_metric_name="独处皮质醇降幅", medical_baseline=5.0, medical_unit="μg/dL ↓",
    sibling_dims=[22,23,24,25,26], danger_threshold_lower=0.0, risk_threshold_lower=1.0,
)

class D21PrivateSpaceChannel(BaseChannel):
    def __init__(self): super().__init__(D21_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        loc = s.temporal_context.get("location", "home")
        is_private = loc in ("home", "bedroom", "private")
        noise = s.environmental_params.get("noise_db", 40)
        solitude_hits = sum(1 for kw in ["一个人","安静","独处","私密","自己","放松","卸下","回到","家"] if kw in s.raw_input_text)
        disturbance_hits = sum(1 for kw in ["嘈杂","吵闹","打扰","人多","不私密","不安"] if kw in s.raw_input_text)
        drop = 5.0
        if is_private: drop += solitude_hits * 1.5
        drop -= disturbance_hits * 1.8 + max(0, noise - 50) * 0.1
        drop = round(max(-3.0, min(drop, 10.0)), 1)
        privacy = round(drop / 10, 2)
        return OrganState(organ_name="环境应激皮质醇/休息恢复系统", metrics={"cortisol_drop": drop, "privacy_index": max(0.0, privacy), "is_private": 1 if is_private else 0}, activation_level=round(1.0 - max(0.0, privacy), 2))

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        drop = o.metrics["cortisol_drop"]
        pi = o.metrics["privacy_index"]
        if drop >= 4: return (0.7, Intensity.LOW, "独处私密安稳,身心充分放松回血")
        if drop >= 2: return (0.25, Intensity.MEDIUM, "独处基本舒适,略有干扰")
        if drop >= 1: return (-0.25, Intensity.MEDIUM, "居所略嘈杂,独处降压有限")
        if drop >= 0: return (-0.55, Intensity.HIGH, "缺少安静私密空间,身心无法放松")
        return (-0.85, Intensity.EXTREME, "无私密空间,皮质醇全程居高不下")
