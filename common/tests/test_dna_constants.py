"""测试 dna_constants.py — 全局 DNA 常量单源真相"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def test_global_uid_length():
    from common.dna_constants import GLOBALUID_TOTAL_LENGTH, GLOBALUID_SEGMENT_LENGTHS
    assert GLOBALUID_TOTAL_LENGTH == 23
    assert sum(GLOBALUID_SEGMENT_LENGTHS.values()) == 23

def test_dim_count_locked():
    from common.dna_constants import DIM_COUNT, SECTOR_DIM_MAP
    assert DIM_COUNT == 32
    assert len(SECTOR_DIM_MAP) == 32 + 1  # 0-32 inclusive

def test_dim_categories():
    from common.dna_constants import DimCategory
    cats = {DimCategory.PERCEIVE_USER_EMOTION, DimCategory.PHYSICAL_BODY, DimCategory.HOLISTIC}
    assert len(cats) == 3

def test_l0_domains():
    from common.dna_constants import L0Domain
    assert hasattr(L0Domain, "FAMILY")
    assert hasattr(L0Domain, "EMOTION")
    assert len(L0Domain) >= 6

def test_calcium_levels():
    from common.dna_constants import CalciumLevel, CALCIUM_THRESHOLDS, SAND_TO_GOLD_CALCIUM, GOLD_TO_DIAMOND_CALCIUM
    assert SAND_TO_GOLD_CALCIUM == 1.0
    assert GOLD_TO_DIAMOND_CALCIUM == 4.5
    assert len(CALCIUM_THRESHOLDS) == 4

def test_leaf_zones():
    from common.dna_constants import LeafZone, LEAF_ZONE_PREFIXES
    assert len(LeafZone) == 5
    assert LeafZone.EMOTION_VALENCE in LEAF_ZONE_PREFIXES

def test_mh_rules():
    from common.dna_constants import MH_RULES
    assert len(MH_RULES) == 7
    assert "MH-1" in MH_RULES
    assert "MH-7" in MH_RULES

def test_boundary_constants():
    from common.dna_constants import BOUNDARY_TIME_GAP_MS, BOUNDARY_CONFIDENCE
    assert BOUNDARY_TIME_GAP_MS == 30 * 60 * 1000
    assert "time_gap" in BOUNDARY_CONFIDENCE
