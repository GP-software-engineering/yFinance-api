# yFinance Self-Hosted API Server ![Python](https://img.shields.io/badge/Python-3.10%2B-blue)

This project provides a lightweight, self-hosted REST API for the `yfinance` Python library. It is designed to run as a robust `systemd` service on Ubuntu, featuring:
- request caching, 
- IP-based request counting, and 
- modular codebase.

---

## Table of Contents
- [Quick Start Guide](#quick-start-guide)
- [API Endpoints](#2-api-endpoints)

- [1. Installation and Setup (Production)](#1-installation-and-setup-production)
  - [Prerequisites](#prerequisites)
  - [Step 1: Create Service User and Directories](#step-1-create-service-user-and-directories)
  - [Step 2: Deploy Application Files](#step-2-deploy-application-files)
  - [Step 3: Configure the Application](#step-3-configure-the-application)
  - [Step 4: Setup the systemd Service](#step-4-setup-the-systemd-service)
  - [Step 5: Activate and Start the Service](#step-5-activate-and-start-the-service)

- [3. Configuring nginx as a Reverse Proxy (optional)](#3-configuring-nginx-as-a-reverse-proxy-optional)
  - [Step 1: Create nginx Configuration File](#step-1-create-nginx-configuration-file)
  - [Step 2: Example nginx Configuration](#step-2-example-nginx-configuration)
  - [Step 3: Enable and Restart nginx](#step-3-enable-and-restart-nginx)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [License](#license)

---


## 1. Installation and Setup (Production)

These instructions cover setting up the application as a production-ready service on an Ubuntu server, following system best practices.

### Prerequisites
- An Ubuntu server (18.04, 20.04, 22.04 or later).
- **Python 3.10+** and the `venv` module (`sudo apt install python3 python3-venv`).
- `nginx` (recommended, see section 3).

### Step 1: Create Service User and Directories
First, create a dedicated system user and the standardized directories for the application's code, configuration, and logs.

```bash
# 1. Create a system user named 'yfinance-api' with no login shell
sudo adduser --system --no-create-home --group yfinance-api

# 2. Create the application directory in /opt
sudo mkdir /opt/yfinance-api
sudo chown yfinance-api:yfinance-api /opt/yfinance-api

# 3. Create the configuration directory in /etc
sudo mkdir /etc/yfinance-api
sudo chown yfinance-api:yfinance-api /etc/yfinance-api

# 4. Create the log directory in /var/log
sudo mkdir /var/log/yfinance-api
sudo chown yfinance-api:yfinance-api /var/log/yfinance-api
```

### Step 2: Deploy Application Files

Copy the application files (`api_server.py`, `core_services.py`, `yfinance_service.py`) to `/opt/yfinance-api/`.

Then, create the virtual environment and install dependencies:

```bash
cd /opt/yfinance-api
sudo python3 -m venv venv
sudo venv/bin/pip install fastapi "uvicorn[standard]" yfinance cachetools json5
sudo chown -R yfinance-api:yfinance-api /opt/yfinance-api
```

### Step 3: Configure the Application
Create the configuration file at `/etc/yfinance-api/config.json`:

```bash
sudo nano /etc/yfinance-api/config.json
```

Example configuration:

```json
{
  "server": {
    "host": "0.0.0.0",        // Host to bind to. '0.0.0.0' for all interfaces.
    "port": 5000,             // Port for the service to listen on.
    "cors_origins": [
      "http://localhost",     // List of origins allowed to make requests.
      "[http://192.168.1.100](http://192.168.1.100)"  // Add your LAN IPs or front-end domains here.
    ]
  },
  "logging": {
    "main_log_file": "/var/log/yfinance-api/activity.log",
    "ip_counts_file": "/var/log/yfinance-api/ip_counts.json",
    // How many requests before batch-writing IP counts to disk.
    // Set to 50 for good performance. Set to 1 to write on every request.
    "ip_write_frequency": 50
  },
  "caching": {
    "enabled": true,          // Master switch for the cache.
    "ttl_seconds": 600,       // How long to cache a result (600 = 10 minutes).
    "max_size": 128           // Max number of unique tickers to cache.
  }
}
```

### Step 4: Setup the `systemd` Service

Create the service file:
```bash
sudo nano /etc/systemd/system/yfinance-api.service
```

Content:

```ini
[Unit]
Description=yFinance API Server
After=network.target

[Service]
User=yfinance-api
Group=yfinance-api
WorkingDirectory=/opt/yfinance-api
Environment="YFINANCE_API_CONFIG=/etc/yfinance-api/config.json"
ExecStart=/opt/yfinance-api/venv/bin/python /opt/yfinance-api/api_server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Step 5: Activate and Start the Service

Load and start the new service.

```bash
sudo systemctl daemon-reload
sudo systemctl enable yfinance-api.service
sudo systemctl start yfinance-api.service
```

Check status and logs:
```bash
sudo systemctl status yfinance-api.service
sudo journalctl -u yfinance-api.service -f
```


# 3. Configuring nginx as a Reverse Proxy (optional)

It is highly recommended to run this service behind `nginx`. This provides SSL (HTTPS), request buffering, and allows you to run on standard ports (80/443).

### Step 1: Create nginx Configuration File

Create a new config file for your API:

	sudo nano /etc/nginx/sites-available/yfinance-api

### Step 2: Example `nginx` Configuration

Paste the following configuration. This example forwards all requests from port 80 to the service running on port 5000. It also passes the correct headers so the application can log the real client IP.

```json
# Define the upstream service (our Python app)
upstream yfinance_service {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name api.yourdomain.com; # Or just the server's IP

    # --- Optional: IP Restrictions ---
    # Deny a specific IP
    # deny 192.168.1.253;
    # Allow all other IPs on the LAN
    # allow 192.168.1.0/24;
    # Deny everyone else
    # deny all;

    location / {
        # Forward the request to our app
        proxy_pass http://yfinance_service;

        # Pass client info headers
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        
        proxy_redirect off;
    }
}
```

### Step 3: Enable and Restart `nginx`

```bash
sudo ln -s /etc/nginx/sites-available/yfinance-api /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

Your service is now accessible via `http://api.yourdomain.com` (or your server's IP) and is fully managed by nginx.

---

## Architecture
Below is a high-level architecture diagram of the service and its main components.

```mermaid
flowchart LR
    C[Client / Browser / App]
    RP[nginx Reverse Proxy]
    API[yFinance API (FastAPI + Uvicorn)]
    SVC[Service Layer\ncore_services.py]
    YF[yfinance Library]
    YAHOO[(Yahoo Finance)]
    CACHE[(In-Memory Cache)]
    LOGS[(Logs + IP Counts)]

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

---

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
MIT License (or specify your license here).
