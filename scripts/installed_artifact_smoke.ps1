param(
    [string]$Version = "",
    [string]$Python = "3.12",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

function Get-ProjectVersion {
    $pyproject = Get-Content -Path "pyproject.toml" -Raw
    $match = [regex]::Match($pyproject, '(?m)^version\s*=\s*"([^"]+)"')
    if (-not $match.Success) {
        throw "Could not read project version from pyproject.toml"
    }
    return $match.Groups[1].Value
}

function Invoke-SmokeStep {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    Write-Host "==> $Name"
    $global:LASTEXITCODE = 0
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Installed artifact smoke failed at: $Name"
    }
}

if (-not $Version) {
    $Version = Get-ProjectVersion
}

if (-not $SkipBuild) {
    Invoke-SmokeStep "build artifacts" { uv build }
}

$artifacts = @(
    "dist\context_crafter_mcp-$Version-py3-none-any.whl",
    "dist\context_crafter_mcp-$Version.tar.gz"
)

foreach ($artifact in $artifacts) {
    if (-not (Test-Path $artifact)) {
        throw "Expected artifact missing: $artifact"
    }
}

foreach ($artifact in $artifacts) {
    $resolvedArtifact = (Resolve-Path $artifact).Path
    $artifactName = Split-Path $resolvedArtifact -Leaf
    $venv = Join-Path ([System.IO.Path]::GetTempPath()) ("ccmcp-artifact-smoke-" + [System.Guid]::NewGuid().ToString("N"))

    try {
        Write-Host "==> smoke artifact: $artifactName"
        Invoke-SmokeStep "create venv" { uv venv $venv --python $Python }
        $venvPython = Join-Path $venv "Scripts\python.exe"
        $cli = Join-Path $venv "Scripts\context-crafter-mcp.exe"

        Invoke-SmokeStep "install $artifactName" { uv pip install --python $venvPython $resolvedArtifact }
        Invoke-SmokeStep "help" { & $cli --help | Out-Host }
        Invoke-SmokeStep "version" {
            $actual = & $cli version
            Write-Host $actual
            if ($actual.Trim() -ne $Version) {
                throw "Version mismatch: expected $Version, got $actual"
            }
        }
        Invoke-SmokeStep "doctor" { & $cli doctor }
        Invoke-SmokeStep "detect" { & $cli detect . --json }
        Invoke-SmokeStep "self-test" { & $cli self-test . }
        Invoke-SmokeStep "generate" { & $cli generate . --output docs/generated --profile standard --json }
        Invoke-SmokeStep "validate" { & $cli validate docs/generated --repo . --json }
    }
    finally {
        if (Test-Path $venv) {
            Remove-Item -LiteralPath $venv -Recurse -Force
        }
    }
}

Write-Host "Installed artifact smoke passed for version $Version."
