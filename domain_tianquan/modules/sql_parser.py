"""
sql_parser.py — 天权 SQL 解析与审计器
=======================================
输入 SQL 文件路径或文本，输出 Schema 报告（表/索引/外键/触发器等）。

规格依据: TIANQUAN_DOMAIN_SPEC.md §3.3
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
@dataclass
class TableInfo:
    name: str
    columns: List[Dict[str, str]] = field(default_factory=list)
    primary_key: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    is_without_rowid: bool = False


@dataclass
class IndexInfo:
    name: str
    table: str
    columns: List[str] = field(default_factory=list)
    unique: bool = False


@dataclass
class FKInfo:
    name: str
    from_table: str
    from_columns: List[str] = field(default_factory=list)
    to_table: str = ""
    to_columns: List[str] = field(default_factory=list)


@dataclass
class TriggerInfo:
    name: str
    table: str
    timing: str  # BEFORE/AFTER/INSTEAD OF
    event: str   # INSERT/UPDATE/DELETE


@dataclass
class SchemaReport:
    tables: Dict[str, TableInfo] = field(default_factory=dict)
    indexes: List[IndexInfo] = field(default_factory=list)
    foreign_keys: List[FKInfo] = field(default_factory=list)
    triggers: List[TriggerInfo] = field(default_factory=list)


@dataclass
class SQLAuditReport:
    schema: SchemaReport = field(default_factory=SchemaReport)
    naming_violations: List[str] = field(default_factory=list)
    missing_pk_tables: List[str] = field(default_factory=list)
    missing_index_warnings: List[str] = field(default_factory=list)
    redundant_indexes: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
class SQLParser:
    """
    解析 SQL DDL，提取 schema 元数据。

    用法:
        parser = SQLParser()
        report = parser.parse_file("schema.sql")
        report = parser.parse_text(open("schema.sql").read())
    """

    # 常见 SQL 关键字（不应作为表名/列名）
    SQL_KEYWORDS = {
        "select", "from", "where", "insert", "update", "delete", "create",
        "alter", "drop", "table", "index", "trigger", "view", "into",
        "values", "set", "order", "group", "by", "having", "limit",
        "join", "inner", "left", "right", "outer", "on", "and", "or",
        "not", "null", "default", "primary", "key", "foreign", "references",
        "check", "unique", "constraint", "without", "rowid",
    }

    # ------------------------------------------------------------------
    def parse_file(self, filepath: str) -> SchemaReport:
        with open(filepath, "r", encoding="utf-8") as fh:
            return self.parse_text(fh.read())

    def parse_text(self, sql_text: str) -> SchemaReport:
        report = SchemaReport()

        # 去除注释
        clean = re.sub(r"--.*$", "", sql_text, flags=re.MULTILINE)
        clean = re.sub(r"/\*.*?\*/", "", clean, flags=re.DOTALL)

        # 按分号分割语句
        statements = [s.strip() for s in clean.split(";") if s.strip()]

        for stmt in statements:
            stmt_upper = stmt.upper()

            # CREATE TABLE
            if re.match(r"CREATE\s+TABLE", stmt_upper):
                table = self._parse_create_table(stmt.lstrip())
                if table:
                    # 合并重复定义（先到为准）
                    if table.name not in report.tables:
                        report.tables[table.name] = table

            # CREATE INDEX / CREATE UNIQUE INDEX
            elif re.match(r"CREATE\s+(UNIQUE\s+)?INDEX", stmt_upper):
                idx = self._parse_create_index(stmt.lstrip())
                if idx:
                    report.indexes.append(idx)

            # CREATE TRIGGER
            elif re.match(r"CREATE\s+TRIGGER", stmt_upper):
                trig = self._parse_create_trigger(stmt.lstrip())
                if trig:
                    report.triggers.append(trig)

        # 从 CREATE TABLE 中提取内联外键
        for table in report.tables.values():
            for constraint in table.constraints:
                fk = self._parse_inline_fk(constraint, table.name)
                if fk:
                    report.foreign_keys.append(fk)

        return report

    # ------------------------------------------------------------------
    def _parse_create_table(self, stmt: str) -> Optional[TableInfo]:
        # CREATE TABLE [IF NOT EXISTS] name ( ... )
        m = re.match(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\((.*)\)\s*(WITHOUT\s+ROWID)?",
            stmt, re.IGNORECASE | re.DOTALL,
        )
        if not m:
            return None

        name = m.group(1)
        body = m.group(2)
        without_rowid = bool(m.group(3))

        # 跳过 CREATE TABLE ... AS SELECT
        if "SELECT" in body.upper() and "AS" in stmt.upper():
            return TableInfo(name=name, is_without_rowid=without_rowid)

        table = TableInfo(name=name, is_without_rowid=without_rowid)

        # 解析列定义和约束（逐层切割，避免嵌套括号误伤）
        parts = self._split_table_body(body)
        for part in parts:
            part_stripped = part.strip()
            part_upper = part_stripped.upper()

            if part_upper.startswith("PRIMARY KEY"):
                pk_cols = re.findall(r"(\w+)", part_stripped)[1:]  # 跳过 "PRIMARY" "KEY"
                table.primary_key = pk_cols
            elif part_upper.startswith("FOREIGN KEY") or part_upper.startswith("CONSTRAINT"):
                table.constraints.append(part_stripped)
            elif part_upper.startswith("CHECK"):
                table.constraints.append(part_stripped)
            elif part_upper.startswith("UNIQUE"):
                pass  # 已在 column 级别处理
            else:
                # 列定义: name type [constraints...]
                col_match = re.match(r"(\w+)\s+(\w+(?:\s*\([^)]*\))?)\s*(.*)", part_stripped, re.DOTALL)
                if col_match:
                    col_name = col_match.group(1)
                    col_type = col_match.group(2)
                    col_rest = col_match.group(3).upper()
                    col_info = {"name": col_name, "type": col_type}
                    if "PRIMARY KEY" in col_rest:
                        table.primary_key = [col_name]
                    table.columns.append(col_info)

        return table

    @staticmethod
    def _split_table_body(body: str) -> List[str]:
        """按逗号切割 CREATE TABLE 体，正确处理嵌套括号。"""
        parts: List[str] = []
        depth = 0
        current: List[str] = []
        for ch in body:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            if ch == "," and depth == 0:
                parts.append("".join(current))
                current = []
            else:
                current.append(ch)
        if current:
            parts.append("".join(current))
        return parts

    # ------------------------------------------------------------------
    def _parse_create_index(self, stmt: str) -> Optional[IndexInfo]:
        m = re.match(
            r"CREATE\s+(UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s+ON\s+(\w+)\s*\((.*)\)",
            stmt, re.IGNORECASE | re.DOTALL,
        )
        if not m:
            return None
        unique = bool(m.group(1))
        idx_name = m.group(2)
        table = m.group(3)
        cols_raw = m.group(4)
        cols = [c.strip().split()[0] for c in cols_raw.split(",")]
        return IndexInfo(name=idx_name, table=table, columns=cols, unique=unique)

    # ------------------------------------------------------------------
    def _parse_create_trigger(self, stmt: str) -> Optional[TriggerInfo]:
        m = re.match(
            r"CREATE\s+TRIGGER\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s+(BEFORE|AFTER|INSTEAD\s+OF)\s+(INSERT|UPDATE|DELETE)\s+ON\s+(\w+)",
            stmt, re.IGNORECASE,
        )
        if not m:
            return None
        return TriggerInfo(name=m.group(1), timing=m.group(2).upper(), event=m.group(3).upper(), table=m.group(4))

    # ------------------------------------------------------------------
    def _parse_inline_fk(self, constraint: str, from_table: str) -> Optional[FKInfo]:
        m = re.match(
            r"(?:CONSTRAINT\s+(\w+)\s+)?FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+(\w+)\s*\(([^)]+)\)",
            constraint, re.IGNORECASE,
        )
        if not m:
            return None
        fk_name = m.group(1) or f"fk_{from_table}_auto"
        from_cols = [c.strip() for c in m.group(2).split(",")]
        to_table = m.group(3)
        to_cols = [c.strip() for c in m.group(4).split(",")]
        return FKInfo(name=fk_name, from_table=from_table, from_columns=from_cols, to_table=to_table, to_columns=to_cols)


# ---------------------------------------------------------------------------
# 审计器
# ---------------------------------------------------------------------------


class SQLAuditor:
    """
    基于解析结果执行规范审计。

    用法:
        auditor = SQLAuditor()
        report = auditor.audit(parser.parse_file("schema.sql"))
    """

    def audit(self, schema: SchemaReport) -> SQLAuditReport:
        report = SQLAuditReport(schema=schema)

        for name, table in schema.tables.items():
            # 检查命名
            if name.lower() in SQLParser.SQL_KEYWORDS:
                report.naming_violations.append(f"表名 '{name}' 是 SQL 关键字")
            if name != name.lower():
                report.naming_violations.append(f"表名 '{name}' 应使用全小写 (snake_case)")

            # 检查主键
            if not table.primary_key:
                report.missing_pk_tables.append(name)

        # 检查索引冗余
        idx_signatures: Dict[str, str] = {}
        for idx in schema.indexes:
            sig = f"{idx.table}:{','.join(idx.columns)}"
            if sig in idx_signatures:
                report.redundant_indexes.append(f"索引 {idx.name} 与 {idx_signatures[sig]} 覆盖相同列")
            else:
                idx_signatures[sig] = idx.name

        # 检查外键列是否有索引
        indexed_cols: Dict[str, set] = {}
        for idx in schema.indexes:
            indexed_cols.setdefault(idx.table, set()).update(idx.columns)

        for fk in schema.foreign_keys:
            for col in fk.from_columns:
                if col not in indexed_cols.get(fk.from_table, set()):
                    report.missing_index_warnings.append(
                        f"外键 {fk.from_table}.{col} → {fk.to_table} 缺少索引"
                    )

        report.recommendations = self._gen_recommendations(report)
        return report

    @staticmethod
    def _gen_recommendations(report: SQLAuditReport) -> List[str]:
        recs: List[str] = []
        if report.missing_pk_tables:
            recs.append(f"{len(report.missing_pk_tables)} 张表缺少主键: {report.missing_pk_tables}")
        if report.redundant_indexes:
            recs.append(f"{len(report.redundant_indexes)} 组冗余索引")
        if report.missing_index_warnings:
            recs.append(f"{len(report.missing_index_warnings)} 处外键列缺少索引")
        if not recs:
            recs.append("Schema 审计通过，无问题")
        return recs


# ---------------------------------------------------------------------------
def quick_audit(sql_text: str) -> SQLAuditReport:
    """快捷审计 —— 一步完成解析 + 审计。"""
    parser = SQLParser()
    schema = parser.parse_text(sql_text)
    return SQLAuditor().audit(schema)
