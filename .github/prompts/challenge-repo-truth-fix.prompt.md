---
mode: ask
description: "Fix a truthfulness problem exposed by the local challenge repo with regression-first workflow and no repo-specific hacks."
---

Use `context-crafter-adversarial-testing`, plus `context-crafter-analyzer-authoring` or `context-crafter-evidence-grounding` as needed.

Goal:
- reproduce misleading output on `context-crafter-tests`
- isolate smallest real failure
- implement smallest general fix
- prove it with regression coverage

Workflow:
1. run challenge repro commands
2. inspect generated output and identify misleading claim or missing real surface
3. define regression assertion before patching
4. patch smallest generalizable layer
5. run focused tests
6. rerun challenge detect/generate/validate
7. summarize what improved, what still fails, and residual overfit risk

Rules:
- truthfulness over flattering output
- no hardcoded challenge-repo paths/names in product logic
- do not suppress warnings to make output look cleaner
