"""
health_report.py — 瑶灵健康报告生成器
======================================
综合多场景采样，输出月度体检表格式。
"""

import json, sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from channels import create_all_channels, SignalInput
from safety.threshold_registry import get_threshold, ThresholdLevel
from safety.guard_evaluator import GuardAction, evaluate_dimension, evaluate_d32_vital_sign

# ── 采样场景 ──
SCENARIOS = [
    ("晚间伴侣陪伴", "晚上好，回家看到你好开心，抱抱~", ["partner"],
     dict(hours_sitting=5, work_duration_hours=8, sleep_hours=7, hours_since_last_chat=2),
     dict(time_of_day="evening", season="summer", weather="clear", location="bedroom"),
     dict(temperature=22, noise_db=35, light_lux=200)),
    ("正常午后休息", "下午好，今天天气不错，在家休息放松", ["family"],
     dict(hours_sitting=2, work_duration_hours=4, sleep_hours=8, hours_since_last_chat=1),
     dict(time_of_day="afternoon", season="spring", weather="clear", location="home"),
     dict(temperature=24, noise_db=30, light_lux=400)),
    ("工作时段", "今天任务挺多的，不过还行，慢慢做", [],
     dict(hours_sitting=6, work_duration_hours=7, sleep_hours=7, hours_since_last_chat=3),
     dict(time_of_day="afternoon", season="summer", weather="cloudy", location="office"),
     dict(temperature=25, noise_db=50, light_lux=500)),
]

# ── 维度的核心医学指标键 ──
MED_KEY = {
    1: "lactate", 2: "vas_score", 3: "sns_excitation_%", 4: "cortisol",
    5: "sweat_cortisol", 6: "bmr_decline_%", 7: "lactate_clearance", 8: "noise_db",
    9: "esteem_score", 10: "neurotransmitter_decline_%", 11: "sas_score", 12: "oxytocin",
    13: "mirror_neuron_activation", 14: "alertness_baseline",
    15: "oxytocin", 16: "cortisol", 17: "security_score", 18: "cortisol",
    19: "cortisol_rise", 20: "stress_hormone",
    21: "cortisol_drop", 22: "recovery_efficiency_%", 23: "cortisol", 24: "sns_excitation_%",
    25: "cortisol", 26: "melatonin",
    27: "fluctuation_amplitude", 28: "dopamine_decline_%",
    29: "neurotransmitter_decline_%", 30: "serotonin_decline_%",
    31: "harmony_score", 32: "health_index",
}


def sample_all():
    """多场景采样，返回 {dim_id: [values]} 和 vitals 汇总。"""
    dim_vals = {d: [] for d in range(1, 33)}
    vital_vals = {"heart_rate": [], "blood_pressure_sys": [], "blood_pressure_dia": [],
                  "cortisol_avg": [], "pleasure_hormone_avg": [], "health_index": []}

    for label, text, labels, dur, tctx, env in SCENARIOS:
        ch = create_all_channels()
        sig = SignalInput(source_channel="yaoguang_snapshot", raw_input_text=text,
                          interpersonal_labels=labels, environmental_params=env,
                          temporal_context=tctx, duration_context=dur)
        results = {}
        for dim_id, channel in ch.items():
            results[dim_id] = channel.process(sig)
        d32_state = ch[32].compute_holistic(results)

        for dim_id in range(1, 33):
            r = results.get(dim_id)
            if not r: continue
            if dim_id == 32:
                # D32 uses compute_holistic, not process()
                dim_vals[32].append(d32_state.metrics.get("health_index", 75.0))
                continue
            key = MED_KEY.get(dim_id, "")
            if key:
                val = r.organ_state.metrics.get(key, 0.0)
                dim_vals[dim_id].append(val)

        m = d32_state.metrics
        for vk in vital_vals:
            if vk in m:
                vital_vals[vk].append(m[vk])

    # 平均
    avg_dims = {}
    for d in range(1, 33):
        vals = dim_vals[d]
        avg_dims[d] = round(sum(vals) / len(vals), 2) if vals else 0.0

    avg_vitals = {}
    for vk, vals in vital_vals.items():
        avg_vitals[vk] = round(sum(vals) / len(vals), 1) if vals else 0.0

    return avg_dims, avg_vitals


def level_icon(level: str) -> str:
    return {"healthy": "[OK]", "sub_healthy": "[~!]", "risk": "[!!]", "danger": "[XX]"}.get(level, "[??]")


def level_label(level: str) -> str:
    return {"healthy": "健康", "sub_healthy": "亚健康", "risk": "风险", "danger": "危险"}.get(level, "未知")


def generate():
    avg_dims, avg_vitals = sample_all()

    print("=" * 72)
    print("  瑶灵 · 32D 全身健康月度体检报告")
    print("  采样场景: 伴侣晚间 / 正常午后 / 工作时段 (3场景均值)")
    print("=" * 72)

    # ── D32 核心生命体征 ──
    print()
    print("  >>> D32 核心生命体征 (优先展示) <<<")
    print(f"  ┌─────────────────┬──────────┬──────────────┬────────┐")
    print(f"  │ 指标             │ 当前值    │ 正常参考区间  │ 判定   │")
    print(f"  ├─────────────────┼──────────┼──────────────┼────────┤")

    vitals_def = [
        ("heart_rate", "静息心率", "次/分", (60, 72), (55, 90)),
        ("blood_pressure_sys", "收缩压(高压)", "mmHg", (110, 120), (90, 140)),
        ("blood_pressure_dia", "舒张压(低压)", "mmHg", (68, 78), (60, 90)),
        ("cortisol_avg", "全天平均皮质醇", "ug/dL", (10, 15), (5, 24)),
        ("pleasure_hormone_avg", "愉悦激素均值", "pg/mL", (110, 200), (70, 250)),
    ]
    for vk, label, unit, (lo, hi), (dlo, dhi) in vitals_def:
        val = avg_vitals.get(vk, 0)
        if val < dlo or val > dhi:
            verdict = "!! 危险"
        elif val < lo or val > hi:
            verdict = "~  偏离"
        else:
            verdict = "O  正常"
        print(f"  │ {label:15s} │ {val:6.1f} {unit:4s} │ {lo}-{hi}{' ' + unit if len(unit)<5 else unit:6s} │ {verdict:6s} │")
    print(f"  └─────────────────┴──────────┴──────────────┴────────┘")

    # ── 健康指数 ──
    hi = avg_vitals.get("health_index", 75)
    hi_level = "健康" if hi >= 65 else "亚健康" if hi >= 45 else "风险" if hi >= 30 else "危险"
    print(f"\n  综合健康指数: {hi:.0f}/100  [{hi_level}]")

    # ── D1-D31 逐维报告 ──
    print()
    print("  >>> D1-D31 逐维体检 <<<")
    print(f"  {'维度':4s} {'指标值':>10s} {'健康参考':>12s} {'偏移等级':8s} 通俗解读")

    categories = [
        ("肉身实体基底 D1-D8", range(1, 9)),
        ("个体精神内核 D9-D14", range(9, 15)),
        ("圈层人际羁绊 D15-D20", range(15, 21)),
        ("时空环境感知 D21-D26", range(21, 27)),
        ("动态生长耦合 D27-D32", range(27, 33)),
    ]

    for cat_name, dim_range in categories:
        print(f"\n  [{cat_name}]")
        for dim_id in dim_range:
            val = avg_dims.get(dim_id, 0)
            t = get_threshold(dim_id)
            level = t.evaluate(val)
            icon = level_icon(level.value)
            label = level_label(level.value)
            tip = t.get_tip(level)
            clean_tip = tip.replace("⚠", "!").replace("️", "")

            # 格式化区间
            lo, hi = getattr(t, f"{level.value}_range")
            if lo is not None and hi is not None:
                rng = f"[{lo}-{hi}]"
            elif lo is not None:
                rng = f"[>{lo}]"
            elif hi is not None:
                rng = f"[<{hi}]"
            else:
                rng = "--"

            print(f"  D{dim_id:02d} {val:8.1f}{t.medical_unit:4s} {t.medical_baseline:6.0f}{t.medical_unit:4s} {icon:4s} {label:4s} {clean_tip[:40]}")


    # ── 汇总建议 ──
    print()
    print("=" * 72)
    hr = avg_vitals.get("heart_rate", 66)
    cort = avg_vitals.get("cortisol_avg", 14)
    pleas = avg_vitals.get("pleasure_hormone_avg", 110)
    bp_s = avg_vitals.get("blood_pressure_sys", 115)
    bp_d = avg_vitals.get("blood_pressure_dia", 73)

    issues = []
    if hr < 60: issues.append("静息心率偏低，可能存在副交感过度或体虚")
    if hr > 85: issues.append("静息心率偏高，存在心动过速倾向")
    if cort > 18: issues.append("全天皮质醇偏高，长期压力积累，需减少工作负荷、增加放松时间")
    if cort < 8: issues.append("皮质醇偏低，可能存在肾上腺疲劳")
    if pleas < 80: issues.append("愉悦激素不足，缺少正向情感滋养，建议增加陪伴和兴趣爱好")
    if bp_s > 130: issues.append("收缩压偏高，与工作压力、久坐相关")
    if bp_d < 65: issues.append("舒张压偏低，可能供血不足、体虚")

    if not issues:
        print("  [综合判定] 整体状态良好，各系统运行正常。继续保持当前作息和陪伴节奏。")
    else:
        print("  [综合判定]")
        for i, issue in enumerate(issues, 1):
            print(f"    {i}. {issue}")

    print()
    print("  --- 报告生成: 瑶灵32D体感引擎 ---")
    print("=" * 72)


if __name__ == "__main__":
    generate()
