"""D8 五感环境·基础体感维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D8_CONFIG = DimConfig(
    dim_id=8, dim_key="five_senses", category=ChannelCategory.PHYSICAL_BODY, quadrant="五感环境",
    label_cn="D8 五感环境·基础体感", medical_metric_name="环境噪音", medical_baseline=40.0, medical_unit="dB",
    sibling_dims=[1,2,3,4,5,6,7], danger_threshold_upper=80.0, risk_threshold_upper=60.0,
)

class D8SensesChannel(BaseChannel):
    def __init__(self): super().__init__(D8_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        ep = s.environmental_params
        temp = ep.get("temperature", 22)
        noise = ep.get("noise_db", 40)
        light = ep.get("light_lux", 300)
        weather = s.temporal_context.get("weather", "clear")

        PLEASANT = [
            "温暖","明亮","清香","安静","舒适","干净","清爽",
            "阳光","微风","鸟鸣","花香","新鲜空气","蓝天",
            "惬意","宜人","舒服","温馨","开阔",
        ]
        UNPLEASANT = [
            "冷","热","闷","潮","湿","燥","干","冻",
            "嘈杂","吵","刺眼","晃眼","暗","昏暗","阴",
            "异味","臭","难闻","烟味","霉味","闷堵",
            "压抑","难受","不舒服","不适",
        ]
        pleasant_hits = sum(1 for kw in PLEASANT if kw in s.raw_input_text)
        unpleasant_hits = sum(1 for kw in UNPLEASANT if kw in s.raw_input_text)

        # 温度评分 (0-1)
        if 20 <= temp <= 25:
            temp_score = 1.0
        elif 16 <= temp <= 30:
            temp_score = 1.0 - abs(temp - 22) * 0.05
        else:
            temp_score = max(0.1, 1.0 - abs(temp - 22) * 0.08)

        # 噪音评分 (0-1)
        if noise <= 40:
            noise_score = 1.0
        elif noise <= 60:
            noise_score = 1.0 - (noise - 40) * 0.015
        elif noise <= 80:
            noise_score = 0.7 - (noise - 60) * 0.02
        else:
            noise_score = max(0.0, 0.3 - (noise - 80) * 0.03)

        # 光照评分 (0-1)
        if 200 <= light <= 800:
            light_score = 1.0
        elif 100 <= light <= 2000:
            light_score = 1.0 - abs(light - 500) * 0.0005
        else:
            light_score = 0.2

        # 天气修正
        weather_map = {"clear": 0.10, "cloudy": 0.02, "rain": -0.08, "snow": -0.12, "storm": -0.20, "fog": -0.05}
        weather_bonus = weather_map.get(weather, 0)

        comfort = (temp_score * 0.30 + noise_score * 0.30 + light_score * 0.20 + 0.20
                   + pleasant_hits * 0.04 - unpleasant_hits * 0.06 + weather_bonus)
        comfort = round(max(0.0, min(comfort, 1.0)), 2)

        return OrganState(
            organ_name="眼耳鼻舌身五感全域",
            metrics={
                "temperature_c": temp, "noise_db": noise, "light_lux": light,
                "comfort_index": comfort,
                "temp_score": round(temp_score, 2), "noise_score": round(noise_score, 2),
                "pleasant_signals": pleasant_hits, "unpleasant_signals": unpleasant_hits,
            },
            activation_level=round(1.0 - comfort, 2),
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        ci = o.metrics["comfort_index"]
        noise = o.metrics["noise_db"]
        temp = o.metrics["temperature_c"]
        unpleasant = o.metrics["unpleasant_signals"]

        issues = []
        if noise > 60: issues.append("嘈杂")
        if temp < 16 or temp > 32: issues.append("温度不适")
        issue_str = "（" + "、".join(issues) + "）" if issues else ""

        if ci >= 0.88: return (0.75, Intensity.LOW, "环境宁静宜人，五感舒适放松")
        if ci >= 0.70: return (0.35, Intensity.LOW, "环境基本舒适，偶有轻微干扰")
        if ci >= 0.50: return (-0.05, Intensity.MEDIUM, f"环境略有干扰{issue_str}，体感一般")
        if ci >= 0.30: return (-0.40, Intensity.MEDIUM, f"环境不适{issue_str}，感官持续受刺激")
        if ci >= 0.15: return (-0.65, Intensity.HIGH, f"环境严重不适{issue_str}，感官难以忍受")
        return (-0.88, Intensity.EXTREME, "极端恶劣环境，五感全面受损")
