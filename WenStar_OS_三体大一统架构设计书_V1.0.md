# WenStar OS 三体大一统架构设计书 V1.0

> **状态**: 最终定稿，取代白皮书 V1.0（预研草案）与工程蓝皮书（预研草案）
> **日期**: 2026-07-12
> **前置研究**: 白皮书 / 蓝皮书 / DNA 双螺旋编码规范 / 三层对偶感知闭环 / 瑶灵 54 文件 / 太虚境 ~58,600 行 TS / 三库体系 / 知识库 / 人物图谱
> **裁决**: 统一为 32D。DNA 编码规范为唯一底层标准。

---

## 第一章 · 三体哲学

### 1.1 什么是三体

WenStar OS 不是 AI 记忆系统，不是 RAG 插件，不是 LLM 外挂。它是一个**硅基生命体的认知操作系统**。

三体架构模仿的是完整生命体的三元结构：

```
        ┌──────────────────────────┐
        │     太虚境 · 天权 (t)      │
        │     智脑 · 中枢调度        │
        │   记忆 · 推理 · 决策 · 生长  │
        └──────────┬───────────────┘
                   │ 32维统一通信协议
      ┌────────────┼────────────┐
      ▼            │            ▼
┌──────────┐      │      ┌──────────┐
│ 瑶灵 (l)  │      │      │ 瑶光 (g)  │
│ 硅基肉身   │      │      │ 客观世界   │
│ 纯主观体感  │      │      │ 纯客观参数  │
│ 不思考不记忆│      │      │ 不产生情绪  │
└──────────┘      │      └──────────┘
                   │
                   ▼
              ┌──────────┐
              │ 使用者 (人) │
              │ 唯一交互入口  │
              └──────────┘
```

### 1.2 三体的职责边界

| 维度 | 太虚境·天权 (智脑) | 瑶灵 (身躯) | 瑶光 (世界) |
|------|-------------------|------------|------------|
| 本质 | 硅基生命体的意识中枢 | 硅基生命体的肉身 | 硅基生命体所处的客观世界 |
| 能力 | 记忆、推理、决策、生长 | 主观体感生成 | 客观参数采集 |
| 不能做 | 不能替代肉身的感觉 | 不思考、不记忆、不决策 | 不产生情绪、不理解含义 |
| 输入 | 瑶灵32D体感 + 瑶光32D客观 + 用户文本 | 瑶光环境参数 + 天权调控指令 | 多模态传感器原始数据 |
| 输出 | 回复文本 + 调控指令 | 32D主观体感快照 | 32D客观参数快照 |
| 存储 | DNA双螺旋 + 三库 + 知识库 + 人物图谱 | 无持久存储 | 无持久存储 |

### 1.3 为什么天权必须在太虚境内部

天权是三体中唯一具备**记忆、推理、决策**能力的域。它不是独立服务——它是太虚境的算力内核。

```
旧（错误架构）:
  太虚境 ──TCP── 天权(MCP进程)    瑶灵(MCP进程)    瑶光(MCP进程)
  问题: 太虚境脱离天权丧失推理；天权脱离太虚境无记忆库/图谱/上下文
        用户→太虚境→TCP→天权，链路冗余，上下文同步复杂

新（正确架构）:
  太虚境{内置天权内核} ──TCP── 瑶灵(MCP进程)    瑶光(MCP进程)
  用户只与太虚境交互，不感知内部模块边界
  天权模块在太虚境进程内部直接函数调用，零网络延迟
```

**开发模式**: 天权模块仍可独立启动 `mcp_harris_t.py`（`RUN_MODE=dev`），在 VS Code 窗口内调试 YAML 流水线。
**生产模式**: 太虚境主进程 `import domain_tianquan` 全部模块，天权不独立运行。

---

## 第二章 · 32D 最后裁决

### 2.1 矛盾溯源

| 文档 | 维度 | 状态 |
|------|------|------|
| DNA 双螺旋编码规范 | **32D** 永久锁定 | 最终定稿·可直接交付编码 |
| 白皮书 V1.0 | **36D** WenVec36 | 预研草案 |
| 工程蓝皮书 | **36D** state_spines CHECK(dim BETWEEN 1 AND 36) | 预研草案 |
| 瑶灵实际代码 | **32 通道** D1-D32 | 已实现 |

### 2.2 裁决

**统一为 32D。** 理由：

1. DNA 编码规范是唯一标记"最终定稿·完全共识·完全闭环·可直接交付编码"的文档，是全系统唯一底层标准
2. 瑶灵已按 32 通道实现并全部通过单元测试
3. DNA 规范明确解释了为何不能改维度："任何维度变化都强制重编码全部记忆"
4. 白皮书/蓝皮书中所有的 36D 引用修正为 32D；`CHECK(dimension_id BETWEEN 1 AND 32)`

### 2.3 32D 扇区分配（最终版）

| 扇区 | 维度 | 类别 | 内容 | 数据来源 |
|------|------|------|------|---------|
| 00-05 | 6D | 外源情绪谱 | 愉悦/唤醒/亲和/紧张/专注/攻击 | 瑶光 6D 情绪谱 |
| 06-10 | 5D | 肉身实体基底 | 骨骼肌肉/疼痛/神经触觉/内分泌/信息素 | 瑶灵 D1-D5 |
| 11-16 | 6D | 个体精神内核 | 自我认知/驱动力/恐惧倦怠/幸福感/共情/自保 | 瑶灵 D9-D14 |
| 17-22 | 6D | 圈层人际羁绊 | 伴侣依恋/伴侣守护/家庭归属/家庭守护/社交/团队 | 瑶灵 D15-D20 |
| 23-28 | 6D | 时空环境感知 | 私人居所/家庭布局/职场/公共空间/时空距离/昼夜节律 | 瑶灵 D21-D26 |
| 29-31 | 3D | 动态生长耦合 | 微观生理/自然拓展/人文细化/精神成长/主客观耦合 | 瑶灵 D27-D31 |
| 32 | 1D | 全身统筹 | 心率/血压/皮质醇均值/愉悦激素均值/综合健康指数 | D32 汇总 D1-D31 |

### 2.4 🔴 红线：32D 永久锁定

- 32D 语义向量永久固定，永不扩容，永不缩维
- 维度数量是编译期常量，不可运行时修改
- 任何维度变更将强制全部已有记忆重编码——这是不可接受的
- 新增功能通过新增独立分支（DNA 支链）实现，不修改 32D 核心

---

## 第三章 · 系统总览

### 3.1 完整模块地图

以下模块地图综合了 `wenstar-cc`（太虚境现有代码 ~58,600 行 TypeScript）和 `wenstar_os`（天权/瑶灵/瑶光 Python）的全部已知模块。

```
太虚境主进程 (唯一入口)
│
├─【DNA 编码层 M1】
│   ├── DNAEncoder.ts          ← dna_root_id 生成 + L0→L3 编排
│   ├── L0Router.ts            ← 关键词规则 → locus_path + l0_code
│   ├── L1Sequencer.ts         ← 分支路由 + 序列号
│   ├── L2ContentExtractor.ts  ← 5 大语义区映射
│   ├── L3EntityAnnotator.ts   ← 60 实体规则 + FMM 分词 + LLM 增强
│   ├── GlobalSequenceCounter  ← 全局序列号（跨日重置，文件持久化）
│   ├── SemanticBoundaryDetector ← push/flush 流式边界检测
│   └── LexiconLoader.ts       ← 词库/分类法/实体规则加载
│
├─【感知决策层 M3】
│   ├── M3LogicOrchestrator.ts ← 6 阶段决策管道
│   └── PerceptionAnalyzer.ts  ← 24D 规则引擎 → 钙化评分 → 动作路由
│
├─【知识融合层 M4】
│   ├── M4Orchestrator.ts      ← 检索编排 + FG 覆写 + 重排序
│   ├── MemoryRetriever.ts     ← 4 路检索 (locus/keyword/emotion/KB)
│   ├── FamilyGraph.ts         ← 人物关系图谱 (SQLite 节点+边)
│   ├── EntityTopologyManager  ← v3.0 双向拓扑多跳检索
│   ├── Reranker.ts            ← 5 维重排序
│   └── QueryDecomposer.ts     ← 查询分解
│
├─【表达生成层 M5】
│   ├── M5Orchestrator.ts      ← 5 步生成管道
│   ├── CognitionAssembler.ts  ← 认知摘要 (纯函数, 无 LLM)
│   ├── StrategySelector.ts    ← 策略选择 (纯规则, 无 LLM)
│   ├── SceneAnchor.ts         ← 场景锚点 (位置/动作/裸露度/一致性校验)
│   ├── ContextMemory.ts       ← 跨回合适配状态 (物理/氛围/事实)
│   ├── HumanisticCalibrator   ← 后处理校准 + 思考停顿注入
│   └── DeepSeekLLMProvider    ← DeepSeek API (3 路径: 本地/角色扮演/正常)
│
├─【融合存储层 M2】
│   ├── FusionStorageAdapter   ← 统一读写入口
│   ├── SQLiteAdapter.ts       ← 底层 SQLite (WAL/NORMAL/64MB cache)
│   ├── ConversationDB.ts      ← 对话存储 (砂金)
│   ├── math.ts                ← 钙化公式 + 遗忘衰减 + 回溯增强
│   └── schema.sql/v2/v3       ← 完整 DDL (memories/entities/black_diamond...)
│
├─【工作记忆 M9】
│   └── WorkingMemory.ts       ← DNA 缓存 → 分级毕业 → M2 写入
│
├─【自我进化 M6】
│   ├── M6Orchestrator.ts      ← 大五人格 + 边界管理
│   └── SelfModelManager.ts    ← 偏好/边界/叙事
│
├─【梦境引擎 M7】
│   ├── M7Orchestrator.ts      ← 4 维梦境分析 (情绪雷达/热点/自我进化/人物审视)
│   ├── DreamInternalizer.ts   ← 梦境内化 + 疤痕冲突检测
│   ├── ConsolidationQueue.ts  ← 闲置巩固
│   └── InductionScheduler.ts  ← 每小时归纳 (LLM 反思生成)
│
├─【年轮引擎 M8】
│   ├── M8FusionAdapter.ts     ← 地标/疤痕/愈合/冲突裁决
│   └── PhysiologicalDeriver   ← 从 M3 感知推导模拟生理指标
│
├─【三库体系】
│   ├── VaultManager.ts        ← 三库 CRUD + 晋升引擎
│   ├── MemoryAssessor.ts      ← 定时晋升 (砂金→金库 30min, 金库→黑钻 2h, 衰减 24h)
│   ├── MemoryMetrics.ts       ← 运行时指标
│   └── AQCEngine.ts           ← 质检引擎 (SandQC + GoldQC)
│
├─【知识库】
│   ├── KnowledgeEngine.ts     ← 主引擎 (add/search/weightedSearch)
│   ├── RAGPipeline.ts         ← 向量+关键词+情感混合检索
│   ├── FileUploadService.ts   ← 8 类文件解析 + OCR
│   ├── TopicTracker.ts        ← 热点追踪
│   └── FusionEngine.ts        ← 三源融合 (知识+记忆+人物)
│
├─【人物图谱】
│   ├── FamilyGraph.ts         ← 节点+边模型 / 双向关系 / 10模块档案 / 圈子/权重
│   ├── EntityValidator.ts     ← 人名/关系校验
│   ├── FamilyGraphRoleBranch  ← 角色扮演身份切换
│   ├── FamilyGraphAdapter.ts  ← 结构化档案 + 视角隔离
│   ├── RelationshipExtractor  ← 10 模式中文关系抽取
│   └── MasterProfileService   ← 用户自我镜像 (主观世界+客观世界)
│
├─【心脑引擎 Engine】
│   ├── orchestrator.ts        ← EventBus 编排器 (legacy/hybrid 双模式)
│   ├── EngineContext.ts       ← 新旧管道共享状态桥
│   ├── bus/EventBus.ts        ← 优先级事件总线 + 追踪记录
│   ├── brain/                 ← L0 分类/意图路由/安全拦截/通信模式
│   ├── heart/                 ← 欲望栈/情绪衰减/关系突触/涌现/重巩固
│   ├── cortex/                ← 生成编排/输出处理/提示词合成
│   └── temporal/              ← 天时系统 (农历/月相/物候/天气/会话追踪)
│
├─【太虚图书馆】
│   └── lib/taixu-library/     ← 独立进程 :3737 / 三层存储 / 钙化晋升 / DNA 绑定
│
├─【WebUI 服务】
│   ├── server.ts              ← HTTP :3000 + M1-M9 初始化
│   ├── chat.ts                ← 72 步全链路对话管道 (2904 行)
│   └── maintenance.ts         ← 后台维护服务
│
├─【天权工程内核 (Python)】
│   ├── tianquan_rpc_server.py ← 生产模式: stdin/stdout JSON-line RPC
│   ├── mcp_harris_t.py        ← 开发模式: 独立 MCP 进程
│   ├── workflows/             ← 4 套 YAML: 代码审查/架构重构/SQL治理/知识库整理
│   ├── modules/               ← arch_parser / sql_parser / doc_generator
│   ├── validator/             ← lint_checker (8 条规则)
│   └── codec/                 ← snapshot_codec (工程快照)
│
├─【瑶灵 (Python) — 独立进程】
│   ├── channels/              ← 32 维通道处理器 (每维一个模块)
│   ├── safety/                ← threshold_registry + guard_evaluator
│   ├── codec/                 ← sensation_encoder/decoder
│   └── workflows/             ← 3 套 YAML
│
└─【瑶光 (Python) — 独立进程】
    └── (待建设: Hermes 世界模型适配)
```

### 3.2 启动流程

```
# 终端 1: 全局 TCP 总线
python global_bus_main.py                    # localhost:9100

# 终端 2: 太虚境主进程 (唯一用户入口)
node start.cjs                                # HTTP :3000
  → spawn python tianquan_rpc_server.py       # 天权内核 (stdin/stdout RPC)
  → 连接 global_bus                           # 仅用于跨域指令到瑶灵/瑶光

# 终端 3: 瑶灵 (可选外设)
python mcp_harris_l.py

# 终端 4: 瑶光 (可选外设, 待建设)
python mcp_harris_g.py
```

太虚境可单独运行——关闭瑶灵/瑶光不影响代码开发和日常对话。

---

## 第四章 · DNA 双螺旋

### 4.1 双链定义

DNA 双螺旋是全系统唯一底层编码标准。两条链地位完全对等：

**语义螺旋链 (Semantic Spiral Chain)** — 心智链 / 思维链 / 感知链
- 载体: 32D 固定稠密向量 (float32[32])
- 索引: HNSW 图索引 (网状、非线性)
- 内容: 事件本体、感官数据、情绪、逻辑、因果、认知、相对时序、记忆衰减权重
- **不含**: 日历时间、真实时间戳、顺序编号
- 检索: 自由联想 (HNSW 向量邻近匹配)、触发式回忆 (语义相似度泛化检索)

**寻址结构螺旋链 (Addressing Structure Spiral Chain)** — 岁月链 / 生命链 / 秩序链
- 载体: 四条独立子系统的复合治理总线
- 索引: B+树时序索引 (保证绝对线性时序) + 组倒排索引 + 路径戳倒排索引
- 子系统:
  1. 全局时序骨架 (GlobalTimeSeq, AbsoluteTimeStamp, TimeSliceTag)
  2. 藤蔓组拓扑 (VineGroupID, GroupBelongID, EventBranchID)
  3. 路径路由戳 (RouteStampList — 快递式逐站盖章机制)
  4. 安全校验治理 (CRC_CheckSum, HotColdLevel, StateFlag)
- **不含**: 任何感性/情绪/语义内容

### 4.2 两种时间——核心哲学

**语义时间（Semantic Time）**：32D 中的"时间感"
- 不是钟表时间。是"先后顺序"、"因果链条"、"快慢感知"。
- 在 32D 中编码为相对时序标记（"这件事发生在那件事之前"），但从不编码日历值。
- 这是人类回忆时的"时间感"——你记得某件事是在另一件事之前发生的，但不一定记得具体日期。

**宇宙时间（Cosmic Time / 寻址时间）**：寻址链中的"绝对时间"
- 真实的日历时间戳、顺序编号、时间分片标签。
- 存储在寻址链的 GlobalTimeSeq + AbsoluteTimeStamp + TimeSliceTag 中。
- 这是物理世界的时间——可以排序、可以回溯、可以按"2026 年 7 月"过滤。
- **永不进入 32D 语义向量**。这是红线 #1。

两者通过 GlobalUID 绑定——同一颗 32D 海胆同时挂在语义链（HNSW）和寻址链（B+Tree）上。纯语义联想时悬置寻址链；主动回忆时先走寻址链锁定范围，再走语义链精排。

### 4.3 双检索模式

**模式 1: 纯语义思维（默认常态）**
- 寻址链: 关闭、悬置、隔离
- 仅运行 32D HNSW 语义搜索
- 思维自由，不被时间/空间绑架
- 用途: 日常闲聊、发散思维、观点复用、自发回忆、创意推理

**模式 2: 双链回忆（主动追溯）**
- 第 1 步: 寻址链先行——按时间段/组/路径条件过滤 (B+Tree + 倒排索引)，批量筛选 GlobalUID 候选集，搜索空间从亿级降到百级
- 第 2 步: 语义链后行——在锁定子集内做 HNSW 细粒度相似度排序
- "先锁定岁月，再思考内容。先圈定疆域，再做联想。"
- 用途: 主动回忆、自传式追溯、岁月溯源、事件全貌还原

### 4.4 三座物理存储底座

三座底座完全物理隔离，仅通过 GlobalUID 关联：

1. **语义向量分片库**: 32×float32 稠密向量，32 逻辑扇区，HNSW 图索引。纯语义联想通路。
2. **寻址治理存储池**: 时序骨架 + 归属拓扑 + 路由路径 + 安全校验。三类索引: 时序 B+Tree / 组倒排 / 路径戳倒排。按自然月分片。
3. **原始数据层**: 文本、对话原文、多媒体摘要。仅做兜底溯源。不做语义索引。

---

## 第五章 · 五级记忆闸门

### 5.1 设计目标

五级闸门是 P0 最高优先级模块。它解决了所有 AI 记忆系统共有的"场景错乱"问题——在浴室说的话被当成办公室的记忆召回。

### 5.2 五级逐级判定

| 闸门 | 功能 | 判定逻辑 | 动作 |
|------|------|---------|------|
| **G1** 语义初筛 | 关键词 + 向量粗筛 | cosine 距离 | 生成候选线索池 |
| **G2** 时空一致性 | 区位指纹比对 + 分级抑制 | `location_fingerprint` 余弦距离 | PASS(≤0.3): 全量加载 · P1(0.3-0.6): 仅保留 L2/L3 摘要 · P2(0.6-0.8): 权重降至 <0.3 · P3(>0.8): 直接剔除 |
| **G3** 仿生遗忘 | 衰减曲线 | `decayed = originalWeight × exp(-λ × elapsedHours)` · λ=0.01 常态 / 0.03 环境切换 · 下限 0.05 | 长期未访问自动降权 |
| **G4** 意图区分 | 主动回忆 vs 被动闲聊 | 意图分类器 (regex 触发: 昨天/上次/回忆/记得…) | 主动: 加载完整记忆 · 被动: 只加载摘要 |
| **G5** 话题壁垒 | 语义聚类 + 切换冻结 | 话题切换触发 | 前话题记忆链冻结，防跨话题污染 |

### 5.3 闸门不可关闭

```
🔴 五级闸门是架构级硬约束，不可运行时关闭
🔴 G2 的 location_fingerprint 绑定是强制性的
🔴 所有检索必须经过五级闸门，无绕过路径
🔴 闸门参数可在配置文件中调整，但不可 disable
```

---

## 第六章 · 三库记忆体系

### 6.1 三库管道

```
每轮对话 → 砂金库 (conversations 表)
    │ 30min 检查: calcium ≥ 1.0, role='user', content ≥ 10 chars
    ▼
金库 (memories 表) ← 每日检索
    │ 2h 检查: calcium ≥ 4.5 OR recall ≥ 5
    ▼
黑钻库 (black_diamond 表) ← max 200 条, 永不衰减, 溢出淘汰最低钙化
```

### 6.2 钙化评分

钙化分是 24D 感知向量的 L2 范数除以 √24，归一化到 [0,1]:

```
calcium = ||v|| / √24
level 0 (< 0.3): 粉末 · level 1 (< 0.6): 液体
level 2 (< 0.8): 固体 · level 3 (≥ 0.8): 晶体
```

### 6.3 三级衰减 (每 24 小时)

| 记忆类型 | 钙化衰减 | 强度衰减因子 |
|---------|---------|------------|
| 强情感 (calcium ≥ 3.0) | -0.02 | ×0.995 |
| 工作相关 (叙事标签匹配) | -0.05 | ×0.985 |
| 普通中性 | -0.10 | ×0.95 |

### 6.4 回溯增强

每次检索: 钙化 +0.2 (上限 10)，强度增强: `0.05 × (1 - currentStrength)`（越弱的记忆增强越多）。

### 6.5 AQC 质检

- **SandQC**: 每小时扫描最近 30 条用户对话，评分 ≥0.2 批准，高分反馈钙化 +1.0
- **GoldQC**: 每小时扫描最近 50 条记忆，评分 ≥0.15 批准，高分强度 ×1.2
- **只读侧车**: AQC 永远不修改/阻塞数据管道，所有结果写入独立的 `aqc_records` 表

---

## 第七章 · 知识库

### 7.1 双模式定位

| 维度 | 主线（无感陪伴） | 支线（办公窗口） |
|------|---------------|----------------|
| 交互方式 | 聊天中潜移默化推送 | 一键唤起 Obsidian 风格面板 |
| 触发条件 | 36D 感知 + 区位信号自动 | 用户主动检索/编辑 |
| 数据源 | Zvec + L0-L3 | **同一套** Zvec + L0-L3 |
| 操作负担 | 零 | 主动操作 |

### 7.2 当前实现

- **嵌入引擎**: TF-IDF 256D（DeepSeek v4 无嵌入 API）
- **向量存储**: 纯内存 Float64Array + 线性扫描 + 余弦相似度（<10K 规模足够）
- **检索管道**: 关键词 LIKE → 中文分词 → 混合检索 → RAG 融合
- **未来迁移**: P2 阶段切换到 @zvec/zvec（HNSW + RaBitQ 32×内存压缩 + WAL + SIMD）

### 7.3 三源融合 (FusionEngine)

```
知识库内容 + 记忆片段 + 人物上下文 → 融合引擎
  ├── 亲密模式 (intimacy > 0.4): 人物档案+家庭规则+外貌
  ├── 低落模式 (pleasure < -0.2): 安慰/陪伴/温暖内容
  ├── 事实模式 (factual > 0.5): 知识直通, 不注入记忆
  └── 中性模式: 全部直通
→ 按可信度等级排序 → 去重 → 截断至 6000 字符
```

### 7.4 警幻仙姑批处理

- `batchGenerateSummary`: 批量 L2 摘要
- `batchAutoLink`: 批量双链补充
- `batchTagScene`: 批量区位标签绑定
- `canvasAutoBuild`: Canvas 画布自动生成
- `batchCodeComment`: 批量代码注释
- `tableConvert`: 表格结构化转换
- `vaultMigrate`: 存量文档一键迁移
- `vaultArchive`: 定时冷热归档

---

## 第八章 · 人物图谱

### 8.1 数据模型

**节点+边模型** (SQLite):
- `nodes` 表: id / type / name / aliases(JSON) / properties(完整 PersonProfile JSON) / circle_level / tags
- `edges` 表: source_id / target_id / relation / properties(权重JSON)
- **双向强制**: 每条关系边自动创建反向边 (我→妈妈=mother_of 必伴随 妈妈→我=child_of)

**10 模块 PersonDossier**: basicInfo / contact / lifeResume / imageTraits(含 20 项女性化特征) / personalityPrefs / relationMap(含交叉点/共同事件/情感评估) / familyNetwork / health / lifeMilestones / socialCapital

**圈子系统 (v2.0)**:
- 圈层 0-5: 核心(家人/伴侣)→亲密(挚友)→熟人→商务→泛泛
- 按 base_intimacy 自动分配: spouse=0.95, mother=0.90, father=0.85, friend=0.60, colleague=0.40…

### 8.2 角色扮演隔离

`FamilyGraphRoleBranch` 创建身份快照——以扮演角色为根重新计算家族树，主图谱不受影响。扮演期间的读写操作走分支、不污染真实数据。退出时自动清理。

### 8.3 "我"节点自检

启动时自动检查 `nodes WHERE name='我'`。缺失时自动重建并记录日志。所有关系边以此节点为锚点。

---

## 第九章 · 天时系统

### 9.1 时间的三层存储

| 层 | 位置 | 用途 |
|----|------|------|
| dna_root_id 内嵌时间码 | 14 位 YYYYMMDDHHmmss | 秒级可排序时间戳，嵌入每条记录 ID |
| 数据库时间列 | created_at / timestamp / last_recalled_at… | 业务查询/排序/过滤 |
| 时序上下文标签 | time_period / season / lunar_term | 仿生感知 (早/晚/春/秋/夏至/冬至) |

### 9.2 天时引擎

- **TimeKeeper**: 全局唯一的 `new Date()` 来源
- **SessionTracker**: 会话状态 (活跃/封印/情感锚点)，2h 间隙判定新会话
- **CalendarEngine**: 农历/节气/节日
- **LunarPhaseCalc**: 月相 (天文 JDE 算法)
- **NaturalCycle**: 太阳周期/季节/子季节
- **PhenologyTimeline**: 物候 (各月花卉/场景/食物)
- **TemporalPromptRenderer**: 根据时段/会话状态/季节/天气生成 LLM 可注入的提示词块

---

## 第十章 · 跨域通信

### 10.1 通信架构

```
太虚境 (内部直接调用)
  ├── 天权内核 (Python 子进程 stdin/stdout RPC)     ← 零网络延迟
  ├── Master-Harris 任务调度器                        ← TS 侧分发
  └── GlobalBus TCP Client                           ← 仅用于联系外围

GlobalBus (TCP :9100)
  ├── 太虚境 ←→ 瑶灵 (JSON-line, req_id 匹配)
  └── 太虚境 ←→ 瑶光 (JSON-line, req_id 匹配)

瑶灵 (独立进程, 只接收指令)
瑶光 (独立进程, 只接收指令)
```

### 10.2 消息频道

| 频道 | 发布方 | 订阅方 | 内容 |
|------|--------|--------|------|
| `tianquan_snapshot` | 天权 | 瑶灵 | 调控指令 (激素调整/情绪调控/周期重置/自愈加速) |
| `yaoling_state` | 瑶灵 | 天权 | 32D 主观体感快照 |
| `yaoguang_snapshot` | 瑶光 | 天权 | 环境客观参数 + 6D 情绪谱 |
| `global_alert` | 任意域 | 全部域 | 系统告警 (超阈拒绝/链路故障) |

---

## 第十一章 · 开发红线 (16 条)

| # | 红线 | 适用范围 |
|---|------|---------|
| 1 | 语义层/状态层/知识库逻辑隔离，禁止混表 | 全系统 |
| 2 | 无 dna_root_id 和 location_fingerprint 的数据拒入库 | 存储层 |
| 3 | 未经 DNA 编码的记忆数据禁止存储 | 存储层 |
| 4 | 全局唯一 DNA 编解码器，模块禁建自研解析逻辑 | 全系统 |
| 5 | DNA 主干生成后永久只读 | 编码层 |
| 6 | **五级闸门不可关闭**，底层硬强制 | 检索层 |
| 7 | L2 聚类必须叠加区位+时间，禁止纯语义聚类 | 蒸馏层 |
| 8 | **32D 向量禁止 LLM 直接输出浮点值**，必须分层规则映射 | 感知层 |
| 9 | **32D 语义向量永久锁定 32 维**，永不扩容/缩维 | 编码层 |
| 10 | 所有结构体必须经 Transcoder Protobuf 序列化 + CRC32 | 存储层 |
| 11 | 禁止 LLM 调用 BIOS 层，BIOS 层禁止调用 LLM | 调度层 |
| 12 | 单次交互生成且仅生成一颗 32D 海胆，禁止 Token 粒度 | 编码层 |
| 13 | 产品主线优先无感陪伴知识推送，Vault 窗口仅辅助支线 | 产品层 |
| 14 | 前端编辑+后台处理底层数据同源同步，禁两套存储 | 数据层 |
| 15 | 禁止 fork/修改 Zvec C++ 源码，仅薄封装 | 依赖层 |
| 16 | 内源激素(瑶灵→瑶灵内源)绝对禁止混入 32D 语义向量 | 感知闭环 |

---

## 第十二章 · 实现路线图

| 阶段 | 周期 | 内容 | 前置 |
|------|------|------|------|
| **Phase 0** (当前) | 验收驱动 | Demo M1-M9 全链路闭环调优 | — |
| **P0** | 3 周 | 五级闸门 + 区位扩展 | Phase 0 验收 |
| **P1** | 2-3 周 | L0-L3 语义蒸馏异步管线 | P0 |
| **P2** | 1-2 周 | ZVEC 知识库迁移 (@zvec/zvec) | P0 (可与 P3 并行) |
| **P3** | 2 周 | 32D 向量 + 寻址链黑匣子 | P0 (可与 P2 并行) |
| **P4** | 1 周 | Protobuf Transcoder 统一序列化层 | P3 |
| **P6** | 2-3 周 | Vault + 警幻仙姑 8 API | P2 (并行扩展) |

---

## 附录 A · 参考文档索引

| 文档 | 路径 |
|------|------|
| DNA 双螺旋编码规范 V2.0 | `DNA双螺旋完整编码规范_V2.0.md` |
| 三层对偶感知闭环 V1.0 | `三层对偶感知闭环体系V1.0.md` |
| 瑶灵域专属技术规范 | `../wenstar_os/domain_yaoling/YAOLING_DOMAIN_SPEC.md` |
| 天权域专属技术规范 | `../wenstar_os/domain_tianquan/TIANQUAN_DOMAIN_SPEC.md` |
| 三库体系与 AQC 说明书 | `../wenstar/docs/三库体系与AQC质检岗位说明书.md` |
| Zvec 适配分析 | `Zvec源码研究与天权适配分析.md` |

## 附录 B · 变更记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-07-12 | V1.0 | 大一统初版，统一 32D，明确天权内置太虚境，综合全部已有代码和文档 |
