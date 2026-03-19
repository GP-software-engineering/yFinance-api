##
# yfinance endpoints with cache management
#
# yfinance_service.py
import yfinance as yf
import yfinance.utils as yf_utils 
import os
from fastapi import HTTPException
from cachetools import TTLCache, cached
from core_services import logger, cache_config
import math
from datetime import datetime, timezone

# --- Cache Setup ---
if cache_config.get("enabled", True):
    ttl = cache_config.get("ttl_seconds", 600)
    max_size = cache_config.get("max_size", 128)
    cache_dir = cache_config.get("cache_dir", "/tmp/py-yfinance-cache")
    
    logger.info(f"Caching enabled: TTL={ttl}s, MaxSize={max_size}")
    
    # Single item caches
    info_cache = TTLCache(maxsize=max_size, ttl=ttl)
    history_cache = TTLCache(maxsize=max_size, ttl=ttl)
    quote_cache = TTLCache(maxsize=max_size, ttl=ttl)
    dividends_cache = TTLCache(maxsize=max_size, ttl=ttl)
    splits_cache = TTLCache(maxsize=max_size, ttl=ttl)
    recommendations_cache = TTLCache(maxsize=max_size, ttl=ttl)
    calendar_cache = TTLCache(maxsize=max_size, ttl=ttl)
    
    # Batch result caches
    multi_info_cache = TTLCache(maxsize=64, ttl=ttl)
    multi_quote_cache = TTLCache(maxsize=64, ttl=ttl)

    try:
        # Ensure the cache directory exists and is writable
        os.makedirs(cache_dir, exist_ok=True)
        yf.set_tz_cache_location(cache_dir)
        logger.info(f"yfinance internal cache set to: {cache_dir}")
    except Exception as e:
        logger.warning(f"Could not set custom yfinance cache location at {cache_dir}: {e}")
else:
    logger.info("Caching is disabled via config.")
    # Dummy caches
    info_cache = TTLCache(maxsize=1, ttl=1)
    history_cache = TTLCache(maxsize=1, ttl=1)
    quote_cache = TTLCache(maxsize=1, ttl=1)
    dividends_cache = TTLCache(maxsize=1, ttl=1)
    splits_cache = TTLCache(maxsize=1, ttl=1)
    recommendations_cache = TTLCache(maxsize=1, ttl=1)
    calendar_cache = TTLCache(maxsize=1, ttl=1)
    multi_info_cache = TTLCache(maxsize=1, ttl=1)
    multi_quote_cache = TTLCache(maxsize=1, ttl=1)

# --- Helper: Data Mapping ---

def _map_fast_info_to_dict(ticker_symbol, fi, info=None):
    """Helper to extract and clean data from the fast_info object."""
    def clean(val):
        return val if (val is not None and not math.isnan(val)) else None

    try:
        last_price = fi.last_price
        prev_close = fi.previous_close
        
        if last_price is None or math.isnan(last_price):
            return {
                "symbol": ticker_symbol, 
                "isNotValid": True, 
                "error": f"Quote not found for symbol: {ticker_symbol}"
            }

        change = 0.0
        pct_change = 0.0
        
        if prev_close is not None and prev_close != 0:
            change = last_price - prev_close
            pct_change = (change / prev_close) * 100

        exch_timezone = getattr(fi, 'timezone', None)

        # get the official timestamp from 'info' if available
        market_time = None
        if info and isinstance(info, dict):
            market_time = info.get("regularMarketTime")

        iso_time = None
        if market_time:
            iso_time = datetime.fromtimestamp(market_time, timezone.utc).isoformat().replace("+00:00", "Z")

        return {
            "symbol": ticker_symbol,
            "currentPrice": clean(last_price),
            "previousClose": clean(prev_close),
            "open": clean(fi.open),
            "dayHigh": clean(fi.day_high),
            "dayLow": clean(fi.day_low),
            "change": clean(change),
            "percentChange": clean(pct_change),
            "volume": clean(fi.last_volume),
            "exchangeTimezone": exch_timezone,
            "timestamp": iso_time,
            "fetchTime": datetime.now(timezone.utc).isoformat()
        }
    except Exception:
        return {
            "symbol": ticker_symbol, 
            "isNotValid": True, 
            "error": f"Quote not found for symbol: {ticker_symbol}"
        }

# --- Core Fetching Functions (Single) ---

@cached(info_cache, lock=None)
def _fetch_info_single(ticker_symbol):
    logger.info(f"CACHE MISS: Fetching info for {ticker_symbol}")
    try:
        ticker = yf.Ticker(ticker_symbol)
        # Basic validation
        if not ticker.info or (len(ticker.info) <= 1 and 'regularMarketPrice' not in ticker.info):
             return {
                 "symbol": ticker_symbol, 
                 "isNotValid": True, 
                 "error": f"Information not found for symbol: {ticker_symbol}"
             }
        return ticker.info
    except Exception:
        return {
            "symbol": ticker_symbol, 
            "isNotValid": True, 
            "error": f"Information not found for symbol: {ticker_symbol}"
        }

@cached(quote_cache, lock=None)
def _fetch_quote_single(ticker_symbol):
    logger.info(f"CACHE MISS: Fetching quote for {ticker_symbol}")
    ticker = yf.Ticker(ticker_symbol)
    return _map_fast_info_to_dict(ticker_symbol, ticker.fast_info, ticker.info)

@cached(history_cache, lock=None)
def _fetch_history_single(ticker_symbol, period, interval):
    logger.info(f"CACHE MISS: Fetching history for {ticker_symbol}")
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period, interval=interval)
        if hist.empty:
            return {
                "symbol": ticker_symbol, 
                "isNotValid": True, 
                "error": f"No historical data found for symbol: {ticker_symbol}"
            } 
        return hist.reset_index().to_dict(orient="records")
    except Exception:
        return {
            "symbol": ticker_symbol, 
            "isNotValid": True, 
            "error": f"No historical data found for symbol: {ticker_symbol}"
        }

# --- Core Fetching Functions (Batch) ---

@cached(multi_info_cache, lock=None)
def _fetch_info_batch(symbols_str):
    """Uses yf.Tickers for threaded batch fetching of info."""
    logger.info(f"CACHE MISS: Fetching batch info for: {symbols_str}")
    symbols_list = symbols_str.split(" ")
    tickers = yf.Tickers(symbols_str)
    results = {}
    for symbol in symbols_list:
        try:
            ticker_obj = tickers.tickers.get(symbol)
            if ticker_obj and ticker_obj.info and len(ticker_obj.info) > 1:
                results[symbol] = ticker_obj.info
            else:
                results[symbol] = {
                    "symbol": symbol, 
                    "isNotValid": True, 
                    "error": f"Information not found for symbol: {symbol}"
                }
        except Exception:
            results[symbol] = {
                "symbol": symbol, 
                "isNotValid": True, 
                "error": f"Information not found for symbol: {symbol}"
            }
    return results

@cached(multi_quote_cache, lock=None)
def _fetch_quote_batch(symbols_str):
    """Uses yf.Tickers for threaded batch fetching of quotes."""
    logger.info(f"CACHE MISS: Fetching batch quotes for: {symbols_str}")
    symbols_list = symbols_str.split(" ")
    tickers = yf.Tickers(symbols_str)
    results = {}
    for symbol in symbols_list:
        try:
            ticker_obj = tickers.tickers.get(symbol)
            if ticker_obj:
                results[symbol] = _map_fast_info_to_dict(symbol, ticker_obj.fast_info, ticker_obj.info)
            else:
                results[symbol] = {
                    "symbol": symbol, 
                    "isNotValid": True, 
                    "error": f"Quote not found for symbol: {symbol}"
                }
        except Exception:
            results[symbol] = {
                "symbol": symbol, 
                "isNotValid": True, 
                "error": f"Quote not found for symbol: {symbol}"
            }
    return results

# --- Public Accessors (Unified) ---

def get_info(symbols_list):
    # ROUTER INTELLIGENTE: 1 simbolo -> cache singola, N simboli -> cache batch
    if len(symbols_list) == 1:
        sym = symbols_list[0]
        return {sym: _fetch_info_single(sym)}
    
    joined = " ".join(sorted(symbols_list))
    return _fetch_info_batch(joined)

def get_quote(symbols_list):
    if len(symbols_list) == 1:
        sym = symbols_list[0]
        return {sym: _fetch_quote_single(sym)}
    
    joined = " ".join(sorted(symbols_list))
    return _fetch_quote_batch(joined)

def get_history(symbols_list, period, interval):
    results = {}
    for sym in symbols_list:
        results[sym] = _fetch_history_single(sym, period, interval)
    return results

# --- Other Single-Only Fetchers (Wrapped in Dict for consistency) ---

def _generic_single_fetch(symbols_list, cache_func, error_msg_tag):
    results = {}
    for sym in symbols_list:
        try:
            res = cache_func(sym)
            results[sym] = res
        except Exception:
            results[sym] = {
                "symbol": sym, 
                "isNotValid": True, 
                "error": f"{error_msg_tag} not found for symbol: {sym}"
            }
    return results

@cached(dividends_cache, lock=None)
def _fetch_dividends_single(sym):
    t = yf.Ticker(sym)
    if t.dividends.empty:
        try:
            if t.fast_info.last_price is None:
                return {
                    "symbol": sym, 
                    "isNotValid": True, 
                    "error": f"Dividends not found for symbol: {sym}"
                }
        except Exception:
            return {
                "symbol": sym, 
                "isNotValid": True, 
                "error": f"Dividends not found for symbol: {sym}"
            }
        return []
    return t.dividends.reset_index().to_dict(orient="records")

@cached(splits_cache, lock=None)
def _fetch_splits_single(sym):
    t = yf.Ticker(sym)
    if t.splits.empty:
        try:
            if t.fast_info.last_price is None:
                return {
                    "symbol": sym, 
                    "isNotValid": True, 
                    "error": f"Splits not found for symbol: {sym}"
                }
        except Exception:
            return {
                "symbol": sym, 
                "isNotValid": True, 
                "error": f"Splits not found for symbol: {sym}"
            }
        return []
    return t.splits.reset_index().to_dict(orient="records")

@cached(recommendations_cache, lock=None)
def _fetch_recs_single(sym):
    t = yf.Ticker(sym)
    if t.recommendations.empty:
        try:
            if t.fast_info.last_price is None:
                return {
                    "symbol": sym, 
                    "isNotValid": True, 
                    "error": f"Recommendations not found for symbol: {sym}"
                }
        except Exception:
            return {
                "symbol": sym, 
                "isNotValid": True, 
                "error": f"Recommendations not found for symbol: {sym}"
            }
        return []
    return t.recommendations.reset_index().to_dict(orient="records")

@cached(calendar_cache, lock=None)
def _fetch_calendar_single(sym):
    t = yf.Ticker(sym)
    if t.calendar.empty: 
        return {
            "symbol": sym, 
            "isNotValid": True, 
            "error": f"Calendar not found for symbol: {sym}"
        }
    cal = t.calendar.to_dict().get(0, {})
    return {k: (v.isoformat() if hasattr(v, 'isoformat') else v) for k, v in cal.items()}

# --- Public Wrappers ---

def get_dividends(symbols_list): return _generic_single_fetch(symbols_list, _fetch_dividends_single, "Dividends")
def get_splits(symbols_list): return _generic_single_fetch(symbols_list, _fetch_splits_single, "Splits")
def get_recommendations(symbols_list): return _generic_single_fetch(symbols_list, _fetch_recs_single, "Recommendations")
def get_calendar(symbols_list): return _generic_single_fetch(symbols_list, _fetch_calendar_single, "Calendar")
