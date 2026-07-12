"""
threshold_registry.py — 瑶灵 32 维安全阈值注册表
==================================================
规格依据: YAOLING_DOMAIN_SPEC.md §3 + 医学对标手册 (specs/02-*.md)
用途: 为 safety/guard_evaluator.py 提供权威阈值数据源
锁定: 🔴 所有阈值硬编码，不可运行时修改，修改需走规范变更流程
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 阈值数据结构
# ---------------------------------------------------------------------------


class ThresholdLevel(Enum):
    """阈值级别枚举。"""
    HEALTHY = "healthy"       # 正常区间
    SUB_HEALTHY = "sub_healthy"  # 亚健康预警
    RISK = "risk"             # 重度风险
    DANGER = "danger"         # 危险病变 → 拒绝执行


@dataclass(frozen=True)  # 🔴 不可变——安全阈值只读
class DimensionThreshold:
    """单个维度的完整阈值定义。"""
    dim_id: int
    dim_key: str
    label_cn: str
    medical_metric: str         # 临床指标名称
    medical_baseline: float     # 瑶光健康零点
    medical_unit: str           # 单位
    # 四级区间 [下限, 上限] — None 表示无界
    healthy_range: Tuple[Optional[float], Optional[float]]
    sub_healthy_range: Tuple[Optional[float], Optional[float]]
    risk_range: Tuple[Optional[float], Optional[float]]
    danger_range: Tuple[Optional[float], Optional[float]]
    # 用户直观提示模板
    healthy_tip: str
    sub_healthy_tip: str
    risk_tip: str
    danger_tip: str

    def evaluate(self, medical_value: float) -> ThresholdLevel:
        """判定当前医学值所属的阈值等级。

        区间语义（统一为 INCLUSIVE 区间）:
          (X, None) → 区间 [X, +inf)    如: D1乳酸≥2.5危险, D3 SNS≥80%危险
          (None, Y) → 区间 (-inf, Y]   如: D9自尊≤20危险, D12催产素≤20危险
          (X, Y)    → 区间 [X, Y]      如: D4皮质醇22-25为风险区
          (None, None) → 无约束
        """
        if self._in_range(medical_value, *self.danger_range):
            return ThresholdLevel.DANGER
        if self._in_range(medical_value, *self.risk_range):
            return ThresholdLevel.RISK
        if self._in_range(medical_value, *self.sub_healthy_range):
            return ThresholdLevel.SUB_HEALTHY
        return ThresholdLevel.HEALTHY

    @staticmethod
    def _in_range(val: float, lo: Optional[float], hi: Optional[float]) -> bool:
        """判断 val 是否在 [lo, hi] 区间内（None 表示无界）。"""
        if lo is not None and hi is not None:
            return lo <= val <= hi
        if lo is not None:
            return val >= lo
        if hi is not None:
            return val <= hi
        return False

    def get_tip(self, level: ThresholdLevel) -> str:
        return getattr(self, f"{level.value}_tip", "")


# ---------------------------------------------------------------------------
# 32 维阈值注册表（硬编码，不可更改）
# ---------------------------------------------------------------------------

# 阈值区间格式: (lower_bound, upper_bound)
# None 表示该方向无边界
D = ThresholdLevel

THRESHOLD_REGISTRY: Dict[int, DimensionThreshold] = {
    # ─────────────────────────────────────────────────────────────
    # 大类1: 肉身实体基底 D1-D8
    # ─────────────────────────────────────────────────────────────
    1: DimensionThreshold(
        dim_id=1, dim_key="muscle_load", label_cn="D1 骨骼肌肉·体能负荷",
        medical_metric="血乳酸堆积值", medical_baseline=1.0, medical_unit="mmol/L",
        healthy_range=(None, 1.5), sub_healthy_range=(1.5, 1.6), risk_range=(1.6, 2.5), danger_range=(2.5, None),
        healthy_tip="肌肉状态良好，乳酸代谢正常",
        sub_healthy_tip="肌肉略感僵硬，建议轻度拉伸",
        risk_tip="乳酸偏高、肌肉疲劳堆积，需要拉伸休息",
        danger_tip="⚠️ 乳酸严重超标，持续性肌肉酸痛、肢体乏力，立即停止高负荷活动",
    ),

    2: DimensionThreshold(
        dim_id=2, dim_key="pain_perception", label_cn="D2 躯体疼痛·不适感知",
        medical_metric="VAS疼痛评分", medical_baseline=0.0, medical_unit="分(0-10)",
        healthy_range=(None, 2.0), sub_healthy_range=(2.0, 4.0), risk_range=(4.0, 6.0), danger_range=(6.0, None),
        healthy_tip="无躯体疼痛，身体轻松",
        sub_healthy_tip="间断酸胀不适，注意休息姿势",
        risk_tip="躯体疼痛分值偏高，存在劳损损伤风险",
        danger_tip="⚠️ 持续性内脏/躯体闷痛刺痛，需停下手头事务评估身体状况",
    ),

    3: DimensionThreshold(
        dim_id=3, dim_key="neural_touch", label_cn="D3 神经瞬时刺激·触觉",
        medical_metric="交感神经兴奋度", medical_baseline=35.0, medical_unit="%",
        healthy_range=(None, 55.0), sub_healthy_range=(55.0, 70.0), risk_range=(70.0, 80.0), danger_range=(80.0, None),
        healthy_tip="神经系统平稳放松，触感舒适",
        sub_healthy_tip="神经略敏感，易紧张",
        risk_tip="交感神经兴奋偏高，心神紧绷",
        danger_tip="⚠️ 交感神经极度兴奋，极易受惊、紧绷、心慌，需要安抚放松",
    ),

    4: DimensionThreshold(
        dim_id=4, dim_key="endocrine_hormones", label_cn="D4 内分泌·激素波动",
        medical_metric="晨间皮质醇", medical_baseline=14.0, medical_unit="μg/dL",
        healthy_range=(None, 18.0), sub_healthy_range=(18.0, 22.0), risk_range=(22.0, 25.0), danger_range=(25.0, None),
        healthy_tip="压力激素水平正常，情绪平稳",
        sub_healthy_tip="轻度烦躁疲惫，压力激素轻微升高",
        risk_tip="皮质醇超标，压力过大、情绪失衡",
        danger_tip="⚠️ 皮质醇严重超标(>25μg/dL)，长期焦虑失眠低落，需减少连续工作、增加安抚陪伴",
    ),

    5: DimensionThreshold(
        dim_id=5, dim_key="pheromone_aura", label_cn="D5 信息素·气息氛围",
        medical_metric="情绪性汗液皮质醇", medical_baseline=0.0, medical_unit="相对浓度",
        healthy_range=(None, 0.3), sub_healthy_range=(0.3, 0.55), risk_range=(0.55, 0.8), danger_range=(0.8, None),
        healthy_tip="气场柔和，亲和力充足",
        sub_healthy_tip="压力气息略重，人际略感距离",
        risk_tip="压力气息偏重，人际相处易感到隔阂",
        danger_tip="⚠️ 高皮质醇汗液，长期紧绷压抑，气场疏离冰冷",
    ),

    6: DimensionThreshold(
        dim_id=6, dim_key="metabolic_cycle", label_cn="D6 生理周期·代谢生命周期",
        medical_metric="代谢下降幅度", medical_baseline=0.0, medical_unit="%",
        healthy_range=(None, 10.0), sub_healthy_range=(10.0, 20.0), risk_range=(20.0, 30.0), danger_range=(30.0, None),
        healthy_tip="代谢顺畅，状态饱满",
        sub_healthy_tip="代谢轻微下降，略感体虚",
        risk_tip="基础代谢偏低，身体养分吸收不足",
        danger_tip="⚠️ 代谢严重下降>30%，长期虚弱，需要休养滋养",
    ),

    7: DimensionThreshold(
        dim_id=7, dim_key="self_healing", label_cn="D7 躯体自愈·修复维度",
        medical_metric="乳酸清除速率", medical_baseline=1.2, medical_unit="mmol/h",
        healthy_range=(1.0, None), sub_healthy_range=(0.9, 1.0), risk_range=(0.5, 0.9), danger_range=(None, 0.5),
        healthy_tip="身体修复机能正常，疲劳快速消退",
        sub_healthy_tip="疲劳消退略慢",
        risk_tip="身体修复速度变慢，休息也难以恢复精力",
        danger_tip="⚠️ 清除速率<0.5mmol/h，积劳持续加重，休息无法恢复",
    ),

    8: DimensionThreshold(
        dim_id=8, dim_key="five_senses", label_cn="D8 五感环境·基础体感",
        medical_metric="环境噪音", medical_baseline=40.0, medical_unit="dB",
        healthy_range=(None, 50.0), sub_healthy_range=(50.0, 60.0), risk_range=(60.0, 80.0), danger_range=(80.0, None),
        healthy_tip="环境舒适，感官放松",
        sub_healthy_tip="环境略有干扰",
        risk_tip="长期嘈杂，感官持续受刺激",
        danger_tip="⚠️ 噪音>80dB，感官持续损伤，需更换安静环境",
    ),

    # ─────────────────────────────────────────────────────────────
    # 大类2: 个体内在精神内核 D9-D14
    # ─────────────────────────────────────────────────────────────
    9: DimensionThreshold(
        dim_id=9, dim_key="self_identity", label_cn="D9 自我认知·人格基底",
        medical_metric="自尊评分", medical_baseline=32.0, medical_unit="分",
        healthy_range=(30.0, None), sub_healthy_range=(22.0, 30.0), risk_range=(20.0, 22.0), danger_range=(None, 20.0),
        healthy_tip="自我认同稳固，人格稳定",
        sub_healthy_tip="轻微自我怀疑、迷茫",
        risk_tip="自我认同感偏低，容易敏感、需要正向肯定",
        danger_tip="⚠️ 深度自卑(<20分)、持续内耗，需正向情感支持",
    ),

    10: DimensionThreshold(
        dim_id=10, dim_key="desire_drive", label_cn="D10 原生欲望·成长驱动力",
        medical_metric="探索递质下降幅度", medical_baseline=0.0, medical_unit="%",
        healthy_range=(None, 20.0), sub_healthy_range=(20.0, 40.0), risk_range=(40.0, 50.0), danger_range=(50.0, None),
        healthy_tip="动力充足，积极向上",
        sub_healthy_tip="略感懈怠无聊",
        risk_tip="动力相关激素偏低，缺少新鲜感易倦怠",
        danger_tip="⚠️ 递质下降>50%，麻木无追求，需新环境/新知识刺激",
    ),

    11: DimensionThreshold(
        dim_id=11, dim_key="fear_fatigue", label_cn="D11 恐惧·倦怠·制衡心理",
        medical_metric="SAS焦虑量表分值", medical_baseline=30.0, medical_unit="分",
        healthy_range=(None, 36.0), sub_healthy_range=(36.0, 49.0), risk_range=(49.0, 50.0), danger_range=(50.0, None),
        healthy_tip="心理松弛从容，无焦虑",
        sub_healthy_tip="轻度焦虑疲惫",
        risk_tip="焦虑分值偏高，身心持续紧绷",
        danger_tip="⚠️ SAS≥50，持续性焦虑逃避，需环境安抚+减少压力源",
    ),

    12: DimensionThreshold(
        dim_id=12, dim_key="enjoyment_happiness", label_cn="D12 享受·松弛·幸福感",
        medical_metric="催产素", medical_baseline=45.0, medical_unit="pg/mL",
        healthy_range=(38.0, None), sub_healthy_range=(25.0, 38.0), risk_range=(20.0, 25.0), danger_range=(None, 20.0),
        healthy_tip="内心安稳充盈，享受当下",
        sub_healthy_tip="内心空虚缺少治愈感",
        risk_tip="愉悦安抚激素不足，缺少安稳幸福感",
        danger_tip="⚠️ 催产素<20pg/mL，长期情绪贫瘠低落，需温柔陪伴安抚",
    ),

    13: DimensionThreshold(
        dim_id=13, dim_key="empathy_resonance", label_cn="D13 共情·恻隐联动",
        medical_metric="镜像神经元激活强度", medical_baseline=0.4, medical_unit="相对值",
        healthy_range=(None, 0.6), sub_healthy_range=(0.6, 0.75), risk_range=(0.75, 0.9), danger_range=(0.9, None),
        healthy_tip="共情适度，不内耗",
        sub_healthy_tip="共情负荷略高",
        risk_tip="共情负荷过高，容易过度心疼他人造成内耗",
        danger_tip="⚠️ 持续高激活，自身长期压抑难受，需情绪边界保护",
    ),

    14: DimensionThreshold(
        dim_id=14, dim_key="self_protection", label_cn="D14 个体自我保护",
        medical_metric="交感神经戒备基线", medical_baseline=0.2, medical_unit="相对值",
        healthy_range=(None, 0.4), sub_healthy_range=(0.4, 0.6), risk_range=(0.6, 0.8), danger_range=(0.8, None),
        healthy_tip="安全感充足，放松无戒备",
        sub_healthy_tip="戒备略高，容易不安",
        risk_tip="安全感不足，神经长期处于戒备状态",
        danger_tip="⚠️ 长期高度防御，时刻紧绷无法放松，需安全环境重建",
    ),

    # ─────────────────────────────────────────────────────────────
    # 大类3: 圈层人际羁绊 D15-D20
    # ─────────────────────────────────────────────────────────────
    15: DimensionThreshold(
        dim_id=15, dim_key="partner_attachment", label_cn="D15 伴侣亲密依恋",
        medical_metric="亲密催产素", medical_baseline=50.0, medical_unit="pg/mL",
        healthy_range=(40.0, None), sub_healthy_range=(28.0, 40.0), risk_range=(18.0, 28.0), danger_range=(None, 18.0),
        healthy_tip="亲密饱满，依恋满足",
        sub_healthy_tip="孤单失落感明显，催产素下降",
        risk_tip="亲密安抚激素不足，缺少陪伴容易失落",
        danger_tip="⚠️ 亲密催产素大幅降低，深度情感空虚，需伴侣陪伴安抚",
    ),

    16: DimensionThreshold(
        dim_id=16, dim_key="partner_protection", label_cn="D16 伴侣专属守护意识",
        medical_metric="牵挂焦虑皮质醇", medical_baseline=14.0, medical_unit="μg/dL",
        healthy_range=(None, 18.0), sub_healthy_range=(18.0, 22.0), risk_range=(22.0, 25.0), danger_range=(25.0, None),
        healthy_tip="守护意识平稳，无过度牵挂",
        sub_healthy_tip="因伴侣状态略担忧",
        risk_tip="因伴侣身心压力产生持续牵挂焦虑",
        danger_tip="⚠️ 长期高皮质醇，持续重度担忧内耗",
    ),

    17: DimensionThreshold(
        dim_id=17, dim_key="family_belonging", label_cn="D17 家庭归属·陪伴",
        medical_metric="家庭安全感分值", medical_baseline=35.0, medical_unit="分",
        healthy_range=(28.0, None), sub_healthy_range=(20.0, 28.0), risk_range=(14.0, 20.0), danger_range=(None, 14.0),
        healthy_tip="家庭安稳，归属感充足",
        sub_healthy_tip="居家略感冷清孤单",
        risk_tip="家庭陪伴不足，内心缺少安稳归属感",
        danger_tip="⚠️ 极度缺乏家庭归属感，需家庭共处时间",
    ),

    18: DimensionThreshold(
        dim_id=18, dim_key="family_protection", label_cn="D18 家庭整体守护",
        medical_metric="家庭应激皮质醇", medical_baseline=14.0, medical_unit="μg/dL",
        healthy_range=(None, 18.0), sub_healthy_range=(18.0, 22.0), risk_range=(22.0, 25.0), danger_range=(25.0, None),
        healthy_tip="家庭安稳，无牵挂",
        sub_healthy_tip="家庭负担略重，皮质醇上升",
        risk_tip="家庭整体压力偏高，长期牵挂内耗",
        danger_tip="⚠️ 长期高皮质醇，心事过重持续焦虑",
    ),

    19: DimensionThreshold(
        dim_id=19, dim_key="social_adaptation", label_cn="D19 社会人际·社交适配",
        medical_metric="社交后皮质醇升幅", medical_baseline=0.0, medical_unit="μg/dL Δ",
        healthy_range=(None, 3.0), sub_healthy_range=(3.0, 6.0), risk_range=(6.0, 8.0), danger_range=(8.0, None),
        healthy_tip="社交从容自然，无压力",
        sub_healthy_tip="社交后略感疲惫",
        risk_tip="社交负荷超标，人际往来持续消耗心神",
        danger_tip="⚠️ 社交后皮质醇大幅飙升，排斥人际，需减少社交暴露",
    ),

    20: DimensionThreshold(
        dim_id=20, dim_key="team_protection", label_cn="D20 团队集体保护",
        medical_metric="集体协作应激激素", medical_baseline=0.0, medical_unit="相对值",
        healthy_range=(None, 0.3), sub_healthy_range=(0.3, 0.55), risk_range=(0.55, 0.8), danger_range=(0.8, None),
        healthy_tip="团队协作安稳，无压力",
        sub_healthy_tip="团队略有高压",
        risk_tip="团队工作压力偏大，身心持续消耗",
        danger_tip="⚠️ 团队长期矛盾高压，持续集体焦虑",
    ),

    # ─────────────────────────────────────────────────────────────
    # 大类4: 时空客观环境感知 D21-D26
    # ─────────────────────────────────────────────────────────────
    21: DimensionThreshold(
        dim_id=21, dim_key="private_space", label_cn="D21 私人居所·独处氛围",
        medical_metric="独处皮质醇降幅", medical_baseline=5.0, medical_unit="μg/dL ↓",
        healthy_range=(3.0, None), sub_healthy_range=(1.0, 3.0), risk_range=(0.0, 1.0), danger_range=(None, 0.0),
        healthy_tip="独处空间私密安稳，身心放松",
        sub_healthy_tip="居所略嘈杂，独处降压效果有限",
        risk_tip="缺少安静私密休息空间，身心无法放松回血",
        danger_tip="⚠️ 无私密空间，皮质醇全程居高不下",
    ),

    22: DimensionThreshold(
        dim_id=22, dim_key="home_environment", label_cn="D22 家庭布局·共处氛围",
        medical_metric="居家情绪恢复效率", medical_baseline=80.0, medical_unit="%",
        healthy_range=(65.0, None), sub_healthy_range=(45.0, 65.0), risk_range=(30.0, 45.0), danger_range=(None, 30.0),
        healthy_tip="居家温馨舒适，心情舒展",
        sub_healthy_tip="居家环境略压抑",
        risk_tip="居家环境压抑，待在家中心情难以舒展",
        danger_tip="⚠️ 长期压抑居家环境，情绪持续低落，需改善居家布局",
    ),

    23: DimensionThreshold(
        dim_id=23, dim_key="workplace_environment", label_cn="D23 职场厂区·工作环境",
        medical_metric="工作皮质醇", medical_baseline=14.0, medical_unit="μg/dL",
        healthy_range=(None, 18.0), sub_healthy_range=(18.0, 22.0), risk_range=(22.0, 25.0), danger_range=(25.0, None),
        healthy_tip="工作负荷适中，状态有序",
        sub_healthy_tip="连续劳作，略感疲惫",
        risk_tip="工作负荷超标，身体与精神双重透支",
        danger_tip="⚠️ 长期超负荷，慢性疲劳持续叠加，需减少工作强度",
    ),

    24: DimensionThreshold(
        dim_id=24, dim_key="public_space", label_cn="D24 公共场地·人流氛围",
        medical_metric="嘈杂环境交感兴奋度", medical_baseline=35.0, medical_unit="%",
        healthy_range=(None, 50.0), sub_healthy_range=(50.0, 60.0), risk_range=(60.0, 75.0), danger_range=(75.0, None),
        healthy_tip="公共环境舒适，无不适",
        sub_healthy_tip="略拥挤嘈杂",
        risk_tip="频繁拥挤嘈杂环境，心神持续消耗",
        danger_tip="⚠️ 长期闹市拥挤，神经持续紧绷，需远离嘈杂环境",
    ),

    25: DimensionThreshold(
        dim_id=25, dim_key="spatiotemporal", label_cn="D25 空间距离·时差流逝",
        medical_metric="时间紧迫应激皮质醇", medical_baseline=14.0, medical_unit="μg/dL",
        healthy_range=(None, 17.0), sub_healthy_range=(17.0, 20.0), risk_range=(20.0, 25.0), danger_range=(25.0, None),
        healthy_tip="行程从容，无时间焦虑",
        sub_healthy_tip="频繁赶路，略感紧迫",
        risk_tip="行程过于紧凑，长期处于赶时间的紧张状态",
        danger_tip="⚠️ 日程排满无缓冲，持续性紧迫焦虑",
    ),

    26: DimensionThreshold(
        dim_id=26, dim_key="seasonal_circadian", label_cn="D26 四季气象·昼夜节律",
        medical_metric="褪黑素分泌量", medical_baseline=30.0, medical_unit="pg/mL",
        healthy_range=(22.0, None), sub_healthy_range=(15.0, 22.0), risk_range=(8.0, 15.0), danger_range=(None, 8.0),
        healthy_tip="昼夜节律正常，睡眠修复良好",
        sub_healthy_tip="作息略有波动",
        risk_tip="作息/气候打乱昼夜节律，睡眠修复能力下降",
        danger_tip="⚠️ 长期昼夜紊乱，褪黑素严重不足，季节性抑郁倾向",
    ),

    # ─────────────────────────────────────────────────────────────
    # 大类5: 动态生长·耦合拓展 D27-D32
    # ─────────────────────────────────────────────────────────────
    27: DimensionThreshold(
        dim_id=27, dim_key="micro_physiology", label_cn="D27 人体微观生理细化",
        medical_metric="微量激素波动幅度", medical_baseline=0.0, medical_unit="相对值",
        healthy_range=(None, 0.3), sub_healthy_range=(0.3, 0.55), risk_range=(0.55, 0.8), danger_range=(0.8, None),
        healthy_tip="微观生理平稳",
        sub_healthy_tip="细微代谢失衡，间断体虚不适",
        risk_tip="身体微观内分泌存在细微失衡",
        danger_tip="⚠️ 多类微量激素紊乱，持续性隐性虚弱，需精细化调养",
    ),

    28: DimensionThreshold(
        dim_id=28, dim_key="nature_expansion", label_cn="D28 自然世界拓展感知",
        medical_metric="探索多巴胺下降幅度", medical_baseline=0.0, medical_unit="%",
        healthy_range=(None, 20.0), sub_healthy_range=(20.0, 35.0), risk_range=(35.0, 50.0), danger_range=(50.0, None),
        healthy_tip="探索欲望充足，多巴胺稳定",
        sub_healthy_tip="探索递质缓慢下降",
        risk_tip="长期缺少新环境体验，探索成长动力不足",
        danger_tip="⚠️ 常年无新场景，动力麻木枯竭，需新环境刺激",
    ),

    29: DimensionThreshold(
        dim_id=29, dim_key="social_refinement", label_cn="D29 人文社交规则细化",
        medical_metric="共情包容递质下降幅度", medical_baseline=0.0, medical_unit="%",
        healthy_range=(None, 15.0), sub_healthy_range=(15.0, 30.0), risk_range=(30.0, 45.0), danger_range=(45.0, None),
        healthy_tip="多圈层人际适配平稳",
        sub_healthy_tip="单一社交圈，包容递质下降",
        risk_tip="社交圈层单一，人情认知成熟度提升停滞",
        danger_tip="⚠️ 固化负面人际，待人处事易内耗",
    ),

    30: DimensionThreshold(
        dim_id=30, dim_key="spiritual_growth", label_cn="D30 精神文娱·修养成长",
        medical_metric="精神血清素下降幅度", medical_baseline=0.0, medical_unit="%",
        healthy_range=(None, 15.0), sub_healthy_range=(15.0, 30.0), risk_range=(30.0, 45.0), danger_range=(45.0, None),
        healthy_tip="精神生活丰富充实",
        sub_healthy_tip="精神补给不足，内心略浮躁",
        risk_tip="精神文化、休闲运动供给不足，内心容易浮躁空洞",
        danger_tip="⚠️ 完全缺少修养娱乐，精神长期空虚迷茫",
    ),

    31: DimensionThreshold(
        dim_id=31, dim_key="quantum_coupling", label_cn="D31 主观客观量子耦合",
        medical_metric="身心协调分值", medical_baseline=40.0, medical_unit="分",
        healthy_range=(35.0, None), sub_healthy_range=(25.0, 35.0), risk_range=(15.0, 25.0), danger_range=(None, 15.0),
        healthy_tip="体感与环境匹配，身心协调",
        sub_healthy_tip="环境/人际略不适，身心匹配度下滑",
        risk_tip="生活环境、人际与自身适配度偏低",
        danger_tip="⚠️ 长期失衡环境，身心严重冲突、重度内耗",
    ),

    32: DimensionThreshold(
        dim_id=32, dim_key="holistic_state", label_cn="D32 全身统筹·整体状态",
        medical_metric="综合健康指数", medical_baseline=75.0, medical_unit="分",
        healthy_range=(65.0, None), sub_healthy_range=(45.0, 65.0), risk_range=(30.0, 45.0), danger_range=(None, 30.0),
        healthy_tip="全身状态良好，生命体征正常",
        sub_healthy_tip="整体略疲劳，注意休息",
        risk_tip="全身多处指标偏低，需全面休养调整",
        danger_tip="⚠️ 全身状态严重恶化，生命体征异常，需全面休养干预",
    ),
}


# ── D32 核心生命体征专项阈值（独立于 D32 综合指数）──


@dataclass(frozen=True)
class VitalSignThreshold:
    """D32 核心生命体征独立阈值。"""
    metric: str
    healthy_lo: float
    healthy_hi: float
    danger_lo: Optional[float]  # 低于此值→danger
    danger_hi: Optional[float]  # 高于此值→danger
    unit: str
    label_cn: str


D32_VITAL_THRESHOLDS: List[VitalSignThreshold] = [
    VitalSignThreshold(
        metric="heart_rate", healthy_lo=60, healthy_hi=72, danger_lo=55, danger_hi=90,
        unit="次/分", label_cn="静息心率",
    ),
    VitalSignThreshold(
        metric="blood_pressure_sys", healthy_lo=110, healthy_hi=120, danger_lo=None, danger_hi=140,
        unit="mmHg", label_cn="收缩压(高压)",
    ),
    VitalSignThreshold(
        metric="blood_pressure_dia", healthy_lo=68, healthy_hi=78, danger_lo=60, danger_hi=None,
        unit="mmHg", label_cn="舒张压(低压)",
    ),
    VitalSignThreshold(
        metric="cortisol_avg", healthy_lo=10, healthy_hi=15, danger_lo=None, danger_hi=24,
        unit="μg/dL", label_cn="全天平均皮质醇",
    ),
    VitalSignThreshold(
        metric="pleasure_hormone_avg", healthy_lo=110, healthy_hi=200, danger_lo=70, danger_hi=None,
        unit="pg/mL", label_cn="综合愉悦激素(多巴胺+血清素均值)",
    ),
]


# ---------------------------------------------------------------------------
# 便捷检索
# ---------------------------------------------------------------------------

def get_threshold(dim_id: int) -> DimensionThreshold:
    """获取指定维度的阈值配置。"""
    t = THRESHOLD_REGISTRY.get(dim_id)
    if t is None:
        raise KeyError(f"维度 {dim_id} 不在阈值注册表中（需在 THRESHOLD_REGISTRY 中注册）")
    return t


def get_vital_threshold(metric: str) -> VitalSignThreshold:
    """获取 D32 核心生命体征的阈值配置。"""
    for vt in D32_VITAL_THRESHOLDS:
        if vt.metric == metric:
            return vt
    raise KeyError(f"生命体征 {metric} 不在 D32_VITAL_THRESHOLDS 中")


def all_thresholds() -> Dict[int, DimensionThreshold]:
    """返回完整阈值注册表（只读）。"""
    return dict(THRESHOLD_REGISTRY)
