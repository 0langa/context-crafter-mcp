"""Tests for Java analyzer."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.analyzers.java import analyze_java


def test_java_maven() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pom.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<project xmlns="http://maven.apache.org/POM/4.0.0">\n'
            "  <artifactId>myapp</artifactId>\n"
            "  <dependencies>\n"
            "    <dependency>\n"
            "      <groupId>org.junit</groupId>\n"
            "      <artifactId>junit</artifactId>\n"
            "    </dependency>\n"
            "  </dependencies>\n"
            "</project>\n"
        )
        (root / "src" / "main" / "java" / "com" / "example" / "App.java").parent.mkdir(parents=True)
        (root / "src" / "main" / "java" / "com" / "example" / "App.java").write_text(
            "package com.example;\n"
            "@Entity\n"
            "public class App {\n"
            "  public static void main(String[] args) { }\n"
            '  public String getName() { return "app"; }\n'
            "}\n"
        )
        result = analyze_java(td)
        assert result.java_projects
        proj = result.java_projects[0]
        assert proj.name == "myapp"
        assert proj.build_tool == "maven"
        assert any("org.junit:junit" in d for d in proj.dependencies)
        assert len(proj.classes) == 1
        assert any("App.java" in ep for ep in proj.entry_points)
        assert "getName" in proj.methods
        assert "Entity" in proj.annotations


def test_java_gradle() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "build.gradle").write_text(
            'rootProject.name = "mygradle"\nimplementation "com.google.guava:guava:31.0-jre"\n'
        )
        (root / "src" / "main" / "java" / "Foo.java").parent.mkdir(parents=True)
        (root / "src" / "main" / "java" / "Foo.java").write_text("public class Foo { }\n")
        result = analyze_java(td)
        assert result.java_projects
        proj = result.java_projects[0]
        assert proj.name == "mygradle"
        assert proj.build_tool == "gradle"
