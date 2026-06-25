# Roadmap

## Current state

- Package version in code is **`0.6.0`**.
- Latest public git tag on the remote is **`0.6.0`**.
- Current local `main` and the public `0.6.0` tag are aligned on the current hardening baseline.

### What shipped in `0.6.0`

The `0.6.0` hardening release adds:

- truthful canonical scan metrics and analyzer coverage tracking
- stronger `doctor` failure handling
- reachable generated-path classification
- real-repo smoke automation for Python / Node / Go / Rust
- richer `RUN_STATE.json` diagnostics with additive schema guidance
- tighter docs around stack confidence and release readiness

## Where we stand

The project is no longer just proving out the architecture. The current work is a **pre-`1.0.0` hardening line** with three main characteristics:

1. Core CLI and MCP surfaces are stable enough to start freezing.
2. Truthfulness and bounded-scan behavior are now a larger focus than raw feature growth.
3. Python / Node / Go / Rust have meaningful real-repo smoke confidence; Java / .NET remain supported but lower-confidence, fixture-backed stacks.
4. Generic fallback honesty is now guarded locally after the retired external D-drive platform became unavailable.

## Concrete release plan

### Phase 1: `0.6.0` hardening release (complete)

Purpose:

- publish the post-`0.5.0` hardening work as a real release line
- realign public tags with the code and docs people will actually read
- avoid pretending `1.0.0` readiness before the explicit gate is run end-to-end

Status: complete. `0.6.0` is now tagged and published as the verified hardening baseline.

### Phase 2: Execute the pre-`1.0.0` gate

Use [`docs/PRE_1_0_GATE.md`](PRE_1_0_GATE.md) as the checklist of record.

Focus:

- local release gate execution via `scripts/local_release_gate.ps1`
- acceptance commands on a clean checkout
- wheel and sdist verification
- smoke evidence captured and documented
- docs-truth audit across README, architecture, limitations, security, and output contract
- MCP tool/resource/result-surface stability review

### Phase 3: Decide whether to tag `1.0.0`

Tag `1.0.0` only when all of these are true:

- the pre-`1.0.0` gate has been executed rather than assumed
- public docs match the real codebase and current release state
- no known truthfulness issue undermines generated output on the fixed smoke set
- MCP/CLI contracts are stable enough that future changes are additive-only or clearly versioned

If those are not yet true, continue with another hardening release instead of forcing `1.0.0`.

## Near-term priorities

### 1. Release hygiene

- Keep `README.md`, `CHANGELOG.md`, example outputs, package metadata, and public tags aligned to the same version.
- Ensure roadmap/release docs describe both the latest public tag and the current local hardening line accurately.
- Keep local-only artifacts and private workflow debris out of git.

### 2. Product hardening

- Preserve truthful output on ugly mixed repos under bounded scans.
- Keep ambiguous/generic repos honest: low-trust docs/tests/examples/tooling language hints must not promote stack detection.
- Keep vendor/generated/tooling material de-weighted in primary conclusions.
- Improve non-Python analyzer signal only where tests and smoke runs verify it.
- Keep `RUN_STATE.json` and other machine-readable outputs additive and automation-friendly.

### 3. Stable-release gate

- `powershell -ExecutionPolicy Bypass -File .\scripts\local_release_gate.ps1` passes on the reset-PC setup.
- All acceptance commands pass on a clean checkout.
- Remote tags/releases match the version claimed by code and docs.
- Public docs stay honest about limitations and unreleased work.
- Release decisions are driven by the explicit gate, not by optimism.

## Stable-release criteria

- CI green on Windows + Ubuntu, Python 3.11/3.12/3.13.
- Challenge-repo output is truthful, not merely valid.
- Public smoke matrix green with only documented, accepted limitations.
- Docs match real behavior and do not overclaim.
- Installed wheel and sdist pass the release checklist, not just the source tree.
