##
# Main file
#
# api_server.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn
from typing import Optional

# Import the version from your __init__.py
from __init__ import __version__

from core_services import (
    logger,
    ip_counts,
    save_ip_counts,
    server_config,
    logging_config
)
from yfinance_service import (
    get_info,
    get_quote,
    get_history,
    get_dividends,
    get_splits,
    get_recommendations,
    get_calendar
)

# --- Helper Functions ---
def parse_symbols(symbol: str, symbols: str):
    """Parses single or multiple symbols into a list."""
    if symbols:
        return [s.strip().upper() for s in symbols.split(",")]
    if symbol:
        return [symbol.strip().upper()]
    return []

# --- Lifespan Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info(f"yFinance API Server v{__version__} starting up...")
    yield  
    
    # Shutdown logic
    logger.info("Server shutting down. Saving final IP counts...")
    try:
        save_ip_counts(logging_config.get("ip_counts_file"), ip_counts)
        logger.info("Final IP counts saved successfully.")
    except Exception as e:
        logger.error(f"Failed to save IP counts on shutdown: {e}")

# --- App Init ---
# Set docs_url="/" to show Swagger UI at the root address
app = FastAPI(
    title="yFinance API",
    description="A unified, self-hosted API for yFinance data.",
    version=__version__,
    lifespan=lifespan,
    docs_url="/",      # Swagger UI now at http://localhost:5000/
    redoc_url="/redoc" # ReDoc available at http://localhost:5000/redoc
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=server_config.get("cors_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WRITE_FREQ = logging_config.get("ip_write_frequency", 50)

@app.middleware("http")
async def ip_counter_middleware(request: Request, call_next):
    client_ip = request.client.host
    ip_counts[client_ip] += 1
    logger.info(f"Request from {client_ip}: {request.method} {request.url.path}")
    
    if WRITE_FREQ > 0 and sum(ip_counts.values()) % WRITE_FREQ == 0:
        save_ip_counts(logging_config.get("ip_counts_file"), ip_counts)

    return await call_next(request)

# --- Helper: Symbol Parser ---
def parse_symbols(symbol: Optional[str], symbols: Optional[str]):
    """
    Consolidates 'symbol' and 'symbols' query params into a unique list.
    """
    final_list = []
    
    # Handle 'symbols' (plural, comma separated)
    if symbols:
        final_list.extend([s.strip().upper() for s in symbols.split(",") if s.strip()])
    
    # Handle 'symbol' (singular, legacy or convenience)
    if symbol:
        final_list.extend([s.strip().upper() for s in symbol.split(",") if s.strip()])
        
    if not final_list:
        raise HTTPException(status_code=400, detail="No ticker symbols provided. Use ?symbols=AAPL,MSFT")
        
    # Remove duplicates while preserving order
    return list(dict.fromkeys(final_list))

# --- Unified Endpoints ---

@app.get("/tickers/info", tags=["Ticker Data"])
def route_info(symbol: str = Query(None), symbols: str = Query(None)):
    """Get comprehensive information for one or more tickers."""
    target_list = parse_symbols(symbol, symbols)
    try:
        return get_info(target_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tickers/quote", tags=["Ticker Data"])
def route_quote(symbol: str = Query(None), symbols: str = Query(None)):
    """Get real-time quote data for one or more tickers."""
    target_list = parse_symbols(symbol, symbols)
    try:
        return get_quote(target_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tickers/history", tags=["Market Data"])
def route_history(
    symbol: str = Query(None),
    symbols: str = Query(None),
    period: str = "1mo",
    interval: str = "1d"
):
    """Get historical data (OHLCV) for one or more tickers."""
    target_list = parse_symbols(symbol, symbols)
    try:
        return get_history(target_list, period, interval)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tickers/dividends", tags=["Corporate Actions"])
def route_dividends(symbol: str = Query(None), symbols: str = Query(None)):
    """Get dividend history for one or more tickers."""
    return get_dividends(parse_symbols(symbol, symbols))

@app.get("/tickers/splits", tags=["Corporate Actions"])
def route_splits(symbol: str = Query(None), symbols: str = Query(None)):
    """Get stock split history."""
    return get_splits(parse_symbols(symbol, symbols))

@app.get("/tickers/recommendations", tags=["Analysis"])
def route_recs(symbol: str = Query(None), symbols: str = Query(None)):
    """Get analyst recommendations."""
    return get_recommendations(parse_symbols(symbol, symbols))

@app.get("/tickers/calendar", tags=["Analysis"])
def route_calendar(symbol: str = Query(None), symbols: str = Query(None)):
    """Get earnings and historical events calendar."""
    return get_calendar(parse_symbols(symbol, symbols))

# --- Main Execution ---
if __name__ == "__main__":
    h = server_config.get("host", "0.0.0.0")
    p = server_config.get("port", 5000)
    logger.info(f"Starting server on {h}:{p}")
    uvicorn.run("api_server:app", host=h, port=p, reload=False)
