# Real Repo Smoke Matrix

Maintainer-facing hardening confidence set for the current `0.9.0` line on `main`. These repos are not vendored into this repository.

## Fixed smoke set

| Stack | Repository | Why |
|------|------------|-----|
| Python | `https://github.com/pallets/click` | Mature Python package with `pyproject.toml`, CLI entrypoints, and tests |
| Node/TypeScript | `https://github.com/sindresorhus/ky` | Small TS-first package with modern package metadata |
| Go | `https://github.com/spf13/cobra` | Widely used Go module with CLI-oriented structure |
| Rust | `https://github.com/serde-rs/json` | Established Rust crate with clear package metadata |

Java and .NET stay on fixture coverage until their results meet the same trust bar or a blocker forces earlier work.

## Automation

Run the full matrix automatically:

```sh
uv run python scripts/smoke_repos.py
```

Run it from the repository root. Invoking the script from other working directories can change the relative output path and is not the maintainer-supported release-check path.

Options:
- `--output <path>` — write JSON summary to a file (default: `docs/generated/smoke-results.json`)
- `--keep-temps` — preserve cloned repositories in temp for debugging

The script:
1. Clones each repo with `--depth 1` into a temp directory
2. Runs `detect`, `generate`, and `validate` for each
3. Writes a deterministic JSON summary to stdout and the output file
4. Cleans up temp directories unless `--keep-temps` is passed

If network is unavailable, the script prints a clear message and exits non-zero with a `network_unavailable` note.

## Manual command set (fallback)

For each repo:

```sh
git clone --depth 1 <repo-url> <tmp-dir>
uv run context-crafter-mcp detect <tmp-dir> --json
uv run context-crafter-mcp generate <tmp-dir> --output docs/generated --profile standard --json
uv run context-crafter-mcp validate <tmp-dir>/docs/generated --repo <tmp-dir> --json
```

## Latest run

Run date: `2026-06-25` for the `0.9.0` release-candidate line.

| Repository | Detect | Generate | Validate | Files scanned | Warnings | Notes |
|------------|--------|----------|----------|---------------|----------|-------|
| `pallets/click` | pass | pass | pass | 133 | 5 unknown-stack warnings for non-Python stacks | detected `generic, python`; counts vary by scanner config and repo state |
| `sindresorhus/ky` | pass | pass | pass | 60 | 5 unknown-stack warnings for non-Node stacks | detected `generic, node`; counts vary by scanner config and repo state |
| `spf13/cobra` | pass | pass | pass | 59 | 5 unknown-stack warnings for non-Go stacks | detected `generic, go`; counts vary by scanner config and repo state |
| `serde-rs/json` | pass | pass | pass | 88 | 5 unknown-stack warnings for non-Rust stacks | detected `generic, rust`; counts vary by scanner config and repo state |

These warnings came from `detect_project` reporting unsupported/non-matching stacks as `unknown`; they were not generation or validation failures.

## Acceptance

- No command crashes.
- Output files are generated and validate cleanly or with documented non-blocking warnings.
- Any warning that undermines core trust becomes a blocker for the next tagged release or a documented limitation.
