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
    generated_at: str | None = None

    def to_tool_result(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "ok": self.ok,
            "summary": (
                f"Generated {len(self.written)} file(s) for {', '.join(self.detect_result.project_types if self.detect_result else [])}"
                if self.ok
                else f"Generation failed: {'; '.join(self.errors)}"
            ),
            "generated_files": self.written,
            "written": self.written,
            "files_scanned": self.analysis.scan_summary.files_scanned
            if self.analysis and self.analysis.scan_summary
            else 0,
            "project_types": self.detect_result.project_types if self.detect_result else [],
            "resolved_output_dir": self.resolved_output_dir,
            "warnings": [],
            "errors": self.errors,
        }
        if self.analysis and self.analysis.scan_summary:
            ss = self.analysis.scan_summary
            result["scan_summary"] = {
                "files_scanned": ss.files_scanned,
                "dirs_scanned": ss.dirs_scanned,
                "files_skipped": ss.files_skipped,
                "dirs_skipped": ss.dirs_skipped,
                "budget_exhausted": ss.budget_exhausted,
                "skipped_reasons": ss.skipped_reasons,
                "category_counts": ss.category_counts,
            }
            result["analyzer_files_parsed"] = self.analysis.analyzer_files_parsed
        return result
