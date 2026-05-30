# context-crafter-mcp codex-local routing

Use this file as an additional local anchor for Codex in this repo.

## Mandatory behavior

- Caveman ultra is mandatory in all user-facing responses in this repo.
- Do not rely on the `caveman` skill for this; the repo instructions themselves are authoritative.
- Do not fall back to normal prose unless the user explicitly asks or clarity/safety truly requires a brief exception.
- Treat caveman ultra as a hard output contract, not a soft style preference.
- If output slips into normal prose, self-correct immediately in next line and resume caveman ultra.
- Forbidden unless user explicitly asks:
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
- After reread, compaction, resume, or refresh: caveman ultra still mandatory.

## Skills

- Prefer Project-scope skills from `.agents/skills/` over overlapping user-scope workflow skills.
- For `context-crafter-tests`, adversarial regression, detector/analyzer truthfulness, vendor-flood handling, or monorepo inference work, always load and follow `context-crafter-adversarial-testing`.
- If `context-crafter-adversarial-testing` is not visible in the current session, stop and refresh/restart before continuing that work.

## Kimi subagents

- If Kimi exposes the `Agent` tool in this repo, make an explicit subagent decision before large tasks.
- Use subagents by default for repo audits, challenge-repo work, multi-file changes, CI/debug ambiguity, or parallel exploration/planning/implementation tracks.
- Prefer:
  - `explore` for read-only mapping/evidence
  - `plan` for approach design
  - `coder` for isolated fix slices

## Product guardrails

- Preserve stable CLI command names.
- Preserve stable MCP tool names.
- Do not rename or remove existing JSON result keys.
- Keep behavior deterministic, local-first, and static-only.
- No repo-specific hacks keyed to `context-crafter-tests`.
