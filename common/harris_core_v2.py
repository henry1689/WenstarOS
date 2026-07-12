"""
harris_core_v2.py — Harris 工作流引擎 V2.0
============================================
新增能力 (vs V1.0):
  - RouteStamp: 快递式逐站盖章, 写入海胆寻址链
  - AgentType 枚举: tool / rpc_call / bus_command / llm / guard_only
  - RemoteExecutor: 跨域 TCP 指令下发 (瑶灵/瑶光)
  - 生命周期钩子: 7 个事件, Master-Harris 五层各自注册
  - 约束自动注入: Master-Harris 从 SPEC 加载 → constraints
  - 增强 WorkflowContext: DNA 绑定 + 约束校验 + route_stamps
  - 增强 HarrisOrchestrator: 钩子系统 + 路由戳 + 约束校验
  - 增强 HarrisDslParser: 支持 V2.0 YAML 字段 + 向后兼容 V1.0

适配: Master-Harris V1.0 / DNA V2.0 / 天权底座 V1.0 / Harris-YAML V2.0
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import yaml

# ── 从 V1.0 导入基础类 (保持兼容) ──────────────────────────
from .harris_core import (
    HarrisError,
    GuardRejectionError,
    DSLParseError,
    AgentNodeTimeoutError,
    RunMode,
    GuardAction,
    GuardRule,
    WorkflowGuard,
    AgentNode,
    PhaseUnit,
    HarrisWorkflow,
    GuardController,
    HarrisOrchestrator as HarrisOrchestratorV1,
    HarrisDslParser as HarrisDslParserV1,
    WorkflowContext as WorkflowContextV1,
    make_quick_workflow as make_quick_workflow_v1,
)

logger = logging.getLogger("harris.core.v2")

# ═══════════════════════════════════════════════════════════════
# 第一章 · V2.0 新增数据结构
# ═══════════════════════════════════════════════════════════════


class AgentType(str, Enum):
    """V2.0 Agent 节点类型——精确控制执行方式。"""
    TOOL        = "tool"          # 本地 Python 函数调用 (同步, 毫秒级)
    RPC_CALL    = "rpc_call"      # 内置天权 RPC 调用 (stdin/stdout, 毫秒级)
    BUS_COMMAND = "bus_command"   # 远程瑶灵/瑶光 TCP 指令 (5s 超时, 2 次重试)
    LLM         = "llm"           # Mind 核 LLM 生成 (BIOS 核拒绝执行此类型)
    GUARD_ONLY  = "guard_only"    # 仅执行守门校验, 无实际操作


@dataclass
class RouteStamp:
    """快递式逐站盖章——每经过一个车间即追加一条戳记。

    工作流执行完毕后, 全量 route_stamps[] 序列化为 Protobuf BLOB,
    写入海胆寻址链 atom_address_timeline.route_stamp_list。
    """
    workshop:   str      # 车间标识: "M1"/"M2"/"Master-Harris"/"TianquanRPC"/"YaolingBus"/"YaoguangBus"
    operation:  str      # 操作类型: "ENCODE"/"WRITE"/"GUARD_CHECK"/"PHASE_ENTRY"/"PHASE_COMPLETE"/"NODE_EXECUTED"
    phase_id:   str      # 当前阶段 ID
    node_id:    str      # 当前节点 ID (phase 级操作时为 "_phase_")
    timestamp:  float    # Unix 秒
    detail:     str      # 操作详情
    crc_snap:   str      # 本条戳记前 WorkflowContext 的校验快照 (SHA256 前 8 位)


@dataclass
class WorkflowContextV2(WorkflowContextV1):
    """V2.0 增强上下文——DNA 绑定 + 路由戳 + 约束校验 + 降级标记。

    向后兼容 V1.0: 所有 V1.0 字段 (task/constraints/artifacts/metrics/trace) 全部保留。
    """

    # ── DNA 绑定 (Master-Harris 注入) ──
    global_uid: str = ""
    location_fingerprint: str = ""

    # ── 执行身份 ──
    domain: str = ""             # "tianquan" | "yaoling" | "yaoguang"
    executor_type: str = ""      # "local_rpc" | "remote_tcp" | "stdio_mcp"

    # ── 路由戳 (V2.0 新增) ──
    route_stamps: List[RouteStamp] = field(default_factory=list)

    # ── 时间 ──
    started_at: float = 0.0
    completed_at: float = 0.0

    # ── 降级标记 ──
    degraded: bool = False
    degradation_reason: str = ""

    # ── 钩子数据 (各层钩子可读写) ──
    hook_data: Dict[str, Any] = field(default_factory=dict)

    # ── 内部 ──
    _crc_counter: int = 0

    # ------------------------------------------------------------------
    def stamp(self, workshop: str, operation: str, phase_id: str,
              node_id: str = "_phase_", detail: str = "") -> "WorkflowContextV2":
        """追加工厂车间路由戳。

        自动计算当前 artifacts 的 CRC 快照作为戳记防篡改校验。
        """
        snap_raw = json.dumps(
            {"artifacts_keys": sorted(self.artifacts.keys()),
             "metrics": self.metrics},
            sort_keys=True, default=str,
        )
        crc_snap = hashlib.sha256(snap_raw.encode()).hexdigest()[:8]

        stamp = RouteStamp(
            workshop=workshop,
            operation=operation,
            phase_id=phase_id,
            node_id=node_id,
            timestamp=time.time(),
            detail=detail,
            crc_snap=crc_snap,
        )
        self.route_stamps.append(stamp)
        self._crc_counter += 1
        return self

    # ------------------------------------------------------------------
    def validate_constraints(self, schema: Optional[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """对照 constraints_schema 校验 constraints 的 required 字段。"""
        if schema is None:
            return True, []
        required = schema.get("required", [])
        missing = [f for f in required if f not in self.constraints or self.constraints[f] is None]
        return len(missing) == 0, missing

    # ------------------------------------------------------------------
    def to_summary(self) -> Dict[str, Any]:
        """输出执行摘要——供 Master-Harris SnapshotAggregator 使用。"""
        return {
            "global_uid": self.global_uid,
            "domain": self.domain,
            "task": self.task[:200],
            "degraded": self.degraded,
            "degradation_reason": self.degradation_reason,
            "elapsed_seconds": self.metrics.get("elapsed_seconds", 0),
            "phase_count": len([s for s in self.route_stamps if s.operation == "PHASE_ENTRY"]),
            "node_count": len([s for s in self.route_stamps if s.operation == "NODE_EXECUTED"]),
            "guard_reject": self.metrics.get("guard_reject", 0),
            "stamp_count": len(self.route_stamps),
        }


# ═══════════════════════════════════════════════════════════════
# 第二章 · 远程执行器
# ═══════════════════════════════════════════════════════════════


class RemoteExecutor:
    """向远程域 (瑶灵/瑶光) 下发工作流执行指令。

    协议: 通过 GlobalBusTCPClient 发布 bus_command 类型的指令,
         目标域 MCP 进程接收后执行本地工作流, 结果通过总线回传。

    约束:
      - 仅 Master-Harris 可调用 (MH-1)
      - 5s 超时 + 最多 2 次重发
      - 失败不抛异常, 返回 error dict 供 FaultMemoryArchiver 处理
    """

    def __init__(self, bus_client: Any, target_domain: str) -> None:
        if bus_client is None:
            raise HarrisError("RemoteExecutor 需要有效的总线客户端")
        if target_domain not in ("l", "g"):
            raise HarrisError(f"未知的远程域: {target_domain} (仅支持 'l' 或 'g')")

        self.bus = bus_client
        self.target = target_domain
        self._timeout = 5.0
        self._max_retries = 2
        self._stats = {"dispatched": 0, "succeeded": 0, "failed": 0, "timeouts": 0}

    # ------------------------------------------------------------------
    async def dispatch(
        self,
        workflow_id: str,
        task: str,
        constraints: Dict[str, Any],
    ) -> Dict[str, Any]:
        """下发 run_static_workflow 指令到远程域, 等待执行结果。

        Returns:
            {"status": "ok", "msg_id": "...", "delivered": 1, "result": {...}}
            {"status": "error", "reason": "..."}
            {"status": "timeout", "reason": "..."}
        """
        self._stats["dispatched"] += 1
        last_error = ""

        for attempt in range(self._max_retries + 1):
            try:
                ack = await asyncio.wait_for(
                    self.bus.publish(
                        target_domain=self.target,
                        cmd="run_static_workflow",
                        payload={
                            "workflow_id": workflow_id,
                            "task": task,
                            "constraints": constraints,
                        },
                    ),
                    timeout=self._timeout,
                )

                if ack.get("status") == "ok":
                    self._stats["succeeded"] += 1
                    return ack

                last_error = json.dumps(ack, ensure_ascii=False)
                logger.warning(
                    "[RemoteExecutor] %s → %s 执行失败 (attempt %d/%d): %s",
                    workflow_id, self.target, attempt + 1, self._max_retries + 1, last_error[:200],
                )

            except asyncio.TimeoutError:
                self._stats["timeouts"] += 1
                last_error = f"超时 ({self._timeout}s)"
                logger.warning(
                    "[RemoteExecutor] %s → %s 超时 (attempt %d/%d)",
                    workflow_id, self.target, attempt + 1, self._max_retries + 1,
                )

            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                logger.exception("[RemoteExecutor] %s → %s 异常", workflow_id, self.target)

        self._stats["failed"] += 1
        return {
            "status": "error",
            "reason": f"远程域 {self.target} 无响应: {last_error[:300]}",
        }

    # ------------------------------------------------------------------
    @property
    def stats(self) -> Dict[str, int]:
        return dict(self._stats)


# ═══════════════════════════════════════════════════════════════
# 第三章 · V2.0 增强 HarrisOrchestrator
# ═══════════════════════════════════════════════════════════════


class HarrisOrchestratorV2(HarrisOrchestratorV1):
    """V2.0 增强编排器——继承 V1.0 全部能力, 新增钩子+路由戳+约束校验。

    向后兼容: V1.0 的 run() 方法语义完全保留, 外部调用者无需修改。
    V2.0 独有能力通过 on()/off() 钩子、ctx.stamp()、ctx.validate_constraints() 暴露。
    """

    def __init__(
        self,
        workflow: Optional[HarrisWorkflow],
        bus: Any = None,
        mode: Optional[RunMode] = None,
        domain: str = "",
    ) -> None:
        super().__init__(workflow, bus, mode)

        # ── V2.0 新增 ──
        self.domain = domain or (workflow.metadata.get("domain", "") if workflow else "")
        self.remote_executor: Optional[RemoteExecutor] = None

        # 钩子系统
        self._hooks: Dict[str, List[Callable]] = defaultdict(list)

        # 路由戳配置
        self._stamp_enabled: bool = True  # 开发模式可关闭

    # ------------------------------------------------------------------
    # 钩子系统 (V2.0 新增)
    # ------------------------------------------------------------------

    def on(self, event: str, callback: Callable) -> "HarrisOrchestratorV2":
        """注册生命周期钩子。

        Args:
            event: 钩子事件名:
                workflow:pre_flight     — 全局守门前
                workflow:guard_failed   — 守门拒绝后
                workflow:complete       — 工作流完成后
                workflow:fault          — 任何异常时
                phase:entry             — 每阶段入口守门前
                phase:exit              — 每阶段出口守门后
                node:pre_execute        — 每节点执行前
                node:post_execute       — 每节点执行后
            callback: async fn(ctx, **kwargs) → None
        """
        self._hooks[event].append(callback)
        return self

    def off(self, event: str, callback: Callable) -> "HarrisOrchestratorV2":
        """移除钩子。"""
        if event in self._hooks:
            self._hooks[event] = [h for h in self._hooks[event] if h != callback]
        return self

    async def _fire(self, event: str, **kwargs: Any) -> None:
        """触发所有已注册钩子。每个钩子独立异常隔离——一个失败不影响其他。"""
        for hook in self._hooks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(**kwargs)
                else:
                    hook(**kwargs)
            except Exception:
                logger.exception("[HarrisV2] 钩子 [%s] %s 异常", event,
                                 getattr(hook, "__name__", str(hook)))

    # ------------------------------------------------------------------
    # 约束注入 (V2.0 新增)
    # ------------------------------------------------------------------

    @staticmethod
    def inject_master_constraints(
        task: str,
        global_uid: str,
        location_fingerprint: str,
        spec_version: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Master-Harris 统一约束注入——所有工作流调用的前置步骤。

        Args:
            task: 任务描述
            global_uid: 本次交互的海胆 GlobalUID
            location_fingerprint: 128-bit 区位指纹 (hex)
            spec_version: 域规范版本号
            extra: 额外业务参数 (project_root, change_files 等)

        Returns:
            完整的 constraints dict

        注入优先级 (高→低):
          1. Master-Harris 注入 (最高, 不可覆盖): global_uid/location_fingerprint/spec_version
          2. 域 SPEC 自动加载 (从 DNA 向量库读取, 不可覆盖)
          3. 用户提供 (最低, 仅在不冲突时保留)
        """
        constraints: Dict[str, Any] = {
            "dna_root_id": global_uid,             # 兼容旧字段名
            "global_uid": global_uid,
            "location_fingerprint": location_fingerprint,
            "spec_version": spec_version,
            "task": task,
        }
        # 合并用户提供的额外参数 (不可覆盖 Master 注入字段)
        if extra:
            protected = {"dna_root_id", "global_uid", "location_fingerprint", "spec_version", "task"}
            for k, v in extra.items():
                if k not in protected:
                    constraints[k] = v
        return constraints

    # ------------------------------------------------------------------
    # V2.0 增强 run() (V1.0 语义完全保留, 新增钩子+路由戳+约束校验)
    # ------------------------------------------------------------------

    async def run(
        self,
        task: str,
        constraints: Optional[Dict[str, Any]] = None,
        node_executor: Optional[Callable[..., Any]] = None,
    ) -> WorkflowContextV2:
        """V2.0 增强执行——带钩子 + 路由戳 + 约束校验。"""
        if self.workflow is None:
            raise HarrisError("HarrisOrchestrator 未绑定工作流")

        constraints = constraints or {}

        # ── 构建 V2.0 上下文 ──
        ctx = WorkflowContextV2(
            task=task,
            constraints=constraints,
            run_id=self.workflow.digest(),
            domain=self.domain,
            executor_type=self.workflow.metadata.get("communication", ""),
            global_uid=constraints.get("global_uid", constraints.get("dna_root_id", "")),
            location_fingerprint=constraints.get("location_fingerprint", ""),
            started_at=time.time(),
        )

        # ── Hook: pre_flight ──
        await self._fire("workflow:pre_flight", ctx=ctx)

        # ── 约束校验 ──
        if self.workflow.constraints_schema:
            ok, missing = ctx.validate_constraints(self.workflow.constraints_schema)
            if not ok:
                ctx.degraded = True
                ctx.degradation_reason = f"缺少约束: {missing}"
                ctx.log_step("_constraints", "missing", "; ".join(missing))
                await self._fire("workflow:fault", ctx=ctx, reason="constraints_missing")
                if self.mode == RunMode.STRICT:
                    raise HarrisError(f"约束缺失: {missing}")
                logger.warning("[HarrisV2] 约束缺失 (非 STRICT 模式, 降级继续): %s", missing)

        # ── 全局守门 ──
        t0 = time.time()
        ok, msgs = self.guard_ctrl.check(self.workflow.global_guard, ctx, "Global")
        if not ok:
            ctx.metrics["guard_reject"] = 1.0
            ctx.log_step("_global_guard", "rejected", "; ".join(msgs))
            await self._fire("workflow:guard_failed", ctx=ctx, messages=msgs)
            if self._stamp_enabled:
                ctx.stamp(self.domain, "GUARD_REJECTED", "_global_", detail="; ".join(msgs[:3]))
            return ctx

        # ── 阶段推进 (增强: 钩子 + 路由戳) ──
        for phase in self.workflow.phases:
            if self._cancelled or ctx.cancelled:
                ctx.log_step(phase.phase_id, "cancelled")
                break

            # Hook: phase:entry
            await self._fire("phase:entry", ctx=ctx, phase=phase)

            # 阶段入口守门
            ok, msgs = self.guard_ctrl.check(phase.entry_guard, ctx, f"Phase({phase.phase_id})")
            if not ok:
                ctx.log_step(phase.phase_id, "guard_blocked", "; ".join(msgs))
                if self._stamp_enabled:
                    ctx.stamp(self.domain, "GUARD_BLOCKED", phase.phase_id, detail="; ".join(msgs[:3]))
                continue

            # 阶段入口戳
            if self._stamp_enabled:
                ctx.stamp(self.domain, "PHASE_ENTRY", phase.phase_id)

            ctx.log_step(phase.phase_id, "started")

            # 执行节点
            if phase.parallel and len(phase.nodes) > 1:
                tasks = [self._run_node_with_guard_v2(node, ctx, node_executor) for node in phase.nodes]
                await asyncio.gather(*tasks, return_exceptions=True)
            else:
                for node in phase.nodes:
                    if ctx.cancelled:
                        break
                    await self._run_node_with_guard_v2(node, ctx, node_executor)

            # 阶段出口守门 + 路由戳
            self.guard_ctrl.check(phase.exit_guard, ctx, f"Phase({phase.phase_id})-exit")
            if self._stamp_enabled:
                ctx.stamp(self.domain, "PHASE_COMPLETE", phase.phase_id)
            ctx.log_step(phase.phase_id, "completed")

            # Hook: phase:exit
            await self._fire("phase:exit", ctx=ctx, phase=phase)

        # ── 收尾 ──
        elapsed = time.time() - t0
        ctx.completed_at = time.time()
        ctx.metrics["elapsed_seconds"] = round(elapsed, 3)
        ctx.log_step("_workflow", "completed", f"{elapsed:.2f}s")

        if self._stamp_enabled:
            ctx.stamp(self.domain, "WORKFLOW_COMPLETE", "_workflow_",
                       detail=f"elapsed={elapsed:.2f}s")

        await self._fire("workflow:complete", ctx=ctx)

        logger.info("[HarrisV2] ✓ %s 完成 [%.2fs, %d stamps]",
                     self.workflow.workflow_id, elapsed, len(ctx.route_stamps))

        return ctx

    # ------------------------------------------------------------------
    async def _run_node_with_guard_v2(
        self,
        node: AgentNode,
        ctx: WorkflowContextV2,
        executor: Optional[Callable[..., Any]] = None,
    ) -> None:
        """V2.0 增强节点执行——AgentType 感知 + 钩子 + 路由戳。"""
        # ── 前置守门 ──
        ok, msgs = self.guard_ctrl.check(node.pre_guard, ctx, f"Node({node.node_id})-pre")
        if not ok:
            ctx.log_step(node.node_id, "pre_guard_blocked", "; ".join(msgs))
            return

        # ── 依赖检查 ──
        for dep_id in node.depends_on:
            completed = any(t["node"] == dep_id and t["status"] == "completed" for t in ctx.trace)
            if not completed:
                ctx.log_step(node.node_id, "dependency_missing", f"依赖 {dep_id} 未完成")
                if self.mode == RunMode.STRICT:
                    raise HarrisError(f"AgentNode {node.node_id} 依赖 {dep_id} 未满足")
                return

        # ── AgentType 感知 ──
        agent_type = node.metadata.get("agent_type_v2", node.agent_type)

        # GUARD_ONLY: 仅守门, 不执行
        if agent_type == AgentType.GUARD_ONLY.value:
            ctx.log_step(node.node_id, "guard_only", "跳过执行 (GUARD_ONLY)")
            self.guard_ctrl.check(node.post_guard, ctx, f"Node({node.node_id})-post")
            return

        # LLM: BIOS 核拒绝 (MH-4 + 底座第四层)
        if agent_type == AgentType.LLM.value:
            ctx.log_step(node.node_id, "llm_rejected",
                          "BIOS 核禁止 LLM 调用——仅 Mind 核的 M5 生成环节可调 LLM")
            return

        # BUS_COMMAND: 远程域执行
        if agent_type == AgentType.BUS_COMMAND.value:
            if self.remote_executor is None:
                raise HarrisError(
                    f"AgentNode {node.node_id} 需要 BUS_COMMAND, 但 HarrisOrchestrator 未绑定 RemoteExecutor"
                )
            bus_target = node.metadata.get("bus_target_domain", "")
            bus_cmd = node.metadata.get("bus_command", "")
            if not bus_target or not bus_cmd:
                raise HarrisError(f"AgentNode {node.node_id}: BUS_COMMAND 缺少 bus_target_domain 或 bus_command")

            ctx.log_step(node.node_id, "bus_dispatch",
                          f"→ {bus_target}:{bus_cmd}")
            result = await self.remote_executor.dispatch(
                workflow_id=bus_cmd,
                task=ctx.task,
                constraints=ctx.constraints,
            )
            ctx.artifacts[f"{node.node_id}_result"] = result
            if result.get("status") != "ok":
                ctx.degraded = True
                ctx.degradation_reason = f"远程执行失败: {result.get('reason', '')[:200]}"
        else:
            # ── 本地执行 (TOOL / RPC_CALL) ──
            # Hook: node:pre_execute
            await self._fire("node:pre_execute", ctx=ctx, node=node)

            for attempt in range(node.retry_count + 1):
                try:
                    result = await node.execute(ctx, executor)
                    ctx.artifacts[f"{node.node_id}_result"] = result
                    break
                except AgentNodeTimeoutError:
                    if attempt == node.retry_count:
                        raise
                    logger.warning("[HarrisV2] AgentNode %s 超时, 重试 %d/%d",
                                    node.node_id, attempt + 1, node.retry_count)

            # 路由戳
            if self._stamp_enabled:
                ctx.stamp(self.domain, "NODE_EXECUTED",
                           ctx.route_stamps[-1].phase_id if ctx.route_stamps else "_unknown_",
                           node.node_id)

            # Hook: node:post_execute
            await self._fire("node:post_execute", ctx=ctx, node=node)

        # ── 后置守门 ──
        self.guard_ctrl.check(node.post_guard, ctx, f"Node({node.node_id})-post")

    # ------------------------------------------------------------------
    # RPC 调用工厂 (V2.0 新增)
    # ------------------------------------------------------------------

    def bind_remote_executor(self, bus_client: Any, target_domain: str) -> "HarrisOrchestratorV2":
        """绑定远程执行器——用于 BUS_COMMAND 类型的 AgentNode。"""
        self.remote_executor = RemoteExecutor(bus_client, target_domain)
        return self

    def set_stamp_enabled(self, enabled: bool) -> "HarrisOrchestratorV2":
        """开关路由戳 (开发模式调试时可关闭)。"""
        self._stamp_enabled = enabled
        return self


# ═══════════════════════════════════════════════════════════════
# 第四章 · V2.0 增强 HarrisDslParser
# ═══════════════════════════════════════════════════════════════


class HarrisDslParserV2(HarrisDslParserV1):
    """V2.0 YAML DSL 解析器——继承 V1.0 全部, 新增 V2.0 字段解析。

    向后兼容:
      V1.0 YAML → V2.0 解析器:
        缺失 domain → 默认 "tianquan"
        缺失 route_tag → 默认 workflow_id
        缺失 executor_type → 默认 "local_rpc"
        缺失 route_stamp_* → 不加戳, 不报错
        缺失 mh_* 守门规则 → 打印 WARN, 不阻断 (过渡期)
    """

    # ------------------------------------------------------------------
    @classmethod
    def _build_workflow(cls, raw: Dict[str, Any]) -> HarrisWorkflow:
        """V2.0 增强构建——解析 V2.0 新增顶层字段。"""
        wf = super()._build_workflow(raw)

        # ── V2.0 新增顶层字段 (全部可选, 缺失时使用默认值) ──
        domain = raw.get("domain", "tianquan")
        route_tag = raw.get("route_tag", wf.workflow_id)
        executor_type = raw.get("executor_type", "local_rpc")

        # 合并到 metadata
        wf.metadata.setdefault("domain", domain)
        wf.metadata.setdefault("route_tag", route_tag)
        wf.metadata.setdefault("communication", executor_type)
        wf.metadata.setdefault("spec_version", raw.get("metadata", {}).get("spec_version", ""))
        wf.metadata.setdefault("allow_dynamic", raw.get("metadata", {}).get("allow_dynamic", False))
        wf.metadata.setdefault("harris_version", "2.0")

        # ── V2.0 强制 mh_* 守门规则检查 ──
        required_mh_rules = {
            "mh_no_cross_domain_issue",
            "mh_spec_constraints_required",
            "mh_no_llm_float_output",
            "mh_single_globaluid",
            "mh_no_local_persistence",
        }
        if wf.global_guard is not None:
            existing = {r.name for r in wf.global_guard.rules}
            missing_mh = required_mh_rules - existing
            if missing_mh:
                logger.warning(
                    "[HarrisV2] YAML %s 缺少 Master-Harris 铁律守门规则: %s",
                    wf.workflow_id, missing_mh,
                )
        else:
            logger.warning(
                "[HarrisV2] YAML %s 缺少 global_guard——跳过 mh_* 规则校验", wf.workflow_id
            )

        return wf

    # ------------------------------------------------------------------
    @classmethod
    def _build_phase(cls, raw: Dict[str, Any]) -> PhaseUnit:
        """V2.0 增强构建——解析 phase 级 route_stamp 字段。"""
        phase = super()._build_phase(raw)

        # ── V2.0 新增 route_stamp 元数据 ──
        phase.metadata.setdefault("route_stamp_workshop",
                                   raw.get("route_stamp_workshop", ""))
        phase.metadata.setdefault("route_stamp_operation",
                                   raw.get("route_stamp_operation", ""))

        return phase

    # ------------------------------------------------------------------
    @classmethod
    def _build_node(cls, raw: Dict[str, Any]) -> AgentNode:
        """V2.0 增强构建——解析 node 级 V2.0 扩展字段。"""
        node = super()._build_node(raw)

        # ── V2.0 route_stamp ──
        node.metadata.setdefault("route_stamp_workshop",
                                  raw.get("route_stamp_workshop", ""))
        node.metadata.setdefault("route_stamp_operation",
                                  raw.get("route_stamp_operation", ""))

        # ── V2.0 AgentType ──
        agent_type_v2 = raw.get("agent_type", raw.get("agent_type_v2", "tool"))
        node.metadata.setdefault("agent_type_v2", agent_type_v2)

        # ── BUS_COMMAND 专用字段 ──
        if agent_type_v2 == AgentType.BUS_COMMAND.value:
            node.metadata.setdefault("bus_target_domain", raw.get("bus_target_domain", ""))
            node.metadata.setdefault("bus_command", raw.get("bus_command", ""))
            node.metadata.setdefault("bus_timeout_seconds", raw.get("bus_timeout_seconds", 5))
            node.metadata.setdefault("bus_max_retries", raw.get("bus_max_retries", 2))

        # ── RPC_CALL 专用字段 ──
        if agent_type_v2 == AgentType.RPC_CALL.value:
            node.metadata.setdefault("rpc_method", raw.get("rpc_method", ""))
            node.metadata.setdefault("rpc_params", raw.get("rpc_params", {}))

        return node


# ═══════════════════════════════════════════════════════════════
# 第五章 · V2.0 便捷工厂
# ═══════════════════════════════════════════════════════════════


def make_workflow_v2(
    wf_id: str,
    domain: str = "tianquan",
    route_tag: str = "",
    executor_type: str = "local_rpc",
    agent_type: str = "tool",
    prompt: str = "",
    mode: RunMode = RunMode.STRICT,
) -> HarrisWorkflow:
    """快速构建 V2.0 单节点单阶段工作流 (Demo / 测试用)。"""
    node = AgentNode(
        node_id="main",
        agent_type=agent_type,
        prompt_template=prompt,
        metadata={"agent_type_v2": agent_type},
    )
    phase = PhaseUnit(phase_id="main_phase", nodes=[node])
    return HarrisWorkflow(
        workflow_id=wf_id,
        mode=mode,
        phases=[phase],
        metadata={
            "domain": domain,
            "route_tag": route_tag or wf_id,
            "communication": executor_type,
            "harris_version": "2.0",
        },
    )
