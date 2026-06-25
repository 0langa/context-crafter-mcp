# Context Crafter MCP Testing Status

> This is a repo-side **stable-facts summary** of the external battle-testing platform.
>
> The old external D-drive platform no longer exists on the current development machine.
> Do not treat any previous D-drive path as live evidence.

## Platform Overview

The historical external `context-crafter-tests` platform was a deterministic, regenerable,
adversarial battle-hardening environment for `context-crafter-mcp`.

- **Current availability**: unavailable; the old external drive path has been retired
- **Historical scenarios materialized**: 17
- **Historical total files**: ~4,499
- **Historical total lines**: ~196,129
- **Historical scale focus**: L3 and L4 scenarios were expanded for large-repo pressure

## Current Local Testing Source

Until a replacement platform exists, use:

- local repo tests under `tests/`
- release and smoke commands in `docs/PRE_1_0_GATE.md`
- real-repo smoke automation in `scripts/smoke_repos.py`
- stable product state in `docs/project_state.md`

## Known Stable Product Failure Patterns

- **Generic fallback honesty**: historical external results showed `L1-GENERIC-001` failing when the product incorrectly claimed specific stacks (`python`, `node`) in an intentionally generic scenario. This should be re-verified locally or on any rebuilt platform before release.
- **Bounded-scan disclosure**: the historical platform evaluated scan-bound honesty using a three-tier materiality rule:
  - hard blocker for `budget_exhausted` without disclosure
  - major blocker for material non-budget bounds without disclosure
  - minor finding for benign skips without disclosure

## Retired Platform Tooling

The retired platform tool supported the following commands. They are not currently runnable unless
the platform is rebuilt:

- `validate-contract` — validate platform contracts and indexes
- `materialize` — build scenario repos from manifests
- `reset` — reset generated scenarios or outputs
- `run-suite` — run one or more suites
- `run-scenario` — run one or more scenarios directly
- `status` — show latest curated status file path
- `verify-session-completion` — machine-checkable session closure verifier (supports profiles: `hardening-followup`, `targeted-regression`, `suite-review`, `release-gate`, `platform-contract-change`)
  - `--report` is required (no auto-discovery fallback)
  - `--run-id` is required for profiles needing official runs
  - does not silently reuse `runtime-state.json` last_run_id
  - enforces report-to-run binding
  - runs live `validate-contract` check for `platform-contract-change`

## Repo-side Testing Anchors

Tracked repo-side testing docs live under:

- `docs/testing/README.md`
- `docs/testing/TEST_ENVIRONMENT_HANDOFF.md`
- `docs/testing/TESTING_STATUS.md`

## What This File Does NOT Contain

- Specific run IDs, timestamps, or pass/fail counts from individual runs.
- Claims about "latest" status that can drift within minutes.

For current release readiness, rerun the local gate instead of relying on historical external output.
