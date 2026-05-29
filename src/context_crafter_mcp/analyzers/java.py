"""Java analyzer with javalang AST and regex fallback."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from context_crafter_mcp.analyzers import register_analyzer, register_analyzer_spec
from context_crafter_mcp.detectors import _is_fixture_path
from context_crafter_mcp.filesystem import safe_read_text, safe_scan, validate_repo_path
from context_crafter_mcp.models import AnalysisResult, AnalyzerSpec, EvidenceKind, JavaProject, ScanConfig
from context_crafter_mcp.parsers import parse_java

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
    ev = result.evidence_set
    java_proj = JavaProject()
    classes: list[str] = []
    count = 0
    parser_used = "regex"

    pom = path / "pom.xml"
    gradle = path / "build.gradle"
    gradle_kts = path / "build.gradle.kts"

    if pom.exists():
        java_proj = parse_pom(pom)
        java_proj.build_tool = "maven"
        ev.add(
            EvidenceKind.OBSERVED,
            "Java build tool `maven` detected from `pom.xml`",
            source_path="pom.xml",
            analyzer="java",
        )
        for dep in java_proj.dependencies:
            ev.add(
                EvidenceKind.OBSERVED,
                f"Java dependency `{dep}` from `pom.xml`",
                source_path="pom.xml",
                analyzer="java",
            )
    elif gradle.exists():
        java_proj = parse_gradle(gradle)
        java_proj.build_tool = "gradle"
        ev.add(
            EvidenceKind.OBSERVED,
            "Java build tool `gradle` detected from `build.gradle`",
            source_path="build.gradle",
            analyzer="java",
        )
        for dep in java_proj.dependencies:
            ev.add(
                EvidenceKind.OBSERVED,
                f"Java dependency `{dep}` from `build.gradle`",
                source_path="build.gradle",
                analyzer="java",
            )
    elif gradle_kts.exists():
        java_proj = parse_gradle(gradle_kts)
        java_proj.build_tool = "gradle"
        ev.add(
            EvidenceKind.OBSERVED,
            "Java build tool `gradle` detected from `build.gradle.kts`",
            source_path="build.gradle.kts",
            analyzer="java",
        )
        for dep in java_proj.dependencies:
            ev.add(
                EvidenceKind.OBSERVED,
                f"Java dependency `{dep}` from `build.gradle.kts`",
                source_path="build.gradle.kts",
                analyzer="java",
            )
    else:
        ev.add(
            EvidenceKind.UNKNOWN,
            "No `pom.xml` or `build.gradle` found; Java build metadata unavailable.",
            analyzer="java",
        )

    for fi in safe_scan(path, max_depth=cfg.max_depth + 2, max_files_per_dir=cfg.max_files_per_dir):
        if fi.is_dir:
            continue
        if _is_fixture_path(fi.rel_path):
            continue
        name = fi.path.name
        if name.endswith(".java"):
            count += 1
            classes.append(fi.rel_path)

            # Try javalang first
            parsed = parse_java(fi.path)
            if parsed and parsed.parser_used != "none" and not parsed.error:
                parser_used = parsed.parser_used
                for cls in parsed.classes:
                    java_proj.classes.append(cls)
                for func in parsed.functions:
                    java_proj.methods.append(func)
                for ann in parsed.dependencies:
                    java_proj.annotations.append(ann)
                for imp in parsed.imports:
                    if not imp.startswith("java.") and not imp.startswith("javax."):
                        java_proj.dependencies.append(imp)
                if parsed.entry_points:
                    java_proj.entry_points.extend(parsed.entry_points)
            else:
                # Regex fallback
                src = safe_read_text(fi.path, max_bytes=500_000)
                if src:
                    if JAVA_MAIN_RE.search(src):
                        java_proj.entry_points.append(fi.rel_path)
                        ev.add(
                            EvidenceKind.OBSERVED,
                            f"Java entry point `{fi.rel_path}` (`public static void main`)",
                            source_path=fi.rel_path,
                            analyzer="java",
                        )
                    for m in JAVA_CLASS_RE.finditer(src):
                        class_name = m.group(3)
                        pkg_match = JAVA_PACKAGE_RE.search(src)
                        pkg = pkg_match.group(1) + "." if pkg_match else ""
                        java_proj.classes.append(pkg + class_name)
                    for m in JAVA_IMPORT_RE.finditer(src):
                        imp = m.group(1)
                        if not imp.startswith("java.") and not imp.startswith("javax."):
                            java_proj.dependencies.append(imp)
                    for m in JAVA_METHOD_RE.finditer(src):
                        java_proj.methods.append(m.group(2))
                    for m in JAVA_ANNOTATION_RE.finditer(src):
                        java_proj.annotations.append(m.group(1))

    java_proj.classes = sorted(set(java_proj.classes))
    java_proj.methods = sorted(set(java_proj.methods))
    java_proj.annotations = sorted(set(java_proj.annotations))
    java_proj.dependencies = sorted(set(java_proj.dependencies))
    result.java_projects = [java_proj]
    result.files_scanned += count

    if java_proj.classes or java_proj.methods:
        ev.add(
            EvidenceKind.OBSERVED if parser_used != "regex" else EvidenceKind.INFERRED,
            f"Java symbols via {parser_used}: {len(java_proj.classes)} class(es), {len(java_proj.methods)} method(s)",
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
