# 瑶光全域客观世界演算规范 V1.0

> **文档编号**：WS-SPEC-YAOGUANG-001  
> **版本**：V1.0  
> **最后更新**：2026-07-09  
> **适用对象**：瑶光客观世界演算开发团队  
> **核心原则**：输出纯量化客观参数，无任何主观情绪体感

---

## 一、底层通信约束

1. **输出纯量化客观参数**：所有输出为可量化数值，无主观情绪、无体感描述
2. **D1–D32 逐条客观演算规则**：每条维度基于物理/生理/人文客观规则输出
3. **无主观情绪、无体感**：不产生快乐/痛苦/焦虑等主观感受
4. **接收太虚解锁指令**：动态新增场景/生理/人文规则库
5. **32 维客观快照上行打包**：标准化协议上传太虚境

---

## 二、五大演算单元

### 2.1 自然时空单元

**职责**：演算时间、季节、气象、昼夜节律、天体运行等纯自然规律

| 参数 | 演算规则 | 输出区间 |
|------|---------|---------|
| 当前时间 | 系统时钟 | ISO 8601 |
| 季节相位 | 根据日期推算春/夏/秋/冬 | 0.0~4.0 |
| 气温 | 根据场景+季节+地域规则 | -20~50 ℃ |
| 日照时长 | 根据纬度+季节演算 | 0~24 h |
| 天气类型 | 随机加权 + 季节约束 | 晴/阴/雨/雪/风 |

### 2.2 空间建模单元

**职责**：演算场景空间布局、区位属性、物理距离

| 参数 | 演算规则 | 输出区间 |
|------|---------|---------|
| 场景类型 | 根据场景 ID 查规则库 | home/office/outdoor/public |
| 空间面积 | 场景预设值 | m² |
| 人流密度 | 场景类型 + 时间段规则 | 0.0~1.0 |
| 噪音水平 | 场景预设 + 时间修正 | 20~100 dB |
| 光照照度 | 场景+天气+时间 | 0~100000 lux |

### 2.3 人体生理规则单元

**职责**：演算标准人体在给定环境下的客观生理指标范围

| 参数 | 演算规则 | 输出区间 |
|------|---------|---------|
| 标准静息心率 | 年龄/性别/健康基线 | 55~90 bpm |
| 标准血压区间 | 年龄基线 | 收缩压 100~140 mmHg |
| 标准皮质醇曲线 | 昼夜节律（晨高夜低） | 5~25 μg/dL |
| 标准代谢率 BMR | Mifflin-St Jeor 公式 | 1200~2500 kcal |
| 标准睡眠需求 | 年龄基线 7~9 h | 小时 |

### 2.4 人文社交单元

**职责**：演算社交规则、礼仪规范、人际关系客观约束

| 参数 | 演算规则 |
|------|---------|
| 社交距离 | 关系类型 + 场合 → 客观距离 |
| 交谈礼仪 | 场合 + 关系等级 → 正式程度 |
| 家庭角色期望 | 文化预设 + 家庭结构 |
| 职场层级关系 | 组织结构 + 职级 |
| 公共场合行为准则 | 场合类型 → 行为约束集 |

### 2.5 资源拓展单元

**职责**：管理世界解锁、场景扩容、新规则注册

- **世界解锁申请**：接收太虚境拓展指令 → 新增场景、生理规则、人文规则库
- **场景扩容**：在空间建模单元注册新区位
- **规则注册**：在人体生理/人文社交单元新增规则集

---

## 三、D1–D32 逐条客观演算规则

### D1 骨骼肌肉・体能负荷（客观）

- **演算输入**：当日活动量（步数/运动时长/劳动强度）、睡眠质量
- **客观输出**：标准乳酸阈值 1.0 mmol/L，肌力基线值
- **扩容解锁**：新增运动类型 → 注册新的肌群负荷曲线

### D2 躯体疼痛・不适感知（客观）

- **演算输入**：外伤/炎症事件、慢性病史、活动强度
- **客观输出**：标准 VAS 疼痛预期区间
- **规则**：无外部伤害事件时默认 VAS=0

### D3–D31（类似规则，每种输出纯客观标准值/区间）

### D32 全域统筹总控（客观）

- **演算输入**：D1–D31 客观参数汇总 + 瑶灵主观对照
- **客观输出**：
  - 标准心率区间
  - 标准血压区间
  - 全天皮质醇标准曲线
  - 综合健康等级参考

---

## 四、接收太虚解锁指令规范

```typescript
interface WorldUnlockCommand {
    command_id: string;
    command_type: 'add_scene' | 'add_physiology_rule' | 'add_social_rule' | 'expand_parameter';
    payload: {
        scene_id?: string;
        scene_type?: string;
        rules?: Record<string, unknown>;
        parameters?: Record<string, number>;
    };
    timestamp_ms: number;
}
```

## 五、32 维客观快照上行规范

### 5.1 6D 环境感知快照（轻量通道）

瑶光第一层「自然时空」优先输出轻量 6D 快照，毫秒级刷新，C 端展示为"环境体感卡片"：

```typescript
interface YaoguangEnv6D {
    temperature_c: number;       // 温度 (℃)，区间 -20 ~ 50
    noise_db: number;            // 环境噪音 (dB)，区间 20 ~ 100
    light_lux: number;           // 光照照度 (lux)，区间 0 ~ 100000
    crowd_density: number;       // 人流密度 (0.0 ~ 1.0, 0=无人 1=极度拥挤)
    urgency: number;             // 时间紧迫度 (0.0 ~ 1.0, 0=完全宽松 1=极度紧迫)
    circadian_shift: number;     // 昼夜节律偏移量 (0.0=正常, -1.0=严重颠倒)
}
```

6D 快照由 `wf_objective_env_sample` 静态流水线产生，输入 D8/D24/D25/D26 四维原始信号，经感知滤波归一化后输出。作为 32 维全量快照的前置轻量通道，环境数据优先到达太虚境，确保场景上下文在 32 维海胆快照生成前已就绪。

### 5.2 32 维完整客观快照

```typescript
interface YaoguangUpstream {
    dna_root_id: string;
    timestamp_ms: number;
    objective: {
        d1_muscle_fatigue_standard: number;
        d2_pain_vas_standard: number;       // 默认 0
        d3_nerve_arousal_standard: number;  // 标准放松态 35%
        d4_hormones_standard: {
            cortisol_curve: number[];        // 24h 标准曲线
            dopamine_baseline: number;
            serotonin_baseline: number;
        };
        d5_pheromone_baseline: number;
        d6_bmr_standard: number;
        d7_heal_rate_standard: number;       // 乳酸清除 1.2 mmol/h
        d8_env_comfort_standard: number;
        // ... D9–D32 类似
        d32_vital_signs_standard: {
            heart_rate: { min: 60, max: 72, standard: 66 };
            blood_pressure: { systolic: { standard: 115 }, diastolic: { standard: 73 } };
            cortisol_daily_avg: { standard: 14 };
            joy_hormone_avg: { standard: 115 };
        };
    };
}
```

---

> **配套文档**：[产品白皮书](../01-产品白皮书/WenStar-OS-三体全域仿生个人世界白皮书-V1.0.md) | [工程蓝皮书](../02-工程蓝皮书/WS-ARCH-32D-MEM-工程蓝皮书-最终修订版.md) | [太虚运算规范](C-太虚境Hermes天权中枢运算规范-V1.0.md) | [通信对照表](../04-配套统一标准/32维三体双向通信总对照表.md)
