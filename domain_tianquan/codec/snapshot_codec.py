"""
snapshot_codec.py — 天权工程快照序列化器
==========================================
将项目状态编码为 .snap 文件，供架构重构前/后对比。

规格依据: TIANQUAN_DOMAIN_SPEC.md §5
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
@dataclass
class EngineeringSnapshot:
    snapshot_id: str          # SNAP-{timestamp}-{hash6}
    project_root: str
    file_count: int
    file_list: List[str] = field(default_factory=list)
    file_checksums: Dict[str, str] = field(default_factory=dict)
    arch_report_json: Optional[str] = None    # ArchReport.to_json()
    sql_audit_json: Optional[str] = None      # SQLAuditReport.to_json()
    timestamp: str = ""
    crc32: str = ""


# ---------------------------------------------------------------------------
class SnapshotCodec:
    """
    工程快照编码/解码器。

    用法:
        codec = SnapshotCodec("D:/wenstar/wenstar_os")
        snap = codec.capture()
        codec.save(snap)                    # → .tianquan/snapshots/SNAP-*.snap
        loaded = codec.load(snapshot_id)
    """

    SNAPSHOT_DIR = ".tianquan/snapshots"
    MAX_SNAPSHOTS = 30

    def __init__(self, project_root: str) -> None:
        self.root = Path(project_root).resolve()
        self._snap_dir = self.root / self.SNAPSHOT_DIR

    # ------------------------------------------------------------------
    def capture(
        self,
        include_patterns: Optional[List[str]] = None,
        arch_report_json: Optional[str] = None,
        sql_audit_json: Optional[str] = None,
    ) -> EngineeringSnapshot:
        """
        捕获当前项目状态。

        Args:
            include_patterns: 包含的文件模式，默认 ["*.py", "*.yaml", "*.md", "*.json", "*.ts"]
            arch_report_json: 附加的架构报告（来自 arch_parser）
            sql_audit_json: 附加的 SQL 审计报告
        """
        patterns = include_patterns or ["*.py", "*.yaml", "*.md", "*.json", "*.ts"]
        ignores = {"__pycache__", ".git", "node_modules", ".venv", ".tianquan", "dist", "build"}

        files: List[Path] = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in ignores]
            for fname in filenames:
                if any(fname.endswith(p.replace("*", "")) for p in patterns):
                    files.append(Path(dirpath) / fname)

        file_list: List[str] = []
        checksums: Dict[str, str] = {}

        for fpath in files:
            rel = str(fpath.relative_to(self.root)).replace("\\", "/")
            file_list.append(rel)
            try:
                content = fpath.read_bytes()
                checksums[rel] = hashlib.sha256(content).hexdigest()[:16]
            except Exception:
                checksums[rel] = "READ_ERROR"

        ts = int(time.time())
        ts_str = time.strftime("%Y%m%d-%H%M%S", time.localtime(ts))

        # 生成 snapshot_id
        raw = json.dumps({"ts": ts, "root": str(self.root), "count": len(file_list)}, sort_keys=True)
        hash6 = hashlib.sha256(raw.encode()).hexdigest()[:6]

        snap = EngineeringSnapshot(
            snapshot_id=f"SNAP-{ts_str}-{hash6}",
            project_root=str(self.root),
            file_count=len(file_list),
            file_list=sorted(file_list),
            file_checksums=checksums,
            arch_report_json=arch_report_json,
            sql_audit_json=sql_audit_json,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(ts)),
        )

        # CRC32
        payload = json.dumps(snap.file_checksums, sort_keys=True)
        snap.crc32 = format(self._crc32(payload), "08x")

        return snap

    # ------------------------------------------------------------------
    def save(self, snap: EngineeringSnapshot) -> Path:
        """保存快照到 .snap 文件。"""
        self._snap_dir.mkdir(parents=True, exist_ok=True)

        data = json.dumps(self._snap_to_dict(snap), ensure_ascii=False, indent=2)
        compressed = gzip.compress(data.encode("utf-8"))

        fpath = self._snap_dir / f"{snap.snapshot_id}.snap"
        fpath.write_bytes(compressed)

        # 清理旧快照
        self._cleanup_old()

        return fpath

    # ------------------------------------------------------------------
    def load(self, snapshot_id: str) -> Optional[EngineeringSnapshot]:
        """从 .snap 文件加载快照。"""
        fpath = self._snap_dir / f"{snapshot_id}.snap"
        if not fpath.exists():
            return None

        compressed = fpath.read_bytes()
        data = json.loads(gzip.decompress(compressed).decode("utf-8"))
        return self._dict_to_snap(data)

    # ------------------------------------------------------------------
    def list_snapshots(self) -> List[str]:
        """列出所有快照 ID（按时间倒序）。"""
        if not self._snap_dir.exists():
            return []
        snaps = sorted(
            [f.stem for f in self._snap_dir.glob("SNAP-*.snap")],
            reverse=True,
        )
        return snaps

    # ------------------------------------------------------------------
    def diff(self, snap1_id: str, snap2_id: str) -> Dict[str, Any]:
        """对比两个快照的差异。"""
        s1 = self.load(snap1_id)
        s2 = self.load(snap2_id)
        if not s1 or not s2:
            return {"error": "快照不存在"}

        files1 = set(s1.file_list)
        files2 = set(s2.file_list)

        added = sorted(files2 - files1)
        removed = sorted(files1 - files2)
        changed = []

        for f in sorted(files1 & files2):
            if s1.file_checksums.get(f) != s2.file_checksums.get(f):
                changed.append(f)

        return {
            "snap1": snap1_id,
            "snap2": snap2_id,
            "file_count_diff": len(files2) - len(files1),
            "added": added,
            "removed": removed,
            "changed": changed,
            "added_count": len(added),
            "removed_count": len(removed),
            "changed_count": len(changed),
        }

    # ------------------------------------------------------------------
    def _cleanup_old(self) -> None:
        snaps = sorted(self._snap_dir.glob("SNAP-*.snap"), key=os.path.getmtime, reverse=True)
        for old in snaps[self.MAX_SNAPSHOTS:]:
            old.unlink()

    # ------------------------------------------------------------------
    @staticmethod
    def _snap_to_dict(snap: EngineeringSnapshot) -> Dict[str, Any]:
        return {
            "snapshot_id": snap.snapshot_id,
            "project_root": snap.project_root,
            "file_count": snap.file_count,
            "file_list": snap.file_list,
            "file_checksums": snap.file_checksums,
            "arch_report_json": snap.arch_report_json,
            "sql_audit_json": snap.sql_audit_json,
            "timestamp": snap.timestamp,
            "crc32": snap.crc32,
        }

    @staticmethod
    def _dict_to_snap(data: Dict[str, Any]) -> EngineeringSnapshot:
        return EngineeringSnapshot(
            snapshot_id=data.get("snapshot_id", ""),
            project_root=data.get("project_root", ""),
            file_count=data.get("file_count", 0),
            file_list=data.get("file_list", []),
            file_checksums=data.get("file_checksums", {}),
            arch_report_json=data.get("arch_report_json"),
            sql_audit_json=data.get("sql_audit_json"),
            timestamp=data.get("timestamp", ""),
            crc32=data.get("crc32", ""),
        )

    @staticmethod
    def _crc32(data: str) -> int:
        """计算 CRC32。"""
        crc = 0xFFFFFFFF
        for byte in data.encode("utf-8"):
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xEDB88320
                else:
                    crc >>= 1
        return crc ^ 0xFFFFFFFF


# ---------------------------------------------------------------------------
def capture_snapshot(project_root: str) -> EngineeringSnapshot:
    """快捷捕获快照。"""
    return SnapshotCodec(project_root).capture()


def save_snapshot(project_root: str, snap: Optional[EngineeringSnapshot] = None) -> Path:
    """快捷保存快照。"""
    codec = SnapshotCodec(project_root)
    return codec.save(snap or codec.capture())
