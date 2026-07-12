"""测试 harris_core.py — V1.0 引擎"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import yaml
from common.harris_core import (
    RunMode, GuardAction, WorkflowContext, GuardRule, WorkflowGuard,
    AgentNode, PhaseUnit, HarrisWorkflow, GuardController,
    HarrisDslParser, make_quick_workflow, HarrisOrchestrator,
    HarrisError, GuardRejectionError, DSLParseError,
)

YAML_TEXT = """
workflow_id: test_wf
version: "1.0"
mode: strict
phases:
  - phase_id: p1
    nodes:
      - node_id: n1
        agent_type: tool
        prompt_template: "hello"
"""

def test_run_mode_enum():
    assert RunMode.STRICT.value == "strict"
    assert RunMode.FLEXIBLE.value == "flexible"

def test_guard_action_enum():
    assert GuardAction.ALLOW is not None
    assert GuardAction.DENY is not None

def test_workflow_context():
    ctx = WorkflowContext(task="test", constraints={"k": "v"})
    ctx.log_step("n1", "completed", "ok")
    assert len(ctx.trace) == 1
    assert ctx.trace[0]["status"] == "completed"

def test_guard_rule():
    def check(ctx): return GuardAction.ALLOW, "pass"
    rule = GuardRule(name="r1", checker=check, priority=10)
    action, msg = rule.evaluate(WorkflowContext(task="t"))
    assert action == GuardAction.ALLOW

def test_workflow_guard():
    guard = WorkflowGuard("g1")
    guard.add_rule(GuardRule(name="r1", priority=5))
    guard.add_rule(GuardRule(name="r2", priority=10))
    assert len(guard.rules) == 2
    assert guard.rules[0].name == "r1"  # sorted by priority

def test_agent_node():
    node = AgentNode(node_id="n1", agent_type="tool", timeout_seconds=60, depends_on=["n0"])
    assert node.node_id == "n1"
    assert "n0" in node.depends_on

def test_phase_unit():
    phase = PhaseUnit(phase_id="p1", parallel=False)
    phase.add_node(AgentNode(node_id="n1", agent_type="tool"))
    assert len(phase.nodes) == 1

def test_harris_workflow():
    wf = make_quick_workflow("test", "tool", prompt="hello")
    assert wf.workflow_id == "test"
    assert len(wf.phases) == 1
    assert wf.all_nodes[0].node_id == "main"
    digest = wf.digest()
    assert len(digest) == 16  # SHA256 hex 前 16

def test_guard_controller():
    gc = GuardController(RunMode.STRICT)
    guard = WorkflowGuard("g1")
    guard.add_rule(GuardRule(name="r1", priority=0,
        checker=lambda ctx: (GuardAction.DENY, "blocked")))
    ctx = WorkflowContext(task="t")
    try:
        gc.check(guard, ctx, "Test")
        assert False, "should have rejected"
    except GuardRejectionError:
        pass

def test_dsl_parser():
    wf = HarrisDslParser.from_yaml_text(YAML_TEXT)
    assert wf.workflow_id == "test_wf"
    assert wf.version == "1.0"
    assert wf.mode == RunMode.STRICT
    assert len(wf.phases) == 1
    assert wf.phases[0].phase_id == "p1"
    assert len(wf.all_nodes) == 1

def test_dsl_parser_invalid_yaml():
    try:
        HarrisDslParser.from_yaml_text("{invalid")
        assert False
    except DSLParseError:
        pass
