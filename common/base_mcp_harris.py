"""
BaseHarrisMCP — 三域 (天权 / 瑶灵 / 瑶光) 统一 MCP 基类 V2.0
======================================================================
每个域继承此基类，自动获得:
  - run_static_workflow      (静态 YAML 工作流)
  - generate_dynamic_workflow (动态工作流生成, 需 allow_dynamic_workflow=True)
  - query_global_memory      (跨域记忆检索)

仅瑶灵/瑶光额外获得:
  - send_cross_domain_command (接收/响应跨域指令 — 不主动发起, MH-1)

天权域 (tianquan) 不注册 send_cross_domain_command:
  天权内置太虚境, 跨域指令由 Master-Harris 统一发出, 天权不直接通信外设。

适配: MCP Python SDK 1.28.0 (FastMCP + @tool 装饰器)
     Harris-YAML V2.0 / Master-Harris V1.0 / DNA V2.0
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP
from dataclasses import dataclass, field

from .harris_core import HarrisOrchestrator, HarrisDslParser
from .harris_core_v2 import (
    HarrisOrchestratorV2,
    HarrisDslParserV2,
    WorkflowContextV2,
    AgentType,
)

logger = logging.getLogger("harris.mcp")

# ---------------------------------------------------------------------------
# 总线常量
# ---------------------------------------------------------------------------

DEFAULT_BUS_HOST = "127.0.0.1"
DEFAULT_BUS_PORT = 9100


# ---------------------------------------------------------------------------
# 占位存根 — 后续实现真实逻辑
# ---------------------------------------------------------------------------


class GlobalMemoryRetriever:
    """全局记忆检索引擎存根。

    后续对接三库 (砂金 / 金库 / 黑钻) 及 Zvec 向量检索后再实现。
    """

    async def search(
        self,
        vector: list[float],
        domain_filter: Optional[str] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        return {"result": []}


# ---------------------------------------------------------------------------
# TCP 全局总线客户端 (替代原占位存根)
# ---------------------------------------------------------------------------


class GlobalBusTCPClient:
    """
    TCP 全局总线客户端 — 连接到 global_bus_main.py 的 BusTCPServer。

    设计要点:
      - _read_loop 是唯一的 reader，所有服务端响应/推送都由它分发
      - 同步请求 (auth/subscribe/publish) 靠 req_id + Future 匹配
      - 异步推送 (message) 入 incoming 队列
    """

    def __init__(
        self,
        domain_tag: str,
        host: str = DEFAULT_BUS_HOST,
        port: int = DEFAULT_BUS_PORT,
    ) -> None:
        self.domain_tag = domain_tag
        self.host = host
        self.port = port
        self.connected = False

        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

        # 接收队列 — 服务端主动推送的跨域消息
        self.incoming: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

        # 待订阅频道 (connect 前登记，connect 后统一发送)
        self._pending_channels: list[str] = []

        # 请求-响应匹配
        self._req_counter: int = 0
        self._pending: Dict[str, asyncio.Future] = {}

        # 后台读任务
        self._reader_task: Optional[asyncio.Task] = None

    # ------------------------------------------------------------------
    # 连接管理
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """建立 TCP 连接 → auth → flush 订阅渠道。"""
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=5.0,
            )
        except (ConnectionRefusedError, OSError) as e:
            logger.warning("[BUS] %s 无法连接总线 %s:%s — %s", self.domain_tag, self.host, self.port, e)
            self.connected = False
            return
        except asyncio.TimeoutError:
            logger.warning("[BUS] %s 连接总线超时 %s:%s", self.domain_tag, self.host, self.port)
            self.connected = False
            return

        # 启动后台读取 (auth 的响应也需要它来分发)
        self.connected = True
        self._reader_task = asyncio.create_task(self._read_loop())

        # auth
        auth_resp = await self._request({"type": "auth", "domain": self.domain_tag})
        if auth_resp is None or auth_resp.get("type") != "auth_ok":
            logger.error("[BUS] %s auth 失败: %s", self.domain_tag, auth_resp)
            self.connected = False
            self._close_writer()
            return

        logger.info("[BUS] ✓ %s 已连接到总线", self.domain_tag)

        # 一次性发送所有待订阅频道
        if self._pending_channels:
            sub_resp = await self._request(
                {"type": "subscribe", "channels": list(self._pending_channels)}
            )
            if sub_resp and sub_resp.get("type") == "subscribed":
                logger.info("[BUS] %s 订阅 %s", self.domain_tag, sub_resp.get("channels", []))

    async def disconnect(self) -> None:
        self.connected = False
        if self._reader_task:
            self._reader_task.cancel()
            self._reader_task = None
        self._close_writer()
        # 释放所有等待者
        for fut in self._pending.values():
            if not fut.done():
                fut.set_exception(RuntimeError("总线已断开"))
        self._pending.clear()
        logger.info("[BUS] %s 已断开总线", self.domain_tag)

    def _close_writer(self) -> None:
        if self._writer:
            try:
                self._writer.close()
            except Exception:
                pass
            self._writer = None

    # ------------------------------------------------------------------
    # 频道订阅
    # ------------------------------------------------------------------

    def subscribe(self, channel: str) -> None:
        """登记频道。已连接则立即发送，未连接则连接时统一发送。"""
        if channel not in self._pending_channels:
            self._pending_channels.append(channel)

    # ------------------------------------------------------------------
    # 消息发布
    # ------------------------------------------------------------------

    async def publish(
        self,
        target_domain: str,
        cmd: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """发送跨域指令 → 等待 published 响应。"""
        if not self.connected:
            return {"status": "disconnected", "error": "总线未连接，消息未发送"}

        try:
            resp = await self._request({
                "type": "publish",
                "channel": "global_alert",
                "cmd": cmd,
                "payload": payload,
                "target": target_domain,
            })
            if resp and resp.get("type") == "published":
                return {"status": "ok", "msg_id": resp.get("msg_id"), "delivered": resp.get("delivered", 0)}
            return {"status": "error", "raw": resp}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    # ------------------------------------------------------------------
    # 低层协议: _send + _request (由 _read_loop 统一分发)
    # ------------------------------------------------------------------

    async def _send(self, data: Dict[str, Any]) -> None:
        """写入一行 JSON。"""
        if not self._writer:
            raise RuntimeError("未连接")
        payload = json.dumps(data, ensure_ascii=False) + "\n"
        self._writer.write(payload.encode("utf-8"))
        await self._writer.drain()

    async def _request(self, data: Dict[str, Any], timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """
        发送请求并同步等待响应。

        给每条请求分配 req_id，服务器在响应中原样带回 req_id。
        _read_loop 收到响应后通过 _pending[req_id] 的 Future 唤醒。
        """
        self._req_counter += 1
        req_id = f"req:{self._req_counter}"
        data["req_id"] = req_id

        fut: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[req_id] = fut

        await self._send(data)

        try:
            resp = await asyncio.wait_for(fut, timeout=timeout)
            return resp
        except asyncio.TimeoutError:
            self._pending.pop(req_id, None)
            return None

    async def _read_loop(self) -> None:
        """
        唯一条读取循环。

        读取每一行 JSON → 根据 type 分发:
          - auth_ok / subscribed / published → 通过 req_id 匹配 Future
          - message → incoming 队列 (跨域推送)
        """
        while self.connected and self._reader:
            try:
                line = await self._reader.readline()
            except (ConnectionResetError, BrokenPipeError, OSError):
                self.connected = False
                break

            if not line:
                self.connected = False
                break

            try:
                data = json.loads(line.decode("utf-8").strip())
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type", "")

            if msg_type == "message":
                # 跨域消息推送
                await self.incoming.put(data)
            elif msg_type in ("auth_ok", "subscribed", "published", "error"):
                # 同步请求的响应 — 通过 req_id 匹配 Future
                req_id = data.get("req_id", "")
                if req_id and req_id in self._pending:
                    self._pending.pop(req_id).set_result(data)
                else:
                    logger.debug("[BUS] 孤儿响应 %s: %s", req_id, msg_type)
            else:
                logger.debug("[BUS] 未知消息类型: %s", msg_type)

        logger.info("[BUS] %s 读取循环退出", self.domain_tag)

    async def receive(self) -> Optional[Dict[str, Any]]:
        """非阻塞取一条推送消息。"""
        if self.incoming.empty():
            return None
        return await self.incoming.get()


# ---------------------------------------------------------------------------
# 域配置
# ---------------------------------------------------------------------------


@dataclass
class DomainConfig:
    domain_name: str
    domain_tag: str
    default_rigid_pool: Dict[str, str]
    guard_token_quota: int
    allow_dynamic_workflow: bool
    subscribe_cross_channel: list[str]
    allow_cross_domain: bool = True  # V2.0: 天权=False (MH-1), 瑶灵/瑶光仅接收不主动发起
    dynamic_workflow_allowlist: Optional[list[str]] = None
    # ^ 若为非空列表，则 generate_dynamic_workflow 的 task_outline
    #   必须包含至少一个关键词才放行；若为 None 则不额外限制（但仍需 allow_dynamic_workflow=True）


# ---------------------------------------------------------------------------
# 总线客户端工厂
# ---------------------------------------------------------------------------


def create_bus_client(
    domain_tag: str,
    host: str = DEFAULT_BUS_HOST,
    port: int = DEFAULT_BUS_PORT,
) -> GlobalBusTCPClient:
    """快速创建总线客户端 (供各域 mcp_harris_*.py 调用)。"""
    return GlobalBusTCPClient(domain_tag=domain_tag, host=host, port=port)


# ---------------------------------------------------------------------------
# MCP 基类
# ---------------------------------------------------------------------------


class BaseHarrisMCP:
    """Harris 域 MCP 基类 — 每个域实例化一份。"""

    def __init__(
        self,
        domain_cfg: DomainConfig,
        harris_instance: HarrisOrchestrator,
        bus_client: Optional[GlobalBusTCPClient] = None,
    ) -> None:
        self.cfg = domain_cfg
        self.harris = harris_instance
        self.memory = GlobalMemoryRetriever()
        self.global_bus = bus_client or create_bus_client(domain_cfg.domain_tag)
        self.app = FastMCP(f"harris-{domain_cfg.domain_tag}-mcp")
        self._register_core_tools()

    # ------------------------------------------------------------------
    # 核心工具注册
    # ------------------------------------------------------------------

    def _register_core_tools(self) -> None:

        @self.app.tool()
        async def run_static_workflow(
            workflow_id: str,
            task: str,
            constraints: Optional[Dict] = None,
        ) -> str:
            """从本域 rigid_pool 中取出 YAML，解析并执行静态工作流。

            V2.0 引擎: 优先使用 HarrisDslParserV2 + HarrisOrchestratorV2 (支持约束校验/路由戳/AgentType 感知)。
            若 V2.0 解析失败, 自动降级为 V1.0 引擎 (向后兼容)。
            """
            yaml_text = self.cfg.default_rigid_pool.get(workflow_id)
            if not yaml_text:
                return json.dumps(
                    {"code": -1, "msg": f"不存在该静态工作流: {workflow_id}"},
                    ensure_ascii=False,
                )
            try:
                # ── V2.0 引擎优先 ──
                try:
                    workflow = HarrisDslParserV2.from_yaml_text(yaml_text)
                    orchestrator = HarrisOrchestratorV2(workflow, self.harris.bus)
                except Exception:
                    # 降级 V1.0
                    workflow = HarrisDslParser.from_yaml_text(yaml_text)
                    orchestrator = HarrisOrchestrator(workflow, self.harris.bus)

                result_ctx = await orchestrator.run(task, constraints or {})

                # V2.0 上下文有更多字段
                if isinstance(result_ctx, WorkflowContextV2):
                    return json.dumps(
                        {
                            "code": 0,
                            "data": result_ctx.artifacts,
                            "trace": result_ctx.trace[-20:],
                            "stamp_count": len(result_ctx.route_stamps),
                            "degraded": result_ctx.degraded,
                            "elapsed": result_ctx.metrics.get("elapsed_seconds", 0),
                        },
                        ensure_ascii=False,
                    )
                else:
                    return json.dumps(
                        {"code": 0, "data": result_ctx.artifacts, "trace": result_ctx.trace[-20:]},
                        ensure_ascii=False,
                    )
            except Exception as e:
                return json.dumps({"code": -2, "error": str(e)}, ensure_ascii=False)

        @self.app.tool()
        async def generate_dynamic_workflow(
            task_outline: str,
            mode: str = "flexible",
        ) -> str:
            """根据任务描述动态生成 Harris 工作流 (需本域开启 allow_dynamic_workflow)。

            若域配置了 dynamic_workflow_allowlist，则 task_outline 必须包含
            至少一个白名单关键词才放行。
            """
            if not self.cfg.allow_dynamic_workflow:
                return json.dumps(
                    {"code": -3, "msg": "本域禁止动态生成工作流"},
                    ensure_ascii=False,
                )
            # ── 白名单门控 ──
            if self.cfg.dynamic_workflow_allowlist is not None:
                if not any(
                    kw in task_outline
                    for kw in self.cfg.dynamic_workflow_allowlist
                ):
                    return json.dumps(
                        {
                            "code": -4,
                            "msg": (
                                f"动态工作流被拒绝。task_outline 必须包含以下至少一个关键词: "
                                f"{self.cfg.dynamic_workflow_allowlist}"
                            ),
                        },
                        ensure_ascii=False,
                    )
            # 占位 — 后续接入 LLM 自动生成 DSL
            return json.dumps(
                {"code": 0, "data": {}, "dynamic_dsl": "placeholder"},
                ensure_ascii=False,
            )

        @self.app.tool()
        async def query_global_memory(
            vector: list[float],
            domain_filter: Optional[str] = None,
            top_k: int = 5,
        ) -> str:
            """跨域记忆检索 (向量 + 域过滤 + Top-K)。"""
            res = await self.memory.search(vector, domain_filter, top_k)
            return json.dumps({"code": 0, "memory_result": res}, ensure_ascii=False)

        # ── 跨域通信 (仅瑶灵/瑶光, 天权不注册 — MH-1) ──
        if self.cfg.allow_cross_domain:

            @self.app.tool()
            async def send_cross_domain_command(
                target_domain: str,
                cmd: str,
                payload: Dict,
            ) -> str:
                """接收/响应来自 Master-Harris 的跨域指令。本域不主动发起——仅被动执行。"""
                try:
                    ack = await self.global_bus.publish(target_domain, cmd, payload)
                    return json.dumps({"code": 0, "ack": ack}, ensure_ascii=False)
                except Exception as e:
                    return json.dumps({"code": -5, "error": str(e)}, ensure_ascii=False)

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    async def start_stdio(self) -> None:
        """启动 stdio-MCP 服务。"""
        # 先登记所有待订阅频道，再连接（connect 时一次性 flush）
        for ch in self.cfg.subscribe_cross_channel:
            self.global_bus.subscribe(ch)
        await self.global_bus.connect()
        if not self.global_bus.connected:
            logger.warning(
                "[MCP] %s 总线未连接 — send_cross_domain_command 将返回 disconnected",
                self.cfg.domain_tag,
            )
        await self.app.run_stdio_async()
