"""
doc_generator.py — 天权变更报告自动生成器
===========================================
生成四段式变更报告（摘要 / 详情 / 影响面 / 验证方法）。

规格依据:
  - TIANQUAN_DOMAIN_SPEC.md §3.4
  - 标准变更报告规则（change-report-rule.md）
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
class ChangeType(Enum):
    FEATURE = "feature"
    FIX = "fix"
    REFACTOR = "refactor"
    PERF = "perf"
    SECURITY = "security"
    DOCS = "docs"


CHANGE_TYPE_LABELS: Dict[str, str] = {
    "feature": "新功能",
    "fix": "缺陷修复",
    "refactor": "重构",
    "perf": "性能优化",
    "security": "安全加固",
    "docs": "文档更新",
}


@dataclass
class ChangeReport:
    """四段式变更报告。"""
    title: str
    change_type: ChangeType
    author: str
    timestamp: str = ""
    module_tags: List[str] = field(default_factory=list)

    # 四段内容
    summary: str = ""            # 做了什么
    details: str = ""            # 具体内容
    impact: str = ""             # 影响范围
    verification: str = ""       # 如何验证

    # 元数据
    affected_files: List[str] = field(default_factory=list)
    related_docs: List[str] = field(default_factory=list)
    breaking_change: bool = False
    version: str = "1.0"


# ---------------------------------------------------------------------------
class DocGenerator:
    """
    变更报告生成器。

    用法:
        gen = DocGenerator()
        report = gen.generate(
            title="修复五级闸门G2时空校验bug",
            change_type=ChangeType.FIX,
            author="天权-Harris",
            details="G2的location_fingerprint比对逻辑使用了大小写敏感匹配...",
            impact="仅影响M4检索管线，不影响存储层",
            affected_files=["src/gate/five_stage_gate.ts"],
        )
    """

    def generate(
        self,
        title: str,
        change_type: ChangeType,
        author: str,
        summary: str = "",
        details: str = "",
        impact: str = "",
        verification: str = "",
        affected_files: Optional[List[str]] = None,
        related_docs: Optional[List[str]] = None,
        breaking_change: bool = False,
        module_tags: Optional[List[str]] = None,
    ) -> ChangeReport:
        report = ChangeReport(
            title=title,
            change_type=change_type,
            author=author,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
            module_tags=module_tags or [],
            summary=summary or self._auto_summary(title, change_type),
            details=details,
            impact=impact or "待评估",
            verification=verification or self._default_verification(change_type),
            affected_files=affected_files or [],
            related_docs=related_docs or [],
            breaking_change=breaking_change,
        )
        return report

    # ------------------------------------------------------------------
    def to_markdown(self, report: ChangeReport) -> str:
        """渲染为 Markdown 四段式变更报告。"""
        lines = [
            f"# 变更报告: {report.title}",
            "",
            f"| 字段 | 内容 |",
            f"|------|------|",
            f"| 类型 | {CHANGE_TYPE_LABELS.get(report.change_type.value, report.change_type.value)} |",
            f"| 作者 | {report.author} |",
            f"| 时间 | {report.timestamp} |",
            f"| 破坏性变更 | {'⚠️ 是' if report.breaking_change else '否'} |",
        ]

        if report.module_tags:
            lines.append(f"| 模块 | {', '.join(report.module_tags)} |")

        if report.affected_files:
            lines.append("")
            lines.append("## 涉及文件")
            for f in report.affected_files:
                lines.append(f"- `{f}`")

        lines.extend([
            "",
            "## 一、变更摘要",
            report.summary or "(待补充)",
            "",
            "## 二、变更详情",
            report.details or "(待补充)",
            "",
            "## 三、影响范围",
            report.impact or "待评估",
            "",
            "## 四、验证方法",
            report.verification,
        ])

        if report.related_docs:
            lines.append("")
            lines.append("## 相关文档")
            for doc in report.related_docs:
                lines.append(f"- {doc}")

        lines.extend([
            "",
            "---",
            f"*报告由天权域 Harris 引擎自动生成 · {report.timestamp}*",
        ])

        return "\n".join(lines)

    # ------------------------------------------------------------------
    @staticmethod
    def _auto_summary(title: str, change_type: ChangeType) -> str:
        prefix = CHANGE_TYPE_LABELS.get(change_type.value, "变更")
        return f"{prefix}: {title}"

    @staticmethod
    def _default_verification(change_type: ChangeType) -> str:
        if change_type == ChangeType.FIX:
            return "1. 复现原始bug场景\n2. 确认修复后不再触发\n3. 回归相关用例"
        if change_type == ChangeType.FEATURE:
            return "1. 按验收标准逐条测试\n2. 性能基准对比\n3. 集成测试全链路"
        if change_type == ChangeType.REFACTOR:
            return "1. 全量单元测试通过\n2. 接口签名无变化\n3. 性能无退化"
        return "1. 单元测试通过\n2. 人工Review确认"


# ---------------------------------------------------------------------------
def generate_change_report(
    title: str,
    change_type: ChangeType,
    author: str = "天权-Harris",
    **kwargs,
) -> str:
    """快捷生成 Markdown 变更报告。"""
    gen = DocGenerator()
    report = gen.generate(title, change_type, author, **kwargs)
    return gen.to_markdown(report)
