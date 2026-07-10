$ErrorActionPreference = "Stop"

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,

        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$CommandArgs
    )

    & $Command @CommandArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Native command failed with exit code ${LASTEXITCODE}: $Command $($CommandArgs -join ' ')"
    }
}

Invoke-NativeCommand python -m compileall -q src
Invoke-NativeCommand python -m pytest -q

$Wheels = @(Get-ChildItem -Path dist -Filter "ixunfei_docx_reader-*.whl" -File)
if ($Wheels.Count -ne 1) {
    throw "Expected exactly one wheel under dist/, found $($Wheels.Count)"
}
$Wheel = $Wheels[0]

$SmokeRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("ixfdoc-smoke-" + [guid]::NewGuid())
$VenvDir = Join-Path $SmokeRoot "venv"
$SmokeHome = Join-Path $SmokeRoot "home"
New-Item -ItemType Directory -Path $SmokeHome -Force | Out-Null

$OriginalHome = $env:HOME
$OriginalUserProfile = $env:USERPROFILE

try {
    Invoke-NativeCommand python -m venv --system-site-packages $VenvDir

    $VenvPython = Join-Path $VenvDir "Scripts/python.exe"
    $VenvIxfdoc = Join-Path $VenvDir "Scripts/ixfdoc.exe"
    Invoke-NativeCommand $VenvPython -m pip install --no-deps $Wheel.FullName

    $env:HOME = $SmokeHome
    $env:USERPROFILE = $SmokeHome

    $PackageVersion = & $VenvPython -c "import importlib.metadata; print(importlib.metadata.version('ixunfei-docx-reader'))"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to read installed package metadata"
    }
    $CliVersion = & $VenvIxfdoc --version
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to run installed ixfdoc"
    }
    if ($CliVersion -ne "ixfdoc $PackageVersion") {
        throw "CLI version mismatch: $CliVersion != ixfdoc $PackageVersion"
    }

    Write-Output $CliVersion
    Invoke-NativeCommand $VenvIxfdoc doctor --json | Out-Null
    Invoke-NativeCommand $VenvIxfdoc setup skills --runtimes codex --json | Out-Null

    $SkillPath = Join-Path $SmokeHome ".codex/skills/ixunfei-docx-reader/SKILL.md"
    if (-not (Test-Path $SkillPath)) {
        throw "Packaged Codex skill was not installed"
    }
    if (-not (Select-String -Path $SkillPath -Pattern "ixfdoc outline" -Quiet)) {
        throw "Installed Codex skill does not contain the structured reading workflow"
    }
}
finally {
    $env:HOME = $OriginalHome
    $env:USERPROFILE = $OriginalUserProfile
    if (Test-Path $SmokeRoot) {
        Remove-Item -Path $SmokeRoot -Recurse -Force
    }
}
