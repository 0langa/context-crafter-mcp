---
name: crafter:using-context-crafter
description: Use this skill when you land in an unfamiliar repository, when the user asks what a codebase is or how it is laid out, before planning a large refactor or migration in code you have not read, when onboarding to a project after a context reset or handoff, or when you need a dependency graph, repo map, or architecture summary. Also use it when deciding whether a Context Crafter claim is trustworthy enough to act on.
---

# Using Context Crafter

## Purpose

Context Crafter turns a repository into a compact context bundle so you can orient
without reading every file. It is a static analyser. It reads source text and
project metadata. It never executes target-repo code, resolves dependencies over
the network, or calls a model.

Reach for it when the cost of reading the repo file by file is higher than the
cost of one scan.

## When to use it

Good triggers:

- You are in a repository you have not seen and need its shape before acting.
- The user asks "what is this project", "how is this laid out", "what depends on what".
- You are about to plan a refactor, migration, or review across code you have not read.
- A session started fresh after a context reset and needs project orientation.
- You need a dependency graph or an architecture summary as a deliverable.

Poor triggers:

- You already know the file you need. Read it directly.
- The question is about one function or one file. Read it directly.
- You need runtime behavior, actual call graphs, or resolved dependency versions.
  Context Crafter is static and will not have them.

## Tools

| Tool | Use it for |
|------|-----------|
| `detect_project` | Which stacks a repo uses. Cheap. Run first when unsure. |
| `generate_context` | The full bundle. The main entry point. |
| `generate_project_overview` | Just `PROJECT_OVERVIEW.md`. |
| `generate_repo_map` | Just `REPO_MAP.md`. |
| `generate_dependency_graph` | Just `DEPENDENCY_GRAPH.md` plus the raw `.mmd` source. |
| `generate_architecture_summary` | Just `ARCHITECTURE_SUMMARY.md`. |
| `validate_generated_context` | Check a bundle is complete and internally consistent. |
| `explain_capabilities` | Capability and analyzer metadata. Use when unsure what is supported. |

Every tool returns JSON with `ok`, `summary`, `warnings`, and `errors`. Check `ok`
before trusting the rest.

## What gets generated

Nine Markdown files plus four companions. Read them in this order:

1. `AGENT_BRIEF.md` — one page, written for you. Start here.
2. `REPO_MAP.md` — directory tree with config and test directories marked.
3. `ARCHITECTURE_SUMMARY.md` — patterns, risks, and stated unknowns.
4. `DEPENDENCY_GRAPH.md` — Mermaid graph plus external dependencies.

The rest (`PROJECT_OVERVIEW.md`, `COMMANDS.md`, `VALIDATION_REPORT.md`,
`SCAN_REPORT.md`, `AI_CONTEXT_INDEX.md`) are there when you need detail.

Machine-readable companions: `DEPENDENCY_GRAPH.mmd`, `EVIDENCE_LEDGER.json`,
`CONTEXT_MANIFEST.json`, `RUN_STATE.json`. Their schemas are additive. Parse
defensively.

## Evidence discipline

This is the part that matters most.

`EVIDENCE_LEDGER.json` labels every claim as **observed**, **inferred**,
**unknown**, **unsupported**, or **error**. Honor those labels:

- **observed** — read directly from the repo. Safe to state as fact.
- **inferred** — a heuristic guess. Say "looks like" or verify before acting.
- **unknown** — the analyzer could not tell. Do not fill the gap with a guess.

Never upgrade an inferred claim to an observed one when you summarize. The whole
point of the ledger is that the bundle tells you what it does not know.

`COMMANDS.md` is inferred, not executed. The commands in it are plausible, not
verified. Check before running one.

## Limits worth knowing

- Python is AST-backed via stdlib `ast`. Node/TypeScript, Go, Rust, and .NET use
  tree-sitter with a regex fallback. Java uses `javalang`.
- Java and .NET are fixture-backed only. They work, but they have not been proven
  against real repositories the way Python, Node, Go, and Rust have. Weight their
  output accordingly.
- Bounded scans can truncate. Check `SCAN_REPORT.md` for `budget_exhausted` and
  skipped counts before treating coverage as complete.
- Generated writes are confined to the repository root. If a requested output path
  would escape it, output lands in `docs/generated`. Read `resolved_output_dir` in
  the result to see where files actually went.
- Secret handling is conservative redaction of obvious key/token/password values.
  It is not a secret scanner. Review generated output before sharing it.

## Related

For the step-by-step orientation workflow, use `crafter:onboard-repo`.
