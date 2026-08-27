Map the current repository with Context Crafter and report what it found.

Run `detect_project` on the current directory, then `generate_context` with
`profile="standard"` and `output_dir="docs/generated"`.

Read `AGENT_BRIEF.md` and `SCAN_REPORT.md` from the result. Report:

- detected stacks
- the repo's shape in a few lines: entry points, main source layout, test layout
- anything `SCAN_REPORT.md` flags as skipped or truncated, and whether coverage is partial
- where the files were written, using `resolved_output_dir`

Keep it under 15 lines. Do not paste the generated files back. Do not restate an
inferred claim as an observed one — check `EVIDENCE_LEDGER.json` if a claim
matters.

If the user passed an argument, treat it as the repo path to scan instead of the
current directory.
