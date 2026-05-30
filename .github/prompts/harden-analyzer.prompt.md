---
mode: ask
description: "Harden a Context Crafter analyzer, detector, or ranking path for truthful, evidence-grounded output with regression coverage."
---

Use `context-crafter-analyzer-authoring` and `context-crafter-evidence-grounding`.

Goal:
- improve analyzer/detector/ranking behavior
- reduce overclaiming
- preserve deterministic, source-grounded output

Workflow:
1. inspect relevant analyzer/detector/ranking files and nearest tests
2. identify exact failure class:
   - missed entrypoint
   - wrong project type
   - vendor/fixture pollution
   - weak confidence assignment
   - misleading summary wording from weak evidence
3. define smallest generalizable fix
4. patch analyzer/detector/ranking/validation layer, not just renderer wording unless wording is root cause
5. add focused regression tests, including challenge-repo coverage if relevant
6. run focused tests, then broader checks if contract changed
7. report what became more truthful and what remains uncertain

Quality bar:
- observed evidence preferred over inferred
- unknown/unsupported states preserved when certainty missing
- no repo-specific hacks
- tests prove change
