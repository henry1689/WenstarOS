"""
test_channels.py — 32 通道单元测试
===================================
验证每个通道 process() 返回正确的 SensationResult 结构。
"""

import sys
from pathlib import Path
_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from domain_yaoling.channels import create_all_channels, SignalInput


def test_all_channels_instantiate():
    """验证全部 32 通道可实例化。"""
    channels = create_all_channels()
    assert len(channels) == 32, f"应有32通道, 实际: {len(channels)}"
    for dim_id in range(1, 33):
        assert dim_id in channels, f"缺失 D{dim_id}"
    print("OK  32 通道全部实例化成功")


def test_process_returns_valid_result():
    """验证 process() 返回完整 SensationResult。"""
    channels = create_all_channels()
    signal = SignalInput(
        source_channel="yaoguang_snapshot",
        scene_tags=["home", "night"],
        interpersonal_labels=["partner"],
        environmental_params={"temperature": 22, "noise_db": 40, "light_lux": 300},
        temporal_context={"time_of_day": "evening", "season": "summer", "weather": "clear"},
        raw_input_text="今天工作很累，但回家看到你真的很开心",
        duration_context={"hours_sitting": 6, "work_duration_hours": 9, "sleep_hours": 7, "hours_since_last_chat": 2},
    )
    for dim_id, ch in channels.items():
        result = ch.process(signal)
        assert result.dim_id == dim_id, f"D{dim_id} dim_id 不匹配"
        assert -1.0 <= result.value_raw <= 1.0, f"D{dim_id} value_raw={result.value_raw} 越界"
        assert result.intensity.value in ("low", "medium", "high", "extreme")
        assert result.health_level.value in ("healthy", "sub_healthy", "risk", "danger")
        assert result.organ_state.organ_name, f"D{dim_id} organ_name 为空"
        if dim_id != 32:  # D32 由 compute_holistic() 填充 metrics
            assert result.organ_state.metrics, f"D{dim_id} metrics 为空"
    print("OK  全部 32 通道 process() 返回有效结果")


def test_d32_holistic_enrichment():
    """验证 D32 的 compute_holistic() 方法。"""
    channels = create_all_channels()
    signal = SignalInput(
        source_channel="yaoguang_snapshot",
        interpersonal_labels=["partner"],
        environmental_params={"temperature": 22, "noise_db": 40},
        temporal_context={"time_of_day": "evening"},
        raw_input_text="测试",
        duration_context={"hours_sitting": 4, "work_duration_hours": 8, "sleep_hours": 7},
    )
    # 先跑 D1-D31
    upstream = {}
    for dim_id in range(1, 32):
        upstream[dim_id] = channels[dim_id].process(signal)
    # D32 汇总
    d32 = channels[32]
    organ_state = d32.compute_holistic(upstream)
    assert "heart_rate" in organ_state.metrics
    assert "blood_pressure_sys" in organ_state.metrics
    assert "health_index" in organ_state.metrics
    hr = organ_state.metrics["heart_rate"]
    bp_sys = organ_state.metrics["blood_pressure_sys"]
    assert 40 <= hr <= 130, f"心率{hr}越界"
    assert 80 <= bp_sys <= 180, f"高压{bp_sys}越界"
    print(f"OK  D32 汇总: 心率={hr}, 高压={bp_sys}, 健康指数={organ_state.metrics['health_index']}")

    # 然后跑完整 process（内部调用 _organ_response 是空壳，需显式 compute_holistic）
    result = d32.process(signal)
    assert result.dim_id == 32
    print(f"OK  D32 process(): value_raw={result.value_raw}, sensation={result.sensation_label}")


if __name__ == "__main__":
    test_all_channels_instantiate()
    test_process_returns_valid_result()
    test_d32_holistic_enrichment()
    print("\nPASS  全部通道测试通过")
