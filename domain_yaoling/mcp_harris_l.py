"""
domain_yaoling — 瑶灵域 MCP 服务入口
======================================
启动方式:  python mcp_harris_l.py
注册方式:  claude mcp add harris-l -- python D:/wenstar/wenstar_os/domain_yaoling/mcp_harris_l.py

提供工具:
  - run_static_workflow: 瑶灵体感流水线 (32通道→安全守门→快照发射)
  - query_global_memory: 跨域记忆检索 (存根)
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# 静态工作流 YAML 加载 (用于校验)
# ---------------------------------------------------------------------------

_WORKFLOW_DIR = Path(__file__).resolve().parent / "workflows"

VALID_WORKFLOWS = {
    "wf_sensation_pipeline": "wf_sensation_pipeline.yaml",
    "wf_safety_gate": "wf_safety_gate.yaml",
    "wf_yaoling_snapshot": "wf_yaoling_snapshot.yaml",
}


def _load_workflow_yaml(filename: str) -> str:
    path = _WORKFLOW_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"瑶灵域静态工作流文件缺失: {path}")
    return path.read_text(encoding="utf-8")

# 启动时预加载验证
for wf_id, filename in VALID_WORKFLOWS.items():
    _load_workflow_yaml(filename)

# ---------------------------------------------------------------------------
# MCP 应用
# ---------------------------------------------------------------------------

app = FastMCP("harris-l-mcp")


@app.tool(name="run_static_workflow")
async def yaoling_sensation_pipeline(
    workflow_id: str,
    task: str,
    constraints: Optional[Dict] = None,
) -> str:
    """
    瑶灵域 32D 体感流水线 — 信号→32通道器官响应→安全守门→快照发射。

    Args:
        workflow_id: wf_sensation_pipeline | wf_safety_gate | wf_yaoling_snapshot
        task: 任务描述
        constraints: {
            "dna_root_id": "DNA-20260712-1430-001",
            "location_fingerprint": "home.bedroom.night",
            "medical_baseline_version": "YAOGUANG-MED-001",
            "raw_input_text": "用户输入文本",
            "interpersonal_labels": ["partner"],
            "temporal_context": {"time_of_day":"evening","season":"summer","weather":"clear","location":"bedroom"},
            "environmental_params": {"temperature":22,"noise_db":35,"light_lux":200},
            "duration_context": {"hours_sitting":5,"work_duration_hours":8,"sleep_hours":7,"hours_since_last_chat":2},
        }
    """
    constraints = constraints or {}

    # 校验
    dna_root_id = constraints.get("dna_root_id", "")
    if not dna_root_id:
        return json.dumps({"code": -1, "msg": "缺少 dna_root_id"}, ensure_ascii=False)
    location = constraints.get("location_fingerprint", "")
    if not location:
        return json.dumps({"code": -1, "msg": "缺少 location_fingerprint"}, ensure_ascii=False)
    if workflow_id not in VALID_WORKFLOWS:
        return json.dumps({"code": -1, "msg": f"未知工作流: {workflow_id}，可用: {list(VALID_WORKFLOWS.keys())}"}, ensure_ascii=False)

    try:
        from workflow_executor import run_pipeline as _run_pipeline

        result = _run_pipeline(
            raw_text=constraints.get("raw_input_text", task),
            dna_root_id=dna_root_id,
            location_fingerprint=location,
            source_channel=constraints.get("source_channel", "yaoguang_snapshot"),
            scene_tags=constraints.get("scene_tags", []),
            interpersonal_labels=constraints.get("interpersonal_labels", []),
            environmental_params=constraints.get("environmental_params"),
            temporal_context=constraints.get("temporal_context"),
            duration_context=constraints.get("duration_context"),
        )

        vs = result.get("snapshot", {}).get("vital_signs", {})
        return json.dumps(
            {
                "code": result.get("code", 0),
                "workflow_id": workflow_id,
                "phase": result.get("phase", "?"),
                "overall_health": result.get("snapshot", {}).get("overall_health", "unknown"),
                "vital_signs": {
                    "heart_rate": vs.get("heart_rate", 0),
                    "blood_pressure": f"{vs.get('blood_pressure_sys',0):.0f}/{vs.get('blood_pressure_dia',0):.0f}",
                    "cortisol_avg": vs.get("cortisol_avg", 0),
                    "pleasure_hormone_avg": vs.get("pleasure_hormone_avg", 0),
                },
                "danger_count": result.get("danger_count", 0),
                "safety_reject": result.get("safety_reject", False),
                "reject_reason": result.get("reject_reason", ""),
                "protobuf_ready": result.get("protobuf_ready", False),
            },
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps({"code": -2, "error": str(e), "workflow_id": workflow_id}, ensure_ascii=False)


@app.tool()
async def query_global_memory(
    vector: list[float],
    domain_filter: Optional[str] = None,
    top_k: int = 5,
) -> str:
    """跨域记忆检索 (存根 — 后续对接三库+ZVEC)。"""
    return json.dumps({"code": 0, "memory_result": {"result": []}}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

async def main() -> None:
    await app.run_stdio_async()


if __name__ == "__main__":
    asyncio.run(main())
