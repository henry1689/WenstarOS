"""
test_workflows.py — 天权工作流集成测试
========================================
验证四套 YAML 工作流可被 HarrisDslParser 正确解析，
且 Guard 结构符合 TIANQUAN_DOMAIN_SPEC.md §2.3 要求。
"""

import sys
from pathlib import Path

_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

_PARENT2 = _PARENT.parent
if str(_PARENT2) not in sys.path:
    sys.path.insert(0, str(_PARENT2))

try:
    from common.harris_core import HarrisDslParser, RunMode
except ImportError:
    print("⚠️ 无法导入 HarrisDslParser，跳过 YAML 解析测试")
    sys.exit(0)


WORKFLOW_DIR = Path(__file__).resolve().parent.parent / "workflows"
REQUIRED_WORKFLOWS = [
    "wf_code_review.yaml",
    "wf_arch_refactor.yaml",
    "wf_sql_governance.yaml",
    "wf_knowledge_organize.yaml",
]


def test_all_workflows_exist():
    for wf in REQUIRED_WORKFLOWS:
        path = WORKFLOW_DIR / wf
        assert path.exists(), f"缺失工作流: {wf}"
    print("✅ 四套工作流文件全部存在")


def test_parse_all_workflows():
    for wf in REQUIRED_WORKFLOWS:
        path = WORKFLOW_DIR / wf
        workflow = HarrisDslParser.from_yaml_file(str(path))
        assert workflow.workflow_id, f"{wf}: workflow_id 为空"
        assert workflow.mode in (RunMode.STRICT, RunMode.FLEXIBLE), f"{wf}: 模式无效"
        assert len(workflow.phases) > 0, f"{wf}: 阶段数为0"
        print(f"  ✅ {wf}: mode={workflow.mode.value}, phases={len(workflow.phases)}, nodes={len(workflow.all_nodes)}")


def test_guard_structure():
    for wf in REQUIRED_WORKFLOWS:
        path = WORKFLOW_DIR / wf
        workflow = HarrisDslParser.from_yaml_file(str(path))
        assert workflow.global_guard is not None, f"{wf}: 缺少 global_guard"
        rule_names = {r.name for r in workflow.global_guard.rules}
        # 天权域关键守门规则
        assert any("impact" in r.name.lower() or "change_report" in r.name.lower() or "backup" in r.name.lower() or "coding_standard" in r.name.lower() or "no_destructive" in r.name.lower() for r in workflow.global_guard.rules), \
            f"{wf}: 缺少天权工程守门规则 (impact_analysis / change_report / backup / coding_standard / no_destructive)"
        print(f"  ✅ {wf} Guard: {len(workflow.global_guard.rules)} rules, names={rule_names}")


def test_constraints_schema():
    for wf in REQUIRED_WORKFLOWS:
        path = WORKFLOW_DIR / wf
        workflow = HarrisDslParser.from_yaml_file(str(path))
        schema = workflow.constraints_schema
        assert schema is not None, f"{wf}: 缺失 constraints_schema"
        print(f"  ✅ {wf} constraints: required={schema.get('required', [])}")


if __name__ == "__main__":
    test_all_workflows_exist()
    test_parse_all_workflows()
    test_guard_structure()
    test_constraints_schema()
    print("\n🎉 天权域全部工作流集成测试通过")
