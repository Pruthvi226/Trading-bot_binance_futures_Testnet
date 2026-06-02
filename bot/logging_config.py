"""
Logging configuration for Trading Bot
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(log_file=None):
    """
    Configure logging for the trading bot.
    
    Args:
        log_file (str): Path to the log file
        
    Returns:
        logging.Logger: Configured logger instance
    """
    log_file = log_file or os.getenv("TRADING_BOT_LOG_FILE", "logs/trading_bot.log")

    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.DEBUG)
    
    # Create file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    
    # Set log level
    file_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add formatter to handler
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.propagate = False
    
    return logger
