# Real Repo Smoke Matrix

Maintainer-facing pre-`1.0.0` confidence set. These repos are not vendored into this repository.

## Fixed smoke set

| Stack | Repository | Why |
|------|------------|-----|
| Python | `https://github.com/pallets/click` | Mature Python package with `pyproject.toml`, CLI entrypoints, and tests |
| Node/TypeScript | `https://github.com/sindresorhus/ky` | Small TS-first package with modern package metadata |
| Go | `https://github.com/spf13/cobra` | Widely used Go module with CLI-oriented structure |
| Rust | `https://github.com/serde-rs/json` | Established Rust crate with clear package metadata |

Java and .NET stay on fixture coverage until the `0.9.5` release sprint unless a release blocker appears sooner.

## Command set

For each repo:

```sh
git clone --depth 1 <repo-url> <tmp-dir>
uv run context-crafter-mcp detect <tmp-dir> --json
uv run context-crafter-mcp generate <tmp-dir> --output docs/generated --profile standard --json
uv run context-crafter-mcp validate <tmp-dir>/docs/generated --repo <tmp-dir> --json
```

## Latest run

Run date: `2026-05-29`

| Repository | Detect | Generate | Validate | Files scanned | Warnings | Notes |
|------------|--------|----------|----------|---------------|----------|-------|
| `pallets/click` | pass | pass | pass | 182 | unknown-stack warnings for non-Python stacks | detected `generic, python`; generated to repo-local `docs/generated` |
| `sindresorhus/ky` | pass | pass | pass | 112 | unknown-stack warnings for non-Node stacks | detected `generic, node`; generated to repo-local `docs/generated` |
| `spf13/cobra` | pass | pass | pass | 95 | unknown-stack warnings for non-Go stacks | detected `generic, go`; generated to repo-local `docs/generated` |
| `serde-rs/json` | pass | pass | pass | 159 | unknown-stack warnings for non-Rust stacks | detected `generic, rust`; generated to repo-local `docs/generated` |

These warnings came from `detect_project` reporting unsupported/non-matching stacks as `unknown`; they were not generation or validation failures.

## Acceptance

- No command crashes.
- Output files are generated and validate cleanly or with documented non-blocking warnings.
- Any warning that undermines core trust becomes a release blocker or a documented limitation.
