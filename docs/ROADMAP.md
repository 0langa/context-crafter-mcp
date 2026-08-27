# Roadmap

## Current state

- Package version in code: **`1.0.0`**.
- Latest public git tag on the remote: `1.0.0`.
- `main` is the **stable `1.0.0` line**. The public contract is frozen; changes are additive-only until a major bump.

### What shipped in `1.0.0`

First stable release. `docs/PRE_1_0_GATE.md` was executed end-to-end on `2026-08-27` and carries a
dated evidence table of the commands run and their results.

- pre-`1.0.0` gate executed rather than assumed
- dated real-repo smoke evidence for Python, Node/TypeScript, Go, Rust with zero errors
- installed wheel and sdist smoke passing on clean temporary environments
- PyPI distribution as `context-crafter-mcp`, so the documented `uvx context-crafter-mcp serve` MCP
  client config resolves a real published package
- `.github/workflows/release.yml` for tag-triggered build, trusted publishing, and release upload

### What shipped in `0.7.0b1`

`0.7.0b1` beta adds:

- local release gate automation for reset-PC setup
- public-surface validation for CLI version/help, MCP config snippets, MCP stdio initialize/tools-list
- release-doc validation for pre-`1.0.0` checklist, roadmap state, CI action baselines
- generic fallback honesty hardening and regression coverage
- retired D-drive external testing references rewritten as historical context
- optional session-completion verifier tests that skip unless rebuilt external verifier configured
- fresh fixed real-repo smoke evidence for Python, Node/TypeScript, Go, Rust

### What shipped in `0.6.0`

`0.6.0` hardening release adds:

- truthful canonical scan metrics and analyzer coverage tracking
- stronger `doctor` failure handling
- reachable generated-path classification
- real-repo smoke automation for Python / Node / Go / Rust
- richer `RUN_STATE.json` diagnostics with additive schema guidance
- tighter docs around stack confidence and release readiness

## Where we stand

No longer proving out architecture. Current work: **pre-`1.0.0` release train** with five characteristics:

1. Core CLI and MCP surfaces stable enough to freeze.
2. Truthfulness and bounded-scan behavior outrank raw feature growth.
3. Python / Node / Go / Rust have real-repo smoke confidence; Java / .NET stay supported but lower-confidence, fixture-backed stacks.
4. Generic fallback honesty guarded locally after retired external D-drive platform became unavailable.
5. `0.9.0` release-candidate line freezes public contract and proves installed artifacts before final `1.0.0` push.

## Concrete release plan

### Phase 1: `0.6.0` hardening release (complete)

Purpose:

- publish post-`0.5.0` hardening work as real release line
- realign public tags with code and docs people read
- never claim `1.0.0` readiness before explicit gate runs end-to-end

Status: complete. `0.6.0` tagged and published as verified hardening baseline.

### Phase 2: `0.7.0b1` beta (complete)

Status: complete. `0.7.0b1` tagged as reset-PC/local-gate beta baseline.

### Phase 3: `0.8.0` consumer-value feature sprint

Purpose:

- make generated context bundles easier for agents, humans, automation to consume
- preserve additive output contract while adding high-value metadata
- keep release small enough to validate with existing local gate

Status: complete. `0.8.0` packages consumer-value generated-bundle features added after `0.7.0b1` beta.

Shipped:

- `CONTEXT_MANIFEST.json` as generated-bundle manifest
- `EVIDENCE_LEDGER.json` as filterable evidence surface for agent trust decisions
- `COMMANDS.md` as static, evidence-labeled runbook of likely setup/test/build commands
- clearer recommended starting points for agent, human, navigation, automation consumers
- docs-truth updates for every generated companion file
- regression tests proving manifest is emitted and referenced by `RUN_STATE.json`

### Phase 4: `0.9.0` release-candidate hardening

Purpose:

- freeze public CLI/MCP/output contract before `1.0.0`
- expand confidence from local fixtures to maintained real-repo smoke evidence

Status: complete. `0.9.0` is release-candidate hardening line before `1.0.0`.

Shipped:

- installed wheel and sdist smoke on clean temporary environments
- repeatable installed-artifact smoke gate for release candidates
- public surface freeze evidence in `docs/PUBLIC_SURFACE_FREEZE.md`
- real-repo smoke refresh and matrix update
- MCP resource/result-surface compatibility review
- limitations/security/docs-truth audit

### Phase 5: Execute the pre-`1.0.0` gate (complete)

Status: complete. [`docs/PRE_1_0_GATE.md`](PRE_1_0_GATE.md) was executed end-to-end on `2026-08-27`
and records its evidence inline.

Covered:

- acceptance commands on clean checkout
- wheel and sdist verification
- smoke evidence captured and documented
- docs-truth audit across README, architecture, limitations, security, output contract
- MCP tool/resource/result-surface stability review

### Phase 6: Tag `1.0.0` (complete)

Status: complete. Every gate condition held at tag time:

- pre-`1.0.0` gate executed, not assumed
- public docs match real codebase and current release state
- no known truthfulness issue undermines generated output on fixed smoke set
- MCP/CLI contracts stable enough that future changes are additive-only or clearly versioned

### Phase 7: Post-`1.0.0` (open)

Additive work only; anything removing public surface needs a deprecation cycle and a major bump.

- promote Java and .NET from fixture-only to real-repo smoke confidence
- incremental regeneration so large repos avoid full-scan cost on unchanged scope
- richer `CONTEXT_MANIFEST.json` consumers, HTML renderer polish, MCP resource pagination for large bundles

## Near-term priorities

### 1. Release hygiene

- Keep `README.md`, `CHANGELOG.md`, example outputs, package metadata, public tags aligned to same version.
- Roadmap/release docs describe both latest public tag and current local hardening line accurately.
- Keep local-only artifacts and private workflow debris out of git.

### 2. Product hardening

- Preserve truthful output on ugly mixed repos under bounded scans.
- Keep ambiguous/generic repos honest: low-trust docs/tests/examples/tooling language hints must not promote stack detection.
- Keep vendor/generated/tooling material de-weighted in primary conclusions.
- Improve non-Python analyzer signal only where tests and smoke runs verify it.
- Keep `CONTEXT_MANIFEST.json`, `RUN_STATE.json`, other machine-readable outputs additive and automation-friendly.

### 3. Release gate (now the standing per-release bar)

- `powershell -ExecutionPolicy Bypass -File .\scripts\local_release_gate.ps1` passes on reset-PC setup.
- `python .\scripts\validate_public_surface.py` passes on reset-PC setup.
- All acceptance commands pass on clean checkout.
- Remote tags/releases match version claimed by code and docs.
- Public docs stay honest about limitations and unreleased work.
- Release decisions driven by explicit gate, not optimism.

## Per-release criteria (held for `1.0.0`, applies to every release after it)

- CI green on Windows + Ubuntu, Python 3.11/3.12/3.13.
- Challenge-repo output truthful, not merely valid.
- Public smoke matrix green with only documented, accepted limitations.
- Docs match real behavior and do not overclaim.
- Installed wheel and sdist pass release checklist, not just source tree.
