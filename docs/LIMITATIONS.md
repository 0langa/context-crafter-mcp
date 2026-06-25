# Limitations

## Analysis depth

- Static only: no runtime behavior, dynamic imports, or conditional architecture.
- Python: stdlib `ast`.
- Java: `javalang`.
- Node/TypeScript: `tree-sitter-javascript` / `tree-sitter-typescript` with regex fallback.
- Go: `tree-sitter-go` with regex fallback.
- Rust: `tree-sitter-rust` with regex fallback.
- .NET: `tree-sitter-c-sharp` for `.cs` plus XML parsing for project files, with regex fallback where needed.
- Generic: directory and filename heuristics only.

## Parser support matrix

| Language | Metadata Detection | Syntax-Aware Parsing | AST Backend | Fallback | Extra Required |
|----------|-------------------|----------------------|-------------|----------|----------------|
| Python | `pyproject.toml`, `requirements.txt`, `setup.py`, `*.py` | Yes | stdlib `ast` | N/A (always available) | — |
| Node/TS | `package.json`, `tsconfig.json`, `*.js`, `*.ts` | Yes | `tree-sitter-javascript` / `tree-sitter-typescript` | Regex/heuristics | `parsers` |
| .NET | `*.sln`, `*.csproj` | Yes | `tree-sitter-c-sharp` | Regex/XML | `parsers` |
| Rust | `Cargo.toml`, `*.rs` | Yes | `tree-sitter-rust` | Regex/heuristics | `parsers` |
| Go | `go.mod`, `*.go` | Yes | `tree-sitter-go` | Regex/heuristics | `parsers` |
| Java | `pom.xml`, `build.gradle`, `*.java` | Yes | `javalang` | Regex/heuristics | — |
| Generic | Directory/filename heuristics | No | None | N/A | — |

Install the `parsers` extra to enable Tree-sitter backends:

```bash
uv sync --extra parsers
```

## Fallback behavior

Non-Python analyzers are intended to degrade gracefully when parser support is unavailable or parsing fails. Result quality can drop from AST-backed evidence to regex/heuristic evidence without becoming a hard crash.

## Known gaps

- Basic secret awareness flags potential secret files (`.env`, `secrets.json`, `credentials.json`) in scan reports. Generated outputs apply conservative redaction for obvious key/token/password values, but this is not a full secret-scanning engine; review generated output before sharing.
- No deep semantic call graph construction.
- No runtime dependency resolution.
- HTML rendering uses the `markdown` package when available, with stdlib fallback otherwise.
- Test/example/demo-context fixtures are excluded from primary project detection. Product-path fixtures (e.g., `src/fixtures/`) are included.
- Directories named `vendor`, `vendors`, `node_modules`, `third_party`, `generated`, `gen`, `autogen`, `dist`, `build`, `out`, `target`, `bin`, `obj`, `.next`, `.turbo`, `.cache` and similar are hard-skipped during scanning and do not appear in scan statistics or generated output.
- Some generated-like directories (e.g., `output/`) may still be scanned and classified as `[generated]` rather than omitted entirely.
- Bounded scans may truncate files when `max_files` or `max_files_per_dir` caps are exceeded. Priority ordering ensures truncation hits lowest-signal files first.
- Source-reference validation is conservative and backtick-oriented; bare prose paths are not validated.
- Compact profile intentionally omits optional sections even when a small repo could technically fit more detail.

## Roadmap-scope note

For the current pre-`1.0.0` hardening target, real-world smoke coverage is focused on Python, Node/TypeScript, Go, and Rust. Java now supports nested multi-module discovery (all `pom.xml` / `build.gradle` files), but its analysis depth is still not at the same trust bar. .NET remains primarily fixture-backed until it is hardened enough for the same standard.
