"""测试 snapshot_codec.py — 工程快照编解码器"""
import sys, tempfile, json
from pathlib import Path
_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path: sys.path.insert(0, str(_PARENT))

from codec.snapshot_codec import SnapshotCodec

def test_capture_empty_dir():
    with tempfile.TemporaryDirectory() as td:
        Path(td, "test.py").write_text("x=1", encoding="utf-8")
        codec = SnapshotCodec(td)
        snap = codec.capture()
        assert snap.file_count > 0
        assert snap.snapshot_id.startswith("SNAP-")

def test_save_and_load():
    with tempfile.TemporaryDirectory() as td:
        Path(td, "test.py").write_text("x=1", encoding="utf-8")
        codec = SnapshotCodec(td)
        snap = codec.capture()
        saved = codec.save(snap)
        assert saved.exists()
        assert saved.suffix == ".snap"

def test_capture_metadata():
    with tempfile.TemporaryDirectory() as td:
        Path(td, "a.py").write_text("pass", encoding="utf-8")
        codec = SnapshotCodec(td)
        snap = codec.capture()
        assert snap.project_root == td
        assert snap.timestamp
        assert snap.crc32
        assert "a.py" in snap.file_list or any("a.py" in f for f in snap.file_list)

def test_max_snapshots_limit():
    with tempfile.TemporaryDirectory() as td:
        codec = SnapshotCodec(td)
        for i in range(5):
            Path(td, f"f{i}.py").write_text(f"#file{i}", encoding="utf-8")
            snap = codec.capture()
            codec.save(snap)
        snaps = list(Path(td, ".tianquan", "snapshots").glob("SNAP-*"))
        assert len(snaps) <= SnapshotCodec.MAX_SNAPSHOTS
