"""
test_channels.py — 瑶光 32 维客观通道单元测试
"""
import sys
from pathlib import Path
_PARENT = Path(__file__).resolve().parent.parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from channels import create_all_objective_channels, ObjCategory


def test_all_32_channels():
    """验证 32 通道全部可实例化 + 计算输出。"""
    channels = create_all_objective_channels()
    assert len(channels) == 32, f"Expected 32 channels, got {len(channels)}"

    env = {"temperature": 22, "noise_db": 40, "light_lux": 300, "crowd_density": 0.1}
    temporal = {"time_of_day": "afternoon", "season": "summer", "weather": "clear"}
    duration = {"hours_sitting": 4, "work_duration_hours": 8, "sleep_hours": 7,
                "hours_since_last_chat": 2, "activity_minutes": 15, "buffer_min": 60}
    interpersonal = ["partner", "family"]

    errors = []
    for dim_id in range(1, 33):
        ch = channels[dim_id]
        try:
            result = ch.process(env, temporal, duration, interpersonal,
                               dna_root_id="DNA-20260712-0000-TEST",
                               location_fingerprint="home.livingroom.sofa",
                               timestamp_ms=1720771200000)
            assert result.dim_id == dim_id, f"D{dim_id} dim_id mismatch: {result.dim_id}"
            assert result.standard_unit, f"D{dim_id} missing unit"
            assert result.standard_range_low <= result.standard_range_high, \
                f"D{dim_id} bad range: [{result.standard_range_low}, {result.standard_range_high}]"

            # 客观铁律：标准值应在参考区间 50% ~ 150% 范围内
            lo = result.standard_range_low
            hi = result.standard_range_high
            margin = (hi - lo) * 0.5 if hi > lo else abs(hi) * 0.5
            if result.standard_value < lo - margin:
                errors.append(f"D{dim_id}: {result.standard_value} << [{lo},{hi}]")
            if result.standard_value > hi + margin:
                errors.append(f"D{dim_id}: {result.standard_value} >> [{lo},{hi}]")

        except Exception as e:
            errors.append(f"D{dim_id}: {e}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        assert False, f"{len(errors)} errors"
    print(f"[PASS] All 32 channels: computed OK, no forbidden words in output")

    # 大类分布
    cats = {}
    for ch in channels.values():
        c = ch.cfg.category.value
        cats[c] = cats.get(c, 0) + 1
    print(f"[INFO] Category distribution: {cats}")
    assert cats.get("physical_body", 0) == 8, f"D1-D8 should be 8, got {cats.get('physical_body', 0)}"
    assert cats.get("inner_spirit", 0) == 6
    assert cats.get("social_bonds", 0) == 6
    assert cats.get("spatiotemporal", 0) == 6
    assert cats.get("dynamic_growth", 0) == 6


def test_d4_endocrine_day_night():
    """D4 内分泌: 早晚皮质醇差符合生理节律。"""
    channels = create_all_objective_channels()
    env = {"temperature": 22, "noise_db": 40, "light_lux": 300}
    dur = {"sleep_hours": 7}

    morning = channels[4].process(env, {"time_of_day": "morning"}, dur, [])
    night = channels[4].process(env, {"time_of_day": "night"}, dur, [])

    assert morning.standard_value > night.standard_value, \
        f"D4 morning cortisol ({morning.standard_value}) should > night ({night.standard_value})"
    print(f"[PASS] D4 circadian rhythm: morning={morning.standard_value} night={night.standard_value}")


def test_d26_melatonin_cycle():
    """D26 褪黑素: 夜间 > 白天。"""
    channels = create_all_objective_channels()
    env = {}; dur = {}
    day = channels[26].process(env, {"time_of_day": "afternoon"}, dur, [])
    night = channels[26].process(env, {"time_of_day": "night"}, dur, [])

    assert night.standard_value > day.standard_value, \
        f"D26 night melatonin ({night.standard_value}) should > day ({day.standard_value})"
    print(f"[PASS] D26 melatonin cycle: day={day.standard_value} night={night.standard_value}")


def test_d32_vital_signs():
    """D32 核心生命体征标准: 心率/血压在正常范围。"""
    channels = create_all_objective_channels()
    d32 = channels[32].process({}, {"time_of_day": "afternoon"}, {}, [])

    hr = d32.evidence_context.get("heart_rate", 0)
    bp_sys = d32.evidence_context.get("blood_pressure_sys", 0)
    bp_dia = d32.evidence_context.get("blood_pressure_dia", 0)

    assert 55 <= hr <= 90, f"D32 heart_rate {hr} out of range [55,90]"
    assert 100 <= bp_sys <= 140, f"D32 bp_sys {bp_sys} out of range [100,140]"
    assert 60 <= bp_dia <= 85, f"D32 bp_dia {bp_dia} out of range [60,85]"
    print(f"[PASS] D32 vital signs: HR={hr} BP={bp_sys}/{bp_dia}")


def test_env_6d_snapshot():
    """6D 环境快照端到端。"""
    from workflow_executor import YaoguangWorkflowExecutor
    ex = YaoguangWorkflowExecutor()
    env6 = ex.run_env_sample(
        dna_root_id="DNA-TEST-001",
        location_fingerprint="office.floor3.desk_a2",
        environmental_params={"temperature": 25, "noise_db": 55, "light_lux": 800, "crowd_density": 0.4},
        temporal_context={"time_of_day": "afternoon"},
    )
    d = env6.to_dict()
    assert 20 <= d["temperature_c"] <= 30
    assert 30 <= d["noise_db"] <= 70
    assert d["crowd_density"] == 0.4
    print(f"[PASS] 6D env snapshot: temp={d['temperature_c']} noise={d['noise_db']} crowd={d['crowd_density']}")


def test_full_32d_snapshot():
    """全 32 维快照端到端。"""
    from workflow_executor import run_env_snapshot
    result = run_env_snapshot(
        dna_root_id="DNA-20260712-2000-E2E",
        location_fingerprint="home.bedroom.night",
        environmental_params={"temperature": 22, "noise_db": 35, "light_lux": 200, "crowd_density": 0.0},
        temporal_context={"time_of_day": "evening", "season": "summer", "weather": "clear"},
        duration_context={"hours_sitting": 2, "work_duration_hours": 6, "sleep_hours": 7.5,
                         "hours_since_last_chat": 1, "buffer_min": 120},
        interpersonal_labels=["partner"],
    )
    assert result["dna_root_id"] == "DNA-20260712-2000-E2E"
    assert len(result["objective"]) == 32
    assert result["env_6d"]["temperature_c"] == 22
    assert result["crc32"]
    assert len(result["crc32"]) == 16

    # 验证 D4 在傍晚的皮质醇
    d4 = result["objective"]["d4"]
    assert 4.0 <= d4["standard_value"] <= 10.0, f"D4 evening cortisol {d4['standard_value']} out of range"

    print(f"[PASS] Full 32D snapshot: {len(result['objective'])} dims, CRC32={result['crc32']}")
    print(f"  D4 cortisol={d4['standard_value']} {d4['standard_unit']}")
    print(f"  D32 health_index={result['objective']['d32']['standard_value']}")
    print(f"  D12 oxytocin={result['objective']['d12']['standard_value']} (partner present)")


if __name__ == "__main__":
    test_all_32_channels()
    test_d4_endocrine_day_night()
    test_d26_melatonin_cycle()
    test_d32_vital_signs()
    test_env_6d_snapshot()
    test_full_32d_snapshot()
    print("\n===== ALL 6 TESTS PASS =====")
