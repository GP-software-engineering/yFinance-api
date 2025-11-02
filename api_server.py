##
# Main file
#
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# --- Import Core & Service Logic ---
from core_services import (
    logger,
    ip_counts,
    save_ip_counts,
    server_config,
    logging_config
)
from yfinance_service import (
    get_ticker_info,
    get_ticker_history,
    get_ticker_dividends,
    get_ticker_splits,
    get_ticker_recommendations,
    get_ticker_calendar
)

# --- 1. Initialize FastAPI App ---
app = FastAPI(
    title="yFinance API",
    description="A self-hosted API for yFinance data."
)

# --- 2. Add Shutdown Event Handler ---
@app.on_event("shutdown")
def shutdown_event():
    """
    This function is triggered when FastAPI shuts down cleanly
    (e.g., on 'systemctl stop').
    """
    logger.info("Server shutting down. Saving final IP counts...")
    try:
        save_ip_counts(logging_config["ip_counts_file"], ip_counts)
        logger.info("Final IP counts saved successfully.")
    except Exception as e:
        logger.error(f"Failed to save IP counts on shutdown: {e}")

# --- 3. Add Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=server_config["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WRITE_FREQUENCY = logging_config.get("ip_write_frequency", 50)

@app.middleware("http")
async def ip_counter_middleware(request: Request, call_next):
    """
    Middleware to count requests by IP and log them.
    Includes batch-writing logic.
    """
    client_ip = request.client.host
    ip_counts[client_ip] += 1
    logger.info(f"Request from {client_ip} for {request.url.path}")

    if WRITE_FREQUENCY > 0:
        total_requests = sum(ip_counts.values())
        if total_requests % WRITE_FREQUENCY == 0:
            logger.info(f"Reached {total_requests} requests. Batch-writing IP counts to disk...")
            try:
                save_ip_counts(logging_config["ip_counts_file"], ip_counts)
            except Exception as e:
                logger.error(f"Failed to batch-write IP counts: {e}")

    response = await call_next(request)
    return response

# --- 4. API Endpoints ---

@app.get("/")
def read_root():
    """A health check endpoint."""
    logger.info("Health check endpoint '/' was hit.")
    return {"status": "online", "message": "Welcome to your yFinance API"}

@app.get("/ticker/{ticker_symbol}/info")
def http_get_ticker_info(ticker_symbol: str):
    """Retrieves the complete .info object for a given ticker."""
    try:
        data = get_ticker_info(ticker_symbol)
        logger.info(f"Successfully served info for {ticker_symbol}")
        return data
    except Exception as e:
        logger.error(f"Error in info endpoint for {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/ticker/{ticker_symbol}/history")
def http_get_ticker_history(ticker_symbol: str, period: str = "1mo", interval: str = "1d"):
    """Retrieves historical (OHLCV) data for a given ticker."""
    try:
        data = get_ticker_history(ticker_symbol, period, interval)
        logger.info(f"Successfully served history for {ticker_symbol}")
        return data
    except Exception as e:
        logger.error(f"Error in history endpoint for {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# --- NEW Endpoints ---

@app.get("/ticker/{ticker_symbol}/dividends")
def http_get_ticker_dividends(ticker_symbol: str):
    """Retrieves dividend history for a given ticker."""
    try:
        data = get_ticker_dividends(ticker_symbol)
        logger.info(f"Successfully served dividends for {ticker_symbol}")
        return data
    except Exception as e:
        logger.error(f"Error in dividends endpoint for {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/ticker/{ticker_symbol}/splits")
def http_get_ticker_splits(ticker_symbol: str):
    """Retrieves stock split history for a given ticker."""
    try:
        data = get_ticker_splits(ticker_symbol)
        logger.info(f"Successfully served splits for {ticker_symbol}")
        return data
    except Exception as e:
        logger.error(f"Error in splits endpoint for {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/ticker/{ticker_symbol}/recommendations")
def http_get_ticker_recommendations(ticker_symbol: str):
    """RetrieVes analyst recommendations for a given ticker."""
    try:
        data = get_ticker_recommendations(ticker_symbol)
        logger.info(f"Successfully served recommendations for {ticker_symbol}")
        return data
    except Exception as e:
        logger.error(f"Error in recommendations endpoint for {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/ticker/{ticker_symbol}/calendar")
def http_get_ticker_calendar(ticker_symbol: str):
    """Retrieves upcoming event calendar for a given ticker."""
    try:
        data = get_ticker_calendar(ticker_symbol)
        logger.info(f"Successfully served calendar for {ticker_symbol}")
        return data
    except Exception as e:
        logger.error(f"Error in calendar endpoint for {ticker_symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# --- 5. Main execution ---
if __name__ == "__main__":
    """
    This block is executed when 'python api_server.py' is run.
    systemd uses this to start the application.
    """
    logger.info(f"Starting server on {server_config['host']}:{server_config['port']}")
    uvicorn.run(
        "api_server:app",
        host=server_config["host"],
        port=server_config["port"],
        reload=False
    )
