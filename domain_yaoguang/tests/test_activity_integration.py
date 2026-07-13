"""test_activity_integration.py — 活动模型+通道+场景全链路验证"""
import sys, os, json, asyncio
sys.path.insert(0, 'D:/wenstar/wenstar_os')
os.chdir('D:/wenstar/wenstar_os/domain_yaoguang')
sys.path.insert(0, '..')

async def main():
    from workflow_executor import YaoguangWorkflowExecutor
    from mcp_harris_g import YaoguangMCP, yaoguang_config, yaoguang_executor
    from harris_g_instance import harris_g_global
    from activity_model import (
        WALK_ROUTES, DRIVE_ROUTES, build_typical_workday, compute_daily_fatigue,
        TrafficCondition, WeatherImpact, SCENE_ENV_BASELINES,
        ActivityType, WalkRoute, DriveRoute, DailyActivity,
    )

    ex = YaoguangWorkflowExecutor()
    all_pass = 0
    all_fail = 0

    def check(condition, label):
        nonlocal all_pass, all_fail
        if condition:
            all_pass += 1
        else:
            all_fail += 1
            print(f'  FAIL: {label}')

    # ============================================================
    # A: 工作日开车通勤 (中度拥堵)
    # ============================================================
    print('=== A: Workday drive (moderate traffic) ===')
    snap = ex.run_full_snapshot(
        dna_root_id='DNA-A',
        location_fingerprint='office:guangming_office:desk_a2',
        temporal_context={'time_of_day': 'morning', 'season': 'summer'},
        interpersonal_labels=['colleague'],
        activity_context=dict(use_apartment=False, work_hours=9.0,
            commute_traffic='moderate', weather='clear',
            evening_walk=True, sleep_hours=6.5),
    )
    d = snap.to_dict()
    d25 = d['objective']['d25']
    d23 = d['objective']['d23']

    check(d25['context']['commute_km'] == 30.0, 'A1: commute_km=30')
    check(d25['context']['commute_min'] >= 55, f'A2: moderate≥55min got {d25["context"]["commute_min"]}')
    check(d25['context']['urgency'] >= 0.5, f'A3: urgency {d25["context"]["urgency"]} (moderate traffic with 30min buffer)')
    check(d23['context']['drive_fatigue'] > 0.1, f'A4: drive_fatigue {d23["context"]["drive_fatigue"]}')
    print(f'  D25: {d25["context"]["commute_km"]}km/{d25["context"]["commute_min"]}min urgency={d25["context"]["urgency"]}')
    print(f'  D23: cortisol={d23["standard_value"]} fatigue={d23["context"]["drive_fatigue"]}')
    print('  [OK]')

    # ============================================================
    # B: 公寓步行上班 (零通勤)
    # ============================================================
    print()
    print('=== B: Apartment walk (no commute) ===')
    snap_b = ex.run_full_snapshot(
        dna_root_id='DNA-B',
        location_fingerprint='office:guangming_office:desk_a2',
        temporal_context={'time_of_day': 'morning'},
        activity_context=dict(use_apartment=True, work_hours=8.0,
            commute_traffic='free_flow', weather='clear',
            evening_walk=True, sleep_hours=7.5),
    )
    db = snap_b.to_dict()
    check(db['objective']['d25']['context'].get('commute_km', 0) <= 0.5, 'B1: near-zero commute')
    check(db['objective']['d25']['context']['urgency'] == 0.0, 'B2: zero urgency')
    check(db['objective']['d23']['context']['drive_fatigue'] == 0.0, 'B3: no drive fatigue')
    print('  [OK]')

    # ============================================================
    # C: 暴雨+严重拥堵回家
    # ============================================================
    print()
    print('=== C: Severe traffic + rain home ===')
    snap_c = ex.run_full_snapshot(
        dna_root_id='DNA-C',
        location_fingerprint='home:xinghai_mingcheng:entrance',
        temporal_context={'time_of_day': 'evening'},
        interpersonal_labels=['family'],
        activity_context=dict(use_apartment=False, work_hours=10.0,
            commute_traffic='severe', weather='rain_heavy',
            evening_walk=False, sleep_hours=6.0),
    )
    dc = snap_c.to_dict()
    check(dc['objective']['d25']['context']['commute_min'] >= 80, 'C1: severe≥80min')
    check(dc['objective']['d23']['standard_value'] >= 18, 'C2: cortisol high')
    print(f'  D25: {dc["objective"]["d25"]["context"]["commute_min"]}min')
    print(f'  D23: cortisol={dc["objective"]["d23"]["standard_value"]}')
    print('  [OK]')

    # ============================================================
    # D: 周末在家
    # ============================================================
    print()
    print('=== D: Weekend home ===')
    snap_d = ex.run_full_snapshot(
        dna_root_id='DNA-D',
        location_fingerprint='home:xinghai_mingcheng:living_sofa',
        environmental_params={'temperature': 28, 'noise_db': 32, 'light_lux': 25000},
        temporal_context={'time_of_day': 'afternoon'},
        interpersonal_labels=['family'],
    )
    dd = snap_d.to_dict()
    check(len(dd['objective']) == 32, 'D1: 32dims')
    check(4 <= dd['objective']['d4']['standard_value'] <= 12, 'D2: afternoon cortisol')
    print(f'  D4: {dd["objective"]["d4"]["standard_value"]} D22: {dd["objective"]["d22"]["standard_value"]}')
    print('  [OK]')

    # ============================================================
    # E: 步行物理参数
    # ============================================================
    print()
    print('=== E: Walk/Drive physics ===')
    wr = WALK_ROUTES.get('xinghai_mingcheng→荷兰花卉小镇')
    check(wr is not None, 'E1: walk route exists')
    check(5.5 <= wr.walk_time_min <= 7.0, f'E2: 500m~6min got {wr.walk_time_min}')
    check(wr.step_count >= 600, f'E3: steps≥600 got {wr.step_count}')
    print(f'  500m walk: {wr.walk_time_min}min {wr.energy_kcal}kcal {wr.step_count}steps')

    dr = DRIVE_ROUTES.get('home→office')
    check(dr is not None, 'E4: drive route exists')
    normal = dr.drive_time_min(TrafficCondition.FREE_FLOW, WeatherImpact.CLEAR)
    heavy_rain = dr.drive_time_min(TrafficCondition.HEAVY, WeatherImpact.RAIN_HEAVY)
    severe_typhoon = dr.drive_time_min(TrafficCondition.SEVERE, WeatherImpact.TYPHOON)
    check(normal == 45.0, f'E5: normal=45 got {normal}')
    check(heavy_rain >= 70, f'E6: heavy rain≥70 got {heavy_rain}')
    check(severe_typhoon >= 100, f'E7: severe typhoon≥100 got {severe_typhoon}')
    print(f'  30km drive: normal={normal} heavy+rain={heavy_rain} severe+typhoon={severe_typhoon}')

    # 疲劳计算
    acts, drives, walks = build_typical_workday(
        work_hours=9, commute_traffic=TrafficCondition.HEAVY,
        weather=WeatherImpact.RAIN_LIGHT, use_apartment=False)
    fat = compute_daily_fatigue(acts, drives, walks, sleep_hours=6.5)
    check(fat.driving_fatigue > 0.2, f'E8: drive fatigue {fat.driving_fatigue}')
    check(fat.composite_fatigue > 0.2, f'E9: composite fatigue {fat.composite_fatigue}')
    print(f'  Fatigue: energy={fat.total_energy_kcal}kcal physical={fat.physical_fatigue} mental={fat.mental_fatigue} drive={fat.driving_fatigue} composite={fat.composite_fatigue}')
    print(f'  Rest={fat.recommended_rest_min}min lactate={fat.lactate_estimate}mmol/L')
    print('  [OK]')

    # ============================================================
    # F: MCP pipeline with activity_context
    # ============================================================
    print()
    print('=== F: MCP pipeline ===')
    bridge = YaoguangMCP(yaoguang_config, harris_g_global, yaoguang_executor)
    tool = bridge.app._tool_manager._tools.get('run_static_workflow')
    r = await tool.fn('wf_perception_filter', 'monday', {
        'dna_root_id': 'DNA-MCP-F',
        'location_fingerprint': 'office:guangming_office:desk_a2',
        'temporal_context': {'time_of_day': 'morning'},
        'interpersonal_labels': ['colleague'],
        'activity_context': dict(use_apartment=False, work_hours=9,
            commute_traffic='heavy', weather='rain_light',
            evening_walk=True, sleep_hours=6.5),
    })
    df = json.loads(r)
    check(df['code'] == 0, 'F1: code=0')
    check(len(df['snapshot']['objective']) == 32, 'F2: 32dims')
    d25f = df['snapshot']['objective']['d25']
    check(d25f['context']['commute_km'] == 30.0, 'F3: commute 30km')
    check(d25f['context']['commute_min'] >= 60, f'F4: heavy≥60min got {d25f["context"]["commute_min"]}')
    print(f'  MCP D25: {d25f["context"]["commute_min"]}min via heavy traffic')
    print('  [OK]')

    print()
    print(f'===== {all_pass} PASS, {all_fail} FAIL =====')
    assert all_fail == 0, f'{all_fail} checks failed'

asyncio.run(main())
