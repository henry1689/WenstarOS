"""D20 团队集体保护维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D20_CONFIG = DimConfig(
    dim_id=20, dim_key="team_protection", category=ChannelCategory.SOCIAL_BONDS, quadrant="团队保护",
    label_cn="D20 团队集体保护", medical_metric_name="集体协作应激激素", medical_baseline=0.0, medical_unit="相对值",
    sibling_dims=[15,16,17,18,19], danger_threshold_upper=0.8, risk_threshold_upper=0.55,
)

class D20TeamChannel(BaseChannel):
    def __init__(self): super().__init__(D20_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        team_hits = sum(1 for kw in ["团队","集体","同事","合作","协作","一起","项目","任务","分工"] if kw in s.raw_input_text)
        stress_hits = sum(1 for kw in ["压力","矛盾","冲突","问题","困难","加班","赶工","紧张"] if kw in s.raw_input_text)
        work_duration = s.duration_context.get("work_duration_hours", 0)
        stress = team_hits * 0.05 + stress_hits * 0.1 + work_duration * 0.04
        stress = round(max(0.0, min(stress, 1.0)), 2)
        belonging = round(0.5 + team_hits * 0.05 - stress_hits * 0.06, 2)
        belonging = max(0.0, min(belonging, 1.0))
        return OrganState(organ_name="集体责任感/团队守护中枢", metrics={"stress_hormone": stress, "team_belonging": belonging, "tension": stress}, activation_level=stress)

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        stress = o.metrics["stress_hormone"]
        belonging = o.metrics["team_belonging"]
        if stress <= 0.2 and belonging >= 0.6: return (0.6, Intensity.LOW, "团队协作安稳,归属感强")
        if stress <= 0.4: return (0.2, Intensity.MEDIUM, "团队基本平稳,轻度压力")
        if stress <= 0.6: return (-0.3, Intensity.MEDIUM, "团队工作压力偏大,身心消耗")
        if stress <= 0.8: return (-0.6, Intensity.HIGH, "团队长期矛盾高压,集体焦虑")
        return (-0.85, Intensity.EXTREME, "团队危机感强烈,集体持续内耗")
