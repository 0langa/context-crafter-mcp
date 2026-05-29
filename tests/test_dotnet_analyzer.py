"""Tests for .NET analyzer features."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.analyzers.dotnet import analyze_dotnet


def test_dotnet_project_refs_and_frameworks() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "MyApp.csproj").write_text(
            '<Project Sdk="Microsoft.NET.Sdk">\n'
            "  <PropertyGroup>\n"
            "    <TargetFramework>net8.0</TargetFramework>\n"
            "  </PropertyGroup>\n"
            "  <ItemGroup>\n"
            '    <PackageReference Include="Newtonsoft.Json" Version="13.0.1" />\n'
            '    <ProjectReference Include="..\\Lib\\Lib.csproj" />\n'
            "  </ItemGroup>\n"
            "</Project>\n"
        )
        (root / "MyApp.sln").write_text(
            'Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "MyApp", "MyApp.csproj", "{GUID}"\nEndProject\n'
        )
        result = analyze_dotnet(td)
        assert result.dotnet_projects
        proj = result.dotnet_projects[0]
        assert "net8.0" in proj.target_frameworks
        assert "Newtonsoft.Json" in proj.package_refs
        assert any("Lib.csproj" in ref for ref in proj.project_refs)
        assert result.dotnet_solutions
        assert result.dotnet_solutions[0].name == "MyApp"


def test_dotnet_parse_error_collected() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "Bad.csproj").write_text("<Project><NotClosed>\n")
        result = analyze_dotnet(td)
        assert any("Parse error" in str(p.target_frameworks) for p in result.dotnet_projects)
