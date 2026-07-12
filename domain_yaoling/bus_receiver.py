"""
bus_receiver.py — 瑶灵域 总线消息接收器
==========================================
连接 global_bus :9100, 监听跨域指令并执行体感流水线。
"""
import asyncio, json, logging, sys
from pathlib import Path

_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from common.base_mcp_harris import GlobalBusTCPClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-5s | %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("yaoling.bus")


async def handle_command(msg: dict) -> dict:
    """处理传入的总线指令，执行瑶灵工作流。"""
    cmd = msg.get("cmd", "")
    payload = msg.get("payload", {})
    logger.info("收到跨域指令: %s → %s", cmd, payload.get("workflow_id", "?"))

    try:
        from workflow_executor import run_pipeline as _run_yaoling_pipeline

        result = _run_yaoling_pipeline(
            raw_text=payload.get("task", payload.get("raw_input_text", "")),
            dna_root_id=payload.get("dna_root_id", "TT00000001M01SYS0000000"),
            location_fingerprint=payload.get("location_fingerprint", "home.default.default"),
            source_channel=payload.get("source_channel", "yaoguang_snapshot"),
            scene_tags=payload.get("scene_tags", []),
            interpersonal_labels=payload.get("interpersonal_labels", []),
            environmental_params=payload.get("environmental_params"),
            temporal_context=payload.get("temporal_context"),
            duration_context=payload.get("duration_context"),
        )
        vs = result.get("snapshot", {}).get("vital_signs", {})
        return {
            "status": "ok",
            "code": 0,
            "phase": result.get("phase", "?"),
            "overall_health": result.get("snapshot", {}).get("overall_health", "unknown"),
            "danger_count": result.get("danger_count", 0),
            "vital_signs": {
                "heart_rate": vs.get("heart_rate", 0),
                "blood_pressure": f"{vs.get('blood_pressure_sys', 0):.0f}/{vs.get('blood_pressure_dia', 0):.0f}",
            },
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def main():
    bus = GlobalBusTCPClient(domain_tag="l")
    bus.subscribe("global_alert")
    logger.info("瑶灵总线接收器启动...")
    await bus.connect()

    if not bus.connected:
        logger.error("总线连接失败")
        return

    logger.info("✓ 瑶灵监听中 (wf_sensation_pipeline / wf_safety_gate)")

    while bus.connected:
        msg = await bus.receive()
        if msg is None:
            await asyncio.sleep(0.5)
            continue
        try:
            result = await handle_command(msg)
            await bus.publish("t", "workflow_result", result)
            logger.info("→ 结果已回传: %s", json.dumps(result, ensure_ascii=False)[:120])
        except Exception as e:
            logger.error("处理失败: %s", e)


if __name__ == "__main__":
    asyncio.run(main())
