# Limitations

## Analysis Depth

- **Static only**: No runtime behavior, dynamic imports, or conditional architecture.
- **Python**: AST-based via stdlib `ast` (best depth).
- **Java**: AST-based via `javalang` (full AST parsing).
- **Node/TypeScript**: AST-based via `tree-sitter-javascript` / `tree-sitter-typescript`.
- **Go**: AST-based via `tree-sitter-go`.
- **Rust**: AST-based via `tree-sitter-rust`.
- **.NET**: AST-based via `tree-sitter-c-sharp` for `.cs` files; XML for `.csproj`.
- **Generic**: Directory and filename heuristics only.

## Fallback Behavior

All non-Python analyzers gracefully fall back to regex-based parsing if the AST parser is unavailable or fails. This ensures the tool works even when optional native parser wheels cannot be installed.

## Known Gaps

- No secret redaction; review output before sharing.
- HTML rendering uses the `markdown` library when available, stdlib fallback otherwise.
- Fixture/example directories are excluded from primary project detection.
- Nested `.gitignore` files are supported via `pathspec` with "deepest matching wins" semantics.
- Profile differences on small repositories: compact always omits optional sections (Evidence, Generic Notes, Architecture subsections) regardless of repo size.
- Source-reference validation covers `src/`, `tests/`, `docs/`, `scripts/`, `examples/` (with extensions), and common config files; bare paths without backticks are not validated.
