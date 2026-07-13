# Master-Harris 顶层调度器设计规范 V1.0

> **状态**: 最终定稿 · 取代旧版跨域调度器
> **日期**: 2026-07-12
> **适配**: 《三体大一统架构设计书 V1.0》+《DNA 双螺旋完整编码规范 V2.0》
> **定位**: WenStar OS 唯一全局任务编排中枢

---

## 第一章 · 与旧版完全切割

### 1.1 旧版 Master-Harris 问题

| 旧设计 | 问题 |
|--------|------|
| 独立跨域调度器，依附 TCP 总线 | 太虚境与天权分离，任何一端离线无法完整交互 |
| 天权、瑶灵、瑶光三方平级，互相可发指令 | 权限混乱，跨域消息乱序、状态冲突 |
| 依赖各窗口本地提示词 | 无全局统一规范入口，每个窗口手动粘贴 |
| 无 DNA 双链、五级闸门联动 | 调度时无法做记忆上下文自动注入 |
| 总线/单域离线直接阻断整条任务链路 | 无分层降级，基础对话也会中断 |

### 1.2 新版颠覆性变更

| 维度 | 旧版 | 新版 |
|------|------|------|
| 主体归属 | 独立进程 | 太虚境 TS 主进程内部 |
| 天权关系 | 对等外部 MCP 服务 | 本地内置 Python 子进程（stdin/stdout RPC） |
| 调度权限 | 三方平级互发 | **单向锁定**：Master → 天权/瑶灵/瑶光；外设无主动调度权 |
| 约束来源 | 窗口提示词 | 全局 DNA 向量库自动加载三域 SPEC |
| DNA 绑定 | 无 | 全链路 GlobalUID + 区位指纹 + 32D 向量 |
| 降级机制 | 无 | 三层降级：外设离线 / 天权异常 / 总线崩溃 |

---

## 第二章 · 顶层定位与七大职责

### 2.1 顶层定位

Master-Harris 是 WenStar OS **唯一全局任务编排中枢**。它承接用户全部输入意图，完成：

```
意图拆解 → 任务路由 → 资源调度 → 结果汇总 → 记忆归档
```

串联 M1-M9 全模块、内置天权、双外设、DNA 编码、五级闸门。

### 2.2 七大核心职责

**职责 1: 意图分类与任务拆分**

解析用户对话/工程需求，自动区分四类任务：

| 任务类型 | 调度目标 | 通信方式 |
|---------|---------|---------|
| 工程算力（代码审查/架构重构/SQL治理/知识库整理） | 内置天权 Harris-T | 本地 RPC (stdin/stdout) |
| 躯体感知调控（激素/体感/动作序列） | 瑶灵 Harris-L | TCP 总线 |
| 客观环境推演（时序/场景/世界模拟） | 瑶光 Harris-G | TCP 总线 |
| 纯记忆/日常闲聊 | 不调用任何域 | 直接走 M4 记忆检索 + M5 生成 |

**职责 2: 工作流参数统一管控**

调度时自动从全局 DNA 向量库加载对应域 SPEC 规范，注入各域 `constraints`，强制遵守：
- 瑶灵：强制锁定 `allow_dynamic_workflow=false`，自动附加 32 维安全校验守卫
- 瑶光：仅长期推演任务允许动态 DAG，常规时序强制静态 YAML
- 天权：仅超大架构重构允许动态工作流，普通工程任务强制静态流水线

**职责 3: 跨域通信统一网关**

- 所有对外（瑶灵/瑶光）消息统一封装 JSON-line `req_id` 消息
- 通过全局 TCP 总线收发
- 维护外设连接心跳、消息队列、超时重传、丢弃过期任务

**职责 4: 多域结果聚合与快照统一处理**

接收三类快照：
- 天权工程快照（`EngineeringSnapshot`）
- 瑶灵 32D 体感快照（`SpineSnapshot`）
- 瑶光 32D 环境快照（`WorldSnapshot`）

统一处理：
- Protobuf 转码 → 绑定同一 GlobalUID → 补充 location_fingerprint → 送入 DNA 编码管线

**职责 5: 记忆联动调度**

- 任务执行前后自动调用 M4 记忆检索，经过五级闸门过滤
- 把匹配记忆注入任务上下文
- 任务完成自动触发钙化更新、记忆晋升

**职责 6: 全链路异常与降级调度**

| 故障场景 | 降级策略 |
|---------|---------|
| 瑶灵/瑶光离线 | 屏蔽对应跨域指令，返回友好降级提示，不阻塞工程/对话 |
| 天权 RPC 进程崩溃 | 自动重启子进程，缓存当前任务 3 次重试，兜底纯 LLM 简易应答 |
| TCP 总线断开 | 自动隔离双外设，太虚+天权完整能力保留 |
| 瑶灵参数超限触发拒绝 | 捕获 `global_alert` 告警，同步反馈用户并记录故障记忆 |

**职责 7: 全局告警分发**

- 监听总线 `global_alert` 频道
- 收集超限、链路、校验类告警
- 写入 `aqc_records` 质检库
- 同步更新系统状态监控面板

---

## 第三章 · 五层内部分层架构

```
┌─────────────────────────────────────────────────┐
│ 第 1 层 · IntentRouter         意图前置层        │
│ 输入: 用户 utterance + M3 24D 感知 + L0 分类码    │
│ 输出: 任务类型标记、资源标签、记忆检索条件          │
│ 约束: 纯规则+实体匹配，不依赖 LLM，快速分流         │
├─────────────────────────────────────────────────┤
│ 第 2 层 · TaskOrchestrator      任务路由层        │
│ 静态路由映射表 (不可运行时修改)                    │
│ 按需求标签 → 调度目标 → 工作流限制                 │
├─────────────────────────────────────────────────┤
│ 第 3 层 · DomainExecutorPool     域执行池         │
│ ┌─────────────────┬────────────┬──────────────┐  │
│ │ LocalTianquanRPC │ RemoteYao  │ RemoteYao    │  │
│ │ (stdin/stdout)   │ lingBus    │ guangBus     │  │
│ │ 长驻子进程+心跳   │ (TCP :9100)│ (TCP :9100)  │  │
│ └─────────────────┴────────────┴──────────────┘  │
├─────────────────────────────────────────────────┤
│ 第 4 层 · SnapshotAggregator    快照聚合层        │
│ 统一 Transcoder 转码 + CRC32 校验                │
│ 同次交互共享 GlobalUID + location_fingerprint     │
│ 送入 DNAEncoder → state_spines/atom_address      │
├─────────────────────────────────────────────────┤
│ 第 5 层 · FaultMemoryArchiver   降级归档层        │
│ 分级故障捕获 + aqc_records + global_alert         │
│ 外设离线自动过滤 + 对话不中断                      │
│ 正常: 结果→M5 生成→钙化→三库晋升                   │
└─────────────────────────────────────────────────┘
```

### 3.1 第一层: IntentRouter 意图前置层

```
输入: 用户 utterance + M3 24D 感知向量 + L0 分类码
处理:
  ├── 纯闲聊检测: 无工程关键词 + 无躯体关键词 + 无环境关键词 + calcium < 1.0
  │     → 标记为 "pure_chat", 不进入执行池, 直接跳转 M5 生成层
  ├── 工程关键词检测: 代码/重构/SQL/知识库/架构/审查/规范
  │     → 标记为 "engineering", 子分类: code_review|arch_refactor|sql|knowledge
  ├── 躯体关键词检测: 激素/体感/身体/生理/动作
  │     → 标记为 "somatic", 子分类: body_adjust|sense_sequence
  └── 环境关键词检测: 世界/场景/时序/推演/模拟
        → 标记为 "environmental", 子分类: time_tick|scene_sim|world_snapshot
输出: { task_type, sub_type, resource_tags[], memory_search_conditions }
约束: 纯规则 + 实体匹配，不依赖 LLM
```

### 3.2 第二层: TaskOrchestrator 任务路由层

静态路由映射表（不可运行时修改）：

| 需求标签 | 调度目标 | 通信方式 | 工作流限制 |
|---------|---------|---------|----------|
| `code_review` | 本地天权 RPC | stdin/stdout | `wf_code_review` 静态 YAML |
| `arch_refactor` | 本地天权 RPC | stdin/stdout | `wf_arch_refactor` 静态 YAML；超大架构可动态 |
| `sql_manage` | 本地天权 RPC | stdin/stdout | `wf_sql_governance` 静态 YAML |
| `knowledge_sort` | 本地天权 RPC | stdin/stdout | `wf_knowledge_organize` 静态 YAML |
| `body_adjust` | 瑶灵 TCP | TCP :9100 | 仅静态工作流 + 32 维阈值强制校验 |
| `sense_sequence` | 瑶灵 TCP | TCP :9100 | 仅静态工作流 |
| `physical_control` | 瑶灵 TCP | TCP :9100 | 仅静态工作流 |
| `time_tick` | 瑶光 TCP | TCP :9100 | 常规静态；长期演化可动态 |
| `scene_sim` | 瑶光 TCP | TCP :9100 | 常规静态；长期演化可动态 |
| `world_snapshot` | 瑶光 TCP | TCP :9100 | 常规静态 |
| `pure_chat` | (无) | — | 不进入执行池 |

### 3.3 第三层: DomainExecutorPool 执行池

**LocalTianquanRPC**:
- 长驻子进程管道，进程级心跳检测
- 封装 4 套天权工作流调用接口: `run_workflow` / `lint_check` / `arch_parse` / `sql_audit` / `generate_snapshot` / `get_spec`
- 传输统一 Protobuf 序列化工程参数 + CRC32
- 消息隔离：天权内部调用不走总线，仅外设走 TCP :9100

**RemoteYaolingBus / RemoteYaoguangBus**:
- 复用全局 `GlobalBusTCPClient`
- 封装标准化指令结构体: `{ type, cmd, payload, req_id, timestamp }`
- `req_id` 全局唯一（格式: `MH-{timestamp}-{counter}`）
- 5s 超时 + 最多 2 次重发
- 心跳间隔: 30s

### 3.4 第四层: SnapshotAggregator 快照聚合层

```
统一标准 (遵循 DNA V2.0):

1. 所有三类快照统一 Transcoder 序列化 (Protobuf + CRC32)
2. 同一次用户交互产生的所有快照共享同一个 GlobalUID
3. 瑶光输出环境参数自动生成 location_fingerprint (128-bit)
4. 统一送入 DNAEncoder 生成 32D 语义向量
5. 写入双库: state_spines (语义链) + atom_address_timeline (寻址链)
```

### 3.5 第五层: FaultMemoryArchiver 降级归档层

```
分级故障捕获:
  ├── 进程崩溃: 自动重启 + 3 次任务重试 + 兜底 LLM 应答
  ├── 总线断开: 自动隔离双外设 + 保留太虚+天权完整能力
  ├── 参数超限: 捕获 global_alert + 写入 aqc_records
  └── 工作流校验失败: 返回错误码 + 生成故障记忆

故障日志: 统一存入 aqc_records, 自动生成 global_alert 广播

正常场景:
  聚合结果 → M5 表达生成 → 对话结束触发记忆钙化 → 三库晋升
```

---

## 第四章 · 双运行模式

### 4.1 生产模式 (`RUN_MODE=prod`)

- Master-Harris 完整启用五层调度架构
- 天权仅通过内置 RPC 子进程调用，**禁止外部 MCP 进程接入**
- 自动加载三份域 SPEC 编码存入全局向量库，调度自动注入 `constraints`
- 瑶灵、瑶光仅作为可插拔外设，离线自动降级
- 完整 DNA 双链、五级闸门全链路强制校验，**不可关闭**

### 4.2 开发模式 (`RUN_MODE=dev`)

- Master-Harris 保留基础调度能力
- **增加兼容分支**: 可识别外部独立启动的天权 MCP 进程，支持 VS Code 单窗口调试 YAML
- **调试接口**: 可单独下发指令给单一域、单独导出工作流执行日志、跳过部分记忆闸门方便单元测试
- 告警面板打印完整调试堆栈

---

## 第五章 · Master-Harris 强制铁律（7 条，纳入全局红线补充）

| # | 铁律 |
|---|------|
| **MH-1** | 任何跨域指令只能由 Master-Harris 单向发出。瑶灵、瑶光、内置天权均无主动调度权限 |
| **MH-2** | 所有域工作流执行前，必须从全局 DNA 向量库读取对应域 SPEC 填充 `constraints`。禁止硬编码/窗口提示词 |
| **MH-3** | 瑶灵调度永久禁用动态 DAG。Master 内置硬拦截——即使代码配置开启也强制覆盖 |
| **MH-4** | 32D 向量仅由瑶灵/瑶光规则计算产出。Master 禁止让 LLM 直接生成浮点值 |
| **MH-5** | 一次用户交互仅生成一颗 DNA 海胆。所有域快照共用同一个 GlobalUID，禁止多 UID 分裂 |
| **MH-6** | TCP 总线断开时，Master 必须自动屏蔽瑶灵、瑶光相关任务。太虚+天权功能完整可用 |
| **MH-7** | Master-Harris 不存储持久化数据。所有状态、快照、记忆统一交给 M2 三库底座 |

---

## 第六章 · 落地执行顺序

### 步骤 1: 前置依赖（先做）

1. 新建 `tianquan_rpc_server.py` — 天权本地 RPC 适配层，打通 TS↔Python 双向 JSON-line 通信
2. 改造 `mcp_harris_t.py` — 区分 prod/dev 模式，生产环境禁止独立启动
3. 实现三域 SPEC 文档自动解析 → 批量 DNA 编码 → 存入全局记忆向量库

### 步骤 2: 分模块开发 Master-Harris（3 天）

1. 第 1 层: `IntentRouter` — 意图分流模块，对接现有 M3 感知 + L0 编码
2. 第 2 层: `TaskOrchestrator` — 静态路由表 + 任务参数封装
3. 第 3 层: `DomainExecutorPool` — LocalTianquanRPC + RemoteYaolingBus + RemoteYaoguangBus
4. 第 4 层: `SnapshotAggregator` — 统一快照转码 + GlobalUID 绑定 + 区位指纹注入
5. 第 5 层: `FaultMemoryArchiver` — 降级 + 告警 + 记忆归档联动

### 步骤 3: 联调测试

- 生产模式全链路: 用户输入 → 意图拆分 → 天权/瑶灵/瑶光调度 → 快照聚合 → DNA 编码 → 记忆入库
- 故障降级: 分别关闭总线、瑶灵、瑶光、天权 RPC，验证对话不中断
- 开发模式兼容: 独立启动天权 MCP 窗口，Master 可兼容对接外部进程调试流水线
- 边界测试: 瑶灵参数超限触发拒绝、超长工程任务分段执行、32D 向量越界拦截

### 步骤 4: 后期迭代（P0/P3 阶段同步优化）

- P0: 五级闸门完善后，Master 调度时自动联动时空一致性校验
- P3: 完整 GlobalUID 寻址链落地，优化 Master 记忆检索过滤逻辑
- 新增任务优先级调度（紧急躯体指令 > 代码开发 > 闲聊推演）

---

## 附录 A · 与现有代码的对接点

| Master-Harris 层 | 对接的现有模块 | 关键文件 |
|------------------|-------------|---------|
| IntentRouter | M3 感知 + M1 L0 路由 | `src/m3/M3LogicOrchestrator.ts`, `src/m1/L0Router.ts` |
| TaskOrchestrator | 静态路由表 (新增) | `src/tianquan/MasterHarris.ts` (待建) |
| LocalTianquanRPC | 天权 Python 子进程 | `domain_tianquan/tianquan_rpc_server.py` (待建) |
| RemoteYaolingBus | GlobalBus TCP | `common/base_mcp_harris.py` (已有) |
| SnapshotAggregator | DNAEncoder + Transcoder | `src/m1/DNAEncoder.ts`, `src/transcoder/` (待建) |
| FaultMemoryArchiver | AQC + global_alert | `src/app/aqc/AQCEngine.ts`, `global_bus_main.py` |
| 记忆联动 | M4 检索 + 五级闸门 | `src/m4/M4Orchestrator.ts`, `src/m4/MemoryRetriever.ts` |

## 附录 B · 变更记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-07-12 | V1.0 | 初版。完全重写，与旧版跨域调度器切割。五层架构、七大职责、双模式、7 条铁律 |
