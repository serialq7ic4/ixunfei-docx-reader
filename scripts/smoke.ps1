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
Invoke-NativeCommand ixfdoc --version
Invoke-NativeCommand ixfdoc doctor --json | Out-Null
Invoke-NativeCommand ixfdoc setup skills --runtimes none --json | Out-Null
