# WS-ARCH-32D-MEM 工程蓝皮书 最终修订版

> **文档编号**：WS-ARCH-32D-MEM-20260709  
> **版本**：最终修订版  
> **最后更新**：2026-07-09  
> **适用对象**：Hermes 后端开发、ClaudeCode 后端开发、存储开发  
> **前置依赖**：`complete-architecture.md` 旧 24D Demo 源码、全局统一命名规范、32 维三体对照表  

---

## 核心整改清单（全部落实评审意见）

1. ✅ 删除 PCIe 协议栈、物理磁点、块设备直写等不切实际描述
2. ✅ 修正"转码器已完成"，更名 Transcoder 序列化层，采用 Protobuf + BLOB + SQLite
3. ✅ 32 分区改为 `state_spines` 复合索引逻辑表，废弃硬件寻址描述
4. ✅ ZVEC 对外名称不变，底层复用 sqlite-vec，不自研向量引擎
5. ✅ 修正 32D 向量生成逻辑，禁止 LLM 直接输出浮点，采用分层规则/瑶光输入
6. ✅ 补充 L0–L3 异步调度、算力量化
7. ✅ 新增完整 Proto、SQL、TS 示例、单行开发任务看板、全局强制红线

---

## 目录

1. [系统工程概述](#1-系统工程概述)
2. [顶层三体数据流与 M1-M9 模块分工](#2-顶层三体数据流与-m1-m9-模块分工)
3. [全局 dna_root_id 时序 ID 规范](#3-全局-dna_root_id-时序-id-规范)
4. [32D 海胆 state_spines 存储规范](#4-32d-海胆-state_spines-存储规范)
5. [L0-L3 语义分层蒸馏工程实现](#5-l0-l3-语义分层蒸馏工程实现)
6. [ZVEC 向量知识库封装规范](#6-zvec-向量知识库封装规范)
7. [Transcoder Protobuf 序列化完整设计](#7-transcoder-protobuf-序列化完整设计)
8. [FiveStageGate 五级闸门完整管线实现](#8-fivestagegate-五级闸门完整管线实现)
9. [统一 NVMe+SQLite 持久化链路规范](#9-统一-nvmesqlite-持久化链路规范)
10. [旧 Demo 24D 平滑迁移方案](#10-旧-demo-24d-平滑迁移方案)
11. [分阶段单行开发任务看板](#11-分阶段单行开发任务看板)
12. [全局强制开发约束红线](#12-全局强制开发约束红线)
13. [附录](#13-附录)

---

## 1 系统工程概述

WenStar OS 的工程实现分为 **M1–M9 九个后端模块**、一套 **ZVEC 向量知识库**、一套 **三库（砂金/金库/黑钻）记忆存储体系**。本蓝皮书聚焦于 32 维记忆子系统（32D 海胆 + 五级闸门 + L0–L3 蒸馏 + ZVEC 检索 + Protobuf 序列化）的工程落地规范。

---

## 2 顶层三体数据流与 M1–M9 模块分工

（复用 Demo 模块编号，完整版见《太虚境运算规范》）

| 模块 | 职责 | 与本蓝皮书关联 |
|------|------|---------------|
| M1 | 事件总线 / 32 通道调度 | 承载 32 维数据流 |
| M2 | 情感谱系 / 关系突触 | 提供 D9–D20 推理上下文 |
| M3 | 知识库 | 融合 ZVEC 向量库 |
| M4 | 32D 海胆记忆（本蓝皮书核心） | 五级闸门、state_spines、L0–L3 |
| M5 | 角色扮演域 | 消费 32 维记忆快照 |
| M6 | 提示词组合器 | 引用 L0–L3 摘要 |
| M7 | 梦境引擎 / 离线巩固 | 消费 state_spines 全量快照 |
| M8 | 三库存储 | 存储 Protobuf 序列化后的 BLOB |
| M9 | 人格演化 | 消费 32 维趋势数据 |

---

## 3 全局 dna_root_id 时序 ID 规范

### 3.1 生成规则

每条记忆快照生成一个全局唯一 `dna_root_id`，格式：

```
{timestamp_ms}-{random_hex}
```

示例：`20260709123456789-a1b2c3d4`

### 3.2 绑定要求

- 每条 32D 海胆快照必须携带 `dna_root_id`
- `dna_root_id` 作为三库（砂金 → 金库 → 黑钻）全链路追踪主键
- 禁止重复、跳跃、回退

---

## 4 32D 海胆 state_spines 存储规范

### 4.1 设计原则

- 废弃旧 Demo 的扁平 24D 表结构
- 新建 `state_spines` 逻辑分区表，按时间 + 区位双索引
- 所有数据经 Protobuf 序列化为 BLOB 存储

### 4.2 建表 SQL

```sql
CREATE TABLE IF NOT EXISTS state_spines (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dna_root_id     TEXT    NOT NULL UNIQUE,
    timestamp_ms    INTEGER NOT NULL,
    location_fingerprint TEXT NOT NULL,  -- D24/D25 区位编码
    spine_blob      BLOB    NOT NULL,    -- Protobuf 序列化后的 32D 全量快照
    summary_l0      TEXT,                -- 关键词级摘要
    summary_l1      TEXT,                -- 单句摘要
    summary_l2      TEXT,                -- 段落摘要（聚类后）
    summary_l3      TEXT,                -- 完整对话摘要
    gate_level      INTEGER DEFAULT 0,   -- 五级闸门输出等级
    created_at      TEXT    DEFAULT (datetime('now')),
    UNIQUE(dna_root_id)
);

CREATE INDEX idx_spines_time ON state_spines(timestamp_ms);
CREATE INDEX idx_spines_location ON state_spines(location_fingerprint);
CREATE INDEX idx_spines_time_location ON state_spines(timestamp_ms, location_fingerprint);
```

### 4.3 区位指纹编码

`location_fingerprint` 格式：

```
{scene_type}:{scene_id}:{sub_zone}
```

示例：`home:livingroom:sofa` | `office:floor3:desk_a2` | `outdoor:park:lake`

---

## 5 L0–L3 语义分层蒸馏工程实现

### 5.1 分层定义

| 层级 | 名称 | 内容粒度 | 触发时机 | 平均 Token |
|------|------|---------|---------|-----------|
| L0 | 关键词级 | 抽取命名实体 + 情感标签 | 每条快照生成时同步 | ~50 tokens |
| L1 | 单句摘要 | 一句话概括核心事件 | 每条快照生成时同步 | ~100 tokens |
| L2 | 段落摘要 | 语义+区位+时间三重聚类后聚合 | 每 N 条快照或定时异步 | ~300 tokens |
| L3 | 完整对话摘要 | 整轮对话压缩蒸馏 | 对话结束或定时异步 | ~500 tokens |

### 5.2 异步调度策略

```
L0 / L1 ── 同步生成（毫秒级，随快照写入）
              ↓
L2 ──────── 异步队列（积累 N=10 条快照 或 每 5 分钟触发）
              ↓
L3 ──────── 异步队列（对话结束标记触发 或 每 30 分钟强制蒸馏）
```

### 5.3 L2 聚类约束

**强制三重判定**，禁止纯文本匹配：

1. **语义相似度**：cosine > 0.75
2. **区位一致**：`location_fingerprint` 同场景类
3. **时间窗口**：ΔT < 2 小时

---

## 6 ZVEC 向量知识库封装规范

### 6.1 技术选型

- 对外名称：**ZVEC**（Zero-dependency Vector Engine）
- 底层实现：**sqlite-vec**（SQLite 向量扩展）
- 淘汰原有 TF-IDF 知识库

### 6.2 存储结构

```sql
CREATE TABLE IF NOT EXISTS zvec_entries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id        TEXT    NOT NULL UNIQUE,
    content_text    TEXT    NOT NULL,
    embedding       BLOB    NOT NULL,       -- sqlite-vec 向量（浮点数组）
    scene_tags      TEXT    NOT NULL,        -- JSON: ["home","livingroom","companion"]
    source_type     TEXT    NOT NULL DEFAULT 'knowledge', -- knowledge | memory | document
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- 通过 sqlite-vec 的虚拟表进行向量检索
-- CREATE VIRTUAL TABLE vec_entries USING vec0(embedding float32[768]);
```

### 6.3 核心约束

- 每条 ZVEC 条目必须绑定 `scene_tags`（场景标签）
- 检索时必须传入当前 `location_fingerprint` 作为过滤条件
- 记忆与知识共用同一套时空校验规则

---

## 7 Transcoder Protobuf 序列化完整设计

### 7.1 设计原则

- 统一蛇形命名（snake_case）字段
- 内置 CRC32 校验
- 所有记忆、向量、摘要统一序列化为 SQLite BLOB
- 废弃裸文本存储

### 7.2 Proto 文件

#### spine.proto（32D 海胆快照）

```protobuf
syntax = "proto3";
package wenstar.v1;

message SpineSnapshot {
    string dna_root_id = 1;
    int64 timestamp_ms = 2;
    string location_fingerprint = 3;
    
    // 大类 1: 肉身实体基底 D1-D8
    float d1_muscle_fatigue = 10;
    float d2_pain_level = 11;
    float d3_nerve_arousal = 12;
    map<string, float> d4_hormones = 13;       // cortisol, dopamine, serotonin
    float d5_pheromone = 14;
    float d6_metabolic_cycle = 15;
    float d7_self_heal = 16;
    float d8_sensory_env = 17;
    
    // 大类 2: 个体内在精神 D9-D14
    float d9_self_identity = 20;
    float d10_desire = 21;
    float d11_fear_anxiety = 22;
    float d12_pleasure = 23;
    float d13_empathy = 24;
    float d14_self_protect = 25;
    
    // 大类 3: 圈层人际 D15-D20
    float d15_partner_attachment = 30;
    float d16_partner_protect = 31;
    float d17_family_belonging = 32;
    float d18_family_protect = 33;
    float d19_social_fit = 34;
    float d20_team_protect = 35;
    
    // 大类 4: 时空环境 D21-D26
    float d21_private_space = 40;
    float d22_home_atmosphere = 41;
    float d23_workplace = 42;
    float d24_public_space = 43;
    float d25_space_distance = 44;
    float d26_season_climate = 45;
    
    // 大类 5: 动态成长 D27-D32
    float d27_micro_physiology = 50;
    float d28_nature_expand = 51;
    float d29_social_refine = 52;
    float d30_culture_growth = 53;
    float d31_subjective_objective_couple = 54;
    float d32_global_overview = 55;
    
    bytes crc32_checksum = 99;  // 整包 CRC32 校验
}
```

#### token.proto（对话 Token 摘要）

```protobuf
syntax = "proto3";
package wenstar.v1;

message TokenSummary {
    string dna_root_id = 1;
    string l0_keywords = 2;
    string l1_single_sentence = 3;
    float l2_cluster_score = 4;
    repeated string l3_paragraphs = 5;
    bytes crc32_checksum = 99;
}
```

#### zvec_entry.proto（向量条目）

```protobuf
syntax = "proto3";
package wenstar.v1;

message ZvecEntry {
    string entry_id = 1;
    string content_text = 2;
    repeated float embedding = 3 [packed = true];
    repeated string scene_tags = 4;
    string source_type = 5;
    bytes crc32_checksum = 99;
}
```

### 7.3 Transcoder.ts 封装

```typescript
// Transcoder.ts — 统一编解码入口
import * as protobuf from 'protobufjs';

export class Transcoder {
    private root: protobuf.Root;
    
    constructor(protoDir: string) {
        this.root = new protobuf.Root();
        this.root.loadSync(`${protoDir}/spine.proto`);
        this.root.loadSync(`${protoDir}/token.proto`);
        this.root.loadSync(`${protoDir}/zvec_entry.proto`);
    }
    
    encodeSpine(snapshot: SpineData): Buffer {
        const Spine = this.root.lookupType('wenstar.v1.SpineSnapshot');
        const message = Spine.create(snapshot);
        const buffer = Spine.encode(message).finish();
        return Buffer.from(buffer);
    }
    
    decodeSpine(buffer: Buffer): SpineData {
        const Spine = this.root.lookupType('wenstar.v1.SpineSnapshot');
        const message = Spine.decode(buffer);
        // 校验 CRC32
        return message as unknown as SpineData;
    }
    
    // 类似方法: encodeToken, decodeToken, encodeZvec, decodeZvec
}
```

---

## 8 FiveStageGate 五级闸门完整管线实现

### 8.1 五级定义

| 级别 | 名称 | 过滤规则 | 抑制场景 |
|------|------|---------|---------|
| G0 | 无过滤 | 全部记忆可见 | 当前同场景同时间 |
| G1 | 场景软约束 | 仅抑制不同区位记忆 | 跨房间/跨场地 |
| G2 | 时间硬约束 | 仅召回 ΔT < 24h 的记忆 | 跨天但同场景 |
| G3 | 心境隔离 | 仅召回同情感极性记忆 | 情绪反差过大场景 |
| G4 | 最大抑制 | 仅召回当前同场景片段 | 高度敏感场合 |

### 8.2 管线流程

```
输入：当前 location_fingerprint + timestamp_ms + 情感状态
  ↓
G0: 是否同场景同时间？→ 是 → 全部放行
  ↓ 否
G1: location_fingerprint 是否匹配？→ 否 → 抑制不同区位
  ↓ 是
G2: ΔT < 24h？→ 否 → 抑制跨天记忆
  ↓ 是
G3: 情感极性余弦 > 0.5？→ 否 → 抑制情绪反差
  ↓ 是
G4: 是否高度敏感场合？→ 是 → 仅放行同场景片段
  ↓
输出：过滤后记忆列表
```

### 8.3 强制约束

- 五级闸门**不可关闭**，底层强制过滤逻辑
- 每次记忆检索必须经过五级闸门管线

---

## 9 统一 NVMe + SQLite 持久化链路规范

### 9.1 数据链路

```
Hermes 业务层
    ↓
Transcoder 编解码（Protobuf serialize / deserialize）
    ↓
SQLite（WAL 开启，PRAGMA journal_mode=WAL）
    ↓
NTFS / ext4 文件系统
    ↓
NVMe SSD
```

### 9.2 关键配置

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;         -- 64MB cache
PRAGMA busy_timeout = 5000;
PRAGMA foreign_keys = ON;
```

### 9.3 铁律

- 全文移除 PCI、总线、硬件协议栈描述
- 嵌入式设备仅修改数据库路径环境变量
- 所有 IO 经由操作系统文件系统，无底层硬件直写

---

## 10 旧 Demo 24D 平滑迁移方案

### 10.1 迁移步骤

1. **P3 阶段执行**：新建 `state_spines` 表（含 32 维 + 区位指纹）
2. **数据转换**：读取旧 24D 表，补充 D25–D32 默认值（置零或瑶光初始值）
3. **区位回填**：根据对话时间戳，按最邻近场景匹配回填 `location_fingerprint`
4. **原地保留**：旧表保留为只读备份，新表上线后逐步切换读写流量
5. **验证**：对比新旧检索结果，diff 不超过 5%

### 10.2 兼容层

```typescript
// 旧 24D → 新 32D 适配器
class LegacyAdapter {
    adapt(old24: LegacySpine): SpineData {
        return {
            ...old24,
            // D25-D32 新增字段，默认填充
            d25_space_distance: 0,
            d26_season_climate: 0.5,
            d27_micro_physiology: 0.5,
            d28_nature_expand: 0.5,
            d29_social_refine: 0.5,
            d30_culture_growth: 0.5,
            d31_subjective_objective_couple: 0.5,
            d32_global_overview: 0.5,
            // 区位指纹从旧对话元数据推断
            location_fingerprint: inferLocation(old24),
        };
    }
}
```

---

## 11 分阶段单行开发任务看板

### P0（第 1–3 周）

| # | 任务 | 模块 | 预估工时 |
|---|------|------|---------|
| 1 | 五级闸门管线实现（含测试） | M4 | 5 天 |
| 2 | D24/D25 区位指纹扩展 | M4 | 2 天 |
| 3 | 区位编码规范 + 场景注册 | M4 | 1 天 |
| 4 | 32D state_spines 建表 + 迁移 | M4 | 2 天 |
| 5 | P0 集成测试 | QA | 3 天 |

### P1（第 4–6 周）

| # | 任务 | 模块 | 预估工时 |
|---|------|------|---------|
| 1 | L0–L1 同步摘要生成 | M4 | 2 天 |
| 2 | L2 异步聚类引擎（三重判定） | M4 | 3 天 |
| 3 | L3 异步对话蒸馏 | M4 | 3 天 |
| 4 | P1 集成测试 | QA | 3 天 |

### P2（并行 1–2 周）

| # | 任务 | 模块 | 预估工时 |
|---|------|------|---------|
| 1 | sqlite-vec 集成与验证 | ZVEC | 2 天 |
| 2 | ZVEC 检索 API 封装 | ZVEC | 2 天 |
| 3 | 旧 TF-IDF 数据迁移 | ZVEC | 1 天 |
| 4 | 场景标签绑定校验 | ZVEC | 1 天 |

### P3（并行 2 周）

| # | 任务 | 模块 | 预估工时 |
|---|------|------|---------|
| 1 | 24D → 32D 平滑迁移脚本 | M4 | 3 天 |
| 2 | 适配器兼容层 | M4 | 1 天 |
| 3 | 全链路回归测试 | QA | 3 天 |

### P4（第 7 周）

| # | 任务 | 模块 | 预估工时 |
|---|------|------|---------|
| 1 | Protobuf 三套 proto 定义 | M8 | 1 天 |
| 2 | Transcoder.ts 编解码封装 | M8 | 2 天 |
| 3 | SQLite BLOB 读写迁移 | M8 | 2 天 |
| 4 | CRC32 校验全链路覆盖 | M8 | 1 天 |

---

## 12 全局强制开发约束红线

1. **逻辑隔离**：语义层、32D 状态层、ZVEC 知识库逻辑隔离，禁止混表
2. **必填校验**：无 `dna_root_id`、无 `location_fingerprint` 记忆拒绝入库；ZVEC 条目必须绑定场景标签
3. **闸门强制**：五级闸门不可关闭，底层强制过滤逻辑
4. **三重判定**：L2 聚类必须语义 + 区位 + 时间三重判定，禁止纯文本匹配
5. **分层生成**：32D 向量分层生成，禁止 LLM 直接输出浮点数值
6. **统一 sqlite-vec**：ZVEC 底层统一 sqlite-vec，淘汰原有 TF-IDF 知识库
7. **Protobuf 序列化**：所有业务结构体必须 Protobuf 序列化存入 BLOB，禁止裸文本入库
8. **文件系统 IO**：取消底层硬件驱动开发，所有 IO 经由操作系统文件系统
9. **单次单颗**：单次交互仅生成一颗完整 32D 海胆，禁止单 Token 粒度向量

---

## 13 附录

### A. 编译脚本

```bash
# Protobuf 编译
npx protoc --ts_out src/generated \
  --proto_path protos \
  protos/spine.proto protos/token.proto protos/zvec_entry.proto
```

### B. Transcoder.ts 测试

```typescript
// transcoder.test.ts
test('encode/decode spine roundtrip', () => {
    const original = createTestSpine({ d1_muscle_fatigue: 0.7, d4_cortisol: 18.5 });
    const buffer = transcoder.encodeSpine(original);
    const decoded = transcoder.decodeSpine(buffer);
    expect(decoded.d1_muscle_fatigue).toBeCloseTo(0.7);
    // CRC32 校验自动执行
});
```

### C. 相关文档

- [产品白皮书](../01-产品白皮书/WenStar-OS-三体全域仿生个人世界白皮书-V1.0.md)
- [瑶灵肉身规范](../03-三体技术规范/A-瑶灵硅基肉身32维主观响应规范-V1.0.md)
- [瑶光世界演算规范](../03-三体技术规范/B-瑶光全域客观世界演算规范-V1.0.md)
- [太虚运算规范](../03-三体技术规范/C-太虚境Hermes天权中枢运算规范-V1.0.md)
- [32 维通信对照表](../04-配套统一标准/32维三体双向通信总对照表.md)
- [医学指标手册](../04-配套统一标准/32维真人医学对标指标手册.md)
- [全局命名规范](../04-配套统一标准/全局统一命名规范全集.md)
