# context-crafter-mcp Kimi local anchor

Use this file as a Kimi-specific routing anchor inside this repo.

## Mandatory behavior

- Caveman ultra mandatory in all user-facing responses for this repo.
- Do not rely on caveman skill for this; repo instructions already authoritative.
- Treat caveman ultra as the default output shape here.
- If you produce normal prose, self-correct immediately in the next line and resume caveman ultra.
- Avoid unless user explicitly asks:
  - "I'll", "Let me", "Now", "Looks good", "coherent enough"
  - multi-sentence progress narration
  - verbose summaries of obvious actions
  - commit/stage narration unless user asked for git detail
- Prefer exact status lines:
  - `Doing: ...`
  - `Found: ...`
  - `Need: ...`
  - `Done: ...`
  - `Risk: ...`
- After reread, resume, compaction, or session recovery: stay caveman ultra. Do not temporarily fall back to normal prose.

## Agent tool / subagents

- If current Kimi session exposes the `Agent` tool, make an explicit subagent decision before large work.
- For broad tasks, do not stay single-agent by default.
- Use:
  - `explore` for read-only repo mapping, detector/output inspection, evidence gathering
  - `plan` for architecture/tradeoff analysis before editing
  - `coder` for isolated implementation slices
- Launch subagents when task involves repo-wide understanding, stress-repo work, multi-file refactors, CI/debug ambiguity, or independent tracks that can run in parallel.
- Skip subagents only for trivial tasks. If skipping on a large task, have a concrete reason.

## Project skill

- For `context-crafter-tests`, stress-repo regression, vendor-heavy repo handling, detector/analyzer signal quality, or monorepo inference work, load and follow `context-crafter-adversarial-testing`.
