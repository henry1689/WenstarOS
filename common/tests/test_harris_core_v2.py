"""测试 harris_core_v2.py — V2.0 引擎"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
from common.harris_core_v2 import (
    AgentType, RouteStamp, WorkflowContextV2,
    HarrisDslParserV2, HarrisOrchestratorV2,
    HarrisError, RunMode,
)

YAML_V2 = """workflow_id: test_v2
version: "2.0"
mode: strict
domain: tianquan
route_tag: test
executor_type: local_rpc
constraints_schema:
  type: object
  required: [task]
global_guard:
  guard_name: g1
  rules:
    - { name: r1, priority: 0 }
phases:
  - phase_id: p1
    route_stamp_workshop: "T"
    route_stamp_operation: "OP"
    nodes:
      - { node_id: n1, agent_type: tool }
metadata:
  domain: tianquan
  harris_version: "2.0"
"""

def test_agent_type_enum():
    assert AgentType.TOOL.value == "tool"
    assert AgentType.LLM.value == "llm"
    assert AgentType.GUARD_ONLY.value == "guard_only"
    assert len(AgentType) == 5

def test_route_stamp():
    stamp = RouteStamp(workshop="T", operation="OP", phase_id="p1",
                       node_id="n1", timestamp=123.0, detail="ok", crc_snap="abc")
    assert stamp.workshop == "T"
    assert stamp.phase_id == "p1"

def test_workflow_context_v2():
    ctx = WorkflowContextV2(task="t", domain="tianquan", global_uid="G001")
    ctx.stamp("T", "OP", "p1", "n1", detail="test")
    assert len(ctx.route_stamps) == 1
    assert ctx.route_stamps[0].workshop == "T"
    ctx.log_step("n1", "done")
    assert ctx.trace[-1]["status"] == "done"

def test_dsl_parser_v2():
    wf = HarrisDslParserV2.from_yaml_text(YAML_V2)
    assert wf.workflow_id == "test_v2"
    assert wf.version == "2.0"
    assert wf.metadata.get("domain") == "tianquan"
    assert wf.metadata.get("route_tag") == "test"
    assert wf.constraints_schema is not None
    assert "task" in wf.constraints_schema["required"]
    assert len(wf.phases) == 1
    assert len(wf.all_nodes) == 1

def test_dsl_parser_v2_backward_compat():
    """V2.0 parser should handle V1.0 YAML"""
    yaml_v1 = """workflow_id: old_wf
version: "1.0"
mode: strict
phases:
  - phase_id: p1
    nodes:
      - { node_id: n1, agent_type: tool }
"""
    wf = HarrisDslParserV2.from_yaml_text(yaml_v1)
    assert wf.workflow_id == "old_wf"
    assert wf.version == "1.0"

def test_inject_master_constraints():
    c = HarrisOrchestratorV2.inject_master_constraints(
        task="test", global_uid="G01", location_fingerprint="FF"*16,
        spec_version="v1", extra={"project_root": "/tmp"}
    )
    assert c["dna_root_id"] == "G01"
    assert c["task"] == "test"
    assert c["project_root"] == "/tmp"

def test_orchestrator_v2_run():
    """Execute a minimal V2 workflow end-to-end"""
    yaml_min = """workflow_id: min_v2
version: "2.0"
mode: flexible
phases:
  - phase_id: p1
    nodes:
      - { node_id: n1, agent_type: tool }
"""
    wf = HarrisDslParserV2.from_yaml_text(yaml_min)
    orch = HarrisOrchestratorV2(wf, domain="tianquan")

    async def _exec(node, ctx):
        return {"status": "ok", "node": node.node_id}

    result = asyncio.run(orch.run("test", node_executor=_exec))
    assert isinstance(result, WorkflowContextV2)
    assert len(result.trace) > 0
    assert len(result.route_stamps) > 0
