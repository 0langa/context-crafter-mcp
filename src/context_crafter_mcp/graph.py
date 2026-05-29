"""LangGraph orchestration for context-crafter-mcp."""

from __future__ import annotations

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from context_crafter_mcp.analyzers import analyze_for_type
from context_crafter_mcp.analyzers.generic import analyze_generic
from context_crafter_mcp.detectors import detect_project
from context_crafter_mcp.models import AnalysisResult, DetectResult, RenderResult, ScanConfig
from context_crafter_mcp.renderers.markdown import (
    render_ai_context_index,
    render_agent_brief,
    render_architecture_summary,
    render_project_overview,
    render_repo_map,
    render_scan_report,
    render_validation_report,
)
from context_crafter_mcp.renderers.mermaid import render_dependency_graph
from context_crafter_mcp.state import RepoState


def node_validate_repo(state: RepoState) -> dict[str, object]:
    """Validate repo_path exists."""
    from context_crafter_mcp.filesystem import validate_repo_path

    path = validate_repo_path(state.repo_path)
    if path is None:
        state.ok = False
        state.errors.append(f"Invalid repo_path: {state.repo_path}")
    return {"ok": state.ok}


def node_detect_project(state: RepoState) -> dict[str, object]:
    """Detect project types."""
    if not state.ok:
        return {}
    state.detect_result = detect_project(state.repo_path)
    if not state.detect_result.exists:
        state.ok = False
        state.errors.append(state.detect_result.error or "Repository does not exist")
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

    for ptype in state.detect_result.project_types:
        if ptype == "generic":
            continue
        state.analysis = analyze_for_type(ptype, state.repo_path, state.analysis, state.scan_config)

    return {"analysis": state.analysis}


def node_render_outputs(state: RepoState) -> dict[str, object]:
    """Render all output files."""
    if not state.ok:
        return {}
    if state.analysis is None or state.detect_result is None:
        state.ok = False
        state.errors.append("Missing analysis or detection result")
        return {"ok": False}

    results: list[RenderResult] = []
    results.append(render_ai_context_index(state.repo_path, state.detect_result, state.analysis, state.output_dir))
    results.append(render_project_overview(state.repo_path, state.detect_result, state.analysis, state.output_dir))
    results.append(render_repo_map(state.repo_path, state.detect_result, state.analysis, state.output_dir))
    results.append(render_dependency_graph(state.repo_path, state.detect_result, state.analysis, state.output_dir))
    results.append(render_architecture_summary(state.repo_path, state.detect_result, state.analysis, state.output_dir))
    results.append(render_agent_brief(state.repo_path, state.detect_result, state.analysis, state.output_dir))
    results.append(render_scan_report(state.repo_path, state.detect_result, state.analysis, state.output_dir))

    written: list[str] = []
    for r in results:
        if r.ok:
            written.extend(r.written)
        else:
            if r.error:
                state.errors.append(r.error)

    # Validation report needs the full written list
    val_result = render_validation_report(
        state.repo_path, state.detect_result, state.analysis, state.output_dir, written_files=written
    )
    if val_result.ok:
        written.extend(val_result.written)
    elif val_result.error:
        state.errors.append(val_result.error)

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
    builder.add_edge("validate_repo", "detect_project")
    builder.add_edge("detect_project", "scan_files")
    builder.add_edge("scan_files", "run_analyzers")
    builder.add_edge("run_analyzers", "render_outputs")
    builder.add_edge("render_outputs", END)

    return builder.compile()


def _run_analysis(repo_path: str, config: ScanConfig | None = None) -> tuple[DetectResult, AnalysisResult | None]:
    """Run detection and analysis for a single tool call."""
    detect = detect_project(repo_path)
    if not detect.exists:
        return detect, None
    cfg = config or ScanConfig()
    analysis = analyze_generic(repo_path, config=cfg)
    for ptype in detect.project_types:
        if ptype == "generic":
            continue
        analysis = analyze_for_type(ptype, repo_path, analysis, cfg)
    return detect, analysis


def run_generate_all(
    repo_path: str, output_dir: str = "docs/generated", scan_config: ScanConfig | None = None
) -> RepoState:
    """Run the full pipeline synchronously and return the final state."""
    graph = build_graph()
    state = RepoState(repo_path=repo_path, output_dir=output_dir, scan_config=scan_config or ScanConfig())
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
