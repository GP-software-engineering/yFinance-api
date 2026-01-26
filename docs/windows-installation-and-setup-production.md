# yFinance Self-Hosted API Server ![Python](https://img.shields.io/badge/Python-3.10%2B-blue)

This is project provides a lightweight, self-hosted REST API for the `yfinance` Python library on
a **Microsoft Windows OS**.
See the [README](../README.md) file for usage and contribution guidelines.

---

## 1. Requirements
- Windows 10+ or Windows Server 2019+
- Python 3.10+
- PowerShell 5+
- Git (optional)
- NSSM (recommended for running as a Windows service)

## 2. Download the Project
```
powershell
git clone https://github.com/GP-software-engineering/yFinance-api
cd yFinance-api
```

## 3. Create Virtual Environment & Install Dependencies
```
powershell
python -m venv venv
./venv/Scripts/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Prepare Configuration File
```
powershell
Copy-Item config.json.example config.json
```

Edit as needed.

## 5. Start API Server (manual run)
```
powershell
./venv/Scripts/python.exe -m uvicorn yfinance_api.api_server:app --host 0.0.0.0 --port 5000
```

## 6. Install as Windows Service (NSSM)
```
powershell
powershell -ExecutionPolicy Bypass -File ./scripts/install-yfinance-service-win.ps1
```

Manual alternative:
```
powershell
nssm install yFinanceAPI "C:\path\to\yFinance-api\venv\Scripts\python.exe" "C:\path\to\yFinance-api\api_server.py"
nssm start yFinanceAPI
```

## 7. Update Application
```
powershell
nssm stop yFinanceAPI
git pull
./venv/Scripts/pip install -r requirements.txt
nssm start yFinanceAPI
```

## 8. Logs & Troubleshooting
```
powershell
nssm status yFinanceAPI
```

## 9. Optional Automated Setup
```
powershell
powershell -ExecutionPolicy Bypass -File ./scripts/startup-win.ps1
```
