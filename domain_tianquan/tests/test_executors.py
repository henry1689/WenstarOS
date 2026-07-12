"""测试 node_executors.py — 执行器注册表 + 核心执行器函数"""
import sys, os, json, tempfile
from pathlib import Path

_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

import asyncio
from executor.node_executors import (
    EXECUTOR_REGISTRY, create_executor, execute_node, list_executors,
)
from common.harris_core_v2 import WorkflowContextV2

def test_all_executors_registered():
    """47+ nodes registered"""
    execs = list_executors()
    assert len(execs) >= 47, f"Expected >= 47 executors, got {len(execs)}"
    # Spot-check key executors exist
    for nid in ["n1_lint_check", "n1_scan_references", "n1_extract_schema",
                "n1_content_hash", "n1_scan_test_files", "n1_git_diff",
                "n1_parse_dependencies", "n1_scan_logs", "n1_collect_configs",
                "n1_scan_file_handles"]:
        assert nid in EXECUTOR_REGISTRY, f"Missing executor: {nid}"

def test_create_executor():
    dispatch = create_executor()
    assert callable(dispatch)

def test_execute_nonexistent_node():
    from common.harris_core import AgentNode
    ctx = WorkflowContextV2(task="test")
    node = AgentNode(node_id="nonexistent_node", agent_type="tool")
    result = asyncio.run(execute_node("nonexistent_node", node, ctx))
    assert result["status"] == "no_executor"

def test_lint_executor():
    """n1_lint_check runs without error on a temp dir"""
    from common.harris_core import AgentNode
    with tempfile.TemporaryDirectory() as td:
        Path(td, "good_file.py").write_text("x = 1\n", encoding="utf-8")
        ctx = WorkflowContextV2(task="lint", constraints={"project_root": td})
        node = AgentNode(node_id="n1_lint_check", agent_type="tool")
        result = asyncio.run(execute_node("n1_lint_check", node, ctx))
        assert result["status"] == "ok"
        assert result["files_scanned"] > 0

def test_arch_executor():
    """n3_module_coupling on self"""
    from common.harris_core import AgentNode
    root = str(Path(__file__).resolve().parent.parent)
    ctx = WorkflowContextV2(task="arch", constraints={"project_root": root})
    node = AgentNode(node_id="n3_module_coupling", agent_type="tool")
    result = asyncio.run(execute_node("n3_module_coupling", node, ctx))
    assert result["status"] == "ok"
    assert result["avg_coupling"] >= 0

def test_content_hash_executor():
    """n1_content_hash on a temp vault"""
    from common.harris_core import AgentNode
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td) / "vault"
        vault.mkdir()
        (vault / "doc1.md").write_text("# Hello\nworld", encoding="utf-8")
        (vault / "doc2.md").write_text("# Hello\nworld", encoding="utf-8")  # duplicate
        (vault / "doc3.md").write_text("unique", encoding="utf-8")
        ctx = WorkflowContextV2(task="hash", constraints={"project_root": td, "vault_path": "vault"})
        node = AgentNode(node_id="n1_content_hash", agent_type="tool")
        result = asyncio.run(execute_node("n1_content_hash", node, ctx))
        assert result["status"] == "ok"
        assert result["total_files"] == 3
        assert result["duplicates_found"] == 1

def test_git_diff_executor():
    """n1_git_diff on self project"""
    from common.harris_core import AgentNode
    root = str(Path(__file__).resolve().parent.parent.parent)
    ctx = WorkflowContextV2(task="diff", constraints={"project_root": root})
    node = AgentNode(node_id="n1_git_diff", agent_type="tool")
    result = asyncio.run(execute_node("n1_git_diff", node, ctx))
    assert result["status"] == "ok"
    # should find either git changes or report no-git
    assert "has_git" in result
