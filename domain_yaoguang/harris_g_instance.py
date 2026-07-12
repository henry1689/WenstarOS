"""
domain_yaoguang — 瑶光感知采集域 · Harris 实例
================================================
全局单例: harris_g_global

瑶光域职责（对应白皮书 §2.2 六层架构）:
  第一层 自然时空      — 气象/季节/昼夜节律客观演算 (D8, D26)
  第二层 空间建模      — 场景区位指纹生成与空间元数据 (D21-D25)
  第三层 人体生理规则  — 标准生理基线输出 (D1-D7)
  第四层 人文社交      — 社交规则/礼仪规范客观约束 (D9-D20)
  第五层 资源拓展      — 场景/生理/人文规则库动态注册 (D27-D30)
  第六层 通道封装      — 32 维标准数据包上行 (D31-D32)

三体通信:
  上行 → 瑶光 32 维客观参数包 → 太虚境 Hermes
  下行 ← 太虚世界解锁拓展指令

铁律:
  - 仅输出纯量化客观参数，无主观情绪体感
  - 32 维向量分层生成，禁止 LLM 直接输出浮点数值
  - 五级闸门仅太虚侧执行，瑶光不做记忆过滤
"""

import sys
from pathlib import Path

_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from common.harris_core import HarrisOrchestrator


class SystemBus:
    """域级系统总线占位 — 后续对接 GlobalBusClient (global_bus_main.py)。

    当前状态: 占位 — 仅存储 domain_tag，不做实际消息收发。
    升级计划: 对接 global_bus_main.GlobalEventBus，实现三域跨进程消息投递。
    """

    def __init__(self, domain_tag: str) -> None:
        self.domain_tag = domain_tag
        self.probe_pool = None


system_bus_g = SystemBus("g")
harris_g_global = HarrisOrchestrator(None, system_bus_g)
