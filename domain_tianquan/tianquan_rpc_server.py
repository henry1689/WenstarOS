"""
tianquan_rpc_server.py — 天权域生产 RPC 服务 (V2.0)
=====================================================
由太虚境主进程 spawn，通过 stdin/stdout JSON-line RPC 通信。
使用 Harris V2.0 引擎——支持约束注入、路由戳、钩子系统、AgentType 感知。

协议:
  ← stdin:  {"id":"1","method":"run_workflow","params":{...}}
  → stdout: {"id":"1","result":{...}}  |  {"id":"1","error":"..."}

启动条件:
  RUN_MODE != "dev" (生产模式专用)
  开发调试请使用: RUN_MODE=dev python mcp_harris_t.py

跨语言:
  Python 侧 (此文件) ↔ TypeScript 侧 (TianquanRPCClient.ts)
  阶段 1: JSON-line 过渡 (工程参数无浮点精度问题)
  阶段 4: Protobuf 二进制切换
"""

import asyncio
import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

# ── 路径设置 ──────────────────────────────────────────────────
_SELF = Path(__file__).resolve()
_DOMAIN_DIR = _SELF.parent
_PROJECT_DIR = _DOMAIN_DIR.parent

for _p in (_PROJECT_DIR, _DOMAIN_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# ── V2.0 引擎 ────────────────────────────────────────────────
from common.harris_core_v2 import (
    HarrisDslParserV2,
    HarrisOrchestratorV2,
    WorkflowContextV2,
    AgentType,
    RunMode,
    HarrisError,
)

# ── 天权模块 ──────────────────────────────────────────────────
from modules.arch_parser import ArchParser
from modules.sql_parser import SQLParser, SQLAuditor
from modules.doc_generator import DocGenerator, ChangeType
from validator.lint_checker import LintChecker
from codec.snapshot_codec import SnapshotCodec
from executor.node_executors import create_executor, list_executors

# ── 工作流配置 ────────────────────────────────────────────────
from mcp_harris_t import tianquan_config, _WORKFLOW_DIR

# ── 环境检查 ──────────────────────────────────────────────────
RUN_MODE = os.environ.get("RUN_MODE", "prod")
if RUN_MODE == "dev":
    print(
        "FATAL: tianquan_rpc_server.py 是生产模式专用 RPC 服务。\n"
        "开发调试请使用: RUN_MODE=dev python mcp_harris_t.py\n"
        "或设置环境变量 RUN_MODE=prod 后再试。",
        file=sys.stderr,
    )
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════
# RPC 服务
# ═══════════════════════════════════════════════════════════════


class TianquanRPCServer:
    """stdin/stdout JSON-line RPC 服务——天权 V2.0 引擎。"""

    def __init__(self) -> None:
        self._running = False
        self._req_count = 0
        self._started_at = time.time()
        self._lint_checker: Optional[LintChecker] = None
        self._arch_parser: Optional[ArchParser] = None
        self._snapshot_codec: Optional[SnapshotCodec] = None
        self._handlers = {
            "health":            self._health,
            "run_workflow":      self._run_workflow,
            "lint_check":        self._lint_check,
            "arch_parse":        self._arch_parse,
            "sql_audit":         self._sql_audit,
            "generate_snapshot": self._generate_snapshot,
            "get_spec":          self._get_spec,
            "list_workflows":    self._list_workflows,
        }

    # ═══════════════════════════════════════════════════════════
    # 主循环
    # ═══════════════════════════════════════════════════════════

    async def run(self) -> None:
        """stdin/stdout RPC 服务循环。线程池读stdin，主循环逐行处理。"""
        self._running = True
        loop = asyncio.get_event_loop()

        # 就绪信号
        self._write_line({"type": "ready", "server": "tianquan-rpc-v2",
                          "pid": os.getpid(), "workflows": list(tianquan_config.default_rigid_pool.keys())})

        stdin_buffer = sys.stdin.buffer

        def _read_line() -> Optional[bytes]:
            try:
                line = stdin_buffer.readline()
                return line if line else None
            except Exception:
                return None

        while self._running:
            try:
                line = await loop.run_in_executor(None, _read_line)
            except Exception:
                break
            if line is None:
                break

            try:
                data = json.loads(line.decode("utf-8").strip())
            except json.JSONDecodeError:
                self._write_line({"type": "error", "reason": "JSON 解析失败"})
                continue

            req_id = data.get("id", "")
            method = data.get("method", "")
            params = data.get("params", {})

            handler = self._handlers.get(method)
            if handler is None:
                self._write_resp(req_id, error=f"未知方法: {method}")
                continue

            self._req_count += 1
            try:
                result = await handler(params) if asyncio.iscoroutinefunction(handler) else handler(params)
                self._write_resp(req_id, result=result)
            except HarrisError as e:
                self._write_resp(req_id, error=f"HarrisError: {e}")
            except Exception as e:
                self._write_resp(req_id, error=f"{type(e).__name__}: {e}")
                traceback.print_exc(file=sys.stderr)

        self._running = False

    # ═══════════════════════════════════════════════════════════
    # RPC 方法实现
    # ═══════════════════════════════════════════════════════════

    def _health(self, params: dict) -> dict:
        return {
            "status": "ok",
            "server": "tianquan-rpc-v2",
            "pid": os.getpid(),
            "uptime_seconds": round(time.time() - self._started_at, 1),
            "request_count": self._req_count,
            "workflows_loaded": list(tianquan_config.default_rigid_pool.keys()),
            "executors_registered": len(list_executors()),
            "run_mode": RUN_MODE,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        }

    async def _run_workflow(self, params: dict) -> dict:
        """V2.0 引擎执行工作流——含约束注入 + 路由戳。"""
        workflow_id = params.get("workflow_id", "")
        task = params.get("task", "")
        constraints = params.get("constraints", {})

        if not workflow_id or not task:
            return {"code": -1, "error": "缺少 workflow_id 或 task"}

        yaml_text = tianquan_config.default_rigid_pool.get(workflow_id)
        if not yaml_text:
            return {"code": -1, "error": f"未知工作流: {workflow_id}"}

        workflow = HarrisDslParserV2.from_yaml_text(yaml_text)

        # ── 智能约束补齐 ──
        if "task" not in constraints:
            constraints["task"] = task
        if "spec_version" not in constraints:
            constraints["spec_version"] = workflow.metadata.get("spec_version", "TIANQUAN-SPEC-20260711")
        if "location_fingerprint" not in constraints:
            constraints["location_fingerprint"] = "0" * 32
        if "dna_root_id" not in constraints:
            constraints["dna_root_id"] = "TT00000001M01SYS0000000"

        _DEFAULT_VALUES: Dict[str, Any] = {
            "project_root":      str(_PROJECT_DIR),
            "change_files":      ["*"],
            "affected_modules":  ["*"],
            "refactor_scope":    "auto",
            "backup_verified":   True,
            "vault_path":        "",
            "db_path":           "",
            "schema_version":    "1.0",
            "knowledge_category": "spec",
            "force_overwrite":   False,
            "migration_scope":   [],
        }
        schema_required = (workflow.constraints_schema or {}).get("required", [])
        for key in schema_required:
            if key not in constraints and key in _DEFAULT_VALUES:
                constraints[key] = _DEFAULT_VALUES[key]

        orchestrator = HarrisOrchestratorV2(
            workflow, None,
            domain=workflow.metadata.get("domain", "tianquan"),
        )
        executor = create_executor()
        ctx = await orchestrator.run(task, constraints, node_executor=executor)

        return {
            "code": 0,
            "workflow_id": workflow_id,
            "data": ctx.artifacts,
            "trace": ctx.trace[-30:],
            "metrics": ctx.metrics,
            "stamps": len(ctx.route_stamps),
            "degraded": ctx.degraded,
            "degradation_reason": ctx.degradation_reason,
        }

    def _lint_check(self, params: dict) -> dict:
        project_root = params.get("project_root", "")
        if not project_root:
            return {"code": -1, "error": "缺少 project_root"}
        if self._lint_checker is None:
            self._lint_checker = LintChecker()
        report = self._lint_checker.check_directory(project_root)
        return {
            "code": 0,
            "passed": report.passed,
            "files_scanned": report.files_scanned,
            "errors": len(report.violations),
            "warnings": len(report.warnings),
            "violations": [
                {"file": v.file, "line": v.line, "rule": v.rule, "message": v.message}
                for v in report.violations
            ],
            "lint_duration_ms": report.lint_duration_ms,
        }

    def _arch_parse(self, params: dict) -> dict:
        project_root = params.get("project_root", "")
        if not project_root:
            return {"code": -1, "error": "缺少 project_root"}
        if self._arch_parser is None:
            self._arch_parser = ArchParser()
        report = self._arch_parser.parse(project_root)
        return {
            "code": 0,
            "total_files": report.total_files,
            "modules": len(report.modules),
            "cycles": len(report.cycles),
            "avg_coupling": report.avg_coupling,
            "recommendations": report.recommendations,
            "cycle_details": report.cycles[:5],
        }

    def _sql_audit(self, params: dict) -> dict:
        sql_text = params.get("sql_text", "")
        file_path = params.get("file_path", "")
        if file_path:
            parser = SQLParser()
            schema = parser.parse_file(file_path)
            audit = SQLAuditor().audit(schema)
        elif sql_text:
            from modules.sql_parser import quick_audit
            audit = quick_audit(sql_text)
        else:
            return {"code": -1, "error": "需要 sql_text 或 file_path"}
        return {
            "code": 0,
            "tables": len(audit.schema.tables),
            "indexes": len(audit.schema.indexes),
            "fks": len(audit.schema.foreign_keys),
            "naming_violations": audit.naming_violations,
            "missing_pk_tables": audit.missing_pk_tables,
            "missing_index_warnings": audit.missing_index_warnings,
            "redundant_indexes": audit.redundant_indexes,
            "recommendations": audit.recommendations,
        }

    def _generate_snapshot(self, params: dict) -> dict:
        project_root = params.get("project_root", "")
        if not project_root:
            return {"code": -1, "error": "缺少 project_root"}
        if self._snapshot_codec is None:
            self._snapshot_codec = SnapshotCodec(project_root)
        snap = self._snapshot_codec.capture()
        saved_path = self._snapshot_codec.save(snap)
        return {
            "code": 0,
            "snapshot_id": snap.snapshot_id,
            "file_count": snap.file_count,
            "saved_to": str(saved_path),
            "timestamp": snap.timestamp,
        }

    def _get_spec(self, params: dict) -> dict:
        spec_path = _DOMAIN_DIR / "TIANQUAN_DOMAIN_SPEC.md"
        if not spec_path.exists():
            return {"code": -1, "error": "TIANQUAN_DOMAIN_SPEC.md 不存在"}
        content = spec_path.read_text(encoding="utf-8")
        return {
            "code": 0,
            "spec_id": "TIANQUAN-SPEC-20260711",
            "size_bytes": len(content),
            "content": content,
        }

    def _list_workflows(self, params: dict) -> dict:
        workflows_info = {}
        execs = list_executors()
        for wf_id, yaml_text in tianquan_config.default_rigid_pool.items():
            try:
                wf = HarrisDslParserV2.from_yaml_text(yaml_text)
                guard_names = [r.name for r in wf.global_guard.rules] if wf.global_guard else []
                node_ids = [n.node_id for n in wf.all_nodes]
                exec_covered = [nid for nid in node_ids if nid in execs]
                workflows_info[wf_id] = {
                    "version": wf.version,
                    "description": wf.description,
                    "mode": wf.mode.value,
                    "domain": wf.metadata.get("domain", ""),
                    "route_tag": wf.metadata.get("route_tag", ""),
                    "phases": len(wf.phases),
                    "nodes": len(node_ids),
                    "nodes_with_executor": len(exec_covered),
                    "node_ids": node_ids,
                    "guard_rules": len(guard_names),
                    "required_constraints": list(wf.constraints_schema.get("required", [])) if wf.constraints_schema else [],
                }
            except Exception as e:
                workflows_info[wf_id] = {"error": str(e)}
        return {"code": 0, "workflows": workflows_info}

    # ═══════════════════════════════════════════════════════════
    # 低层 I/O (同步, 无并发问题)
    # ═══════════════════════════════════════════════════════════

    def _write_line(self, data: dict) -> None:
        line = json.dumps(data, ensure_ascii=False) + "\n"
        sys.stdout.buffer.write(line.encode("utf-8"))
        sys.stdout.buffer.flush()

    def _write_resp(self, req_id: str, result: Any = None, error: Optional[str] = None) -> None:
        if error:
            self._write_line({"id": req_id, "error": error})
        else:
            self._write_line({"id": req_id, "result": result})


# ═══════════════════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════════════════


def main() -> None:
    server = TianquanRPCServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
