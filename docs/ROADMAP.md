# Roadmap

## Current state

Package version on `main` is **v0.5.0**.

Latest git tag on the public remote is **`0.5.0`**.

Current `main` is the tagged `0.5.0` release line.

## Near-term priorities

### 1. Release hygiene

- Keep `README.md`, `CHANGELOG.md`, example outputs, package metadata, and public tags aligned to the same version.
- Keep local agent/customization artifacts out of git.

### 2. Product hardening

- Preserve truthful output on ugly mixed repos under bounded scans.
- Keep vendor/generated/tooling material de-weighted in primary conclusions.
- Improve non-Python analyzer signal only where tests and smoke runs verify it.

### 3. Stable-release gate

- All acceptance commands pass on a clean checkout.
- Remote tags/releases match the version claimed by code and docs.
- Public docs stay honest about limitations and unreleased work.

## Stable-release criteria

- CI green on Windows + Ubuntu, Python 3.11/3.12/3.13.
- Challenge-repo output is truthful, not merely valid.
- Public smoke matrix green with only documented, accepted limitations.
- Docs match real behavior and do not overclaim.
