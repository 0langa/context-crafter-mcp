"""Helpers for running analyzers against a shared RepoSnapshot."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from context_crafter_mcp.models import AnalysisResult, ScanConfig
from context_crafter_mcp.scanner import RepoSnapshot, Scanner, ScannerOptions, SnapshotFile


def build_analysis_snapshot(root: Path, config: ScanConfig, *, extra_depth: int = 4) -> RepoSnapshot:
    """Build one shared snapshot deep enough for all shipped analyzers."""
    max_depth = min(config.max_depth + extra_depth, 20)
    max_files = max(config.max_files_per_dir * 20, 5_000)
    return Scanner().scan(
        root,
        ScannerOptions(
            max_depth=max_depth,
            max_files=max_files,
            max_file_bytes=config.max_file_bytes,
            max_files_per_dir=config.max_files_per_dir,
        ),
    )


def get_analysis_snapshot(root: Path, analysis: AnalysisResult | None, config: ScanConfig) -> RepoSnapshot:
    """Reuse an attached snapshot when possible; otherwise build and attach one."""
    snapshot = analysis.snapshot if analysis is not None else None
    if isinstance(snapshot, RepoSnapshot) and snapshot.root.resolve() == root.resolve():
        return snapshot
    snapshot = build_analysis_snapshot(root, config)
    if analysis is not None:
        analysis.snapshot = snapshot
    return snapshot


def iter_snapshot_files(snapshot: RepoSnapshot) -> Iterator[tuple[SnapshotFile, Path]]:
    """Yield snapshot files paired with absolute on-disk paths."""
    for sf in snapshot.files:
        yield sf, snapshot.root / sf.rel_path
