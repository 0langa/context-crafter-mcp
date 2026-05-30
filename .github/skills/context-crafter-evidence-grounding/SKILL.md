---
name: context-crafter-evidence-grounding
description: "Harden context-crafter-mcp evidence quality, confidence assignment, validation checks, and truthfulness of generated docs. Use when: evidence inflation, misleading architecture summary, wrong confidence, missing warnings, validator too weak, generated docs overclaim, or output needs better observed vs inferred grounding."
---

# Context Crafter Evidence Grounding

Use this skill when generated output feels misleading, overconfident, or under-explained.

## Goal

Keep generated docs truthful:

- observed facts first
- inferred claims labeled clearly
- unknowns preserved
- unsupported paths admitted
- warnings exposed when confidence weak

## Workflow

1. inspect failing/misleading generated output
2. trace claim back to analyzer/ranking/renderer/validation source
3. classify failure:
   - evidence missing
   - confidence too high
   - ranking amplified weak signal
   - renderer overstated wording
   - validator missed misleading output
4. patch smallest responsible layer
5. add regression test near source of failure
6. rerun generate/validate path if output wording changed

## Checks to strengthen

- observed vs inferred balance
- warnings for skipped or budget-limited scans
- mixed-monorepo wording
- primary-surface claims backed by evidence
- generated docs avoid fantasy certainty

## Anti-patterns

- silencing warnings instead of fixing claim quality
- moving weak claims from inferred to observed
- patching renderer wording while root evidence still wrong
- optimizing for pretty docs over truthful docs

## Prompt examples

- "Use context-crafter-evidence-grounding to reduce overclaiming in architecture summary."
- "Use context-crafter-evidence-grounding to add validation for misleading generated docs."
- "Use context-crafter-evidence-grounding to fix confidence scoring on mixed repos."
