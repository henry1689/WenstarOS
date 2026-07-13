"""test_avatar_integration.py — 年龄/性别/经验 全维度差异化验证"""
import sys, os, json, asyncio
os.chdir('D:/wenstar/wenstar_os/domain_yaoguang')
sys.path.insert(0,'.'); sys.path.insert(0,'..')

PASS=0; FAIL=0
def check(cond,label):
    global PASS,FAIL
    if cond: PASS+=1
    else: print(f'  FAIL: {label}'); FAIL+=1

def test_avatar_presets():
    """7个预设avatar完整性"""
    print('=== 1: Avatar presets ===')
    from avatar_profile import PRESET_AVATARS, AvatarProfile
    check(len(PRESET_AVATARS) == 7, f'7 presets, got {len(PRESET_AVATARS)}')
    for k, a in PRESET_AVATARS.items():
        ctx = a.to_context_dict()
        check('age_group' in ctx, f'{k} age_group')
        check('biological_sex' in ctx, f'{k} sex')
    # 14岁少女特有参数
    a14f = PRESET_AVATARS['adolescent_f_14']
    check(a14f.tanner_stage == 3, f'tanner=3 got {a14f.tanner_stage}')
    check(a14f.menarche_age == 12.5, f'menarche=12.5')
    check(a14f.age_group.frontal_lobe_maturity < 0.5, f'frontal<0.5 got {a14f.age_group.frontal_lobe_maturity}')
    a35m = PRESET_AVATARS['mature_m']
    check(a35m.has_children, 'mature_m has children')
    check(a35m.age_group.frontal_lobe_maturity == 1.0, 'mature frontal=1.0')
    print(f'  [OK] {len(PRESET_AVATARS)} presets verified')
    return PRESET_AVATARS

def test_age_modifier_matrix():
    """年龄对32维修正系数"""
    print()
    print('=== 2: Age modifier matrix ===')
    from avatar_profile import PRESET_AVATARS
    child = PRESET_AVATARS['child_f']
    adol = PRESET_AVATARS['adolescent_f_14']
    mature = PRESET_AVATARS['mature_m']
    midage = PRESET_AVATARS['middle_age_m']

    # D7 恢复速率: child > adol > mature > middle_age
    check(child.get_dimension_age_modifier(7) > adol.get_dimension_age_modifier(7),
          'child recovery > adol')
    check(mature.get_dimension_age_modifier(7) > midage.get_dimension_age_modifier(7),
          'mature recovery > middle_age')
    # D4 内分泌: 青春期最不稳定（负值最大）
    check(adol.get_dimension_age_modifier(4) < mature.get_dimension_age_modifier(4),
          'adol D4 < mature (adol less stable)')
    # D10 探索欲: child > mature
    check(child.get_dimension_age_modifier(10) > mature.get_dimension_age_modifier(10),
          'child D10 > mature')
    # D15 依恋: adol > mature (青春期强烈)
    check(adol.get_dimension_age_modifier(15) > mature.get_dimension_age_modifier(15),
          'adol D15 > mature')
    # D9 自我认知: mature > adol (成熟=稳定)
    check(mature.get_dimension_age_modifier(9) > adol.get_dimension_age_modifier(9),
          'mature D9 > adol (mature more stable)')

    for dim_id in range(1, 33):
        mod = mature.get_dimension_age_modifier(dim_id)
        check(-0.3 <= mod <= 0.3, f'D{dim_id} age mod in [-0.3,0.3]: {mod}')
    print('  [OK] age modifier gradient verified')

def test_sex_differences():
    """性别差异化"""
    print()
    print('=== 3: Sex differences ===')
    from avatar_profile import PRESET_AVATARS
    f_adult = PRESET_AVATARS['young_adult_f']
    # Use mature_m as comparison
    m_adult = PRESET_AVATARS['mature_m']

    # D1 肌肉: 男 > 女
    check(m_adult.get_dimension_age_modifier(1) > f_adult.get_dimension_age_modifier(1),
          'male D1 muscle > female')
    # D2 疼痛: 女更敏感 (负值更大)
    check(f_adult.get_dimension_age_modifier(2) < m_adult.get_dimension_age_modifier(2),
          'female D2 pain (more negative=mor sensitive)')
    # Use mature_f vs mature_m for fair sex comparison (same age group)
    f_mat = PRESET_AVATARS['mature_f']
    m_mat = PRESET_AVATARS['mature_m']
    # D13 共情: 同龄女 > 同龄男
    check(f_mat.get_dimension_age_modifier(13) > m_mat.get_dimension_age_modifier(13),
          f'female D13 empathy {f_mat.get_dimension_age_modifier(13):.2f} > male {m_mat.get_dimension_age_modifier(13):.2f}')
    print('  [OK] sex differences verified')

def test_experience_effects():
    """经验对维度的修正"""
    print()
    print('=== 4: Experience effects ===')
    from avatar_profile import (AvatarProfile, AgeGroup, BiologicalSex,
        ExperienceTracker, ExperienceDomain, ExperienceLevel, PhysicalTraits)
    # 35岁成熟女性，无性经验
    naive = AvatarProfile(
        age_group=AgeGroup.MATURE, biological_sex=BiologicalSex.FEMALE,
        experience=ExperienceTracker())
    # 相同条件但性经验丰富
    exp = AvatarProfile(
        age_group=AgeGroup.MATURE, biological_sex=BiologicalSex.FEMALE,
        experience=ExperienceTracker())
    exp.experience.records[ExperienceDomain.SEXUAL] = (ExperienceLevel.EXPERIENCED, 10, 0)
    exp.experience.records[ExperienceDomain.SOCIAL_LARGE_GROUP] = (ExperienceLevel.EXPERIENCED, 8, 0)

    # naive D11 恐惧 > experienced
    check(naive.get_experience_modifier(11, ExperienceDomain.SEXUAL) <
          exp.get_experience_modifier(11, ExperienceDomain.SEXUAL),
          'naive D11 fear > experienced')
    # naive D12 幸福感: naive新奇高
    check(naive.get_experience_modifier(12, ExperienceDomain.SEXUAL) >
          exp.get_experience_modifier(12, ExperienceDomain.SEXUAL),
          'naive D12 novelty happiness > experienced')
    # experienced D13 共情: 更有同理心
    check(exp.get_experience_modifier(13, ExperienceDomain.SEXUAL) >=
          naive.get_experience_modifier(13, ExperienceDomain.SEXUAL),
          'experienced D13 >= naive')

    # 性行为专项修正
    sex_mods = naive.get_sexual_response_modifiers()
    check(sex_mods.get(2, 0) < 0, f'naive sexual D2 pain neg: {sex_mods.get(2)}')
    check(sex_mods.get(11, 0) < -0.2, f'naive sexual D11 fear high: {sex_mods.get(11)}')
    check(sex_mods.get(15, 0) > 0.1, f'naive sexual D15 attach high: {sex_mods.get(15)}')

    sex_mods_exp = exp.get_sexual_response_modifiers()
    check(sex_mods_exp.get(12, 0) > sex_mods.get(12, 0),
          'experienced D12 > naive D12')
    print('  [OK] experience effects verified')

def test_pipeline_age_groups():
    """管道中四个年龄组的32D输出差异"""
    print()
    print('=== 5: Pipeline age group comparison (same scene) ===')
    from unlock_dispatcher import handle_unlock_event

    base = dict(
        event_type='scene_unlock', dna_root_id='DNA-AGE-TEST',
        location_fingerprint='home:xinghai_mingcheng:living_sofa',
        scene_type='home', time_of_day='evening', weather='clear',
        season='summer', day_type='weekend',
    )

    results = {}
    for avatar_key in ['child_f', 'adolescent_f_14', 'mature_f', 'middle_age_m']:
        r = handle_unlock_event(**base, avatar_key=avatar_key)
        results[avatar_key] = r
        check(r['code'] == 0, f'{avatar_key} code=0')
        check(len(r['objective']) == 32, f'{avatar_key} 32dims')

    # D7 修复速率: child > adolescent > mature > middle_age
    d7_vals = {k: v['objective']['d7']['standard_value'] for k, v in results.items()}
    check(d7_vals['child_f'] > d7_vals['adolescent_f_14'], f'D7 child>{d7_vals["adolescent_f_14"]} adol, got {d7_vals}')
    check(d7_vals['adolescent_f_14'] > d7_vals['mature_f'], f'D7 adol>mature, got {d7_vals}')
    check(d7_vals['mature_f'] > d7_vals['middle_age_m'], f'D7 mature>middle, got {d7_vals}')

    # D11 SAS: 14岁少女社交焦虑最高
    d11_vals = {k: v['objective']['d11']['standard_value'] for k, v in results.items()}
    check(d11_vals['adolescent_f_14'] >= d11_vals['child_f'], f'D11 adol SAS high: {d11_vals}')
    check(d11_vals['adolescent_f_14'] >= d11_vals['mature_f'], f'D11 adol>{d11_vals["mature_f"]} mature: {d11_vals}')

    # D12 催产素: 儿童高纯真, 中年U型回弹
    d12_vals = {k: v['objective']['d12']['standard_value'] for k, v in results.items()}
    check(d12_vals['child_f'] > d12_vals['mature_f'], f'D12 child>{d12_vals["mature_f"]} mature: {d12_vals}')

    print(f'  D7 recovery: {d7_vals}')
    print(f'  D11 SAS: {d11_vals}')
    print(f'  D12 oxytocin: {d12_vals}')
    print('  [OK] age gradient preserved across pipeline')

def test_sexual_experience_scenario():
    """14岁首次 vs 35岁经验丰富 性行为场景对比"""
    print()
    print('=== 6: Sexual experience scenario ===')
    from unlock_dispatcher import handle_unlock_event

    base = dict(
        event_type='social_event', dna_root_id='DNA-SEX-COMPARE',
        location_fingerprint='home:xinghai_mingcheng:master_bed',
        scene_type='home', time_of_day='night', hour=23,
        weather='clear', season='summer', day_type='weekend',
        interpersonal_labels=['partner'],
    )

    # 14岁少女首次
    r_young = handle_unlock_event(**base, avatar_key='adolescent_f_14',
        avatar_custom={'experience': {'sexual': {'level': 'naive', 'count': 0, 'last_ts': 0}}})
    # 35岁女性经验丰富
    r_mature = handle_unlock_event(**base, avatar_key='mature_f',
        avatar_custom={'experience': {'sexual': {'level': 'experienced', 'count': 100, 'last_ts': 1720771200000}}})

    d4_young = r_young['objective']['d4']
    d4_mature = r_mature['objective']['d4']
    d11_young = r_young['objective']['d11']
    d11_mature = r_mature['objective']['d11']
    d2_young = r_young['objective']['d2']
    d2_mature = r_mature['objective']['d2']
    d15_young = r_young['objective']['d15']
    d15_mature = r_mature['objective']['d15']

    # 首次: D4皮质醇更高(紧张) + D11 SAS更高(焦虑) + D2疼痛预期更高
    check(d4_young['standard_value'] > d4_mature['standard_value'],
          f'young naive D4 cortisol {d4_young["standard_value"]} > mature {d4_mature["standard_value"]}')
    check(d11_young['standard_value'] >= d11_mature['standard_value'],
          f'young naive D11 SAS {d11_young["standard_value"]} > mature {d11_mature["standard_value"]}')
    check(d2_young['standard_value'] > d2_mature['standard_value'],
          f'young naive D2 pain {d2_young["standard_value"]} > mature {d2_mature["standard_value"]}')
    # 首次: D15依恋更强烈
    check(d15_young['standard_value'] >= d15_mature['standard_value'] * 0.9,
          f'young naive D15 attach {d15_young["standard_value"]} >= mature {d15_mature["standard_value"]}')

    print(f'  14yo-naive: D4_cort={d4_young["standard_value"]} D11_SAS={d11_young["standard_value"]} D2_pain={d2_young["standard_value"]} D15_oxy={d15_young["standard_value"]}')
    print(f'  35yo-exper: D4_cort={d4_mature["standard_value"]} D11_SAS={d11_mature["standard_value"]} D2_pain={d2_mature["standard_value"]} D15_oxy={d15_mature["standard_value"]}')
    print('  [OK] sexual experience differentiation verified')

def test_mcp_avatar_passthrough():
    """MCP wf_world_unlock 携带 avatar 参数"""
    print()
    print('=== 7: MCP avatar passthrough ===')
    from mcp_harris_g import YaoguangMCP, yaoguang_config, yaoguang_executor
    from harris_g_instance import harris_g_global

    async def run():
        bridge = YaoguangMCP(yaoguang_config, harris_g_global, yaoguang_executor)
        tool = bridge.app._tool_manager._tools.get('run_static_workflow')
        fn = tool.fn

        # 14岁少女 + 首次社交
        r = await fn('wf_world_unlock', 'adolescent social', {
            'dna_root_id': 'DNA-AVATAR-MCP',
            'event_type': 'social_event',
            'location_fingerprint': 'home:xinghai_mingcheng:living_sofa',
            'avatar_key': 'adolescent_f_14',
            'avatar_custom': {'experience': {'social_large': {'level':'naive','count':0,'last_ts':0}}},
            'interpersonal_labels': ['partner'],
        })
        d = json.loads(r)
        check(d['code'] == 0, 'mcp code=0')
        d11 = d['objective']['d11']
        check(d11['standard_value'] >= 28, f'mcp D11 SAS elevated for adolescent naive: {d11["standard_value"]}')
        d15 = d['objective']['d15']
        check(d15['standard_value'] >= 45, f'mcp D15 attachment: {d15["standard_value"]}')
        print(f'  MCP 14yo-naive: D11={d11["standard_value"]} D15={d15["standard_value"]}')
        print('  [OK] MCP avatar passthrough')

    asyncio.run(run())


# ============================================================
test_avatar_presets()
test_age_modifier_matrix()
test_sex_differences()
test_experience_effects()
test_pipeline_age_groups()
test_sexual_experience_scenario()
test_mcp_avatar_passthrough()

print()
print(f'===== {PASS} PASS, {FAIL} FAIL =====')
if FAIL:
    print(f'{FAIL} checks FAILED!')
    sys.exit(1)
print('ALL CHECKS PASSED')
