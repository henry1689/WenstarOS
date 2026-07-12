"""
domain_tianquan — 天权域 MCP 服务入口
======================================
启动方式:  python mcp_harris_t.py
注册方式:  claude mcp add harris-t -- python mcp_harris_t.py

天权域约束:
  - allow_dynamic_workflow = True (超大架构重构时允许动态生成)
  - 订阅: global_alert / yaoling_state / yaoguang_snapshot
  - 发布: tianquan_snapshot → 瑶灵 / yaoguang_snapshot → 瑶光
"""

import asyncio
import os
import sys
from pathlib import Path

_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from common.base_mcp_harris import BaseHarrisMCP, DomainConfig
from harris_t_instance import harris_t_global

# ---------------------------------------------------------------------------
# 运行模式
# ---------------------------------------------------------------------------

RUN_MODE = os.environ.get("RUN_MODE", "prod")

# ---------------------------------------------------------------------------
# 静态工作流 YAML 加载
# ---------------------------------------------------------------------------

_WORKFLOW_DIR = Path(__file__).resolve().parent / "workflows"


def _load_workflow_yaml(filename: str) -> str:
    """从 workflows/ 目录加载 YAML 工作流文件。文件缺失直接报错，拒绝启动。"""
    path = _WORKFLOW_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"天权域静态工作流文件缺失: {path}\n"
            f"请确认 {filename} 已部署到 workflows/ 目录。\n"
            f"天权工程规范 (TIANQUAN_DOMAIN_SPEC.md §2.1) 要求四套工作流全部就位。"
        )
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 天权域配置
# ---------------------------------------------------------------------------

tianquan_config = DomainConfig(
    domain_name="天权算力工程域",
    domain_tag="t",
    default_rigid_pool={
        # ── 工程四大流水线 ──
        "wf_code_review":          _load_workflow_yaml("wf_code_review.yaml"),
        "wf_arch_refactor":        _load_workflow_yaml("wf_arch_refactor.yaml"),
        "wf_sql_governance":       _load_workflow_yaml("wf_sql_governance.yaml"),
        "wf_knowledge_organize":   _load_workflow_yaml("wf_knowledge_organize.yaml"),
        "wf_test_governance":      _load_workflow_yaml("wf_test_governance.yaml"),
        "wf_change_report":        _load_workflow_yaml("wf_change_report.yaml"),
        "wf_dependency_audit":     _load_workflow_yaml("wf_dependency_audit.yaml"),
        "wf_log_analysis":         _load_workflow_yaml("wf_log_analysis.yaml"),
        "wf_config_drift":         _load_workflow_yaml("wf_config_drift.yaml"),
        "wf_resource_scan":        _load_workflow_yaml("wf_resource_scan.yaml"),
    },
    guard_token_quota=120_000,
    allow_dynamic_workflow=True,
    allow_cross_domain=False,  # V2.0 MH-1: 天权不直接跨域通信, 由 Master-Harris 统一发出
    subscribe_cross_channel=[
        "global_alert",
        "yaoling_state",
        "yaoguang_snapshot",
    ],
)

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


async def main() -> None:
    """MCP 服务入口 — 仅在 RUN_MODE=dev 时启动。"""
    bridge = BaseHarrisMCP(tianquan_config, harris_t_global)
    await bridge.start_stdio()


if __name__ == "__main__":
    if RUN_MODE != "dev":
        print(
            "=" * 60,
            "\n"
            "  ⛔ 天权域在生产模式下不可独立启动。\n"
            "\n"
            "  天权是太虚境的内核算力组件，由主进程通过\n"
            "  tianquan_rpc_server.py (stdin/stdout RPC) 调用。\n"
            "\n"
            "  如需独立调试，请设置环境变量:\n"
            "    set RUN_MODE=dev    (Windows CMD)\n"
            "    $env:RUN_MODE='dev' (PowerShell)\n"
            "    export RUN_MODE=dev (Git Bash)\n"
            "\n"
            f"  当前 RUN_MODE={RUN_MODE!r}\n"
            "\n" + "=" * 60,
            file=sys.stderr,
        )
        sys.exit(1)

    asyncio.run(main())
