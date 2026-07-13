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
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from common.base_mcp_harris import BaseHarrisMCP, DomainConfig
from harris_g_instance import harris_g_global
from workflow_executor import YaoguangWorkflowExecutor

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
# 瑶光域全局执行器
# ---------------------------------------------------------------------------

yaoguang_executor = YaoguangWorkflowExecutor()

# ---------------------------------------------------------------------------
# YaoguangMCP — 继承 BaseHarrisMCP，串联瑶光 32 通道执行器
# ---------------------------------------------------------------------------


class YaoguangMCP(BaseHarrisMCP):
    """瑶光域 MCP — 在基类基础上重写 run_static_workflow，路由到 32 维客观通道。"""

    def __init__(self, cfg: DomainConfig, harris_instance, executor: YaoguangWorkflowExecutor) -> None:
        self._yaoguang = executor
        super().__init__(cfg, harris_instance)
        # 基类 _register_core_tools 已注册 run_static_workflow
        # FastMCP 不允许同名覆盖，所以先移除基类版本，再注册瑶光版本
        self.app._tool_manager._tools.pop("run_static_workflow", None)
        self._register_yaoguang_override()

    # ------------------------------------------------------------------
    # 覆盖 run_static_workflow — 路由瑶光 workflow 到 32 通道执行器
    # ------------------------------------------------------------------

    def _register_yaoguang_override(self) -> None:
        """重新注册 run_static_workflow，将瑶光 3 个 workflow 路由到真执行器。"""

        _executor = self._yaoguang

        @self.app.tool()
        async def run_static_workflow(
            workflow_id: str,
            task: str,
            constraints: Optional[Dict] = None,
        ) -> str:
            """瑶光域静态工作流执行 — 路由到 32 维客观通道计算。

            支持的 workflow_id:
              wf_objective_env_sample  — 6D 环境感知快照
              wf_location_fingerprint  — 标准化区位指纹
              wf_perception_filter     — 全 32 维客观参数快照
              wf_emotion_sample        — 旧别名 (等同于 wf_objective_env_sample)
            """
            constraints = constraints or {}

            # ── 路由: 瑶光专用 workflow → 32 通道执行器 ──
            if workflow_id in ("wf_objective_env_sample", "wf_emotion_sample"):
                try:
                    loc = constraints.get("location_fingerprint", "")
                    dn = constraints.get("dna_root_id", "YAOGUANG-" + str(hash(task))[:16])
                    ts = constraints.get("timestamp_ms")
                    env6 = _executor.run_env_sample(
                        location_fingerprint=loc,
                        dna_root_id=dn,
                        timestamp_ms=ts,
                        environmental_params=constraints.get("environmental_params"),
                        temporal_context=constraints.get("temporal_context"),
                        duration_context=constraints.get("duration_context"),
                    )
                    return json.dumps({
                        "code": 0,
                        "workflow_id": workflow_id,
                        "env_6d": env6.to_dict(),
                    }, ensure_ascii=False)
                except Exception as e:
                    return json.dumps({"code": -2, "error": str(e), "workflow_id": workflow_id}, ensure_ascii=False)

            elif workflow_id == "wf_location_fingerprint":
                try:
                    result = _executor.run_location_fingerprint(
                        scene_context=constraints.get("scene_context", task),
                        known_scene_id=constraints.get("known_scene_id", ""),
                        known_sub_zone=constraints.get("known_sub_zone", ""),
                    )
                    return json.dumps({"code": 0, "workflow_id": workflow_id, **result}, ensure_ascii=False)
                except Exception as e:
                    return json.dumps({"code": -2, "error": str(e), "workflow_id": workflow_id}, ensure_ascii=False)

            elif workflow_id == "wf_perception_filter":
                try:
                    dn = constraints.get("dna_root_id", "")
                    if not dn:
                        return json.dumps(
                            {"code": -1, "msg": "缺少 dna_root_id — 无全局锚点拒绝输出"},
                            ensure_ascii=False,
                        )
                    loc = constraints.get("location_fingerprint", "")
                    if not loc:
                        return json.dumps(
                            {"code": -1, "msg": "缺少 location_fingerprint — 无区位拒绝输出"},
                            ensure_ascii=False,
                        )
                    snapshot = _executor.run_full_snapshot(
                        dna_root_id=dn,
                        location_fingerprint=loc,
                        timestamp_ms=constraints.get("timestamp_ms"),
                        environmental_params=constraints.get("environmental_params"),
                        temporal_context=constraints.get("temporal_context"),
                        duration_context=constraints.get("duration_context"),
                        interpersonal_labels=constraints.get("interpersonal_labels"),
                        activity_context=constraints.get("activity_context"),
                    )
                    return json.dumps({
                        "code": 0,
                        "workflow_id": workflow_id,
                        "snapshot": snapshot.to_dict(),
                    }, ensure_ascii=False)
                except Exception as e:
                    return json.dumps({"code": -2, "error": str(e), "workflow_id": workflow_id}, ensure_ascii=False)

            elif workflow_id == "wf_world_unlock":
                try:
                    from unlock_dispatcher import handle_unlock_event
                    result = handle_unlock_event(
                        event_type=constraints.get("event_type", "custom"),
                        dna_root_id=constraints.get("dna_root_id", "YAOGUANG-" + str(hash(task))[:16]),
                        event_description=task,
                        location_fingerprint=constraints.get("location_fingerprint", ""),
                        scene_type=constraints.get("scene_type", "home"),
                        time_of_day=constraints.get("time_of_day", "afternoon"),
                        hour=constraints.get("hour", 14),
                        weather=constraints.get("weather", "clear"),
                        season=constraints.get("season", "summer"),
                        outdoor_temp_c=constraints.get("outdoor_temp_c", 28.0),
                        day_type=constraints.get("day_type", "workday"),
                        crowd_density=constraints.get("crowd_density", 0.1),
                        noise_db_override=constraints.get("noise_db_override"),
                        interpersonal_labels=constraints.get("interpersonal_labels", []),
                        activity_context=constraints.get("activity_context"),
                        extra_params=constraints.get("extra_params", {}),
                    )
                    return json.dumps(result, ensure_ascii=False)
                except Exception as e:
                    return json.dumps({"code": -2, "error": str(e), "workflow_id": workflow_id}, ensure_ascii=False)

            else:
                return json.dumps(
                    {"code": -1, "msg": f"未知工作流: {workflow_id}，瑶光域可用: wf_objective_env_sample | wf_location_fingerprint | wf_perception_filter | wf_emotion_sample"},
                    ensure_ascii=False,
                )


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
    bridge = YaoguangMCP(yaoguang_config, harris_g_global, yaoguang_executor)
    await bridge.start_stdio()


if __name__ == "__main__":
    asyncio.run(main())
