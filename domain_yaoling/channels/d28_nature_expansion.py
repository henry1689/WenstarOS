"""D28 自然世界拓展感知维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D28_CONFIG = DimConfig(
    dim_id=28, dim_key="nature_expansion", category=ChannelCategory.DYNAMIC_GROWTH, quadrant="自然拓展",
    label_cn="D28 自然世界拓展感知", medical_metric_name="探索多巴胺下降幅度", medical_baseline=0.0, medical_unit="%",
    sibling_dims=[27,29,30,31,32], danger_threshold_upper=50.0, risk_threshold_upper=35.0,
)

class D28NatureExpansionChannel(BaseChannel):
    def __init__(self): super().__init__(D28_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        location = s.temporal_context.get("location", "unknown")
        hours_since_chat = s.duration_context.get("hours_since_last_chat", 0)

        EXPLORE = [
            "旅行","远行","出发","探索","冒险","发现","新地方","新环境",
            "户外","自然","山","海","湖","河","森林","草原","沙漠","星空",
            "风景","美景","壮观","辽阔","宽广","新鲜","空气好","清新",
            "改变","换环境","出去走走","出门","走走","出去",
            "想出去","想去","想看看","向往","憧憬",
        ]
        STALE = [
            "一成不变","单调","重复","无聊","待腻了","没新意","老样子",
            "困住","囚禁","出不去","封闭","憋","闷","关着",
            "日复一日","年复一年","原地踏步","停滞","死水",
            "羡慕","看别人","别人都","我也想去",
        ]
        explore_hits = sum(1 for kw in EXPLORE if kw in s.raw_input_text)
        stale_hits = sum(1 for kw in STALE if kw in s.raw_input_text)

        # 探索度下降 = 停滞词×7 + 孤独时长×1.5/h(>6h) + 重复场景 - 探索词×8 - 户外场景
        decline = stale_hits * 7 + max(0, hours_since_chat - 6) * 1.5
        decline -= explore_hits * 8
        # 场景加成: 户外/自然场景→下降放缓
        if location in ("outdoor", "nature", "park", "mountain", "beach", "forest"):
            decline -= 10
        decline = round(max(0.0, min(decline, 60.0)), 1)
        curiosity = round(max(0.0, 1.0 - decline / 60), 2)

        return OrganState(
            organ_name="探索多巴胺/新鲜场景兴奋递质系统",
            metrics={"dopamine_decline_%": decline, "curiosity_index": curiosity,
                     "explore_intent": explore_hits, "stale_feeling": stale_hits},
            activation_level=round(decline / 60, 2),
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        ci = o.metrics["curiosity_index"]
        decline = o.metrics["dopamine_decline_%"]
        explore = o.metrics["explore_intent"]
        stale = o.metrics["stale_feeling"]

        if decline <= 8: return (0.65, Intensity.LOW, "探索欲望充沛，对世界充满好奇与向往")
        if decline <= 18: return (0.2, Intensity.MEDIUM, "探索递质缓慢下降，略感平淡")
        if decline <= 30: return (-0.15, Intensity.MEDIUM, "长期单一环境，探索动力不足，渴望新体验")
        if decline <= 42: return (-0.45, Intensity.HIGH, "长年无新场景，动力明显麻木")
        if decline <= 55: return (-0.70, Intensity.HIGH, f"世界感知固化，深度渴望改变" + ("，强烈想出去" if explore > 0 else ""))
        return (-0.88, Intensity.EXTREME, "探索欲几乎归零，世界感知完全冻结")
