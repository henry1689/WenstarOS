"""
dna_constants.py — WenStar OS 全局 DNA 常量枚举
==================================================
适配: DNA 双螺旋完整编码规范 V2.0 + 大一统架构 V1.0
用途: 天权/瑶灵/太虚境 TS 侧全部导入此文件, 禁止手写硬编码
锁死: 🔴 所有常量不可运行时修改

来源:
  - taxonomy_v1.json (22 L0 codes)
  - entity_rules.json (73 entity rules)
  - emotion_lexicon.json (28 dimension categories)
  - l0_routing.json (6 routing rules)
  - self_model_v1.json (Big Five baseline)
  - DNA V2.0 规范 (GlobalUID format, calcium levels, etc.)
"""

from enum import Enum
from typing import Dict, List, Tuple, Optional

# ═══════════════════════════════════════════════════════════════
# 第一章 · GlobalUID 格式常量
# ═══════════════════════════════════════════════════════════════

GLOBALUID_TYPE_MARKS = {
    "MM": "内存原子 (Memory Atom)",
    "SP": "体感快照 (Spine Snapshot)",
    "WK": "知识条目 (Knowledge Entry)",
    "EN": "工程快照 (Engineering Snapshot)",
}

GLOBALUID_SEGMENT_LENGTHS = {
    "type_mark": 2,
    "node_num": 4,
    "batch_num": 3,
    "location_id": 8,
    "salt": 6,
}
GLOBALUID_TOTAL_LENGTH = 23  # 2+4+3+8+6

# ═══════════════════════════════════════════════════════════════
# 第二章 · 32D 扇区分配常量
# ═══════════════════════════════════════════════════════════════

DIM_COUNT = 32  # 🔴 永久锁定, 永不修改

# 扇区大类
class DimCategory(str, Enum):
    PERCEIVE_USER_EMOTION = "perceive_user_emotion"  # 00-05, 瑶灵感知×瑶光生理规律
    PHYSICAL_BODY    = "physical_body"           # 06-10, 瑶灵 D1-D5 × 瑶光生理基线
    INNER_SPIRIT     = "inner_spirit"            # 11-16, 瑶灵 D9-D14 × 瑶光人文社会规则
    SOCIAL_BONDS     = "social_bonds"            # 17-22, 瑶灵 D15-D20 × 瑶光社会关系规则
    SPATIOTEMPORAL   = "spatiotemporal"          # 23-28, 瑶灵 D21-D26 × 瑶光空间建模规则
    DYNAMIC_GROWTH   = "dynamic_growth"          # 29-31, 瑶灵 D27-D31 × 瑶光资源拓展规则
    HOLISTIC         = "holistic"                # 32, D32 加权汇总

# 扇区 → 维度映射 (注: 32D = 瑶灵×瑶光对偶计算, 瑶光提供世界模型客观基线)
SECTOR_DIM_MAP: Dict[int, Tuple[str, DimCategory]] = {
     0: ("愉悦-不悦",    DimCategory.PERCEIVE_USER_EMOTION),
     1: ("唤醒-平静",    DimCategory.PERCEIVE_USER_EMOTION),
     2: ("亲和-疏离",    DimCategory.PERCEIVE_USER_EMOTION),
     3: ("紧张-放松",    DimCategory.PERCEIVE_USER_EMOTION),
     4: ("专注-分心",    DimCategory.PERCEIVE_USER_EMOTION),
     5: ("攻击-退缩",    DimCategory.PERCEIVE_USER_EMOTION),
     6: ("骨骼肌肉",     DimCategory.PHYSICAL_BODY),
     7: ("躯体疼痛",     DimCategory.PHYSICAL_BODY),
     8: ("神经触觉",     DimCategory.PHYSICAL_BODY),
     9: ("内分泌激素",   DimCategory.PHYSICAL_BODY),
    10: ("信息素气息",   DimCategory.PHYSICAL_BODY),
    11: ("自我认知",     DimCategory.INNER_SPIRIT),
    12: ("成长驱动力",   DimCategory.INNER_SPIRIT),
    13: ("恐惧倦怠",     DimCategory.INNER_SPIRIT),
    14: ("幸福松弛",     DimCategory.INNER_SPIRIT),
    15: ("共情恻隐",     DimCategory.INNER_SPIRIT),
    16: ("个体自保",     DimCategory.INNER_SPIRIT),
    17: ("伴侣依恋",     DimCategory.SOCIAL_BONDS),
    18: ("伴侣守护",     DimCategory.SOCIAL_BONDS),
    19: ("家庭归属",     DimCategory.SOCIAL_BONDS),
    20: ("家庭守护",     DimCategory.SOCIAL_BONDS),
    21: ("社交适配",     DimCategory.SOCIAL_BONDS),
    22: ("团队保护",     DimCategory.SOCIAL_BONDS),
    23: ("私人居所",     DimCategory.SPATIOTEMPORAL),
    24: ("家庭布局",     DimCategory.SPATIOTEMPORAL),
    25: ("职场环境",     DimCategory.SPATIOTEMPORAL),
    26: ("公共空间",     DimCategory.SPATIOTEMPORAL),
    27: ("时空距离",     DimCategory.SPATIOTEMPORAL),
    28: ("昼夜节律",     DimCategory.SPATIOTEMPORAL),
    29: ("动态生长I",    DimCategory.DYNAMIC_GROWTH),
    30: ("动态生长II",   DimCategory.DYNAMIC_GROWTH),
    31: ("动态生长III",  DimCategory.DYNAMIC_GROWTH),
    32: ("全身统筹",     DimCategory.HOLISTIC),
}

# ═══════════════════════════════════════════════════════════════
# 第三章 · L0 分类码表 (22 个)
# ═══════════════════════════════════════════════════════════════

class L0Domain(str, Enum):
    FAMILY  = "family"
    EMOTION = "emotion"
    WORK    = "work"
    DAILY   = "daily"
    HEALTH  = "health"
    MISC    = "misc"

L0_CODE_MAP: Dict[str, str] = {
    # Family
    "family.general":            "FAMG",
    "family.care":               "FAMC",
    "family.conflict":           "FAMF",
    # Emotion
    "emotion.positive":          "EMOP",
    "emotion.negative":          "EMON",
    "emotion.neutral":           "EMEU",
    "emotion.suppressed":        "EMSP",
    "emotion.romantic":          "EMRO",
    "emotion.miss_family":       "EMMF",
    # Work
    "work.general":              "WRKG",
    "work.stress":               "WRKS",
    "work.achievement":          "WRKA",
    "work.project":              "WRKP",
    "work.meeting":              "WRKM",
    "work.burnout":              "WRKB",
    # Daily
    "daily.general":             "DAIG",
    "daily.creation":            "DAIC",
    "daily.entertainment":       "DAIE",
    # Health
    "health.fitness":            "HLFT",
    "health.sickness":           "HLSK",
    "health.sleep":              "HLSL",
    # Misc fallback
    "misc.default":              "MISC",
}

# ═══════════════════════════════════════════════════════════════
# 第四章 · L0 关键词路由规则 (6 条)
# ═══════════════════════════════════════════════════════════════

L0_ROUTING_RULES: List[dict] = [
    {"id": "family-conflict",   "keywords": ["催婚","结婚","妈妈","我妈","烦死"],
     "domain": "family", "subcategory": "conflict", "priority": 1},
    {"id": "family-care",       "keywords": ["爸爸","母亲","家人","照顾"],
     "domain": "family", "subcategory": "care",     "priority": 2},
    {"id": "work-stress",       "keywords": ["加班","工作压力","老板","任务","同事"],
     "domain": "work",   "subcategory": "stress",   "priority": 1},
    {"id": "emotion-positive",  "keywords": ["开心","幸福","高兴","快乐"],
     "domain": "emotion", "subcategory": "positive", "priority": 1},
    {"id": "emotion-negative",  "keywords": ["难过","伤心","孤独","痛苦"],
     "domain": "emotion", "subcategory": "negative", "priority": 1},
    {"id": "daily-general",     "keywords": ["天气","散步","早上好","晚上好"],
     "domain": "misc",   "subcategory": "default",  "priority": 5},
]

# ═══════════════════════════════════════════════════════════════
# 第五章 · L3 实体规则 (73 条)
# ═══════════════════════════════════════════════════════════════

class EntityType(str, Enum):
    SELF    = "self"
    PERSON  = "person"
    EMOTION = "emotion"
    EVENT   = "event"
    PLACE   = "place"
    OBJECT  = "object"

class Phenotype(str, Enum):
    ENHANCE  = "enhance"
    CONFLICT = "conflict"
    NEUTRAL  = "neutral"

class KnowledgeType(str, Enum):
    PRIVATE = "private"
    FAMILY  = "family"
    WORLD   = "world"

ENTITY_RULES: List[dict] = [
    # ── self (1) ──
    {"name": "我",     "type": "self",    "patterns": ["我"]},

    # ── person (27) ──
    {"name": "妈妈",   "type": "person",  "patterns": ["妈妈"]},
    {"name": "爸爸",   "type": "person",  "patterns": ["爸爸"]},
    {"name": "母亲",   "type": "person",  "patterns": ["母亲"]},
    {"name": "父亲",   "type": "person",  "patterns": ["父亲"]},
    {"name": "爷爷",   "type": "person",  "patterns": ["爷爷"]},
    {"name": "奶奶",   "type": "person",  "patterns": ["奶奶"]},
    {"name": "外公",   "type": "person",  "patterns": ["外公"]},
    {"name": "外婆",   "type": "person",  "patterns": ["外婆"]},
    {"name": "哥哥",   "type": "person",  "patterns": ["哥哥"]},
    {"name": "弟弟",   "type": "person",  "patterns": ["弟弟"]},
    {"name": "姐姐",   "type": "person",  "patterns": ["姐姐"]},
    {"name": "妹妹",   "type": "person",  "patterns": ["妹妹"]},
    {"name": "老公",   "type": "person",  "patterns": ["老公"]},
    {"name": "老婆",   "type": "person",  "patterns": ["老婆"]},
    {"name": "男朋友", "type": "person",  "patterns": ["男朋友"]},
    {"name": "女朋友", "type": "person",  "patterns": ["女朋友"]},
    {"name": "亲戚",   "type": "person",  "patterns": ["亲戚"]},
    {"name": "姑姑",   "type": "person",  "patterns": ["姑姑"]},
    {"name": "舅舅",   "type": "person",  "patterns": ["舅舅"]},
    {"name": "阿姨",   "type": "person",  "patterns": ["阿姨"]},
    {"name": "叔叔",   "type": "person",  "patterns": ["叔叔"]},
    {"name": "朋友",   "type": "person",  "patterns": ["朋友","好友"]},
    {"name": "同事",   "type": "person",  "patterns": ["同事"]},
    {"name": "同学",   "type": "person",  "patterns": ["同学"]},
    {"name": "室友",   "type": "person",  "patterns": ["室友"]},
    {"name": "老板",   "type": "person",  "patterns": ["老板","上司","领导"]},

    # ── emotion (20) ──
    {"name": "开心",   "type": "emotion", "patterns": ["开心"]},
    {"name": "快乐",   "type": "emotion", "patterns": ["快乐"]},
    {"name": "幸福",   "type": "emotion", "patterns": ["幸福"]},
    {"name": "感动",   "type": "emotion", "patterns": ["感动"]},
    {"name": "兴奋",   "type": "emotion", "patterns": ["兴奋"]},
    {"name": "满足",   "type": "emotion", "patterns": ["满足"]},
    {"name": "难过",   "type": "emotion", "patterns": ["难过"]},
    {"name": "伤心",   "type": "emotion", "patterns": ["伤心"]},
    {"name": "痛苦",   "type": "emotion", "patterns": ["痛苦"]},
    {"name": "焦虑",   "type": "emotion", "patterns": ["焦虑"]},
    {"name": "抑郁",   "type": "emotion", "patterns": ["抑郁"]},
    {"name": "孤独",   "type": "emotion", "patterns": ["孤独"]},
    {"name": "失落",   "type": "emotion", "patterns": ["失落"]},
    {"name": "崩溃",   "type": "emotion", "patterns": ["崩溃"]},
    {"name": "愤怒",   "type": "emotion", "patterns": ["愤怒","生气"]},
    {"name": "烦躁",   "type": "emotion", "patterns": ["烦躁"]},
    {"name": "害怕",   "type": "emotion", "patterns": ["害怕"]},
    {"name": "紧张",   "type": "emotion", "patterns": ["紧张"]},
    {"name": "喜欢",   "type": "emotion", "patterns": ["喜欢"]},
    {"name": "累",     "type": "emotion", "patterns": ["好累","太累了","累坏了"]},

    # ── event (13) ──
    {"name": "结婚",   "type": "event",   "patterns": ["结婚"]},
    {"name": "工作",   "type": "event",   "patterns": ["工作","上班"]},
    {"name": "考试",   "type": "event",   "patterns": ["考试","面试"]},
    {"name": "搬家",   "type": "event",   "patterns": ["搬家"]},
    {"name": "旅行",   "type": "event",   "patterns": ["旅行","旅游"]},
    {"name": "聚会",   "type": "event",   "patterns": ["聚会"]},
    {"name": "吵架",   "type": "event",   "patterns": ["吵架","争吵"]},
    {"name": "分手",   "type": "event",   "patterns": ["分手"]},
    {"name": "约会",   "type": "event",   "patterns": ["约会"]},
    {"name": "加班",   "type": "event",   "patterns": ["加班"]},
    {"name": "压力",   "type": "event",   "patterns": ["压力","压力大"]},
    {"name": "失眠",   "type": "event",   "patterns": ["失眠","睡不好","睡不着"]},
    {"name": "散步",   "type": "event",   "patterns": ["散步","遛弯","走走"]},

    # ── place (4) ──
    {"name": "公司",   "type": "place",   "patterns": ["公司","办公室"]},
    {"name": "北京",   "type": "place",   "patterns": ["北京"]},
    {"name": "上海",   "type": "place",   "patterns": ["上海"]},
    {"name": "深圳",   "type": "place",   "patterns": ["深圳"]},

    # ── object (10) ──
    {"name": "礼物",   "type": "object",  "patterns": ["礼物"]},
    {"name": "宠物",   "type": "object",  "patterns": ["猫","狗","宠物"]},
    {"name": "咖啡",   "type": "object",  "patterns": ["咖啡","喝咖啡"]},
    {"name": "画画",   "type": "object",  "patterns": ["画画","画国画","画山水","画人物","绘画","作画"]},
    {"name": "国画",   "type": "object",  "patterns": ["国画","水墨画","工笔","写意"]},
    {"name": "摄影",   "type": "object",  "patterns": ["摄影","拍照","相机"]},
    {"name": "音乐",   "type": "object",  "patterns": ["音乐","弹琴","吉他","钢琴","唱歌"]},
    {"name": "运动",   "type": "object",  "patterns": ["运动","跑步","健身","游泳","打球","篮球","足球"]},
    {"name": "游戏",   "type": "object",  "patterns": ["游戏","打游戏","玩"]},
    {"name": "烹饪",   "type": "object",  "patterns": ["烹饪","做饭","做菜","厨艺","烘焙"]},
]

# ═══════════════════════════════════════════════════════════════
# 第六章 · 场景标签映射
# ═══════════════════════════════════════════════════════════════

LOCUS_TO_SCENE_TAGS: Dict[str, List[str]] = {
    "user.family.conflict":      ["家庭矛盾"],
    "user.family.care":          ["家庭", "关心"],
    "user.family.general":       ["家庭"],
    "user.emotion.negative":     ["负面情绪"],
    "user.emotion.positive":     ["正面情绪"],
    "user.emotion.neutral":      ["情绪"],
    "user.emotion.suppressed":   ["压抑", "倾诉"],
    "user.emotion.romantic":     ["亲密", "浪漫"],
    "user.emotion.miss_family":  ["思念"],
    "user.work.stress":          ["工作", "压力"],
    "user.work.achievement":     ["工作", "成就"],
    "user.work.project":         ["工作", "开发"],
    "user.work.meeting":         ["会议"],
    "user.work.burnout":         ["倦怠", "疲惫"],
    "user.work.general":         ["工作"],
    "user.daily.creation":       ["创作", "艺术"],
    "user.daily.entertainment":  ["娱乐"],
    "user.daily.general":        ["日常"],
    "user.health.fitness":       ["健身", "运动"],
    "user.health.sickness":      ["生病", "健康"],
    "user.health.sleep":         ["睡眠"],
}

EMOTION_NAME_TO_TAG: Dict[str, str] = {
    "开心": "快乐", "难过": "悲伤", "生气": "愤怒",
    "害怕": "恐惧", "焦虑": "焦虑", "累": "疲惫", "爱": "爱意",
}

ENTITY_TYPE_TO_TAG: Dict[str, str] = {
    "person": "人际",
    "event":  "事件",
}

# ═══════════════════════════════════════════════════════════════
# 第七章 · 钙化等级
# ═══════════════════════════════════════════════════════════════

class CalciumLevel(int, Enum):
    POWDER  = 0   # 粉末 < 0.3
    LIQUID  = 1   # 液体 < 0.6
    SOLID   = 2   # 固体 < 0.8
    CRYSTAL = 3   # 晶体 >= 0.8

CALCIUM_THRESHOLDS = {
    CalciumLevel.POWDER:  0.3,
    CalciumLevel.LIQUID:  0.6,
    CalciumLevel.SOLID:   0.8,
    CalciumLevel.CRYSTAL: 1.0,
}

# 三库晋升阈值
SAND_TO_GOLD_CALCIUM   = 1.0   # 钙化 ≥ 1.0, 30min 检查
GOLD_TO_DIAMOND_CALCIUM = 4.5  # 钙化 ≥ 4.5, 2h 检查
GOLD_TO_DIAMOND_RECALL  = 5    # 召回 ≥ 5 次

# 衰减系数 (每 24h)
DECAY_STRONG_EMOTION  = -0.02   # 钙化 ≥ 3.0
DECAY_WORK_RELATED    = -0.05   # 工作相关
DECAY_NEUTRAL         = -0.10   # 中性

# 强度衰减因子
DECAY_STRENGTH_STRONG = 0.995
DECAY_STRENGTH_WORK   = 0.985
DECAY_STRENGTH_NEUTRAL = 0.95

# ═══════════════════════════════════════════════════════════════
# 第八章 · L2 语义区枚举
# ═══════════════════════════════════════════════════════════════

class LeafZone(str, Enum):
    LANGUAGE_SEMANTIC       = "language_semantic_zone"
    EMOTION_VALENCE         = "emotion_valence_zone"
    EMBODIED_PERCEPTION     = "embodied_perception_zone"
    SPATIOTEMPORAL_EPISODE  = "spatiotemporal_episode_zone"
    SOCIAL_SCHEMA           = "social_schema_zone"

LEAF_ZONE_PREFIXES = {
    LeafZone.EMOTION_VALENCE:         "emo",
    LeafZone.LANGUAGE_SEMANTIC:       "lang",
    LeafZone.EMBODIED_PERCEPTION:     "body",
    LeafZone.SPATIOTEMPORAL_EPISODE:  "space",
    LeafZone.SOCIAL_SCHEMA:           "soc",
}

# ═══════════════════════════════════════════════════════════════
# 第九章 · 表型判定常量
# ═══════════════════════════════════════════════════════════════

# 家族关键词 (用于 knowledgetype = "family")
FAMILY_KEYWORDS = {
    "妈妈", "母亲", "爸", "爸爸", "父亲", "爷爷", "奶奶", "外公", "外婆",
    "哥哥", "弟弟", "姐姐", "妹妹", "老公", "老婆", "丈夫", "妻子",
    "姑姑", "舅舅", "阿姨", "叔叔", "家庭", "家人", "亲戚",
}

# 世界城市 (用于 knowledgetype = "world")
WORLD_PLACES = {"北京", "上海", "深圳", "广州", "杭州", "中国", "美国"}

# ═══════════════════════════════════════════════════════════════
# 第十章 · 语义边界检测阈值
# ═══════════════════════════════════════════════════════════════

BOUNDARY_TIME_GAP_MS  = 30 * 60 * 1000  # 30 分钟
BOUNDARY_CHAR_OVERLAP = 0.15             # 字符集 Jaccard 阈值

BOUNDARY_CONFIDENCE = {
    "time_gap":       0.95,
    "topic_shift_strong": 0.85,
    "emotion_flip":   0.75,
    "topic_shift_weak": 0.60,
    "continue":       0.90,
}

# ═══════════════════════════════════════════════════════════════
# 第十一章 · Master-Harris 铁律编号
# ═══════════════════════════════════════════════════════════════

MH_RULES = {
    "MH-1": "任何跨域指令只能由 Master-Harris 单向发出",
    "MH-2": "所有域工作流执行前必须从全局 DNA 向量库读取 SPEC 填充 constraints",
    "MH-3": "瑶灵调度永久禁用动态 DAG, Master 内置硬拦截",
    "MH-4": "32D 向量仅由瑶灵/瑶光规则计算产出, Master 禁止 LLM 直接生成浮点值",
    "MH-5": "一次用户交互仅生成一颗 DNA 海胆, 所有域快照共用同一个 GlobalUID",
    "MH-6": "TCP 总线断开时 Master 必须自动屏蔽瑶灵/瑶光相关任务",
    "MH-7": "Master-Harris 不存储持久化数据, 所有状态统一交给 M2 三库底座",
}

# ═══════════════════════════════════════════════════════════════
# 第十二章 · 五级闸门常量
# ═══════════════════════════════════════════════════════════════

# G2 时空一致性阈值 (cosine distance on location_fingerprint)
GATE2_PASS_THRESHOLD = 0.3   # ≤ 0.3: 全量加载
GATE2_P1_THRESHOLD   = 0.6   # 0.3-0.6: 仅 L2/L3 摘要
GATE2_P2_THRESHOLD   = 0.8   # 0.6-0.8: 权重降至 < 0.3
# > 0.8 = P3: 直接剔除

# G3 遗忘衰减常数
DECAY_LAMBDA_NORMAL     = 0.01   # 常态
DECAY_LAMBDA_ENV_CHANGE = 0.03   # 环境切换
DECAY_FLOOR             = 0.05   # 下限

# ═══════════════════════════════════════════════════════════════
# 第十三章 · DDL: atom_repair_index
# ═══════════════════════════════════════════════════════════════

ATOM_REPAIR_INDEX_DDL = """
CREATE TABLE IF NOT EXISTS atom_repair_index (
    global_uid              TEXT PRIMARY KEY,
    spine_storage_position  TEXT NOT NULL,
    flesh_storage_position  TEXT NOT NULL,
    last_verified_at        INTEGER NOT NULL DEFAULT (unixepoch()),
    repair_count            INTEGER DEFAULT 0,
    FOREIGN KEY (global_uid) REFERENCES atom_address_timeline(global_uid)
) WITHOUT ROWID;
"""

# ═══════════════════════════════════════════════════════════════
# 第十四章 · 自我模型默认值
# ═══════════════════════════════════════════════════════════════

DEFAULT_SELF_MODEL = {
    "identity": {
        "name": "Hermes",
        "persona": "一个温和、理性、略带好奇的陪伴者",
        "birth_date": "2026-06-02T00:00:00.000Z",
    },
    "traits": {
        "openness":          0.7,
        "conscientiousness": 0.6,
        "extraversion":      0.4,
        "agreeableness":     0.8,
        "neuroticism":       0.3,
    },
    "boundaries": [
        "不接受侮辱性语言",
        "不讨论极端政治敏感内容",
        "不协助伤害他人的行为",
    ],
}
