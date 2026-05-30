# Roadmap

## Current state

Package is still at **v0.4.0**. The project now has a working scanner, CLI, MCP server, analyzers, validation layer, challenge-repo regression coverage, and a small public smoke matrix.

That is **not** the same thing as being near a public `1.0.0`.

The immediate roadmap target is **`0.5.0`**:

- internal hardening baseline
- actionable and validated against the current codebase
- strong enough to support future autonomous documentation/context workflows
- still **not** a public release

`1.0.0` remains the first public release and stays outside this roadmap pass.

## Active path to 0.5.0

### 1. Control-plane hardening

- Keep CLI command names and MCP tool names stable.
- Keep JSON result contracts additive-only; no silent key removals or renames.
- Preserve `resolved_output_dir` and other explicit run metadata.
- Keep scanner, analyzers, renderers, and validation on clean boundaries so the Python control plane can survive future lower-level backend work.
- Reduce contract ambiguity between human-facing docs and machine-facing results.

### 2. Unattended-operation readiness

- Treat every run as something future automation will call repeatedly, without an LLM cleaning up after it.
- Keep commands deterministic, bounded, and explicit about degraded states.
- Make repo-dirty side effects unacceptable unless intentionally documented.
- Strengthen honesty around skipped files, truncated scans, unsupported stacks, and inference strength.
- Tighten self-test, generate, and validate behavior so they are safe building blocks for scheduled or trigger-driven use later.

### 3. Real-world correctness on hostile repositories

- Continue hardening against ugly local repos, especially:
  - mixed-language monorepos
  - vendor/generated flood
  - deeply nested manifests and entry points
  - large docs trees
  - nested ignore rules
  - fixture/demo pollution
- Treat challenge-repo truthfulness as a core quality bar, not an optional confidence pass.
- Keep public smoke coverage for Python, Node/TypeScript, Go, and Rust.
- Keep Java and .NET explicitly below the bar until their results are trustworthy enough for the same standard.

### 4. Machine-actionable output and validation

- Improve outputs so they are not only readable, but reliable inputs for future autonomous maintenance workflows.
- Keep validation conservative and honest; do not hide uncertainty behind “pass” states.
- Prefer explicit unknown/unsupported/degraded reporting over optimistic summaries.
- Continue reducing coupling between ranking heuristics and correctness decisions where that coupling weakens trust.

### 5. Documentation truth and internal audit discipline

- Keep public docs conservative and code-grounded.
- Use `docs/internal/observed_issues.md` for candid internal notes and scary findings that should not become public claims.
- Remove roadmap entries that are already done and unlikely to matter again before the next major quality-gate phase.
- Keep this roadmap focused on what still blocks a credible `0.5.0`.

## 0.5.0 exit criteria

`0.5.0` is done only when all of these are true:

- CLI and MCP contracts are stable enough for future automation to depend on them.
- Current docs match real behavior and do not overclaim maturity.
- Challenge-repo output is not merely valid, but strategically useful and truthful.
- Public smoke matrix remains green with only documented, accepted limitations.
- The codebase reads as a durable Python control plane rather than a throwaway single-purpose MCP utility.
- Known scary issues are either resolved, explicitly accepted, or tracked as blockers in internal notes.

## Not part of this roadmap pass

- Public release preparation
- publish automation
- `1.0.0` release polish
- Rust/C++ backend implementation
- broad feature expansion beyond what is needed to make the current foundation trustworthy
