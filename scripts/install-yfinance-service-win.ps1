<#
    yFinance-api Windows Service Installer
    --------------------------------------
    Requirements:
    - NSSM installed and available in PATH
#>

Write-Host "=== Installing yFinance-api as a Windows Service ==="

$serviceName = "yFinanceAPI"
$pythonPath = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
$appPath = Join-Path $PSScriptRoot "api_server.py"

if (-Not (Get-Command "nssm.exe" -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: NSSM is not installed or not in PATH."
    Write-Host "Download from https://nssm.cc/download"
    exit 1
}

Write-Host "Creating service '$serviceName'..."
nssm install $serviceName $pythonPath $appPath

Write-Host "Setting service parameters..."
nssm set $serviceName DisplayName "yFinance API Service"
nssm set $serviceName Start SERVICE_AUTO_START
nssm set $serviceName AppDirectory $PSScriptRoot

Write-Host "Starting service..."
nssm start $serviceName

Write-Host "Service installed and running."
