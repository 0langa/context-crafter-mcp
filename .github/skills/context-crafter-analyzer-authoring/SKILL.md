---
name: context-crafter-analyzer-authoring
description: "Author or extend language analyzers for context-crafter-mcp with source-grounded evidence, safe fallback behavior, fixture/vendor awareness, and regression coverage. Use when: add analyzer, extend analyzer, improve Python/Node/.NET/Rust/Go/Java analysis, add AST parsing, improve entrypoint detection, improve symbol extraction, or add new language support."
---

# Context Crafter Analyzer Authoring

Use this skill when changing files under `src/context_crafter_mcp/analyzers/` or analyzer wiring.

## Goal

Improve analysis quality without breaking:

- deterministic output
- source grounding
- scanner/analyzer boundary
- mixed-monorepo honesty
- fallback behavior for unknown constructs

## Rules

- analyzers consume snapshot/evidence inputs, not ad-hoc recursive filesystem walks
- prefer observed evidence over inferred claims
- preserve `UNKNOWN` / `UNSUPPORTED` states when certainty missing
- avoid language-specific hacks tied to one repo layout

## Workflow

1. inspect current analyzer spec and registry
2. inspect fixture for target language under `tests/fixtures/`
3. define missing evidence or wrong claim
4. patch analyzer with smallest general rule
5. add or update focused analyzer tests
6. run focused tests, then broader validation if registry/output changed

## Evidence rules

- tag direct parse findings as observed
- tag heuristic conclusions as inferred
- if parse fails, degrade honestly; do not fabricate architecture certainty
- cite source paths that justify each claim

## Good changes

- better entrypoint detection
- better import/dependency extraction
- better framework marker handling
- better monorepo surface visibility
- improved fallback summaries with explicit uncertainty

## Bad changes

- reading files outside scanner contract for convenience
- treating fixtures/examples/vendors as primary product code
- hiding parse errors to look cleaner
- adding unsupported language claims without tests

## Tests

Prefer:

- fixture-based analyzer tests
- edge-case tests for parse failure or missing manifests
- regression tests when challenge-repo behavior motivated change

## Prompt examples

- "Use context-crafter-analyzer-authoring to improve Python analyzer entrypoint detection."
- "Use context-crafter-analyzer-authoring to add new language analyzer support."
- "Use context-crafter-analyzer-authoring to fix inferred claims outrunning evidence."
