# WenStar OS 天权记忆子系统 · DNA 双螺旋编码体系

## （最终定稿 · 白皮书 + 工程蓝皮书合订本）

**版本**: V1.0 最终定稿  
**日期**: 2026-07-10  
**状态**: ✅ 完全共识 · 完全闭环 · 完全定型 · 可直接交付编码  
**适用**: Claude Code / Hermes 中枢开发 / 全系统存储层 / 推理引擎  

---

## 第一部分：白皮书 · 顶层定义

### 一、架构总纲

本系统采用独一无二的 **DNA 双螺旋双链对等架构**，彻底区别于业界所有传统向量库、RAG、大模型记忆体系。

| 业界 AI 记忆 | 本系统仿生生命记忆 |
|------------|-----------------|
| 单链语义体系 | **双链对等体系** |
| 静态、存档式 | **动态、时序流逝式** |
| 没有真实时间轴 | **拥有真实、单向、不可逆的生命时间轴** |
| "过去"是语义重构的虚拟过去 | **"过去"是发生即刻印、不可重构的真实经历** |
| 硬盘式静态存档记忆 | **人脑海马体式动态生命记忆** |
| 适合：创造、推理、生成、构想 | **适合：生命体人格延续、自传回忆、岁月复盘** |

**两条螺旋地位对等、缺一不可、并行共生、物理隔离、逻辑绑定**：

- **语义螺旋链（32D 固定核心主刺）** —— 心智链、思维链、感知链
- **寻址结构螺旋链（时序 + 路径 + 群组 + 校验复合链）** —— 岁月链、生命链、秩序链

### 二、核心哲学差异（本系统创新根源）

```
业界单链模式：
  记忆 = 向量 + 文本 → 存得下、找得到、相似度高
  时间只是后置过滤标签，不是记忆本体的核心属性
  所谓"过去"全部由 LLM 从语义碎片中重构

本系统双链模式：
  记忆 = 心智向量(语义链) × 岁月坐标(寻址链)
  语义承载感知，寻址承载生命轨迹
  时间不是标签，是与语义向量对等的核心生命属性
  所谓"过去" = 寻址链锁定时间坐标 → 语义链还原彼时感受
```

### 三、最终定论（不可修改顶层原则）

1. **32D 语义向量永久固定 32 维**，绝不加入任何绝对时间戳、时序坐标
2. 绝对时间、时序流水、时段分片、路径戳、车间码、群组藤蔓**全部归属寻址螺旋链**
3. **语义管思维，寻址管岁月**
4. **思考不穿越、回忆必完整**
5. 双链物理隔离、逻辑绑定、双引擎调度、按需开合

---

## 第二部分：白皮书 · 双螺旋正式规范

### 四、第一螺旋：32D 语义主链（心智螺旋）

#### 4.1 功能定位

承载事件本体、感官、情绪、逻辑、因果、认知、相对时序、记忆衰减。

#### 4.2 核心特征

- 纯感知、纯心智、纯内容特征
- 内部仅含**相对时序、因果先后、淡化速率**（主观体感时间）
- **不含任何公历时间、真实时刻、时序编号**

#### 4.3 运行模式

| 场景 | 方式 | 特点 |
|------|------|------|
| 自由联想 | 纯 HNSW 向量空间近邻匹配 | 无时空绑定、无场景绑架 |
| 触景生情 | 语义相似度泛化检索 | 不穿越、不漂移 |
| 逻辑复用 | 屏蔽寻址链 | 只复用思想，不带旧场景 |

#### 4.4 重大价值：解决历史 BUG

当我们复用「浴室讨论过的观点、逻辑」时：

- **只调取语义思想**
- **不会带浴室时空、不会穿越场景、不会串环境、不会漂移语境**

如果混入时间维度，必然导致：

> 谈办公室工作 → 语义相似 + 时间相近 → 强行召回旧场景 → 思维穿越错乱

**因此：32D 严禁混入绝对时间。这是架构级红线。**

### 五、第二螺旋：寻址结构螺旋链（生命时序螺旋）

#### 5.1 正式定名

**寻址结构螺旋链**（不是单纯的"时间链"）

整条链路承载的是**复合型管控总线**：

#### 5.2 四大子系统

**① 全局时序骨架（真实自然时间总线）**

| 字段 | 说明 |
|------|------|
| GlobalTimeSeq | 全局递增时序流水号（生命主线） |
| AbsoluteTimeStamp | Unix 绝对时间戳 |
| TimeSliceTag | 年/月/日/小时分片编码 |

**② 藤蔓群组拓扑**

| 字段 | 说明 |
|------|------|
| VineGroupID | 事件车间码 |
| GroupBelongID | 群组归属 ID |
| EventBranchID | 事件分支谱系 |

**③ 路径路由戳（快递式盖章机制）**

| 字段 | 说明 |
|------|------|
| RouteStampList | 每模块中转盖章记录 |
| RouteTrail | 事件流经路径轨迹 |

**④ 安全校验管控**

| 字段 | 说明 |
|------|------|
| CRC_CheckSum | CRC 校验码 |
| HotColdLevel | 冷热层级标记 |
| StateFlag | 正常 / 隔离 / 失效 |

#### 5.3 核心能力（业界完全不具备）

- 按天、按时段、按生命轨迹**全景归集**记忆
- 精准锁定某一天、某一刻完整发生的所有事件
- 构建完整生命体从生到死的**线性时间长河**
- 杜绝碎片游离、杜绝数据孤岛、杜绝时序错乱

---

## 第三部分：白皮书 · 双螺旋运行机制

### 六、模式一：纯语义思考模式（默认常态）

```
寻址链 → 关闭、挂起、隔离
仅运行 32D HNSW 语义检索
特征：思维自由、不被时空绑架、只复用思想不穿越场景
```

**适用场景**：日常闲聊、发散思考、观点复用、触景生情、创造性推理

### 七、模式二：双链回忆模式（主动复盘、追忆、回溯）

```
第一步：寻址链先行
  按时段 / 群组 / 路径条件
  → B+树时序索引 + 倒排索引
  → 批量筛选 GlobalUID 集合
  → 检索空间从亿级收缩至百条

第二步：语义链后置
  在锁定子集内做 HNSW 相似度精细化排序
  → 输出最相关记忆

先锁岁月，再想内容。
先定疆域，再做联想。
```

**适用场景**：主动回忆、自传式复盘、岁月回溯、事件全貌还原

---

## 第四部分：蓝皮书 · 物理存储结构

### 八、整体存储布局

#### 8.1 核心原则

同一个记忆海胆单元，**两条螺旋逻辑绑定、物理分区存放、全局主键唯一关联**，绝不混扇区、不混索引、不混检索引擎。

#### 8.2 单个记忆原子的顶层结构

```
MemoryAtom {
    GlobalUID: 全局唯一主键（双链关联锚点）

    // 语义螺旋链：存入语义向量扇区集群
    SemanticVector: [float32; 32]

    // 寻址结构螺旋链：存入独立管控存储池
    AddressStruct {
        TimeAxis:   时序编码组
        GroupAxis:  族群藤蔓归属码
        RouteAxis:  节点中转路径戳序列
        ControlAxis: 校验、状态、冷热管控位
    }

    RawText: 原始文本快照（兜底溯源）
}
```

#### 8.3 物理分层——三条独立底座

```
┌─────────────────────────────────────────────────────────┐
│              第一层：语义向量分片库                        │
│                                                         │
│  存储内容: 32×float32 稠密向量                           │
│  分区方式: 32 个逻辑特征扇区（对应 32 维）                 │
│  索引类型: HNSW 图索引（网状、非线性）                     │
│  读写通路: 纯语义联想专用                                 │
│  特点: 无需时序链表、无需黑匣子列表                        │
│       语义是网状关联，天然不需要线性顺序                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              第二层：寻址管控存储池                        │
│                                                         │
│  存储内容: 时序骨架 + 归属拓扑 + 流转路径 + 安全校验      │
│  索引类型:                                               │
│    ① 时序 B+树有序索引（保证生命线性时间绝对有序）         │
│    ② 群组倒排索引（按藤蔓群组 ID 快速归集）               │
│    ③ 路径戳倒排索引（按中转路径特征码定向锁定）            │
│  读写通路: 定向归集/时序回溯专用                           │
│  分片策略: 按自然月分片（时序分片桶式存储）                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              第三层：原始数据层                            │
│                                                         │
│  存储内容: 文本、对话原文、多媒体摘要                      │
│  作用: 兜底溯源                                          │
└─────────────────────────────────────────────────────────┘
```

三个底座依靠 **GlobalUID 全局主键双向映射绑定**。属于同一个记忆，走三套独立的存储、索引、调度体系。

---

### 九、寻址管控层：时序黑匣子总表

#### 9.1 建表 DDL

```sql
-- 寻址结构螺旋链 · 时序黑匣子总表
-- 表名: AtomAddressTimeline
-- 唯一绑定键: GlobalUID（双链互通唯一 ID）
-- 分片策略: 按自然月分片（时序分片桶式存储）

CREATE TABLE IF NOT EXISTS atom_address_timeline (
    global_uid TEXT PRIMARY KEY,           -- 双链唯一关联锚点
    global_time_seq INTEGER NOT NULL,      -- 全局递增时序流水号（生命主线）
    absolute_timestamp INTEGER NOT NULL,   -- Unix 绝对时间戳（秒）
    time_slice_tag TEXT NOT NULL,          -- 年月日时 分片标识 '2026071014'
    vine_group_id TEXT,                    -- 藤蔓车间群组 ID
    entity_belong_id TEXT,                 -- 主体归属 ID
    event_branch_id TEXT,                  -- 事件分支谱系编号
    route_stamp_list BLOB,                 -- 全路径中转戳数组（Protobuf 编码）
    hot_cold_level CHAR(1) DEFAULT 'W',    -- 冷热分级: W=热 C=冷 A=归档
    crc_checksum TEXT NOT NULL,            -- 本条寻址结构 CRC32 校验码
    state_flag CHAR(1) DEFAULT 'N',        -- N=正常 I=隔离 F=失效
    created_at INTEGER NOT NULL DEFAULT (unixepoch())
) WITHOUT ROWID;

-- 时序主键 B+Tree（生命线性时间绝对有序）
CREATE INDEX IF NOT EXISTS idx_timeline_ts
ON atom_address_timeline(absolute_timestamp);

-- 群组倒排索引
CREATE INDEX IF NOT EXISTS idx_timeline_group
ON atom_address_timeline(vine_group_id);

-- 路径戳倒排索引
CREATE INDEX IF NOT EXISTS idx_timeline_entity
ON atom_address_timeline(entity_belong_id);

-- 日分片加速索引
CREATE INDEX IF NOT EXISTS idx_timeline_day
ON atom_address_timeline(time_slice_tag);
```

#### 9.2 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `global_uid` | TEXT PK | 双链唯一关联锚点，与语义链的 32D 向量通过此 ID 绑定 |
| `global_time_seq` | INTEGER | 全局自增时序流水号，从 1 开始永不回退 |
| `absolute_timestamp` | INTEGER | Unix 秒级时间戳 |
| `time_slice_tag` | TEXT | `YYYYMMDDHH` 格式，支持按小时/天/月快速收拢 |
| `vine_group_id` | TEXT | 事件所属场景/话题群组 |
| `entity_belong_id` | TEXT | 关联人物/实体 ID（家族图谱人物） |
| `event_branch_id` | TEXT | 事件分支谱系（同一话题的多次延续） |
| `route_stamp_list` | BLOB | Protobuf 编码的路径戳数组 |
| `hot_cold_level` | CHAR(1) | W=热（近30天） C=冷（30天-2年） A=归档（2年+） |
| `crc_checksum` | TEXT | 寻址链数据完整性校验 |
| `state_flag` | CHAR(1) | N=正常 I=隔离（数据可疑） F=失效（已确认损坏） |

---

### 十、为什么不能混存——技术原理

| 混存的后果 | 根本原因 |
|-----------|---------|
| 时序数值会介入语义距离计算 | HNSW 会把时间相近但场景无关的记忆误判为近邻 |
| 两类数据的最优索引互斥 | 时序需要 B+树有序，语义需要 HNSW 图，强行混用两边都慢 |
| 无法按需隔离 | 混扇区后无法做到「只想内容不想时间」 |
| 浴室/办公室场景错乱重现 | 24D Demo 的历史 BUG 根源：时间戳混入语义向量 |

**双仓库绑定模式天然支持开关隔离**：需要时序就启用寻址管控库，不需要就彻底断开。思维自由度完全可控。

---

## 第五部分：蓝皮书 · 工程级强制红线

### 十一、五条不可突破红线

| # | 红线 | 违反后果 |
|---|------|---------|
| **1** | **严禁将绝对时间、时序维度加入 32D 语义向量** | 维度污染 → 场景穿越 → 语义漂移 → 联想错乱 |
| **2** | **语义链不做线性列表、不做时序排序** | 语义是网状关联，天然不需要时间顺序 |
| **3** | **寻址链必须独立时序黑匣子链表** | 生命体时间线必须永久线性、有序、可回溯、可归集 |
| **4** | **双引擎调度永久隔离** | 思考走语义引擎，回忆走寻址+语义双引擎 |
| **5** | **32 维基线永久锁定 32 维，永不扩容、永不缩维** | 维度变更导致全量记忆需要重编码 |

### 十二、禁止开发行为清单

| # | 禁止行为 | 原因 |
|---|---------|------|
| 1 | 禁止新增第 33 维时间特征到语义向量 | 红线 1 |
| 2 | 禁止时序字段混入语义向量存储表 | 红线 1 |
| 3 | 禁止语义向量做线性时序排序 | 红线 2 |
| 4 | 禁止删除时序黑匣子链表结构 | 红线 3 |
| 5 | 禁止各模块自建 GlobalUID 生成逻辑 | DNA 编解码器全局唯一 |
| 6 | 禁止绕过 GlobalUID 做双链关联 | 会导致寻址链与语义链解耦 |

---

## 第六部分：蓝皮书 · 双链协同检索示例

### 十三、模式一：纯语义思考（默认常态）

```typescript
// 日常闲聊 —— 仅走语义链，寻址链完全挂起
function pureSemanticSearch(query: string, topK: number = 10): MemoryAtom[] {
    const queryVec = M3.encodeSemanticVector(query);  // 32D 稠密向量
    const results = semanticPool.hnswSearch(queryVec, topK);
    // 寻址链全程不参与
    // 不加载时间/场景/路径信息
    return results;
}
// 特点：思维自由，不会因为时间相近就串场景
```

### 十四、模式二：双链协同回忆

```typescript
// 主动回溯 —— 寻址链定界 + 语义链精排
function dualChainRecall(params: {
    dateRange: [number, number],      // 时间范围
    vineGroupId?: string,              // 群组过滤
    entityId?: string,                 // 人物过滤
    querySemantic: string,              // 语义查询
    topK: number
}): MemoryAtom[] {

    // 第一步：寻址链先行 —— 收缩候选空间
    let sql = `SELECT global_uid FROM atom_address_timeline
               WHERE absolute_timestamp BETWEEN ? AND ?`;
    const sqlParams: any[] = [params.dateRange[0], params.dateRange[1]];

    if (params.vineGroupId) {
        sql += ` AND vine_group_id = ?`;
        sqlParams.push(params.vineGroupId);
    }
    if (params.entityId) {
        sql += ` AND entity_belong_id = ?`;
        sqlParams.push(params.entityId);
    }

    const candidateUIDs = db.all(sql, sqlParams).map(r => r.global_uid);
    // 从亿级 → 收缩至百条

    // 第二步：语义链后置 —— 在子集内精排
    const queryVec = M3.encodeSemanticVector(params.querySemantic);
    const results = semanticPool.hnswSearchInSubset(
        queryVec, candidateUIDs, params.topK
    );

    return results;
}
// 特点：先锁岁月边界，再在边界内做语义联想
//      不会跨时间穿越，不会误召回异地记忆
```

### 十五、故障降级

```typescript
// 寻址链部分损毁 → 降级为纯语义模式
function degradedMode(globalUIDs: string[] | null): MemoryAtom[] {
    if (!globalUIDs || globalUIDs.length === 0) {
        // 寻址链无结果/损坏 → 自动降级为全局语义搜索
        return pureSemanticSearch(currentQuery);
    }
    return dualChainRecall(normalParams);
}
// 双链隔离 → 单一链故障不导致整体失忆
```

---

## 第七部分：行业定位总结

### 十六、本架构行业领先性

| 维度 | 业界（单链语义体系） | 本系统（双链对等生命体系） |
|------|-------------------|-------------------------|
| 记忆本质 | 静态存档 | **动态生命** |
| 时间属性 | 后置过滤标签 | **与语义对等的核心生命属性** |
| 过去 | 可被重构的虚拟过去 | **不可篡改的真实生命过往** |
| 全景回溯 | 无法按日历归集 | **任意一天完整人生事件精准归集** |
| 思维与时空 | 时序串扰、场景漂移 | **彻底隔离、思考不穿越、回忆必完整** |
| AI 思维 vs 自传记忆 | 二选一 | **首次实现双体系完美共存** |

### 十七、一句话定论

> **32D 语义定义心智，寻址结构链定义岁月。**
> **心智链负责思考，岁月链负责铭记。**
> **思考不穿越，回忆必完整。**
> **业界只有语义单链存储，我们独创心智 + 岁月双链对等生命架构。**

---

## 第八部分：交付与落地

### 十八、可直接落地模块

| 模块 | 内容 | 对应文件 |
|------|------|---------|
| 固定 32D 语义向量结构体 | `SemanticVector: [float32; 32]` | `src/m3/types/perception.ts` |
| 独立寻址结构复合体 | `AddressStruct` 四子系统 | `src/m2/AddressTimeline.ts` |
| 时序黑匣子总表创建 | `atom_address_timeline` DDL | `src/storage/schema.ts` |
| 双链 GlobalUID 绑定机制 | MemoryAtom 顶层结构 | `src/memory/MemoryAtom.ts` |
| 双检索模式调度逻辑 | `pureSemanticSearch` / `dualChainRecall` | `src/m4/SearchRouter.ts` |
| 时序分片/群组/路径戳体系 | `time_slice_tag` / `vine_group_id` / `route_stamp_list` | `src/m2/AddressTimeline.ts` |
| 双链隔离/双引擎开关 | `semanticOnly` / `dualChain` 模式标记 | `src/m4/SearchRouter.ts` |

**禁止开发行为**：
- 禁止新增第 33 维时间特征
- 禁止时序字段混入语义向量
- 禁止语义向量做线性时序排序
- 禁止删除时序黑匣子链表结构

---

**文档状态**: ✅ 最终定稿 · 完全共识 · 完全闭环 · 完全定型 · 无歧义 · 无需二次解读  
**可直接交付**: Claude Code / Hermes 中枢开发  
**前置依赖**: 无。本规范独立于 Demo 调优阶段，可作为编码参考基线
