# Transcoder 序列化层设计规范 V1.0

> **状态**: 最终定稿 · P4 阶段核心模块
> **日期**: 2026-07-12
> **适配**: 大一统架构 V1.0 + DNA V2.0 + 天权底座架构 V1.0
> **定位**: 全系统统一序列化层——跨 Python/TypeScript 的唯一数据契约

---

## 序言 · 为什么 Transco…der 必须先定稿

天权最底层的通信跨越两种语言——太虚境用 TypeScript（Node.js），天权内核 / 瑶灵 / 瑶光用 Python。任何在这两种语言之间传输的数据——32D 向量、海胆快照、知识库条目——都经过 Transcoder。

如果 Transcoder 的字段编号、数据类型、CRC 校验规则在今天不锁定，到了 P4 阶段再改，所有存量海胆都需要重编码。这就是"前期少量投入，后期海量减负"的典型案例。

---

## 第一章 · 三套消息协议

### 1.1 协议总览

| .proto 文件 | 对应底座 | 用途 |
|------------|---------|------|
| `spine.proto` | 语义向量池 (state_spines) | 32D 海胆快照：瑶灵体感 / 瑶光环境 → 太虚境统一编码 |
| `token.proto` | 原始数据层 (memories) | 壳肉语义单元：对话原文拆分 + L0-L3 附着 |
| `zvec_entry.proto` | 知识库 (Zvec) | 知识条目：L0-L3 分层内容 + 场景绑定 + 交互追踪 |

### 1.2 源文件位置

```
wenstar_os/common/proto/
  ├── spine.proto        ← 99 行, 5 个 message
  ├── token.proto        ← 69 行, 4 个 message
  └── zvec_entry.proto   ← 88 行, 6 个 message

单一源文件, Python 和 TypeScript 共享
编译脚本: proto/compile.sh (protoc 两端生成)
```

### 1.3 字段编号锁定规则

```
🔴 已分配的字段编号永久锁定, 永不回收、永不重排
🔴 新增字段只能使用新的连续编号
🔴 废弃字段标记 reserved, 不得删除
🔴 字段类型一旦定稿不得修改 (int32 → int64 视为新字段)
```

---

## 第二章 · spine.proto —— 32D 海胆快照

### 2.1 消息结构

```protobuf
message SpineSnapshot {
  string global_uid              = 1;   // 双链唯一绑定锚点 (23 字符)
  string dna_root_id             = 2;   // 向后兼容: 旧版根 ID
  string dialog_group_id         = 3;   // 对话藤蔓组 ID
  string location_fingerprint    = 4;   // 128-bit 区位指纹 (hex 编码)
  string timestamp               = 5;   // ISO8601
  repeated string scene_tags     = 6;   // 场景标签

  repeated SpineEntry entries    = 10;  // 32 个维度条目

  repeated CrossDimWarning cross_dim_warnings = 20;
  SafetyVerdict safety_verdict   = 30;

  VitalSigns vital_signs         = 40;
  string overall_health_level    = 41;
  float  overall_deviation       = 42;

  string crc32                   = 50;
  string encoder_version         = 51;
}
```

### 2.2 单维条目

```protobuf
message SpineEntry {
  uint32 dim_id        = 1;   // 1-32
  string dim_key       = 2;   // 维度英文键名
  float  value_raw     = 3;   // [-1.0, 1.0], float32 ← 🔴 精度锁定
  string intensity     = 4;   // low | medium | high | extreme
  string sensation_label = 5;

  // 医学对标
  string medical_metric_name = 10;
  float  medical_value       = 11;
  string medical_unit        = 12;
  float  medical_baseline    = 13;
  float  deviation           = 14;

  // 器官状态
  string organ_name          = 20;
  map<string, float> organ_metrics = 21;

  string evidence_text   = 30;
  repeated uint32 sibling_dims = 31;
}
```

### 2.3 D32 生命体征

```protobuf
message VitalSigns {
  float heart_rate         = 1;   // 静息心率 (次/分)
  float blood_pressure_sys = 2;   // 收缩压 (mmHg)
  float blood_pressure_dia = 3;   // 舒张压 (mmHg)
  float cortisol_avg       = 4;   // 全天平均皮质醇 (μg/dL)
  float pleasure_hormone_avg = 5; // 综合愉悦激素均值 (pg/mL)
}
```

### 2.4 安全校验结果

```protobuf
message SafetyVerdict {
  bool   passed            = 1;
  uint32 danger_count      = 2;
  uint32 risk_count        = 3;
  string overall_level     = 4;
  string reject_reason     = 5;
  repeated Violation violations = 6;
}
```

---

## 第三章 · token.proto —— 壳肉语义单元

### 3.1 消息结构

```protobuf
message FleshContainer {
  string global_uid       = 1;
  string raw_text         = 2;   // 原始对话文本 (完整)
  repeated SemanticToken tokens = 3;
  repeated EntityGene entity_genes = 4;

  string locus_path       = 10;
  string l0_code          = 11;
  string branch_id        = 12;
  repeated string scene_tags = 13;

  string crc32            = 20;
  string encoder_version  = 21;
}
```

### 3.2 最小语义单元

```protobuf
message SemanticToken {
  string global_uid       = 1;
  string dna_root_id      = 2;
  uint32 seq_idx          = 3;   // 在海胆内的序号 (从 0 递增)

  string token_text       = 10;
  uint32 char_offset      = 11;
  uint32 char_length      = 12;

  string locus_path       = 20;
  string l0_code          = 21;
  string branch_id        = 22;
  uint32 seq_pos          = 23;
  string leaf_zone        = 24;
  string ref              = 25;

  repeated uint32 entity_gene_indices = 30;
  bytes  context_offset   = 40;

  string crc32            = 50;
}
```

### 3.3 实体基因

```protobuf
message EntityGene {
  string name             = 1;
  string type             = 2;   // person | place | event | emotion | object | self
  string allele           = 3;   // 原始文本片段
  string phenotype        = 4;   // enhance | conflict | neutral
  string knowledge_type   = 5;   // private | family | world
}
```

---

## 第四章 · zvec_entry.proto —— 知识库条目

### 4.1 消息结构

```protobuf
message ZvecEntry {
  string resource_id      = 1;
  string global_uid       = 2;
  string dna_root_id      = 3;

  string source           = 10;
  string source_type      = 11;  // txt | md | pdf | docx | conversation | family_graph
  string source_name      = 12;

  string l0_raw           = 20;
  string l1_facts         = 21;
  string l2_summary       = 22;
  string l3_profile       = 23;

  string classification   = 30;
  bool   classification_pending = 31;

  bytes  scene_label      = 40;
  repeated string scene_tags = 41;

  string interaction_type = 50;
  float  impression_score = 51;
  string last_recalled_at = 52;

  int64  created_at       = 60;
  int64  updated_at       = 61;

  string crc32            = 70;
}
```

---

## 第五章 · CRC32 校验规范

### 5.1 计算范围

CRC32 在编码时计算——在所有字段填充完毕后、序列化写入存储之前。校验范围是除 `crc32` 字段本身外的所有字段。

### 5.2 算法

```
CRC32 多项式: 0xEDB88320 (IEEE 802.3 标准)
初始值:       0xFFFFFFFF
输入:         序列化后的 Protobuf 二进制字节 (不含 crc32 字段)
输出:         8 位十六进制字符串 (如 "a1b2c3d4")
```

### 5.3 校验时机

```
编码时: Transcoder.encode() → 计算 CRC32 → 写入 crc32 字段 → 序列化
解码时: Transcoder.decode() → 反序列化 → 重新计算 CRC32 → 对比 crc32 字段
        不一致 → FATAL: 数据完整性损坏, 拒绝入库
        一致   → 通过, 正常入库
```

---

## 第六章 · 两阶段通信方案

### 6.1 阶段 1 (当前 → P3)：JSON-line 过渡

```
适用场景: 天权 RPC 工程参数传输 (文件路径、任务描述、工作流ID)
不适用: 32D 向量传输 (JSON number 精度不足)

协议: JSON-line (每行一个 JSON 对象, \n 分隔)
字段: 使用 proto 定义的字段名, 但以 JSON 格式编码

优势:
  - 无编译依赖, 不需要 protoc
  - 人类可读, 方便调试
  - 工程参数全部是字符串/整数, 无精度问题

限制:
  - 32D float32 可能尾数丢失 (JSON number = IEEE 754 double, 转 float32 有截断)
  - 无 CRC32 自动校验
  - 无强类型约束
```

### 6.2 阶段 4 (P4 切换)：Protobuf 二进制

```
适用场景: 全系统全类型数据传输

协议: Protobuf 二进制编码
编译: protoc 从 .proto 源文件生成 Python (protobuf) + TypeScript (protobufjs) 代码

优势:
  - float32 精度保证 (Protobuf float = IEEE 754 single precision)
  - 内置 CRC32 校验
  - 强类型契约, 字段编号锁定
  - 编码后体积比 JSON 小 30-50%

切换要求:
  - 所有 BLOB 字段从 JSON 文本改为 Protobuf 二进制
  - 存量数据批量重新编码
  - P3 阶段完成前, 不切换
```

### 6.3 切换条件

```
全部满足才切换:
  ✅ 三套 .proto 文件已通过两端编译测试
  ✅ CRC32 校验在两端的 encode/decode 往返测试通过 (100% 通过率)
  ✅ 现存所有海胆的 JSON BLOB 已迁移为 Protobuf BLOB
  ✅ 瑶光端已产出真实 location_fingerprint (不再全 0)
```

---

## 第七章 · Transcoder 接口契约

### 7.1 编码接口

```typescript
// TypeScript 侧 (wenstar-cc)
class Transcoder {
  // 编码: JS 对象 → Protobuf BLOB
  encodeSpine(snapshot: SpineSnapshotLike): Buffer;
  encodeToken(container: FleshContainerLike): Buffer;
  encodeZvec(entry: ZvecEntryLike): Buffer;

  // 解码: Protobuf BLOB → JS 对象
  decodeSpine(buffer: Buffer): SpineSnapshotLike;
  decodeToken(buffer: Buffer): FleshContainerLike;
  decodeZvec(buffer: Buffer): ZvecEntryLike;

  // 校验
  computeCRC32(buffer: Buffer): string;      // 返回 8 位 hex
  verifyCRC32(buffer: Buffer, expected: string): boolean;
}
```

### 7.2 Python 侧等价接口

```python
class Transcoder:
    def encode_spine(self, snapshot: dict) -> bytes: ...
    def encode_token(self, container: dict) -> bytes: ...
    def encode_zvec(self, entry: dict) -> bytes: ...

    def decode_spine(self, buffer: bytes) -> dict: ...
    def decode_token(self, buffer: bytes) -> dict: ...
    def decode_zvec(self, buffer: bytes) -> dict: ...

    def compute_crc32(self, buffer: bytes) -> str: ...
    def verify_crc32(self, buffer: bytes, expected: str) -> bool: ...
```

### 7.3 编码 → 解码 往返测试

```
约束: 任意数据 encode → decode → 逐字段比对 → 完全一致
      包括 float32: encode(0.1234567) → decode → 0.1234567 (7 位有效数字不丢失)
      CRC32: encode(+crc) → decode → verify → true
```

---

## 第八章 · BLOB 存储规范

### 8.1 存储位置

| 数据 | 表 | 列 | 格式 |
|------|-----|-----|------|
| 32D 语义快照 | `state_spines` | `dna_branch` | Protobuf 二进制 (spine.SpineSnapshot) |
| 壳肉容器 | `memories` | (新增 `flesh_blob`) | Protobuf 二进制 (token.FleshContainer) |
| 知识库条目 | `knowledge_base` | (新增 `zvec_blob`) | Protobuf 二进制 (zvec_entry.ZvecEntry) |
| 路由戳列表 | `atom_address_timeline` | `route_stamp_list` | Protobuf 二进制 (RouteStamp 数组) |

### 8.2 不应存储为 BLOB 的字段

以下字段保持在关系列中，不做 Protobuf 编码——以便 SQL 直接查询：

```
state_spines.global_uid
state_spines.dimension_id
state_spines.value          ← 冗余, 方便 SQL 直接过滤
atom_address_timeline.global_uid
atom_address_timeline.absolute_timestamp
atom_address_timeline.time_slice_tag
```

---

## 附录 A · 编译脚本示例

```bash
#!/bin/bash
# proto/compile.sh — 从 .proto 源文件生成 Python + TypeScript 代码

PROTO_DIR="wenstar_os/common/proto"
OUT_TS="wenstar-cc/src/transcoder/generated"
OUT_PY="wenstar_os/common/proto/generated"

# TypeScript (protobufjs)
pbjs -t static-module -w commonjs \
  -o "$OUT_TS/proto.js" \
  "$PROTO_DIR/spine.proto" "$PROTO_DIR/token.proto" "$PROTO_DIR/zvec_entry.proto"
pbts -o "$OUT_TS/proto.d.ts" "$OUT_TS/proto.js"

# Python (protoc)
protoc -I="$PROTO_DIR" --python_out="$OUT_PY" \
  "$PROTO_DIR/spine.proto" "$PROTO_DIR/token.proto" "$PROTO_DIR/zvec_entry.proto"
```

## 附录 B · 变更记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-07-12 | V1.0 | 初版。三套 proto 消息定义、CRC32 规范、两阶段通信方案、BLOB 存储规范 |
