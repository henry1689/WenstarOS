"""D22 家庭布局·共处氛围维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D22_CONFIG = DimConfig(
    dim_id=22, dim_key="home_environment", category=ChannelCategory.SPATIOTEMPORAL, quadrant="家庭布局",
    label_cn="D22 家庭布局·共处氛围", medical_metric_name="居家情绪恢复效率", medical_baseline=80.0, medical_unit="%",
    sibling_dims=[21,23,24,25,26], danger_threshold_lower=30.0, risk_threshold_lower=45.0,
)

class D22HomeEnvironmentChannel(BaseChannel):
    def __init__(self): super().__init__(D22_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        loc = s.temporal_context.get("location", "home")
        is_home = loc in ("home", "bedroom", "living_room")
        cosy_hits = sum(1 for kw in ["温馨","整洁","舒服","明亮","温暖","干净","宽敞","布置","家"] if kw in s.raw_input_text)
        gloomy_hits = sum(1 for kw in ["昏暗","杂乱","脏","闷","压抑","窄","吵闹","不透气"] if kw in s.raw_input_text)
        light = s.environmental_params.get("light_lux", 300)
        recovery = 80.0
        if is_home:
            recovery += cosy_hits * 5 - gloomy_hits * 7
            recovery += (min(light, 800) - 300) * 0.02 if light < 600 else -5
        recovery = round(max(10.0, min(recovery, 100.0)), 1)
        mood = round(recovery / 100, 2)
        return OrganState(organ_name="居家情绪恢复/光照应激系统", metrics={"recovery_efficiency_%": recovery, "mood_index": mood, "is_home": 1 if is_home else 0}, activation_level=round(1.0 - mood, 2))

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        recovery = o.metrics["recovery_efficiency_%"]
        mood = o.metrics["mood_index"]
        if recovery >= 75: return (0.65, Intensity.LOW, "居家温馨舒适,心情舒展放松")
        if recovery >= 55: return (0.2, Intensity.MEDIUM, "居家基本舒适,偶有沉闷")
        if recovery >= 40: return (-0.3, Intensity.HIGH, "居家环境压抑,心情难以舒展")
        if recovery >= 25: return (-0.6, Intensity.HIGH, "长期压抑居家环境,情绪持续低迷")
        return (-0.85, Intensity.EXTREME, "居家环境严重压抑,完全无法放松")
