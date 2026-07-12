"""
domain_yaoling — 瑶灵仿生认知域 · Harris 实例
================================================
全局单例: harris_l_global
瑶灵域负责: 人格生成 / 情感调控 / 三库记忆炼化 / 欲望栈 / 思念引擎
allow_dynamic_workflow = False (躯体部分只允许静态流水线)
"""

import sys
from pathlib import Path

_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from common.harris_core import HarrisOrchestrator


class SystemBus:
    """域级系统总线占位 — 后续对接 GlobalBusClient。"""

    def __init__(self, domain_tag: str) -> None:
        self.domain_tag = domain_tag
        self.probe_pool = None


system_bus_l = SystemBus("l")
harris_l_global = HarrisOrchestrator(None, system_bus_l)
