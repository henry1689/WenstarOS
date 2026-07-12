"""
global_bus_main — 三域全局消息总线 (TCP 持久服务)
====================================================
天权(t) · 瑶灵(l) · 瑶光(g) 三域互通中枢。

启动:  python global_bus_main.py
端口:  localhost:9100
协议:  JSON-line (每行一个 JSON, \n 分隔)

架构:
    ┌──────────────────────────────────────────┐
    │           BusTCPServer :9100              │
    │         ┌──────────────────┐              │
    │         │  GlobalEventBus  │              │
    │         │  · 订阅表         │              │
    │         │  · 消息路由        │              │
    │         │  · TTL 防转发      │              │
    │         └──────────────────┘              │
    └────────┬──────────┬──────────┬───────────┘
             │ TCP      │ TCP      │ TCP
        ┌────┴────┐┌────┴────┐┌────┴────┐
        │ 天权 t  ││ 瑶灵 l  ││ 瑶光 g  │
        └─────────┘└─────────┘└─────────┘
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("global_bus")

# ---------------------------------------------------------------------------
# 域身份
# ---------------------------------------------------------------------------


class DomainId(Enum):
    TIANQUAN = "t"
    YAOLING = "l"
    YAOGUANG = "g"


DOMAIN_NAMES: Dict[str, str] = {
    "t": "天权算力工程域",
    "l": "瑶灵仿生认知域",
    "g": "瑶光感知采集域",
}

# ---------------------------------------------------------------------------
# 消息信封
# ---------------------------------------------------------------------------


@dataclass
class BusMessage:
    """全局总线消息信封。"""

    msg_id: str
    source_domain: str
    target_domain: str
    channel: str
    cmd: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    ttl: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "msg_id": self.msg_id,
            "source": self.source_domain,
            "target": self.target_domain,
            "channel": self.channel,
            "cmd": self.cmd,
            "payload": self.payload,
            "ts": self.timestamp,
        }


# ---------------------------------------------------------------------------
# 订阅者 (服务端内部使用)
# ---------------------------------------------------------------------------

SubscriberCallback = Callable[[BusMessage], Any]


@dataclass
class Subscriber:
    domain: str
    channel: str
    callback: SubscriberCallback
    subscriber_id: str


# ---------------------------------------------------------------------------
# 全局事件总线内核 (保留)
# ---------------------------------------------------------------------------


class GlobalEventBus:
    """三域全局事件总线内核 — 订阅表 + 消息路由。"""

    def __init__(self) -> None:
        self._subscriptions: Dict[str, List[Subscriber]] = defaultdict(list)
        self._msg_counter: int = 0

    def subscribe(self, domain: str, channel: str, callback: SubscriberCallback) -> str:
        sub_id = f"{domain}:{channel}:{id(callback)}"
        sub = Subscriber(domain=domain, channel=channel, callback=callback, subscriber_id=sub_id)
        self._subscriptions[channel].append(sub)
        logger.info("[BUS] %s 订阅频道 %s", domain, channel)
        return sub_id

    def unsubscribe(self, subscriber_id: str) -> bool:
        for ch, subs in self._subscriptions.items():
            self._subscriptions[ch] = [s for s in subs if s.subscriber_id != subscriber_id]
        return True

    def unsubscribe_domain(self, domain: str) -> None:
        """断开连接时清理该域所有订阅。"""
        for ch in list(self._subscriptions.keys()):
            self._subscriptions[ch] = [s for s in self._subscriptions[ch] if s.domain != domain]

    async def publish(
        self,
        source_domain: str,
        channel: str,
        cmd: str,
        payload: Dict[str, Any],
        target_domain: str = "",
        ttl: int = 3,
    ) -> Dict[str, Any]:
        self._msg_counter += 1
        msg = BusMessage(
            msg_id=f"bus:{self._msg_counter}:{int(time.time() * 1000)}",
            source_domain=source_domain,
            target_domain=target_domain,
            channel=channel,
            cmd=cmd,
            payload=payload,
            ttl=ttl,
        )

        subs = self._subscriptions.get(channel, [])
        delivered = 0

        for sub in subs:
            if target_domain and sub.domain != target_domain:
                continue
            if sub.domain == source_domain:
                continue
            try:
                if asyncio.iscoroutinefunction(sub.callback):
                    await sub.callback(msg)
                else:
                    sub.callback(msg)
                delivered += 1
            except Exception:
                logger.exception("[BUS] 投递 %s → %s 失败", msg.msg_id, sub.domain)

        logger.info(
            "[BUS] %s → ch=%s cmd=%s → %s  | 投递 %d 域",
            source_domain,
            channel,
            cmd,
            target_domain or "broadcast",
            delivered,
        )

        return {"status": "ok", "msg_id": msg.msg_id, "delivered": delivered, "channel": channel}

    def status(self) -> Dict[str, Any]:
        return {
            "subscriptions": {ch: len(subs) for ch, subs in self._subscriptions.items()},
            "total_subscribers": sum(len(s) for s in self._subscriptions.values()),
            "msg_counter": self._msg_counter,
        }


# ---------------------------------------------------------------------------
# 响应构建工具
# ---------------------------------------------------------------------------


def _rsp(msg_type: str, req_id: str = "", **kwargs: Any) -> Dict[str, Any]:
    """构建带 req_id 的响应，客户端用于匹配请求-响应。"""
    r = {"type": msg_type, **kwargs}
    if req_id:
        r["req_id"] = req_id
    return r


# ---------------------------------------------------------------------------
# TCP 服务器层
# ---------------------------------------------------------------------------

BIND_HOST = "127.0.0.1"
BIND_PORT = 9100


class BusTCPServer:
    """
    全局总线 TCP 服务。

    协议 (JSON-line, 每行一条 JSON, \\n 分隔):

    Client → Server:
      {"type":"auth","domain":"t"}
      {"type":"subscribe","channels":["global_alert","yaoling_state"]}
      {"type":"publish","channel":"...","cmd":"...","payload":{...},"target":""}

    Server → Client:
      {"type":"auth_ok","domain":"t","server":"harris-bus"}
      {"type":"subscribed","channels":["global_alert","yaoling_state"]}
      {"type":"published","msg_id":"...","delivered":2}
      {"type":"message","msg_id":"...","source":"t","channel":"...","cmd":"...","payload":{...}}
      {"type":"error","reason":"..."}
    """

    def __init__(self, host: str = BIND_HOST, port: int = BIND_PORT) -> None:
        self.host = host
        self.port = port
        self.bus = GlobalEventBus()
        # domain_tag → StreamWriter (用于推送消息到客户端)
        self._clients: Dict[str, asyncio.StreamWriter] = {}
        self._server: Optional[asyncio.Server] = None

    # ------------------------------------------------------------------
    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_client, self.host, self.port
        )
        addr = self._server.sockets[0].getsockname() if self._server.sockets else (self.host, self.port)
        logger.info("══════════════════════════════════════════")
        logger.info("  Harris 全局消息总线 已启动")
        logger.info("  地址: tcp://%s:%s", addr[0], addr[1])
        logger.info("  等待三域 MCP 连接...")
        logger.info("══════════════════════════════════════════")

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        logger.info("[BUS] 服务已停止")

    # ------------------------------------------------------------------
    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """处理一个 TCP 客户端连接。"""
        domain_tag: Optional[str] = None
        peer = writer.get_extra_info("peername", "unknown")

        try:
            while True:
                line = await reader.readline()
                if not line:
                    break  # 客户端断开

                try:
                    data = json.loads(line.decode("utf-8").strip())
                except json.JSONDecodeError:
                    await self._send(writer, {"type": "error", "reason": "JSON 解析失败"})
                    continue

                msg_type = data.get("type", "")
                req_id = data.get("req_id", "")  # 客户端请求 ID — 所有响应原样带回

                if msg_type == "auth":
                    domain_tag = data.get("domain", "")
                    if domain_tag not in DOMAIN_NAMES:
                        await self._send(writer, _rsp("error", req_id, reason=f"未知域: {domain_tag}"))
                        domain_tag = None
                        continue
                    # 如果同域重连，先踢掉旧连接
                    if domain_tag in self._clients:
                        old = self._clients[domain_tag]
                        try:
                            old.close()
                        except Exception:
                            pass
                    self._clients[domain_tag] = writer
                    await self._send(writer, _rsp("auth_ok", req_id, domain=domain_tag, server="harris-bus"))
                    logger.info("[BUS] ✓ %s (%s) 已连接", DOMAIN_NAMES[domain_tag], peer)

                elif msg_type == "subscribe":
                    if not domain_tag:
                        await self._send(writer, _rsp("error", req_id, reason="请先 auth"))
                        continue
                    channels = data.get("channels", [])
                    for ch in channels:
                        self.bus.subscribe(
                            domain_tag, ch,
                            lambda msg, d=domain_tag: asyncio.create_task(
                                self._push_to_domain(d, msg)
                            ),
                        )
                    await self._send(writer, _rsp("subscribed", req_id, channels=channels))
                    logger.info("[BUS] %s 订阅 %s", DOMAIN_NAMES.get(domain_tag, domain_tag), channels)

                elif msg_type == "publish":
                    if not domain_tag:
                        await self._send(writer, _rsp("error", req_id, reason="请先 auth"))
                        continue
                    result = await self.bus.publish(
                        source_domain=domain_tag,
                        channel=data.get("channel", ""),
                        cmd=data.get("cmd", ""),
                        payload=data.get("payload", {}),
                        target_domain=data.get("target", ""),
                    )
                    await self._send(writer, _rsp("published", req_id, **result))

                else:
                    await self._send(writer, _rsp("error", req_id, reason=f"未知消息类型: {msg_type}"))

        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("[BUS] 客户端 %s 异常", peer)
        finally:
            # 清理
            if domain_tag:
                self._clients.pop(domain_tag, None)
                self.bus.unsubscribe_domain(domain_tag)
                logger.info("[BUS] ✗ %s 已断开", DOMAIN_NAMES.get(domain_tag, domain_tag))
            try:
                writer.close()
            except Exception:
                pass

    async def _send(self, writer: asyncio.StreamWriter, data: Dict[str, Any]) -> None:
        """向客户端发送 JSON 行。"""
        try:
            payload = json.dumps(data, ensure_ascii=False) + "\n"
            writer.write(payload.encode("utf-8"))
            await writer.drain()
        except Exception:
            logger.exception("[BUS] 发送失败")

    async def _push_to_domain(self, target_domain: str, msg: BusMessage) -> None:
        """将消息推送到目标域的 TCP 连接。"""
        writer = self._clients.get(target_domain)
        if writer is None:
            logger.debug("[BUS] 域 %s 不在线，跳过投递", target_domain)
            return
        await self._send(
            writer,
            {
                "type": "message",
                "msg_id": msg.msg_id,
                "source": msg.source_domain,
                "channel": msg.channel,
                "cmd": msg.cmd,
                "payload": msg.payload,
            },
        )


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------


async def main() -> None:
    server = BusTCPServer()
    try:
        await server.start()
        # 永久运行
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("[BUS] 收到中断信号")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
