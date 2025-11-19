# yFinance Self-Hosted API Server ![Python](https://img.shields.io/badge/Python-3.10%2B-blue)

This project provides a lightweight, self-hosted REST API for the `yfinance` Python library. It is designed to run as a robust `systemd` service on Ubuntu, featuring:
- **Unified Endpoints**: Single and batch requests via a normalized API structure.
- **Smart Caching**: In-memory caching to prevent rate-limiting (customizable TTL).
- **Lightweight Quotes**: Specific endpoint for fast, bandwidth-efficient price data.
- **Traffic Monitoring**: IP-based request counting and logging.

To install and run in a production environment see the [installation-and-setup-production](installation-and-setup-production.md) instructions.

---
## Table of Contents
- [Quick Start Guide](#quick-start-guide)
- [API Endpoints](#api-endpoints)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [License](#license)
---

## Quick Start Guide
To run the API server locally for testing, execute the following commands:

```bash
# Clone the repository
git clone https://github.com/GP-software-engineering/yFinance-api
cd yFinance-api

# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate

# Either install from 'requirements' or install packages explicitly:
# 
# uncomment this for installing from requirements
# pip install -r requirements.txt
#
pip install fastapi "uvicorn[standard]" yfinance cachetools json5

# copy the 'config.json.example' file into 'config.json' and change 
# the setting values values according to yours preferences. Then
# Start the server
python api_server.py

## my comment: uvicorn yfinance_api.api_server:app --host 0.0.0.0 --port 5000
```

Access the API at: `http://127.0.0.1:5000`

**Notes**:

1. To prevent your IP address from being **blacklisted** by Yahoo, the application caches requests 
in memory by default (10-minute TTL); this and other settings can be modified in the `config.json`
file (requires a server restart).
2. To install and run in production environment see the [installation-and-setup-production](installation-and-setup-production.md) instructions.

---

## API Endpoints

Base URL: `http://[SERVER_IP]:[PORT]`

#### Health Check

	GET {Base_URL}/

Checks if the API server is online.

**Example:**

    curl "http://127.0.0.1:5000/"

#### Ticker Info
```
GET {Base_URL}/tickers/info?symbols={Ticker_1},{Ticker_2},...
```
Returns the main .info dictionary ffor one or more tickers, containing profiles, summary, and market data.

**Example:**
```
curl "http://127.0.0.1:5000/tickers/info?symbols=AAPL,ENI.MI"
```

#### Quotes
```
GET {Base_URL}/tickers/quote?symbols={Ticker_1},{Ticker_2},...
```
Returns lightweight quote data.

**Example:**
```
curl "http://127.0.0.1:5000/tickers/quote?symbols=MSFT"
```

#### Ticker History

    GET {Base_URL}/tickers/history?period={Period}&interval={interval}&symbols={Ticker_1},{Ticker_2},...

Returns historical OHLCV (Open, High, Low, Close, Volume) data.

**Query Parameters:**

- `period` (default: 1mo): 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
- `interval` (default: 1d): 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo

**Example:**

    curl "http://127.0.0.1:5000/tickers/history?symbols=MSFT,ENI.MI&period=1d&interval=2m"

#### Dividends
```
GET {Base_URL}/tickers/dividends?symbols={Ticker_1},{Ticker_2},...
```
Returns historical dividend payments.

**Example:**
```
curl "http://127.0.0.1:5000/tickers/dividends?symbols=AAPL,KO"
```

#### Splits
```
GET {Base_URL}/tickers/splits?symbols={Ticker_1},{Ticker_2},...
```

Returns historical stock splits.

**Example:**
```
curl "http://127.0.0.1:5000/tickers/splits?symbols=TSLA"
```

#### Recommendations
```
GET {Base_URL}/tickers/recommendations?symbols={Ticker_1},{Ticker_2},...
```
Returns historical analyst recommendations.

**Example:**
```
curl "http://127.0.0.1:5000/tickers/recommendations?symbols=NVDA"
```

#### Calendar
```
GET {Base_URL}/tickers/calendar?symbols={Ticker_1},{Ticker_2},...
```
Returns upcoming events (e.g., earnings dates).

**Example:**
```
curl "http://127.0.0.1:5000/tickers/calendar?symbols=GOOGL"
```

### Complete Batch Request Example
Request multiple endpoints for multiple tickers in sequence:
```bash
# Info for AAPL and ENI.MI
curl "http://127.0.0.1:5000/tickers/info?symbols=AAPL,ENI.MI"

# Quotes for MSFT, TSLA, and NVDA
curl "http://127.0.0.1:5000/tickers/quote?symbols=MSFT,TSLA,NVDA"
```


## Architecture
Below is a high-level architecture diagram of the service and its main components.

```mermaid
flowchart LR
    C["Client / Browser / App"]
    RP["nginx Reverse Proxy"]
    API["yFinance API (FastAPI + Uvicorn)"]
    SVC["Service Layer\ncore_services.py"]
    YF["yfinance Library"]
    YAHOO["Yahoo Finance"]
    CACHE["In-Memory Cache"]
    LOGS["Logs + IP Counts"]

    C --> RP --> API
    API --> SVC --> YF --> YAHOO
    API --> CACHE
    API --> LOGS
```

**Notes**
- **FastAPI + Uvicorn** serves the REST endpoints.
- **Cache** (TTL-based) reduces repeated upstream calls.
- **Logging & IP counting** are persisted under `/var/log/yfinance-api/`.
- **nginx** optionally fronts the service for TLS, buffering and standard ports (80/443).

## Contributing
We welcome contributions! To contribute:

1. Fork the repository.
2. Create a new branch for your feature or fix: `git checkout -b feat/awesome-thing`.
3. Commit with conventional messages (e.g., `feat: add cache metrics`).
4. Ensure code follows PEP 8 and is formatted with `black` / `ruff`.
5. Add or update tests where applicable.
6. Open a Pull Request describing the change and rationale.

### Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements-dev.txt
pre-commit install
pytest -q
```

---

## License
MIT License Copyright (c) 2025 GP software engineering (by gpcaretti)
