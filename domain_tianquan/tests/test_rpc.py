"""测试 tianquan_rpc_server.py — RPC 服务 + 约束注入"""
import sys, os, json
from pathlib import Path
_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path: sys.path.insert(0, str(_PARENT))
os.environ['RUN_MODE'] = 'prod'

def test_server_import():
    from tianquan_rpc_server import TianquanRPCServer
    srv = TianquanRPCServer()
    assert srv is not None
    assert "health" in srv._handlers
    assert "run_workflow" in srv._handlers
    assert len(srv._handlers) == 8

def test_health_response():
    from tianquan_rpc_server import TianquanRPCServer
    srv = TianquanRPCServer()
    result = srv._health({})
    assert result["status"] == "ok"
    assert result["server"] == "tianquan-rpc-v2"
    assert "workflows_loaded" in result
    assert len(result["workflows_loaded"]) == 10

def test_list_workflows():
    from tianquan_rpc_server import TianquanRPCServer
    srv = TianquanRPCServer()
    result = srv._list_workflows({})
    assert result["code"] == 0
    assert len(result["workflows"]) == 10
    for wf_id, info in result["workflows"].items():
        assert info["nodes_with_executor"] == info["nodes"], f"{wf_id}: {info['nodes_with_executor']}/{info['nodes']}"

def test_lint_check():
    from tianquan_rpc_server import TianquanRPCServer
    srv = TianquanRPCServer()
    root = str(Path(__file__).resolve().parent.parent)
    result = srv._lint_check({"project_root": root})
    assert result["code"] == 0
    assert result["files_scanned"] > 0

def test_arch_parse():
    from tianquan_rpc_server import TianquanRPCServer
    srv = TianquanRPCServer()
    root = str(Path(__file__).resolve().parent.parent)
    result = srv._arch_parse({"project_root": root})
    assert result["code"] == 0
    assert result["modules"] > 0

def test_snapshot():
    from tianquan_rpc_server import TianquanRPCServer
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        Path(td, "x.py").write_text("pass", encoding="utf-8")
        srv = TianquanRPCServer()
        result = srv._generate_snapshot({"project_root": td})
        assert result["code"] == 0
        assert result["snapshot_id"].startswith("SNAP-")
