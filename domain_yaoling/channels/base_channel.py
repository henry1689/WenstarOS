"""
base_channel.py — 瑶灵 32 维通道基类
=====================================
所有维度通道 (d1_muscle.py ~ d32_holistic.py) 继承此基类。
每条通道实现: 信号接收 → 器官响应 → 正负体感 → 标准化输出

设计约束 (YAOLING_DOMAIN_SPEC.md §1.2):
  - 只产生主观体感数据，不演算客观规律
  - 所有数值由规则公式计算，禁止 LLM 直接生成浮点
  - 通道之间互不调用（独立处理），联动由太虚统筹
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# 枚举常量（与 spine.proto 保持对齐）
# ---------------------------------------------------------------------------


class Intensity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class HealthLevel(str, Enum):
    HEALTHY = "healthy"          # 0 ~ +30
    SUB_HEALTHY = "sub_healthy"  # -30 ~ -1
    RISK = "risk"                # -60 ~ -31
    DANGER = "danger"            # < -60

    @classmethod
    def from_deviation(cls, deviation: float) -> "HealthLevel":
        if deviation >= 0:
            return cls.HEALTHY
        if deviation >= -30:
            return cls.SUB_HEALTHY
        if deviation >= -60:
            return cls.RISK
        return cls.DANGER


class ChannelCategory(str, Enum):
    PHYSICAL_BODY = "physical_body"        # D1-D8
    INNER_SPIRIT = "inner_spirit"          # D9-D14
    SOCIAL_BONDS = "social_bonds"          # D15-D20
    SPATIOTEMPORAL = "spatiotemporal"      # D21-D26
    DYNAMIC_GROWTH = "dynamic_growth"      # D27-D32


# ---------------------------------------------------------------------------
# 通道输入/输出数据结构
# ---------------------------------------------------------------------------


@dataclass
class SignalInput:
    """外部输入信号——来自瑶光快照或天权快照。"""
    source_channel: str  # "tianquan_snapshot" | "yaoguang_snapshot"
    scene_tags: List[str] = field(default_factory=list)
    interpersonal_labels: List[str] = field(default_factory=list)  # partner/family/colleague/stranger
    environmental_params: Dict[str, float] = field(default_factory=dict)  # temp/light/noise/weather
    temporal_context: Dict[str, Any] = field(default_factory=dict)  # time_of_day/season/day_of_week
    raw_input_text: str = ""  # 触发体感的原始文本片段（如用户消息）
    duration_context: Dict[str, float] = field(default_factory=dict)  # hours_sitting/work_duration/etc


@dataclass
class OrganState:
    """器官/系统响应后的内部状态。"""
    organ_name: str  # 响应器官名称（中文）
    metrics: Dict[str, float] = field(default_factory=dict)  # 量化指标
    activation_level: float = 0.0  # 0.0-1.0 激活程度


@dataclass
class SensationResult:
    """单个维度的标准化输出——对应规范 §2.2 输出数据包格式。"""
    dim_id: int
    dim_key: str
    category: ChannelCategory
    # 主观体感
    value_raw: float           # -1.0 ~ 1.0
    intensity: Intensity
    sensation_label: str        # 中文体感描述（正向/负向）
    # 医学对标
    medical_metric_name: str    # 真人临床指标名称
    medical_value: float        # 折算后的医学数值
    medical_unit: str           # 单位
    medical_baseline: float     # 瑶光健康零点
    deviation: float            # 相对基准的偏移
    health_level: HealthLevel
    # 证据与上下文
    evidence_text: str          # 输入信号中触发此体感的原文片段
    organ_state: OrganState
    sibling_dims: List[int]     # 同象限兄弟维度编号
    # 元数据
    timestamp: str = ""         # ISO8601，由上层填充
    dna_root_id: str = ""       # DNA时序锚点，由上层填充


# ---------------------------------------------------------------------------
# 维度配置
# ---------------------------------------------------------------------------


@dataclass
class DimConfig:
    """维度静态配置——每条通道初始化时声明。"""
    dim_id: int
    dim_key: str
    category: ChannelCategory
    quadrant: str  # 五大类内子分组（如 D1-D8 内的"骨骼"子组）
    label_cn: str  # 中文标签
    medical_metric_name: str
    medical_baseline: float
    medical_unit: str
    sibling_dims: List[int] = field(default_factory=list)
    # 安全阈值
    danger_threshold_upper: Optional[float] = None  # 超过此值→danger
    danger_threshold_lower: Optional[float] = None  # 低于此值→danger
    risk_threshold_upper: Optional[float] = None
    risk_threshold_lower: Optional[float] = None


# ---------------------------------------------------------------------------
# 通道基类
# ---------------------------------------------------------------------------


class BaseChannel(ABC):
    """
    32 维通道基类。

    子类必须实现:
      - _organ_response(signal) → OrganState
      - _compute_sensation(organ_state, signal) → value_raw, intensity, label

    子类可选覆盖:
      - _to_medical_value(value_raw) → float  (默认: value_raw 线性映射到医学指标)
      - _deviation_formula(medical_value, baseline) → float  (默认: medical_value - baseline)
    """

    def __init__(self, config: DimConfig) -> None:
        self.cfg = config
        self._last_result: Optional[SensationResult] = None

    # ------------------------------------------------------------------
    # 公共入口: signal → SensationResult
    # ------------------------------------------------------------------

    def process(self, signal: SignalInput) -> SensationResult:
        """
        通道处理主入口。

        执行顺序:
          1. 信号校验 (validate_signal)
          2. 器官响应 (_organ_response) — 子类实现
          3. 体感计算 (_compute_sensation) — 子类实现
          4. 医学映射 (to_medical)
          5. 组装输出 (assemble_result)
        """
        self.validate_signal(signal)

        organ_state = self._organ_response(signal)
        value_raw, intensity, sensation_label = self._compute_sensation(organ_state, signal)

        medical_value = self._to_medical_value(value_raw, organ_state)
        deviation = self._deviation_formula(medical_value)
        health_level = HealthLevel.from_deviation(deviation)

        result = SensationResult(
            dim_id=self.cfg.dim_id,
            dim_key=self.cfg.dim_key,
            category=self.cfg.category,
            value_raw=round(value_raw, 4),
            intensity=intensity,
            sensation_label=sensation_label,
            medical_metric_name=self.cfg.medical_metric_name,
            medical_value=round(medical_value, 4),
            medical_unit=self.cfg.medical_unit,
            medical_baseline=self.cfg.medical_baseline,
            deviation=round(deviation, 2),
            health_level=health_level,
            evidence_text=signal.raw_input_text,
            organ_state=organ_state,
            sibling_dims=list(self.cfg.sibling_dims),
        )
        self._last_result = result
        return result

    # ------------------------------------------------------------------
    # 子类必须实现
    # ------------------------------------------------------------------

    @abstractmethod
    def _organ_response(self, signal: SignalInput) -> OrganState:
        """
        器官/激素/神经对外部信号的响应。

        子类根据信号参数计算器官激活状态，输出量化指标。
        禁止使用 LLM —— 全部规则公式。
        """
        ...

    @abstractmethod
    def _compute_sensation(
        self, organ_state: OrganState, signal: SignalInput
    ) -> tuple[float, Intensity, str]:
        """
        从器官状态计算主观体感。

        Returns:
          (value_raw, intensity, sensation_label)
          value_raw: -1.0(极度负向) ~ 0(中性) ~ 1.0(极度正向)
          intensity: low/medium/high/extreme
          sensation_label: 中文正向或负向体感描述
        """
        ...

    # ------------------------------------------------------------------
    # 医学映射（子类可覆盖）
    # ------------------------------------------------------------------

    def _to_medical_value(self, value_raw: float, organ_state: OrganState) -> float:
        """
        将 -1.0~1.0 体感值映射为真人医学指标数值。

        默认: 线性映射 value_raw → [baseline*0.3, baseline*2.0]
        子类可覆盖为更精确的生理曲线。
        """
        abs_max = max(abs(self.cfg.medical_baseline * 0.7), 1.0)
        return self.cfg.medical_baseline + value_raw * abs_max

    def _deviation_formula(self, medical_value: float) -> float:
        """
        计算医学指标偏移量（相对瑶光基准零点）。

        偏移 ≥ 0: 正常或优于基准
        偏移 < 0: 低于基准

        对于 baseline=0 的指标（如下降百分比），以危险阈值为参考：
          deviation = -medical_value / danger_ref * 100
        """
        if self.cfg.medical_baseline == 0:
            if medical_value == 0:
                return 0.0
            # 用危险阈值作为参考尺度
            if self.cfg.danger_threshold_upper and self.cfg.danger_threshold_upper > 0:
                return - (medical_value / self.cfg.danger_threshold_upper) * 100
            if self.cfg.danger_threshold_lower and self.cfg.danger_threshold_lower < 0:
                return (medical_value / abs(self.cfg.danger_threshold_lower)) * 100
            # 极端fallback: 不允许 inf
            return medical_value * -10.0 if medical_value < 0 else medical_value * 10.0
        baseline = self.cfg.medical_baseline
        return ((medical_value - baseline) / baseline) * 100

    # ------------------------------------------------------------------
    # 信号校验
    # ------------------------------------------------------------------

    def validate_signal(self, signal: SignalInput) -> None:
        """子类可覆盖以添加维度特定的信号校验。"""
        if not signal.source_channel:
            raise ValueError(f"[D{self.cfg.dim_id}] source_channel 为空——信号来源不明")

    # ------------------------------------------------------------------
    # 安全阈值快速判断
    # ------------------------------------------------------------------

    def is_danger(self, medical_value: float) -> bool:
        """当前医学值是否触达危险阈值。"""
        if self.cfg.danger_threshold_upper is not None and medical_value > self.cfg.danger_threshold_upper:
            return True
        if self.cfg.danger_threshold_lower is not None and medical_value < self.cfg.danger_threshold_lower:
            return True
        return False

    def is_risk(self, medical_value: float) -> bool:
        """当前医学值是否在风险区间。"""
        if self.is_danger(medical_value):
            return True
        if self.cfg.risk_threshold_upper is not None and medical_value > self.cfg.risk_threshold_upper:
            return True
        if self.cfg.risk_threshold_lower is not None and medical_value < self.cfg.risk_threshold_lower:
            return True
        return False

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def clamp(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
        return max(lo, min(hi, value))

    @staticmethod
    def to_intensity(abs_value: float) -> Intensity:
        if abs_value >= 0.75:
            return Intensity.EXTREME
        if abs_value >= 0.5:
            return Intensity.HIGH
        if abs_value >= 0.25:
            return Intensity.MEDIUM
        return Intensity.LOW

    @property
    def last_result(self) -> Optional[SensationResult]:
        return self._last_result
