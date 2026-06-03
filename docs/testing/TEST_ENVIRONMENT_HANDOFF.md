# Test Environment Handoff

This is the tracked repo-side handoff for the external `context-crafter-tests` planning and future reporting flow.

## Canonical planning location

The canonical planning and phase-1 specification files currently live on the external test drive at:

- `D:\DEVTESTING\context-crafter-mcp\DOCUMENTS\planning-and-setup\context-crafter-tests-master-plan.md`
- `D:\DEVTESTING\context-crafter-mcp\DOCUMENTS\planning-and-setup\phase-1-spec-pack.md`

The phase-1 spec pack currently includes:

- directory contract
- manifest schema
- expectation schema
- scoring and blocker schema
- run-ledger schema
- scenario ID and seed rules

## Current intent

The external test platform is being designed as a deterministic, resettable, anti-cheat battle-hardening environment for `context-crafter-mcp`.

It is intended to exceed normal real-world ugliness rather than mirror only clean or medium-complexity repositories.

Its long-term purpose is to verify:

- large-repo operational reliability
- truthfulness under bounded scans
- stack-specific and mixed-stack credibility
- CLI / MCP / validation / artifact behavior
- repeatable, traceable regression and release-gate evidence

## Rules for future agents

1. Do not invent a different directory model for the D-drive platform.
2. Do not start scaffolding the environment from memory if the D-drive docs exist.
3. Treat the D-drive planning docs as canonical until they are intentionally revised.
4. Mirror only curated summaries back into this repo. Raw run data stays on the D drive.
5. If the D-drive contracts change, update this handoff note and `docs/project_state.md` in the same change set.

## Important: gitignored paths are not durable truth

`docs/internal/` is listed in `.gitignore`. Do not rely on files under that path as authoritative repo-side anchors. Any durable repo-side summary must live in a tracked path such as `docs/testing/TESTING_STATUS.md` or `docs/testing/TEST_ENVIRONMENT_HANDOFF.md`.

## Expected future repo-side files

This repo is expected to later gain:

- `docs/testing/TESTING_STATUS.md` (stable facts only, no volatile "latest run" claims)
- durable incident reviews derived from brutal test runs

Volatile run data, latest-gate summaries, and run history remain on the D-drive platform.
