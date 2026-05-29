"""Benchmark scanner with a synthetic fixture.

Outputs JSON with timing and stats to stdout.
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

from context_crafter_mcp.scanner import Scanner, ScannerOptions


def create_synthetic_fixture(root: Path, files: int = 500, depth: int = 4) -> None:
    """Create a synthetic repository with many files."""
    for i in range(files):
        d = root
        for _ in range(min(depth - 1, i % depth)):
            d = d / f"subdir_{d.name}_{i % 10}"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"file_{i}.py").write_text(
            f"# file {i}\ndef func_{i}():\n    return {i}\n",
            encoding="utf-8",
        )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark scanner.")
    parser.add_argument("--files", type=int, default=500, help="Number of files to create.")
    parser.add_argument("--depth", type=int, default=4, help="Max directory depth.")
    parser.add_argument("--max-files", type=int, default=1_000, help="Scanner max_files limit.")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        create_synthetic_fixture(root, files=args.files, depth=args.depth)

        scanner = Scanner()
        options = ScannerOptions(max_depth=args.depth + 2, max_files=args.max_files)

        t0 = time.perf_counter()
        snapshot = scanner.scan(root, options)
        t1 = time.perf_counter()

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
                "elapsed_seconds": round(t1 - t0, 4),
            },
            "stats": {
                "files_scanned": len(snapshot.files),
                "directories_scanned": len(snapshot.directories),
                "skipped": len(snapshot.skipped),
            },
        }
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
