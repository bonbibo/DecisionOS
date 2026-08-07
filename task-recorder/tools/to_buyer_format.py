#!/usr/bin/env python3
"""Convert a Task Recorder task folder into a single buyer_manifest.json summary.

Usage:
    python to_buyer_format.py <task_folder> [--out PATH]

Reads task.json / git_meta.json / input_events.jsonl / unity_events.jsonl / screen.* from
the task folder (see ../docs/FORMAT.md) and writes a summary manifest. Never modifies or
deletes the raw event files — the manifest is purely additive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

REQUIRED_FILES = ("task.json",)
VIDEO_STEM = "screen"


class TaskFolderError(ValueError):
    """Raised when a task folder is missing files a manifest cannot be built without."""


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def _count_console_levels(unity_events_path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not unity_events_path.exists():
        return counts
    with unity_events_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "console_log":
                level = event.get("level", "Unknown")
                counts[level] = counts.get(level, 0) + 1
    return counts


def _find_video_file(task_folder: Path) -> Path | None:
    for candidate in sorted(task_folder.glob(f"{VIDEO_STEM}.*")):
        if candidate.is_file():
            return candidate
    return None


def _sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _duration_seconds(started_at: str | None, ended_at: str | None) -> float | None:
    if not started_at or not ended_at:
        return None
    try:
        start = datetime.fromisoformat(started_at)
        end = datetime.fromisoformat(ended_at)
    except ValueError:
        return None
    return max(0.0, (end - start).total_seconds())


@dataclass
class BuyerManifest:
    task_id: str
    description: str
    success: str
    started_at: str | None
    ended_at: str | None
    duration_seconds: float | None
    video_file: str | None
    video_sha256: str | None
    input_event_count: int
    unity_event_count: int
    console_log_counts: dict[str, int]
    git: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "success": self.success,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_seconds": self.duration_seconds,
            "video_file": self.video_file,
            "video_sha256": self.video_sha256,
            "input_event_count": self.input_event_count,
            "unity_event_count": self.unity_event_count,
            "console_log_counts": self.console_log_counts,
            "git": self.git,
        }


def build_manifest(task_folder: Path, *, hash_video: bool = True) -> BuyerManifest:
    """Pure function: reads a task folder, returns the manifest. No I/O side effects
    beyond reading input files (and hashing the video, unless disabled for speed/tests)."""
    task_folder = Path(task_folder)

    task_json_path = task_folder / "task.json"
    for name in REQUIRED_FILES:
        if not (task_folder / name).exists():
            raise TaskFolderError(f"görev klasöründe {name} yok: {task_folder}")

    task_meta = json.loads(task_json_path.read_text(encoding="utf-8"))

    git_meta_path = task_folder / "git_meta.json"
    git_meta = json.loads(git_meta_path.read_text(encoding="utf-8")) if git_meta_path.exists() else {}

    video_path = _find_video_file(task_folder)
    video_sha256 = _sha256(video_path) if (video_path and hash_video) else None

    return BuyerManifest(
        task_id=task_meta.get("task_id", task_folder.name),
        description=task_meta.get("description", ""),
        success=task_meta.get("success", "incomplete"),
        started_at=task_meta.get("started_at"),
        ended_at=task_meta.get("ended_at"),
        duration_seconds=_duration_seconds(task_meta.get("started_at"), task_meta.get("ended_at")),
        video_file=video_path.name if video_path else None,
        video_sha256=video_sha256,
        input_event_count=_count_lines(task_folder / "input_events.jsonl"),
        unity_event_count=_count_lines(task_folder / "unity_events.jsonl"),
        console_log_counts=_count_console_levels(task_folder / "unity_events.jsonl"),
        git=git_meta,
    )


def write_manifest(task_folder: Path, out_path: Path | None = None, *, hash_video: bool = True) -> Path:
    manifest = build_manifest(task_folder, hash_video=hash_video)
    out_path = out_path or (Path(task_folder) / "buyer_manifest.json")
    out_path.write_text(json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_folder", type=Path, help="Görev klasörü (task.json içeren)")
    parser.add_argument("--out", type=Path, default=None, help="Çıktı yolu (varsayılan: <task_folder>/buyer_manifest.json)")
    parser.add_argument("--no-hash-video", action="store_true", help="Video checksum hesaplama (büyük dosyalarda hızlandırır)")
    args = parser.parse_args(argv)

    try:
        out_path = write_manifest(args.task_folder, args.out, hash_video=not args.no_hash_video)
    except TaskFolderError as exc:
        print(f"hata: {exc}", file=sys.stderr)
        return 1

    print(f"yazıldı: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
