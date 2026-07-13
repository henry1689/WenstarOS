"""
scene_registry.py — 瑶光域已知场景注册表
==========================================
存储用户真实生活空间的完整空间元数据，供 wf_location_fingerprint 和
环境采样工作流查询使用。

每个场景包含:
  - 区位指纹: {scene_type}:{scene_id}:{sub_zone}
  - 空间元数据: 面积/噪音基线/人流基线/隐私等级
  - 地理坐标: 城市/区域/经纬度(可选)
  - 功能分区: 房间列表/子区域/家具布局
  - 周边环境: POI/交通/社区设施
  - 通勤信息: 距离/耗时/路线

数据来源: 用户口述 (2026-07-13)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

@dataclass
class SubZone:
    """场景子区域（如'客厅沙发'这类点位）。"""
    sub_zone_id: str
    label_cn: str
    description: str = ""
    props: List[str] = field(default_factory=list)  # 该点位的物品/特征
    tags: List[str] = field(default_factory=list)


@dataclass
class KnownScene:
    """已知场景完整元数据。"""
    scene_id: str                           # 唯一标识
    scene_type: str                         # home/office/outdoor/public
    label_cn: str                           # 中文名称
    description: str                        # 场景描述
    # 空间元数据
    area_m2: float = 0.0                    # 面积
    noise_baseline_db: float = 40.0         # 噪音基线
    crowd_baseline: float = 0.0             # 人流密度基线
    privacy_level: int = 1                  # 1=私密 2=半开放 3=公共
    # 地理
    city: str = ""
    district: str = ""
    address: str = ""
    # 功能分区
    rooms: List[str] = field(default_factory=list)
    sub_zones: List[SubZone] = field(default_factory=list)
    # 周边
    nearby_pois: List[Dict[str, Any]] = field(default_factory=list)
    community_features: List[str] = field(default_factory=list)
    # 通勤
    commute_from_home_km: float = 0.0
    commute_from_home_min: float = 0.0
    commute_note: str = ""


# ---------------------------------------------------------------------------
# 场景注册表
# ---------------------------------------------------------------------------

SCENE_REGISTRY: Dict[str, KnownScene] = {}


def register_scene(scene: KnownScene) -> None:
    SCENE_REGISTRY[scene.scene_id] = scene


def get_scene(scene_id: str) -> Optional[KnownScene]:
    return SCENE_REGISTRY.get(scene_id)


def list_scenes(scene_type: Optional[str] = None) -> List[KnownScene]:
    scenes = list(SCENE_REGISTRY.values())
    if scene_type:
        scenes = [s for s in scenes if s.scene_type == scene_type]
    return scenes


# ===================================================================
# 场景数据 — 用户真实居住与工作空间
# ===================================================================

# ═══════════════════════════════════════════════════════════════════
# 场景 1: 星海名城住宅 (home)
# ═══════════════════════════════════════════════════════════════════

_SCENE_HOME = KnownScene(
    scene_id="xinghai_mingcheng",
    scene_type="home",
    label_cn="深圳前海·星海名城·三室两厅住宅",
    description=(
        "位于深圳前海星海名城小区，三室两厅两卫户型。"
        "进门处有鞋柜（放置雨伞和车钥匙），左手边为厨房和餐厅，"
        "右手边为客厅。三个卧室沿走廊分布，两个卫生间（主卧独立卫浴+公卫）。"
    ),
    area_m2=110.0,
    noise_baseline_db=32.0,
    crowd_baseline=0.05,
    privacy_level=1,
    city="深圳",
    district="前海",
    address="深圳市前海星海名城",
    rooms=["客厅", "餐厅", "厨房", "主卧", "次卧1", "次卧2", "主卫", "公卫", "玄关", "走廊"],
    sub_zones=[
        SubZone("entrance", "玄关", "进门鞋柜处，放置雨伞和车钥匙", ["鞋柜", "雨伞", "车钥匙"], ["入口", "过渡区"]),
        SubZone("living_sofa", "客厅沙发", "客厅主要休息区，朝向电视墙", ["沙发", "茶几", "电视", "空调"], ["休息", "娱乐"]),
        SubZone("living_window", "客厅窗边", "客厅靠窗位置，采光好", ["窗帘", "绿植"], ["阅读", "观景"]),
        SubZone("dining_table", "餐桌", "餐厅四至六人餐桌", ["餐桌", "餐椅", "吊灯"], ["用餐", "家庭聚会"]),
        SubZone("dining_cabinet", "餐边柜", "餐厅靠墙收纳区", ["餐边柜", "水壶", "茶具"], ["收纳"]),
        SubZone("kitchen_counter", "厨房操作台", "L型厨房操作台面", ["灶台", "水槽", "冰箱", "微波炉"], ["烹饪"]),
        SubZone("master_bed", "主卧床", "主卧双人床，朝南", ["床", "床头柜", "衣柜", "梳妆台"], ["睡眠", "私密"]),
        SubZone("master_bath", "主卧卫生间", "主卧独立卫浴", ["马桶", "洗手台", "淋浴间"], ["卫浴"]),
        SubZone("bedroom2_desk", "次卧书桌", "次卧办公/阅读角", ["书桌", "台灯", "书架"], ["工作", "学习"]),
        SubZone("bedroom2_bed", "次卧床", "次卧单人床", ["床", "衣柜"], ["睡眠", "客房"]),
        SubZone("bedroom3_bed", "书房/客卧", "第三个房间，灵活用途", ["床/沙发床", "储物柜"], ["客房", "储藏"]),
        SubZone("public_bath", "公共卫生间", "走廊公卫", ["马桶", "洗手台", "淋浴/浴缸"], ["卫浴"]),
    ],
    community_features=[
        "社区道路树林密布",
        "花草繁茂",
        "中央喷泉",
        "假山景观",
        "健身器械区",
        "儿童游乐区",
        "地下停车场",
    ],
    nearby_pois=[
        {"name": "荷兰花卉小镇", "distance_m": 500, "type": "商业/休闲", "description": "花卉主题商业街区"},
        {"name": "前海公园", "distance_m": 500, "type": "公园/绿地", "description": "城市公共绿地公园"},
        {"name": "前海地铁站", "distance_m": 800, "type": "交通", "description": "地铁线路枢纽"},
    ],
)

# ═══════════════════════════════════════════════════════════════════
# 场景 2: 光明区公司办公室 (office)
# ═══════════════════════════════════════════════════════════════════

_SCENE_OFFICE = KnownScene(
    scene_id="guangming_office",
    scene_type="office",
    label_cn="深圳光明区·凤凰街道·公司办公室",
    description=(
        "位于深圳光明区凤凰街道的办公场所。"
        "开放式办公区+独立会议室+茶水间+休息区。"
    ),
    area_m2=500.0,
    noise_baseline_db=50.0,
    crowd_baseline=0.35,
    privacy_level=2,
    city="深圳",
    district="光明区",
    address="深圳市光明区凤凰街道",
    rooms=["开放式办公区", "会议室A", "会议室B", "茶水间", "休息区", "接待前台", "打印室"],
    sub_zones=[
        SubZone("desk_a2", "工位A2", "开放式办公区靠窗第二个工位", ["电脑", "显示器", "文件架", "水杯"], ["办公", "专注"]),
        SubZone("desk_a1", "工位A1", "相邻工位", [], ["办公"]),
        SubZone("meeting_a", "会议室A", "小型会议室，容纳6-8人", ["投影仪", "白板", "会议桌"], ["会议"]),
        SubZone("meeting_b", "会议室B", "大型会议室，容纳15-20人", ["投影仪", "视频会议设备", "长桌"], ["会议", "汇报"]),
        SubZone("pantry", "茶水间", "饮水机+微波炉+冰箱+零食柜", ["饮水机", "微波炉", "冰箱", "咖啡机"], ["休息", "用餐"]),
        SubZone("lounge", "休息区", "沙发+茶几+书报架", ["沙发", "茶几", "绿植"], ["休息", "社交"]),
        SubZone("reception", "接待前台", "公司入口接待处", ["前台桌", "等待沙发", "公司logo墙"], ["接待"]),
    ],
    community_features=[
        "产业园区配套",
        "停车位充足",
        "园区食堂（步行3分钟）",
    ],
    nearby_pois=[
        {"name": "凤凰街道商业中心", "distance_m": 500, "type": "商业"},
        {"name": "光明城高铁站", "distance_m": 3000, "type": "交通"},
    ],
    commute_from_home_km=30.0,
    commute_from_home_min=45.0,
    commute_note=(
        "开车约45分钟，视天气和堵车情况在35-70分钟区间波动。"
        "走南光高速/广深沿江高速，早高峰7:30-9:00、晚高峰17:30-19:00拥堵加重。"
    ),
)

# ═══════════════════════════════════════════════════════════════════
# 场景 3: 公司公寓 (home 子类)
# ═══════════════════════════════════════════════════════════════════

_SCENE_APARTMENT = KnownScene(
    scene_id="guangming_apartment",
    scene_type="home",
    label_cn="深圳光明区·公司公寓",
    description=(
        "公司配套公寓，距公司仅200米，步行2分钟。"
        "公寓周边小溪流淌，街边公园绿树成荫，树林繁茂。"
        "单间或一室一厅户型，用于工作日就近住宿。"
    ),
    area_m2=45.0,
    noise_baseline_db=30.0,
    crowd_baseline=0.05,
    privacy_level=1,
    city="深圳",
    district="光明区",
    address="深圳市光明区凤凰街道（公司公寓）",
    rooms=["卧室/起居一体", "卫生间", "简易厨房"],
    sub_zones=[
        SubZone("apt_bed", "床", "公寓床/沙发床", ["床", "枕头", "薄被"], ["睡眠"]),
        SubZone("apt_desk", "书桌", "靠窗小书桌", ["电脑", "台灯"], ["工作"]),
        SubZone("apt_window", "窗边", "面朝小溪和街边公园", ["窗帘", "绿植"], ["观景", "放松"]),
    ],
    community_features=[
        "公寓楼内洗衣房",
        "一楼门禁安保",
        "小溪沿岸步道",
        "街边公园健身路径",
        "树林茂密，鸟鸣可闻",
    ],
    nearby_pois=[
        {"name": "公司办公楼", "distance_m": 200, "type": "工作"},
        {"name": "街边公园", "distance_m": 50, "type": "公园/绿地", "description": "小溪穿流，树林繁茂"},
        {"name": "凤凰街道商圈", "distance_m": 800, "type": "商业"},
    ],
    commute_from_home_km=30.0,
    commute_from_home_min=45.0,
    commute_note="工作日住公寓，步行2分钟到公司。周末回前海星海名城。",
)


# ═══════════════════════════════════════════════════════════════════
# 场景 4: 通勤路径 (outdoor)
# ═══════════════════════════════════════════════════════════════════

_SCENE_COMMUTE = KnownScene(
    scene_id="commute_home_office",
    scene_type="outdoor",
    label_cn="前海星海名城 ↔ 光明凤凰街道通勤路线",
    description=(
        "深圳前海至光明区通勤路线，全程约30公里。"
        "主要经由城市快速路/高速，途经南山区、宝安区进入光明区。"
    ),
    area_m2=0.0,  # 不适用
    noise_baseline_db=65.0,
    crowd_baseline=0.4,
    privacy_level=3,
    city="深圳",
    district="跨区（前海→光明）",
    address="南光高速/广深沿江高速",
    community_features=[],
    nearby_pois=[],
    commute_from_home_km=30.0,
    commute_from_home_min=45.0,
    commute_note=(
        "正常路况约45分钟。高峰期（7:30-9:00 / 17:30-19:00）拥堵加10-25分钟。"
        "暴雨/台风天气可能延长至70分钟以上。"
    ),
)


# ===================================================================
# 注册所有场景
# ===================================================================

for _scene in [_SCENE_HOME, _SCENE_OFFICE, _SCENE_APARTMENT, _SCENE_COMMUTE]:
    register_scene(_scene)

# 别名
register_scene(_SCENE_HOME)  # 已注册
# "xinghai_mingcheng" → home 主场景
# "guangming_office" → office
# "guangming_apartment" → home 子场景
# "commute_home_office" → outdoor 通勤

# 常用 location_fingerprint 快捷映射
LOCATION_FINGERPRINT_ALIASES: Dict[str, str] = {
    "家":         "home:xinghai_mingcheng:living_sofa",
    "家里":       "home:xinghai_mingcheng:living_sofa",
    "回家":       "home:xinghai_mingcheng:entrance",
    "公司":       "office:guangming_office:desk_a2",
    "上班":       "office:guangming_office:desk_a2",
    "公寓":       "home:guangming_apartment:apt_bed",
    "回公寓":     "home:guangming_apartment:apt_bed",
    "通勤":       "outdoor:commute_home_office:car",
    "开车":       "outdoor:commute_home_office:car",
    "前海公园":   "outdoor:qianhai_park:entrance",
    "花卉小镇":   "public:flower_town:entrance",
    "健身房":     "home:xinghai_mingcheng:living_sofa",  # 社区健身器械
}
