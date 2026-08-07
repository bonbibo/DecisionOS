import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from to_buyer_format import TaskFolderError, build_manifest, main, write_manifest  # noqa: E402


def _make_task_folder(tmp_path: Path, **task_overrides) -> Path:
    folder = tmp_path / "20260807-143012_fix-navmesh-bug"
    folder.mkdir()

    task = {
        "task_id": "20260807-143012_fix-navmesh-bug",
        "description": "NavMesh eşik takılma sorunu",
        "repo_path": "C:\\Projects\\MyGame",
        "started_at": "2026-08-07T14:30:12+03:00",
        "ended_at": "2026-08-07T15:12:44+03:00",
        "success": "success",
        "success_note": None,
        "recorder_version": "0.1.0",
    }
    task.update(task_overrides)
    (folder / "task.json").write_text(json.dumps(task), encoding="utf-8")

    git_meta = {
        "branch": "feature/navmesh-fix",
        "start_commit": "a1b2c3d",
        "end_commit": "d4e5f6a",
        "start_dirty": True,
        "end_dirty": False,
    }
    (folder / "git_meta.json").write_text(json.dumps(git_meta), encoding="utf-8")

    input_events = [
        {"t": 1.0, "type": "mouse_move", "x": 1, "y": 2},
        {"t": 1.1, "type": "mouse_down", "x": 1, "y": 2, "button": "left"},
        {"t": 1.2, "type": "key_down", "key": "S", "combo": ["Ctrl", "S"]},
    ]
    with (folder / "input_events.jsonl").open("w", encoding="utf-8") as f:
        for e in input_events:
            f.write(json.dumps(e) + "\n")

    unity_events = [
        {"t": 2.0, "type": "play_mode_changed", "state": "EnteredPlayMode"},
        {"t": 2.5, "type": "console_log", "level": "Error", "message": "boom"},
        {"t": 2.6, "type": "console_log", "level": "Error", "message": "boom again"},
        {"t": 2.7, "type": "console_log", "level": "Warning", "message": "careful"},
    ]
    with (folder / "unity_events.jsonl").open("w", encoding="utf-8") as f:
        for e in unity_events:
            f.write(json.dumps(e) + "\n")

    (folder / "screen.mkv").write_bytes(b"fake-video-bytes")

    return folder


def test_build_manifest_happy_path(tmp_path):
    folder = _make_task_folder(tmp_path)

    manifest = build_manifest(folder)

    assert manifest.task_id == "20260807-143012_fix-navmesh-bug"
    assert manifest.success == "success"
    assert manifest.input_event_count == 3
    assert manifest.unity_event_count == 4
    assert manifest.console_log_counts == {"Error": 2, "Warning": 1}
    assert manifest.video_file == "screen.mkv"
    assert manifest.video_sha256 is not None
    assert manifest.git["branch"] == "feature/navmesh-fix"
    # 15:12:44 - 14:30:12 = 42 minutes 32 seconds
    assert manifest.duration_seconds == pytest.approx(42 * 60 + 32)


def test_build_manifest_without_video_hash_is_fast_and_none(tmp_path):
    folder = _make_task_folder(tmp_path)

    manifest = build_manifest(folder, hash_video=False)

    assert manifest.video_file == "screen.mkv"
    assert manifest.video_sha256 is None


def test_build_manifest_missing_optional_files_degrades_gracefully(tmp_path):
    folder = tmp_path / "20260807-000000_minimal"
    folder.mkdir()
    (folder / "task.json").write_text(json.dumps({
        "task_id": "20260807-000000_minimal",
        "description": "no video, no git, no events",
        "started_at": None,
        "ended_at": None,
        "success": "incomplete",
    }), encoding="utf-8")

    manifest = build_manifest(folder)

    assert manifest.video_file is None
    assert manifest.video_sha256 is None
    assert manifest.input_event_count == 0
    assert manifest.unity_event_count == 0
    assert manifest.console_log_counts == {}
    assert manifest.git == {}
    assert manifest.duration_seconds is None


def test_build_manifest_missing_task_json_raises(tmp_path):
    folder = tmp_path / "empty"
    folder.mkdir()

    with pytest.raises(TaskFolderError):
        build_manifest(folder)


def test_write_manifest_writes_json_file(tmp_path):
    folder = _make_task_folder(tmp_path)

    out_path = write_manifest(folder)

    assert out_path == folder / "buyer_manifest.json"
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["task_id"] == "20260807-143012_fix-navmesh-bug"
    assert data["console_log_counts"] == {"Error": 2, "Warning": 1}


def test_write_manifest_custom_out_path(tmp_path):
    folder = _make_task_folder(tmp_path)
    out_path = tmp_path / "somewhere_else.json"

    result = write_manifest(folder, out_path)

    assert result == out_path
    assert out_path.exists()
    assert not (folder / "buyer_manifest.json").exists()


def test_cli_main_success(tmp_path, capsys):
    folder = _make_task_folder(tmp_path)

    exit_code = main([str(folder)])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "yazıldı" in captured.out
    assert (folder / "buyer_manifest.json").exists()


def test_cli_main_missing_task_json_returns_error(tmp_path, capsys):
    folder = tmp_path / "empty"
    folder.mkdir()

    exit_code = main([str(folder)])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "hata" in captured.err
