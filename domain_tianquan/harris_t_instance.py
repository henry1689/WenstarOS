"""
domain_tianquan — 天权算力工程域 · Harris 实例
================================================
全局单例: harris_t_global
"""

import sys
from pathlib import Path

# 确保 common 可导入
_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from common.harris_core import HarrisOrchestrator


# ---------------------------------------------------------------------------
# 简易占位总线 — 后续对接 GlobalBusClient 完善
# ---------------------------------------------------------------------------


class SystemBus:
    """域级系统总线占位。"""

    def __init__(self, domain_tag: str) -> None:
        self.domain_tag = domain_tag
        self.probe_pool = None


# ---------------------------------------------------------------------------
# 天权域全局 Harris 实例
# ---------------------------------------------------------------------------

system_bus_t = SystemBus("t")
harris_t_global = HarrisOrchestrator(None, system_bus_t)
