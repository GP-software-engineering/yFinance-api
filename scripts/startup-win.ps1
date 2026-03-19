# yFinance-api Setup and Launch Script for Windows 11

$repoUrl = "https://github.com/GP-software-engineering/yFinance-api"
$folderName = "yFinance-api"

Write-Host "--- yFinance-api Automation Tool ---" -ForegroundColor Yellow

# Ensure script stops on errors
$ErrorActionPreference = "Stop"

<# 
# Clone the repository if it doesn't exist
if (-not (Test-Path $folderName)) {
    Write-Host "Cloning repository..." -ForegroundColor Cyan
    git clone $repoUrl
}

Set-Location -Path $folderName
#>

# Create Virtual Environment
if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv venv
}

Write-Host "Activating virtual environment..."
.\venv\Scripts\Activate

# Install dependencies
Write-Host "Installing required packages..." -ForegroundColor Cyan
pip --upgrade pip pip install -r requirements.txt 

# Prepare Configuration File
if (-not (Test-Path "config.json")) {
    Write-Host "[4/5] Creating config.json from example..." -ForegroundColor Cyan
    Copy-Item "config.json.example" "config.json"
}

# 5. Launch the API Server
Write-Host "Launching API Server..." -ForegroundColor Green
Write-Host "The API will be available at: http://127.0.0.1:5000" -ForegroundColor White
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor Gray

# Running
python .\src\yfinance_api\api_server.py

#.\venv\Scripts\python.exe -m uvicorn yfinance_api.api_server:app --host 127.0.0.1 --port 5000