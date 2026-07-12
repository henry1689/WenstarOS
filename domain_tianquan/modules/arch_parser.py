"""
arch_parser.py — 天权架构依赖解析器
=====================================
输入项目根路径，输出模块依赖图、循环依赖检测、耦合度评分。

规格依据: TIANQUAN_DOMAIN_SPEC.md §3.2
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
@dataclass
class ModuleInfo:
    path: str                       # 相对路径
    name: str                       # 模块名
    imports: List[str] = field(default_factory=list)       # 导入的模块名列表
    imported_by: List[str] = field(default_factory=list)   # 被哪些模块导入
    exports: List[str] = field(default_factory=list)       # 导出的符号
    coupling_score: float = 0.0     # 耦合度 (0-1)


@dataclass
class ArchReport:
    root: str
    modules: Dict[str, ModuleInfo] = field(default_factory=dict)
    cycles: List[List[str]] = field(default_factory=list)
    total_files: int = 0
    avg_coupling: float = 0.0
    recommendations: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
class ArchParser:
    """
    解析 Python/TypeScript 项目的模块依赖结构。

    用法:
        parser = ArchParser()
        report = parser.parse("D:/wenstar/wenstar_os")
    """

    def __init__(self, ignore_patterns: Optional[List[str]] = None) -> None:
        self._ignore = ignore_patterns or [
            "__pycache__", ".git", "node_modules", ".venv",
            "dist", "build", ".tianquan",
        ]

    # ------------------------------------------------------------------
    def parse(self, root: str) -> ArchReport:
        root_path = Path(root).resolve()
        report = ArchReport(root=str(root_path))

        py_files: List[Path] = []
        for dirpath, dirnames, filenames in os.walk(root_path):
            dirnames[:] = [d for d in dirnames if d not in self._ignore]
            for f in filenames:
                if f.endswith(".py"):
                    py_files.append(Path(dirpath) / f)

        report.total_files = len(py_files)

        # 第一遍: 构建模块信息
        for fpath in py_files:
            mod = self._parse_file(fpath, root_path)
            report.modules[mod.path] = mod

        # 第二遍: 计算反向引用
        for mod in report.modules.values():
            for imp in mod.imports:
                if imp in report.modules:
                    report.modules[imp].imported_by.append(mod.path)

        # 第三遍: 检测循环依赖 + 计算耦合度
        report.cycles = self._detect_cycles(report.modules)

        for mod in report.modules.values():
            out_degree = len(set(mod.imports))
            in_degree = len(set(mod.imported_by))
            total = len(report.modules)
            mod.coupling_score = self._calc_coupling(out_degree, in_degree, total)

        scores = [m.coupling_score for m in report.modules.values()]
        report.avg_coupling = sum(scores) / len(scores) if scores else 0.0

        # 生成建议
        report.recommendations = self._generate_recommendations(report)

        return report

    # ------------------------------------------------------------------
    def _parse_file(self, fpath: Path, root: Path) -> ModuleInfo:
        rel = str(fpath.relative_to(root)).replace("\\", "/")
        mod_name = rel.replace("/", ".").replace(".py", "")

        imports: List[str] = []
        exports: List[str] = []

        try:
            with open(fpath, "r", encoding="utf-8") as fh:
                source = fh.read()
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError):
            return ModuleInfo(path=rel, name=mod_name)

        for node in ast.walk(tree):
            # import xxx / from xxx import yyy
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
            # def xxx / class xxx → exports
            elif isinstance(node, ast.FunctionDef):
                if not node.name.startswith("_"):
                    exports.append(node.name)
            elif isinstance(node, ast.ClassDef):
                if not node.name.startswith("_"):
                    exports.append(node.name)
            # 顶层赋值也视为导出
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if not target.id.startswith("_"):
                            exports.append(target.id)

        imports = [i for i in imports if not i.startswith("_")]

        return ModuleInfo(
            path=rel,
            name=mod_name,
            imports=list(dict.fromkeys(imports)),
            exports=list(dict.fromkeys(exports)),
        )

    # ------------------------------------------------------------------
    def _detect_cycles(self, modules: Dict[str, ModuleInfo]) -> List[List[str]]:
        """
        DFS 检测循环依赖。

        只考虑项目内部模块间的引用（module paths 在 modules 字典中的）。
        """
        adj: Dict[str, List[str]] = {}
        for path, mod in modules.items():
            adj[path] = []
            for imp in mod.imports:
                if imp in modules:
                    adj[path].append(imp)

        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {p: WHITE for p in adj}
        parent: Dict[str, Optional[str]] = {p: None for p in adj}
        cycles: List[List[str]] = []

        def dfs(u: str) -> None:
            color[u] = GRAY
            for v in adj.get(u, []):
                if color.get(v) == GRAY:
                    # 找到环 — 回溯路径
                    cycle: List[str] = [v, u]
                    cur = u
                    while parent.get(cur) and parent[cur] != v:
                        cur = parent[cur]  # type: ignore
                        cycle.append(cur)
                    cycle.append(v)
                    cycle.reverse()
                    cycles.append(cycle)
                elif color.get(v) == WHITE:
                    parent[v] = u
                    dfs(v)
            color[u] = BLACK

        for node in adj:
            if color.get(node) == WHITE:
                dfs(node)

        # 去重（同一个环的不同起点）
        unique: List[List[str]] = []
        seen: Set[str] = set()
        for cycle in cycles:
            sig = "|".join(sorted(cycle))
            if sig not in seen:
                seen.add(sig)
                unique.append(cycle)

        return unique

    # ------------------------------------------------------------------
    @staticmethod
    def _calc_coupling(out_degree: int, in_degree: int, total: int) -> float:
        if total <= 1:
            return 0.0
        max_possible = (total - 1) * 2
        raw = (out_degree + in_degree) / max_possible
        return round(min(raw, 1.0), 4)

    # ------------------------------------------------------------------
    def _generate_recommendations(self, report: ArchReport) -> List[str]:
        recs: List[str] = []

        if report.cycles:
            recs.append(f"发现 {len(report.cycles)} 个循环依赖，建议优先解环")

        heavy = [
            (path, mod.coupling_score)
            for path, mod in report.modules.items()
            if mod.coupling_score > 0.5
        ]
        if heavy:
            recs.append(f"{len(heavy)} 个模块耦合度 > 0.5，建议隔离接口")

        if report.avg_coupling > 0.3:
            recs.append(f"平均耦合度 {report.avg_coupling:.3f} 偏高")

        return recs


# ---------------------------------------------------------------------------
def quick_parse(root: str) -> ArchReport:
    """快捷解析——一次调用获取完整报告。"""
    return ArchParser().parse(root)
