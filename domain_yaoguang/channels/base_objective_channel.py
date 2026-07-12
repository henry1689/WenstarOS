"""
base_objective_channel.py — 瑶光 32 维客观参数通道基类
======================================================
与瑶灵基类的核心区别:
  - 瑶灵: _organ_response() + _compute_sensation() → 主观体感
  - 瑶光: compute_objective() → 纯客观标准基线值（无情绪、无体感）

每条通道输出:
  - 当前场景下该维度的客观标准值 (medical_baseline 的上下文修正)
  - 标准参考区间 [low, high]
  - 输出单位
  - 无任何主观偏移量计算（偏移由太虚比对瑶灵主观值后生成）

设计约束 (白皮书 §2.2):
  - 仅输出纯量化客观参数，无主观情绪体感
  - 所有数值由规则公式计算，禁止 LLM 直接生成浮点
  - 接收 constraints 中的环境参数作为输入
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ObjCategory(str, Enum):
    PHYSICAL_BODY = "physical_body"        # D1-D8
    INNER_SPIRIT = "inner_spirit"          # D9-D14
    SOCIAL_BONDS = "social_bonds"          # D15-D20
    SPATIOTEMPORAL = "spatiotemporal"      # D21-D26
    DYNAMIC_GROWTH = "dynamic_growth"      # D27-D32


@dataclass
class ObjDimConfig:
    """客观维度静态配置。"""
    dim_id: int
    dim_key: str
    category: ObjCategory
    label_cn: str
    medical_metric_name: str         # 真人临床指标名称
    medical_baseline: float          # 标准健康零点
    medical_unit: str                # 单位
    standard_range: Tuple[float, float]  # 正常参考区间 (low, high)
    sibling_dims: List[int] = field(default_factory=list)
    description: str = ""


@dataclass
class ObjectiveResult:
    """单个维度的客观参数输出——对应 YaoguangUpstream 格式。"""
    dim_id: int
    dim_key: str
    category: ObjCategory
    label_cn: str
    # 客观标准值
    standard_value: float            # 当前场景的客观标准基线值
    standard_unit: str
    standard_range_low: float        # 正常参考下限
    standard_range_high: float       # 正常参考上限
    # 输入上下文
    evidence_context: Dict[str, Any] = field(default_factory=dict)
    # 元数据
    dna_root_id: str = ""
    location_fingerprint: str = ""
    timestamp_ms: int = 0


class BaseObjectiveChannel(ABC):
    """32 维客观参数通道基类。

    子类必须实现:
      - compute_objective(env, temporal, duration) → ObjectiveResult

    铁律:
      - 禁止输出任何主观情绪/体感词汇
      - 禁止 LLM 直接生成浮点值
      - 全部规则公式计算
    """

    def __init__(self, config: ObjDimConfig) -> None:
        self.cfg = config

    # ------------------------------------------------------------------
    # 公共入口
    # ------------------------------------------------------------------

    def process(
        self,
        environmental_params: Dict[str, float],
        temporal_context: Dict[str, Any],
        duration_context: Dict[str, float],
        interpersonal_labels: Optional[List[str]] = None,
        dna_root_id: str = "",
        location_fingerprint: str = "",
        timestamp_ms: int = 0,
    ) -> ObjectiveResult:
        result = self.compute_objective(
            environmental_params, temporal_context, duration_context,
            interpersonal_labels or [],
        )
        result.dna_root_id = dna_root_id
        result.location_fingerprint = location_fingerprint
        result.timestamp_ms = timestamp_ms
        return result

    # ------------------------------------------------------------------
    # 子类必须实现
    # ------------------------------------------------------------------

    @abstractmethod
    def compute_objective(
        self,
        env: Dict[str, float],
        temporal: Dict[str, Any],
        duration: Dict[str, float],
        interpersonal: List[str],
    ) -> ObjectiveResult:
        """计算当前场景下该维度的客观标准参数。"""
        ...

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def clamp(value: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, value))

    def make_result(self, standard_value: float, **extra_context) -> ObjectiveResult:
        return ObjectiveResult(
            dim_id=self.cfg.dim_id,
            dim_key=self.cfg.dim_key,
            category=self.cfg.category,
            label_cn=self.cfg.label_cn,
            standard_value=round(standard_value, 2),
            standard_unit=self.cfg.medical_unit,
            standard_range_low=self.cfg.standard_range[0],
            standard_range_high=self.cfg.standard_range[1],
            evidence_context={
                "metric": self.cfg.medical_metric_name,
                "baseline": self.cfg.medical_baseline,
                **extra_context,
            },
        )
