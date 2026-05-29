# Limitations

## Analysis Depth

- **Static only**: No runtime behavior, dynamic imports, or conditional architecture.
- **Python**: AST-based (best depth).
- **Non-Python**: Regex/XML/TOML-based metadata parsing (no deep syntax trees).

## Language Support Matrix

| Stack | Detection | Dependency parsing | AST analysis |
|-------|-----------|-------------------|--------------|
| Python | Observed | Observed | Yes |
| Node/JS | Observed | Observed | No |
| .NET | Observed | Observed | No |
| Rust | Observed | Observed | No |
| Go | Observed | Observed | No |
| Java | Observed | Observed | No |
| Generic | Inferred | None | No |

## Known Gaps

- No secret redaction; review output before sharing.
- HTML rendering is stdlib-only.
- Tree-sitter integration is experimental and optional.
- Fixture/example directories are excluded from primary project detection.
