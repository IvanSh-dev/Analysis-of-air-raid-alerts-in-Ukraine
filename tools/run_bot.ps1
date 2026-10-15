param([string]$Python = "")
$ErrorActionPreference = "Stop"
$PreviousUtf8 = $env:PYTHONUTF8
$env:PYTHONUTF8 = '1'
$ProjectRoot = Split-Path $PSScriptRoot -Parent
if (!$Python) { $Python = Join-Path $ProjectRoot '.venv/Scripts/python.exe' }
$EnteredToken = $false
if (!$env:TELEGRAM_BOT_TOKEN) {
    $SecretToken = Read-Host 'Telegram bot token (hidden; not saved)' -AsSecureString
    $TokenPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecretToken)
    try { $env:TELEGRAM_BOT_TOKEN = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($TokenPointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($TokenPointer) }
    $EnteredToken = $true
}
Push-Location $ProjectRoot
try { & $Python -m alerts_forecast.telegram_bot }
finally {
    Pop-Location
    if ($EnteredToken) { Remove-Item Env:TELEGRAM_BOT_TOKEN }
    $env:PYTHONUTF8 = $PreviousUtf8
}
