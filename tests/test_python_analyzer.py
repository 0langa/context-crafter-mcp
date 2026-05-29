"""Tests for Python analyzer."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.analyzers.python import analyze_python


def test_python_basic() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "main.py").write_text(
            "import os\n"
            "from collections import abc\n"
            "class Foo:\n    pass\n"
            "def bar():\n    pass\n"
            "async def baz():\n    pass\n"
            'if __name__ == "__main__":\n    bar()\n'
        )
        result = analyze_python(td)
        assert result.python_modules
        mod = result.python_modules[0]
        assert "os" in mod.imports
        assert "collections" in mod.imports
        assert "Foo" in mod.classes
        assert "bar" in mod.functions
        assert "baz" in mod.async_functions
        assert mod.is_entry_point


def test_python_console_scripts() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text('[project]\nname = "x"\nscripts = { cli = "app:main" }\n')
        result = analyze_python(td)
        assert any("cli" in ep for ep in result.likely_entry_points)


def test_python_requirements_txt() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "main.py").write_text("import requests\n")
        (root / "requirements.txt").write_text(
            "requests>=2.0\nnumpy==1.24\n# comment\n-r other.txt\npytest>=7.0; python_version>='3.9'\nblack[extra]\n"
        )
        result = analyze_python(td)
        assert "requests" in result.python_dependencies
        assert "numpy" in result.python_dependencies
        assert "pytest" in result.python_dependencies
        assert "black" in result.python_dependencies
        assert "other" not in result.python_dependencies
        ev_msgs = [e.message for e in result.evidence_set.items]
        assert any("requirements.txt" in m for m in ev_msgs)


def test_python_setup_py_deps() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "main.py").write_text("import flask\n")
        (root / "setup.py").write_text(
            "from setuptools import setup\n"
            "setup(\n"
            '    name="demo",\n'
            '    install_requires=["flask>=2.0", "click"],\n'
            "    extras_require={\n"
            '        "dev": ["pytest>=7.0", "black"],\n'
            '        "docs": ["sphinx"],\n'
            "    },\n"
            ")\n"
        )
        result = analyze_python(td)
        assert "flask" in result.python_dependencies
        assert "click" in result.python_dependencies
        assert "pytest" in result.python_dev_dependencies
        assert "black" in result.python_dev_dependencies
        assert "sphinx" in result.python_dev_dependencies
        ev_msgs = [e.message for e in result.evidence_set.items]
        assert any("setup.py" in m for m in ev_msgs)


def test_python_pipfile_deps() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "main.py").write_text("import django\n")
        (root / "Pipfile").write_text(
            '[packages]\ndjango = "*"\ncelery = ">=5.0"\n\n[dev-packages]\npytest = "*"\nmypy = "*"\n'
        )
        result = analyze_python(td)
        assert "django" in result.python_dependencies
        assert "celery" in result.python_dependencies
        assert "pytest" in result.python_dev_dependencies
        assert "mypy" in result.python_dev_dependencies
        ev_msgs = [e.message for e in result.evidence_set.items]
        assert any("Pipfile" in m for m in ev_msgs)


def test_python_merged_deps() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "main.py").write_text("import os\n")
        (root / "pyproject.toml").write_text('[project]\nname = "demo"\ndependencies = ["requests>=2.0"]\n')
        (root / "requirements.txt").write_text("requests>=2.0\nnumpy\n")
        result = analyze_python(td)
        assert "requests" in result.python_dependencies
        assert "numpy" in result.python_dependencies
        # Should deduplicate
        assert result.python_dependencies.count("requests") == 1
        ev_msgs = [e.message for e in result.evidence_set.items]
        assert any("pyproject.toml" in m for m in ev_msgs)
        assert any("requirements.txt" in m for m in ev_msgs)


def test_python_malformed_pipfile() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "main.py").write_text("import os\n")
        (root / "Pipfile").write_text("this is not toml at all\n")
        result = analyze_python(td)
        ev_errors = [e for e in result.evidence_set.items if e.kind == "error"]
        assert any("Pipfile parse error" in e.message for e in ev_errors)


def test_python_setup_py_regex_timeout_safety() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "main.py").write_text("import os\n")
        # Write a large but benign setup.py to ensure regex doesn't hang
        large = "from setuptools import setup\n" + "\n".join(f'x{i} = "{"a" * 100}"' for i in range(500))
        large += '\nsetup(\n    install_requires=["requests"],\n)\n'
        (root / "setup.py").write_text(large)
        result = analyze_python(td)
        assert "requests" in result.python_dependencies
