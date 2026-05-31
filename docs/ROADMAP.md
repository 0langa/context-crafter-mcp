# Roadmap

## Current state

Package version on `main` is **v0.4.0**.

Latest git tag on the public remote is **`0.2.0`**.

There is additional unreleased work on `main`, but it is not a tagged `0.5.0` or `0.6.0` line. Treat it as hardening work in progress until a real release tag is cut.

## Near-term priorities

### 1. Release hygiene

- Cut the next release from verified `main` and tag it coherently.
- Keep `README.md`, `CHANGELOG.md`, example outputs, and package metadata aligned to the same version.
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
