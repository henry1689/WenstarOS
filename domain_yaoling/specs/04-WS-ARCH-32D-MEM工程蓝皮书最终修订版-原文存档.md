# WS-ARCH-32D-MEM 工程蓝皮书 最终修订版

> 存档日期：2026-07-09
> 存档编号：YL-ARCH-004
> 原始来源：用户口述 + ClaudeCode 评审整改
> 本文件为**原文存档**，后续实现中的任何修改应在实现文件中说明，不直接修改此存档

---

## 文档基础信息

编号：WS-ARCH-32D-MEM-20260709
适用：Hermes、ClaudeCode 后端开发
前置依赖：complete-architecture.md 旧 24D Demo 源码、全局统一命名规范、32 维三体对照表

### 核心整改清单（全部落实评审意见）

1. 删除 PCIe 协议栈、物理磁点、块设备直写等不切实际描述；
2. 修正"转码器已完成"，更名 Transcoder 序列化层，采用 Protobuf + BLOB + SQLite；
3. 32 分区改为 state_spines 复合索引逻辑表，废弃硬件寻址描述；
4. ZVEC 对外名称不变，底层复用 sqlite-vec，不自研向量引擎；
5. 修正 32D 向量生成逻辑，禁止 LLM 直接输出浮点，采用分层规则/瑶光输入；
6. 补充 L0-L3 异步调度、算力量化；
7. 新增完整 Proto、SQL、TS 示例、单行开发任务看板、全局强制红线。

### 目录

1. 系统工程概述
2. 顶层三体数据流与 M1-M9 模块分工（复用 Demo 模块编号）
3. 全局 dna_root_id 时序 ID 规范
4. 32D 海胆 state_spines 存储规范（建表 SQL 附录）
5. L0-L3 语义分层蒸馏工程实现（异步策略、算力说明）
6. ZVEC 向量知识库封装规范（底层 sqlite-vec）
7. Transcoder Protobuf 序列化完整设计（三套 proto 源码）
8. FiveStageGate 五级闸门完整管线实现（P0 核心模块）
9. 统一 NVMe+SQLite 持久化链路规范
10. 旧 Demo 24D 平滑迁移方案
11. 分阶段单行开发任务看板（Hermes+ClaudeCode+推理引擎）
12. 全局强制开发约束红线（更新后完整版）
13. 附录：SQL/Proto/编译脚本/TS 封装代码

### 核心工程内容（精简关键修订章节）

#### 7 Transcoder 序列化层

三套标准 proto：spine.proto / token.proto / zvec_entry.proto，统一蛇形字段，内置 CRC32 校验；
编译脚本、Transcoder.ts 统一 encode/decode 封装，所有记忆、向量、摘要统一序列化为 SQLite BLOB，废弃裸文本存储。

#### 9 存储链路固定标准

Hermes 业务层 → Transcoder 编解码 → SQLite（WAL 开启）→ NTFS/ext4 文件系统 → NVMe SSD；
全文移除 PCI、总线、硬件协议栈描述，嵌入式仅修改数据库路径环境变量。

#### 12 全局强制开发约束

1. 语义层、32D 状态层、ZVEC 知识库逻辑隔离，禁止混表；
2. 无 dna_root_id、无 location_fingerprint 记忆拒绝入库，ZVEC 条目必须绑定场景标签；
3. 五级闸门不可关闭，底层强制过滤逻辑；
4. L2 聚类必须语义+区位+时间三重判定，禁止纯文本匹配；
5. 32D 向量分层生成，禁止 LLM 直接输出浮点数值；
6. ZVEC 底层统一 sqlite-vec，淘汰原有 TF-IDF 知识库；
7. 所有业务结构体必须 Protobuf 序列化存入 BLOB，禁止裸文本入库；
8. 取消底层硬件驱动开发，所有 IO 经由操作系统文件系统；
9. 单次交互仅生成一颗完整 32D 海胆，禁止单 Token 粒度向量。

---

> 完整正式版见：`D:\WenstarOS\02-工程蓝皮书\WS-ARCH-32D-MEM-工程蓝皮书-最终修订版.md`
