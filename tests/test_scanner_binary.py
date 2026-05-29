"""Tests for scanner binary detection."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.scanner import _guess_is_text, _has_binary_magic


def test_has_binary_magic_png() -> None:
    assert _has_binary_magic(b"\x89PNG\r\n\x1a\n")


def test_has_binary_magic_elf() -> None:
    assert _has_binary_magic(b"\x7fELF")


def test_has_binary_magic_pdf() -> None:
    assert _has_binary_magic(b"%PDF-1.4")


def test_no_binary_magic_text() -> None:
    assert not _has_binary_magic(b"hello world")


def test_guess_is_text_with_magic() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td, "unknown_file")
        path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00")
        assert _guess_is_text(path) is False


def test_guess_is_text_plain() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td, "readme")
        path.write_text("hello world", encoding="utf-8")
        assert _guess_is_text(path) is True
