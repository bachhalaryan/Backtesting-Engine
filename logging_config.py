import logging
import sys
import os
from datetime import datetime

def setup_logging(log_level=logging.INFO, log_dir="logs"):
    """
    Sets up the root logger to output to both a file and the console.
    If log_dir is provided, the log file will be created within that directory.
    """
    log_formatter = logging.Formatter('%(asctime)s [%(levelname)-5.5s] [%(name)-12.12s] %(message)s')
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG) # Capture all levels at the root

    # --- File Handler ---
    # Create a unique log file name for each backtest run
    log_filename = f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Ensure the log directory exists
    os.makedirs(log_dir, exist_ok=True)
    log_filepath = os.path.join(log_dir, log_filename)

    file_handler = logging.FileHandler(log_filepath)
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG) # Log everything to the file
    root_logger.addHandler(file_handler)

    # --- Console Handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(log_level) # Use the specified level for console output
    root_logger.addHandler(console_handler)

    # Add the log filename to the root logger so it can be retrieved later
    root_logger.log_filename = log_filepath
