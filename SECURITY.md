# Security Policy

## Threat Model

`context-crafter-mcp` is a local-first, static-analysis tool. It reads source files and writes generated documentation into a configurable output directory inside the repository.

Primary threats we design against:

- **Directory traversal via output_dir** — mitigated by resolving output path and enforcing it stays within the repository root.
- **Symlink traversal / infinite loops** — mitigated by not following symlinks during scanning.
- **Arbitrary code execution in target repo** — mitigated by static analysis only; no execution of target code.
- **Exfiltration via generated docs** — mitigated by local-only operation; no network calls during generation.
- **Prompt injection via untrusted source text** — mitigated by treating all source text as untrusted and escaping it in rendered output.

## Safe Defaults

- Symlinks are **not followed**.
- Hidden files are **excluded** by default.
- Scan depth and file count are **bounded**.
- Binary and oversized files are **skipped**.
- Output is **confined** to the repository root.
- No stdout logging in **MCP stdio mode**.

## Secret Handling

The tool does not attempt to redact secrets from source files. Generated documentation may contain hardcoded credentials if they exist in the source. Review generated output before sharing it.

## Known Limitations

- Static analysis cannot detect runtime behavior, dynamic imports, or conditional architecture.
- Generated docs reflect the state of the repo at scan time.
- HTML rendering uses stdlib-only conversion; complex Markdown may not render perfectly.

## Reporting Process

If you discover a security issue, please open a private vulnerability report via GitHub or email the maintainer directly. Do not open public issues for security bugs.
