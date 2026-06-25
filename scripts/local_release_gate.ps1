param(
    [string]$Python = ".\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

function Invoke-GateStep {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    Write-Host "==> $Name"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Local release gate failed at: $Name"
        exit $LASTEXITCODE
    }
}

Invoke-GateStep "project-state validation" { python .\scripts\validate_project_state.py }
Invoke-GateStep "release-doc validation" { python .\scripts\validate_release_docs.py }
Invoke-GateStep "ruff" { uv run ruff check . }
Invoke-GateStep "mypy" { & $Python -m mypy src }
Invoke-GateStep "pytest" { & $Python -m pytest -q }
Invoke-GateStep "doctor" { uv run context-crafter-mcp doctor }
Invoke-GateStep "public surface validation" { & $Python .\scripts\validate_public_surface.py }
Invoke-GateStep "self-test" { uv run context-crafter-mcp self-test . }
Invoke-GateStep "generate docs/generated" {
    uv run context-crafter-mcp generate . --output docs/generated --profile standard --json
}
Invoke-GateStep "validate docs/generated" {
    uv run context-crafter-mcp validate docs/generated --repo . --json
}

Write-Host "Local release gate passed."
