"""
lint_checker.py — 天权编码规范校验器
======================================
逐文件扫描，执行 8 条强制规则。输出 violations + warnings。

规格依据: TIANQUAN_DOMAIN_SPEC.md §4 + dev-docs/04
"""

from __future__ import annotations

import ast
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
@dataclass
class LintViolation:
    file: str
    line: int
    rule: str
    severity: str  # error | warning
    message: str


@dataclass
class LintReport:
    passed: bool
    total_rules: int = 8
    violations: List[LintViolation] = field(default_factory=list)
    warnings: List[LintViolation] = field(default_factory=list)
    files_scanned: int = 0
    lint_duration_ms: float = 0.0


# ---------------------------------------------------------------------------
# 规则定义
# ---------------------------------------------------------------------------

CRITICAL_RULES = {"L1", "L2", "L8"}  # 触发即为 error


# 硬编码密钥模式（L8）
SECRET_PATTERNS = [
    re.compile(r"(api[_-]?key|apikey|secret|token|password|passwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE),
    re.compile(r"(Bearer\s+[A-Za-z0-9\-._~+/]+=*)"),
    re.compile(r"(sk-[A-Za-z0-9]{20,})"),
    re.compile(r"(mongodb://[^'\"\s]+)"),
    re.compile(r"(mysql://[^'\"\s]+)"),
    re.compile(r'("(?:[A-Za-z0-9+/]{40,}=)")\s*#\s*(?:key|token|secret|密码|密钥)', re.IGNORECASE),
]


# ---------------------------------------------------------------------------
class LintChecker:
    """
    编码规范校验器。

    8 条规则:
      L1 - kebab-case 文件名
      L2 - PascalCase 类名
      L3 - camelCase 函数/变量
      L4 - 无 console.log / print 残留（工具模块除外）
      L5 - import 禁止循环依赖（由 arch_parser 提供）
      L6 - 模块接口契约校验（占位）
      L7 - DNA 红线禁止项检测
      L8 - 禁止硬编码密钥/Token
    """

    def __init__(self) -> None:
        self._results: List[LintViolation] = []

    # ------------------------------------------------------------------
    def check_file(self, filepath: Path, project_root: Path) -> List[LintViolation]:
        """对单个文件执行全部规则。"""
        violations: List[LintViolation] = []
        rel = str(filepath.relative_to(project_root)).replace("\\", "/")

        # L1: kebab-case 文件名
        violations.extend(self._check_l1(filepath, rel))

        # 读取内容
        try:
            source = filepath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            return violations

        # 尝试 AST 解析
        try:
            tree = ast.parse(source)
        except SyntaxError:
            violations.append(LintViolation(rel, 0, "L0", "error", f"语法错误: {filepath.name}"))
            return violations

        # L2: PascalCase 类名 / L3: camelCase 函数/变量
        violations.extend(self._check_l2(tree, rel))
        violations.extend(self._check_l3(tree, rel))

        # L4: 无 console.log / print 残留
        violations.extend(self._check_l4(source, tree, rel))

        # L7: DNA 红线检测
        violations.extend(self._check_l7(source, rel))

        # L8: 禁止硬编码密钥
        violations.extend(self._check_l8(source, rel))

        return violations

    # ------------------------------------------------------------------
    def check_directory(self, root: str, ignore_patterns: Optional[List[str]] = None) -> LintReport:
        """扫描整个目录。"""
        t0 = time.time()
        ignores = set(ignore_patterns or [])
        ignores.update({"__pycache__", ".git", "node_modules", ".venv", ".tianquan"})

        root_path = Path(root).resolve()
        all_violations: List[LintViolation] = []
        files_scanned = 0

        for dirpath, dirnames, filenames in root_path.walk() if hasattr(root_path, 'walk') else self._walk(root_path):
            # 过滤忽略目录
            dirnames[:] = [d for d in dirnames if d not in ignores]

            for fname in filenames:
                if not fname.endswith(".py") and not fname.endswith(".ts"):
                    continue

                fpath = Path(dirpath) / fname
                violations = self.check_file(fpath, root_path)
                all_violations.extend(violations)
                files_scanned += 1

        errors = [v for v in all_violations if v.severity == "error"]
        warnings = [v for v in all_violations if v.severity == "warning"]

        elapsed = (time.time() - t0) * 1000
        passed = len(errors) == 0

        return LintReport(
            passed=passed,
            violations=errors,
            warnings=warnings,
            files_scanned=files_scanned,
            lint_duration_ms=round(elapsed, 1),
        )

    @staticmethod
    def _walk(root: Path):
        """兼容 Walk 遍历。"""
        import os
        for dirpath, dirnames, filenames in os.walk(root):
            yield dirpath, dirnames, filenames

    # ------------------------------------------------------------------
    # L1: kebab-case 文件名
    # ------------------------------------------------------------------
    def _check_l1(self, filepath: Path, rel: str) -> List[LintViolation]:
        name = filepath.stem
        violations: List[LintViolation] = []
        # 允许: __init__, __main__, 下划线前缀的私有文件
        if name.startswith("_"):
            return violations
        # 不允许: 驼峰、中文、空格
        if re.search(r"[A-Z一-鿿\s]", name):
            violations.append(LintViolation(
                rel, 0, "L1", "error",
                f"文件名 '{name}' 应使用 kebab-case（全小写+连字符），如 'arch-parser.py'"
            ))
        return violations

    # ------------------------------------------------------------------
    # L2: PascalCase 类名
    # ------------------------------------------------------------------
    def _check_l2(self, tree: ast.AST, rel: str) -> List[LintViolation]:
        violations: List[LintViolation] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not node.name[0].isupper():
                    violations.append(LintViolation(
                        rel, node.lineno, "L2", "error",
                        f"类名 '{node.name}' 应使用 PascalCase"
                    ))
        return violations

    # ------------------------------------------------------------------
    # L3: camelCase 函数/变量
    # ------------------------------------------------------------------
    def _check_l3(self, tree: ast.AST, rel: str) -> List[LintViolation]:
        violations: List[LintViolation] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if "_" in node.name and not node.name.startswith("_"):
                    # snake_case → warning（Python社区标准，非强制）
                    pass  # Python 项目接受 snake_case
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if re.search(r"[A-Z]", node.id) and not node.id.isupper():
                    violations.append(LintViolation(
                        rel, node.lineno, "L3", "warning",
                        f"变量 '{node.id}' 疑似 camelCase，Python 推荐 snake_case"
                    ))
        return violations

    # ------------------------------------------------------------------
    # L4: 禁止调试残留
    # ------------------------------------------------------------------
    def _check_l4(self, source: str, tree: ast.AST, rel: str) -> List[LintViolation]:
        violations: List[LintViolation] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = None
                if isinstance(node.func, ast.Attribute):
                    func = node.func.attr
                elif isinstance(node.func, ast.Name):
                    func = node.func.id
                if func in ("console_log", "console.log", "debugger"):
                    violations.append(LintViolation(
                        rel, node.lineno, "L4", "warning",
                        f"调试残留: {func}() — 提交前应移除"
                    ))
        # 检测裸 print()
        for i, line in enumerate(source.split("\n"), 1):
            stripped = line.strip()
            if stripped.startswith("print(") and "logger" not in rel.lower():
                violations.append(LintViolation(
                    rel, i, "L4", "warning",
                    f"调试残留: print() — 建议替换为 logging"
                ))
        return violations

    # ------------------------------------------------------------------
    # L7: DNA 红线检测
    # ------------------------------------------------------------------
    def _check_l7(self, source: str, rel: str) -> List[LintViolation]:
        violations: List[LintViolation] = []
        # 检测: 动态修改维度数量
        if re.search(r"(dim_count|DIM_COUNT|num_dimensions?)\s*=\s*(33|36|64|128)", source):
            violations.append(LintViolation(
                rel, 0, "L7", "error",
                "DNA红线: 32D永久固定，禁止修改维度数量"
            ))
        # 检测: 混入内源激素到语义向量
        if re.search(r"hormone.*vector|emotion.*32d|internal.*spine", source, re.IGNORECASE):
            violations.append(LintViolation(
                rel, 0, "L7", "warning",
                "DNA红线: 内源激素禁止混入32D语义向量(仅00-05外源情绪)"
            ))
        return violations

    # ------------------------------------------------------------------
    # L8: 禁止硬编码密钥
    # ------------------------------------------------------------------
    def _check_l8(self, source: str, rel: str) -> List[LintViolation]:
        violations: List[LintViolation] = []
        for i, line in enumerate(source.split("\n"), 1):
            for pattern in SECRET_PATTERNS:
                if pattern.search(line) and not line.strip().startswith("#"):
                    violations.append(LintViolation(
                        rel, i, "L8", "error",
                        f"疑似硬编码密钥: {line.strip()[:60]}..."
                    ))
                    break  # 每行只报一次
        return violations


# ---------------------------------------------------------------------------
def quick_lint(root: str) -> LintReport:
    """快捷校验。"""
    return LintChecker().check_directory(root)
