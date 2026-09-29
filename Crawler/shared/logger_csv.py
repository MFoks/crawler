import csv
import os
from datetime import datetime

LOGS_DIR = "logs"
LOG_FILE_PATH = None  # Dynamic per run

def init_log_file(domain_url: str):
    """Create a new log file per session and store the path globally."""
    global LOG_FILE_PATH
    os.makedirs(LOGS_DIR, exist_ok=True)

    domain = domain_url.replace("https://", "").replace("http://", "").split("/")[0]
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"{domain}_{timestamp}.csv"
    LOG_FILE_PATH = os.path.join(LOGS_DIR, filename)

    # Write header with timestamp
    with open(LOG_FILE_PATH, mode="w", newline="", encoding="utf-8") as log_file:
        writer = csv.writer(log_file)
        writer.writerow([f"# Crawler run for {domain} on {timestamp}"])


def log_to_csv(source: str, log_message: str):
    """Append a log message to the current session file with timestamp and source label."""
    if not LOG_FILE_PATH:
        raise RuntimeError("Logger not initialized. Call init_log_file(domain_url) first.")

    with open(LOG_FILE_PATH, mode="a", newline="", encoding="utf-8") as log_file:
        writer = csv.writer(log_file)
        writer.writerow([source, log_message])


def get_current_log_file() -> str:
    """Expose current log file path for live reading."""
    if not LOG_FILE_PATH:
        raise RuntimeError("Logger not initialized. Call init_log_file(domain_url) first.")
    return LOG_FILE_PATH
