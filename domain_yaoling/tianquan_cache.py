"""
tianquan_cache.py — 太虚境本地缓存模块
========================================
当天权 MCP (harris-t) 离线时，将 32D 快照保存到本地 JSON 文件。
太虚境上线后可通过 query_global_memory 同步。

格式: 每条记录为一份完整的 Protobuf 就绪 dict + 发射元数据
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════
# 缓存文件配置
# ═══════════════════════════════════════════════════════════════

CACHE_DIR = Path(__file__).resolve().parent / "cache"
CACHE_FILE = CACHE_DIR / "tianquan_offline_queue.json"
MAX_CACHE_ENTRIES = 500  # 最多保留 500 条待同步快照


# ═══════════════════════════════════════════════════════════════
# 缓存条目
# ═══════════════════════════════════════════════════════════════


@dataclass
class CacheEntry:
    dna_root_id: str
    timestamp: str
    location_fingerprint: str
    snapshot_summary: Dict[str, Any]  # vital_signs + overall_health
    protobuf_dict: Dict[str, Any]     # 完整快照
    yaoguang_source: str              # "live" | "fallback"
    emission_attempted: bool = False
    emission_error: str = ""
    synced: bool = False
    synced_at: str = ""


class TianquanCache:
    """太虚境本地缓存管理器。"""

    def __init__(self) -> None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._entries: List[CacheEntry] = []
        self._load()

    # ------------------------------------------------------------------
    # 写入
    # ------------------------------------------------------------------

    def store(
        self,
        dna_root_id: str,
        location_fingerprint: str,
        snapshot_summary: Dict[str, Any],
        protobuf_dict: Dict[str, Any],
        yaoguang_source: str = "fallback",
    ) -> CacheEntry:
        """将 32D 快照存入本地缓存队列。"""
        entry = CacheEntry(
            dna_root_id=dna_root_id,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
            location_fingerprint=location_fingerprint,
            snapshot_summary=snapshot_summary,
            protobuf_dict=protobuf_dict,
            yaoguang_source=yaoguang_source,
        )
        self._entries.append(entry)
        # 超出上限时淘汰最旧的
        if len(self._entries) > MAX_CACHE_ENTRIES:
            self._entries = self._entries[-MAX_CACHE_ENTRIES:]
        self._save()
        return entry

    # ------------------------------------------------------------------
    # 读取
    # ------------------------------------------------------------------

    def get_unsynced(self) -> List[CacheEntry]:
        """获取所有未同步到太虚境的缓存条目。"""
        return [e for e in self._entries if not e.synced]

    def count_unsynced(self) -> int:
        return len(self.get_unsynced())

    def get_by_dna_root_id(self, dna_root_id: str) -> Optional[CacheEntry]:
        for e in self._entries:
            if e.dna_root_id == dna_root_id:
                return e
        return None

    # ------------------------------------------------------------------
    # 同步
    # ------------------------------------------------------------------

    def mark_synced(self, dna_root_id: str) -> bool:
        """标记某条快照已同步到太虚境。"""
        for e in self._entries:
            if e.dna_root_id == dna_root_id:
                e.synced = True
                e.synced_at = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
                self._save()
                return True
        return False

    def mark_emission_attempted(self, dna_root_id: str, error: str = "") -> bool:
        for e in self._entries:
            if e.dna_root_id == dna_root_id:
                e.emission_attempted = True
                e.emission_error = error
                self._save()
                return True
        return False

    # ------------------------------------------------------------------
    # 状态
    # ------------------------------------------------------------------

    def status(self) -> Dict[str, Any]:
        return {
            "cache_file": str(CACHE_FILE),
            "total_entries": len(self._entries),
            "unsynced": self.count_unsynced(),
            "synced": sum(1 for e in self._entries if e.synced),
            "oldest_entry": self._entries[0].timestamp if self._entries else None,
            "newest_entry": self._entries[-1].timestamp if self._entries else None,
        }

    # ------------------------------------------------------------------
    # 持久化
    # ------------------------------------------------------------------

    def _save(self) -> None:
        data = []
        for e in self._entries:
            data.append({
                "dna_root_id": e.dna_root_id,
                "timestamp": e.timestamp,
                "location_fingerprint": e.location_fingerprint,
                "snapshot_summary": e.snapshot_summary,
                "protobuf_dict": e.protobuf_dict,
                "yaoguang_source": e.yaoguang_source,
                "emission_attempted": e.emission_attempted,
                "emission_error": e.emission_error,
                "synced": e.synced,
                "synced_at": e.synced_at,
            })
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self) -> None:
        if not CACHE_FILE.exists():
            self._entries = []
            return
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self._entries = []
            for item in raw:
                self._entries.append(CacheEntry(
                    dna_root_id=item["dna_root_id"],
                    timestamp=item["timestamp"],
                    location_fingerprint=item["location_fingerprint"],
                    snapshot_summary=item["snapshot_summary"],
                    protobuf_dict=item["protobuf_dict"],
                    yaoguang_source=item.get("yaoguang_source", "fallback"),
                    emission_attempted=item.get("emission_attempted", False),
                    emission_error=item.get("emission_error", ""),
                    synced=item.get("synced", False),
                    synced_at=item.get("synced_at", ""),
                ))
        except (json.JSONDecodeError, KeyError):
            self._entries = []


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_tianquan_cache: Optional[TianquanCache] = None


def get_cache() -> TianquanCache:
    global _tianquan_cache
    if _tianquan_cache is None:
        _tianquan_cache = TianquanCache()
    return _tianquan_cache
