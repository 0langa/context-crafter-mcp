# AGENTS.md

## Agent communication

- All responses use **caveman ultra** mode.
- Drop articles, filler, hedging. Fragments OK. Abbreviate (DB/auth/config/req/res/fn/impl). Arrows for causality (X → Y). One word when enough.
- Auto-clarity exception: security warnings, irreversible actions, multi-step sequences where fragment order risks misread, or when user asks to clarify. Resume caveman after clear part done.
- "stop caveman" / "normal mode" to revert.

## Kimi Code / Ralph mode

- When using Kimi Code to work on this repo, **always consider enabling Ralph mode** (internal reasoning sub-iterations).
- Ensure `loop_control.max_ralph_iterations` in `~/.kimi-code/config.toml` is set to a non-zero value (e.g., `100`) before deep tasks.
- Ralph mode allows the engine to iterate on complex analysis, refactoring, or generation tasks internally. Do not disable it for this repo unless explicitly requested.

## Skills

- Skills directory: `C:\Users\juliu\.agents\skills`
- When working on this repo, **always consider using relevant skills** from that directory.
- Check available skills before starting tasks; load and apply any that match the current work (debugging, testing, security, docs, CI, etc.).
- Do not skip skill usage unless explicitly told to ignore them.

## Project identity

`context-crafter-mcp` is a local-first Python package with two public surfaces:

- CLI: `context-crafter-mcp`
- stdio MCP server: `context-crafter-mcp serve`

The project statically analyzes source repositories and generates compact, source-grounded context for AI coding agents.

Core mode must remain deterministic, local-first, and static-only.

## Non-negotiable rules

- Do not add LLM/API/cloud generation features.
- Do not execute target repository code during analysis.
- Do not rewrite the project in Rust, Go, TypeScript, or another language.
- Keep Python as the MCP/CLI/product layer.
- Do not make Docker or HTTP service mode the default path.
- Do not create duplicate package trees.
- Do not leave placeholder TODO implementations.
- Do not weaken safety checks to make tests pass.
- Do not print logs, warnings, or human text to stdout in MCP stdio mode.
- Do not claim a command, feature, MCP tool, or safety property works unless verified.

## Architecture boundaries

Use these boundaries:

- CLI and MCP tools call shared core services.
- The scanner returns a deterministic `RepoSnapshot`.
- Analyzers consume `RepoSnapshot`; avoid ad-hoc filesystem traversal.
- `filesystem.safe_scan()` may exist only as a compatibility wrapper around `Scanner`.
- Generated docs must avoid overclaiming. Use observed, inferred, unknown, unsupported, and error states where feasible.
- MCP resources must only expose generated files registered by the current server session.
- Never allow `read_resource()` to read arbitrary local paths.
- Prefer `context-crafter://latest/<filename>` resource URIs.

## Generated output contract

A full generation must produce these Markdown files:

- `AI_CONTEXT_INDEX.md`
- `PROJECT_OVERVIEW.md`
- `REPO_MAP.md`
- `DEPENDENCY_GRAPH.md`
- `ARCHITECTURE_SUMMARY.md`
- `AGENT_BRIEF.md`
- `SCAN_REPORT.md`
- `VALIDATION_REPORT.md`

`DEPENDENCY_GRAPH.mmd` may also be generated as the raw Mermaid graph.

Generated content must be source-grounded, deterministic, concise, and honest about unknowns.

## CLI contract

Maintain these commands:

- `context-crafter-mcp --help`
- `context-crafter-mcp version`
- `context-crafter-mcp doctor`
- `context-crafter-mcp detect <repo_path> [--json]`
- `context-crafter-mcp generate <repo_path> --output <output_dir> [--profile compact|standard|deep] [--json]`
- `context-crafter-mcp validate <output_dir> [--json]`
- `context-crafter-mcp self-test [repo_path]`
- `context-crafter-mcp mcp-config --client <client> [--repo <path>]`
- `context-crafter-mcp serve`

`self-test` must not dirty the repository by default.

`--json` output must be valid JSON only.

## MCP contract

Keep the public MCP tool surface small and predictable:

- `detect_project`
- `generate_context`
- `generate_project_overview`
- `generate_repo_map`
- `generate_dependency_graph`
- `generate_architecture_summary`
- `validate_generated_context`
- `explain_capabilities`

Tool results should be structured and include `ok`, `summary`, `warnings`, `errors`, and relevant stats or generated file paths.

Do not expose internal helper functions as MCP tools.

## Scanner and validation expectations

Scanner behavior must remain bounded and safe:

- no symlink following by default
- bounded file count, depth, and file size
- skip binary and oversized files
- respect ignore rules as documented
- report skipped files and errors instead of crashing
- keep output deterministic

Validation should check more than file existence where feasible:

- required output files
- Markdown relative links
- non-empty Mermaid graph block
- referenced source paths where conservative
- fixture/demo pollution in primary project claims
- machine-readable warning/error codes

## Development commands

Use `uv` for all project commands.

    uv sync --extra dev
    uv run python -m compileall src tests
    uv run ruff check .
    uv run ruff format --check .
    uv run mypy src
    uv run pytest -q
    uv build
    uv run context-crafter-mcp --help
    uv run context-crafter-mcp doctor
    uv run context-crafter-mcp detect . --json
    uv run context-crafter-mcp generate . --output .tmp/generated --profile standard --json
    uv run context-crafter-mcp validate .tmp/generated --json
    uv run context-crafter-mcp self-test .
    uv run python scripts/bench_scan.py --files 1000 --depth 5 --max-files 2000

For MCP stdio smoke testing, use an OS-appropriate timeout command around:

    uv run context-crafter-mcp serve

## Documentation update rules

When behavior changes, update the relevant docs:

- `README.md`
- `CHANGELOG.md`
- `IMPLEMENTATION_REPORT.md`
- `MANUAL_STEPS.md`
- `docs/ARCHITECTURE.md`
- `docs/SCANNER.md`
- `docs/MCP_CLIENTS.md`
- `docs/OUTPUT_CONTRACT.md`
- `docs/LIMITATIONS.md`
- `SECURITY.md`

Do not overstate support. If behavior is partial, document the limitation.

## Repo hygiene

Do not commit accidental local artifacts:

- `.tmp/`
- `.pytest_cache/`
- `.ruff_cache/`
- `.mypy_cache/`
- `__pycache__/`
- `*.pyc`
- stale `dist/`
- local build outputs

Keep `examples/outputs/` only when intentionally regenerated from `examples/demo-repo/`.

Before finishing work, run the strongest feasible verification set and summarize exact results. If a command fails, fix it or document the precise blocker.