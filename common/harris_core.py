"""
Harris 工作流核心引擎 — 天权·瑶灵·瑶光 三域统一编排底座
==========================================================================
RunMode / GuardAction / WorkflowGuard / AgentNode / PhaseUnit /
HarrisWorkflow / GuardController / HarrisOrchestrator / HarrisDslParser
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger("harris.core")

# ---------------------------------------------------------------------------
# 领域异常
# ---------------------------------------------------------------------------


class HarrisError(Exception):
    """Harris 引擎通用异常。"""


class GuardRejectionError(HarrisError):
    """守门逻辑拒绝执行。"""


class DSLParseError(HarrisError):
    """YAML / DSL 解析失败。"""


class AgentNodeTimeoutError(HarrisError):
    """Agent 节点执行超时。"""


# ---------------------------------------------------------------------------
# RunMode  &  GuardAction
# ---------------------------------------------------------------------------


class RunMode(Enum):
    """
    Harris 调度模式。

    - STRICT:    所有 Guard 必须 ALLOW，缺 DSL 则报错。
    - FLEXIBLE:  缺 DSL 时允许动态生成骨架；Guard 首次拦截降级为 WARN。
    - DRY_RUN:   只走校验 + 日志，不执行任何 Agent。
    """

    STRICT = "strict"
    FLEXIBLE = "flexible"
    DRY_RUN = "dry_run"


class GuardAction(Enum):
    """守护节点返回的动作语义。"""

    ALLOW = auto()
    DENY = auto()
    WARN = auto()
    DEFER = auto()  # 交由上层裁决


# ---------------------------------------------------------------------------
# 上下文
# ---------------------------------------------------------------------------


@dataclass
class WorkflowContext:
    """工作流执行过程中的可传递上下文。"""

    task: str
    constraints: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    trace: List[Dict[str, Any]] = field(default_factory=list)
    cancelled: bool = False
    run_id: str = ""

    def log_step(self, node_id: str, status: str, detail: str = "") -> None:
        self.trace.append(
            {
                "ts": time.time(),
                "node": node_id,
                "status": status,
                "detail": detail,
            }
        )


# ---------------------------------------------------------------------------
# WorkflowGuard
# ---------------------------------------------------------------------------


@dataclass
class GuardRule:
    """单条守门规则。"""

    name: str
    description: str = ""
    checker: Optional[Callable[[WorkflowContext], Tuple[GuardAction, str]]] = None
    priority: int = 100  # 越小越先执行

    def evaluate(self, ctx: WorkflowContext) -> Tuple[GuardAction, str]:
        if self.checker is None:
            return GuardAction.ALLOW, f"[{self.name}] 空规则，默认放行"
        return self.checker(ctx)


class WorkflowGuard:
    """
    工作流级守门器 — 管理一组 GuardRule，在 AgentNode 执行前/后触发。
    """

    def __init__(self, guard_name: str = "default") -> None:
        self.guard_name = guard_name
        self._rules: List[GuardRule] = []

    def add_rule(self, rule: GuardRule) -> None:
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority)

    def remove_rule(self, rule_name: str) -> bool:
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.name != rule_name]
        return len(self._rules) < before

    def evaluate_all(self, ctx: WorkflowContext) -> List[Tuple[GuardRule, GuardAction, str]]:
        results: List[Tuple[GuardRule, GuardAction, str]] = []
        for rule in self._rules:
            action, msg = rule.evaluate(ctx)
            results.append((rule, action, msg))
            if action == GuardAction.DENY:
                break  # 硬拒绝不再后判
        return results

    @property
    def rules(self) -> List[GuardRule]:
        return list(self._rules)


# ---------------------------------------------------------------------------
# AgentNode  &  PhaseUnit
# ---------------------------------------------------------------------------


@dataclass
class AgentNode:
    """工作流中最小的可执行单元——一个 Agent 调用。"""

    node_id: str
    agent_type: str  # e.g. "llm", "tool", "human_approval"
    prompt_template: str = ""
    tool_bindings: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    retry_count: int = 0
    pre_guard: Optional[WorkflowGuard] = None
    post_guard: Optional[WorkflowGuard] = None
    depends_on: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    async def execute(
        self,
        ctx: WorkflowContext,
        executor: Optional[Callable[..., Any]] = None,
    ) -> Dict[str, Any]:
        """执行节点。若提供 executor 则委托，否则返回占位结果。"""
        ctx.log_step(self.node_id, "started")

        if executor is not None:
            try:
                if asyncio.iscoroutinefunction(executor):
                    # Python 3.13: asyncio.coroutine() 已移除, 直接调用协程函数即可
                    coro = executor(self, ctx)
                else:
                    coro = asyncio.get_event_loop().run_in_executor(None, executor, self, ctx)
                result = await asyncio.wait_for(coro, timeout=self.timeout_seconds)
            except asyncio.TimeoutError:
                ctx.log_step(self.node_id, "timeout", f"超过 {self.timeout_seconds}s")
                raise AgentNodeTimeoutError(f"AgentNode {self.node_id} 超时")
        else:
            result = {"status": "placeholder", "node_id": self.node_id}

        ctx.log_step(self.node_id, "completed")
        return result


@dataclass
class PhaseUnit:
    """
    阶段 — 包含一组顺序或并行执行的 AgentNode。
    """

    phase_id: str
    nodes: List[AgentNode] = field(default_factory=list)
    parallel: bool = False  # True 表示阶段内节点可并发
    entry_guard: Optional[WorkflowGuard] = None
    exit_guard: Optional[WorkflowGuard] = None
    retry_policy: str = "none"  # none | retry_all | retry_failed
    max_retry: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)  # V2.0: route_stamp 等扩展字段

    def add_node(self, node: AgentNode) -> None:
        self.nodes.append(node)


# ---------------------------------------------------------------------------
# HarrisWorkflow
# ---------------------------------------------------------------------------


@dataclass
class HarrisWorkflow:
    """
    完整的 Harris 工作流定义。

    - phases:     顺序执行的阶段列表（阶段间必然串行）
    - global_guard: 跨阶段全局守门器
    """

    workflow_id: str
    version: str = "1.0"
    description: str = ""
    mode: RunMode = RunMode.STRICT
    phases: List[PhaseUnit] = field(default_factory=list)
    global_guard: Optional[WorkflowGuard] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    constraints_schema: Optional[Dict[str, Any]] = None  # JSON Schema

    def add_phase(self, phase: PhaseUnit) -> None:
        self.phases.append(phase)

    @property
    def all_nodes(self) -> List[AgentNode]:
        nodes: List[AgentNode] = []
        for phase in self.phases:
            nodes.extend(phase.nodes)
        return nodes

    def digest(self) -> str:
        """工作流内容摘要哈希，用于缓存去重。"""
        payload = json.dumps(
            {
                "id": self.workflow_id,
                "v": self.version,
                "phases": [
                    {
                        "pid": p.phase_id,
                        "nids": [n.node_id for n in p.nodes],
                    }
                    for p in self.phases
                ],
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# GuardController — 全局守门调度
# ---------------------------------------------------------------------------


class GuardController:
    """
    全局守门控制器，对 Workflow / Phase / AgentNode 三级守门统一调度。
    """

    def __init__(self, mode: RunMode = RunMode.STRICT) -> None:
        self.mode = mode

    def check(
        self,
        guard: Optional[WorkflowGuard],
        ctx: WorkflowContext,
        label: str = "",
    ) -> Tuple[bool, List[str]]:
        """
        执行守门器，返回 (通过/拦截, 消息列表)。
        STRICT 模式 DENY 直接抛 GuardRejectionError。
        """
        if guard is None:
            return True, []

        verdicts = guard.evaluate_all(ctx)
        messages: List[str] = []
        allowed = True

        for rule, action, msg in verdicts:
            messages.append(f"[{rule.name}] {action.name}: {msg}")
            if action == GuardAction.DENY:
                allowed = False
                if self.mode == RunMode.STRICT:
                    raise GuardRejectionError(
                        f"{label} 守门器 [{guard.guard_name}] 规则 [{rule.name}] 拒绝: {msg}"
                    )
                break
            elif action == GuardAction.WARN:
                logger.warning("Guard WARN [%s] %s: %s", guard.guard_name, rule.name, msg)

        return allowed, messages


# ---------------------------------------------------------------------------
# HarrisOrchestrator
# ---------------------------------------------------------------------------


class HarrisOrchestrator:
    """
    Harris 核心编排器。

    按 phases 顺序推进，阶段间串行；阶段内根据 PhaseUnit.parallel
    决定串行或并发执行 AgentNode。每级执行前后均经过 GuardController。
    """

    def __init__(
        self,
        workflow: Optional[HarrisWorkflow],
        bus: Any = None,
        mode: Optional[RunMode] = None,
    ) -> None:
        self.workflow = workflow
        self.bus = bus
        self.mode = mode or (workflow.mode if workflow else RunMode.FLEXIBLE)
        self.guard_ctrl = GuardController(self.mode)
        self._cancelled = False

    # ---- bus helpers ----

    async def _emit(self, event: str, payload: Dict[str, Any]) -> None:
        if self.bus and hasattr(self.bus, "publish"):
            await self.bus.publish(event, payload)

    # ---- run ----

    async def run(
        self,
        task: str,
        constraints: Optional[Dict[str, Any]] = None,
        node_executor: Optional[Callable[..., Any]] = None,
    ) -> WorkflowContext:
        """
        执行工作流。

        返回 WorkflowContext，内含 trace / artifacts / metrics。
        """
        if self.workflow is None:
            raise HarrisError("HarrisOrchestrator 未绑定工作流")

        ctx = WorkflowContext(
            task=task,
            constraints=constraints or {},
            run_id=self.workflow.digest(),
        )

        logger.info("▶ 启动工作流 %s  [mode=%s]", self.workflow.workflow_id, self.mode.value)
        await self._emit("workflow.started", {"wid": self.workflow.workflow_id, "run_id": ctx.run_id})

        # --- 全局守门 ---
        t0 = time.time()
        ok, msgs = self.guard_ctrl.check(self.workflow.global_guard, ctx, "Global")
        if not ok:
            ctx.metrics["guard_reject"] = 1.0
            ctx.log_step("_global_guard", "rejected", "; ".join(msgs))
            await self._emit("workflow.guard_rejected", {"msgs": msgs})
            return ctx

        # --- 阶段推进 ---
        for phase in self.workflow.phases:
            if self._cancelled or ctx.cancelled:
                ctx.log_step(phase.phase_id, "cancelled")
                break

            # 阶段入口守门
            ok, msgs = self.guard_ctrl.check(phase.entry_guard, ctx, f"Phase({phase.phase_id})")
            if not ok:
                ctx.log_step(phase.phase_id, "guard_blocked", "; ".join(msgs))
                continue

            ctx.log_step(phase.phase_id, "started")

            if phase.parallel and len(phase.nodes) > 1:
                # 并发执行
                tasks = [
                    self._run_node_with_guard(node, ctx, node_executor)
                    for node in phase.nodes
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
            else:
                # 串行执行
                for node in phase.nodes:
                    if ctx.cancelled:
                        break
                    await self._run_node_with_guard(node, ctx, node_executor)

            # 阶段出口守门
            self.guard_ctrl.check(phase.exit_guard, ctx, f"Phase({phase.phase_id})-exit")

            ctx.log_step(phase.phase_id, "completed")

        # --- 收尾 ---
        elapsed = time.time() - t0
        ctx.metrics["elapsed_seconds"] = elapsed
        ctx.log_step("_workflow", "completed", f"{elapsed:.2f}s")

        await self._emit(
            "workflow.completed",
            {"wid": self.workflow.workflow_id, "run_id": ctx.run_id, "elapsed": elapsed},
        )

        logger.info("✓ 工作流 %s 完成  [%.2fs]", self.workflow.workflow_id, elapsed)
        return ctx

    async def _run_node_with_guard(
        self,
        node: AgentNode,
        ctx: WorkflowContext,
        executor: Optional[Callable[..., Any]] = None,
    ) -> None:
        """带守门的单节点执行。"""
        # 前置守门
        ok, msgs = self.guard_ctrl.check(node.pre_guard, ctx, f"Node({node.node_id})-pre")
        if not ok:
            ctx.log_step(node.node_id, "pre_guard_blocked", "; ".join(msgs))
            return

        # 依赖检查
        for dep_id in node.depends_on:
            completed = any(t["node"] == dep_id and t["status"] == "completed" for t in ctx.trace)
            if not completed:
                ctx.log_step(node.node_id, "dependency_missing", f"依赖节点 {dep_id} 未完成")
                if self.mode == RunMode.STRICT:
                    raise HarrisError(f"AgentNode {node.node_id} 依赖 {dep_id} 未满足")
                return

        # 执行
        for attempt in range(node.retry_count + 1):
            try:
                result = await node.execute(ctx, executor)
                ctx.artifacts[f"{node.node_id}_result"] = result
                break
            except AgentNodeTimeoutError:
                if attempt == node.retry_count:
                    raise
                logger.warning("AgentNode %s 超时，重试 %d/%d", node.node_id, attempt + 1, node.retry_count)

        # 后置守门
        self.guard_ctrl.check(node.post_guard, ctx, f"Node({node.node_id})-post")

    def cancel(self) -> None:
        self._cancelled = True


# ---------------------------------------------------------------------------
# HarrisDslParser — YAML → HarrisWorkflow
# ---------------------------------------------------------------------------


class HarrisDslParser:
    """
    将 Harris YAML DSL 文本解析为 HarrisWorkflow 对象。

    YAML 结构示例:
        workflow_id: wf_example
        version: "1.0"
        mode: strict
        phases:
          - phase_id: p1
            parallel: false
            nodes:
              - node_id: n1
                agent_type: llm
                prompt_template: "分析 {{ task }}"
                timeout_seconds: 120
    """

    _MODE_MAP: Dict[str, RunMode] = {
        "strict": RunMode.STRICT,
        "flexible": RunMode.FLEXIBLE,
        "dry_run": RunMode.DRY_RUN,
    }

    # ------------------------------------------------------------------
    @classmethod
    def from_yaml_text(cls, yaml_text: str) -> HarrisWorkflow:
        """从 YAML 文本创建 HarrisWorkflow。"""
        try:
            raw = yaml.safe_load(yaml_text)
        except yaml.YAMLError as exc:
            raise DSLParseError(f"YAML 解析失败: {exc}") from exc

        if not isinstance(raw, dict):
            raise DSLParseError("YAML 顶层必须是映射")

        return cls._build_workflow(raw)

    @classmethod
    def from_yaml_file(cls, filepath: str) -> HarrisWorkflow:
        """从 YAML 文件创建 HarrisWorkflow。"""
        with open(filepath, "r", encoding="utf-8") as fh:
            return cls.from_yaml_text(fh.read())

    # ------------------------------------------------------------------
    # 内部构建方法
    # ------------------------------------------------------------------

    @classmethod
    def _build_workflow(cls, raw: Dict[str, Any]) -> HarrisWorkflow:
        wf_id = raw.get("workflow_id", "unnamed")
        version = str(raw.get("version", "1.0"))
        description = raw.get("description", "")
        mode = cls._MODE_MAP.get(raw.get("mode", "strict"), RunMode.STRICT)

        wf = HarrisWorkflow(
            workflow_id=wf_id,
            version=version,
            description=description,
            mode=mode,
            metadata=raw.get("metadata", {}),
            constraints_schema=raw.get("constraints_schema"),
        )

        # 全局守门器
        if "global_guard" in raw:
            wf.global_guard = cls._build_guard(raw["global_guard"])

        # 阶段
        for phase_raw in raw.get("phases", []):
            wf.add_phase(cls._build_phase(phase_raw))

        return wf

    @classmethod
    def _build_phase(cls, raw: Dict[str, Any]) -> PhaseUnit:
        phase = PhaseUnit(
            phase_id=raw.get("phase_id", "unnamed_phase"),
            parallel=raw.get("parallel", False),
            retry_policy=raw.get("retry_policy", "none"),
            max_retry=raw.get("max_retry", 1),
        )
        if "entry_guard" in raw:
            phase.entry_guard = cls._build_guard(raw["entry_guard"])
        if "exit_guard" in raw:
            phase.exit_guard = cls._build_guard(raw["exit_guard"])
        for node_raw in raw.get("nodes", []):
            phase.add_node(cls._build_node(node_raw))
        return phase

    @classmethod
    def _build_node(cls, raw: Dict[str, Any]) -> AgentNode:
        node = AgentNode(
            node_id=raw.get("node_id", "unnamed_node"),
            agent_type=raw.get("agent_type", "llm"),
            prompt_template=raw.get("prompt_template", ""),
            tool_bindings=raw.get("tool_bindings", []),
            timeout_seconds=raw.get("timeout_seconds", 300),
            retry_count=raw.get("retry_count", 0),
            depends_on=raw.get("depends_on", []),
            metadata=raw.get("metadata", {}),
        )
        if "pre_guard" in raw:
            node.pre_guard = cls._build_guard(raw["pre_guard"])
        if "post_guard" in raw:
            node.post_guard = cls._build_guard(raw["post_guard"])
        return node

    @classmethod
    def _build_guard(cls, raw: Dict[str, Any]) -> WorkflowGuard:
        guard = WorkflowGuard(guard_name=raw.get("guard_name", "unnamed_guard"))
        for rule_raw in raw.get("rules", []):
            guard.add_rule(
                GuardRule(
                    name=rule_raw.get("name", "unnamed_rule"),
                    description=rule_raw.get("description", ""),
                    priority=rule_raw.get("priority", 100),
                )
            )
        return guard


# ---------------------------------------------------------------------------
# 便捷工厂
# ---------------------------------------------------------------------------


def make_quick_workflow(
    wf_id: str,
    agent_type: str = "llm",
    prompt: str = "",
    mode: RunMode = RunMode.FLEXIBLE,
) -> HarrisWorkflow:
    """快速构建单节点单阶段工作流（Demo / 测试用）。"""
    node = AgentNode(node_id="main", agent_type=agent_type, prompt_template=prompt)
    phase = PhaseUnit(phase_id="main_phase", nodes=[node])
    return HarrisWorkflow(workflow_id=wf_id, mode=mode, phases=[phase])
