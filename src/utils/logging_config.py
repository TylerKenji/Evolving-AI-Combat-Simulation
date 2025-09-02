"""
Logging Configuration for Battle AI
Task 1.1.6: Set up logging configuration
"""

import logging
import logging.config
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import colorlog


class BattleAILogger:
    """
    Centralized logging system for Battle AI project.
    Supports both console and file logging with color coding and structured formats.
    """
    
    _instance: Optional['BattleAILogger'] = None
    _configured: bool = False
    
    def __new__(cls) -> 'BattleAILogger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._configured:
            self.setup_logging()
            self._configured = True
    
    def setup_logging(self, 
                     log_level: str = "INFO",
                     log_to_file: bool = True,
                     log_to_console: bool = True,
                     log_dir: str = "logs") -> None:
        """
        Configure logging system with both console and file handlers.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_file: Whether to log to files
            log_to_console: Whether to log to console
            log_dir: Directory for log files
        """
        
        # Create logs directory if it doesn't exist
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        # Generate timestamp for log files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Define log file paths
        main_log_file = log_path / f"battle_ai_{timestamp}.log"
        error_log_file = log_path / "battle_ai_errors.log"
        debug_log_file = log_path / "battle_ai_debug.log"
        
        # Color formatter for console
        console_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        
        # File formatter (more detailed)
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)-20s | %(filename)s:%(lineno)d | %(funcName)s() | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Simple formatter for error file
        error_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(console_formatter)
            console_handler.setLevel(getattr(logging, log_level.upper()))
            root_logger.addHandler(console_handler)
        
        # File handlers
        if log_to_file:
            # Main log file (all messages)
            file_handler = logging.FileHandler(main_log_file, encoding='utf-8')
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(logging.DEBUG)
            root_logger.addHandler(file_handler)
            
            # Error log file (errors and above only)
            error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
            error_handler.setFormatter(error_formatter)
            error_handler.setLevel(logging.ERROR)
            root_logger.addHandler(error_handler)
            
            # Debug log file (debug and above, for development)
            debug_handler = logging.FileHandler(debug_log_file, encoding='utf-8')
            debug_handler.setFormatter(file_formatter)
            debug_handler.setLevel(logging.DEBUG)
            root_logger.addHandler(debug_handler)
        
        # Log the configuration
        logger = logging.getLogger(__name__)
        logger.info("✅ Logging system initialized")
        logger.info(f"📝 Log level: {log_level}")
        logger.info(f"📁 Log directory: {log_path.absolute()}")
        if log_to_file:
            logger.info(f"📄 Main log: {main_log_file}")
            logger.info(f"🚨 Error log: {error_log_file}")
            logger.info(f"🔍 Debug log: {debug_log_file}")
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Get a logger instance for a specific module.
        
        Args:
            name: Logger name (typically __name__)
            
        Returns:
            Configured logger instance
        """
        return logging.getLogger(name)
    
    @staticmethod
    def log_system_info():
        """Log basic system information for debugging."""
        import sys
        import platform
        
        logger = logging.getLogger(__name__)
        logger.info("🖥️ System Information:")
        logger.info(f"  Python: {sys.version}")
        logger.info(f"  Platform: {platform.platform()}")
        logger.info(f"  Architecture: {platform.architecture()}")
        logger.info(f"  Working Directory: {os.getcwd()}")
    
    @staticmethod
    def log_config_info(config):
        """Log configuration information."""
        logger = logging.getLogger(__name__)
        logger.info("⚙️ Configuration loaded:")
        logger.info(f"  Max Agents: {config.simulation.max_agents}")
        logger.info(f"  Battlefield: {config.simulation.battlefield_width}x{config.simulation.battlefield_height}")
        logger.info(f"  Time Step: {config.simulation.time_step}s")
        logger.info(f"  FPS: {config.simulation.fps}")


def setup_logging_from_config(config_dict: Optional[dict] = None):
    """
    Set up logging from configuration dictionary or default settings.
    
    Args:
        config_dict: Configuration dictionary with logging settings
    """
    if config_dict is None:
        config_dict = {
            'level': 'INFO',
            'file': True,
            'console': True,
            'directory': 'logs'
        }
    
    logger_instance = BattleAILogger()
    logger_instance.setup_logging(
        log_level=config_dict.get('level', 'INFO'),
        log_to_file=config_dict.get('file', True),
        log_to_console=config_dict.get('console', True),
        log_dir=config_dict.get('directory', 'logs')
    )
    
    return logger_instance


# Convenience functions for quick logger access
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance. Initialize logging if not already done."""
    if not BattleAILogger._configured:
        BattleAILogger()
    
    if name is None:
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get('__name__', 'battle_ai')
        else:
            name = 'battle_ai'
    
    return logging.getLogger(name)


def log_function_entry(func):
    """Decorator to log function entry and exit."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"🔵 Entering {func.__name__}() with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"🟢 Exiting {func.__name__}() successfully")
            return result
        except Exception as e:
            logger.error(f"🔴 Error in {func.__name__}(): {e}")
            raise
    return wrapper


def log_performance(func):
    """Decorator to log function performance."""
    import time
    
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"⏱️ {func.__name__}() executed in {execution_time:.4f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"⏱️ {func.__name__}() failed after {execution_time:.4f}s: {e}")
            raise
    return wrapper


# Global logger instance
logger_instance = None

def initialize_logging(config=None):
    """Initialize the global logging system."""
    global logger_instance
    if logger_instance is None:
        logger_instance = setup_logging_from_config(config)
    return logger_instance
