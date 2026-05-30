---
mode: ask
description: "Sync Context Crafter docs to actual code and tests, removing stale claims and preserving truthful limitations."
---

Use `context-crafter-docs-sync` and `context-crafter-evidence-grounding`.

Goal:
- update docs to match actual code
- remove stale or inflated claims
- keep docs concise and contract-focused

Workflow:
1. inspect relevant code, tests, and current docs
2. build implemented vs partial vs planned map
3. rewrite only claims supported by code/tests
4. keep limitations explicit
5. update changelog/report docs if behavior changed
6. report files changed and major stale claims removed

Target docs often include:
- `README.md`
- `CHANGELOG.md`
- `IMPLEMENTATION_REPORT.md`
- `docs/ARCHITECTURE.md`
- `docs/OUTPUT_CONTRACT.md`
- `docs/MCP_CLIENTS.md`
- `docs/SCANNER.md`

Quality bar:
- no fabricated support claims
- examples match real commands
- docs reflect actual CLI/MCP contract
