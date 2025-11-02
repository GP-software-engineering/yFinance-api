##
# config, logging and counters by IP addresses
#
import json5 as json
import logging
import sys
import os  # <-- Aggiunto
from collections import Counter

# --- Config Path Logic ---
# Get config path from Environment Variable.
# Fallback to local 'config.json' if not set.
CONFIG_PATH = os.environ.get("YFINANCE_API_CONFIG", "config.json")

# ---

def load_config(config_path):
    """Loads configuration from a JSON file."""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"FATAL ERROR: Configuration file '{config_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"FATAL ERROR: Configuration file '{config_path}' is not valid JSON or contains errors: {e}", file=sys.stderr)
        sys.exit(1)

def setup_logging(log_file):
    """Configures the main application logger."""
    # Ensure log directory exists
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create log directory '{log_file}'. {e}", file=sys.stderr)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def load_ip_counts(path):
    """Loads the IP counter file at startup."""
    try:
        with open(path, "r") as f:
            return Counter(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return Counter()

def save_ip_counts(path, counts):
    """Saves the IP counter file."""
    # Ensure directory exists before writing
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(counts, f, indent=4)
    except IOError as e:
        logger.error(f"Could not save IP counts to {path}: {e}")

# --- Initialize and Export Services ---
# These are loaded once when the module is imported
config = load_config(CONFIG_PATH)
logger = setup_logging(config["logging"]["main_log_file"])
ip_counts = load_ip_counts(config["logging"]["ip_counts_file"])

server_config = config["server"]
logging_config = config["logging"]
cache_config = config["caching"]

logger.info(f"Core services initialized. Loading config from: {CONFIG_PATH}")