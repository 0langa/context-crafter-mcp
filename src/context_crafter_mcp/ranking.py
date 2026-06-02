"""Path classification and importance scoring for repo signal ranking."""

from __future__ import annotations

from enum import Enum
from pathlib import Path


class PathCategory(str, Enum):
    """Classification of a file or directory path."""

    PRODUCT = "product"
    TOOLING = "tooling"
    VENDOR = "vendor"
    GENERATED = "generated"
    FIXTURE = "fixture"
    TEST = "test"
    DOCS = "docs"
    UNKNOWN = "unknown"


# Segments that strongly indicate vendor / third-party / generated material
VENDOR_SEGMENTS: set[str] = {
    "vendor",
    "vendors",
    "node_modules",
    "third_party",
    "thirdparty",
    "3rdparty",
    "aa_vendor_mirror",
    "vendor_mirror",
    "mirrors",
    "mirror",
    ".next",
    ".turbo",
    ".cache",
    "coverage",
    "tmp",
    "temp",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}

# Segments that indicate development / CI / deployment tooling
TOOLING_SEGMENTS: set[str] = {
    "tools",
    "tooling",
    "scripts",
    ".github",
    "ci",
    "cd",
    ".husky",
    "lint-staged",
    "docker",
    "infra",
    "terraform",
    "ansible",
    "k8s",
    "kubernetes",
    "deploy",
    "deployment",
    "provisioning",
    "setup",
    "install",
}

# Segments that indicate product / runtime / application code
PRODUCT_SEGMENTS: set[str] = {
    "src",
    "lib",
    "source",
    "sources",
    "app",
    "apps",
    "services",
    "service",
    "packages",
    "pkg",
    "core",
    "cmd",
    "main",
    "server",
    "api",
    "worker",
    "ingest",
    "indexer",
    "web",
    "frontend",
    "backend",
    "client",
    "internal",
    "domain",
    "runtime",
    "product",
    "crates",
    "components",
    "modules",
    "projects",
    "microservices",
    "gateways",
    "handlers",
    "controllers",
    "repositories",
    "entities",
    "usecases",
    "interactors",
    "presenters",
}

TEST_SEGMENTS: set[str] = {
    "test",
    "tests",
    "spec",
    "specs",
    "__tests__",
    "testing",
    "integration_tests",
    "e2e",
    "unit_tests",
}

DOCS_SEGMENTS: set[str] = {
    "docs",
    "doc",
    "documentation",
    "wiki",
    "guides",
}


# Root filenames that are typically tooling-only manifests
TOOLING_ROOT_FILES: set[str] = {
    ".eslintrc",
    ".eslintrc.json",
    ".eslintrc.js",
    ".prettierrc",
    ".prettierrc.json",
    ".prettierrc.js",
    ".stylelintrc",
    "jest.config.js",
    "jest.config.ts",
    "vitest.config.js",
    "vitest.config.ts",
    "vite.config.js",
    "vite.config.ts",
    "webpack.config.js",
    "rollup.config.js",
    "playwright.config.ts",
    "playwright.config.js",
    "tailwind.config.js",
    "tailwind.config.ts",
    "postcss.config.js",
    ".commitlintrc",
    ".lintstagedrc",
    ".editorconfig",
    ".gitignore",
    ".gitattributes",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "makefile",
    "gnumakefile",
    "cmakelists.txt",
}


def classify_path(rel_path: str) -> PathCategory:
    """Classify a relative path into a signal category."""
    lower = rel_path.lower()
    parts = Path(lower).parts
    name = Path(lower).name

    # Fixture check — explicit policy:
    # - fixtures/ under test/demo/example → FIXTURE (untrustworthy)
    # - fixtures/ under product dirs (src/fixtures, lib/fixtures) → PRODUCT (trustworthy)
    # - root-level fixtures/ → falls through to later rules (typically UNKNOWN)
    # This policy is intentional: product fixture dirs are treated as primary surface.
    if any(p in ("fixtures", "fixture") for p in parts):
        if any(p in TEST_SEGMENTS for p in parts) or any(p in ("examples", "demo", "demo-repo") for p in parts):
            return PathCategory.FIXTURE
        if any(p in PRODUCT_SEGMENTS for p in parts):
            return PathCategory.PRODUCT
        # Ambiguous context (e.g., root-level fixtures/) → fall through

    # Vendor / generated
    if any(p in VENDOR_SEGMENTS for p in parts):
        return PathCategory.VENDOR

    # Generated build artifacts (exact segment names)
    if any(p in ("generated", "gen", "autogen", "dist", "build", "out", "output") for p in parts):
        return PathCategory.GENERATED

    # Test
    if any(p in TEST_SEGMENTS for p in parts):
        return PathCategory.TEST

    # Tooling directories
    if any(p in TOOLING_SEGMENTS for p in parts):
        return PathCategory.TOOLING

    # Docs
    if any(p in DOCS_SEGMENTS for p in parts):
        return PathCategory.DOCS

    # Product directories
    if any(p in PRODUCT_SEGMENTS for p in parts):
        return PathCategory.PRODUCT

    # Root-level tooling config files
    if "/" not in lower and name in TOOLING_ROOT_FILES:
        return PathCategory.TOOLING

    return PathCategory.UNKNOWN


def score_path(
    rel_path: str,
    category: PathCategory | None = None,
    has_marker: bool = False,
    is_entrypoint: bool = False,
) -> float:
    """Return an importance score for a path. Higher = more significant."""
    cat = category or classify_path(rel_path)
    score = 0.0

    if cat == PathCategory.PRODUCT:
        score = 10.0
    elif cat == PathCategory.UNKNOWN:
        score = 5.0
    elif cat == PathCategory.TOOLING:
        score = 2.0
    elif cat == PathCategory.TEST:
        score = 1.0
    elif cat == PathCategory.DOCS:
        score = 1.0
    elif cat == PathCategory.VENDOR:
        score = -5.0
    elif cat == PathCategory.GENERATED:
        score = -3.0
    elif cat == PathCategory.FIXTURE:
        score = -10.0

    # Depth bonus for product/unknown (deeper paths often mean real application code)
    depth = len(Path(rel_path).parts)
    if cat in (PathCategory.PRODUCT, PathCategory.UNKNOWN):
        score += depth * 0.5

    if has_marker:
        score += 5.0

    if is_entrypoint:
        score += 8.0

    return score


def is_vendor_path(rel_path: str) -> bool:
    """Quick check: is this path inside a vendor/generated zone?"""
    return classify_path(rel_path) in (PathCategory.VENDOR, PathCategory.GENERATED, PathCategory.FIXTURE)


def is_likely_tooling_path(rel_path: str) -> bool:
    """Quick check: is this path likely dev/tooling material?"""
    return classify_path(rel_path) == PathCategory.TOOLING


def is_likely_product_path(rel_path: str) -> bool:
    """Quick check: is this path likely product/runtime code?"""
    return classify_path(rel_path) == PathCategory.PRODUCT


def is_primary_surface_path(rel_path: str) -> bool:
    """Check if path is product or unknown (i.e., not vendor/generated/fixture/test/docs/tooling)."""
    cat = classify_path(rel_path)
    return cat not in (
        PathCategory.VENDOR,
        PathCategory.GENERATED,
        PathCategory.FIXTURE,
        PathCategory.TEST,
        PathCategory.DOCS,
        PathCategory.TOOLING,
    )


def rank_primary_surface(paths: list[str], *, is_entrypoint: bool = False) -> list[str]:
    """Filter out vendor/tooling/test/docs/fixture/generated paths, then sort by importance score descending."""
    filtered = [p for p in paths if is_primary_surface_path(p)]
    scored = [(p, score_path(p, is_entrypoint=is_entrypoint)) for p in filtered]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [p for p, _ in scored]
