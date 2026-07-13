"""test_unlock_dispatcher.py — 通用世界解锁技能全场景验证"""
import sys, os, json, asyncio
os.chdir('D:/wenstar/wenstar_os/domain_yaoguang')
sys.path.insert(0, '.'); sys.path.insert(0, '..')

PASS = 0; FAIL = 0

def check(cond, label):
    global PASS, FAIL
    if cond: PASS += 1
    else: print(f'  FAIL: {label}'); FAIL += 1

def test_env_matrix():
    """测试环境影响矩阵的32维计算"""
    print('=== TEST 1: 环境影响矩阵 (晴朗夏日午后·家) ===')
    from environmental_context import compute_env_impact_matrix, EnvContext, TimeOfDay, Season, Weather, DayType, SceneType
    env = EnvContext(
        time_of_day=TimeOfDay.AFTERNOON, hour=14, season=Season.SUMMER,
        weather=Weather.CLEAR, outdoor_temp_c=30.0, humidity_pct=65.0,
        scene_type=SceneType.HOME, indoor=True, indoor_temp_c=25.0,
        noise_db=32.0, light_lux=1500, crowd_density=0.05, day_type=DayType.WEEKEND,
    )
    m = compute_env_impact_matrix(env)
    check(len(m.impacts) == 32, f't1a: 32 impacts, got {len(m.impacts)}')
    check(abs(m.impacts[8].net_correction - 0.35) < 0.2, f't1b: D8 comfort ~0.35 got {m.impacts[8].net_correction}')
    check(m.impacts[12].net_correction > 0.1, f't1c: D12 enjoyment positive got {m.impacts[12].net_correction}')
    check(m.impacts[4].net_correction < 0.05, f't1d: D4 afternoon cortisol mild got {m.impacts[4].net_correction}')
    check(m.daylight_hours > 13, f't1e: summer daylight>13h got {m.daylight_hours}')
    print(f'  daylight={m.daylight_hours}h D4={m.impacts[4].net_correction} D8={m.impacts[8].net_correction} D12={m.impacts[12].net_correction}')
    print('  [OK]')

    print()
    print('=== TEST 2: 环境影响矩阵 (暴雨深夜·办公室) ===')
    env2 = EnvContext(
        time_of_day=TimeOfDay.NIGHT, hour=22, season=Season.SUMMER,
        weather=Weather.RAIN_HEAVY, outdoor_temp_c=25.0, humidity_pct=90.0,
        scene_type=SceneType.OFFICE, indoor=True, indoor_temp_c=24.0,
        noise_db=55.0, light_lux=200, crowd_density=0.05, day_type=DayType.WORKDAY,
    )
    m2 = compute_env_impact_matrix(env2)
    check(m2.impacts[11].net_correction < 0, f't2a: D11 night+rain increases fear, got {m2.impacts[11].net_correction}')
    check(m2.impacts[15].net_correction > 0, f't2b: D15 bad weather increases attachment need, got {m2.impacts[15].net_correction}')
    check(m2.impacts[26].net_correction <= 0.0, f't2c: D26 rain+night ≤0 (summer offsets rain), got {m2.impacts[26].net_correction}')
    check(m2.impacts[16].net_correction > 0, f't2d: D16 night increases worry, got {m2.impacts[16].net_correction}')
    print(f'  D11={m2.impacts[11].net_correction} D15={m2.impacts[15].net_correction} D16={m2.impacts[16].net_correction} D26={m2.impacts[26].net_correction}')
    print('  [OK]')

def test_dispatcher():
    """测试解锁调度器核心流程"""
    from unlock_dispatcher import handle_unlock_event, UnlockEventType

    # ── 场景A：场景解锁——周末晴天下午在家 ──
    print()
    print('=== TEST 3: 解锁——周末晴天下午·家 ===')
    r = handle_unlock_event(
        event_type="scene_unlock",
        dna_root_id="DNA-T3-WEEKEND-HOME",
        event_description="周末下午两点，阳光明媚，在家休息",
        location_fingerprint="home:xinghai_mingcheng:living_sofa",
        scene_type="home", time_of_day="afternoon",
        weather="clear", season="summer", day_type="weekend",
        outdoor_temp_c=32.0,
        interpersonal_labels=["family"],
    )
    check(r['code'] == 0, 't3a: code=0')
    check(len(r['objective']) == 32, 't3b: 32dims')
    check(r['env_context']['daylight_hours'] > 13, 't3c: summer daylight')
    d4 = r['objective']['d4']
    d12 = r['objective']['d12']
    d17 = r['objective']['d17']
    check(d4['standard_value'] < 10, f't3d: afternoon cortisol={d4["standard_value"]}')
    check(d12['env_impact'] > 0, f't3e: enjoyment positive impact={d12["env_impact"]}')
    check(d17['env_impact'] > 0, f't3f: family belonging positive at home={d17["env_impact"]}')
    print(f'  D4_cort={d4["standard_value"]} D12_oxytocin={d12["standard_value"]} D17_belonging={d17["standard_value"]}')
    print(f'  env_6d={r["env_6d"]}')
    print(f'  crc32={r["crc32"]}')
    print('  [OK]')

    # ── 场景B：天气突变——台风暴雨，深夜在家 ──
    print()
    print('=== TEST 4: 解锁——台风暴雨深夜·家 ===')
    r2 = handle_unlock_event(
        event_type="weather_change",
        dna_root_id="DNA-T4-TYPHOON-NIGHT",
        event_description="深夜十点台风登陆，狂风暴雨，气温骤降",
        location_fingerprint="home:xinghai_mingcheng:living_sofa",
        scene_type="home", time_of_day="night", hour=22,
        weather="typhoon", season="summer", day_type="workday",
        outdoor_temp_c=20.0,
        extra_params={"humidity_pct": 95, "wind_speed_ms": 25},
        interpersonal_labels=["partner"],
    )
    check(r2['code'] == 0, 't4a: code=0')
    d8 = r2['objective']['d8']
    d11 = r2['objective']['d11']
    d16 = r2['objective']['d16']
    d26 = r2['objective']['d26']
    check(d26['env_impact'] <= 0.0, f't4b: typhoon negative/neutral on D26, got {d26["env_impact"]}')
    check(d16['env_impact'] >= 0, f't4c: partner worry in typhoon, got {d16["env_impact"]}')
    check(d11['standard_value'] >= 30, f't4d: SAS at least baseline in typhoon night, got {d11["standard_value"]}')
    print(f'  D8_env={d8["standard_value"]} D11_SAS={d11["standard_value"]} D26_season={d26["standard_value"]}')
    print(f'  noise={r2["env_context"]["noise_db"]}dB (typhoon)  wind={r2["env_context"]["wind_speed_ms"]}m/s')
    print('  [OK]')

    # ── 场景C：通勤——周一早高峰中度拥堵开车上班 ──
    print()
    print('=== TEST 5: 解锁——周一早高峰通勤上班 ===')
    r3 = handle_unlock_event(
        event_type="commute_mode",
        dna_root_id="DNA-T5-MON-COMMUTE",
        event_description="周一早晨8点，中度拥堵，开车从星海名城到光明办公室",
        location_fingerprint="office:guangming_office:desk_a2",
        scene_type="office", time_of_day="morning", hour=8,
        weather="clear", season="summer", day_type="workday",
        outdoor_temp_c=28.0,
        activity_context={
            "use_apartment": False, "work_hours": 9,
            "commute_traffic": "moderate", "sleep_hours": 6.5,
            "evening_walk": True,
        },
        interpersonal_labels=["colleague"],
    )
    check(r3['code'] == 0, 't5a: code=0')
    check(r3['activity_report'] is not None, 't5b: activity report present')
    ar = r3['activity_report']
    check(ar['composite_fatigue'] > 0.3, f't5c: fatigue from commute+work, got {ar["composite_fatigue"]}')
    check(ar['driving_fatigue'] > 0.1, f't5d: drive fatigue present')
    d25 = r3['objective']['d25']
    d23 = r3['objective']['d23']
    d1 = r3['objective']['d1']
    check(d25['context'].get('commute_km', 0) == 30.0, 't5e: commute 30km')
    check(d23['standard_value'] > 18, f't5f: work cortisol elevated, got {d23["standard_value"]}')
    print(f'  D25_commute={d25["context"].get("commute_time_min")}min D23_cortisol={d23["standard_value"]}')
    print(f'  Fatigue: composite={ar["composite_fatigue"]} drive={ar["driving_fatigue"]} rest={ar["recommended_rest_min"]}min')
    print(f'  Energy: {ar["total_energy_kcal"]}kcal')
    print('  [OK]')

    # ── 场景D：节假日——中秋夜晚户外赏月 ──
    print()
    print('=== TEST 6: 解锁——中秋夜晚户外赏月 ===')
    r4 = handle_unlock_event(
        event_type="holiday",
        dna_root_id="DNA-T6-MID-AUTUMN",
        event_description="中秋夜晚8点，晴朗，户外赏月，微风拂面",
        location_fingerprint="outdoor:qianhai_park:lakeside",
        scene_type="nature", time_of_day="evening", hour=20,
        weather="clear", season="autumn", day_type="holiday",
        outdoor_temp_c=24.0,
        extra_params={"humidity_pct": 50, "wind_speed_ms": 2},
        interpersonal_labels=["partner", "family"],
    )
    check(r4['code'] == 0, 't6a: code=0')
    d10 = r4['objective']['d10']
    d12 = r4['objective']['d12']
    d15 = r4['objective']['d15']
    d26 = r4['objective']['d26']
    check(d12['env_impact'] > 0.15, f't6b: holiday+outdoor+clear=high enjoyment, got {d12["env_impact"]}')
    check(d10['env_impact'] > 0.1, f't6c: outdoor+holiday=high exploration, got {d10["env_impact"]}')
    check(d15['env_impact'] > 0.05, f't6d: holiday+partner=attachment, got {d15["env_impact"]}')
    check(d26['env_impact'] > 0, f't6e: autumn clear evening positive seasonal, got {d26["env_impact"]}')
    print(f'  D10_desire={d10["standard_value"]} D12_enjoyment={d12["standard_value"]}')
    print(f'  D15_attach={d15["standard_value"]} D26_season={d26["standard_value"]}')
    print(f'  env_6d={r4["env_6d"]}')
    print('  [OK]')

    # ── 场景E：社交——大型会议 ──
    print()
    print('=== TEST 7: 解锁——大型会议 (高人流+长时间) ===')
    r5 = handle_unlock_event(
        event_type="social_event",
        dna_root_id="DNA-T7-MEETING",
        event_description="大型年度汇报会，30人参会，时长2小时，高压力",
        location_fingerprint="office:guangming_office:meeting_b",
        scene_type="office", time_of_day="morning", hour=10,
        weather="clear", season="summer", day_type="workday",
        crowd_density=0.8, noise_db_override=55.0,
        extra_params={"social_type": "meeting", "meeting_duration_h": 2.0},
        interpersonal_labels=["colleague"],
    )
    check(r5['code'] == 0, 't7a: code=0')
    d19 = r5['objective']['d19']
    d13 = r5['objective']['d13']
    d24 = r5['objective']['d24']
    check(d24['env_impact'] < 0, f't7b: crowd negative on D24, got {d24["env_impact"]}')
    check(d19['env_impact'] <= 0, f't7c: meeting social strain <=0, got {d19["env_impact"]}')
    check(d13['standard_value'] >= 0.4, f't7d: empathy baseline met, got {d13["standard_value"]}')
    print(f'  D19_social={d19["standard_value"]} D13_empathy={d13["standard_value"]} D24_public={d24["standard_value"]}')
    print('  [OK]')

    # ── 场景F：健康——运动后恢复 ──
    print()
    print('=== TEST 8: 解锁——晨跑后恢复 ===')
    r6 = handle_unlock_event(
        event_type="health_event",
        dna_root_id="DNA-T8-EXERCISE",
        event_description="早晨7点晨跑5公里回来，出汗疲惫，正在拉伸",
        location_fingerprint="home:xinghai_mingcheng:living_sofa",
        scene_type="home", time_of_day="morning", hour=7,
        weather="clear", season="summer", day_type="weekend",
        outdoor_temp_c=26.0,
        extra_params={"health_type": "exercise", "lactate_mmol_l": 2.2, "exercise_duration_min": 40},
        interpersonal_labels=["partner"],
    )
    check(r6['code'] == 0, 't8a: code=0')
    d1 = r6['objective']['d1']
    d7 = r6['objective']['d7']
    check(d1['standard_value'] >= 1.8, f't8b: lactate elevated post-exercise, got {d1["standard_value"]}')
    check(d7['standard_value'] > 1.2, f't8c: clearance activated >1.2, got {d7["standard_value"]}')
    print(f'  D1_lactate={d1["standard_value"]}mmol/L D7_clearance={d7["standard_value"]}mmol/h')
    print('  [OK]')

def test_mcp_integration():
    """通过MCP工具调用解锁技能"""
    print()
    print('=== TEST 9: MCP wf_world_unlock 工具调用 ===')
    from mcp_harris_g import YaoguangMCP, yaoguang_config, yaoguang_executor
    from harris_g_instance import harris_g_global

    async def run():
        bridge = YaoguangMCP(yaoguang_config, harris_g_global, yaoguang_executor)
        tool = bridge.app._tool_manager._tools.get('run_static_workflow')
        fn = tool.fn

        r = await fn('wf_world_unlock', 'winter night commute', {
            'dna_root_id': 'DNA-MCP-UNLOCK',
            'event_type': 'commute_mode',
            'location_fingerprint': 'home:xinghai_mingcheng:entrance',
            'scene_type': 'home', 'time_of_day': 'evening', 'hour': 18,
            'weather': 'rain_light', 'season': 'winter', 'day_type': 'workday',
            'outdoor_temp_c': 12.0,
            'crowd_density': 0.2,
            'activity_context': {
                'use_apartment': False, 'work_hours': 9,
                'commute_traffic': 'heavy', 'sleep_hours': 7.0,
                'evening_walk': False,
            },
            'interpersonal_labels': ['family'],
        })
        d = json.loads(r)
        global PASS, FAIL
        check(d['code'] == 0, 't9a: MCP code=0')
        check(len(d['objective']) == 32, 't9b: MCP 32dims')
        check(d['activity_report'] is not None, 't9c: MCP activity report')
        d26 = d['objective']['d26']
        check(d26['env_impact'] < 0, f't9d: winter evening negative seasonal, got {d26["env_impact"]}')
        print(f'  MCP D26_winter={d26["standard_value"]} D5_pheromone={d["objective"]["d5"]["standard_value"]}')
        print(f'  env_6d={d["env_6d"]}')
        print(f'  CRC={d["crc32"]}')
        print('  [OK]')

    asyncio.run(run())


test_env_matrix()
test_dispatcher()
test_mcp_integration()

print()
print(f'===== {PASS} PASS, {FAIL} FAIL =====')
assert FAIL == 0, f'{FAIL} checks failed'
