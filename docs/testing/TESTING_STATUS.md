# Context Crafter MCP Testing Status

> This is a repo-side **stable-facts summary** of the external battle-testing platform.
>
> **Do not treat this file as the live latest-run source of truth.**
> Volatile "latest run" status lives on the D-drive platform and changes after every test run.
> For the current latest run, see:
> `D:\DEVTESTING\context-crafter-mcp\DOCUMENTS\test-results\current-status\latest.md`

## Platform Overview

The external `context-crafter-tests` platform is a deterministic, regenerable, adversarial battle-hardening environment for `context-crafter-mcp`.

- **Platform root**: `D:\DEVTESTING\context-crafter-mcp`
- **Scenarios materialized**: 17
- **Total files**: ~4,499
- **Total lines**: ~196,129
- **Scale focus**: L3 and L4 scenarios are expanded for large-repo pressure

## Canonical D-Drive Locations

| Purpose | Path |
|---------|------|
| Current latest run status | `D:\DEVTESTING\context-crafter-mcp\DOCUMENTS\test-results\current-status\latest.md` |
| Run ledger (all runs) | `D:\DEVTESTING\context-crafter-mcp\DOCUMENTS\test-results\run-ledger\` |
| Incident reviews | `D:\DEVTESTING\context-crafter-mcp\DOCUMENTS\test-results\incident-reviews\` |
| Stack reports | `D:\DEVTESTING\context-crafter-mcp\DOCUMENTS\test-results\stack-reports\` |
| Operator guide | `D:\DEVTESTING\context-crafter-mcp\DOCUMENTS\how-to-use\context-crafter-tests-operator-guide.md` |
| Phase-1 spec pack | `D:\DEVTESTING\context-crafter-mcp\DOCUMENTS\planning-and-setup\phase-1-spec-pack.md` |
| Platform-local testing instructions | `D:\DEVTESTING\context-crafter-mcp\AGENTS.md` |

## Known Stable Product Failure Patterns

- **Generic fallback honesty**: `L1-GENERIC-001` fails when the product incorrectly claims specific stacks (`python`, `node`) in an intentionally generic scenario.
- **Bounded-scan disclosure**: The platform evaluates scan-bound honesty using a three-tier materiality rule:
  - hard blocker for `budget_exhausted` without disclosure
  - major blocker for material non-budget bounds without disclosure
  - minor finding for benign skips without disclosure

## Repo-side Testing Anchors

Tracked repo-side testing docs live under:

- `docs/testing/README.md`
- `docs/testing/TEST_ENVIRONMENT_HANDOFF.md`
- `docs/testing/TESTING_STATUS.md`

## What This File Does NOT Contain

- Specific run IDs, timestamps, or pass/fail counts from individual runs.
- Claims about "latest" status that can drift within minutes.

For all volatile run state, use the D-drive canonical paths above.
