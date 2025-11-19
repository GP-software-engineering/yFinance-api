# core_services.py
import json5 as json
import logging
import sys
import os
from collections import Counter

# --- Config Path Logic ---
# Check environment variable or fallback to 'config.json' in current directory
CONFIG_PATH = os.environ.get("YFINANCE_API_CONFIG", "config.json")

# --- Helper Functions ---

def ensure_directory_exists(file_path):
    """
    Creates the parent directory for a file if it doesn't exist.
    Handles paths without a directory component correctly (e.g., 'activity.log').
    """
    if not file_path:
        return
    directory = os.path.dirname(file_path)
    # Create directory only if the path implies one (non-empty string)
    if directory and not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as e:
            print(f"Warning: Could not create directory '{directory}': {e}", file=sys.stderr)

def load_config(config_path):
    """Loads configuration, handling json5 and missing files."""
    if not os.path.exists(config_path):
        print(f"FATAL ERROR: Configuration file '{config_path}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        # Catching generic Exception here covers ValueError (json5) and others
        print(f"FATAL ERROR: Configuration file '{config_path}' error: {e}", file=sys.stderr)
        sys.exit(1)

def setup_logging(log_file):
    """Configures the logger, ensuring the target directory exists."""
    ensure_directory_exists(log_file)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file) if log_file else logging.StreamHandler(sys.stdout),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def load_ip_counts(path):
    """Loads IP counters. Creates directory if missing. Returns empty if file missing."""
    ensure_directory_exists(path)

    try:
        with open(path, "r") as f:
            return Counter(json.load(f))
    # FIX: json5 raises ValueError on decode errors, not JSONDecodeError
    except (FileNotFoundError, ValueError, TypeError):
        # If file doesn't exist or is corrupted, start fresh
        return Counter()

def save_ip_counts(path, counts):
    """Saves IP counters to disk."""
    if not path:
        return
    
    ensure_directory_exists(path)
    
    try:
        with open(path, "w") as f:
            json.dump(counts, f, indent=4)
    except IOError as e:
        logger.error(f"Could not save IP counts to {path}: {e}")

# --- Initialization ---

# 1. Load Config
config = load_config(CONFIG_PATH)

# 2. Extract Sections
server_config = config.get("server", {})
logging_config = config.get("logging", {})
cache_config = config.get("caching", {})

# 3. Setup Logging
log_file_path = logging_config.get("main_log_file", "logs/activity.log")
logger = setup_logging(log_file_path)

# 4. Load IP Counts
ip_counts_path = logging_config.get("ip_counts_file", "logs/ip_counts.json")
ip_counts = load_ip_counts(ip_counts_path)

logger.info(f"Core services initialized. Config loaded from: {CONFIG_PATH}")