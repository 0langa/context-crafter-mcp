"""Benchmark scanner with a synthetic fixture.

Outputs JSON with timing and stats to stdout.
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

from context_crafter_mcp.scanner import Scanner, ScannerOptions


def create_synthetic_fixture(
    root: Path,
    files: int = 500,
    depth: int = 4,
    doc_ratio: float = 0.1,
    binary_ratio: float = 0.02,
) -> None:
    """Create a synthetic repository with many files, docs, and binaries."""
    doc_files = int(files * doc_ratio)
    binary_files = int(files * binary_ratio)
    code_files = files - doc_files - binary_files

    def _write_file(idx: int, file_type: str) -> None:
        d = root
        for _ in range(min(depth - 1, idx % depth)):
            d = d / f"subdir_{d.name}_{idx % 10}"
        d.mkdir(parents=True, exist_ok=True)
        if file_type == "code":
            (d / f"file_{idx}.py").write_text(
                f"# file {idx}\ndef func_{idx}():\n    return {idx}\n",
                encoding="utf-8",
            )
        elif file_type == "doc":
            (d / f"doc_{idx}.md").write_text(
                f"# Document {idx}\n\nSome content here.\n",
                encoding="utf-8",
            )
        elif file_type == "binary":
            (d / f"bin_{idx}.dat").write_bytes(b"\x00" * 1024)

    for i in range(code_files):
        _write_file(i, "code")
    for i in range(doc_files):
        _write_file(code_files + i, "doc")
    for i in range(binary_files):
        _write_file(code_files + doc_files + i, "binary")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark scanner.")
    parser.add_argument("--files", type=int, default=500, help="Number of files to create.")
    parser.add_argument("--depth", type=int, default=4, help="Max directory depth.")
    parser.add_argument("--max-files", type=int, default=1_000, help="Scanner max_files limit.")
    parser.add_argument("--docs", type=int, default=0, help="Number of doc files (overrides doc_ratio).")
    parser.add_argument("--run-pipeline", action="store_true", help="Also run full generation pipeline.")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        doc_ratio = args.docs / args.files if args.docs else 0.1
        create_synthetic_fixture(root, files=args.files, depth=args.depth, doc_ratio=doc_ratio)

        scanner = Scanner()
        options = ScannerOptions(max_depth=args.depth + 2, max_files=args.max_files)

        t0 = time.perf_counter()
        snapshot = scanner.scan(root, options)
        t1 = time.perf_counter()
        scan_time = t1 - t0

        pipeline_time = 0.0
        pipeline_ok = False
        if args.run_pipeline:
            from context_crafter_mcp.graph import run_generate_all

            t2 = time.perf_counter()
            state = run_generate_all(str(root), output_dir="docs/generated")
            t3 = time.perf_counter()
            pipeline_time = t3 - t2
            pipeline_ok = state.ok

        result = {
            "fixture": {
                "files_created": args.files,
                "depth": args.depth,
                "root": str(root),
            },
            "scanner_options": {
                "max_depth": options.max_depth,
                "max_files": options.max_files,
                "max_file_bytes": options.max_file_bytes,
                "follow_symlinks": options.follow_symlinks,
                "include_hidden": options.include_hidden,
                "respect_gitignore": options.respect_gitignore,
            },
            "timing": {
                "scan_seconds": round(scan_time, 4),
                "pipeline_seconds": round(pipeline_time, 4) if args.run_pipeline else None,
            },
            "stats": {
                "files_scanned": len(snapshot.files),
                "directories_scanned": len(snapshot.directories),
                "skipped": len(snapshot.skipped),
                "budget_exhausted": snapshot.stats.budget_exhausted,
            },
            "pipeline": {
                "ran": args.run_pipeline,
                "ok": pipeline_ok,
            }
            if args.run_pipeline
            else None,
        }
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
