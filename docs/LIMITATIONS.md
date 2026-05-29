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

## Fallback behavior

Non-Python analyzers are intended to degrade gracefully when parser support is unavailable or parsing fails. Result quality can drop from AST-backed evidence to regex/heuristic evidence without becoming a hard crash.

## Known gaps

- No secret redaction; review generated output before sharing.
- No deep semantic call graph construction.
- No runtime dependency resolution.
- HTML rendering uses the `markdown` package when available, with stdlib fallback otherwise.
- Fixture/example directories are excluded from primary project detection.
- Source-reference validation is conservative and backtick-oriented; bare prose paths are not validated.
- Compact profile intentionally omits optional sections even when a small repo could technically fit more detail.

## Release-scope note

Before `1.0.0`, real-world smoke coverage is focused on Python, Node/TypeScript, Go, and Rust. Java and .NET remain primarily fixture-backed until the release sprint or until a blocker appears.
