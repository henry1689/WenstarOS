"""D30 精神文娱·修养成长维度"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, Intensity, ChannelCategory

D30_CONFIG = DimConfig(
    dim_id=30, dim_key="spiritual_growth", category=ChannelCategory.DYNAMIC_GROWTH, quadrant="精神成长",
    label_cn="D30 精神文娱·修养成长", medical_metric_name="精神血清素下降幅度", medical_baseline=0.0, medical_unit="%",
    sibling_dims=[27,28,29,31,32], danger_threshold_upper=45.0, risk_threshold_upper=30.0,
)

class D30SpiritualGrowthChannel(BaseChannel):
    def __init__(self): super().__init__(D30_CONFIG)

    def _organ_response(self, s: SignalInput) -> OrganState:
        ENRICH = [
            "看书","读书","音乐","电影","剧","艺术","画","展","博物馆",
            "运动","健身","跑步","瑜伽","游泳","锻炼","打球",
            "学习","上课","课程","培训","知识","技能","读书会",
            "旅行","出游","爬山","徒步","骑行","露营",
            "写","创作","画画","弹琴","唱歌","摄影","手工",
            "充实","丰富","有趣","有意义","成长","收获","启发",
        ]
        VOID = [
            "空虚","无聊","迷茫","没意思","浮躁","空洞","荒废","无所事事",
            "刷手机","刷视频","刷","浪费时间","打发时间",
            "没有方向","不知道干什么","没目标","浑浑噩噩",
            "羡慕别人","别人都好","我怎么","没有自己的",
        ]
        enrich_hits = sum(1 for kw in ENRICH if kw in s.raw_input_text)
        void_hits = sum(1 for kw in VOID if kw in s.raw_input_text)

        # 精神血清素下降 = 空虚词×7 + 孤独(>6h)×1.2/h - 丰富词×9 - 场景加成
        decline = void_hits * 7
        hours_since_chat = s.duration_context.get("hours_since_last_chat", 0)
        decline += max(0, hours_since_chat - 6) * 1.2
        decline -= enrich_hits * 9
        # 周末/休息日 缓解
        day_of_week = s.temporal_context.get("day_of_week", "")
        if day_of_week in ("saturday", "sunday", "周六", "周日", "週末"):
            decline -= 5
        decline = round(max(0.0, min(decline, 55.0)), 1)
        fulfillment = round(max(0.0, 1.0 - decline / 55), 2)

        return OrganState(
            organ_name="精神血清素/修养满足递质系统",
            metrics={"serotonin_decline_%": decline, "fulfillment_index": fulfillment,
                     "enrichment_signals": enrich_hits, "void_signals": void_hits},
            activation_level=round(decline / 55, 2),
        )

    def _compute_sensation(self, o: OrganState, s: SignalInput) -> tuple[float, Intensity, str]:
        fi = o.metrics["fulfillment_index"]
        decline = o.metrics["serotonin_decline_%"]
        enrich = o.metrics["enrichment_signals"]
        void = o.metrics["void_signals"]

        if decline <= 6: return (0.65, Intensity.LOW, "精神生活丰富充实，内心充盈幸福")
        if decline <= 15: return (0.2, Intensity.MEDIUM, "精神补给略有不足，内心偶有浮躁")
        if decline <= 28: return (-0.15, Intensity.MEDIUM, "精神文化、休闲运动供给不足，内心浮躁空洞")
        if decline <= 40: return (-0.45, Intensity.HIGH, "缺少修养娱乐，精神长期空虚迷茫")
        return (-0.85, Intensity.EXTREME, "精神世界彻底枯竭，深度茫然空洞")
