# Testing Docs

This subdirectory contains the tracked repo-side anchors for testing strategy and historical external
`context-crafter-tests` work.

The old external D-drive platform no longer exists on the current development machine. Treat any
previous D-drive references as retired historical context, not as live instructions.

## Files

- `TEST_ENVIRONMENT_HANDOFF.md`
  - structural repo-side handoff for rebuilding a battle-testing environment later
  - explains what should live in this repo vs in any future external platform

- `TESTING_STATUS.md`
  - stable-facts summary only
  - must not contain volatile latest-run claims
  - records that the old external platform is unavailable in the current setup

## Current source of truth

For the current setup, use this repository's tracked tests, docs, and command output. Any future
external test platform should be documented here only after it exists again and has a stable path.

## Rule

Do not place volatile test-run summaries at `docs/` root.
Public product-facing docs should stay at `docs/` root; testing-platform anchors and mirrors live here.
