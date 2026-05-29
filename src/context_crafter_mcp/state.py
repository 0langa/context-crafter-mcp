"""LangGraph state definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from context_crafter_mcp.models import AnalysisResult, DetectResult, ScanConfig


@dataclass
class RepoState:
    """State carried through the LangGraph pipeline."""

    repo_path: str = ""
    output_dir: str = "docs/generated"
    resolved_output_dir: str | None = None
    scan_config: ScanConfig = field(default_factory=ScanConfig)
    detect_result: DetectResult | None = None
    analysis: AnalysisResult | None = None
    written: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    ok: bool = True

    def to_tool_result(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "summary": (
                f"Generated {len(self.written)} file(s) for {', '.join(self.detect_result.project_types if self.detect_result else [])}"
                if self.ok
                else f"Generation failed: {'; '.join(self.errors)}"
            ),
            "generated_files": self.written,
            "written": self.written,
            "files_scanned": self.analysis.files_scanned if self.analysis else 0,
            "project_types": self.detect_result.project_types if self.detect_result else [],
            "resolved_output_dir": self.resolved_output_dir,
            "warnings": [],
            "errors": self.errors,
        }
