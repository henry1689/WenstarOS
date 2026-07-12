"""
test_validator.py — 天权校验器测试
===================================
验证 lint_checker 8 条规则的正/反向用例。
"""

import sys
import tempfile
from pathlib import Path

_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from validator.lint_checker import LintChecker


def test_linter_basic():
    """在临时目录创建测试文件，验证 lint 检测能力。"""
    import os
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # 违规文件: 驼峰命名 (L1)
        bad_file = root / "BadName.py"
        bad_file.write_text('API_KEY = "sk-1234567890abcdef1234567890abcdef1234567890ab"\nprint("hello")\n', encoding="utf-8")

        # 合规文件
        good_file = root / "good-module.py"
        good_file.write_text('"""Good module."""\n\nfrom typing import Optional\n\nclass MyClass:\n    def my_method(self, x: int) -> int:\n        return x\n', encoding="utf-8")

        checker = LintChecker()
        report = checker.check_directory(str(root))

        assert report.files_scanned == 2, f"应扫描2个文件，实际{report.files_scanned}"
        # BadName.py 应触犯 L1(文件名) + L4(print) + L8(密钥)
        bad_violations = [v for v in report.violations if "BadName" in v.file]
        assert len(bad_violations) >= 2, f"BadName.py 应至少有 L1+L8 违规，实际 {len(bad_violations)}"
        print(f"  ✅ lint_scanner: {report.files_scanned} files, {len(report.violations)} errors, {len(report.warnings)} warnings")

        # 验证通过（无error才passed）
        assert not report.passed, "应有 error 级违规"
        print(f"  ✅ lint_passed={report.passed}, duration={report.lint_duration_ms}ms")


def test_l1_kebab_case_detection():
    """L1: 驼峰文件名检测。"""
    root = Path(tempfile.mkdtemp())
    try:
        (root / "MyModule.py").write_text("x = 1", encoding="utf-8")
        checker = LintChecker()
        violations = checker.check_file(root / "MyModule.py", root)
        l1_errors = [v for v in violations if v.rule == "L1"]
        assert len(l1_errors) >= 1, "驼峰文件名应触犯 L1"
        print(f"  ✅ L1: 驼峰 → {l1_errors[0].message}")
    finally:
        import shutil
        shutil.rmtree(root, ignore_errors=True)


def test_l8_secret_detection():
    """L8: 硬编码密钥检测。"""
    root = Path(tempfile.mkdtemp())
    try:
        bad = root / "config.py"
        bad.write_text('api_key = "sk-1234567890abcdefghij"\n', encoding="utf-8")
        checker = LintChecker()
        violations = checker.check_file(bad, root)
        l8_errors = [v for v in violations if v.rule == "L8"]
        assert len(l8_errors) >= 1, "硬编码密钥应触犯 L8"
        print(f"  ✅ L8: 密钥 → {l8_errors[0].message[:60]}")
    finally:
        import shutil
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    test_linter_basic()
    test_l1_kebab_case_detection()
    test_l8_secret_detection()
    print("\n🎉 天权校验器测试全部通过")
