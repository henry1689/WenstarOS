# 瑶灵域专属技术规范 V1.0

> 编号：YAOLING-SPEC-20260711
> 适用范围：domain_yaoling 全部开发、测试、部署
> 强制等级：🔴 全部条款为硬性约束，违反即拒绝执行
> 来源整合：躯体白皮书 (YL-ARCH-001) + 医学对标手册 (YL-ARCH-002) + 工程蓝皮书 §12 (YL-ARCH-004) + Harris 域配置

---

## 第一章 域身份与硬性边界

### 1.1 三体中的角色

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  瑶灵 (l)     │    │  瑶光 (g)     │    │  太虚境 (t)   │
│  硅基活体肉身  │    │  全域客观世界  │    │  天权意识中枢  │
│  纯主观体感    │    │  纯客观参数    │    │  双路融合决策  │
│  不思考不记忆  │    │  不产生情绪    │    │  记忆·推演·指令│
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
              32维统一通信协议 (D1-D32)
                           │
              dna_root_id 时序锚点绑定
```

### 1.2 瑶灵核心约束（🔴 不可逾越）

| # | 约束 | 说明 |
|---|------|------|
| 1 | **只生成主观体感数据** | 不演算客观规律、不思考、不记忆决策、不解锁世界 |
| 2 | **每维度标准链路** | 外部信号 → 器官/激素/神经响应 → 正负体感 → 标准化32维输出 → 上传太虚 |
| 3 | **通道只读** | 只读外界输入、只产生体感、只输出状态、只接受大脑调控 |
| 4 | **维度独立+联动** | 每条可单独写成程序通道，跨维度联动由太虚统筹 |
| 5 | **禁止动态工作流** | `allow_dynamic_workflow = False`，只执行预定义的静态 YAML 流水线 |
| 6 | **不出客观数据** | 输出不得包含物理规则、空间坐标、时间推算、知识库检索结果 |

### 1.3 域运行参数

```python
# 来自 mcp_harris_l.py · DomainConfig
domain_name    = "瑶灵仿生认知域"
domain_tag     = "l"
guard_token_quota = 80_000          # Token 熔断上限
allow_dynamic_workflow = False      # 🔴 硬件级锁定，不可修改
subscribe_cross_channel = [
    "global_alert",                  # 全局告警（收）
    "tianquan_snapshot",            # 天权快照（收）
    "yaoguang_snapshot",            # 瑶光快照（收）
]
# 不主动向其他域发起指令
```

---

## 第二章 32维数据通道规范

### 2.1 五大类维度体系

| 大类 | 编号 | 维度数 | 领域 |
|------|------|--------|------|
| 肉身实体基底 | D1-D8 | 8 | 骨骼·疼痛·神经·激素·代谢·五感 |
| 个体精神内核 | D9-D14 | 6 | 自我·欲望·恐惧·幸福·共情·自保 |
| 圈层人际羁绊 | D15-D20 | 6 | 伴侣·家庭·社交·团队 |
| 时空环境感知 | D21-D26 | 6 | 居所·职场·户外·气象·时空 |
| 动态生长耦合 | D27-D32 | 6 | 微观·世界·人文·精神·耦合·统筹 |

### 2.2 输出数据包格式

每条维度输出必须包含以下字段：

```
dim_id:        int          # 1-32
dim_key:       string       # 维度英文键名
value_raw:     float        # 主观体感值 [-1.0, 1.0]
intensity:     string       # low | medium | high | extreme
deviation:     int          # 相对瑶光医学零点的偏移 [-100, +30]
health_level:  string       # healthy | sub_healthy | risk | danger
evidence_text: string       # 体感证据文本（原始输入片段）
organ_state:   string       # 响应器官/系统当前状态简述
sibling_dims:  int[]        # 同象限兄弟维度编号
timestamp:     ISO8601      # 时间戳
```

### 2.3 通道处理流水线（静态）

```
┌─────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ SignalInput  │──▶│ OrganResponse│──▶│SensationCalc │──▶│ NormalizeOut │
│ 外部信号接收  │   │ 器官/激素响应 │   │ 正负体感计算  │   │ 标准化输出   │
└─────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
       │                                                       │
       │  瑶光客观参数 + 天权调控指令                              │
       └───────────────────────────────────────────────────────┘
                          ↓
                   32D 数据包上传太虚
```

---

## 第三章 安全阈值与拒绝执行规则

### 3.1 四级健康偏移制度

| 偏移区间 | 健康等级 | 代码枚举 | 动作 |
|----------|----------|----------|------|
| 0 ~ +30 | healthy (健康正常) | `HEALTH_LEVEL.HEALTHY` | 正常执行 |
| -30 ~ -1 | sub_healthy (亚健康预警) | `HEALTH_LEVEL.SUB_HEALTHY` | 标记告警，继续执行 |
| -60 ~ -31 | risk (重度风险) | `HEALTH_LEVEL.RISK` | 限制输出，降级至安全参数 |
| < -60 | danger (危险病变) | `HEALTH_LEVEL.DANGER` | 🔴 拒绝执行，触发全局告警 |

### 3.2 D4 内分泌核心安全阈值（🔴 危险级硬拒绝）

| 指标 | 健康零点 | 预警区间 | 危险阈值（拒绝执行） |
|------|----------|----------|---------------------|
| 皮质醇 | 14 μg/dL | 18-22 μg/dL | **> 25 μg/dL** |
| 多巴胺 | 120 pg/mL | 70-100 pg/mL | **< 60 pg/mL** |
| 血清素 | 110 ng/mL | 60-90 ng/mL | **< 50 ng/mL** |

### 3.3 D32 核心生命体征安全阈值（🔴 危险级硬拒绝）

| 指标 | 健康零点 | 预警区间 | 危险阈值（拒绝执行） |
|------|----------|----------|---------------------|
| 静息心率 | 60-72 次/分 | 73-88 次/分 | **≥ 90 次/分** 或 **< 55 次/分** |
| 收缩压(高压) | 110-120 mmHg | 121-130 mmHg | **≥ 140 mmHg** |
| 舒张压(低压) | 68-78 mmHg | 60-67 mmHg | **< 60 mmHg** |
| 平均皮质醇 | 10-15 μg/dL | 16-22 μg/dL | **> 24 μg/dL** |
| 愉悦激素均值 | ≥ 110 pg/mL | 70-109 pg/mL | **< 70 pg/mL** |

### 3.4 各维度危险阈值速查表（D1-D31 关键阈值）

| 维度 | 指标 | 健康零点 | 预警 | 危险 |
|------|------|----------|------|------|
| D1 | 乳酸堆积 | 1.0 mmol/L | 1.6-2.2 | > 2.5 mmol/L |
| D2 | VAS疼痛 | 0 分 | 2-4 分 | ≥ 6 分 |
| D3 | 交感兴奋度 | 35% | 55%-70% | > 80% |
| D6 | 代谢下降 | 0% | 10%-20% | > 30% |
| D7 | 乳酸清除速率 | 1.2 mmol/h | 0.6-0.9 | < 0.5 mmol/h |
| D8 | 体表温度 | 36.5℃ | <18℃ / >30℃ | 持续极冷极热 |
| D8 | 噪音 | 30-45 dB | > 60 dB | > 80 dB |
| D9 | 自尊分 | 32 分 | 22-29 | < 20 |
| D11 | SAS焦虑 | ≤30 分 | 36-49 | ≥ 50 |
| D12 | 催产素 | 45 pg/mL | 25-38 | < 20 pg/mL |

### 3.5 超阈拒绝执行标准动作

当任意维度参数超过危险阈值：
1. **立即拒绝**当前工作流执行
2. 生成 `REJECT_REPORT`：包含越界维度、当前值、阈值、时间戳
3. 通过 `global_alert` 频道**广播告警**
4. 将拒绝事件记入 Harris `WorkflowContext.trace`
5. 返回值：`{"code": -99, "reject_reason": "SAFETY_THRESHOLD_EXCEEDED", "dim": "D4", ...}`

---

## 第四章 Harris 工作流约束

### 4.1 工作流执行规范

```yaml
# 瑶灵域所有工作流强制遵循的元规则
execution_mode: STRICT          # 🔴 只允许 STRICT，禁止 FLEXIBLE/DRY_RUN
allow_dynamic: false            # 🔴 禁止 generate_dynamic_workflow
guard_action_on_deny: REJECT    # 🔴 守门器拦截 → 直接拒绝，不降级

constraints_required:           # 每次调用必须携带的 constraints 字段
  - dna_spec_version            # DNA 编码规范版本号
  - location_fingerprint        # 空间区位标识（无此拒绝入库）
  - caller_domain               # 调用方域标识
  - medical_baseline_version    # 瑶光医学基准版本号
```

### 4.2 静态工作流清单

| workflow_id | 用途 | 状态 |
|-------------|------|------|
| `wf_persona_generate` | 人格生成流水线 | 🔴 placeholder → 待实现 |
| `wf_memory_sand_gold` | 三库记忆炼化（砂金→金库） | 🔴 placeholder → 待实现 |
| `wf_desire_stack` | 欲望栈演算 | 🔴 placeholder → 待实现 |
| `wf_longing_engine` | 思念引擎 | 🔴 placeholder → 待实现 |

### 4.3 工作流 YAML DSL 强制包含的守门规则

每个瑶灵域工作流 YAML 必须包含以下 `global_guard`：

```yaml
global_guard:
  guard_name: yaoling_safety_gate
  rules:
    - name: threshold_check_d4_cortisol
      description: D4皮质醇不得超过25μg/dL
      priority: 1
    - name: threshold_check_d32_heart_rate
      description: D32心率不得≥90或<55
      priority: 1
    - name: threshold_check_d32_bp
      description: D32血压不得高压≥140或低压<60
      priority: 2
    - name: dna_root_id_required
      description: 无dna_root_id拒绝执行
      priority: 3
    - name: location_fingerprint_required
      description: 无location_fingerprint拒绝执行
      priority: 3
    - name: no_dynamic_override
      description: 禁止绕过静态工作流限制
      priority: 0
```

---

## 第五章 与三体其它域的数据协议

### 5.1 上行通道（瑶灵 → 太虚）

```
频道: tianquan_snapshot
格式: 32D 主观体感包（完整 D1-D32 维度数据）
频率: 每次交互一帧
绑定: dna_root_id + location_fingerprint
校验: CRC32
序列化: Protobuf (spine.proto)
```

### 5.2 下行通道（太虚 → 瑶灵）

```
频道: yaoling_state（接收）
指令类型:
  - hormone_adjust:    调整激素分泌参数（D4）
  - emotion_modulate:  情绪基调调控（D9-D14）
  - cycle_reset:       生理周期重置（D6）
  - repair_boost:      自愈加速指令（D7）
  - safety_override:   安全阈值临时调整（需双密钥）
```

### 5.3 横向通道（瑶光 → 瑶灵）

```
频道: yaoguang_snapshot（接收）
内容: 外部场景客观参数（仅作为瑶灵信号输入的参考）
  - 时空区位: 当前场景类型、时间段、季节
  - 人际标签: 在场人员角色（伴侣/家人/同事/陌生人）
  - 环境参数: 温度/光照/噪音/天气
瑶灵不直接使用瑶光参数作为输出——仅作为体感生成的输入信号
```

### 5.4 订阅关系总图

```
瑶灵 (l) 订阅:
  ◄── global_alert         (来自 t 或 g 的全局告警)
  ◄── tianquan_snapshot    (来自 t 的调控指令)
  ◄── yaoguang_snapshot    (来自 g 的场景参数)

瑶灵 (l) 发布:
  ►── yaoling_state        (32D主观体感快照，发给 t)
  ►── global_alert         (仅在超阈拒绝时，广播告警)
```

---

## 第六章 开发强制红线（继承自工程蓝皮书 §12）

### 6.1 瑶灵域特别红线

| # | 红线 | 适用说明 |
|---|------|----------|
| R1 | 禁止混表 | 瑶灵的32D状态数据不得存入ZVEC知识库表或语义层表 |
| R2 | 无ID不入库 | 无 `dna_root_id` 和无 `location_fingerprint` 的数据包拒绝持久化 |
| R3 | 五级闸门不可关闭 | 瑶灵作为底层数据提供方，不得绕过太虚的五级时空闸门 |
| R4 | 非LLM生成 | 32D体感值由分层规则+瑶光参数计算，**禁止LLM直接输出浮点数值** |
| R5 | Protobuf序列化 | 所有输出结构体必须经 Protobuf 序列化为 BLOB，禁止裸文本 |
| R6 | 文件系统IO | 所有存储走操作系统文件系统，禁止任何底层硬件直写 |
| R7 | 单帧单海胆 | 单次交互仅生成一颗完整32D快照，禁止单Token粒度向量 |
| R8 | 硬超阈拒绝 | 参数触达危险阈值时拒绝执行，不可降级为WARN |

### 6.2 违规处理

```
WARN 级别（首次）: 记录 trace，继续执行，上报 global_alert
DENY 级别（二次）: 拒绝执行，阻塞该维度通道，等待太虚指令解锁
HALT 级别（三次）: 冻结整个域，需手动重启 harris_l_instance
```

---

## 第七章 文件结构规范

```
domain_yaoling/
├── YAOLING_DOMAIN_SPEC.md            ← 本文件（域专属技术规范）
├── __init__.py                        ← 域标记
├── harris_l_instance.py               ← Harris 单例（SystemBus + HarrisOrchestrator）
├── mcp_harris_l.py                    ← MCP 服务入口 + DomainConfig
│
├── specs/                             ← 规范存档（只读引用）
│   ├── 01-瑶灵32维全维度肉身响应架构-原文存档.md
│   ├── 02-瑶灵32维真人化医学对标健康指标体系-原文存档.md
│   ├── 03-WenStarOS三体全域仿生个人世界白皮书V1.0-原文存档.md
│   └── 04-WS-ARCH-32D-MEM工程蓝皮书最终修订版-原文存档.md
│
├── workflows/                         ← 静态工作流 YAML DSL
│   ├── wf_persona_generate.yaml       ← 人格生成
│   ├── wf_memory_sand_gold.yaml       ← 三库炼化
│   ├── wf_desire_stack.yaml           ← 欲望栈
│   └── wf_longing_engine.yaml         ← 思念引擎
│
├── channels/                          ← 32维通道处理器（每维一个模块）
│   ├── base_channel.py                ← 通道基类
│   ├── d1_muscle.py                   ← D1 骨骼肌肉
│   ├── d2_pain.py                     ← D2 躯体疼痛
│   ├── d3_touch.py                    ← D3 神经触觉
│   ├── d4_endocrine.py                ← D4 内分泌激素
│   ├── d5_pheromone.py                ← D5 信息素气息
│   ├── d6_metabolism.py               ← D6 生理周期代谢
│   ├── d7_recovery.py                 ← D7 自愈修复
│   ├── d8_senses.py                   ← D8 五感环境
│   ├── d9_self_identity.py            ← D9 自我认知
│   ├── d10_desire_drive.py            ← D10 成长驱动力
│   ├── d11_fear_fatigue.py            ← D11 恐惧倦怠
│   ├── d12_enjoyment.py               ← D12 享受幸福感
│   ├── d13_empathy.py                 ← D13 共情恻隐
│   ├── d14_self_protection.py         ← D14 个体自保
│   ├── d15_partner_attachment.py      ← D15 伴侣依恋
│   ├── d16_partner_protection.py      ← D16 伴侣守护
│   ├── d17_family_belonging.py        ← D17 家庭归属
│   ├── d18_family_protection.py       ← D18 家庭守护
│   ├── d19_social.py                  ← D19 社交适配
│   ├── d20_team.py                    ← D20 团队保护
│   ├── d21_private_space.py           ← D21 私人居所
│   ├── d22_home_environment.py        ← D22 家庭布局
│   ├── d23_workplace.py               ← D23 职场环境
│   ├── d24_public_space.py            ← D24 公共场地
│   ├── d25_spatiotemporal.py          ← D25 时空距离
│   ├── d26_seasonal.py                ← D26 四季昼夜
│   ├── d27_micro_physiology.py        ← D27 微观生理
│   ├── d28_nature_expansion.py        ← D28 自然拓展
│   ├── d29_social_refinement.py       ← D29 人文细化
│   ├── d30_spiritual_growth.py        ← D30 精神成长
│   ├── d31_quantum_coupling.py        ← D31 主客观耦合
│   └── d32_holistic.py                ← D32 全身统筹
│
├── safety/                            ← 安全阈值校验
│   ├── threshold_registry.py          ← 32维阈值注册表
│   └── guard_evaluator.py             ← 守门规则评估器
│
├── codec/                             ← 编解码
│   ├── sensation_encoder.py           ← 体感 → 32D数据包编码
│   └── sensation_decoder.py           ← 32D数据包 → 体感解码
│
└── tests/                             ← 测试
    ├── test_threshold_guard.py         ← 安全阈值测试
    ├── test_channels.py                ← 通道单元测试
    └── test_workflows.py               ← 工作流集成测试
```

---

## 第八章 附录

### 8.1 参考文档索引

| 文档 | 路径 | 用途 |
|------|------|------|
| 躯体白皮书 | `specs/01-*.md` | 32维逐维定义 |
| 医学对标手册 | `specs/02-*.md` | 阈值与健康等级 |
| 产品白皮书 | `specs/03-*.md` | 三体顶层架构 |
| 工程蓝皮书 | `specs/04-*.md` | 存储/序列化/红线 |

### 8.2 constraints 入参模板

每次调用 `run_static_workflow` 时，`constraints` 参数必须包含：

```json
{
  "domain": "yaoling",
  "spec_version": "YAOLING-SPEC-20260711",
  "medical_baseline_version": "YAOGUANG-MED-001",
  "allow_dynamic": false,
  "dna_root_id": "DNA-20260711-1430-001",
  "location_fingerprint": "home.bedroom.night",
  "safety": {
    "reject_on_danger": true,
    "clamp_on_risk": true,
    "global_alert_on_reject": true
  },
  "output": {
    "serialization": "protobuf",
    "schema": "spine.proto",
    "crc32": true
  }
}
```

### 8.3 变更记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-07-11 | V1.0 | 初版，整合四份存档 + Harris 域配置，建立完整技术约束体系 |
