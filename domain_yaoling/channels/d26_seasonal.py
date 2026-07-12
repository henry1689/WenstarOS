"""D26 四季气象·昼夜节律维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D26_CONFIG = DimConfig(
    dim_id=26, dim_key="seasonal_circadian", category=ChannelCategory.SPATIOTEMPORAL, quadrant="四季昼夜",
    label_cn="D26 四季气象·昼夜节律", medical_metric_name="褪黑素分泌量", medical_baseline=30.0, medical_unit="pg/mL",
    sibling_dims=[21,22,23,24,25], danger_threshold_lower=8.0, risk_threshold_lower=15.0,
)

class D26SeasonalChannel(BaseChannel):
    def __init__(self): super().__init__(D26_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        time_of_day = s.temporal_context.get("time_of_day", "afternoon")
        season = s.temporal_context.get("season", "spring")
        weather = s.temporal_context.get("weather", "clear")
        sleep_hours = s.duration_context.get("sleep_hours", 7)
        work_duration = s.duration_context.get("work_duration_hours", 0)

        RHYTHM_GOOD = [
            "早睡","早起","规律","正常作息","按时","定点","生物钟","有规律",
            "睡眠好","睡得好","睡得香","精神好","元气","清醒","精力",
        ]
        RHYTHM_BAD = [
            "熬夜","失眠","睡不着","通宵","颠倒","黑白颠倒","昼夜颠倒",
            "时差","倒时差","半夜醒","凌晨","睡不好","睡眠差",
            "昏沉","犯困","瞌睡","没睡醒","睡不够","困死",
        ]
        good_hits = sum(1 for kw in RHYTHM_GOOD if kw in s.raw_input_text)
        bad_hits = sum(1 for kw in RHYTHM_BAD if kw in s.raw_input_text)

        # 褪黑素 = 时段基础值 + 睡眠修正 + 季节/天气 + 关键词
        HOUR_MAP = {"morning": 8, "noon": 10, "afternoon": 15, "evening": 45, "night": 60}
        base_melatonin = HOUR_MAP.get(time_of_day, 30)
        base_melatonin += (sleep_hours - 7) * 2.5
        SEASON_MAP = {"spring": 0, "summer": -2, "autumn": 2, "winter": 5}
        base_melatonin += SEASON_MAP.get(season, 0)
        WEATHER_MAP = {"clear": 0, "cloudy": 2, "rain": 5, "snow": 8, "storm": -4, "fog": 3}
        base_melatonin += WEATHER_MAP.get(weather, 0)
        base_melatonin += bad_hits * 2.5 - good_hits * 2.0
        base_melatonin += max(0, work_duration - 8) * 0.5  # 加班扰乱节律
        melatonin = round(max(3.0, min(base_melatonin, 70.0)), 1)

        # 节律质量 = 是否符合时段期望值（而非偏离固定值30）
        EXPECTED = {"morning": 8, "noon": 12, "afternoon": 18, "evening": 45, "night": 55}
        expected_val = EXPECTED.get(time_of_day, 30)
        deviation = abs(melatonin - expected_val)
        rhythm_quality = round(max(0.0, 1.0 - deviation / 50), 2)

        return OrganState(
            organ_name="褪黑素/季节性情绪递质/昼夜节律系统",
            metrics={
                "melatonin": melatonin, "rhythm_quality": rhythm_quality,
                "sleep_hours": sleep_hours, "expected_melatonin": expected_val,
                "good_signals": good_hits, "bad_signals": bad_hits,
            },
            activation_level=round(1.0 - rhythm_quality, 2),
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        rq = o.metrics["rhythm_quality"]
        melatonin = o.metrics["melatonin"]
        sleep = o.metrics["sleep_hours"]
        expected = o.metrics["expected_melatonin"]

        issues = []
        if sleep < 6: issues.append("睡眠不足")
        if melatonin < 6 and expected > 20: issues.append("褪黑素严重偏低")
        if melatonin > 50 and expected < 20: issues.append("褪黑素异常偏高（昼夜紊乱）")
        bad = o.metrics.get("bad_signals", 0)
        if bad > 0: issues.append("存在熬夜/失眠信号")
        issue_str = "（" + "、".join(issues) + "）" if issues else ""

        if rq >= 0.88: return (0.65, Intensity.LOW, "昼夜节律健康，睡眠修复良好")
        if rq >= 0.70: return (0.25, Intensity.MEDIUM, "节律轻微波动，基本正常")
        if rq >= 0.50: return (-0.10, Intensity.MEDIUM, f"作息存在偏离，睡眠质量下降{issue_str}")
        if rq >= 0.30: return (-0.45, Intensity.HIGH, f"昼夜节律明显紊乱，身体节奏打乱{issue_str}")
        if rq >= 0.15: return (-0.70, Intensity.HIGH, "长期昼夜颠倒或严重失眠，生物钟濒临瓦解")
        return (-0.88, Intensity.EXTREME, "节律彻底崩溃，季节性抑郁风险极高")
