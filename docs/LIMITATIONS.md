# Limitations

## Analysis Depth

- **Static only**: No runtime behavior, dynamic imports, or conditional architecture.
- **Python**: AST-based (best depth).
- **Non-Python**: Regex/XML/TOML-based metadata parsing (no deep syntax trees).

## Language Support Matrix

| Stack | Detection | Dependency parsing | Symbol extraction |
|-------|-----------|-------------------|-------------------|
| Python | Observed | Observed | AST-based (classes, functions, imports, constants) |
| Node/JS | Observed | Observed | Regex-based (classes, functions, exports, imports) |
| .NET | Observed | Observed | Regex/XML-based (classes, target framework, output type) |
| Rust | Observed | Observed | Regex-based (modules, traits, impls, use statements) |
| Go | Observed | Observed | Regex-based (structs, interfaces, functions, imports) |
| Java | Observed | Observed | Regex/XML-based (classes, methods, annotations, imports) |
| Generic | Inferred | None | None |

## Known Gaps

- No secret redaction; review output before sharing.
- HTML rendering is stdlib-only.
- Tree-sitter integration is experimental and optional.
- Fixture/example directories are excluded from primary project detection.
- Nested `.gitignore` files are supported via `pathspec` with "deepest matching wins" semantics.
- Profile differences on small repositories: compact omits empty optional sections (Architecture Patterns, Key Abstractions, Module Relationships, Generic Notes) when the repo has fewer than 15 scanned files.
- Source-reference validation in generated docs is conservative and may miss some paths or produce false negatives.
