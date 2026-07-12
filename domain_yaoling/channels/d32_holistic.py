"""D32 全身统筹·整体状态输出维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, HealthLevel, ChannelCategory

D32_CONFIG = DimConfig(
    dim_id=32, dim_key="holistic_state", category=ChannelCategory.DYNAMIC_GROWTH, quadrant="统筹汇总",
    label_cn="D32 全身统筹·整体状态", medical_metric_name="综合健康指数", medical_baseline=75.0, medical_unit="分",
    sibling_dims=[27,28,29,30,31], danger_threshold_lower=30.0, risk_threshold_lower=45.0,
)

class D32HolisticChannel(BaseChannel):
    """
    D32 全身统筹——汇总 D1-D31 全部维度状态，计算核心生命体征。

    公式 (禁止 LLM 直接生成):
      心率 = 66 + (D3交感兴奋度-0.35)×60 + (D4皮质醇-14)×1.5
      收缩压 = 115 + (D3交感兴奋度-0.35)×40 + (D1乳酸-1.0)×8
      舒张压 = 73 - (D3交感兴奋度-0.35)×20 - (D4皮质醇-14)×0.5
      皮质醇均值 = D4皮质醇值
      愉悦激素均值 = (D4多巴胺+D12催产素)/2
    """

    def __init__(self): super().__init__(D32_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        # D32 不由外部信号直接驱动，而是从上游 D1-D31 的结果汇总
        # 此方法在 process() 调用前被 upstream_results 覆盖
        return OrganState(organ_name="全身状态汇总中枢", metrics={}, activation_level=0.0)

    def compute_holistic(self, upstream: dict) -> OrganState:
        """从 D1-D31 的 SensationResult 字典计算 D32 汇总。"""
        d1 = upstream.get(1)  # lactate
        d3 = upstream.get(3)  # sns_excitation
        d4 = upstream.get(4)  # cortisol/dopamine/serotonin
        d12 = upstream.get(12)  # oxytocin

        # 提取核心指标
        sns_exc = d3.organ_state.metrics.get("sns_excitation_%", 35) / 100 if d3 else 0.35
        cortisol = d4.organ_state.metrics.get("cortisol", 14) if d4 else 14.0
        lactate = d1.organ_state.metrics.get("lactate", 1.0) if d1 else 1.0
        dopamine = d4.organ_state.metrics.get("dopamine", 120) if d4 else 120.0
        oxytocin = d12.organ_state.metrics.get("oxytocin", 45) if d12 else 45.0

        # 生命体征公式
        hr = round(66 + (sns_exc - 0.35) * 60 + (cortisol - 14) * 1.5, 1)
        bp_sys = round(115 + (sns_exc - 0.35) * 40 + (lactate - 1.0) * 8, 1)
        bp_dia = round(73 - (sns_exc - 0.35) * 20 - (cortisol - 14) * 0.5, 1)
        cortisol_avg = cortisol
        pleasure_avg = round((dopamine + oxytocin) / 2, 1)

        # 综合健康指数: D1-D31 health_level 加权（含偏移幅度修正）
        danger_count = 0; risk_count = 0; sub_count = 0
        danger_severity = 0.0  # 危险维度的总偏移幅度
        risk_severity = 0.0
        for r in upstream.values():
            if not r: continue
            if r.health_level == HealthLevel.DANGER:
                danger_count += 1
                danger_severity += abs(r.deviation)  # -61~-100 → 偏移越大越严重
            elif r.health_level == HealthLevel.RISK:
                risk_count += 1
                risk_severity += abs(r.deviation)
            elif r.health_level == HealthLevel.SUB_HEALTHY:
                sub_count += 1

        # 基础惩罚（降低系数）+ 严重度微调
        danger_penalty = danger_count * 10.0 + danger_severity * 0.02
        risk_penalty = risk_count * 3.0 + risk_severity * 0.01
        sub_penalty = sub_count * 0.5
        base_health = 75.0 - danger_penalty - risk_penalty - sub_penalty
        base_health = round(max(5.0, min(base_health, 95.0)), 1)

        return OrganState(
            organ_name="全身状态汇总中枢",
            metrics={
                "heart_rate": max(40, min(hr, 130)),
                "blood_pressure_sys": max(80, min(bp_sys, 180)),
                "blood_pressure_dia": max(40, min(bp_dia, 110)),
                "cortisol_avg": round(cortisol_avg, 1),
                "pleasure_hormone_avg": max(30, pleasure_avg),
                "health_index": base_health,
                "danger_dims": danger_count,
                "risk_dims": risk_count,
            },
            activation_level=round((100 - base_health) / 100, 2),
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        health = o.metrics.get("health_index", 75)
        danger = o.metrics.get("danger_dims", 0)
        hr = o.metrics.get("heart_rate", 66)
        bp_sys = o.metrics.get("blood_pressure_sys", 115)
        if danger > 0:
            return (-0.9, Intensity.EXTREME, f"⚠️ 全身状态危急: {danger}维度危险,心率{hr},血压{bp_sys}")
        if health >= 70: return (0.65, Intensity.LOW, "全身状态良好,生命体征正常稳定")
        if health >= 55: return (0.15, Intensity.MEDIUM, "全身略疲劳,注意休息调整")
        if health >= 40: return (-0.3, Intensity.MEDIUM, "多处指标偏低,需全面休养")
        return (-0.6, Intensity.HIGH, "全身状态恶化,生命体征异常")
