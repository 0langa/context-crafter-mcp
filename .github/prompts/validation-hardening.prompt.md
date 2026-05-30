---
mode: ask
description: "Strengthen Context Crafter validation so misleading generated output is caught earlier and reported honestly."
---

Use `context-crafter-evidence-grounding` and `context-crafter-mcp-development`.

Goal:
- improve validation coverage beyond file existence
- catch misleading or weakly grounded generated docs

Workflow:
1. inspect `src/context_crafter_mcp/validation.py`, renderers, output contract docs, and validation tests
2. identify missing validation signal:
   - broken relative links
   - weak Mermaid graph block
   - missing source-path grounding
   - fixture/demo pollution in primary claims
   - missing warnings for skipped/budget-limited scans
3. implement smallest conservative validation rule
4. add focused tests
5. rerun validation-related checks
6. report new warning/error codes and behavior

Quality bar:
- conservative checks, not fantasy certainty
- machine-readable warning/error codes where repo pattern supports them
- tests prove validator catches real issue without broad false positives
