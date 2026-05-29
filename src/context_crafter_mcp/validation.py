"""Extended validation for generated context docs."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationCheck:
    code: str
    level: str  # "ok", "warning", "error"
    message: str
    file: str | None = None


@dataclass
class ValidationResult:
    ok: bool
    output_dir: str
    found: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    checks: list[ValidationCheck] = field(default_factory=list)

    def to_dict(self) -> dict:
        warnings = [
            {"code": c.code, "level": c.level, "message": c.message, "file": c.file}
            for c in self.checks
            if c.level == "warning"
        ]
        errors = [
            {"code": c.code, "level": c.level, "message": c.message, "file": c.file}
            for c in self.checks
            if c.level == "error"
        ]
        return {
            "ok": self.ok,
            "summary": f"Found {len(self.found)}/{len(self.found) + len(self.missing)} required files.",
            "output_dir": self.output_dir,
            "found": self.found,
            "missing": self.missing,
            "count": len(self.found),
            "expected": len(self.found) + len(self.missing),
            "warnings": warnings,
            "errors": errors,
            "checks": [{"code": c.code, "level": c.level, "message": c.message, "file": c.file} for c in self.checks],
        }


_REQUIRED_FILES = [
    "AI_CONTEXT_INDEX.md",
    "PROJECT_OVERVIEW.md",
    "REPO_MAP.md",
    "DEPENDENCY_GRAPH.md",
    "ARCHITECTURE_SUMMARY.md",
    "AGENT_BRIEF.md",
    "VALIDATION_REPORT.md",
    "SCAN_REPORT.md",
]

# Markdown relative link pattern: [text](path) where path does not start with http or #
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

# Backtick-wrapped paths that look like source references
# Matches: src/..., tests/..., docs/..., examples/..., config files
# Allows line number suffixes like :123, and directory trailing slashes
_SOURCE_REF_RE = re.compile(
    r"`((?:src|tests|docs|examples)/[\w./-]+|pyproject\.toml|package\.json|Cargo\.toml|go\.mod|pom\.xml|build\.gradle[^`]*|README\.md|LICENSE[^`]*)`"
)

_FIXTURE_PATHS = ("tests/fixtures/", "examples/demo-repo/")


def _extract_md_links(text: str) -> list[tuple[str, str]]:
    """Return list of (text, path) for relative markdown links."""
    results: list[tuple[str, str]] = []
    for match in _MD_LINK_RE.finditer(text):
        path = match.group(2)
        if path.startswith(("http://", "https://", "#", "mailto:")):
            continue
        if path.startswith("data:"):
            continue
        results.append((match.group(1), path))
    return results


def _extract_source_refs(text: str) -> list[str]:
    """Find backtick-wrapped source paths in markdown text."""
    refs: list[str] = []
    for match in _SOURCE_REF_RE.finditer(text):
        ref = match.group(1)
        # Strip line number suffixes like :123
        if ":" in ref:
            # Only strip if the part after : is all digits
            before, _, after = ref.rpartition(":")
            if after.isdigit():
                ref = before
        # Strip class/method/anchor suffixes like path::Class or path#anchor
        for sep in ("::", "(", "#"):
            if sep in ref:
                ref = ref.split(sep)[0]
        # Strip trailing slash for directory refs
        ref = ref.rstrip("/")
        if ref and ref not in refs:
            refs.append(ref)
    return refs


_MERMAID_DIAGRAM_RE = re.compile(
    r"\b(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|journey|gitGraph|mindmap|timeline)\b",
    re.IGNORECASE,
)


def _check_mermaid_block(content: str) -> ValidationCheck | None:
    """Check that DEPENDENCY_GRAPH.md contains a non-empty, syntactically plausible mermaid block."""
    mermaid_match = re.search(r"```mermaid\n(.*?)\n```", content, re.DOTALL)
    if not mermaid_match:
        return ValidationCheck(
            code="missing_mermaid_block",
            level="error",
            message="DEPENDENCY_GRAPH.md does not contain a mermaid block.",
            file="DEPENDENCY_GRAPH.md",
        )
    block = mermaid_match.group(1).strip()
    if not block:
        return ValidationCheck(
            code="empty_mermaid_block",
            level="warning",
            message="DEPENDENCY_GRAPH.md mermaid block is empty.",
            file="DEPENDENCY_GRAPH.md",
        )
    if not _MERMAID_DIAGRAM_RE.search(block):
        return ValidationCheck(
            code="mermaid_no_diagram_keyword",
            level="warning",
            message="DEPENDENCY_GRAPH.md mermaid block does not contain a recognized diagram keyword.",
            file="DEPENDENCY_GRAPH.md",
        )
    return ValidationCheck(
        code="MERMAID_OK",
        level="ok",
        message="DEPENDENCY_GRAPH.md contains a non-empty mermaid block.",
        file="DEPENDENCY_GRAPH.md",
    )


def _check_fixture_pollution(content: str, file_name: str) -> ValidationCheck | None:
    """Warn if fixture/demo paths appear to be treated as primary project facts."""
    for indicator in _FIXTURE_PATHS:
        if indicator in content:
            # Check if it appears in a list context (suggesting primary claim)
            lines = content.splitlines()
            for line in lines:
                if indicator in line and line.strip().startswith(("- ", "* ", "1. ", "2. ")):
                    return ValidationCheck(
                        code="fixture_path_primary_claim",
                        level="warning",
                        message=f"Fixture/demo path '{indicator}' appears as a primary project item in {file_name}.",
                        file=file_name,
                    )
    return None


def _check_oversized(content: str, file_name: str, threshold: int = 500) -> ValidationCheck | None:
    """Warn if a generated file is unexpectedly large."""
    lines = content.splitlines()
    if len(lines) > threshold:
        return ValidationCheck(
            code="oversized_section",
            level="warning",
            message=f"{file_name} is {len(lines)} lines (threshold {threshold}).",
            file=file_name,
        )
    return None


def validate_output_dir(
    output_dir: str | Path,
    repo_path: str | Path | None = None,
) -> ValidationResult:
    """Validate generated output directory with extended checks."""
    out = Path(output_dir)
    found: list[str] = []
    missing: list[str] = []
    checks: list[ValidationCheck] = []

    for name in _REQUIRED_FILES:
        if (out / name).exists():
            found.append(name)
        else:
            missing.append(name)

    # Check .mmd companion exists if DEPENDENCY_GRAPH.md is found
    if "DEPENDENCY_GRAPH.md" in found:
        if not (out / "DEPENDENCY_GRAPH.mmd").exists():
            checks.append(
                ValidationCheck(
                    code="missing_mermaid_block",
                    level="warning",
                    message="DEPENDENCY_GRAPH.md exists but DEPENDENCY_GRAPH.mmd is missing.",
                    file="DEPENDENCY_GRAPH.md",
                )
            )

    # Infer repo path if not provided
    effective_repo = Path(repo_path) if repo_path else None
    if effective_repo is None and out.name == "generated":
        # Common pattern: docs/generated or .tmp/generated
        candidate = out.parent.parent
        if candidate.is_dir():
            effective_repo = candidate

    # Markdown link checks + source refs + fixture pollution + size
    for name in found:
        path = out / name
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            checks.append(
                ValidationCheck(
                    code="validation_internal_error",
                    level="warning",
                    message=f"Could not read {name}: {exc}.",
                    file=name,
                )
            )
            continue

        # Markdown relative links
        links = _extract_md_links(content)
        for link_text, link_path in links:
            target = out / link_path
            if not target.exists():
                checks.append(
                    ValidationCheck(
                        code="broken_markdown_link",
                        level="warning",
                        message=f"Link '{link_text}' -> '{link_path}' does not resolve.",
                        file=name,
                    )
                )

        # Referenced source paths
        if effective_repo is not None:
            refs = _extract_source_refs(content)
            for ref in refs:
                if not (effective_repo / ref).exists():
                    checks.append(
                        ValidationCheck(
                            code="referenced_source_missing",
                            level="warning",
                            message=f"Referenced source path '{ref}' not found in repository.",
                            file=name,
                        )
                    )

        # Fixture/demo pollution
        fixture_check = _check_fixture_pollution(content, name)
        if fixture_check:
            checks.append(fixture_check)

        # Size check
        size_check = _check_oversized(content, name)
        if size_check:
            checks.append(size_check)

        # Mermaid check
        if name == "DEPENDENCY_GRAPH.md":
            mermaid_check = _check_mermaid_block(content)
            if mermaid_check:
                checks.append(mermaid_check)

    ok = len(missing) == 0 and all(c.level != "error" for c in checks)
    return ValidationResult(
        ok=ok,
        output_dir=str(out.resolve()),
        found=found,
        missing=missing,
        checks=checks,
    )
