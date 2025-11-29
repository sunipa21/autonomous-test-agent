import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Create logs directory if it doesn't exist
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Crash report directory
CRASH_DIR = os.path.join(LOG_DIR, "crashes")
os.makedirs(CRASH_DIR, exist_ok=True)

def setup_logger(name="app"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (General logs)
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "app.log"),
        maxBytes=10*1024*1024, # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def log_crash(e: Exception, context: str = ""):
    """
    Logs a crash with full traceback to a separate timestamped file.
    """
    import traceback
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"crash_{timestamp}.txt"
    filepath = os.path.join(CRASH_DIR, filename)
    
    with open(filepath, "w") as f:
        f.write(f"Timestamp: {datetime.now()}\n")
        f.write(f"Context: {context}\n")
        f.write(f"Exception: {str(e)}\n")
        f.write("-" * 50 + "\n")
        f.write(traceback.format_exc())
    
    return filepath
