# Testing Docs

This subdirectory contains the tracked repo-side anchors for the external `context-crafter-tests` platform.

These files are not the canonical live source of truth for test execution.
They exist so the main repo keeps a durable, versioned pointer to the external D-drive platform and its stable mirrored summaries.

## Files

- `TEST_ENVIRONMENT_HANDOFF.md`
  - structural repo-side handoff
  - points agents to the external D-drive platform
  - explains what belongs in repo docs vs what stays on D-drive

- `TESTING_STATUS.md`
  - stable-facts summary only
  - must not contain volatile latest-run claims
  - points readers to the D-drive platform for live run state

## Canonical live source of truth

For current execution state, run ledgers, and latest run status, use:

- `D:\DEVTESTING\context-crafter-mcp\DOCUMENTS\test-results\current-status\latest.md`
- `D:\DEVTESTING\context-crafter-mcp\DOCUMENTS\test-results\run-ledger\`
- `D:\DEVTESTING\context-crafter-mcp\DANGER-ZONE\TESTSPACE\context-crafter-tests\runtime\runtime-state.json`

## Rule

Do not place volatile test-run summaries at `docs/` root.
Public product-facing docs should stay at `docs/` root; testing-platform anchors and mirrors live here.
