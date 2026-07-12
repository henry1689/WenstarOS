"""D31 主观·客观量子耦合体感维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D31_CONFIG = DimConfig(
    dim_id=31, dim_key="quantum_coupling", category=ChannelCategory.DYNAMIC_GROWTH, quadrant="量子耦合",
    label_cn="D31 主观客观量子耦合", medical_metric_name="身心协调分值", medical_baseline=40.0, medical_unit="分",
    sibling_dims=[27,28,29,30,32], danger_threshold_lower=15.0, risk_threshold_lower=25.0,
)

class D31QuantumCouplingChannel(BaseChannel):
    def __init__(self): super().__init__(D31_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        noise = s.environmental_params.get("noise_db", 40)
        temp = s.environmental_params.get("temperature", 22)
        light = s.environmental_params.get("light_lux", 300)
        has_partner = "partner" in s.interpersonal_labels
        has_family = "family" in s.interpersonal_labels
        has_stranger = "stranger" in s.interpersonal_labels
        location = s.temporal_context.get("location", "unknown")
        time_of_day = s.temporal_context.get("time_of_day", "afternoon")
        work_duration = s.duration_context.get("work_duration_hours", 0)
        sleep_hours = s.duration_context.get("sleep_hours", 7)

        # ── 关键词 ──
        HARMONY = [
            "协调","和谐","契合","匹配","适合","刚刚好","正好","对路",
            "得心应手","如鱼得水","顺","顺畅","舒适","自在",
            "融入","融进去","适应","习惯","找到感觉",
        ]
        DISSONANCE = [
            "不协调","矛盾","不对","不对劲","脱节","不适合","不匹配","身心分离",
            "格格不入","不适应","水土不服","别扭","违和","哪里不对",
            "错位","偏差","出入","对不上","接不上","断",
            "我想的","现实的","差距","落差","不一样","不是这样",
        ]
        harmony_hits = sum(1 for kw in HARMONY if kw in s.raw_input_text)
        dissonance_hits = sum(1 for kw in DISSONANCE if kw in s.raw_input_text)

        # ── 环境适配度 (0~1) ──
        temp_score = max(0, 1.0 - abs(temp - 22) / 15)
        noise_score = max(0, 1.0 - max(0, noise - 45) / 80)
        light_score = max(0, 1.0 - abs(light - 300) / 500) if 100 <= light <= 2000 else 0.3
        env_adapt = round((temp_score * 0.35 + noise_score * 0.35 + light_score * 0.3), 2)

        # ── 人际适配度 (0~1) ──
        social_adapt = 0.6
        social_adapt += (0.25 if has_partner else 0) + (0.10 if has_family else 0)
        social_adapt -= (0.15 if has_stranger else 0)
        # 场景修正: 家→人际适配+0.1, 公共场所→-0.1
        if location in ("home", "bedroom", "living_room"): social_adapt += 0.1
        elif location in ("office", "workplace"): social_adapt += 0.0
        elif location in ("outdoor", "public", "mall", "transit"): social_adapt -= 0.1
        social_adapt = round(max(0.1, min(social_adapt, 1.0)), 2)

        # ── 身体适配度 (0~1) ──
        body_adapt = 0.7
        body_adapt -= work_duration * 0.03 + max(0, 7 - sleep_hours) * 0.08
        # 昼夜: 夜间身体应激下降
        if time_of_day == "night": body_adapt -= 0.1
        body_adapt = round(max(0.1, min(body_adapt, 1.0)), 2)

        # ── 综合耦合 = 环境×0.35 + 人际×0.30 + 身体×0.25 + 主观关键词×0.10 ──
        subjective_bias = harmony_hits * 0.06 - dissonance_hits * 0.10
        coupling = env_adapt * 0.35 + social_adapt * 0.30 + body_adapt * 0.25 + 0.10 + subjective_bias
        coupling = round(max(0.05, min(coupling, 1.0)), 2)

        # 映射到 0~50 分
        score = round(coupling * 50, 1)

        return OrganState(
            organ_name="身心协调/主客观同步耦合系统",
            metrics={
                "harmony_score": score, "coupling_index": coupling,
                "env_adapt": env_adapt, "social_adapt": social_adapt, "body_adapt": body_adapt,
                "dissonance_count": dissonance_hits, "harmony_count": harmony_hits,
            },
            activation_level=round(1.0 - coupling, 2),
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        coupling = o.metrics["coupling_index"]
        dissonance = o.metrics["dissonance_count"]
        env = o.metrics["env_adapt"]
        social = o.metrics["social_adapt"]

        # 生成更有信息的描述
        issues = []
        if env < 0.4: issues.append("环境不适")
        if social < 0.4: issues.append("人际不适")
        issue_str = "、".join(issues) if issues else ""

        if coupling >= 0.85:
            return (0.7, Intensity.LOW, "身心与世界高度和谐，体感与处境完美匹配")
        if coupling >= 0.65:
            return (0.2, Intensity.MEDIUM, "大体协调匹配，偶有不协调感")
        if coupling >= 0.45:
            detail = f"（{issue_str}）" if issue_str else ""
            return (-0.2, Intensity.MEDIUM, f"生活环境/人际与自身适配度偏低，身心略感矛盾{detail}")
        if coupling >= 0.28:
            detail = f"（{issue_str}）" if issue_str else ""
            return (-0.55, Intensity.HIGH, f"长期失衡环境，身心严重冲突内耗{detail}")
        return (-0.85, Intensity.EXTREME, "主客观彻底割裂，身心深度矛盾，无法自洽")
