"""Logging utility for the detection system."""

import logging
import os
from datetime import datetime
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }
    
    def format(self, record):
        """Format log record with colors."""
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)


class SystemLogger:
    """System-wide logger for the detection system."""
    
    def __init__(self, log_dir="./logs", log_level=logging.INFO):
        """Initialize logger.
        
        Args:
            log_dir: Directory for log files
            log_level: Logging level
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger('ZeroDayDetection')
        self.logger.setLevel(log_level)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            # Console handler with colors
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
            
            # File handler
            log_file = self.log_dir / f"detection_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def get_logger(self):
        """Get the logger instance."""
        return self.logger

