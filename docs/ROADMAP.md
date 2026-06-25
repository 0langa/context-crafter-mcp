# Roadmap

## Current state

- Package version in code is **`0.7.0b1`**.
- Latest public git tag on the remote is **`0.7.0b1`**.
- Current `main` is the **post-`0.7.0b1` feature and hardening line** with post-`0.7.0b1` hardening commits after the beta tag.

### What shipped in `0.7.0b1`

The `0.7.0b1` beta adds:

- local release gate automation for the reset-PC setup
- public-surface validation for CLI version/help, MCP config snippets, and MCP stdio initialize/tools-list
- release-doc validation for the pre-`1.0.0` checklist, roadmap state, and CI action baselines
- generic fallback honesty hardening and regression coverage
- retired D-drive external testing references rewritten as historical context
- optional session-completion verifier tests that skip unless a rebuilt external verifier is configured
- fresh fixed real-repo smoke evidence for Python, Node/TypeScript, Go, and Rust

### What shipped in `0.6.0`

The `0.6.0` hardening release adds:

- truthful canonical scan metrics and analyzer coverage tracking
- stronger `doctor` failure handling
- reachable generated-path classification
- real-repo smoke automation for Python / Node / Go / Rust
- richer `RUN_STATE.json` diagnostics with additive schema guidance
- tighter docs around stack confidence and release readiness

## Where we stand

The project is no longer just proving out the architecture. The current work is a **pre-`1.0.0` release train** with five main characteristics:

1. Core CLI and MCP surfaces are stable enough to start freezing.
2. Truthfulness and bounded-scan behavior are now a larger focus than raw feature growth.
3. Python / Node / Go / Rust have meaningful real-repo smoke confidence; Java / .NET remain supported but lower-confidence, fixture-backed stacks.
4. Generic fallback honesty is now guarded locally after the retired external D-drive platform became unavailable.
5. The next value push is better downstream consumption: agents should know which generated file to read first, which files are human-facing, and which JSON surfaces are automation-facing.

## Concrete release plan

### Phase 1: `0.6.0` hardening release (complete)

Purpose:

- publish the post-`0.5.0` hardening work as a real release line
- realign public tags with the code and docs people will actually read
- avoid pretending `1.0.0` readiness before the explicit gate is run end-to-end

Status: complete. `0.6.0` is now tagged and published as the verified hardening baseline.

### Phase 2: `0.7.0b1` beta (complete)

Status: complete. `0.7.0b1` is tagged as the reset-PC/local-gate beta baseline.

### Phase 3: `0.8.0` consumer-value feature sprint

Purpose:

- make generated context bundles easier for agents, humans, and automation to consume
- preserve the additive output contract while adding high-value metadata
- keep the release small enough to validate with the existing local gate

Focus:

- `CONTEXT_MANIFEST.json` as the generated-bundle manifest
- `EVIDENCE_LEDGER.json` as a filterable evidence surface for agent trust decisions
- `COMMANDS.md` as a static, evidence-labeled runbook of likely setup/test/build commands
- clearer recommended starting points for agent, human, navigation, and automation consumers
- docs-truth updates for every generated companion file
- regression tests proving the manifest is emitted and referenced by `RUN_STATE.json`

### Phase 4: `0.9.0` release-candidate hardening

Purpose:

- freeze the public CLI/MCP/output contract before `1.0.0`
- expand confidence from local fixtures to maintained real-repo smoke evidence

Focus:

- installed wheel and sdist smoke on clean temporary environments
- real-repo smoke refresh and matrix update
- MCP resource/result-surface compatibility review
- limitations/security/docs-truth audit

### Phase 5: Execute the pre-`1.0.0` gate

Use [`docs/PRE_1_0_GATE.md`](PRE_1_0_GATE.md) as the stable-release checklist of record.

Focus:

- acceptance commands on a clean checkout
- wheel and sdist verification
- smoke evidence captured and documented
- docs-truth audit across README, architecture, limitations, security, and output contract
- MCP tool/resource/result-surface stability review

### Phase 6: Decide whether to tag `1.0.0`

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
- Keep `CONTEXT_MANIFEST.json`, `RUN_STATE.json`, and other machine-readable outputs additive and automation-friendly.

### 3. Stable-release gate

- `powershell -ExecutionPolicy Bypass -File .\scripts\local_release_gate.ps1` passes on the reset-PC setup.
- `python .\scripts\validate_public_surface.py` passes on the reset-PC setup.
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
