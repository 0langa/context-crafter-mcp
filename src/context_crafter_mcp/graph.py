"""LangGraph orchestration for context-crafter-mcp."""

from __future__ import annotations

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from context_crafter_mcp.analyzers import AnalyzerRegistry
from context_crafter_mcp.analyzers.generic import analyze_generic
from context_crafter_mcp.detectors import detect_project, detect_project_from_snapshot
from context_crafter_mcp.models import AnalysisResult, DetectResult, RenderResult, ScanConfig
from context_crafter_mcp.renderers.markdown import (
    render_ai_context_index,
    render_agent_brief,
    render_architecture_summary,
    render_context_manifest,
    render_evidence_ledger,
    render_project_overview,
    render_repo_map,
    render_run_state,
    render_scan_report,
    render_validation_report,
)
from context_crafter_mcp.renderers.mermaid import render_dependency_graph
from context_crafter_mcp.state import RepoState


def node_validate_repo(state: RepoState) -> dict[str, object]:
    """Validate repo_path exists."""
    from context_crafter_mcp.filesystem import safe_output_path, validate_repo_path

    path = validate_repo_path(state.repo_path)
    if path is None:
        state.ok = False
        state.errors.append(f"Invalid repo_path: {state.repo_path}")
        return {"ok": state.ok}
    state.resolved_output_dir = str(safe_output_path(path, state.output_dir))
    return {"ok": state.ok, "resolved_output_dir": state.resolved_output_dir}


def node_detect_project(state: RepoState) -> dict[str, object]:
    """Detect project types."""
    if not state.ok:
        return {}
    snapshot = state.analysis.snapshot if state.analysis is not None else None
    if snapshot is not None:
        state.detect_result = detect_project_from_snapshot(snapshot)
    else:
        state.detect_result = detect_project(state.repo_path)
    if not state.detect_result.exists:
        state.ok = False
        state.errors.append(state.detect_result.error or "Repository does not exist")
    if state.analysis is not None and state.detect_result.evidence_set:
        state.analysis.evidence_set.items.extend(state.detect_result.evidence_set.items)
    return {"detect_result": state.detect_result, "ok": state.ok}


def node_scan_files(state: RepoState) -> dict[str, object]:
    """Run generic scan."""
    if not state.ok:
        return {}
    state.analysis = analyze_generic(state.repo_path, config=state.scan_config)
    return {"analysis": state.analysis}


def node_run_analyzers(state: RepoState) -> dict[str, object]:
    """Run all registered analyzers for detected project types."""
    if not state.ok:
        return {}
    if state.detect_result is None:
        return {}

    registry = AnalyzerRegistry.from_globals()
    for ptype in state.detect_result.project_types:
        if ptype == "generic":
            continue
        state.analysis = registry.analyze_for_type(ptype, state.repo_path, state.analysis, state.scan_config)

    return {"analysis": state.analysis}


def node_render_outputs(state: RepoState) -> dict[str, object]:
    """Render all output files."""
    if not state.ok:
        return {}
    if state.analysis is None or state.detect_result is None:
        state.ok = False
        state.errors.append("Missing analysis or detection result")
        return {"ok": False}

    gen_at = state.generated_at
    results: list[RenderResult] = []
    results.append(
        render_ai_context_index(
            state.repo_path, state.detect_result, state.analysis, state.output_dir, generated_at=gen_at
        )
    )
    results.append(
        render_project_overview(
            state.repo_path, state.detect_result, state.analysis, state.output_dir, generated_at=gen_at
        )
    )
    results.append(
        render_repo_map(state.repo_path, state.detect_result, state.analysis, state.output_dir, generated_at=gen_at)
    )
    results.append(
        render_dependency_graph(
            state.repo_path, state.detect_result, state.analysis, state.output_dir, generated_at=gen_at
        )
    )
    results.append(
        render_architecture_summary(
            state.repo_path, state.detect_result, state.analysis, state.output_dir, generated_at=gen_at
        )
    )
    results.append(
        render_agent_brief(state.repo_path, state.detect_result, state.analysis, state.output_dir, generated_at=gen_at)
    )
    results.append(
        render_scan_report(state.repo_path, state.detect_result, state.analysis, state.output_dir, generated_at=gen_at)
    )

    written: list[str] = []
    for r in results:
        if r.ok:
            written.extend(r.written)
        else:
            if r.error:
                state.errors.append(r.error)

    # Validation report needs the full written list
    val_result = render_validation_report(
        state.repo_path,
        state.detect_result,
        state.analysis,
        state.output_dir,
        written_files=written,
        generated_at=gen_at,
    )
    if val_result.ok:
        written.extend(val_result.written)
    elif val_result.error:
        state.errors.append(val_result.error)

    evidence_result = render_evidence_ledger(
        state.repo_path,
        state.detect_result,
        state.analysis,
        state.output_dir,
        generated_at=gen_at,
    )
    if evidence_result.ok:
        written.extend(evidence_result.written)
    elif evidence_result.error:
        state.errors.append(evidence_result.error)

    # Machine-readable manifest for consumers deciding where to start.
    manifest_result = render_context_manifest(
        state.repo_path,
        state.detect_result,
        state.analysis,
        state.output_dir,
        written_files=written,
        errors=state.errors,
        generated_at=gen_at,
    )
    if manifest_result.ok:
        written.extend(manifest_result.written)
    elif manifest_result.error:
        state.errors.append(manifest_result.error)

    # Machine-readable run-state for downstream automation
    run_state_result = render_run_state(
        state.repo_path,
        state.detect_result,
        state.analysis,
        state.output_dir,
        written_files=written,
        errors=state.errors,
        generated_at=gen_at,
    )
    if run_state_result.ok:
        written.extend(run_state_result.written)
    elif run_state_result.error:
        state.errors.append(run_state_result.error)

    state.written = written
    return {"written": written}


def build_graph() -> CompiledStateGraph:
    """Build and compile the LangGraph pipeline."""
    builder = StateGraph(RepoState)

    builder.add_node("validate_repo", node_validate_repo)
    builder.add_node("detect_project", node_detect_project)
    builder.add_node("scan_files", node_scan_files)
    builder.add_node("run_analyzers", node_run_analyzers)
    builder.add_node("render_outputs", node_render_outputs)

    builder.set_entry_point("validate_repo")
    builder.add_edge("validate_repo", "scan_files")
    builder.add_edge("scan_files", "detect_project")
    builder.add_edge("detect_project", "run_analyzers")
    builder.add_edge("run_analyzers", "render_outputs")
    builder.add_edge("render_outputs", END)

    return builder.compile()


def _run_analysis(repo_path: str, config: ScanConfig | None = None) -> tuple[DetectResult, AnalysisResult | None]:
    """Run detection and analysis for a single tool call.

    Reuses the same node functions as the full graph pipeline to avoid
    duplicating detect / analyze flow.
    """
    state = RepoState(repo_path=repo_path, scan_config=config or ScanConfig())
    node_scan_files(state)
    node_detect_project(state)
    if not state.ok or state.detect_result is None:
        return state.detect_result or DetectResult(repo_path=repo_path, exists=False), None
    node_run_analyzers(state)
    return state.detect_result, state.analysis


def run_generate_all(
    repo_path: str, output_dir: str = "docs/generated", scan_config: ScanConfig | None = None
) -> RepoState:
    """Run the full pipeline synchronously and return the final state."""
    import os

    graph = build_graph()
    state = RepoState(repo_path=repo_path, output_dir=output_dir, scan_config=scan_config or ScanConfig())
    frozen = os.environ.get("CONTEXT_CRAFTER_FROZEN_TIME")
    if frozen:
        state.generated_at = frozen
    result = graph.invoke(state)
    if isinstance(result, RepoState):
        return result
    final = RepoState()
    for key, value in result.items():
        if hasattr(final, key):
            setattr(final, key, value)
    return final


def run_detect(repo_path: str) -> DetectResult:
    """Run detection only."""
    return detect_project(repo_path)


def run_generate_project_overview(
    repo_path: str, output_dir: str = "docs/generated", scan_config: ScanConfig | None = None
) -> RenderResult:
    """Run pipeline and return only project overview result."""
    detect, analysis = _run_analysis(repo_path, scan_config)
    if analysis is None:
        return RenderResult(ok=False, error=detect.error or "Repository not found")
    return render_project_overview(repo_path, detect, analysis, output_dir)


def run_generate_repo_map(
    repo_path: str, output_dir: str = "docs/generated", scan_config: ScanConfig | None = None
) -> RenderResult:
    """Run pipeline and return only repo map result."""
    detect, analysis = _run_analysis(repo_path, scan_config)
    if analysis is None:
        return RenderResult(ok=False, error=detect.error or "Repository not found")
    return render_repo_map(repo_path, detect, analysis, output_dir)


def run_generate_dependency_graph(
    repo_path: str, output_dir: str = "docs/generated", scan_config: ScanConfig | None = None
) -> RenderResult:
    """Run pipeline and return only dependency graph result."""
    detect, analysis = _run_analysis(repo_path, scan_config)
    if analysis is None:
        return RenderResult(ok=False, error=detect.error or "Repository not found")
    return render_dependency_graph(repo_path, detect, analysis, output_dir)


def run_generate_architecture_summary(
    repo_path: str, output_dir: str = "docs/generated", scan_config: ScanConfig | None = None
) -> RenderResult:
    """Run pipeline and return only architecture summary result."""
    detect, analysis = _run_analysis(repo_path, scan_config)
    if analysis is None:
        return RenderResult(ok=False, error=detect.error or "Repository not found")
    return render_architecture_summary(repo_path, detect, analysis, output_dir)
