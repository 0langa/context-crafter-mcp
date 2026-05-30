# Scanner

## Interface

```python
from context_crafter_mcp.scanner import Scanner, ScannerOptions

scanner = Scanner()
snapshot = scanner.scan("/path/to/repo", ScannerOptions(max_depth=6, max_files=5000))
```

## Models

- `ScannerOptions`: `follow_symlinks`, `respect_gitignore`, `include_hidden`, `include_tests`, `max_files`, `max_depth`, `max_file_bytes`, `max_files_per_dir`
- `RepoSnapshot`: `root`, `files`, `directories`, `skipped`, `stats`, `git`
- `SnapshotFile`: `rel_path`, `size`, `extension`, `language_hint`, `is_text`
- `SnapshotDirectory`: `rel_path`
- `SkippedEntry`: `rel_path`, `reason`
- `ScanError`: `rel_path`, `message`
- `ScanStats`: `files_scanned`, `dirs_scanned`, `files_skipped`, `dirs_skipped`, `budget_exhausted`, `skipped_reasons`, `category_counts`, `errors`
- `GitMetadata`: `commit`, `branch`, `dirty`

## Defaults

| Option | Default |
|--------|---------|
| follow_symlinks | false |
| respect_gitignore | true |
| include_hidden | false |
| include_tests | true |
| max_files | 5000 |
| max_depth | 6 |
| max_file_bytes | 5_000_000 |
| max_files_per_dir | 0 (unlimited) |

## Skipped directories

.git, .hg, .svn, .venv, venv, env, __pycache__, .pytest_cache, .mypy_cache, .ruff_cache, node_modules, dist, build, out, target, bin, obj, .next, .turbo, .cache, vendor, vendors, third_party, thirdparty, 3rdparty, aa_vendor_mirror, vendor_mirror, mirrors, mirror, generated, gen, autogen

## .gitignore support

Root `.gitignore` is parsed using `pathspec` with Git-style wildmatch:

- `*.log` ignores all `.log` files.
- `build/` ignores directories named `build`.
- `foo/**` ignores everything under `foo/`.
- `!keep.log` negates a previous ignore pattern.

Nested `.gitignore` files inside subdirectories are supported via `active_gitignores` stack with deepest-matching-wins semantics.

## Determinism

Output order is fully deterministic:

- Directory traversal order: product directories (`src`, `app`, `services`, ...) walked before generic directories, which are walked before vendor/build/cache directories (`vendor`, `dist`, `node_modules`, ...).
- File order within each directory: manifest files (`pyproject.toml`, `package.json`, `go.mod`, ...) first, then tier-1 entrypoints (`main.py`, `__init__.py`, `index.js`, ...), then tier-2 entrypoints (`worker.py`, `gateway.ts`, ...), then config files, then other text files, then binaries last.
- This ordering ensures that when `max_files` or `max_files_per_dir` caps are hit, the highest-signal files are retained and results are reproducible across runs and filesystems.

## Priority reserve

When `max_files` is hit, a reserve budget (`min(1000, max_files // 5)`) is preserved exclusively for product directories. Files in vendor/build/cache directories cannot consume this reserve. If the reserve is triggered, skipped entries carry reason `"priority_reserve"`. `ScanStats.budget_exhausted` is set when the global cap is hit.
