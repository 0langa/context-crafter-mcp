---
name: crafter:onboard-repo
description: Use this skill to orient yourself in an unfamiliar repository before doing work in it - when starting a task in a codebase you have not read, when resuming after a context reset or provider handoff, or when the user asks you to map, survey, or summarize a project. Runs the Context Crafter scan-then-read workflow and keeps evidence levels intact.
---

# Onboard to a repository

A five-step workflow for getting oriented in a codebase you have not read.

Use this when you are about to do real work in an unfamiliar repo. Do not use it
to answer a question about a single known file.

## Step 1 — Detect the stacks

```
detect_project(repo_path=".")
```

Cheap. Tells you which analyzers will run and whether the repo is a monorepo.

If it returns only `generic`, the repo has no recognizable stack markers. That is
an honest answer, not a failure. Expect thinner output and say so.

## Step 2 — Pick a profile, then generate

```
generate_context(repo_path=".", output_dir="docs/generated", profile="standard")
```

| Profile | When |
|---------|------|
| `compact` | Quick orientation, or a very large repo where you want the shape only. |
| `standard` | Default. Use unless you have a reason not to. |
| `deep` | You are doing architecture work and want maximum detail. |

Check `ok` in the result. Check `resolved_output_dir` — if the path you asked for
would have escaped the repo root, output was confined to `docs/generated`.

## Step 3 — Read the brief first

Read `AGENT_BRIEF.md` before anything else. It is one page and written for an
agent audience.

Then read only what your task needs:

- Changing structure or adding files → `REPO_MAP.md`
- Refactoring across modules → `DEPENDENCY_GRAPH.md`
- Judging design or risk → `ARCHITECTURE_SUMMARY.md`
- Needing setup or test commands → `COMMANDS.md`

Do not read all nine files by default. That defeats the purpose.

## Step 4 — Check coverage before trusting it

Read `SCAN_REPORT.md`. Two things matter:

- `budget_exhausted` true means the scan hit a cap and stopped early. Coverage is
  partial. Say so before making whole-repo claims.
- A large `files_skipped` count means the same thing more quietly.

Then run:

```
validate_generated_context(output_dir="docs/generated", repo_path=".")
```

Passing `repo_path` enables source-reference checking, which catches claims that
point at files that do not exist. Worth it.

## Step 5 — Keep the evidence levels

Before you summarize anything to the user, check `EVIDENCE_LEDGER.json` for the
claims you are about to repeat.

State observed claims plainly. Hedge inferred ones. Leave unknowns as unknown.

The bundle's value is that it distinguishes these. If you flatten them into
confident prose, you have thrown away the only thing that made it trustworthy.

## When the repo is too big

If `budget_exhausted` keeps coming back true:

1. Scope the scan to the subtree you actually care about — pass that path as
   `repo_path` instead of the repo root.
2. Or use `profile="compact"` for shape, then generate a focused document for the
   part you need with `generate_repo_map` or `generate_dependency_graph`.

Do not present a truncated scan as a complete survey.

## Related

For tool reference, output meanings, and limits, see `crafter:using-context-crafter`.
