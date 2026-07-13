# Harris-YAML 工作流引擎 V2.0 设计规范

> **状态**: 最终定稿 · 全系统唯一工作流编排标准
> **日期**: 2026-07-12
> **适配**: 大一统架构 V1.0 / DNA V2.0 / Master-Harris V1.0 / 天权底座 V1.0
> **定位**: 三域统一工作流引擎——Master-Harris 调度、执行、聚合、降级的唯一载体
> **取代**: 旧版 `common/harris_core.py` V1.0（保留兼容，新增 `harris_core_v2.py`）

---

## 序言 · 为什么需要 V2.0

旧版 Harris 引擎（V1.0）是一个**独立域内的工作流执行器**——它假设工作流在同一个进程内运行，由同一个域自行调度。它不认识 DNA、不认识 Master-Harris、不认识跨域调度。

新架构下，Harris 引擎必须承载 Master-Harris 五层架构的全部能力：

```
Master-Harris 五层:
  IntentRouter → TaskOrchestrator → DomainExecutorPool → SnapshotAggregator → FaultMemoryArchiver
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    ▼                        ▼                        ▼
            LocalTianquanRPC         RemoteYaolingBus          RemoteYaoguangBus
           (stdin/stdout RPC)        (TCP :9100)              (TCP :9100)
                    │                        │                        │
                    └────────────────────────┼────────────────────────┘
                                             │
                                    所有执行载体 = Harris 工作流引擎
```

V2.0 引擎需要新增六项能力：DNA 绑定、路由戳、生命周期钩子、跨域远程执行、约束自动注入、Master 铁律嵌入。

---

## 第一章 · V2.0 新增核心能力

### 1.1 DNA 绑定——工作流执行的全链路基因追溯

V1.0 的 `WorkflowContext` 不知道 DNA 的存在。V2.0 中，每次工作流执行都由 Master-Harris 注入三件 DNA 凭证：

```
执行前注入 (Master-Harris → WorkflowContext):
  global_uid:            string   // 本次交互的海胆 GlobalUID
  dna_root_id:           string   // 向后兼容
  location_fingerprint:  string   // 128-bit 区位指纹 (hex)
  spec_version:          string   // 域规范版本号

注入时机: Master-Harris TaskOrchestrator 确定路由后、DomainExecutorPool 执行前
注入方式: constraints 参数 — 所有工作流的 constraints_schema.required 前三项统一为
         dna_root_id + location_fingerprint + spec_version
```

### 1.2 路由戳——快递式逐站盖章的实现载体

V1.0 的 `WorkflowContext.trace` 只是一个自由格式的日志列表。V2.0 新增结构化的 `RouteStamp`，每经过一个执行站点（phase 完成 / node 完成）自动追加：

```python
@dataclass
class RouteStamp:
    workshop:   str     # 车间标识: "M1" | "M2" | "Master-Harris" | "TianquanRPC" | "YaolingBus"
    operation:  str     # 操作类型: "ENCODE" | "WRITE" | "GUARD_CHECK" | "PHASE_COMPLETE" | "NODE_EXECUTED"
    phase_id:   str     # 当前阶段 ID
    node_id:    str     # 当前节点 ID (如为 phase 级则为 "_phase_")
    timestamp:  float   # Unix 秒
    detail:     str     # 操作详情
    crc_snap:   str     # 本条戳记之前 WorkflowContext 的 CRC 快照

路由戳生命周期:
  Phase 入口 → 追加 RouteStamp(workshop, "PHASE_ENTRY", phase_id, "_phase_", ...)
  Node 完成   → 追加 RouteStamp(workshop, "NODE_EXECUTED", phase_id, node_id, ...)
  Phase 出口 → 追加 RouteStamp(workshop, "PHASE_COMPLETE", phase_id, "_phase_", ...)
  工作流完成  → 全量 route_stamps[] 写入海胆寻址链 atom_address_timeline.route_stamp_list
```

### 1.3 生命周期钩子——Master-Harris 五层插入点

V1.0 的引擎是封闭的——外部无法在关键节点插入逻辑。V2.0 开放 7 个钩子事件：

```python
# 钩子签名: async def hook(ctx: WorkflowContext, **kwargs) -> None

事件列表:
  workflow:pre_flight    → 全局守门前触发 (FaultMemoryArchiver 注册健康检查)
  workflow:guard_failed  → 守门拒绝后触发 (FaultMemoryArchiver 注册 global_alert 发射)
  phase:entry            → 每阶段入口守门前触发 (DomainExecutorPool 记录执行日志)
  phase:exit             → 每阶段出口守门后触发 (SnapshotAggregator 收集阶段产物)
  node:pre_execute       → 每节点执行前触发 (可用于注入动态上下文)
  node:post_execute      → 每节点执行后触发
  workflow:complete      → 工作流完成后触发 (SnapshotAggregator 聚合 + 写入海胆)
  workflow:fault         → 任何异常时触发 (FaultMemoryArchiver 降级处理)
```

### 1.4 Agent 类型扩展

V1.0 的 `agent_type` 是自由格式字符串。V2.0 定义五种标准类型：

```python
class AgentType(str, Enum):
    TOOL = "tool"              # 本地 Python 函数调用 (同步, 毫秒级)
    RPC_CALL = "rpc_call"      # 内置天权 RPC 调用 (stdin/stdout, 毫秒级)
    BUS_COMMAND = "bus_command" # 远程瑶灵/瑶光 TCP 指令 (5s 超时, 2 次重试)
    LLM = "llm"                 # Mind 核 LLM 生成 (仅 Mind 核使用)
    GUARD_ONLY = "guard_only"   # 仅执行守门校验, 无实际操作

各类型的执行器:
  TOOL          → HarrisOrchestrator 的 node_executor 回调
  RPC_CALL      → LocalTianquanRPC (Python 子进程 stdin/stdout)
  BUS_COMMAND   → RemoteExecutor (GlobalBusTCPClient)
  LLM           → 由 BIOS 核拒绝 (LLM 调用仅存在于 Mind 核的 M5 生成环节)
  GUARD_ONLY    → 仅运行 pre_guard + post_guard, 跳过 execute()
```

### 1.5 跨域远程执行——DomainExecutorPool 的核心载体

V2.0 新增 `RemoteExecutor` 类，封装通过 TCP 总线向瑶灵/瑶光下发工作流的能力：

```python
class RemoteExecutor:
    """向远程域 (瑶灵/瑶光) 下发工作流执行指令。"""
    
    def __init__(self, bus_client: GlobalBusTCPClient, target_domain: str):
        self.bus = bus_client
        self.target = target_domain  # "l" or "g"
    
    async def dispatch(self, workflow_id: str, task: str, constraints: dict) -> dict:
        """下发指令并等待结果。"""
        ack = await self.bus.publish(
            target_domain=self.target,
            cmd="run_static_workflow",
            payload={
                "workflow_id": workflow_id,
                "task": task,
                "constraints": constraints,
            }
        )
        # 瑶灵/瑶光的 MCP 进程执行工作流并通过总线返回结果
        return ack
```

特点：瑶灵和瑶光不主动发起跨域请求。它们只被动接收来自 Master-Harris 的指令，执行本地工作流，将结果通过总线回传。这就是 MH-1（单向调度）的实现。

### 1.6 约束自动注入

Master-Harris 在执行任何工作流前，自动从全局 DNA 向量库加载对应域的 SPEC 规范，注入 `constraints`：

```
注入优先级:
  1. Master-Harris 注入 (最高优先, 不可覆盖):
     dna_root_id / location_fingerprint / spec_version
  2. 域 SPEC 自动加载 (从 DNA 向量库读取):
     域规范版本、工作流限制 (allow_dynamic)、安全阈值
  3. 用户提供 (最低优先, 仅在不冲突时保留):
     任务描述、项目路径、变更文件列表等

约束覆盖规则:
  Master-Harris 注入的值不可被用户提供的值覆盖
  域 SPEC 自动加载的值不可被用户提供的值覆盖
  仅用户特定的业务参数 (project_root, change_files 等) 使用用户提供的值
```

---

## 第二章 · 增强的 WorkflowContext

### 2.1 完整数据结构

```python
@dataclass
class WorkflowContext:
    # ── DNA 绑定 (Master-Harris 注入) ──
    global_uid: str = ""                    # 23 字符 GlobalUID
    dna_root_id: str = ""                   # 向后兼容
    location_fingerprint: str = ""          # 128-bit hex

    # ── 执行身份 ──
    domain: str = ""                        # "tianquan" | "yaoling" | "yaoguang"
    executor_type: str = ""                 # "local_rpc" | "remote_tcp" | "stdio_mcp"

    # ── 任务 (V1.0 已有) ──
    task: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)

    # ── 执行产物 ──
    artifacts: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    trace: List[Dict[str, Any]] = field(default_factory=list)

    # ── 路由戳 (V2.0 新增) ──
    route_stamps: List[RouteStamp] = field(default_factory=list)

    # ── 生命周期 ──
    cancelled: bool = False
    run_id: str = ""
    started_at: float = 0.0
    completed_at: float = 0.0

    # ── 降级标记 ──
    degraded: bool = False                  # 是否在降级模式运行
    degradation_reason: str = ""

    def stamp(self, workshop: str, operation: str, phase_id: str, 
              node_id: str = "_phase_", detail: str = "") -> None:
        """追加工厂车间路由戳。"""
        from hashlib import sha256
        import json as _json
        snap_raw = _json.dumps(self.artifacts, sort_keys=True, default=str)
        crc_snap = sha256(snap_raw.encode()).hexdigest()[:8]
        self.route_stamps.append(RouteStamp(
            workshop=workshop, operation=operation,
            phase_id=phase_id, node_id=node_id,
            timestamp=time.time(), detail=detail, crc_snap=crc_snap,
        ))
```

### 2.2 约束校验

```python
# WorkflowContext 新增方法
def validate_constraints(self, schema: dict) -> Tuple[bool, List[str]]:
    """对照 constraints_schema 校验 constraints 是否包含所有 required 字段。"""
    required = schema.get("required", [])
    missing = [f for f in required if f not in self.constraints]
    return len(missing) == 0, missing
```

---

## 第三章 · 增强的 HarrisOrchestrator

### 3.1 完整执行流程（带钩子 + 路由戳）

```python
async def run(self, task: str, constraints: dict = None,
              node_executor=None) -> WorkflowContext:
    
    ctx = WorkflowContext(
        task=task,
        constraints=constraints or {},
        run_id=self.workflow.digest(),
        domain=self.workflow.metadata.get("domain", ""),
        executor_type=self.workflow.metadata.get("communication", ""),
        global_uid=constraints.get("dna_root_id", ""),  # 从 constraints 提取
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
            await self._fire("workflow:fault", ctx=ctx, reason="constraints_missing")
            if self.mode == RunMode.STRICT:
                raise HarrisError(f"约束缺失: {missing}")
    
    # ── 全局守门 ──
    ok, msgs = self.guard_ctrl.check(self.workflow.global_guard, ctx, "Global")
    if not ok:
        await self._fire("workflow:guard_failed", ctx=ctx, messages=msgs)
        ctx.metrics["guard_reject"] = 1.0
        return ctx
    
    # ── 阶段推进 ──
    for phase in self.workflow.phases:
        if ctx.cancelled:
            break
        
        # Hook: phase:entry + 追加入口戳
        await self._fire("phase:entry", ctx=ctx, phase=phase)
        ctx.stamp(ctx.domain, "PHASE_ENTRY", phase.phase_id)
        
        # 阶段入口守门
        ok, msgs = self.guard_ctrl.check(phase.entry_guard, ctx, f"Phase({phase.phase_id})")
        if not ok:
            ctx.stamp(ctx.domain, "GUARD_BLOCKED", phase.phase_id, detail="; ".join(msgs))
            continue
        
        # 执行节点 (串行或并行)
        if phase.parallel and len(phase.nodes) > 1:
            tasks = [self._run_node_with_guard(node, ctx, node_executor) for node in phase.nodes]
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            for node in phase.nodes:
                if ctx.cancelled: break
                await self._run_node_with_guard(node, ctx, node_executor)
        
        # 阶段出口守门
        self.guard_ctrl.check(phase.exit_guard, ctx, f"Phase({phase.phase_id})-exit")
        
        # 追加出口戳 + Hook: phase:exit
        ctx.stamp(ctx.domain, "PHASE_COMPLETE", phase.phase_id)
        await self._fire("phase:exit", ctx=ctx, phase=phase)
    
    # ── 收尾 ──
    ctx.completed_at = time.time()
    ctx.metrics["elapsed_seconds"] = ctx.completed_at - ctx.started_at
    ctx.stamp(ctx.domain, "WORKFLOW_COMPLETE", "_workflow_")
    await self._fire("workflow:complete", ctx=ctx)
    
    return ctx
```

### 3.2 钩子系统

```python
class HarrisOrchestrator:
    def __init__(self, ...):
        ...
        self._hooks: Dict[str, List[Callable]] = defaultdict(list)
    
    def on(self, event: str, callback: Callable) -> None:
        """注册生命周期钩子。"""
        self._hooks[event].append(callback)
    
    def off(self, event: str, callback: Callable) -> None:
        """移除钩子。"""
        if event in self._hooks:
            self._hooks[event] = [h for h in self._hooks[event] if h != callback]
    
    async def _fire(self, event: str, **kwargs) -> None:
        """触发钩子。每个钩子独立异常隔离——一个失败不影响其他。"""
        for hook in self._hooks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(**kwargs)
                else:
                    hook(**kwargs)
            except Exception:
                logger.exception("Hook [%s] 异常: %s", event, hook.__name__)
```

### 3.3 远程执行器

```python
class RemoteExecutor:
    """
    远程域工作流执行器。
    
    向瑶灵/瑶光下发 run_static_workflow 指令，等待结果返回。
    5s 超时 + 最多 2 次重发。
    """
    
    def __init__(self, bus_client: GlobalBusTCPClient, target_domain: str):
        self.bus = bus_client
        self.target = target_domain
    
    async def dispatch(self, workflow_id: str, task: str, 
                       constraints: dict) -> Dict[str, Any]:
        """下发工作流并等待结果。"""
        for attempt in range(3):
            try:
                ack = await asyncio.wait_for(
                    self.bus.publish(
                        target_domain=self.target,
                        cmd="run_static_workflow",
                        payload={
                            "workflow_id": workflow_id,
                            "task": task,
                            "constraints": constraints,
                        }
                    ),
                    timeout=5.0,
                )
                if ack.get("status") == "ok":
                    return ack
                logger.warning("远程执行 %s → %s 失败 (attempt %d): %s",
                              workflow_id, self.target, attempt+1, ack)
            except asyncio.TimeoutError:
                logger.warning("远程执行 %s → %s 超时 (attempt %d)",
                              workflow_id, self.target, attempt+1)
        
        return {"status": "error", "reason": f"远程域 {self.target} 无响应 (3次尝试全部超时)"}
```

---

## 第四章 · YAML DSL V2.0 完整规范

### 4.1 顶层结构

```yaml
workflow_id: wf_code_review          # 唯一工作流 ID (必填)
version: "2.0"                        # 工作流版本 (必填)
description: >                        # 工作流描述 (必填)
  多行描述文本
mode: strict                          # strict | flexible | dry_run (必填)

# ── V2.0 新增顶层字段 ──
domain: tianquan                      # tianquan | yaoling | yaoguang (必填)
route_tag: code_review                # Master-Harris 路由标签 (必填)
executor_type: local_rpc              # local_rpc | remote_tcp (必填)

# ── 约束 schema ──
constraints_schema:                   # (必填, V2.0 新增 dna_root_id/location_fingerprint/spec_version 为前三个 required)
  type: object
  required: [dna_root_id, location_fingerprint, spec_version, task, ...]
  properties: {...}

# ── 全局守门 ──
global_guard:                         # (必填, V2.0 必须包含 5 条 mh_ 前缀的 Master 铁律守门规则)
  guard_name: xxx
  rules: [...]

# ── 阶段 ──
phases:                               # (必填, 至少 1 个阶段)
  - phase_id: p1_xxx
    route_stamp_workshop: "M1"        # V2.0 新增: 本阶段的路由戳车间标识
    route_stamp_operation: "LINT_CHECK" # V2.0 新增: 本阶段的路由戳操作类型
    ...

# ── 元数据 ──
metadata:
  domain: tianquan
  route_tag: code_review
  spec_version: "TIANQUAN-SPEC-20260711"
  communication: local_rpc
  allow_dynamic: false
  master_harris:                      # V2.0 新增: Master-Harris 五层信息
    layer: DomainExecutorPool
    executor: LocalTianquanRPC
    snapshot_handler: SnapshotAggregator
    fault_handler: FaultMemoryArchiver
```

### 4.2 Agent 节点扩展字段

```yaml
nodes:
  - node_id: n1_lint_check
    agent_type: tool                  # tool | rpc_call | bus_command | llm | guard_only
    prompt_template: >
      执行编码规范校验...
    timeout_seconds: 60
    retry_count: 1
    depends_on: []
    
    # ── V2.0 新增节点字段 ──
    route_stamp_workshop: "M1"       # 节点级路由戳车间 (覆盖 phase 级)
    route_stamp_operation: "LINT"    # 节点级路由戳操作类型
    
    # 跨域指令专用字段 (agent_type = "bus_command" 时必填)
    bus_target_domain: ""            # "l" | "g"
    bus_command: ""                  # 下发指令名称
    bus_timeout_seconds: 5           # 超时
    bus_max_retries: 2               # 重试次数
    
    # RPC 调用专用字段 (agent_type = "rpc_call" 时必填)
    rpc_method: ""                   # RPC 方法名
    rpc_params: {}                   # RPC 参数
```

### 4.3 全局守门 V2.0 强制规则

每个工作流的 `global_guard` 必须包含以下 5 条 Master-Harris 铁律对应的守门规则（以 `mh_` 前缀命名）：

```yaml
global_guard:
  guard_name: tianquan_xxx_preflight
  rules:
    # ... 域特定守门规则 ...
    
    # ── 以下 5 条为全系统强制 ──
    - name: mh_no_cross_domain_issue
      description: MH-1 | 本域禁止主动向其他域下发指令。跨域指令仅由 Master-Harris 发出
      priority: 0
    
    - name: mh_spec_constraints_required
      description: MH-2 | 必须从全局 DNA 向量库读取域 SPEC 填充 constraints
      priority: 0
    
    - name: mh_no_llm_float_output
      description: MH-4 | 32D 向量仅由瑶灵/瑶光规则计算产出，禁止 LLM 直接输出浮点值
      priority: 1
    
    - name: mh_single_globaluid
      description: MH-5 | 本次交互所有快照共用同一个 GlobalUID，禁止多 UID 分裂
      priority: 1
    
    - name: mh_no_local_persistence
      description: MH-7 | 本域不自行持久化。所有状态/快照/结果统一交给太虚境 M2 三库底座
      priority: 2
```

### 4.4 YAML 解析器的 V2.0 变更

`HarrisDslParser` 新增对以下字段的解析：
- 顶层: `domain`, `route_tag`, `executor_type`
- 阶段: `route_stamp_workshop`, `route_stamp_operation`
- 节点: `route_stamp_workshop`, `route_stamp_operation`, `bus_target_domain`, `bus_command`, `bus_timeout_seconds`, `bus_max_retries`, `rpc_method`, `rpc_params`
- 元数据: `master_harris` 子块

解析规则：所有 V2.0 新增字段均为可选（向后兼容 V1.0 YAML）。缺失时使用默认值。

---

## 第五章 · 三域 YAML 工作流全集

### 5.1 天权域 (4 套 + 需要新增的 0 套)

现有 4 套已对齐 Master-Harris 路由表，需升级到 V2.0 DSL 格式：

| workflow_id | route_tag | executor_type | phases | nodes | 升级内容 |
|------------|-----------|--------------|--------|-------|---------|
| `wf_code_review` | `code_review` | `local_rpc` | 4 | 8 | 新增 domain/route_tag/executor_type 顶层字段 + phase/node route_stamp |
| `wf_arch_refactor` | `arch_refactor` | `local_rpc` | 4 | 7 | 同上 |
| `wf_sql_governance` | `sql_manage` | `local_rpc` | 4 | 8 | 同上 |
| `wf_knowledge_organize` | `knowledge_sort` | `local_rpc` | 5 | 7 | 同上 |

### 5.2 瑶灵域 (现有 3 套 + 需要新增 2 套 = 5 套)

| workflow_id | route_tag | executor_type | 状态 |
|------------|-----------|--------------|------|
| `wf_sensation_pipeline` | `sense_sequence` | `remote_tcp` | ✅ 已有, 需升级 V2.0 DSL |
| `wf_safety_gate` | (内部调用, 不暴露为独立路由) | `remote_tcp` | ✅ 已有, 作为 sensation_pipeline 的子流程 |
| `wf_yaoling_snapshot` | (内部调用) | `remote_tcp` | ✅ 已有, 作为快照发射 |
| `wf_body_adjust` | `body_adjust` | `remote_tcp` | ❌ 待新建 — 激素/体感调控 |
| `wf_physical_control` | `physical_control` | `remote_tcp` | ❌ 待新建 — 动作序列控制 |

### 5.3 瑶光域 (0 套 → 需要新建 3 套)

| workflow_id | route_tag | executor_type | 状态 |
|------------|-----------|--------------|------|
| `wf_time_tick` | `time_tick` | `remote_tcp` | ❌ 待新建 — 时序推进 |
| `wf_scene_sim` | `scene_sim` | `remote_tcp` | ❌ 待新建 — 场景模拟 |
| `wf_world_snapshot` | `world_snapshot` | `remote_tcp` | ❌ 待新建 — 世界快照 |

### 5.4 Master-Harris 静态路由表（完整 11 条目）

```python
MH_ROUTE_TABLE = {
    # ── 工程算力 (本地 RPC) ──
    "code_review":      {"domain": "tianquan", "workflow": "wf_code_review",        "executor": "local_rpc"},
    "arch_refactor":    {"domain": "tianquan", "workflow": "wf_arch_refactor",      "executor": "local_rpc"},
    "sql_manage":       {"domain": "tianquan", "workflow": "wf_sql_governance",     "executor": "local_rpc"},
    "knowledge_sort":   {"domain": "tianquan", "workflow": "wf_knowledge_organize", "executor": "local_rpc"},
    
    # ── 躯体感知 (TCP → 瑶灵) ──
    "body_adjust":      {"domain": "yaoling",  "workflow": "wf_body_adjust",        "executor": "remote_tcp"},
    "sense_sequence":   {"domain": "yaoling",  "workflow": "wf_sensation_pipeline", "executor": "remote_tcp"},
    "physical_control": {"domain": "yaoling",  "workflow": "wf_physical_control",   "executor": "remote_tcp"},
    
    # ── 环境推演 (TCP → 瑶光) ──
    "time_tick":        {"domain": "yaoguang", "workflow": "wf_time_tick",          "executor": "remote_tcp"},
    "scene_sim":        {"domain": "yaoguang", "workflow": "wf_scene_sim",          "executor": "remote_tcp"},
    "world_snapshot":   {"domain": "yaoguang", "workflow": "wf_world_snapshot",     "executor": "remote_tcp"},
    
    # ── 无调度 ──
    "pure_chat":        {"domain": "taixu",    "workflow": None,                    "executor": "none"},
}
```

---

## 第六章 · 运行模式与兼容性

### 6.1 三域对 V1.0 / V2.0 YAML 的支持

```
天权域 (tianquan):
  RUN_MODE=dev  → HarrisDslParser 同时支持 V1.0 和 V2.0 YAML 格式
  RUN_MODE=prod → 仅支持 V2.0 YAML (V1.0 格式拒绝解析, 打印迁移指引)

瑶灵域 (yaoling):
  仅支持 V2.0 YAML
  allow_dynamic_workflow = False (MH-3 硬拦截)
  agent_type 仅允许 "tool" 和 "guard_only" (瑶灵不调 LLM, 不上报总线指令)
  新增的 mh_no_cross_domain_issue 守门规则会拦截任何 BUS_COMMAND 类型的节点

瑶光域 (yaoguang):
  仅支持 V2.0 YAML
  allow_dynamic_workflow = True (仅长期推演)
  常规时序强制静态 YAML
```

### 6.2 向后兼容

```
V1.0 YAML → V2.0 解析器:
  缺失 domain → 默认为 "tianquan"
  缺失 route_tag → 默认为 workflow_id
  缺失 executor_type → 默认为 "local_rpc"
  缺失 route_stamp_* → 不加戳, 不报错
  缺失 mh_* 守门规则 → 打印 WARN, 不阻断 (过渡期)
```

---

## 第七章 · 实现清单

### 7.1 新建文件

| 文件 | 内容 |
|------|------|
| `common/harris_core_v2.py` | V2.0 引擎: RouteStamp, WorkflowContext V2, AgentType 枚举, RemoteExecutor, 增强 HarrisOrchestrator (钩子系统 + 路由戳 + 约束校验), HarrisDslParser V2 |
| `common/harris_yaml_v2_spec.md` | 本规范文档 (可选, 内容已在此) |

### 7.2 修改文件

| 文件 | 变更 |
|------|------|
| `common/base_mcp_harris.py` | 移除天权的 `send_cross_domain_command` 工具 (MH-1: 天权不主动跨域发指令)。瑶灵/瑶光保留但标注"仅接收, 不主动发起" |
| `domain_tianquan/mcp_harris_t.py` | 天权 MCP 工具集: 移除 `send_cross_domain_command`, 新增 `run_workflow` / `lint_check` / `arch_parse` / `sql_audit` / `generate_snapshot` (均为本地 RPC 调用) |
| 天权 4 套 YAML | 升级到 V2.0 DSL: 新增 domain/route_tag/executor_type + phase/node route_stamp |
| 瑶灵 3 套 YAML | 升级到 V2.0 DSL |

### 7.3 不修改

| 文件 | 原因 |
|------|------|
| `common/harris_core.py` | 保留 V1.0 兼容, 瑶灵 V1.0 YAML 仍可解析 |
| `global_bus_main.py` | 无变更 |
| `domain_yaoling/` (除 YAML 和 mcp_harris_l.py) | 通道处理器/安全阈值/编解码器无变更 |
| `domain_yaoguang/` | 待 P3 建设 |

---

## 附录 A · 变更记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-07-11 | V1.0 | 初版。RunMode/GuardAction/WorkflowGuard/AgentNode/PhaseUnit/HarrisWorkflow/GuardController/HarrisOrchestrator/HarrisDslParser |
| 2026-07-12 | V2.0 | 新增六大能力: DNA 绑定 / 路由戳 / 生命周期钩子 / Agent 类型扩展 / 跨域远程执行 / 约束自动注入。全局守门强制 5 条 MH 铁律。完整 11 条目路由表。 |
