"""D7 躯体自愈·修复维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D7_CONFIG = DimConfig(
    dim_id=7, dim_key="self_healing", category=ChannelCategory.PHYSICAL_BODY, quadrant="自愈修复",
    label_cn="D7 躯体自愈·修复", medical_metric_name="乳酸清除速率", medical_baseline=1.2, medical_unit="mmol/h",
    sibling_dims=[1,2,3,4,5,6,8], danger_threshold_lower=0.5, risk_threshold_lower=0.9,
)

class D7RecoveryChannel(BaseChannel):
    def __init__(self): super().__init__(D7_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        sleep_hours = s.duration_context.get("sleep_hours", 7)
        rest_minutes = s.duration_context.get("rest_minutes", 30)
        work_duration = s.duration_context.get("work_duration_hours", 0)
        has_partner = "partner" in s.interpersonal_labels

        RESTORE = [
            "放松","休息","安抚","安静","温暖","舒服","舒缓","恢复",
            "睡觉","入眠","深睡","熟睡","小憩","午休","补觉",
            "按摩","泡澡","热敷","SPA","理疗","推拿",
            "休假","度假","周末","放假","休息日",
        ]
        IMPAIR = [
            "失眠","睡不着","熬夜","通宵","反复醒","睡眠浅","多梦",
            "积劳","透支","超负荷","连轴转","不休","不歇",
            "恢复不过来","好不了","退不了","消不掉","消除不了",
        ]
        restore_hits = sum(1 for kw in RESTORE if kw in s.raw_input_text)
        impair_hits = sum(1 for kw in IMPAIR if kw in s.raw_input_text)

        # 乳酸清除 = 1.2(基线) + 睡眠×0.06/h + 休息×0.005/min + 正向×0.08/词 + 伴侣×0.12
        #            - 劳作×0.05/h - 负向×0.09/词
        clearance = 1.2
        clearance += (sleep_hours - 7) * 0.06 + rest_minutes * 0.005 + restore_hits * 0.08
        clearance += (0.12 if has_partner else 0)
        clearance -= work_duration * 0.05 + impair_hits * 0.09
        clearance = round(max(0.2, min(clearance, 2.5)), 2)
        recovery_index = round(clearance / 1.2, 2)

        return OrganState(
            organ_name="全身修复机制/细胞代谢/疲劳消解系统",
            metrics={"lactate_clearance": clearance, "recovery_index": recovery_index,
                     "restore_signals": restore_hits, "impair_signals": impair_hits},
            activation_level=round(1.0 - clearance / 2.5, 2),
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        ri = o.metrics["recovery_index"]
        impair = o.metrics["impair_signals"]
        if ri >= 1.05: return (0.7, Intensity.LOW, "身体修复活跃，疲劳快速消退，机能回升")
        if ri >= 0.85: return (0.25, Intensity.MEDIUM, "修复正常，偶有轻微疲劳残留")
        if ri >= 0.60: return (-0.15, Intensity.MEDIUM, "修复速度变慢，休息也难以完全恢复")
        if ri >= 0.40: return (-0.50, Intensity.HIGH, "修复停滞，疲惫持续堆积，积劳感加重")
        return (-0.85, Intensity.EXTREME, "修复近乎停滞" + ("，失眠/透支信号明显" if impair > 0 else "，积劳持续恶化"))
