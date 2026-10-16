param([string]$Python = "python")
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $ProjectRoot
$PreviousTemp = $env:TEMP
$PreviousTmp = $env:TMP
try {
    New-Item -ItemType Directory -Force .tmp | Out-Null
    $env:TEMP = (Resolve-Path .tmp).Path
    $env:TMP = $env:TEMP
    if (!(Test-Path .venv/Scripts/python.exe)) {
        & $Python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw "Creating the virtual environment failed" }
    }
    & .venv/Scripts/python.exe -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
    & .venv/Scripts/python.exe -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw "Tests failed" }
    & .venv/Scripts/python.exe -m alerts_forecast.pipeline
    if ($LASTEXITCODE -ne 0) { throw "Pipeline failed" }
    & .venv/Scripts/python.exe -m alerts_forecast.improve
    if ($LASTEXITCODE -ne 0) { throw "Improved-model evaluation failed" }
    & .venv/Scripts/python.exe -m alerts_forecast.periods
    if ($LASTEXITCODE -ne 0) { throw "Probability/period evaluation failed" }
    & .venv/Scripts/python.exe -m alerts_forecast.threshold_probability
    if ($LASTEXITCODE -ne 0) { throw "Threshold probability evaluation failed" }
    & .venv/Scripts/python.exe tools/build_dashboard.py
    if ($LASTEXITCODE -ne 0) { throw "Dashboard export failed" }
    & .venv/Scripts/python.exe tools/build_bot_deployment.py
    if ($LASTEXITCODE -ne 0) { throw "Webhook deployment export failed" }
} finally {
    $env:TEMP = $PreviousTemp
    $env:TMP = $PreviousTmp
    Pop-Location
}
