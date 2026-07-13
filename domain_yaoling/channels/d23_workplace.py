"""D23 职场厂区·工作环境维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D23_CONFIG = DimConfig(
    dim_id=23, dim_key="workplace_environment", category=ChannelCategory.SPATIOTEMPORAL, quadrant="职场环境",
    label_cn="D23 职场厂区·工作环境", medical_metric_name="工作皮质醇", medical_baseline=14.0, medical_unit="μg/dL",
    sibling_dims=[21,22,24,25,26], danger_threshold_upper=25.0, risk_threshold_upper=22.0,
)

class D23WorkplaceChannel(BaseChannel):
    def __init__(self): super().__init__(D23_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        is_work = s.temporal_context.get("location", "") in ("office", "workplace", "factory")
        work_duration = s.duration_context.get("work_duration_hours", 0)
        hours_sitting = s.duration_context.get("hours_sitting", 0)

        STRESS = ["赶工","加班","压力","繁忙","紧","任务","项目","报告","交付","节点",
                  "开会","deadline","截止","季度","绩效","考核","汇报"]
        EASE = ["有序","轻松","完成","顺利","休息","下班","放松","摸鱼","不忙","淡季",
                "告一段落","结束","收工"]

        stress_hits = sum(1 for kw in STRESS if kw in s.raw_input_text)
        ease_hits = sum(1 for kw in EASE if kw in s.raw_input_text)

        cortisol = 14.0
        if is_work or work_duration > 4:
            cortisol += work_duration * 0.35 + hours_sitting * 0.15
            cortisol += stress_hits * 1.8 - ease_hits * 2.0
        cortisol = round(max(10.0, min(cortisol, 32.0)), 1)
        lactate = round(min(1.0 + work_duration * 0.18 + stress_hits * 0.12, 3.5), 2)

        return OrganState(
            organ_name="工作应激/疲劳乳酸累积系统",
            metrics={"cortisol": cortisol, "lactate": lactate, "stress_signals": stress_hits,
                     "workload_index": round(work_duration / 12, 2)},
            activation_level=round(cortisol / 32, 2),
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        cortisol = o.metrics["cortisol"]
        if cortisol <= 16: return (0.5, Intensity.LOW, "工作有序轻松，负荷适中")
        if cortisol <= 19: return (0.1, Intensity.MEDIUM, "连续劳作，略感疲惫")
        if cortisol <= 23: return (-0.35, Intensity.HIGH, "工作负荷超标，身体精神双重透支")
        if cortisol <= 27: return (-0.65, Intensity.HIGH, "长期超负荷，慢性疲劳持续叠加")
        return (-0.90, Intensity.EXTREME, "工作严重透支，身心濒临崩溃")
