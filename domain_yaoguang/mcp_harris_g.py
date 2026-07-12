"""
domain_yaoguang — 瑶光域 MCP 服务入口
======================================
启动方式:  python mcp_harris_g.py
注册方式:  claude mcp add harris-g -- python mcp_harris_g.py

瑶光域约束 (对应白皮书 §2.2 六层架构):
  - allow_dynamic_workflow = True
    仅「环境长期推演 / 时序调度 / 世界快照」类任务放行 (白名单门控)
  - 静态流水线 (3 个): 客观环境采样 / 区位指纹建模 / 32D 感知滤波
  - 订阅: global_alert / tianquan_snapshot / yaoling_state

铁律:
  - 仅输出纯量化客观参数，无主观情绪体感
  - 32 维向量分层生成，禁止 LLM 直接输出浮点数值
  - 静态流水线调用时强制传入 constraints (含 dna_root_id / location_fingerprint)
"""

import asyncio
import sys
from pathlib import Path

_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from common.base_mcp_harris import BaseHarrisMCP, DomainConfig
from harris_g_instance import harris_g_global

# ---------------------------------------------------------------------------
# 加载静态工作流 YAML
# ---------------------------------------------------------------------------

_WF_DIR = Path(__file__).resolve().parent / "workflows"


def _load_yaml(filename: str) -> str:
    path = _WF_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"# MISSING: {path}"


# ---------------------------------------------------------------------------
# 瑶光域白名单 — 仅以下任务类型允许动态工作流
# ---------------------------------------------------------------------------

YAOGUANG_DYNAMIC_ALLOWLIST = [
    "环境长期推演",
    "时序调度",
    "世界快照",
    "环境模拟",
    "长期推演",
    "场景解锁",
    "规则库扩展",
    "客观世界演算",
]

# ---------------------------------------------------------------------------
# 瑶光域配置
# ---------------------------------------------------------------------------

yaoguang_config = DomainConfig(
    domain_name="瑶光感知采集域",
    domain_tag="g",
    default_rigid_pool={
        "wf_objective_env_sample":   _load_yaml("wf_objective_env_sample.yaml"),
        "wf_location_fingerprint":   _load_yaml("wf_location_fingerprint.yaml"),
        "wf_perception_filter":      _load_yaml("wf_perception_filter.yaml"),
        # 保留旧 ID 做向后兼容别名
        "wf_emotion_sample":         _load_yaml("wf_objective_env_sample.yaml"),
    },
    guard_token_quota=60_000,
    allow_dynamic_workflow=True,
    dynamic_workflow_allowlist=YAOGUANG_DYNAMIC_ALLOWLIST,
    subscribe_cross_channel=[
        "global_alert",
        "tianquan_snapshot",
        "yaoling_state",
    ],
)

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


async def main() -> None:
    bridge = BaseHarrisMCP(yaoguang_config, harris_g_global)
    await bridge.start_stdio()


if __name__ == "__main__":
    asyncio.run(main())
