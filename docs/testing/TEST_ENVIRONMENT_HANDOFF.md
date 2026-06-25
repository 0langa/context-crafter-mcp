# Test Environment Handoff

This is the tracked repo-side handoff for rebuilding or replacing the external
`context-crafter-tests` planning and reporting flow.

## Current status

The old D-drive external testing platform no longer exists on the current development machine.
Do not assume any previous external path is available.

The historical phase-1 spec pack was intended to include:

- directory contract
- manifest schema
- expectation schema
- scoring and blocker schema
- run-ledger schema
- scenario ID and seed rules

## Intended replacement

If rebuilt, the external test platform should be a deterministic, resettable, anti-cheat
battle-hardening environment for `context-crafter-mcp`.

It is intended to exceed normal real-world ugliness rather than mirror only clean or medium-complexity repositories.

Its long-term purpose is to verify:

- large-repo operational reliability
- truthfulness under bounded scans
- stack-specific and mixed-stack credibility
- CLI / MCP / validation / artifact behavior
- repeatable, traceable regression and release-gate evidence

## Rules for future agents

1. Do not rely on the old D-drive paths; they are retired.
2. Do not claim external battle-test results unless the platform has been rebuilt and run.
3. If a new external platform is created, document its root path, contracts, and operator workflow here.
4. Mirror only curated summaries back into this repo. Raw run data should stay out of product docs.
5. If external testing contracts change, update this handoff note and `docs/project_state.md` in the same change set.

## Important: gitignored paths are not durable truth

`docs/internal/` is listed in `.gitignore`. Do not rely on files under that path as authoritative repo-side anchors. Any durable repo-side summary must live in a tracked path such as `docs/testing/TESTING_STATUS.md` or `docs/testing/TEST_ENVIRONMENT_HANDOFF.md`.

## Expected future repo-side files

This repo may later gain:

- `docs/testing/TESTING_STATUS.md` (stable facts only, no volatile "latest run" claims)
- durable incident reviews derived from brutal test runs

Volatile run data, latest-gate summaries, and run history should be documented only after a new
platform exists again.
