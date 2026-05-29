"""Tests for the evidence model."""

from __future__ import annotations

from context_crafter_mcp.models import (
    AnalysisResult,
    Confidence,
    DetectResult,
    Evidence,
    EvidenceKind,
    EvidenceSet,
)


def test_evidence_kind_values() -> None:
    assert EvidenceKind.OBSERVED.value == "observed"
    assert EvidenceKind.INFERRED.value == "inferred"
    assert EvidenceKind.UNKNOWN.value == "unknown"
    assert EvidenceKind.UNSUPPORTED.value == "unsupported"
    assert EvidenceKind.ERROR.value == "error"


def test_evidence_to_dict() -> None:
    ev = Evidence(
        kind=EvidenceKind.OBSERVED,
        message="found pyproject.toml",
        source_path="pyproject.toml",
        analyzer="python",
    )
    d = ev.to_dict()
    assert d["kind"] == "observed"
    assert d["message"] == "found pyproject.toml"
    assert d["source_path"] == "pyproject.toml"
    assert d["analyzer"] == "python"


def test_evidence_set_add_and_query() -> None:
    es = EvidenceSet()
    es.add(EvidenceKind.OBSERVED, "observed msg", source_path="a.py", analyzer="python")
    es.add(EvidenceKind.INFERRED, "inferred msg", analyzer="generic")
    es.add(EvidenceKind.UNKNOWN, "unknown msg", analyzer="node")
    es.add(EvidenceKind.UNSUPPORTED, "unsupported msg", analyzer="java")
    es.add(EvidenceKind.ERROR, "error msg", source_path="b.py", analyzer="python")

    assert len(es.by_kind(EvidenceKind.OBSERVED)) == 1
    assert len(es.by_kind("observed")) == 1
    assert len(es.by_analyzer("python")) == 2
    assert len(es.warnings()) == 3  # unknown, unsupported, error


def test_evidence_set_bool() -> None:
    empty = EvidenceSet()
    assert not empty
    nonempty = EvidenceSet()
    nonempty.add(EvidenceKind.OBSERVED, "msg")
    assert nonempty


def test_detect_result_includes_evidence_details() -> None:
    es = EvidenceSet()
    es.add(EvidenceKind.OBSERVED, "marker found", source_path="pyproject.toml", analyzer="detectors")
    dr = DetectResult(repo_path="/tmp", exists=True, project_types=["python"], evidence_set=es)
    d = dr.to_dict()
    assert "evidence_details" in d
    assert len(d["evidence_details"]) == 1
    assert d["evidence_details"][0]["kind"] == "observed"


def test_analysis_result_carries_evidence() -> None:
    ar = AnalysisResult(repo_path="/tmp")
    ar.evidence_set.add(EvidenceKind.OBSERVED, "scan done", analyzer="generic")
    assert len(ar.evidence_set.by_kind(EvidenceKind.OBSERVED)) == 1


def test_evidence_confidence_defaults() -> None:
    es = EvidenceSet()
    es.add(EvidenceKind.OBSERVED, "observed msg")
    es.add(EvidenceKind.INFERRED, "inferred msg")
    es.add(EvidenceKind.UNKNOWN, "unknown msg")
    es.add(EvidenceKind.ERROR, "error msg")

    assert es.by_kind(EvidenceKind.OBSERVED)[0].confidence == Confidence.HIGH
    assert es.by_kind(EvidenceKind.INFERRED)[0].confidence == Confidence.MEDIUM
    assert es.by_kind(EvidenceKind.UNKNOWN)[0].confidence == Confidence.LOW
    assert es.by_kind(EvidenceKind.ERROR)[0].confidence == Confidence.HIGH


def test_evidence_confidence_override() -> None:
    es = EvidenceSet()
    es.add(EvidenceKind.OBSERVED, "msg", confidence=Confidence.LOW)
    assert es.items[0].confidence == Confidence.LOW


def test_evidence_to_dict_includes_confidence() -> None:
    ev = Evidence(kind=EvidenceKind.OBSERVED, message="m", confidence=Confidence.HIGH)
    assert ev.to_dict()["confidence"] == "high"


def test_evidence_set_by_confidence() -> None:
    es = EvidenceSet()
    es.add(EvidenceKind.OBSERVED, "high msg")
    es.add(EvidenceKind.UNKNOWN, "low msg")
    assert len(es.by_confidence(Confidence.HIGH)) == 1
    assert len(es.by_confidence("low")) == 1


def test_evidence_set_verify() -> None:
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as td:
        Path(td, "exists.py").write_text("print(1)\n")
        es = EvidenceSet()
        es.add(EvidenceKind.OBSERVED, "found", source_path="exists.py")
        es.add(EvidenceKind.OBSERVED, "missing", source_path="nope.py")
        missing = es.verify(td)
        assert len(missing) == 1
        assert missing[0].source_path == "nope.py"
