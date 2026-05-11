"""Tests for scan config validation."""

from __future__ import annotations

import pytest

from repo_docs_mcp.models import ScanConfig


def test_scan_config_defaults() -> None:
    cfg = ScanConfig()
    assert cfg.max_depth == 4
    assert cfg.max_files_per_dir == 80


def test_scan_config_custom() -> None:
    cfg = ScanConfig(max_depth=6, max_files_per_dir=200)
    assert cfg.max_depth == 6
    assert cfg.max_files_per_dir == 200


def test_scan_config_bounds() -> None:
    with pytest.raises(ValueError):
        ScanConfig(max_depth=0)
    with pytest.raises(ValueError):
        ScanConfig(max_depth=25)
    with pytest.raises(ValueError):
        ScanConfig(max_files_per_dir=0)
    with pytest.raises(ValueError):
        ScanConfig(max_files_per_dir=6000)
