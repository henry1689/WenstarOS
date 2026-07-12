"""
test_modules.py — 天权模块单元测试
===================================
验证 arch_parser / sql_parser / doc_generator 基本功能正常。
"""

import sys
import tempfile
from pathlib import Path

_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from modules.arch_parser import ArchParser, quick_parse
from modules.sql_parser import SQLParser, SQLAuditor, quick_audit
from modules.doc_generator import DocGenerator, ChangeType


# ── ArchParser ──────────────────────────────────────────────

def test_arch_parser_self_scan():
    """扫描天权域自身模块，确保不报错。"""
    parser = ArchParser()
    root = str(Path(__file__).resolve().parent.parent)
    report = parser.parse(root)
    assert report.total_files > 0, "应找到至少一个 Python 文件"
    print(f"  ✅ arch_parser: {report.total_files} files, {len(report.modules)} modules, avg coupling={report.avg_coupling:.3f}")


# ── SQLParser ───────────────────────────────────────────────

SAMPLE_DDL = """
CREATE TABLE IF NOT EXISTS state_spines (
    dna_id TEXT NOT NULL,
    dimension_id INTEGER NOT NULL,
    value_raw REAL NOT NULL DEFAULT 0.0,
    created_at INTEGER NOT NULL DEFAULT (unixepoch()),
    PRIMARY KEY (dna_id, dimension_id),
    CHECK(dimension_id BETWEEN 1 AND 32)
) WITHOUT ROWID;

CREATE INDEX idx_state_spines_dna ON state_spines(dna_id);

CREATE TABLE atom_address_timeline (
    global_uid TEXT PRIMARY KEY,
    global_time_seq INTEGER NOT NULL,
    absolute_timestamp INTEGER NOT NULL
) WITHOUT ROWID;
"""


def test_sql_parser_basic():
    parser = SQLParser()
    report = parser.parse_text(SAMPLE_DDL)
    assert "state_spines" in report.tables, "应解析出 state_spines"
    assert "atom_address_timeline" in report.tables, "应解析出 atom_address_timeline"
    assert len(report.indexes) == 1, "应解析出 1 个索引"
    print(f"  ✅ sql_parser: {len(report.tables)} tables, {len(report.indexes)} indexes")


def test_sql_audit():
    report = quick_audit(SAMPLE_DDL)
    assert report.missing_pk_tables == [], "两张表都有主键"
    print(f"  ✅ sql_audit: naming_violations={len(report.naming_violations)}, recommendations={report.recommendations}")


# ── DocGenerator ────────────────────────────────────────────

def test_doc_generator():
    gen = DocGenerator()
    report = gen.generate(
        title="测试修复五级闸门G2时空校验",
        change_type=ChangeType.FIX,
        author="天权-Harris",
        details="修复了location_fingerprint大小写敏感导致跨场景误召回的问题",
        impact="只影响M4检索管线G2层",
        affected_files=["src/gate/five_stage_gate.ts"],
    )
    md = gen.to_markdown(report)
    assert "变更摘要" in md
    assert "变更详情" in md
    assert "影响范围" in md
    assert "验证方法" in md
    assert "location_fingerprint" in md
    print(f"  ✅ doc_generator: 四段式报告 {len(md)} 字符")


if __name__ == "__main__":
    test_arch_parser_self_scan()
    test_sql_parser_basic()
    test_sql_audit()
    test_doc_generator()
    print("\n🎉 天权模块单元测试全部通过")
