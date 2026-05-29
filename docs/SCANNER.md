# Scanner

## Interface

```python
from context_crafter_mcp.scanner import Scanner, ScannerOptions

scanner = Scanner()
snapshot = scanner.scan("/path/to/repo", ScannerOptions(max_depth=6, max_files=5000))
```

## Models

- `ScannerOptions`: `follow_symlinks`, `respect_gitignore`, `include_hidden`, `include_tests`, `max_files`, `max_depth`, `max_file_bytes`
- `RepoSnapshot`: `root`, `files`, `directories`, `skipped`, `stats`, `git`
- `SnapshotFile`: `rel_path`, `size`
- `SnapshotDirectory`: `rel_path`
- `SkippedEntry`: `rel_path`, `reason`
- `ScanError`: `rel_path`, `message`
- `ScanStats`: `files_scanned`, `dirs_scanned`, `files_skipped`, `dirs_skipped`, `errors`
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

## Skipped directories

.git, .hg, .svn, .venv, venv, env, __pycache__, .pytest_cache, .mypy_cache, .ruff_cache, node_modules, dist, build, out, target, bin, obj, .next, .turbo, .cache
