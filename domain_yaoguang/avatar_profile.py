"""
avatar_profile.py — 瑶光·生理年龄-性别-经验-发育阶段参数矩阵
==============================================================
为所有32维客观通道提供生物-人口学差异化基线。

真人参考依据:
  - 发育内分泌学: Tanner分期, 下丘脑-垂体-性腺轴成熟曲线
  - 运动生理学: 年龄分组VO2max, 肌力峰值年龄, 乳酸清除率年龄曲线
  - 神经发育: 前额叶髓鞘化25岁完成, 杏仁核-前额叶调控发育
  - 疼痛生理: 年龄/性别痛阈差异 (Fillingim 2009 meta-analysis)
  - 性反应生理: Masters & Johnson 人类性反应周期, Kinsey年龄段差异
  - 衰老生物学: 端粒缩短, 线粒体衰退, 生长激素/IGF-1下降曲线
  - 经验神经可塑性: 首次事件杏仁核激活↑, 重复后前额叶调控↑ (LeDoux 2000)

铁律: 全部规则公式, 禁止LLM生成浮点。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import math


# ===================================================================
# 枚举
# ===================================================================

class AgeGroup(str, Enum):
    """生理年龄分组 (基于发育生物学分期)"""
    CHILD = "child"               # 8-12岁  青春期前
    EARLY_ADOLESCENT = "early_adolescent"  # 13-14岁 青春期早期
    LATE_ADOLESCENT = "late_adolescent"    # 15-17岁 青春期晚期
    YOUNG_ADULT = "young_adult"           # 18-25岁 成年早期
    MATURE = "mature"                     # 26-45岁 成熟期
    MIDDLE_AGE = "middle_age"            # 46-60岁 中年期

    @property
    def numeric_age(self) -> float:
        return {AgeGroup.CHILD: 10, AgeGroup.EARLY_ADOLESCENT: 14,
                AgeGroup.LATE_ADOLESCENT: 16, AgeGroup.YOUNG_ADULT: 22,
                AgeGroup.MATURE: 35, AgeGroup.MIDDLE_AGE: 53}[self]

    @property
    def is_adolescent(self) -> bool:
        return self in (AgeGroup.EARLY_ADOLESCENT, AgeGroup.LATE_ADOLESCENT)

    @property
    def is_prepubescent(self) -> bool:
        return self == AgeGroup.CHILD

    @property
    def is_sexually_mature(self) -> bool:
        return self not in (AgeGroup.CHILD, AgeGroup.EARLY_ADOLESCENT)

    @property
    def frontal_lobe_maturity(self) -> float:
        """前额叶成熟度 0-1: 25岁≈1.0"""
        return {AgeGroup.CHILD: 0.35, AgeGroup.EARLY_ADOLESCENT: 0.45,
                AgeGroup.LATE_ADOLESCENT: 0.60, AgeGroup.YOUNG_ADULT: 0.85,
                AgeGroup.MATURE: 1.0, AgeGroup.MIDDLE_AGE: 1.0}[self]

    @property
    def recovery_rate_factor(self) -> float:
        """恢复速率 (相对25岁基准=1.0)"""
        return {AgeGroup.CHILD: 1.4, AgeGroup.EARLY_ADOLESCENT: 1.25,
                AgeGroup.LATE_ADOLESCENT: 1.15, AgeGroup.YOUNG_ADULT: 1.05,
                AgeGroup.MATURE: 0.95, AgeGroup.MIDDLE_AGE: 0.75}[self]


class BiologicalSex(str, Enum):
    MALE = "male"
    FEMALE = "female"

    @property
    def testosterone_baseline_ng_dl(self) -> float:
        """血清总睾酮基线 ng/dL"""
        return 600.0 if self == BiologicalSex.MALE else 40.0

    @property
    def estrogen_baseline_pg_ml(self) -> float:
        """雌二醇基线 pg/mL"""
        return 30.0 if self == BiologicalSex.MALE else 120.0

    @property
    def muscle_mass_pct(self) -> float:
        """骨骼肌占比 %"""
        return 42.0 if self == BiologicalSex.MALE else 33.0

    @property
    def bmr_factor(self) -> float:
        """BMR修正系数"""
        return 1.0 if self == BiologicalSex.MALE else 0.85

    @property
    def pain_threshold_factor(self) -> float:
        """疼痛阈值修正 (女性较低)"""
        return 1.0 if self == BiologicalSex.MALE else 0.85


class ExperienceLevel(str, Enum):
    """经验等级 (领域独立, 每条维度可不同)"""
    NAIVE = "naive"           # 从未经历 — 杏仁核高激活 + 多巴胺新奇响应
    NOVICE = "novice"         # 1-3次经历 — 学习曲线陡峭
    EXPERIENCED = "experienced"  # 多次经历 — 前额叶调控为主, 程序化
    HABITUATED = "habituated"    # 完全适应 — 最低情绪波动, 自动化


class ExperienceDomain(str, Enum):
    """经验领域 (每个领域独立追踪经验等级)"""
    SEXUAL = "sexual"                    # 性行为/亲密
    SOCIAL_LARGE_GROUP = "social_large"  # 大型社交场合
    PUBLIC_SPEAKING = "public_speaking"  # 公开演讲
    EXERCISE = "exercise"                # 体育锻炼
    COMMUTE = "commute"                  # 通勤
    COOKING = "cooking"                  # 烹饪
    MEDICAL_PROCEDURE = "medical"        # 医疗程序
    TRAVEL = "travel"                    # 长途旅行
    CONFLICT = "conflict"                # 人际冲突处理
    PARENTING = "parenting"              # 育儿
    LOSS = "loss"                        # 丧失/哀伤处理


@dataclass
class PhysicalTraits:
    """身体特征参数"""
    height_cm: float = 165.0
    weight_kg: float = 60.0
    body_fat_pct: float = 22.0
    rest_hr_bpm: float = 66.0       # 静息心率
    vo2max_ml_kg_min: float = 38.0   # 最大摄氧量
    flexibility_score: float = 0.6   # 柔韧性 0-1
    chronic_conditions: List[str] = field(default_factory=list)
    medications: List[str] = field(default_factory=list)


# ===================================================================
# 经验追踪器
# ===================================================================

@dataclass
class ExperienceTracker:
    """跨领域的经验追踪——每个领域独立记录次数和时间。

    经验影响:
      naive → 新皮质/海马高编码, 杏仁核高激活, 多巴胺新奇响应↑
      experienced → 基底节程序化, 前额叶调控为主, 皮质醇↓
      habituated → 自动化, 情绪中性, 激素基本无波动
    """
    records: Dict[ExperienceDomain, Tuple[ExperienceLevel, int, float]] = field(default_factory=dict)
    # domain → (level, count, last_timestamp_ms)

    def get_level(self, domain: ExperienceDomain) -> ExperienceLevel:
        entry = self.records.get(domain)
        if entry is None:
            return ExperienceLevel.NAIVE
        return entry[0]

    def get_count(self, domain: ExperienceDomain) -> int:
        entry = self.records.get(domain)
        return entry[1] if entry else 0

    def record(self, domain: ExperienceDomain, timestamp_ms: int) -> None:
        """记录一次经验"""
        entry = self.records.get(domain)
        if entry is None:
            self.records[domain] = (ExperienceLevel.NOVICE, 1, timestamp_ms)
        else:
            level, count, _ = entry
            new_count = count + 1
            new_level = level
            if new_count >= 20:
                new_level = ExperienceLevel.HABITUATED
            elif new_count >= 5:
                new_level = ExperienceLevel.EXPERIENCED
            elif new_count >= 1:
                new_level = ExperienceLevel.NOVICE
            self.records[domain] = (new_level, new_count, timestamp_ms)

    def to_dict(self) -> Dict[str, Any]:
        return {
            domain.value: {"level": level.value, "count": count, "last_ts": last_ts}
            for domain, (level, count, last_ts) in self.records.items()
        }


# ===================================================================
# Avatar 完整生物-人口学画像
# ===================================================================

@dataclass
class AvatarProfile:
    """
    完整生理-心理-经验画像。

    这是瑶光32维客观计算的核心差异化参数——
    同一场景下, 14岁少女和35岁成熟男性的D1-D32输出完全不同。
    """
    age_group: AgeGroup = AgeGroup.MATURE
    biological_sex: BiologicalSex = BiologicalSex.MALE
    physical: PhysicalTraits = field(default_factory=PhysicalTraits)
    experience: ExperienceTracker = field(default_factory=ExperienceTracker)

    # 心理特质 (0-1)
    trait_openness: float = 0.5        # 开放性
    trait_conscientiousness: float = 0.5
    trait_extraversion: float = 0.5
    trait_agreeableness: float = 0.5
    trait_neuroticism: float = 0.5     # 情绪稳定性 (反向)

    # 发育阶段标记
    tanner_stage: int = 5             # 1-5
    menarche_age: Optional[float] = None  # 初潮年龄 (仅女性)
    first_sexual_experience_age: Optional[float] = None

    # 关系状态
    relationship_status: str = "single"  # single/partnered/married/complicated
    has_children: bool = False
    children_ages: List[float] = field(default_factory=list)

    @property
    def numeric_age(self) -> float:
        return self.age_group.numeric_age

    # ------------------------------------------------------------------
    # 32维 × 年龄修正系数
    # ------------------------------------------------------------------

    def get_dimension_age_modifier(self, dim_id: int) -> float:
        """
        返回年龄对该维度的修正系数 (-1.0 ~ +1.0)。

        正值=年龄优势 (如经验丰富→D9自我认知↑)
        负值=年龄劣势 (如恢复慢→D7自愈↓)
        """
        ag = self.age_group
        sex = self.biological_sex

        modifiers: Dict[int, float] = {}

        # ── D1 骨骼肌肉 ──
        # 肌力峰值: 25-30岁, 儿童/青少年=0.6-0.8, 中年=0.85
        muscle_map = {AgeGroup.CHILD: -0.20, AgeGroup.EARLY_ADOLESCENT: -0.10,
                      AgeGroup.LATE_ADOLESCENT: 0.0, AgeGroup.YOUNG_ADULT: 0.05,
                      AgeGroup.MATURE: 0.0, AgeGroup.MIDDLE_AGE: -0.15}
        modifiers[1] = muscle_map.get(ag, 0.0)

        # ── D2 疼痛 ──
        # 儿童痛阈低, 女性痛阈低, 中年慢性疼痛倾向↑
        pain_base = {AgeGroup.CHILD: -0.15, AgeGroup.EARLY_ADOLESCENT: -0.10,
                     AgeGroup.LATE_ADOLESCENT: -0.05, AgeGroup.YOUNG_ADULT: 0.0,
                     AgeGroup.MATURE: -0.05, AgeGroup.MIDDLE_AGE: -0.15}
        modifiers[2] = pain_base.get(ag, 0.0) + (-0.05 if sex == BiologicalSex.FEMALE else 0)

        # ── D3 神经触觉 ──
        # 儿童感官敏锐↑, 中年感官衰退↓
        modifiers[3] = {AgeGroup.CHILD: 0.10, AgeGroup.EARLY_ADOLESCENT: 0.05,
                        AgeGroup.LATE_ADOLESCENT: 0.0, AgeGroup.YOUNG_ADULT: 0.0,
                        AgeGroup.MATURE: -0.03, AgeGroup.MIDDLE_AGE: -0.10}[ag]

        # ── D4 内分泌 ──
        # 青春期激素波动最大 (负向=不稳定), 成熟期最稳定, 中年性激素下降
        modifiers[4] = {AgeGroup.CHILD: 0.05, AgeGroup.EARLY_ADOLESCENT: -0.15,
                        AgeGroup.LATE_ADOLESCENT: -0.10, AgeGroup.YOUNG_ADULT: 0.0,
                        AgeGroup.MATURE: 0.05, AgeGroup.MIDDLE_AGE: -0.10}[ag]

        # ── D5 信息素 ──
        # 青春期信息素活跃↑, 中年后下降
        modifiers[5] = {AgeGroup.CHILD: -0.05, AgeGroup.EARLY_ADOLESCENT: 0.10,
                        AgeGroup.LATE_ADOLESCENT: 0.15, AgeGroup.YOUNG_ADULT: 0.10,
                        AgeGroup.MATURE: 0.05, AgeGroup.MIDDLE_AGE: -0.05}[ag]

        # ── D6 代谢周期 ──
        # BMR随年龄下降: 每10年-2%, 青春期最高
        modifiers[6] = {AgeGroup.CHILD: 0.10, AgeGroup.EARLY_ADOLESCENT: 0.15,
                        AgeGroup.LATE_ADOLESCENT: 0.10, AgeGroup.YOUNG_ADULT: 0.05,
                        AgeGroup.MATURE: 0.0, AgeGroup.MIDDLE_AGE: -0.10}[ag]

        # ── D7 躯体自愈 ──
        # 恢复速率: 儿童>青少年>成年>中年
        modifiers[7] = {AgeGroup.CHILD: 0.15, AgeGroup.EARLY_ADOLESCENT: 0.10,
                        AgeGroup.LATE_ADOLESCENT: 0.05, AgeGroup.YOUNG_ADULT: 0.03,
                        AgeGroup.MATURE: 0.0, AgeGroup.MIDDLE_AGE: -0.12}[ag]

        # ── D8 五感环境 ── 年龄影响不大
        modifiers[8] = 0.0

        # ── D9 自我认知 ──
        # 青春期=身份探索期→自我认同不稳定; 成熟期=稳定; 经验→正
        modifiers[9] = {AgeGroup.CHILD: 0.05, AgeGroup.EARLY_ADOLESCENT: -0.15,
                        AgeGroup.LATE_ADOLESCENT: -0.10, AgeGroup.YOUNG_ADULT: -0.05,
                        AgeGroup.MATURE: 0.10, AgeGroup.MIDDLE_AGE: 0.10}[ag]

        # ── D10 探索欲望 ──
        # 青春期/青年=最高; 中年后=习惯化下降
        modifiers[10] = {AgeGroup.CHILD: 0.15, AgeGroup.EARLY_ADOLESCENT: 0.20,
                         AgeGroup.LATE_ADOLESCENT: 0.15, AgeGroup.YOUNG_ADULT: 0.10,
                         AgeGroup.MATURE: 0.0, AgeGroup.MIDDLE_AGE: -0.05}[ag]

        # ── D11 恐惧/焦虑 ──
        # 儿童=想象力丰富→恐惧↑; 青春期=社交焦虑↑; 成熟=稳定
        modifiers[11] = {AgeGroup.CHILD: -0.10, AgeGroup.EARLY_ADOLESCENT: -0.15,
                         AgeGroup.LATE_ADOLESCENT: -0.10, AgeGroup.YOUNG_ADULT: -0.05,
                         AgeGroup.MATURE: 0.0, AgeGroup.MIDDLE_AGE: -0.05}[ag]

        # ── D12 幸福感 ──
        # 儿童=纯真幸福; 青春期=情绪起伏; 中年=稳定/U型曲线
        modifiers[12] = {AgeGroup.CHILD: 0.15, AgeGroup.EARLY_ADOLESCENT: -0.05,
                         AgeGroup.LATE_ADOLESCENT: 0.0, AgeGroup.YOUNG_ADULT: 0.05,
                         AgeGroup.MATURE: 0.05, AgeGroup.MIDDLE_AGE: 0.08}[ag]

        # ── D13 共情 ──
        # 随年龄和经验增长: 儿童自我中心→成年共情成熟
        modifiers[13] = {AgeGroup.CHILD: -0.10, AgeGroup.EARLY_ADOLESCENT: -0.05,
                         AgeGroup.LATE_ADOLESCENT: 0.0, AgeGroup.YOUNG_ADULT: 0.05,
                         AgeGroup.MATURE: 0.10, AgeGroup.MIDDLE_AGE: 0.10}[ag]

        # ── D14 自我保护 ──
        # 儿童=依赖; 青春期=探索+脆弱; 成年=稳定
        modifiers[14] = {AgeGroup.CHILD: -0.10, AgeGroup.EARLY_ADOLESCENT: -0.10,
                         AgeGroup.LATE_ADOLESCENT: -0.05, AgeGroup.YOUNG_ADULT: 0.0,
                         AgeGroup.MATURE: 0.05, AgeGroup.MIDDLE_AGE: 0.08}[ag]

        # ── D15 伴侣依恋 ──
        # 青春期=初次浪漫依恋→强烈; 成熟=深度依恋; 中年=稳定性依恋
        modifiers[15] = {AgeGroup.CHILD: -0.20, AgeGroup.EARLY_ADOLESCENT: 0.15,
                         AgeGroup.LATE_ADOLESCENT: 0.10, AgeGroup.YOUNG_ADULT: 0.10,
                         AgeGroup.MATURE: 0.05, AgeGroup.MIDDLE_AGE: 0.0}[ag]

        # ── D16 伴侣守护 ──
        modifiers[16] = {AgeGroup.CHILD: -0.20, AgeGroup.EARLY_ADOLESCENT: -0.10,
                         AgeGroup.LATE_ADOLESCENT: 0.0, AgeGroup.YOUNG_ADULT: 0.05,
                         AgeGroup.MATURE: 0.10, AgeGroup.MIDDLE_AGE: 0.10}[ag]

        # ── D17 家庭归属 ──
        modifiers[17] = {AgeGroup.CHILD: 0.15, AgeGroup.EARLY_ADOLESCENT: -0.05,
                         AgeGroup.LATE_ADOLESCENT: -0.05, AgeGroup.YOUNG_ADULT: 0.0,
                         AgeGroup.MATURE: 0.10, AgeGroup.MIDDLE_AGE: 0.10}[ag]

        # ── D18 家庭守护 ──
        modifiers[18] = {AgeGroup.CHILD: -0.15, AgeGroup.EARLY_ADOLESCENT: -0.10,
                         AgeGroup.LATE_ADOLESCENT: -0.05, AgeGroup.YOUNG_ADULT: 0.0,
                         AgeGroup.MATURE: 0.10, AgeGroup.MIDDLE_AGE: 0.15}[ag]

        # ── D19 社交适配 ──
        # 青春期=社交焦虑高峰; 成熟=社交技能成熟
        modifiers[19] = {AgeGroup.CHILD: 0.0, AgeGroup.EARLY_ADOLESCENT: -0.15,
                         AgeGroup.LATE_ADOLESCENT: -0.10, AgeGroup.YOUNG_ADULT: -0.05,
                         AgeGroup.MATURE: 0.05, AgeGroup.MIDDLE_AGE: 0.05}[ag]

        # ── D20 团队保护 ──
        modifiers[20] = {AgeGroup.CHILD: -0.10, AgeGroup.EARLY_ADOLESCENT: -0.05,
                         AgeGroup.LATE_ADOLESCENT: 0.0, AgeGroup.YOUNG_ADULT: 0.05,
                         AgeGroup.MATURE: 0.10, AgeGroup.MIDDLE_AGE: 0.10}[ag]

        # ── D21-D26 时空环境: 年龄影响不大 ──
        for d in range(21, 27):
            modifiers[d] = 0.0

        # ── D27 微观生理 ──
        modifiers[27] = {AgeGroup.CHILD: 0.05, AgeGroup.EARLY_ADOLESCENT: 0.03,
                         AgeGroup.LATE_ADOLESCENT: 0.0, AgeGroup.YOUNG_ADULT: 0.0,
                         AgeGroup.MATURE: -0.03, AgeGroup.MIDDLE_AGE: -0.10}[ag]

        # ── D28 自然拓展 ──
        modifiers[28] = {AgeGroup.CHILD: 0.20, AgeGroup.EARLY_ADOLESCENT: 0.15,
                         AgeGroup.LATE_ADOLESCENT: 0.10, AgeGroup.YOUNG_ADULT: 0.10,
                         AgeGroup.MATURE: 0.0, AgeGroup.MIDDLE_AGE: -0.05}[ag]

        # ── D29 人文社交 ──
        modifiers[29] = {AgeGroup.CHILD: -0.10, AgeGroup.EARLY_ADOLESCENT: -0.05,
                         AgeGroup.LATE_ADOLESCENT: 0.0, AgeGroup.YOUNG_ADULT: 0.05,
                         AgeGroup.MATURE: 0.10, AgeGroup.MIDDLE_AGE: 0.15}[ag]

        # ── D30 精神文娱 ──
        modifiers[30] = {AgeGroup.CHILD: 0.10, AgeGroup.EARLY_ADOLESCENT: 0.05,
                         AgeGroup.LATE_ADOLESCENT: 0.05, AgeGroup.YOUNG_ADULT: 0.05,
                         AgeGroup.MATURE: 0.0, AgeGroup.MIDDLE_AGE: 0.0}[ag]

        # ── D31 主客观耦合 ── 经验→匹配度↑
        modifiers[31] = {AgeGroup.CHILD: -0.05, AgeGroup.EARLY_ADOLESCENT: -0.10,
                         AgeGroup.LATE_ADOLESCENT: -0.05, AgeGroup.YOUNG_ADULT: 0.0,
                         AgeGroup.MATURE: 0.05, AgeGroup.MIDDLE_AGE: 0.05}[ag]

        # ── D32 总控 ── 加权平均
        modifiers[32] = round(sum(modifiers[d] for d in range(1, 32)) / 31, 2)

        sex_mod = self._get_sex_modifier(dim_id)
        return round(modifiers.get(dim_id, 0.0) + sex_mod, 2)

    def _get_sex_modifier(self, dim_id: int) -> float:
        """性别对特定维度的修正"""
        sex = self.biological_sex
        if dim_id == 4:  # 内分泌: 女性周期波动
            return -0.05 if sex == BiologicalSex.FEMALE else 0.0
        if dim_id == 1:  # 肌肉: 男性优势
            return 0.05 if sex == BiologicalSex.MALE else -0.05
        if dim_id == 2:  # 疼痛: 女性痛阈低
            return -0.05 if sex == BiologicalSex.FEMALE else 0.0
        if dim_id == 13:  # 共情: 女性略高
            return 0.05 if sex == BiologicalSex.FEMALE else 0.0
        if dim_id == 14:  # 自我保护: 女性戒备略高
            return -0.05 if sex == BiologicalSex.FEMALE else 0.0
        if dim_id == 6:  # 代谢: 男性BMR高
            return 0.03 if sex == BiologicalSex.MALE else -0.03
        if dim_id == 12:  # 幸福感: 催产素基线女性略高
            return 0.04 if sex == BiologicalSex.FEMALE else 0.0
        return 0.0

    # ------------------------------------------------------------------
    # 经验修正系数
    # ------------------------------------------------------------------

    def get_experience_modifier(self, dim_id: int, domain: ExperienceDomain) -> float:
        """
        返回经验对该维度的修正系数。

        首次经历 → 高杏仁核激活/高新颖多巴胺/高皮质醇
        多次经历 → 程序化/低情绪波动/低应激

        正值=经验优势 (如熟练→焦虑↓)
        负值=经验带来的新奇感消失 (如探索欲↓)
        0=无显著影响
        """
        level = self.experience.get_level(domain)
        naive_bonus = {  # naive时的特殊效应
            ExperienceLevel.NAIVE: 1.0,
            ExperienceLevel.NOVICE: 0.5,
            ExperienceLevel.EXPERIENCED: 0.1,
            ExperienceLevel.HABITUATED: 0.0,
        }
        n = naive_bonus[level]

        # 不同维度对经验的响应不同
        if dim_id == 4:  # 内分泌: naive→皮质醇↑↑ + 多巴胺新奇↑↑
            return round(-0.20 * n + 0.15 * n, 2)  # 净效应 = 压力↑+新奇↑
        if dim_id == 10:  # 探索欲: naive→探索欲↑↑, habituated→↓
            if level == ExperienceLevel.NAIVE: return 0.25
            if level == ExperienceLevel.HABITUATED: return -0.10
            return 0.10
        if dim_id == 11:  # 恐惧/焦虑: naive→高焦虑
            return -0.20 * n
        if dim_id == 12:  # 幸福感: naive→强新奇幸福, habituated→平淡
            return 0.15 * n - 0.05
        if dim_id == 13:  # 共情: 有经验→更能理解他人处境
            return 0.10 if level in (ExperienceLevel.EXPERIENCED, ExperienceLevel.HABITUATED) else 0.0
        if dim_id == 4:  # 激素总效应
            return -0.10 * n  # 紧张为主
        if dim_id == 19:  # 社交: naive→焦虑↑
            return -0.15 * n
        if dim_id == 15:  # 依恋: naive→强烈依恋
            return 0.15 * n
        if dim_id == 9:  # 自我认知: 有经验→自信↑
            bonus = {ExperienceLevel.NAIVE: -0.10, ExperienceLevel.NOVICE: 0.0,
                     ExperienceLevel.EXPERIENCED: 0.10, ExperienceLevel.HABITUATED: 0.10}
            return bonus[level]

        return 0.0

    def get_effort_modifier(self, dim_id: int, effort_level: float) -> float:
        """
        付出/努力程度对维度的修正。

        effort_level: 0.0~1.0 (0=完全不努力, 0.5=正常努力, 1.0=全力以赴)

        体力维度的努力→代谢/乳酸↑; 心理维度的努力→皮质醇↑+成就感↑
        """
        if dim_id == 1:  # 肌肉: 努力→乳酸↑
            return -effort_level * 0.30
        if dim_id == 7:  # 自愈: 过度努力→恢复需求↑(标准值上升=需要更多恢复)
            return effort_level * 0.15
        if dim_id == 23:  # 工作: 努力→负荷↑
            return -effort_level * 0.20
        if dim_id == 10:  # 成长驱动: 适度努力→正向
            return 0.05 if 0.3 <= effort_level <= 0.7 else (-0.05 if effort_level > 0.9 else 0.0)
        if dim_id == 12:  # 幸福感: 努力有成就→正, 过度→负
            return 0.05 if effort_level < 0.8 else -0.10
        if dim_id == 32:  # 总控
            return -effort_level * 0.15
        return 0.0

    # ------------------------------------------------------------------
    # 特殊场景: 性行为年龄适配
    # ------------------------------------------------------------------

    def get_sexual_response_modifiers(self) -> Dict[int, float]:
        """
        首次 vs 经验丰富的性行为 → 差异化32维修正。

        14岁小女生首次: 杏仁核极高激活, 催产素高但夹杂恐惧, 疼痛预期高
        30岁成熟女性经验丰富: 放松, 催产素平稳, 疼痛预期低
        """
        level = self.experience.get_level(ExperienceDomain.SEXUAL)
        ag = self.age_group
        sex = self.biological_sex
        mods: Dict[int, float] = {}

        # D2 疼痛预期: naive+女性+年轻 → 高
        pain_factor = 0.0
        if level == ExperienceLevel.NAIVE:
            pain_factor -= 0.30
            if sex == BiologicalSex.FEMALE:
                pain_factor -= 0.10  # 女性首次更易疼痛
            if ag.is_adolescent:
                pain_factor -= 0.05  # 青少年身体未完全发育
        elif level == ExperienceLevel.EXPERIENCED:
            pain_factor += 0.05
        mods[2] = pain_factor

        # D4 内分泌: naive→皮质醇极高+多巴胺极高; 经验丰富→催产素为主
        if level == ExperienceLevel.NAIVE:
            mods[4] = -0.15  # 净负(紧张>愉悦)
            if ag.is_adolescent:
                mods[4] -= 0.05  # 青少年激素系统未成熟
        elif level == ExperienceLevel.HABITUATED:
            mods[4] = 0.10  # 放松愉悦

        # D11 恐惧: naive→高焦虑
        mods[11] = -0.35 if level == ExperienceLevel.NAIVE else (
            -0.10 if level == ExperienceLevel.NOVICE else 0.05)

        # D12 幸福感: 经验丰富→更高
        mods[12] = 0.05 if level == ExperienceLevel.NAIVE else (
            0.10 if level == ExperienceLevel.NOVICE else 0.20)

        # D15 依恋: naive→强烈
        mods[15] = 0.25 if level == ExperienceLevel.NAIVE else 0.10

        # D3 触觉: naive→高度敏感
        mods[3] = 0.15 if level == ExperienceLevel.NAIVE else 0.05

        # D14 自我保护: naive→戒备
        mods[14] = -0.15 if level == ExperienceLevel.NAIVE else 0.0

        # D1 肌肉: 年轻→更高柔韧性
        if ag.is_adolescent or ag == AgeGroup.YOUNG_ADULT:
            mods[1] = 0.05

        return mods

    # ------------------------------------------------------------------
    # 便捷工厂
    # ------------------------------------------------------------------

    def to_context_dict(self) -> Dict[str, Any]:
        """转为通道可消费的 context dict"""
        return {
            "age_group": self.age_group.value,
            "numeric_age": self.numeric_age,
            "biological_sex": self.biological_sex.value,
            "tanner_stage": self.tanner_stage,
            "frontal_lobe_maturity": self.age_group.frontal_lobe_maturity,
            "recovery_rate_factor": self.age_group.recovery_rate_factor,
            "testosterone_ng_dl": self.biological_sex.testosterone_baseline_ng_dl,
            "estrogen_pg_ml": self.biological_sex.estrogen_baseline_pg_ml,
            "muscle_mass_pct": self.biological_sex.muscle_mass_pct,
            "bmr_factor": self.biological_sex.bmr_factor,
            "pain_threshold_factor": self.biological_sex.pain_threshold_factor,
            "rest_hr_bpm": self.physical.rest_hr_bpm,
            "weight_kg": self.physical.weight_kg,
            "height_cm": self.physical.height_cm,
            "body_fat_pct": self.physical.body_fat_pct,
            "vo2max": self.physical.vo2max_ml_kg_min,
            "trait_openness": self.trait_openness,
            "trait_neuroticism": self.trait_neuroticism,
            "trait_extraversion": self.trait_extraversion,
            "experience": self.experience.to_dict(),
        }


# ===================================================================
# 预设 Avatar 模板 (用于测试和开发)
# ===================================================================

def make_child_female() -> AvatarProfile:
    """10岁小女生"""
    return AvatarProfile(
        age_group=AgeGroup.CHILD, biological_sex=BiologicalSex.FEMALE,
        physical=PhysicalTraits(height_cm=140, weight_kg=35, body_fat_pct=18,
                                rest_hr_bpm=80, vo2max_ml_kg_min=42),
        tanner_stage=1,
        trait_openness=0.7, trait_neuroticism=0.3, trait_extraversion=0.6,
    )


def make_adolescent_female_14() -> AvatarProfile:
    """14岁少女 — 青春期早期, 初次性经验可能年龄"""
    return AvatarProfile(
        age_group=AgeGroup.EARLY_ADOLESCENT, biological_sex=BiologicalSex.FEMALE,
        physical=PhysicalTraits(height_cm=158, weight_kg=48, body_fat_pct=22,
                                rest_hr_bpm=72, vo2max_ml_kg_min=38),
        tanner_stage=3, menarche_age=12.5,
        trait_openness=0.6, trait_neuroticism=0.55, trait_extraversion=0.55,
    )


def make_adolescent_male_14() -> AvatarProfile:
    """14岁少年 — 变声期, 身高快速增长期"""
    return AvatarProfile(
        age_group=AgeGroup.EARLY_ADOLESCENT, biological_sex=BiologicalSex.MALE,
        physical=PhysicalTraits(height_cm=162, weight_kg=50, body_fat_pct=16,
                                rest_hr_bpm=68, vo2max_ml_kg_min=45),
        tanner_stage=3,
        trait_openness=0.65, trait_neuroticism=0.40, trait_extraversion=0.60,
    )


def make_young_adult_female() -> AvatarProfile:
    """22岁年轻女性 — 成年早期, 身体巅峰"""
    return AvatarProfile(
        age_group=AgeGroup.YOUNG_ADULT, biological_sex=BiologicalSex.FEMALE,
        physical=PhysicalTraits(height_cm=163, weight_kg=55, body_fat_pct=24,
                                rest_hr_bpm=68, vo2max_ml_kg_min=36),
        tanner_stage=5, menarche_age=13.0,
        trait_openness=0.6, trait_neuroticism=0.45, trait_extraversion=0.55,
    )


def make_mature_female() -> AvatarProfile:
    """35岁成熟女性 — 稳定期, 可能有孩子"""
    return AvatarProfile(
        age_group=AgeGroup.MATURE, biological_sex=BiologicalSex.FEMALE,
        physical=PhysicalTraits(height_cm=163, weight_kg=58, body_fat_pct=26,
                                rest_hr_bpm=66, vo2max_ml_kg_min=33),
        tanner_stage=5, menarche_age=13.5,
        trait_openness=0.5, trait_neuroticism=0.40, trait_extraversion=0.50,
        relationship_status="married", has_children=True, children_ages=[4, 7],
    )


def make_mature_male() -> AvatarProfile:
    """35岁成熟男性"""
    return AvatarProfile(
        age_group=AgeGroup.MATURE, biological_sex=BiologicalSex.MALE,
        physical=PhysicalTraits(height_cm=175, weight_kg=75, body_fat_pct=20,
                                rest_hr_bpm=64, vo2max_ml_kg_min=40),
        tanner_stage=5,
        trait_openness=0.5, trait_neuroticism=0.35, trait_extraversion=0.50,
        relationship_status="married", has_children=True, children_ages=[4, 7],
    )


def make_middle_age_male() -> AvatarProfile:
    """53岁中年男性"""
    return AvatarProfile(
        age_group=AgeGroup.MIDDLE_AGE, biological_sex=BiologicalSex.MALE,
        physical=PhysicalTraits(height_cm=173, weight_kg=78, body_fat_pct=25,
                                rest_hr_bpm=68, vo2max_ml_kg_min=32),
        tanner_stage=5,
        trait_openness=0.45, trait_neuroticism=0.35, trait_extraversion=0.45,
        relationship_status="married", has_children=True, children_ages=[22, 19],
    )


PRESET_AVATARS: Dict[str, AvatarProfile] = {
    "child_f": make_child_female(),
    "adolescent_f_14": make_adolescent_female_14(),
    "adolescent_m_14": make_adolescent_male_14(),
    "young_adult_f": make_young_adult_female(),
    "mature_f": make_mature_female(),
    "mature_m": make_mature_male(),
    "middle_age_m": make_middle_age_male(),
}
