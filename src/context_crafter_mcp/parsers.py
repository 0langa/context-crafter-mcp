"""Optional deep parsers: tree-sitter for JS/TS/Go/Rust/C#, javalang for Java.

All parsers gracefully fall back to None if libraries are missing or parsing fails.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass
class ParsedModule:
    """Generic parsed module result."""

    imports: list[str] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    traits: list[str] = field(default_factory=list)
    impls: list[str] = field(default_factory=list)
    parser_used: str = "none"
    error: str | None = None


class ParserBackend(Protocol):
    """Protocol for parser backends."""

    def parse(self, source: bytes, language: str) -> Any | None:
        """Parse source bytes and return parsed result or None."""


def _ts_node_text(source: bytes, node: Any) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _find_child_by_type(node: Any, node_type: str) -> Any | None:
    for child in node.children:
        if child.type == node_type:
            return child
    return None


def _find_children_by_type(node: Any, node_type: str) -> list[Any]:
    return [c for c in node.children if c.type == node_type]


def _tree_sitter_parse(source: bytes, language: Any) -> Any | None:
    """Parse source bytes with tree-sitter."""
    try:
        from tree_sitter import Language, Parser

        parser = Parser(Language(language()))
        return parser.parse(source)
    except (ImportError, ModuleNotFoundError, OSError, ValueError, TypeError, RuntimeError):
        return None


class TreeSitterBackend:
    """Tree-sitter parser backend for JS/TS/Go/Rust/C#."""

    def parse(self, source: bytes, language: str) -> Any | None:
        if language == "javascript":
            return self._parse_javascript(source)
        if language == "typescript":
            return self._parse_typescript(source)
        if language == "go":
            return self._parse_go(source)
        if language == "rust":
            return self._parse_rust(source)
        if language == "csharp":
            return self._parse_csharp(source)
        return None

    def _parse_javascript(self, source: bytes) -> ParsedModule | None:
        try:
            from tree_sitter_javascript import language as js_lang
        except (ImportError, ModuleNotFoundError):
            return None

        tree = _tree_sitter_parse(source, js_lang)
        if tree is None:
            return None

        result = ParsedModule(parser_used="tree-sitter-javascript")
        root = tree.root_node

        def _walk(node: Any) -> None:
            if node.type == "import_statement":
                source_clause = _find_child_by_type(node, "string")
                if source_clause:
                    raw = _ts_node_text(source, source_clause).strip("'\"")
                    result.imports.append(raw)
            elif node.type == "export_statement":
                decl = None
                for child in node.children:
                    if child.type in (
                        "function_declaration",
                        "class_declaration",
                        "lexical_declaration",
                        "variable_declaration",
                    ):
                        decl = child
                        break
                if decl:
                    name_node = _find_child_by_type(decl, "identifier")
                    if not name_node and decl.type in ("lexical_declaration", "variable_declaration"):
                        vd = _find_child_by_type(decl, "variable_declarator")
                        if vd:
                            name_node = _find_child_by_type(vd, "identifier")
                    if name_node:
                        result.exports.append(_ts_node_text(source, name_node))
            elif node.type == "function_declaration":
                name_node = _find_child_by_type(node, "identifier")
                if name_node:
                    result.functions.append(_ts_node_text(source, name_node))
            elif node.type == "class_declaration":
                name_node = _find_child_by_type(node, "identifier")
                if name_node:
                    result.classes.append(_ts_node_text(source, name_node))
            elif node.type == "call_expression":
                func = node.children[0] if node.children else None
                if func and func.type == "identifier" and _ts_node_text(source, func) == "require":
                    args = _find_child_by_type(node, "arguments")
                    if args:
                        str_node = _find_child_by_type(args, "string")
                        if str_node:
                            result.imports.append(_ts_node_text(source, str_node).strip("'\""))
            for child in node.children:
                _walk(child)

        _walk(root)
        return result

    def _parse_typescript(self, source: bytes) -> ParsedModule | None:
        try:
            from tree_sitter_typescript import language_typescript as ts_lang
        except (ImportError, ModuleNotFoundError):
            return None

        tree = _tree_sitter_parse(source, ts_lang)
        if tree is None:
            return None

        result = ParsedModule(parser_used="tree-sitter-typescript")
        root = tree.root_node

        def _walk(node: Any) -> None:
            if node.type == "import_statement":
                source_clause = _find_child_by_type(node, "string")
                if source_clause:
                    result.imports.append(_ts_node_text(source, source_clause).strip("'\""))
            elif node.type == "export_statement":
                for child in node.children:
                    if child.type in (
                        "function_declaration",
                        "class_declaration",
                        "lexical_declaration",
                        "variable_declaration",
                        "interface_declaration",
                        "type_alias_declaration",
                    ):
                        name_node = _find_child_by_type(child, "identifier") or _find_child_by_type(
                            child, "type_identifier"
                        )
                        if not name_node and child.type in ("lexical_declaration", "variable_declaration"):
                            decl = _find_child_by_type(child, "variable_declarator")
                            if decl:
                                name_node = _find_child_by_type(decl, "identifier")
                        if name_node:
                            result.exports.append(_ts_node_text(source, name_node))
                        break
            elif node.type == "function_declaration":
                name_node = _find_child_by_type(node, "identifier")
                if name_node:
                    result.functions.append(_ts_node_text(source, name_node))
            elif node.type == "class_declaration":
                name_node = _find_child_by_type(node, "identifier")
                if name_node:
                    result.classes.append(_ts_node_text(source, name_node))
            elif node.type == "interface_declaration":
                name_node = _find_child_by_type(node, "type_identifier")
                if name_node:
                    result.classes.append(_ts_node_text(source, name_node))
            for child in node.children:
                _walk(child)

        _walk(root)
        return result

    def _parse_go(self, source: bytes) -> ParsedModule | None:
        try:
            from tree_sitter_go import language as go_lang
        except (ImportError, ModuleNotFoundError):
            return None

        tree = _tree_sitter_parse(source, go_lang)
        if tree is None:
            return None

        result = ParsedModule(parser_used="tree-sitter-go")
        root = tree.root_node

        def _walk(node: Any) -> None:
            if node.type == "import_spec":
                str_node = _find_child_by_type(node, "interpreted_string_literal") or _find_child_by_type(
                    node, "raw_string_literal"
                )
                if str_node:
                    result.imports.append(_ts_node_text(source, str_node).strip("\"'`"))
            elif node.type == "function_declaration":
                name_node = _find_child_by_type(node, "identifier")
                if name_node:
                    name = _ts_node_text(source, name_node)
                    result.functions.append(name)
                    if name == "main":
                        result.entry_points.append("")
            elif node.type == "type_spec":
                name_node = _find_child_by_type(node, "type_identifier")
                type_node = node.children[-1] if node.children else None
                if name_node and type_node:
                    if type_node.type == "struct_type":
                        result.classes.append(_ts_node_text(source, name_node))
                    elif type_node.type == "interface_type":
                        result.dependencies.append(_ts_node_text(source, name_node))
            for child in node.children:
                _walk(child)

        _walk(root)
        return result

    def _parse_rust(self, source: bytes) -> ParsedModule | None:
        try:
            from tree_sitter_rust import language as rust_lang
        except (ImportError, ModuleNotFoundError):
            return None

        tree = _tree_sitter_parse(source, rust_lang)
        if tree is None:
            return None

        result = ParsedModule(parser_used="tree-sitter-rust")
        root = tree.root_node

        def _walk(node: Any) -> None:
            if node.type == "use_declaration":
                result.imports.append(_ts_node_text(source, node))
            elif node.type == "mod_item":
                name_node = _find_child_by_type(node, "identifier")
                if name_node:
                    result.exports.append(_ts_node_text(source, name_node))
            elif node.type == "function_item":
                name_node = _find_child_by_type(node, "identifier")
                if name_node:
                    name = _ts_node_text(source, name_node)
                    result.functions.append(name)
                    if name == "main":
                        result.entry_points.append("")
            elif node.type == "struct_item":
                name_node = _find_child_by_type(node, "type_identifier") or _find_child_by_type(node, "identifier")
                if name_node:
                    result.classes.append(_ts_node_text(source, name_node))
            elif node.type == "trait_item":
                name_node = _find_child_by_type(node, "type_identifier") or _find_child_by_type(node, "identifier")
                if name_node:
                    result.traits.append(_ts_node_text(source, name_node))
            elif node.type == "impl_item":
                ids = (
                    _find_children_by_type(node, "type_identifier")
                    + _find_children_by_type(node, "identifier")
                    + _find_children_by_type(node, "primitive_type")
                )
                if ids:
                    result.impls.append(_ts_node_text(source, ids[-1]))
            for child in node.children:
                _walk(child)

        _walk(root)
        return result

    def _parse_csharp(self, source: bytes) -> ParsedModule | None:
        try:
            from tree_sitter_c_sharp import language as cs_lang
        except (ImportError, ModuleNotFoundError):
            return None

        tree = _tree_sitter_parse(source, cs_lang)
        if tree is None:
            return None

        result = ParsedModule(parser_used="tree-sitter-c-sharp")
        root = tree.root_node

        def _walk(node: Any) -> None:
            if node.type == "using_directive":
                result.imports.append(_ts_node_text(source, node).replace("using", "").replace(";", "").strip())
            elif node.type == "class_declaration":
                name_node = _find_child_by_type(node, "identifier")
                if name_node:
                    result.classes.append(_ts_node_text(source, name_node))
            elif node.type == "method_declaration":
                name_node = _find_child_by_type(node, "identifier")
                if name_node:
                    result.functions.append(_ts_node_text(source, name_node))
            elif node.type == "interface_declaration":
                name_node = _find_child_by_type(node, "identifier")
                if name_node:
                    result.dependencies.append(_ts_node_text(source, name_node))
            for child in node.children:
                _walk(child)

        _walk(root)
        return result


class JavalangBackend:
    """javalang parser backend for Java."""

    def parse(self, source: bytes, language: str) -> Any | None:
        if language != "java":
            return None
        try:
            import javalang  # type: ignore[import-untyped]
        except (ImportError, ModuleNotFoundError):
            return None

        try:
            text = source.decode("utf-8", errors="replace")
        except (ValueError, TypeError):
            return None

        try:
            tree = javalang.parse.parse(text)
        except Exception as exc:
            return ParsedModule(parser_used="javalang", error=f"{type(exc).__name__}: {exc}")

        result = ParsedModule(parser_used="javalang")

        pkg = tree.package.name if tree.package else ""

        for imp in tree.imports:
            if imp.path:
                result.imports.append(imp.path)

        for type_decl in tree.types:
            if type_decl.name:
                fq = f"{pkg}.{type_decl.name}" if pkg else type_decl.name
                result.classes.append(fq)

            for _, node in type_decl.filter(javalang.tree.MethodDeclaration):
                if node.name:
                    result.functions.append(node.name)
                if node.name == "main" and node.modifiers and "static" in [str(m) for m in node.modifiers]:
                    result.entry_points.append("")

            for _, node in type_decl.filter(javalang.tree.Annotation):
                if node.name:
                    result.dependencies.append(str(node.name))

        return result


class PythonAstBackend:
    """stdlib ast parser backend for Python."""

    def parse(self, source: bytes, language: str) -> Any | None:
        if language != "python":
            return None
        try:
            text = source.decode("utf-8", errors="replace")
        except (ValueError, TypeError):
            return None
        import ast

        try:
            return ast.parse(text)
        except SyntaxError:
            return None


class RegexFallbackBackend:
    """No-op fallback backend."""

    def parse(self, source: bytes, language: str) -> Any | None:
        return None


_BACKENDS: dict[str, ParserBackend] = {
    "javascript": TreeSitterBackend(),
    "typescript": TreeSitterBackend(),
    "csharp": TreeSitterBackend(),
    "go": TreeSitterBackend(),
    "rust": TreeSitterBackend(),
    "java": JavalangBackend(),
    "python": PythonAstBackend(),
}


def get_parser_backend(language: str) -> ParserBackend:
    """Return the parser backend for a language."""
    return _BACKENDS.get(language, RegexFallbackBackend())


# Backward compatibility wrappers


def parse_javascript(path: Path) -> ParsedModule | None:
    """Parse a JavaScript file with tree-sitter."""
    backend = get_parser_backend("javascript")
    try:
        source = path.read_bytes()
    except OSError:
        return None
    return backend.parse(source, "javascript")


def parse_typescript(path: Path) -> ParsedModule | None:
    """Parse a TypeScript file with tree-sitter."""
    backend = get_parser_backend("typescript")
    try:
        source = path.read_bytes()
    except OSError:
        return None
    return backend.parse(source, "typescript")


def parse_java(path: Path) -> ParsedModule | None:
    """Parse a Java file with javalang."""
    backend = get_parser_backend("java")
    try:
        source = path.read_bytes()
    except OSError:
        return None
    return backend.parse(source, "java")


def parse_go(path: Path) -> ParsedModule | None:
    """Parse a Go file with tree-sitter."""
    backend = get_parser_backend("go")
    try:
        source = path.read_bytes()
    except OSError:
        return None
    return backend.parse(source, "go")


def parse_rust(path: Path) -> ParsedModule | None:
    """Parse a Rust file with tree-sitter."""
    backend = get_parser_backend("rust")
    try:
        source = path.read_bytes()
    except OSError:
        return None
    return backend.parse(source, "rust")


def parse_csharp(path: Path) -> ParsedModule | None:
    """Parse a C# file with tree-sitter."""
    backend = get_parser_backend("csharp")
    try:
        source = path.read_bytes()
    except OSError:
        return None
    return backend.parse(source, "csharp")
