---
name: context-crafter-adversarial-testing
description: Use when working on context-crafter-mcp against the local adversarial repo context-crafter-tests, including challenge-repo regression work, detector/analyzer truthfulness fixes, vendor-flood handling, monorepo inference, primary-surface ranking, and hard-repo validation. Regression-first workflow only; no pass-the-test theater or repo-specific hacks.
---

# Context Crafter Adversarial Testing

Use this skill only in `context-crafter-mcp` when the task involves the local challenge repo:

- `C:\Users\juliu\source\repos\context-crafter-tests`

Treat that repo as adversarial signal, not as a special case to hardcode around.

## Objective

Improve `context-crafter-mcp` on ugly real local repos while preserving:

- deterministic behavior
- local-first static-only analysis
- stable CLI command names
- stable MCP tool names
- existing JSON result keys

Truthfulness beats apparent completeness.

## Known Failure Classes

- detector overfits root tooling
- vendored extension floods dominate evidence
- deep primary surfaces get missed
- mixed-monorepo reality gets flattened
- important-file / entrypoint ranking is weak
- generated docs can be structurally valid but strategically wrong
- validator can pass semantically misleading output

## Non-Negotiable Rules

- Do not hardcode `context-crafter-tests` paths or names into product logic unless the logic generalizes cleanly.
- Do not optimize for “pass” by suppressing warnings or hiding uncertainty.
- Do not silently change CLI names, MCP tool names, or existing JSON keys.
- Do not weaken scanner safety limits to brute-force the repo.
- Do not claim the primary surface unless evidence supports it.

## Regression-First Workflow

1. Reproduce current behavior on the challenge repo.
2. Identify the smallest real failure worth fixing.
3. Define an explicit regression assertion before patching.
4. Implement the smallest generalizable fix.
5. Run focused tests first.
6. Re-run challenge-repo detect/generate/validate.
7. Re-run broader repo checks if behavior changed cross-cutting logic.

Do not start with “make it pass somehow.”

## Preferred Initial Assertions

Use only the subset relevant to the change:

- detection includes `python`
- output acknowledges mixed / monorepo reality
- generated docs mention `services/api/python`
- vendor mirror does not dominate primary conclusions
- likely entrypoints include real runtime surfaces, not just tooling scripts
- architecture summary becomes less misleading
- scan-budget pressure or skipped-signal is surfaced honestly when relevant

## Required Commands

Run from `C:\Users\juliu\source\repos\context-crafter-mcp`.

Challenge repro:

```powershell
uv run context-crafter-mcp detect C:\Users\juliu\source\repos\context-crafter-tests --json
uv run context-crafter-mcp generate C:\Users\juliu\source\repos\context-crafter-tests --output docs/generated-real --profile standard --json
uv run context-crafter-mcp validate C:\Users\juliu\source\repos\context-crafter-tests\docs\generated-real --repo C:\Users\juliu\source\repos\context-crafter-tests --json
```

Focused verification:

```powershell
uv run pytest tests/path/to/relevant_test.py -q
```

Broader verification when warranted:

```powershell
uv run ruff check .
uv run mypy src
uv run pytest -q
```

## What Good Looks Like

- challenge output becomes more truthful, not merely more flattering
- primary conclusions stop being hijacked by vendor/tooling noise
- deep real application surfaces become visible
- remaining uncertainty is explicit
- fixes generalize beyond one repo

## Final Report

Always report:

- regression assertion added or updated
- product behavior changed
- challenge commands run
- normal tests run
- what improved
- what still fails
- residual overfit risk
