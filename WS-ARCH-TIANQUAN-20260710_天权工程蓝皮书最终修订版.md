# WS-ARCH-TIANQUAN-20260710 天权工程蓝皮书 最终修订版

**文档编号**: WS-ARCH-TIANQUAN-20260710  
**文档状态**: ⏳ 预研草案（待前置依赖达成后正式发布）  
**前置依赖**:
1. 🔴 **Demo M1-M9 全链路闭环验收通过**（当前所处阶段）
2. 🔴 **WenStarOS DNA 遗传编码强制规范 V1.0 定稿发布**
3. 🔴 **WenVec36 向量体系实测验证无畸形转换**
4. 🟡 以上全部达成后方可进入正式架构开发

**适用团队**: Hermes 中枢开发、Claude Code 底层存储开发、推理引擎适配  
**前置阅读**: WenStar OS 天权白皮书 V1.0、WenStarOS DNA 遗传编码强制规范 V1.0  
**核心修正清单（全部落实评审意见）**:

1. ✅ 永久废弃传统切片 RAG 范式，天权为独立认知 OS
2. ✅ 删除所有 PCIe 协议栈、物理磁点、块设备直写等不切实际描述
3. ✅ 修正「二进制转码器已完成」——更名 Transcoder 序列化层，采用 Protobuf + BLOB + SQLite
4. ✅ 36 维逻辑分区改为 state_spines 复合索引逻辑表
5. ✅ ZVEC 对外名称不变，底层复用 sqlite-vec，不自研向量引擎
6. ✅ 修正 36D 向量生成逻辑，禁止 LLM 直接输出浮点，采用分层规则/瑶光输入
7. ✅ 补充 L0-L3 异步调度、算力量化说明
8. ✅ 删除所有 GPU 强依赖、Doc-RoPE、模型内注意力迁移等不可落地描述
9. ✅ 新增 DNA 遗传编码总线作为全系统唯一底层标准
10. ✅ 新增 Demo 闭环验证阶段及硬性验收门槛
11. ✅ 全局 32D→WenVec36 维度升级

---

## 目录

1. [系统工程概述](#1-系统工程概述)
2. [DNA 遗传编码总线规范（一级标准）](#2-dna-遗传编码总线规范一级标准)
3. [全局 DNA 时序 ID 规范](#3-全局-dna-时序-id-规范)
4. [WenVec36 海胆状态层存储规范](#4-wenvec36-海胆状态层存储规范)
5. [L0-L3 语义分层蒸馏工程规范](#5-l0-l3-语义分层蒸馏工程规范)
6. [ZVEC 向量知识库实现规范](#6-zvec-向量知识库实现规范)
7. [Transcoder Protobuf 序列化层设计](#7-transcoder-protobuf-序列化层设计)
8. [五级记忆召回闸门管线规范](#8-五级记忆召回闸门管线规范)
9. [双路由稀疏寻址实现规范](#9-双路由稀疏寻址实现规范)
10. [分层冷热存储架构](#10-分层冷热存储架构)
11. [记忆交织迭代推理规范](#11-记忆交织迭代推理规范)
12. [持久化存储链路统一规范](#12-持久化存储链路统一规范)
13. [双内核管控体系](#13-双内核管控体系)
14. [旧 24D Demo 平滑迁移方案（含 WenVec36 转换）](#14-旧-24d-demo-平滑迁移方案含-wenvec36-转换)
15. [Demo 闭环调优阶段细则](#15-demo-闭环调优阶段细则)
16. [分阶段开发任务看板](#16-分阶段开发任务看板)
17. [全局强制开发约束红线](#17-全局强制开发约束红线)
18. [附录](#18-附录)

---

## 1 系统工程概述

### 1.1 天权在三体架构中的位置

天权不是 Hermes，天权是统摄瑶灵、瑶光、太虚境三体的完整认知操作系统。三层分工：

| 层级 | 名称 | 技术栈 | 说明 |
|------|------|--------|------|
| 第三层 | 认知推演层 | TypeScript + 规则引擎 + LLM | 36D（WenVec36）海胆认知、五大驱力、人格演化、D36 统筹 |
| 第二层 | 记忆检索层 | TypeScript + SQLite + sqlite-vec | 双路由寻址、L0-L3 蒸馏、ZVEC 知识库、五级闸门 |
| 第一层 | 数据持久层 | TypeScript + DNA 编解码 + Protobuf + SQLite WAL | 双路采集、DNA 总线编码、Transcoder 序列化、state_spines 表 |

### 1.2 M1-M9 模块映射（后续版本规划）

| 模块 | 功能 | 说明 |
|------|------|------|
| **M1** DNAEncoder | dna_root_id 主主干生成 + 功能分支挂载 | 唯一 DNA 编解码入口，全局锁定 |
| **M2** 存储层 | state_spines 表、语义分层分区、ZVEC 向量索引 | 对齐 DNA 总线标准后重构 |
| **M3** PerceptionAnalyzer | 24D→WenVec36 分层量化映射 | 维度扩展 + DNA 感知分支编码 |
| **M4** M4Orchestrator | 并行记忆+ZVEC 检索 + FiveStageGate | 新增五级闸门管线 |
| **M5** LLM 生成管线 | 接收过滤后的 L2/L3 摘要 | 小幅适配 |
| **M7** 梦境引擎 | 离线记忆归纳巩固 | 复用，增量改造 |
| **M8** 年轮引擎 | 长期线索/疤痕 | 复用 |
| **M9** 工作记忆 | 短期交互缓存 | 复用 |

### 1.3 MSA 定位说明（重要·不可混淆）

天权不移植 MSA 代码、不嫁接模型内部组件、不引入 GPU 强依赖。仅借鉴三个工程思想：

| MSA 思想 | 天权落地方式 | 技术栈 |
|---------|------------|--------|
| ① 双路由稀疏寻址 | 路由 A（36D 特征索引粗筛）+ 路由 B（语义精筛） | SQLite 索引 + HNSW |
| ② 分层存储 | 内存层（路由索引键）+ 磁盘层（KV 结构体） | Node.js Buffer + SQLite |
| ③ 迭代推理 | 检索→扩写→再检索 循环回路 | TypeScript 管线 |

### 1.4 当前所处阶段

> **⚠️ 当前所有架构文档为「预研草案」状态。**
>
> 唯一前置任务：**Demo M1-M9 全链路闭环调优**，达成验收标准后，依次产出 DNA 强制规范 → 评审定稿 → 全域统一落地。
>
> P0 等前置开发仅做**业务逻辑骨架预留**，不接入任何 DNA 编解码、ID 关联逻辑。

---

## 2 DNA 遗传编码总线规范（一级标准）

### 2.1 概述与定位

DNA 遗传编码是天权全系统的**唯一底层标准**，不是 M1 的一个模块，而是串联全系统的基因总线。

**覆盖范围**（全链路强制统一）：

```
M1 DNA 主主干生成 → WenVec36 感知维度编码
→ 三金库分级标注 → 实体关系图谱编码
→ ZVEC 知识库条目绑定 → WenCodec 磁盘寻址
→ 前后端 HTTP 传输 → 跨进程插件（TTS/图像/梦境）
→ 存量历史记忆 → 批量迁移工具
```

### 2.2 核心不可突破铁律

| # | 铁律 | 说明 |
|---|------|------|
| 1 | DNA 主链生成后**永久只读** | 编码阶段直接拦截主干字段修改操作 |
| 2 | 分支编码规则**锁定** | 仅允许末尾追加字段、新增独立分支；禁止调换/删除原有字段 |
| 3 | **全局唯一编解码器** | 禁止各模块自建解析逻辑，违者架构级故障 |
| 4 | 主干/分支/分隔符/编解码**任一处改动** | 都会造成基因解读错位，产出错乱情绪、时空、人物记忆 |
| 5 | **新旧版本全量向下兼容** | 新版解码器必须无损解析历史任意版本 DNA，无特征丢失 |

### 2.3 DNA 结构总览

```
DNA 结构：
┌────────────────────────────────────────────────────────┐
│                DNA 主遗传主干（只读）                    │
│  dna_root_id | 版本标记 | 时空基准确认 | ext{}         │
└────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────┐
│               ext：五大标准功能分支                      │
│                                                        │
│  分支1：时空分支（时序戳 + D27/D28 区位指纹）           │
│  分支2：实体关系分支（家族图谱圈层 + 依恋/守护权重）    │
│  分支3：WenVec36 感知分支（36 维向量分段编码）          │
│  分支4：记忆生命周期分支（砂金/金库/黑钻 + 钙化分）    │
│  分支5：WenCodec 磁盘寻址分支（分区号 + 冷热扇区）     │
│                                                        │
│  [预留] 分支6-N：二期多模态拓展                         │
└────────────────────────────────────────────────────────┘
```

### 2.4 五大标准功能分支

#### 分支1：时空分支基因

编码内容：时序戳、D27/D28 区位指纹量化编码、值域、哈希映射规则。  
用途：五级闸门 2 时空一致性校验的底层数据来源。

#### 分支2：实体关系分支基因

编码内容：家族图谱圈层、依恋/守护权重、关系编码映射。  
用途：M8 家族图谱、角色扮演、圈层人际推演。

#### 分支3：WenVec36 感知分支基因

编码内容：36 维仿生向量分段、强度分级、定点二进制映射。  
用途：36D 海胆状态存储与检索的核心载体。

#### 分支4：仿生记忆生命周期分支

编码内容：砂金/金库/黑钻分级、钙化分、遗忘衰减系数、晋升标记。  
用途：三金库晋升/衰减/质检全流程。

#### 分支5：WenCodec 磁盘寻址分支

编码内容：分区编号、冷热扇区、逻辑 LBA 地址。  
用途：磁盘持久化定位、冷热分层迁移。

### 2.5 全局唯一编解码器

#### 四大固定全局接口（不可新增自定义解析函数）

```typescript
// ===== WenStarOS 唯一 DNA 编解码器 =====

// 完整编码：输入原始数据 → 输出完整 DNA（主干 + 全部分支）
DNA.encode(rawInput, m1BaseData, branchExts): FullDNA

// 全量解析：完整解析主干 + 所有分支
DNA.decode(dnaBinary | dnaJson): ParsedDNA

// 轻量化分支读取：只读指定分支，不解析全部
DNA.decodeBranch(dna, branchName): BranchData

// 合规校验：写入/传输前强制调用，不合规阻断
DNA.validate(dna): Boolean
```

#### 编码固定流程

```
Step 1: M1 生成只读不可修改主主干
Step 2: 各车间（感知/图谱/金库/存储）依次挂载对应功能分支至 ext
Step 3: 持久化/传输前执行 validate 校验，不合规直接阻断
Step 4: 统一二进制压缩、分段序列化
```

#### 解码固定流程

```
Step 1: 优先校验主干完整性 → 损坏则抛出 FATAL 异常
Step 2: 按标准分隔符自动拆分各功能分支
Step 3: 读取分支内置版本号 → 匹配对应解析逻辑
Step 4: 旧版本缺失字段自动填充官方默认值
```

#### 异常拦截分级规则

| 等级 | 场景 | 处理 |
|------|------|------|
| **FATAL** | 主干缺失/篡改 | 阻断记忆入库、阻断 LLM 认知组装生成 |
| **ERROR** | 分支编码错位 | 告警日志留存，丢弃错误特征不参与推演 |
| **WARN** | 版本不匹配 | 自动降级兼容解析，记录兼容告警日志 |

### 2.6 全链路传输统一强制标准

| 节点 | 标准 |
|------|------|
| 内部 M1-M9、金库、图谱模块 | 必须传递完整 DNA 结构体，禁止仅截取局部 ID |
| WebUI/HTTP 对外接口 | 固定 DNA 标准 JSON/二进制二选一传输格式 |
| SQLite 磁盘持久层 | 所有核心数据表强制设立完整 DNA 存储字段 |
| 跨进程插件（TTS/梦境/图像） | 完整基因包随参数传递，不可只传短 ID |

### 2.7 版本迭代红线

| 操作 | 状态 |
|------|------|
| 新增完整独立功能分支 | ✅ 允许 |
| 已有分支末尾追加字段 | ✅ 允许 |
| 新增分支版本号、扩展解码器兼容逻辑 | ✅ 允许 |
| 调换主干/分支字段顺序 | ❌ **禁止** |
| 删除、修改历史字段含义/编码长度 | ❌ **禁止** |
| 改动分隔符、dna_root_id 生成算法 | ❌ **禁止** |
| 各模块自建独立编解码逻辑绕过全局工具 | ❌ **禁止（架构级故障）** |

### 2.8 规范发布后全域统一管控

| 手段 | 说明 |
|------|------|
| 代码层锁死 | 全局唯一 DNA 工具类，封装 encode/decode/validate，拦截自定义解析 |
| 全链路标准化 | 内部函数、HTTP 接口、数据库表、离线文件统一完整 DNA 载体 |
| 自动化巡检 | 定时批量扫描存量 DNA，输出畸形数据清单 |
| 架构评审硬性基准 | 任何改动先核对本规范，不合规直接驳回 |
| 永久归档只读 | V1.0 发布后主干核心条款永不修改，新增功能仅发布补充附录 |

---

## 3 全局 DNA 时序 ID 规范

### 3.1 ID 体系定义

| 字段 | 类型 | 职责 | 生成规则 |
|------|------|------|---------|
| `dna_root_id` | string(64) | 全局唯一交互主键 | 毫秒时间戳(13) + 节点编号(4) + 批次号(8) + 区位标识(8) + 随机盐(6) |
| `location_fingerprint` | Buffer(16) | D27/D28 合成的二进制区位指纹 | 瑶光直接传入，128bit |
| `seq_idx` | integer | Token 段内递增下标 | 从 0 递增，仅用于文本还原 |

### 3.2 全链路透传约束

- `dna_root_id` 必须穿透：语义 Token → state_spines 各维度 → ZVEC 条目 → L0-L3 全部层级
- 无 `dna_root_id`、无 `location_fingerprint` 的数据**拒绝持久化**（DNA 编解码层拒绝编码）
- 全链路溯源能力：从 L3 人格画像可反向追溯到 L1 原子事实、L0 原始对话、对应的 36D 状态向量

---

## 4 WenVec36 海胆状态层存储规范

### 4.1 state_spines 建表 SQL

```sql
-- state_spines：36D 海胆硬刺存储表
-- 复合主键 (dna_id, dimension_id) 模拟 36 组逻辑分区

CREATE TABLE IF NOT EXISTS state_spines (
    dna_id TEXT NOT NULL,
    dimension_id INTEGER NOT NULL CHECK(dimension_id BETWEEN 1 AND 36),
    value REAL NOT NULL,
    consistency_mark TEXT NOT NULL DEFAULT 'consistent',
    location_fingerprint BLOB,
    timestamp_ms INTEGER NOT NULL,
    checksum TEXT,
    dna_branch BLOB,                -- WenVec36 感知分支编码（挂载 DNA ext）
    PRIMARY KEY (dna_id, dimension_id)
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS idx_spines_dim_time
ON state_spines(dimension_id, timestamp_ms);

CREATE INDEX IF NOT EXISTS idx_spines_location
ON state_spines(location_fingerprint, dimension_id)
WHERE location_fingerprint IS NOT NULL;
```

### 4.2 维度生成规则

| 维度范围 | 数据来源 | 生成方式 | 仲裁优先 |
|---------|---------|---------|---------|
| D1-D10（肉身实体） | 瑶灵主观 + 规则分类器 | 情感分类器 + 规则映射 | 80:20 |
| D11-D16（内在精神） | LLM 文本语义 + 数值模板 | LLM→代码层映射至模板 | 70:30 |
| D17-D22（圈层人际） | LLM 文本语义 + 数值模板 | LLM→代码层映射至模板 | 60:40 |
| D23-D28（时空环境） | 瑶光直接输出 | 环境传感器/UI 传入 | 20:80 |
| D29-D36（生长解锁） | D36 汇总统筹 | 统筹规则计算 | 由 D36 裁决 |

### 4.3 一致性标记定义

```typescript
type ConsistencyMark =
  | 'consistent'     // 双路一致，正常融合
  | 'biased_subj'    // 主观偏差大，已按规则仲裁
  | 'biased_obj'     // 客观偏差大，已按规则仲裁
  | 'inherited'      // 输入异常，继承上一轮
  | 'overridden';    // D36 统筹强制覆盖
```

---

## 5 L0-L3 语义分层蒸馏工程规范

### 5.1 四层定义与存储

| 层级 | 内容 | 存储位置 | 生成时机 | 加载策略 |
|------|------|---------|---------|---------|
| **L0** | 原始 Token 序列 | `semantic_tokens` 表 | 交互时同步 | 仅完整复盘 |
| **L1** | 原子事实 | `semantic_facts` 表 | **会话结束后异步** | 主动查询 |
| **L2** | 场景摘要 | `semantic_summaries` 表 | **批量定时** | 日常闲聊首选 |
| **L3** | 人格/知识画像 | `semantic_profiles` 表 | **每日 Cron** | 日常闲聊首选 |

### 5.2 L2 聚类三重条件（核心约束）

```typescript
interface L2ClusterCondition {
  semantic_similarity: number;  // ≥ 0.65
  location_distance: number;    // ≤ 0.3（区位指纹差异）
  time_interval: number;        // ≤ 3600s（一小时内的对话）
}
```

### 5.3 算力量化说明

| 层级 | 触发频率 | 单次 Token 消耗 | 日均预估 |
|------|---------|----------------|---------|
| L1 提取 | 每会话结束后 | ~200-500 tokens | ~2000-5000 |
| L2 聚类 | 每 5-10 轮 | ~500-1000 tokens | ~2000-5000 |
| L3 画像 | 每日 1 次 | ~1000-2000 tokens | ~1000-2000 |
| **合计** | — | — | **~5000-12000 tokens/天** |

---

## 6 ZVEC 向量知识库实现规范

### 6.1 架构定位

- **对外统一名称**: ZVEC 向量知识库（架构抽象层）
- **底层实现**: 阿里巴巴开源 in-process 嵌入式 Zvec 向量引擎（`@zvec/zvec` N-API 原生绑定）
- **上层封装**: `ZvecEngine` 抽象层（TypeScript），统一 CRUD/检索接口，与原 sqlite-vec 封装完全对齐
- **不引入**: 任何独立向量库服务（Chroma/Milvus/Pinecone 等），Zvec 为嵌入式库零服务依赖
- **不 fork、不修改 Zvec C++ 源码**，仅 TS 薄封装隔离，阿里持续维护上游
- **淘汰**: 旧 Demo 的 `KnowledgeEngine` TF-IDF 检索逻辑
- **过渡说明**: Demo 调优期继续使用 sqlite-vec，P2 阶段统一切换为 @zvec/zvec，ZvecEngine 抽象接口不变，上层业务无感
- **DNA 绑定**: 每条 ZVEC 条目必须挂载 DNA 编码，支持全链路溯源

### 6.2 核心收益（vs sqlite-vec）

| 能力 | sqlite-vec | @zvec/zvec |
|------|-----------|------------|
| 索引类型 | 仅 IVF | HNSW / IVF / FLAT / Vamana / RaBitQ |
| 标量过滤 | 无，需上层代码二次处理 | **原生 SQL 式 filter**，时空/区位下沉至检索层 |
| WAL 崩溃恢复 | 无 | ✅ 生产级 WAL |
| SIMD 加速 | 无 | ✅ SSE/AVX2/AVX512/NEON 全系列 |
| 混合检索 | 多轮拼接 | **dense + sparse + filter 单次查询** |
| 冷热管理 | 无 | **原生 Segment 分段**（Writable→Persisted→Compaction） |
| 亿级容量 | 不支持 | 单机支持 |

### 6.3 检索流程改造

五级闸门 2 的时空一致性校验下沉至 Zvec 原生 filter：

```typescript
// ZvecEngine.search() — 单次查询完成多层过滤
const results = await zvecCollection.query({
  vectors: [
    { fieldName: "wenvec36_embedding", vector: queryVec },  // 语义检索
    { fieldName: "sparse_keywords", sparseVector: sparseVec }, // 关键词匹配
  ],
  filter: "location_fingerprint == ? AND timestamp BETWEEN ? AND ?",  // 时空约束下沉
  topk: 100,
  reranker: { type: "RRF" },
});
// 不再需要上层多轮拼接 + 二次过滤
```

### 6.4 存储分层规范更新

依托 Zvec 原生 Segment 机制实现记忆冷热分区，替代自研冷热管理逻辑：

| 层级 | Zvec 对应机制 | 说明 |
|------|-------------|------|
| 热（近期频繁访问） | WritableSegment（内存 + WAL） | 当前写入段，响应快 |
| 温（LRU 缓存） | 上层 LRU 内存缓存 | 减少重复解码开销 |
| 冷（历史归档） | PersistedSegment（磁盘列式存储） | 自动 Compaction 合并 |

### 6.5 检索与记忆统一流程

```
用户输入
  ↓
M4Orchestrator.composeContext()
  ├── MemoryRetriever.retrieve()        ← 36D 时序记忆检索
  ├── ZvecEngine.search(query)          ← ZVEC 知识库检索（并行）
  │
  └── FiveStageGate.filter(candidates)  ← 两路结果统一过滤
       ↓
  Reranker.rerank(filtered)
       ↓
  ContextAssembler.assemble()           ← L0-L3 分层组装
```

---

## 7 Transcoder Protobuf 序列化层设计

### 7.1 三套 Proto 定义

```protobuf
// spine.proto — 36D 状态硬刺
syntax = "proto3";
message StateSpine {
  string dna_id = 1;
  int32 dimension_id = 2;
  int64 timestamp_ms = 3;
  bytes location_fingerprint = 4;
  float value = 5;
  string consistency_mark = 6;
  string checksum = 7;
  bytes dna_branch = 8;   // WenVec36 感知分支编码
}
```

```protobuf
// token.proto — 语义 Token
syntax = "proto3";
message SemanticToken {
  string dna_id = 1;
  int32 seq_idx = 2;
  bytes semantic_vector = 3;
  bytes context_offset = 4;
  string dna_branch_ref = 5;  // 关联的 DNA 分支引用
}
```

```protobuf
// zvec_entry.proto — ZVEC 知识库条目
syntax = "proto3";
message ZvecEntry {
  string resource_id = 1;
  bytes scene_label = 2;
  string source = 3;
  string l0_raw = 4;
  string l1_facts = 5;
  string l2_summary = 6;
  string l3_profile = 7;
  bytes high_dim_embedding = 8;
  string checksum = 9;
  string dna_id = 10;       // 绑定 DNA 主干
}
```

### 7.2 Transcoder.ts 基础封装

```typescript
// src/transcoder/Transcoder.ts
import { StateSpine, SemanticToken, ZvecEntry } from './proto';
import crc32 from 'crc-32';

export class Transcoder {
  encodeSpine(obj: StateSpine): Buffer {
    return Buffer.from(StateSpine.encode(obj).finish());
  }
  encodeToken(obj: SemanticToken): Buffer {
    return Buffer.from(SemanticToken.encode(obj).finish());
  }
  encodeZvec(obj: ZvecEntry): Buffer {
    return Buffer.from(ZvecEntry.encode(obj).finish());
  }

  decodeSpine(buf: Buffer): StateSpine {
    return StateSpine.decode(new Uint8Array(buf));
  }
  decodeToken(buf: Buffer): SemanticToken {
    return SemanticToken.decode(new Uint8Array(buf));
  }
  decodeZvec(buf: Buffer): ZvecEntry {
    return ZvecEntry.decode(new Uint8Array(buf));
  }

  computeChecksum(buf: Buffer): string {
    return crc32.str(buf.toString('binary')).toString(16);
  }
  verifyChecksum(buf: Buffer, target: string): boolean {
    return this.computeChecksum(buf) === target;
  }
}
```

---

## 8 五级记忆召回闸门管线规范

### 8.1 管线执行顺序（P0 核心模块）

```typescript
// src/m4/FiveStageGate.ts
export class FiveStageGate {
  async filter(input: GateInput): Promise<GateOutput> {
    let candidates = this.gate1_semanticFilter(input);
    candidates = await this.gate2_spatioTemporalCheck(candidates, input.currentLocation);
    candidates = this.gate3_forgettingDecay(candidates);
    candidates = this.gate4_intentFilter(candidates, input.queryIntent);
    candidates = this.gate5_topicBarrier(candidates, input.currentTopic);
    return candidates;
  }
}
```

### 8.2 闸门 2：时空一致性校验

| 等级 | 判定（区位偏差） | 处理策略 |
|------|----------------|---------|
| PASS | ≤ 0.3 | 完整加载 |
| P1 | 0.3 - 0.6 | 仅保留 L2/L3 摘要，屏蔽原始场景叙事；知识库仅摘录事实 |
| P2 | 0.6 - 0.8 | 降低全局权重至 <0.3，退出主推理队列 |
| P3 | > 0.8 | 直接剔除，禁止进入本轮上下文 |

### 8.3 闸门 3：仿生遗忘衰减

```typescript
function computeDecayedWeight(
  originalWeight: number,
  elapsedHours: number,
  environmentChanged: boolean
): number {
  let lambda = 0.01;
  if (environmentChanged) lambda *= 3;
  const decayed = originalWeight * Math.exp(-lambda * elapsedHours);
  return Math.max(decayed, 0.05);
}
```

### 8.4 闸门 4：意图区分

```typescript
function gate4_intentFilter(candidates: CandidateSet, intent: Intent): CandidateSet {
  if (intent === 'active_recall') return candidates;  // 全量加载

  // 被动闲聊：仅 L2/L3 摘要
  return {
    ...candidates,
    allowedMemory: candidates.allowedMemory.filter(m => m.level === 'L2' || m.level === 'L3'),
    allowedKnowledge: candidates.allowedKnowledge
      .filter(k => k.level === 'L2' || k.level === 'L3')
      .map(k => ({ ...k, text: k.summaryOnly })),
  };
}
```

---

## 9 双路由稀疏寻址实现规范

| 路由 | 输入 | 索引方式 | 作用 |
|------|------|---------|------|
| **路由 A**（记忆库侧粗筛） | 36D 多维特征向量 | HNSW/IVF 多维度联合索引 | 快速定位候选记忆分片 |
| **路由 B**（用户查询精筛） | 用户文本语义 | sqlite-vec 余弦相似度 | 精细匹配查询意图，Top-K 激活 |

### 检索复杂度保证

```
全量扫描:    O(N)           ← 旧 Demo 方案
B-tree 索引: O(log N)       ← 当前 SQLite 方案
双路由:      O(L) 线性级    ← 天权目标，L = Top-K 块大小
```

---

## 10 分层冷热存储架构

| 层级 | 存储内容 | 介质 | 容量 | 延迟 |
|------|---------|------|------|------|
| **L1 热** | 36D 路由索引键 + DNA 目录 | 内存 (RAM) | MB 级 | 纳秒 |
| **L2 温** | 近 N 轮完整记忆结构体 | 内存缓存 (LRU) | 可配置 | 微秒 |
| **L3 冷** | 全部历史记忆 KV + DNA | SQLite + NVMe | 亿级 | 毫秒 |

**去 GPU 强依赖**：路由索引键存入普通内存（MB 级），内容 KV 存入 SQLite WAL + NVMe，中间缓存层使用 LRU 策略。全平台可运行（PC/笔记本/ARM/服务器）。

---

## 11 记忆交织迭代推理规范

```
第 1 轮: 检索 → 基础上下文 → LLM 初判
                ↓（置信度不足）
第 2 轮: 扩写检索条件 → 二次检索 → 补充上下文
                ↓（仍需深挖）
第 N 轮: 继续迭代，直到置信度达标或达到最大轮次（默认 3 轮）
```

---

## 12 持久化存储链路统一规范

### 12.1 标准链路

```
Hermes 业务层 → DNA 编解码器 → Transcoder 序列化层 → SQLite（WAL）→ OS 文件系统 → NVMe SSD
```

### 12.2 链路约束

- ❌ 禁止应用层直写硬件/绕过操作系统
- ❌ 禁止自定义块设备寻址
- ❌ 禁止二进制帧直发协议栈
- ❌ 禁止 GPU VRAM 作为主要存储层级
- ✅ 所有数据经 DNA 编解码后 → Transcoder 序列化 → SQLite WAL 持久化

### 12.3 SQLite 配置

```typescript
const DB_CONFIG = {
  journal_mode: 'WAL',
  synchronous: 'NORMAL',
  cache_size: -64000,      // 64MB
  foreign_keys: 'ON',
  temp_store: 'MEMORY',
  mmap_size: 268435456,    // 256MB
};
```

---

## 13 双内核管控体系

| 特性 | 内核1：底层躯体 BIOS | 内核2：上层心灵推演 |
|------|-------------------|-----------------|
| 运行频率 | 实时响应，每轮交互触发 | 每轮对话触发 |
| LLM 依赖 | **不依赖**（纯规则） | **依赖** |
| 职责 | 36D 双路采集校验、融合仲裁、稳态维持 | 检索、五级闸门、趋力权衡、人格演化 |

---

## 14 旧 24D Demo 平滑迁移方案（含 WenVec36 转换）

### 14.1 迁移流程

```
旧 24D SQLite 数据库
  ↓
第 1 步：读取 fusion_memory 表全部记录
  ↓
第 2 步：24D → WenVec36 维度映射
  旧 D1-D24 → 新 D1-D24（直接映射）
  新 D25-D36 → 补预设默认值（待实测验证无基因畸形）
  ↓
第 3 步：生成 DNA 主干 + 初始化功能分支
  ↓
第 4 步：经 DNA 编解码器编码 → Transcoder 序列化 → 写入新表
  ↓
第 5 步：验证迁移完整性（DNA decode 无异常 + CRC 校验 + 条数匹配）
  ↓
第 6 步：24D ↔ WenVec36 双向转换抽样验证（验收硬性门槛）
```

### 14.2 迁移验收硬性指标

- 24D ↔ WenVec36 双向转换**无失真**，向量数值、记忆权重、钙化等级不丢失
- 多分支 DNA 拆分、拼接、解码**无错位**、字段混淆
- 不存在基因解析畸形引发的场景错乱、人格偏移、知识库匹配错误

---

## 15 Demo 闭环调优阶段细则

### 15.1 当前阶段说明

> **当前唯一前置任务：持续迭代、完整调优现有 Demo**

所有架构文档目前为「预研草案」状态，以下章节（§15.2-§15.4）为当前阶段的工作指南。

### 15.2 当前任务

- [ ] 完成 M1-M9 全链路闭环实验；修复全部数据流、存储、寻址、角色逻辑 bug
- [ ] 完整验证 DNA 主主干 + 多分支基因整套解析、编解码读写兼容性
- [ ] 实测 24D 存量向量平滑迁移至 WenVec36 完整流程，无基因解读畸形、记忆错乱
- [ ] 沉淀全链路踩坑参数、边界异常、兼容处理实测数据，作为 DNA 规范附录原始依据

### 15.3 Demo 验收硬性门槛

1. **全主线、多分支交互无报错**，复现人物/感知/金库/寻址全部逻辑
2. **新旧 24D ↔ WenVec36 双向转换无失真**，向量数值、记忆权重、钙化等级不丢失
3. **多分支 DNA 拆分、拼接、解码无错位**、字段混淆
4. **不存在基因解析畸形引发的场景错乱**、人格偏移、知识库匹配错误

### 15.4 规范编写与落地顺序

```
Demo 调优 → Demo 验收 → 撰写正式 DNA 规范 V1.0 → 规范评审定稿 → 全域统一落地
   ↑               ↑              ↑                      ↑                ↑
当前所处位置    硬性指标         基于实测数据            全员无异议       代码锁死+巡检
```

---

## 16 分阶段开发任务看板

### 当前阶段：Demo 全链路闭环调优

| # | 任务 | 交付物 | 状态 |
|---|------|-------|------|
| 1 | M1-M9 全链路无报错闭环 | 测试报告 | ⏳ |
| 2 | 24D ↔ WenVec36 双向转换验证 | 迁移验证报告 | ⏳ |
| 3 | DNA 主干+多分支编解码兼容性 | 兼容性测试报告 | ⏳ |
| 4 | 沉淀踩坑参数+边界异常数据 | 附录原始素材 | ⏳ |
| 5 | **Demo 验收** | 验收签字 | ❌ 门槛 |

### DNA 规范阶段（Demo 验收后）

| # | 任务 | 交付物 |
|---|------|-------|
| 1 | 撰写 DNA 遗传编码强制规范 V1.0 全文 | 规范文档 |
| 2 | 全员评审 | 评审记录 |
| 3 | 定稿发布、永久归档只读 | 归档锁定 |

### P0：核心痛点修复

| # | 任务 | 说明 |
|---|------|------|
| 1 | M1 扩展 `location_fingerprint` 区位字段 | 仅骨架预留 |
| 2 | 新建 `FiveStageGate` 五级闸门调度类 | 独立开发，隔离 DNA |
| 3 | 闸门 2-5 实现 | 逐级开发 |
| 4 | 接入 M4Orchestrator 管线 | 骨架联调 |

### P1-P5

> 待前置阶段全部完成后方可正式排期。

---

## 17 全局强制开发约束红线

| # | 红线内容 | 检测方式 |
|---|---------|---------|
| 1 | 语义层、36D 状态层、ZVEC 知识库**逻辑隔离**，禁止混表 | Schema 审核 |
| 2 | 无 `dna_root_id`、无 `location_fingerprint` 的数据**拒绝持久化** | DNA 编解码层拒绝编码 |
| 3 | 无 DNA 编码的记忆数据**禁止入库** | 写入前校验 |
| 4 | **全局唯一 DNA 编解码器**，各模块禁止自建解析逻辑 | 代码审查 |
| 5 | DNA 主干生成后**永久只读**，禁止运行时修改 | 编码阶段拦截 |
| 6 | **五级时空抑制闸门不可关闭**，底层强制逻辑 | 硬编码 |
| 7 | L2 聚类**禁止**仅用语义相似度，必须叠加区位+时间 | 聚类条件检测 |
| 8 | 36D 向量**禁止** LLM 直接输出浮点数值 | 写入前校验 |
| 9 | ZVEC 底层统一 **sqlite-vec**，禁止复用旧 TF-IDF | CI 检测 |
| 10 | 所有结构体必须经 **Transcoder Protobuf 序列化**为 BLOB | 代码审查 |
| 11 | **取消底层硬件直写**，所有存储经过 SQLite → OS 文件系统 | 方案评审 |
| 12 | **单轮交互仅生成一颗 WenVec36 海胆**，禁止单 Token 粒度 | 写入校验 |
| 13 | **禁止 fork、修改阿里 Zvec 底层 C++ 源码**，仅允许上层 TS 封装适配 | 架构方案评审 |
| 14 | **双内核职责分离**：BIOS 不调用 LLM，心灵层调用 | 耦合检测 |
| 15 | **产品主线优先保障无感陪伴知识推送**，Vault 可视化窗口仅作为可选辅助支线，**不可设为默认首页** | 产品交互评审 |
| 16 | **前端 Vault 手动编辑 + 后台自动处理 两套逻辑底层数据必须同源同步**，禁止独立两套文件/向量存储 | 数据架构评审 |

---

## 19 ZVEC 瑶灵图书馆工程实现规范

### 19.1 双模式架构隔离但数据同源

- **自动推送管线（M4 内置，无前端强依赖）**：无 UI 面板，对话流程自动调用 Zvec 检索
- **可视化 Vault 前端模块（可选唤起独立窗口）**：轻量化复刻 Obsidian 交互组件，仅作为上层操作入口
- **底层统一**：Vault 文件目录、Zvec 多 Collection、L0-L3 分层表、双链元数据表完全共用，双向写操作实时同步

### 19.2 Vault 前端面板开发标准

**必须实现的组件**：

| 组件 | 功能 | 对标 Obsidian |
|------|------|-------------|
| `FileTreePanel` | 树形文件浏览器 | 左侧边栏 |
| `TabEditor` | 多 Tab MD 编辑器 | 主编辑区 |
| `WikiLink` | `[[link]]` 双链解析 + 图谱可视化组件 | 核心功能 |
| `GraphView` | 知识图谱可视化面板 | 关系图谱 |
| `DataviewPanel` | 标签/时间筛选查询组件 | 数据检索 |
| `CanvasBoard` | Canvas 拖拽画布 | 无限画布 |
| `Preview` | 多模态预览（表格/代码/图片/音视频） | 预览面板 |

**限制约束**：
- 不做重度第三方插件生态
- 仅内置原生办公自动化基础功能
- 复杂批量操作统一交由警幻后台接口执行

### 19.3 双向数据同步硬性规则

| # | 规则 | 触发时机 |
|---|------|---------|
| 1 | 前端 Vault 窗口手动新增/修改 MD、双链、标签 → `实时写入` Zvec 元数据表 → `触发向量增量更新` | onSave |
| 2 | 后台自动生成双链、L1/L2 摘要、区位标签 → `同步渲染`至 Vault 前端图谱、文件标签面板 | onComplete |
| 3 | 关闭窗口后 `自动保存` 所有改动，**无数据割裂、无两套知识库冲突** | onClose |

### 19.4 异步管线适配双模式

文件上传分两条异步分支：
- **轻量即时分支**：供 Vault 窗口实时预览
- **完整后台分支**：执行分层蒸馏、向量化、区位绑定、自动双链生成，同步服务对话推送管线

---

## 20 警幻仙姑运维模块（新增办公批量接口）

### 20.1 原有接口保留

```typescript
interface JingHuanCore {
  healthCheck(): HealthReport;
  autoRepair(): RepairResult;
  isolateAnomaly(globalUID: string): void;
  systemGuide(query: string): string;
}
```

### 20.2 新增批量办公 API

```typescript
interface JingHuanBatchOffice {
  batchGenerateSummary(fileIds: string[]): Promise<SummaryResult[]>;     // 批量 L2 摘要
  batchAutoLink(fileIds: string[]): Promise<LinkResult[]>;              // 批量双链补充
  batchTagScene(fileIds: string[]): Promise<TagResult[]>;               // 批量区位标签
  canvasAutoBuild(rootDir: string): Promise<CanvasNodes>;               // 自动生成画布
  batchCodeComment(fileIds: string[]): Promise<CommentResult[]>;        // 批量代码注释
  tableConvert(fileIds: string[]): Promise<ConvertResult[]>;            // 表格结构化转换
  vaultMigrate(sourceDir: string, targetDir: string): Promise<MigrateResult>; // 存量迁移
  vaultArchive(before: number): Promise<ArchiveResult>;                 // 定时冷热归档
}
```

---

## 18 附录

### A. 建表 SQL 汇总

```sql
-- ==== 36D 状态硬刺表 ====
CREATE TABLE IF NOT EXISTS state_spines (
    dna_id TEXT NOT NULL,
    dimension_id INTEGER NOT NULL CHECK(dimension_id BETWEEN 1 AND 36),
    value REAL NOT NULL,
    consistency_mark TEXT NOT NULL DEFAULT 'consistent',
    location_fingerprint BLOB,
    timestamp_ms INTEGER NOT NULL,
    checksum TEXT,
    dna_branch BLOB,
    PRIMARY KEY (dna_id, dimension_id)
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS idx_spines_dim_time
ON state_spines(dimension_id, timestamp_ms);

-- ==== 语义 Token 表（L0）====
CREATE TABLE IF NOT EXISTS semantic_tokens (
    dna_id TEXT NOT NULL,
    seq_idx INTEGER NOT NULL,
    token_text TEXT NOT NULL,
    semantic_vector BLOB,
    context_offset BLOB,
    l2_clustered INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (dna_id, seq_idx)
);

-- ==== ZVEC 知识库主表 ====
CREATE TABLE IF NOT EXISTS zvec_entries (
    resource_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    l0_raw TEXT,
    l1_facts TEXT,
    l2_summary TEXT,
    l3_profile TEXT,
    scene_label BLOB,
    checksum TEXT,
    dna_id TEXT,
    created_at INTEGER NOT NULL DEFAULT (unixepoch()),
    updated_at INTEGER NOT NULL DEFAULT (unixepoch())
);
```

### B. 版本状态记录

| 日期 | 版本 | 变更内容 |
|------|------|---------|
| 2026-07-10 | V1.0-草案 | 首次完整发布，标注为预研草案，32D→WenVec36 升级，新增 DNA 编码总线章节，新增 Demo 闭环阶段，新增全局约束红线 |

---

**文档版本**: V1.0（预研草案）  
**文档编号**: WS-ARCH-TIANQUAN-20260710  
**文档状态**: ⏳ 前置依赖未达成，正式版本待发布  
**生效条件**: Demo 验收通过 + DNA 遗传编码强制规范 V1.0 定稿  
**对应文件**: 《WenStar OS 天权白皮书》《DNA 遗传编码强制规范 V1.0》
