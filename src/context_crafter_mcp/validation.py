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
        return {
            "ok": self.ok,
            "output_dir": self.output_dir,
            "found": self.found,
            "missing": self.missing,
            "count": len(self.found),
            "expected": len(self.found) + len(self.missing),
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


def _check_mermaid_block(content: str) -> ValidationCheck | None:
    """Check that DEPENDENCY_GRAPH.md contains a non-empty mermaid block."""
    mermaid_match = re.search(r"```mermaid\n(.*?)\n```", content, re.DOTALL)
    if not mermaid_match:
        return ValidationCheck(
            code="MERMAID_MISSING",
            level="error",
            message="DEPENDENCY_GRAPH.md does not contain a mermaid block.",
            file="DEPENDENCY_GRAPH.md",
        )
    block = mermaid_match.group(1).strip()
    if not block:
        return ValidationCheck(
            code="MERMAID_EMPTY",
            level="warning",
            message="DEPENDENCY_GRAPH.md mermaid block is empty.",
            file="DEPENDENCY_GRAPH.md",
        )
    return ValidationCheck(
        code="MERMAID_OK",
        level="ok",
        message="DEPENDENCY_GRAPH.md contains a non-empty mermaid block.",
        file="DEPENDENCY_GRAPH.md",
    )


def validate_output_dir(output_dir: str | Path) -> ValidationResult:
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

    # Markdown link checks
    for name in found:
        path = out / name
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            checks.append(
                ValidationCheck(
                    code="READ_ERROR",
                    level="warning",
                    message=f"Could not read {name}.",
                    file=name,
                )
            )
            continue

        links = _extract_md_links(content)
        for link_text, link_path in links:
            # Resolve relative to output dir
            target = out / link_path
            if not target.exists():
                checks.append(
                    ValidationCheck(
                        code="BROKEN_LINK",
                        level="warning",
                        message=f"Link '{link_text}' -> '{link_path}' does not resolve.",
                        file=name,
                    )
                )

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
