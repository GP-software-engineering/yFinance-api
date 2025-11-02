##
# yfinance endpoints with cache management
#
# /opt/yfinance-api/yfinance_service.py
import yfinance as yf
from fastapi import HTTPException
from cachetools import TTLCache, cached
from core_services import logger, cache_config  # Import services

# --- Cache Setup ---
if cache_config["enabled"]:
    logger.info(f"Caching enabled: TTL={cache_config['ttl_seconds']}s, MaxSize={cache_config['max_size']}")
    info_cache = TTLCache(maxsize=cache_config["max_size"], ttl=cache_config["ttl_seconds"])
    history_cache = TTLCache(maxsize=cache_config["max_size"], ttl=cache_config["ttl_seconds"])
    # --- NEW Caches ---
    dividends_cache = TTLCache(maxsize=cache_config["max_size"], ttl=cache_config["ttl_seconds"])
    splits_cache = TTLCache(maxsize=cache_config["max_size"], ttl=cache_config["ttl_seconds"])
    recommendations_cache = TTLCache(maxsize=cache_config["max_size"], ttl=cache_config["ttl_seconds"])
    calendar_cache = TTLCache(maxsize=cache_config["max_size"], ttl=cache_config["ttl_seconds"])
else:
    logger.info("Caching is disabled.")
    # Use dummy cache objects if disabled (simplifies endpoint logic)
    info_cache = TTLCache(maxsize=1, ttl=1)
    history_cache = TTLCache(maxsize=1, ttl=1)
    # --- NEW Dummy Caches ---
    dividends_cache = TTLCache(maxsize=1, ttl=1)
    splits_cache = TTLCache(maxsize=1, ttl=1)
    recommendations_cache = TTLCache(maxsize=1, ttl=1)
    calendar_cache = TTLCache(maxsize=1, ttl=1)

# --- Private Fetching Functions (Decorated) ---

@cached(info_cache, lock=None)
def _fetch_info_from_yahoo(ticker_symbol):
    """Cached function to fetch Ticker.info"""
    logger.info(f"CACHE MISS: Fetching info for {ticker_symbol} from yfinance")
    try:
        ticker = yf.Ticker(ticker_symbol)
        if not ticker.info or ticker.info.get('regularMarketPrice') is None:
            raise ValueError(f"Ticker '{ticker_symbol}' not found in yfinance.")
        return ticker.info
    except Exception as e:
        logger.error(f"yfinance error fetching info for {ticker_symbol}: {e}")
        raise e

@cached(history_cache, lock=None)
def _fetch_history_from_yahoo(ticker_symbol, period, interval):
    """Cached function to fetch Ticker.history"""
    logger.info(f"CACHE MISS: Fetching history for {ticker_symbol} ({period}, {interval}) from yfinance")
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period, interval=interval)
        if hist.empty:
            raise ValueError(f"No historical data found for '{ticker_symbol}' with params.")
        
        return hist.reset_index().to_dict(orient="records")
    except Exception as e:
        logger.error(f"yfinance error fetching history for {ticker_symbol}: {e}")
        raise e

# --- NEW Private Functions ---

@cached(dividends_cache, lock=None)
def _fetch_dividends_from_yahoo(ticker_symbol):
    """Cached function to fetch Ticker.dividends"""
    logger.info(f"CACHE MISS: Fetching dividends for {ticker_symbol} from yfinance")
    try:
        ticker = yf.Ticker(ticker_symbol)
        dividends = ticker.dividends
        if dividends.empty:
            return [] # Return empty list if no dividends
        return dividends.reset_index().to_dict(orient="records")
    except Exception as e:
        logger.error(f"yfinance error fetching dividends for {ticker_symbol}: {e}")
        return [] # Return empty list on error

@cached(splits_cache, lock=None)
def _fetch_splits_from_yahoo(ticker_symbol):
    """Cached function to fetch Ticker.splits"""
    logger.info(f"CACHE MISS: Fetching splits for {ticker_symbol} from yfinance")
    try:
        ticker = yf.Ticker(ticker_symbol)
        splits = ticker.splits
        if splits.empty:
            return [] # Return empty list if no splits
        return splits.reset_index().to_dict(orient="records")
    except Exception as e:
        logger.error(f"yfinance error fetching splits for {ticker_symbol}: {e}")
        return [] # Return empty list on error

@cached(recommendations_cache, lock=None)
def _fetch_recommendations_from_yahoo(ticker_symbol):
    """Cached function to fetch Ticker.recommendations"""
    logger.info(f"CACHE MISS: Fetching recommendations for {ticker_symbol} from yfinance")
    try:
        ticker = yf.Ticker(ticker_symbol)
        recs = ticker.recommendations
        if recs.empty:
            return [] # Return empty list if no recommendations
        return recs.reset_index().to_dict(orient="records")
    except Exception as e:
        logger.error(f"yfinance error fetching recommendations for {ticker_symbol}: {e}")
        return [] # Return empty list on error

@cached(calendar_cache, lock=None)
def _fetch_calendar_from_yahoo(ticker_symbol):
    """Cached function to fetch Ticker.calendar"""
    logger.info(f"CACHE MISS: Fetching calendar for {ticker_symbol} from yfinance")
    try:
        ticker = yf.Ticker(ticker_symbol)
        calendar = ticker.calendar
        if calendar.empty:
            return {} # Return empty dict if no calendar
        
        # Convert DataFrame (e.g., Index='Earnings Date', Col[0]='2025-01-27') to dict
        calendar_dict = calendar.to_dict().get(0, {})

        # Clean for JSON (convert Timestamps to strings)
        cleaned_calendar = {}
        for key, value in calendar_dict.items():
            if hasattr(value, 'isoformat'):
                cleaned_calendar[key] = value.isoformat()
            else:
                cleaned_calendar[key] = value
                
        return cleaned_calendar
    except Exception as e:
        logger.error(f"yfinance error fetching calendar for {ticker_symbol}: {e}")
        return {} # Return empty dict on error

# --- Public Service Functions ---

def get_ticker_info(ticker_symbol: str):
    """Public-facing function to get ticker info."""
    if cache_config["enabled"]:
        return _fetch_info_from_yahoo(ticker_symbol)
    else:
        logger.info(f"Cache disabled. Fetching info for {ticker_symbol} (direct)")
        return _fetch_info_from_yahoo.__wrapped__(ticker_symbol)

def get_ticker_history(ticker_symbol: str, period: str, interval: str):
    """Public-facing function to get ticker history."""
    if cache_config["enabled"]:
        return _fetch_history_from_yahoo(ticker_symbol, period, interval)
    else:
        logger.info(f"Cache disabled. Fetching history for {ticker_symbol} (direct)")
        return _fetch_history_from_yahoo.__wrapped__(ticker_symbol, period, interval)

def get_ticker_dividends(ticker_symbol: str):
    """Public-facing function to get ticker dividends."""
    if cache_config["enabled"]:
        return _fetch_dividends_from_yahoo(ticker_symbol)
    else:
        logger.info(f"Cache disabled. Fetching dividends for {ticker_symbol} (direct)")
        return _fetch_dividends_from_yahoo.__wrapped__(ticker_symbol)

def get_ticker_splits(ticker_symbol: str):
    """Public-facing function to get ticker splits."""
    if cache_config["enabled"]:
        return _fetch_splits_from_yahoo(ticker_symbol)
    else:
        logger.info(f"Cache disabled. Fetching splits for {ticker_symbol} (direct)")
        return _fetch_splits_from_yahoo.__wrapped__(ticker_symbol)

def get_ticker_recommendations(ticker_symbol: str):
    """Public-facing function to get ticker recommendations."""
    if cache_config["enabled"]:
        return _fetch_recommendations_from_yahoo(ticker_symbol)
    else:
        logger.info(f"Cache disabled. Fetching recommendations for {ticker_symbol} (direct)")
        return _fetch_recommendations_from_yahoo.__wrapped__(ticker_symbol)

def get_ticker_calendar(ticker_symbol: str):
    """Public-facing function to get ticker calendar."""
    if cache_config["enabled"]:
        return _fetch_calendar_from_yahoo(ticker_symbol)
    else:
        logger.info(f"Cache disabled. Fetching calendar for {ticker_symbol} (direct)")
        return _fetch_calendar_from_yahoo.__wrapped__(ticker_symbol)
