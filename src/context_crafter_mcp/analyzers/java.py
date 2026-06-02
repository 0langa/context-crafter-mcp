"""Java analyzer with javalang AST and regex fallback."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from context_crafter_mcp.analyzers import register_analyzer, register_analyzer_spec
from context_crafter_mcp.analyzers.snapshot_utils import get_analysis_snapshot, iter_snapshot_files
from context_crafter_mcp.detectors import _is_fixture_path
from context_crafter_mcp.filesystem import safe_read_text, validate_repo_path
from context_crafter_mcp.models import AnalysisResult, AnalyzerSpec, EvidenceKind, JavaProject, ScanConfig
from context_crafter_mcp.parsers import get_parser_backend
from context_crafter_mcp.scanner import SnapshotFile

GRADLE_NAME_RE = re.compile(r'rootProject\.name\s*=\s*["\']([^"\']+)["\']')
GRADLE_DEP_RE = re.compile(
    r"(?:implementation|compile|api|testImplementation)\s+[=\"\']([^\"\']+:[^\"\']+:[^\"\']+)[\"\']"
)
JAVA_MAIN_RE = re.compile(r"public\s+static\s+void\s+main\s*\(", re.MULTILINE)
JAVA_CLASS_RE = re.compile(r"\b(public\s+)?(class|interface|enum|record)\s+(\w+)")
JAVA_PACKAGE_RE = re.compile(r"^package\s+([\w.]+);", re.MULTILINE)
JAVA_IMPORT_RE = re.compile(r"^import\s+([\w.*]+);", re.MULTILINE)
JAVA_METHOD_RE = re.compile(
    r"\b(public|protected|private)\s+(?:static\s+)?(?:final\s+)?[\w<>,\[\]\s]+\s+(\w+)\s*\(", re.MULTILINE
)
JAVA_ANNOTATION_RE = re.compile(r"@(\w+)")
JAVA_EXTENDS_RE = re.compile(r"\bclass\s+\w+\s+extends\s+(\w+)")
JAVA_IMPLEMENTS_RE = re.compile(r"\bclass\s+\w+\s+implements\s+([\w,\s]+)")
_JAVA_FRAMEWORKS: dict[str, set[str]] = {
    "spring": {"spring", "springboot", "spring-boot", "springframework"},
    "jakarta-ee": {"jakarta", "javax.enterprise", "jakartaee"},
    "micronaut": {"micronaut"},
    "quarkus": {"quarkus"},
    "hibernate": {"hibernate", "jpa"},
}


def parse_pom(path: Path) -> JavaProject:
    """Parse a Maven pom.xml file."""
    proj = JavaProject(build_tool="maven")
    text = safe_read_text(path)
    if text is None:
        return proj
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        proj.dependencies = [f"Parse error: {exc}"]
        return proj

    for name in root.iter("{http://maven.apache.org/POM/4.0.0}artifactId"):
        if name.text and not proj.name:
            proj.name = name.text
            break
    for dep in root.iter("{http://maven.apache.org/POM/4.0.0}dependency"):
        group = dep.find("{http://maven.apache.org/POM/4.0.0}groupId")
        artifact = dep.find("{http://maven.apache.org/POM/4.0.0}artifactId")
        if group is not None and artifact is not None and group.text and artifact.text:
            proj.dependencies.append(f"{group.text}:{artifact.text}")
    for module in root.iter("{http://maven.apache.org/POM/4.0.0}module"):
        if module.text:
            proj.modules.append(module.text)
    return proj


def parse_gradle(path: Path) -> JavaProject:
    """Parse a Gradle build file lightly."""
    proj = JavaProject(build_tool="gradle")
    text = safe_read_text(path)
    if text is None:
        return proj
    m = GRADLE_NAME_RE.search(text)
    if m:
        proj.name = m.group(1)
    for dep in GRADLE_DEP_RE.finditer(text):
        proj.dependencies.append(dep.group(1))
    return proj


def analyze_java(
    repo_path: str,
    base_result: AnalysisResult | None = None,
    config: ScanConfig | None = None,
) -> AnalysisResult:
    """Analyze Java files in the repository."""
    path = validate_repo_path(repo_path)
    if path is None:
        result = base_result or AnalysisResult(repo_path=repo_path)
        result.errors.append(f"Invalid repo_path: {repo_path}")
        return result

    cfg = config or ScanConfig()
    result = base_result or AnalysisResult(repo_path=str(path))
    snapshot = get_analysis_snapshot(path, result, cfg)
    ev = result.evidence_set
    parser_used = "regex"

    # Pass 1: discover build files and collect Java source paths
    build_files: list[tuple[Path, Path, str]] = []
    java_files: list[tuple[SnapshotFile, Path]] = []
    count = 0

    for sf, file_path in iter_snapshot_files(snapshot):
        if _is_fixture_path(sf.rel_path):
            continue
        name = file_path.name
        if name == "pom.xml":
            build_files.append((file_path.parent, file_path, "maven"))
        elif name == "build.gradle":
            build_files.append((file_path.parent, file_path, "gradle"))
        elif name == "build.gradle.kts":
            build_files.append((file_path.parent, file_path, "gradle"))
        elif name.endswith(".java"):
            java_files.append((sf, file_path))
            count += 1

    # Parse build files into projects keyed by module root
    modules: dict[Path, JavaProject] = {}
    for root, bf, btype in sorted(build_files, key=lambda x: len(x[0].parts)):
        rel = root.relative_to(path).as_posix() or "."
        if btype == "maven":
            proj = parse_pom(bf)
        else:
            proj = parse_gradle(bf)
        proj.build_tool = btype
        proj.rel_path = rel
        modules[root] = proj
        ev.add(
            EvidenceKind.OBSERVED,
            f"Java build tool `{btype}` detected from `{bf.relative_to(path).as_posix()}`",
            source_path=bf.relative_to(path).as_posix(),
            analyzer="java",
        )
        for dep in proj.dependencies:
            ev.add(
                EvidenceKind.OBSERVED,
                f"Java dependency `{dep}` from `{bf.relative_to(path).as_posix()}`",
                source_path=bf.relative_to(path).as_posix(),
                analyzer="java",
            )

    if not modules:
        ev.add(
            EvidenceKind.UNKNOWN,
            "No `pom.xml` or `build.gradle` found; Java build metadata unavailable.",
            analyzer="java",
        )

    # Fallback project for orphan .java files
    if path not in modules:
        fallback = JavaProject()
        fallback.rel_path = "."
        modules[path] = fallback

    # Pass 2: assign each .java file to nearest module by path prefix
    for sf, file_path in java_files:
        file_dir = file_path.parent
        best_proj = modules[path]
        best_depth = -1
        for root, proj in modules.items():
            if root == path:
                continue
            try:
                file_dir.relative_to(root)
                depth = len(root.parts)
                if depth > best_depth:
                    best_proj = proj
                    best_depth = depth
            except ValueError:
                continue

        # Try javalang first
        backend = get_parser_backend("java")
        try:
            source = file_path.read_bytes()
        except OSError:
            parsed = None
        else:
            parsed = backend.parse(source, "java")
        if parsed and getattr(parsed, "parser_used", "none") != "none" and not getattr(parsed, "error", None):
            parser_used = parsed.parser_used
            for cls in parsed.classes:
                best_proj.classes.append(cls)
            for func in parsed.functions:
                best_proj.methods.append(func)
            for ann in parsed.dependencies:
                best_proj.annotations.append(ann)
            for imp in parsed.imports:
                if not imp.startswith("java.") and not imp.startswith("javax."):
                    best_proj.dependencies.append(imp)
            if parsed.entry_points and sf.rel_path not in best_proj.entry_points:
                best_proj.entry_points.append(sf.rel_path)
                ev.add(
                    EvidenceKind.OBSERVED,
                    f"Java entry point `{sf.rel_path}` (`public static void main`)",
                    source_path=sf.rel_path,
                    analyzer="java",
                )
        else:
            # Regex fallback
            src = safe_read_text(file_path, max_bytes=500_000)
            if src:
                if JAVA_MAIN_RE.search(src) and sf.rel_path not in best_proj.entry_points:
                    best_proj.entry_points.append(sf.rel_path)
                    ev.add(
                        EvidenceKind.OBSERVED,
                        f"Java entry point `{sf.rel_path}` (`public static void main`)",
                        source_path=sf.rel_path,
                        analyzer="java",
                    )
                pkg_match = JAVA_PACKAGE_RE.search(src)
                pkg = pkg_match.group(1) + "." if pkg_match else ""
                for m in JAVA_CLASS_RE.finditer(src):
                    class_name = m.group(3)
                    best_proj.classes.append(pkg + class_name)
                for m in JAVA_IMPORT_RE.finditer(src):
                    imp = m.group(1)
                    if not imp.startswith("java.") and not imp.startswith("javax."):
                        best_proj.dependencies.append(imp)
                for m in JAVA_METHOD_RE.finditer(src):
                    best_proj.methods.append(m.group(2))
                for m in JAVA_ANNOTATION_RE.finditer(src):
                    best_proj.annotations.append(m.group(1))
                for m in JAVA_EXTENDS_RE.finditer(src):
                    best_proj.class_hierarchy.append((pkg + m.group(0).split()[1], m.group(1)))
                for m in JAVA_IMPLEMENTS_RE.finditer(src):
                    cls = pkg + m.group(0).split()[1]
                    for iface in m.group(1).split(","):
                        best_proj.class_hierarchy.append((cls, iface.strip()))

    # Pass 3: build package graph and detect frameworks
    for proj in modules.values():
        all_imports = [d for d in proj.dependencies if "." in d]
        pkg_deps: set[str] = set()
        for imp in all_imports:
            pkg = ".".join(imp.split(".")[:-1]) if "." in imp else imp
            if pkg and pkg != proj.name:
                pkg_deps.add(pkg)
        for pkg in pkg_deps:
            proj.package_graph.append((proj.name or proj.rel_path or "?", pkg))
        # Framework detection
        dep_str = " ".join(proj.dependencies).lower()
        for fw_name, indicators in _JAVA_FRAMEWORKS.items():
            if any(ind in dep_str for ind in indicators):
                if fw_name not in proj.frameworks:
                    proj.frameworks.append(fw_name)
                    ev.add(
                        EvidenceKind.INFERRED,
                        f"Java framework `{fw_name}` inferred from dependencies",
                        analyzer="java",
                    )

    # Deduplicate and sort, drop empty fallback if real modules exist
    for proj in modules.values():
        proj.classes = sorted(set(proj.classes))
        proj.methods = sorted(set(proj.methods))
        proj.annotations = sorted(set(proj.annotations))
        proj.dependencies = sorted(set(proj.dependencies))
        proj.entry_points = sorted(set(proj.entry_points))
        proj.package_graph = sorted(set(proj.package_graph))

    result.java_projects = [
        p for p in modules.values() if p.rel_path != "." or p.classes or p.methods or p.dependencies
    ]
    result.analyzer_files_parsed += count

    total_classes = sum(len(p.classes) for p in result.java_projects)
    total_methods = sum(len(p.methods) for p in result.java_projects)
    total_frameworks = sum(len(p.frameworks) for p in result.java_projects)
    if total_classes or total_methods:
        ev.add(
            EvidenceKind.OBSERVED if parser_used != "regex" else EvidenceKind.INFERRED,
            f"Java symbols via {parser_used}: {total_classes} class(es), {total_methods} method(s), {total_frameworks} framework(s)",
            analyzer="java",
        )

    return result


register_analyzer("java", analyze_java)
register_analyzer_spec(
    AnalyzerSpec(
        project_type="java",
        display_name="Java",
        support_level="ast",
        parser="javalang",
        detects=["pom.xml", "build.gradle", "*.java"],
        limitations=["Regex fallback when javalang is unavailable"],
    )
)
