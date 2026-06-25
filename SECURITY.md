# Security Policy

## Scope

`context-crafter-mcp` is a local-first, static-analysis CLI and MCP stdio server. It reads repository files, detects likely project stacks, and writes generated context documentation into an output directory that is confined to the scanned repository root.

The primary runtime surfaces are:

- CLI commands: `detect`, `generate`, `validate`, `doctor`, `self-test`, `mcp-config`, and `serve`.
- MCP tools: repository detection, context generation, individual document generation, validation, and capability explanation.
- Session-scoped MCP resources under `context-crafter://latest/<filename>` after generation.

## Threat Model

Primary threats and current mitigations:

| Threat | Existing mitigation |
|--------|---------------------|
| Directory traversal via `output_dir` | Output paths are resolved under the repository root; escaping paths are confined to `docs/generated`. |
| Confused-deputy writes to surprising paths | Generation results include `resolved_output_dir` so callers can verify the actual write location. |
| Arbitrary local file reads through MCP resources | Resource reads are session-scoped to files generated in the current server session; arbitrary local paths and traversal are rejected. |
| Symlink traversal or recursive filesystem loops | Scans do not follow symlinks. |
| Unbounded scanning denial of service | Scans are bounded by depth, file count, per-directory caps, and file size limits. |
| Arbitrary code execution in a target repo | Analysis is static-only; Context Crafter does not execute target repository code. |
| Network exfiltration during generation | Generation is local-only and does not make network calls. |
| Secret-like values copied into generated output | Generated writes apply conservative redaction for obvious key/token/password assignments and values. |
| Prompt injection through untrusted source text | Source text is treated as untrusted input; generated claims should remain evidence-backed and explicit about unknowns. |
| MCP stdio protocol corruption | Server mode avoids stdout logging outside MCP protocol messages. |

## Safe Defaults

- Symlinks are **not followed**.
- Hidden files are **excluded** by default.
- Scan depth and file count are **bounded**.
- Binary and oversized files are **skipped**.
- Output is **confined** to the repository root.
- Generation results report the **resolved output directory** after confinement.
- No stdout logging in **MCP stdio mode**.
- MCP resource reads are **session-scoped**; arbitrary local paths and traversal are blocked.

## Secret Handling

Generated-output writes apply conservative redaction for obvious key/token/password values, including common assignment and JSON-like forms. This is a last-mile sharing guard, not a full secret-scanning engine.

Do not treat generated documentation as guaranteed secret-free. Review generated output before sharing it outside the trusted environment, especially when scanning private repositories.

## Known Limitations

- Static analysis cannot detect runtime behavior, dynamic imports, or conditional architecture.
- Generated docs reflect the state of the repo at scan time.
- Redaction is heuristic and intentionally conservative; it can miss unusual secret formats and can redact benign examples.
- The tool does not authenticate MCP clients. Run it only in trusted local MCP client configurations.
- Generated resources are in-memory/session-scoped; restarting the MCP server clears the resource registry.
- HTML rendering uses the `markdown` library with stdlib fallback; most common Markdown constructs render correctly.

## Reporting Process

If you discover a security issue, please open a private vulnerability report via GitHub or email the maintainer directly. Do not open public issues for security bugs.
