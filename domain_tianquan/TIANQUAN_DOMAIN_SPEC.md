# 天权域专属技术规范 V1.0

> 编号：TIANQUAN-SPEC-20260711
> 适用范围：domain_tianquan 全部开发、测试、部署
> 强制等级：🔴 全部条款为硬性约束，违反即拒绝执行
> 来源整合：白皮书 V1.0 §1-§8 + 工程蓝皮书 §1-§21 + DNA双螺旋编码体系

---

## 第一章 域身份与硬性边界

### 1.1 三体中的角色

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  天权 (t)     │    │  瑶灵 (l)     │    │  瑶光 (g)     │
│  中枢调度引擎  │    │  硅基肉身     │    │  感知采集     │
│  记忆·检索·决策│    │  纯主观体感    │    │  纯客观参数    │
│  DNA双螺旋编排 │    │  不思考不记忆  │    │  不产生情绪    │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
              32维统一通信协议 (D1-D32)
                           │
              global_bus_main (TCP :9100)
```

### 1.2 天权核心约束（🔴 不可逾越）

| # | 约束 | 说明 |
|---|------|------|
| 1 | **唯一中枢** | 天权是三体中唯一具备记忆存储、逻辑推演、决策下发能力的域 |
| 2 | **DNA双螺旋** | 所有记忆必须绑定语义螺旋链(32D) + 寻址结构螺旋链(GlobalUID) |
| 3 | **五级闸门不可关闭** | G1语义 → G2时空 → G3遗忘 → G4意图 → G5话题壁垒 |
| 4 | **32D永久固定** | 永不扩容/缩容，DNA双螺旋定稿红线第5条 |
| 5 | **Protobuf序列化** | 所有持久化结构体经 Transcoder 序列化，CRC32校验 |
| 6 | **禁止LLM直接输出向量** | 32D由分层规则映射，禁止LLM生成浮点数值 |
| 7 | **文件系统IO** | 所有存储走操作系统，禁止底层硬件直写 |
| 8 | **全局总线中枢** | 天权是唯一可向瑶灵/瑶光下发调控指令的域 |

### 1.3 域运行参数

```python
# 来自 mcp_harris_t.py · DomainConfig
domain_name    = "天权算力工程域"
domain_tag     = "t"
guard_token_quota = 120_000
allow_dynamic_workflow = True       # 允许动态生成工作流（仅限超大架构重构）
subscribe_cross_channel = [
    "global_alert",                  # 全局告警（收）
    "yaoling_state",                 # 瑶灵32D快照（收）
    "yaoguang_snapshot",            # 瑶光场景快照（收）
]
publish_to = [
    "tianquan_snapshot",            # 调控指令（发 → l）
    "yaoguang_snapshot",            # 感知采样调整（发 → g）
]
```

---

## 第二章 工程四大流水线

### 2.1 静态工作流清单

| workflow_id | 用途 | YAML | 状态 |
|-------------|------|------|------|
| `wf_code_review` | 多步骤代码审查（语法→架构→安全→性能） | wf_code_review.yaml | ✅ |
| `wf_arch_refactor` | 架构重构（影响面分析→方案设计→逐文件迁移→回归验证） | wf_arch_refactor.yaml | ✅ |
| `wf_sql_governance` | SQL治理（DDL审计→索引分析→数据迁移校验） | wf_sql_governance.yaml | ✅ |
| `wf_knowledge_organize` | 知识库整理（去重→分类→双链→摘要→归档） | wf_knowledge_organize.yaml | ✅ |

### 2.2 工作流执行规范

```yaml
execution_mode: STRICT          # 默认 STRICT
allow_dynamic: true             # 仅超大架构重构时使用 generate_dynamic_workflow
guard_action_on_deny: REJECT    # 守门器拦截 → 直接拒绝
max_retry_per_node: 2
total_timeout_seconds: 900      # 15分钟全局超时
```

### 2.3 工作流 YAML 强制包含的守门规则

每个天权域工作流 YAML 必须包含以下 `global_guard`：

```yaml
global_guard:
  guard_name: tianquan_engineering_gate
  rules:
    - name: impact_analysis_required
      description: 架构级修改必须先输出影响面报告
      priority: 0
    - name: no_destructive_without_backup
      description: 删除/迁移操作前必须确认备份存在
      priority: 1
    - name: coding_standard_compliance
      description: 输出代码必须通过 lint_checker 校验
      priority: 2
    - name: change_report_required
      description: 任何代码修改必须附带四段式变更报告
      priority: 2
    - name: regression_test_gate
      description: P0模块修改后必须执行回归测试
      priority: 3
```

---

## 第三章 工程模块规范

### 3.1 模块清单

| 模块 | 文件 | 功能 |
|------|------|------|
| 架构解析 | `modules/arch_parser.py` | 解析项目模块依赖图、识别循环依赖、计算耦合度 |
| SQL解析 | `modules/sql_parser.py` | DDL/DML 提取、表关系分析、索引审计 |
| 文档生成 | `modules/doc_generator.py` | 四段式变更报告、代码文档自动生成 |

### 3.2 架构解析器输入输出

```
输入: 项目根路径 + 忽略模式
处理: AST遍历 → 导入关系图 → 循环检测 → 耦合度评分
输出: ArchReport { modules, dependencies, cycles, coupling_scores, recommendations }
```

### 3.3 SQL解析器输入输出

```
输入: SQL文件路径 / SQL文本
处理: 词法分析 → DDL/DML分类 → 表关系提取 → 索引审计
输出: SQLReport { tables, indexes, foreign_keys, warnings, suggestions }
```

### 3.4 文档生成器输入输出

```
输入: diff_text + change_type + author
处理: 四段式模板填充 → Markdown渲染
输出: ChangeReport { summary, details, impact, verification }
```

---

## 第四章 编码规范校验器

### 4.1 校验维度

| 编号 | 规则 | 来源 |
|------|------|------|
| L1 | kebab-case 文件名 | dev-docs/04 |
| L2 | PascalCase 类名 | dev-docs/04 |
| L3 | camelCase 函数/变量 | dev-docs/04 |
| L4 | 无 console.log 残留 | dev-docs/04 |
| L5 | import 禁止循环依赖 | dev-docs/02 |
| L6 | 模块接口契约校验 | dev-docs/02 |
| L7 | DNA 红线禁止项检测 | 工程蓝皮书 §12 |
| L8 | 禁止硬编码密钥/Token | dev-docs/08 |

### 4.2 校验输出格式

```json
{
  "passed": true,
  "total_rules": 8,
  "violations": [],
  "warnings": [],
  "lint_duration_ms": 42
}
```

---

## 第五章 工程快照序列化

### 5.1 快照结构

```
EngineeringSnapshot {
  snapshot_id: str           # SNAP-{timestamp}-{hash6}
  project_root: str
  file_count: int
  module_graph: ArchReport
  sql_audit: Optional[SQLReport]
  change_log: List[ChangeReport]
  timestamp: ISO8601
  crc32: str
}
```

### 5.2 序列化格式

- Python dataclass → JSON → gzip → .snap 文件
- 快照目录: `<project_root>/.tianquan/snapshots/`
- 清理策略: 保留最近 30 个快照，更早的自动归档

---

## 第六章 与三体其它域的数据协议

### 6.1 下行通道（天权 → 瑶灵）

```
频道: tianquan_snapshot
指令类型:
  - hormone_adjust:    调整激素分泌参数
  - emotion_modulate:  情绪基调调控
  - cycle_reset:       生理周期重置
  - repair_boost:      自愈加速指令
  - safety_override:   安全阈值临时调整（需双密钥）
```

### 6.2 下行通道（天权 → 瑶光）

```
频道: yaoguang_snapshot
指令类型:
  - sample_config:     调整感知采样频率/精度
  - location_lock:     锁定/解锁空间区位追踪
  - scene_override:    手动设定场景标签
```

### 6.3 上行通道（瑶灵 → 天权）

```
频道: yaoling_state
内容: 32D 主观体感数据包
绑定: dna_root_id
```

### 6.4 上行通道（瑶光 → 天权）

```
频道: yaoguang_snapshot
内容: 场景客观参数（温度/光照/噪音/时空/在场人员）
```

---

## 第七章 文件结构规范

```
domain_tianquan/
├── TIANQUAN_DOMAIN_SPEC.md            ← 本文件
├── __init__.py
├── harris_t_instance.py               ← Harris 单例
├── mcp_harris_t.py                    ← MCP 入口 + DomainConfig
│
├── workflows/                         ← 静态工作流 YAML DSL
│   ├── wf_code_review.yaml           ← 代码审查
│   ├── wf_arch_refactor.yaml         ← 架构重构
│   ├── wf_sql_governance.yaml        ← SQL 规整
│   └── wf_knowledge_organize.yaml    ← 知识库整理
│
├── modules/                           ← 工程解析模块
│   ├── __init__.py
│   ├── arch_parser.py                ← 架构依赖解析
│   ├── sql_parser.py                 ← SQL DDL/DML 解析
│   └── doc_generator.py              ← 变更报告生成
│
├── validator/                         ← 编码规范校验
│   ├── __init__.py
│   └── lint_checker.py               ← 8 条规则逐文件扫描
│
├── codec/                             ← 工程快照序列化
│   ├── __init__.py
│   └── snapshot_codec.py             ← 快照编码/解码
│
└── tests/                             ← 测试
    ├── __init__.py
    ├── test_workflows.py             ← 工作流解析测试
    ├── test_modules.py               ← 模块单元测试
    └── test_validator.py             ← 校验器测试
```

---

## 第八章 附录

### 8.1 参考文档索引

| 文档 | 路径 | 用途 |
|------|------|------|
| 白皮书 | `../WenstarOSTianquan/WenStar_OS_天权三体全域仿生认知系统白皮书V1.0.md` | 产品世界观 |
| 蓝皮书 | `../WenstarOSTianquan/WS-ARCH-TIANQUAN-20260710_天权工程蓝皮书最终修订版.md` | 工程规范 |
| DNA编码 | `../WenstarOSTianquan/DNA双螺旋编码体系_最终定稿白皮书与工程蓝皮书.md` | 编码标准 |
| 开发计划书 | `../WenstarOSTianquan/dev-docs/01_天权开发总体计划书.md` | 里程碑 |

### 8.2 constraints 入参模板

```json
{
  "domain": "tianquan",
  "spec_version": "TIANQUAN-SPEC-20260711",
  "dna_root_id": "DNA-20260711-1430-001",
  "workflow_type": "code_review | arch_refactor | sql_governance | knowledge_organize",
  "project_root": "D:/wenstar/wenstar_os",
  "change_report_required": true,
  "backup_required": true
}
```

### 8.3 变更记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-07-11 | V1.0 | 初版，含四大流水线+三模块+校验器+快照序列化+三域协议 |
