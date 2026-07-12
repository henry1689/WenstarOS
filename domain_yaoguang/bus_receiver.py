"""
bus_receiver.py — 瑶光域 总线消息接收器
==========================================
连接 global_bus :9100, 监听跨域指令并执行 YaoguangWorkflowExecutor。

独立于 MCP 进程——可以单独启动，也可以与 mcp_harris_g.py 共存。
python bus_receiver.py
"""
import asyncio, json, logging, sys
from pathlib import Path

_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from common.base_mcp_harris import GlobalBusTCPClient
from workflow_executor import YaoguangWorkflowExecutor

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-5s | %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("yaoguang.bus")

EXECUTOR = YaoguangWorkflowExecutor()


async def handle_command(msg: dict) -> dict:
    """处理传入的总线指令，执行瑶光工作流。"""
    cmd = msg.get("cmd", "")
    payload = msg.get("payload", {})
    workflow_id = payload.get("workflow_id", "")

    logger.info("收到跨域指令: %s → %s (from %s)", cmd, workflow_id, msg.get("source", "?"))

    try:
        if workflow_id == "wf_objective_env_sample":
            result = EXECUTOR.run_env_sample(
                dna_root_id=payload.get("dna_root_id", ""),
                location_fingerprint=payload.get("location_fingerprint", "home.default.default"),
                environmental_params=payload.get("environmental_params"),
                temporal_context=payload.get("temporal_context"),
                duration_context=payload.get("duration_context"),
            )
            return {"status": "ok", "workflow": workflow_id, "result": result.to_dict()}

        elif workflow_id == "wf_location_fingerprint":
            result = EXECUTOR.run_location_fingerprint(
                scene_context=payload.get("task", ""),
                known_scene_id=payload.get("scene_id", ""),
                known_sub_zone=payload.get("sub_zone", ""),
            )
            return {"status": "ok", "workflow": workflow_id, "result": result}

        elif workflow_id == "wf_perception_filter":
            result = EXECUTOR.run_full_snapshot(
                dna_root_id=payload.get("dna_root_id", "TT00000001M01SYS0000000"),
                location_fingerprint=payload.get("location_fingerprint", "home.default.default"),
                environmental_params=payload.get("environmental_params"),
                temporal_context=payload.get("temporal_context"),
                duration_context=payload.get("duration_context"),
                interpersonal_labels=payload.get("interpersonal_labels", []),
            )
            return {"status": "ok", "workflow": workflow_id, "result": result.to_dict()}

        else:
            return {"status": "unknown_workflow", "workflow_id": workflow_id, "available": ["wf_objective_env_sample", "wf_location_fingerprint", "wf_perception_filter"]}

    except Exception as e:
        logger.error("执行失败: %s", e)
        return {"status": "error", "workflow": workflow_id, "error": str(e)}


async def main():
    bus = GlobalBusTCPClient(domain_tag="g")
    bus.subscribe("global_alert")

    logger.info("瑶光总线接收器启动 — 连接 :9100...")
    await bus.connect()

    if not bus.connected:
        logger.error("总线连接失败，退出")
        return

    logger.info("✓ 瑶光监听中 (wf_objective_env_sample / wf_location_fingerprint / wf_perception_filter)")

    while bus.connected:
        msg = await bus.receive()
        if msg is None:
            await asyncio.sleep(0.5)
            continue

        try:
            result = await handle_command(msg)
            # 尝试发回确认 (publish 到 tianquan_snapshot)
            await bus.publish("t", "workflow_result", result)
            logger.info("→ 结果已回传: %s", json.dumps(result, ensure_ascii=False)[:120])
        except Exception as e:
            logger.error("处理失败: %s", e)


if __name__ == "__main__":
    asyncio.run(main())
