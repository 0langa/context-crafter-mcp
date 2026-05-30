"""Tests for path classification and ranking."""

from __future__ import annotations


from context_crafter_mcp.ranking import (
    classify_path,
    is_likely_product_path,
    is_primary_surface_path,
    is_vendor_path,
    rank_primary_surface,
    score_path,
    PathCategory,
)


class TestClassifyPath:
    def test_vendor_mirror_classified_vendor(self) -> None:
        assert classify_path("aa_vendor_mirror/sdk001/shim.js") == PathCategory.VENDOR

    def test_node_modules_classified_vendor(self) -> None:
        assert classify_path("node_modules/lodash/index.js") == PathCategory.VENDOR

    def test_dist_classified_generated(self) -> None:
        assert classify_path("dist/bundle.js") == PathCategory.GENERATED

    def test_src_classified_product(self) -> None:
        assert classify_path("src/app/main.py") == PathCategory.PRODUCT

    def test_apps_classified_product(self) -> None:
        assert classify_path("apps/dashboard/web/src/index.ts") == PathCategory.PRODUCT

    def test_services_classified_product(self) -> None:
        assert classify_path("services/api/python/src/server.py") == PathCategory.PRODUCT

    def test_tools_classified_tooling(self) -> None:
        assert classify_path("scripts/build.js") == PathCategory.TOOLING

    def test_github_classified_tooling(self) -> None:
        assert classify_path(".github/workflows/ci.yml") == PathCategory.TOOLING

    def test_tests_classified_test(self) -> None:
        assert classify_path("tests/test_api.py") == PathCategory.TEST

    def test_docs_classified_docs(self) -> None:
        assert classify_path("docs/guide.md") == PathCategory.DOCS

    def test_fixture_classified_fixture(self) -> None:
        assert classify_path("tests/fixtures/sample.json") == PathCategory.FIXTURE

    def test_fixture_under_src_classified_product(self) -> None:
        assert classify_path("src/fixtures/data.py") == PathCategory.PRODUCT

    def test_fixture_under_lib_classified_product(self) -> None:
        assert classify_path("lib/fixtures/schema.py") == PathCategory.PRODUCT

    def test_fixture_under_vendor_classified_vendor(self) -> None:
        assert classify_path("vendor/fixtures/lib.py") == PathCategory.VENDOR

    def test_root_fixture_falls_through(self) -> None:
        assert classify_path("fixtures/data.json") == PathCategory.UNKNOWN

    def test_unknown_for_random(self) -> None:
        assert classify_path("foo/bar/baz.py") == PathCategory.UNKNOWN

    def test_root_config_tooling(self) -> None:
        assert classify_path("jest.config.js") == PathCategory.TOOLING
        assert classify_path(".eslintrc.json") == PathCategory.TOOLING
        assert classify_path("Dockerfile") == PathCategory.TOOLING


class TestIsVendorPath:
    def test_true_for_vendor(self) -> None:
        assert is_vendor_path("vendor/lib.js")

    def test_false_for_product(self) -> None:
        assert not is_vendor_path("src/lib.js")


class TestScorePath:
    def test_product_scores_higher_than_tooling(self) -> None:
        assert score_path("src/app.py", category=PathCategory.PRODUCT) > score_path(
            "scripts/build.py", category=PathCategory.TOOLING
        )

    def test_vendor_is_negative(self) -> None:
        assert score_path("vendor/lib.js", category=PathCategory.VENDOR) < 0

    def test_fixture_is_very_negative(self) -> None:
        assert score_path("tests/fixtures/x.py", category=PathCategory.FIXTURE) < score_path(
            "vendor/x.py", category=PathCategory.VENDOR
        )

    def test_depth_bonus_for_product(self) -> None:
        shallow = score_path("src/app.py", category=PathCategory.PRODUCT)
        deep = score_path("services/api/src/app.py", category=PathCategory.PRODUCT)
        assert deep > shallow

    def test_marker_boost(self) -> None:
        base = score_path("src/app.py", category=PathCategory.PRODUCT)
        boosted = score_path("src/app.py", category=PathCategory.PRODUCT, has_marker=True)
        assert boosted > base

    def test_entrypoint_boost(self) -> None:
        base = score_path("src/app.py", category=PathCategory.PRODUCT)
        boosted = score_path("src/app.py", category=PathCategory.PRODUCT, is_entrypoint=True)
        assert boosted > base


class TestProductPath:
    def test_crates_is_product(self) -> None:
        assert is_likely_product_path("crates/indexer/src/main.rs")


class TestIsPrimarySurfacePath:
    def test_true_for_product(self) -> None:
        assert is_primary_surface_path("src/app.py")

    def test_false_for_vendor(self) -> None:
        assert not is_primary_surface_path("node_modules/lodash/index.js")

    def test_false_for_fixture(self) -> None:
        assert not is_primary_surface_path("tests/fixtures/sample.json")

    def test_false_for_docs(self) -> None:
        assert not is_primary_surface_path("docs/guide.md")

    def test_false_for_tooling(self) -> None:
        assert not is_primary_surface_path("scripts/build.js")

    def test_false_for_generated(self) -> None:
        assert not is_primary_surface_path("dist/bundle.js")


class TestRankPrimarySurface:
    def test_filters_vendor(self) -> None:
        paths = ["src/app.py", "vendor/lib.js", "node_modules/x/index.js"]
        ranked = rank_primary_surface(paths)
        assert ranked == ["src/app.py"]

    def test_sorts_by_score(self) -> None:
        paths = ["src/utils.py", "src/app.py", "services/api/main.py"]
        ranked = rank_primary_surface(paths, is_entrypoint=True)
        assert ranked[0] == "services/api/main.py"

    def test_empty_when_all_filtered(self) -> None:
        assert rank_primary_surface(["vendor/a.js", "node_modules/b.js"]) == []
