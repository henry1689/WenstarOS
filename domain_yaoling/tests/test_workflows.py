"""
test_workflows.py — 工作流集成测试
===================================
验证 YAML 工作流可被 HarrisDslParser 正确解析，
且 Guard 规则结构符合规范要求。
"""

import sys
from pathlib import Path
_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

# 注意: 此测试需要 common/harris_core.py 在 path 中
try:
    from common.harris_core import HarrisDslParser
except ImportError:
    print("WARN  无法导入 HarrisDslParser（common/ 不在 sys.path），跳过 YAML 解析测试")
    print("   在 domain_yaoling 窗口内执行 mcp_harris_l.py 时会自动校验 YAML。")
    sys.exit(0)


WORKFLOW_DIR = Path(__file__).resolve().parent.parent / "workflows"
REQUIRED_WORKFLOWS = [
    "wf_sensation_pipeline.yaml",
    "wf_safety_gate.yaml",
    "wf_yaoling_snapshot.yaml",
]


def test_all_workflows_exist():
    """验证三套工作流文件存在。"""
    for wf in REQUIRED_WORKFLOWS:
        path = WORKFLOW_DIR / wf
        assert path.exists(), f"缺失工作流文件: {wf}"
    print("OK  三套工作流文件全部存在")


def test_parse_all_workflows():
    """验证三套工作流 YAML 可被 HarrisDslParser 正确解析。"""
    for wf in REQUIRED_WORKFLOWS:
        path = WORKFLOW_DIR / wf
        workflow = HarrisDslParser.from_yaml_file(str(path))
        assert workflow.workflow_id, f"{wf}: workflow_id 为空"
        assert workflow.mode.value == "strict", f"{wf}: 模式必须为 strict"
        assert len(workflow.phases) > 0, f"{wf}: 阶段数为0"
        print(f"OK  {wf}: mode={workflow.mode.value}, phases={len(workflow.phases)}, nodes={len(workflow.all_nodes)}")


def test_guard_structure():
    """验证 Guard 结构包含必需的守门规则。"""
    for wf in REQUIRED_WORKFLOWS:
        path = WORKFLOW_DIR / wf
        workflow = HarrisDslParser.from_yaml_file(str(path))

        # 所有工作流必须有 global_guard
        assert workflow.global_guard is not None, f"{wf}: 缺少 global_guard"

        # 检查关键守门规则名称
        rule_names = {r.name for r in workflow.global_guard.rules}
        assert "no_dynamic_override" in rule_names or "no_bypass_flag" in rule_names or "no_bypass" in rule_names, \
            f"{wf}: 缺少动态工作流禁止规则"
        assert any("dna" in r.name.lower() for r in workflow.global_guard.rules), \
            f"{wf}: 缺少 dna_root_id 校验"

        print(f"OK  {wf} Guard: {len(workflow.global_guard.rules)} rules, names={rule_names}")


def test_constraints_schema():
    """验证 constraints_schema 包含必需字段。"""
    for wf in REQUIRED_WORKFLOWS:
        path = WORKFLOW_DIR / wf
        workflow = HarrisDslParser.from_yaml_file(str(path))
        schema = workflow.constraints_schema
        assert schema is not None, f"{wf}: 缺失 constraints_schema"
        required = schema.get("required", [])
        assert "dna_root_id" in required, f"{wf}: constraints 未要求 dna_root_id"
        print(f"OK  {wf} constraints: required={required}")


if __name__ == "__main__":
    test_all_workflows_exist()
    test_parse_all_workflows()
    test_guard_structure()
    test_constraints_schema()
    print("\nPASS  全部工作流集成测试通过")
