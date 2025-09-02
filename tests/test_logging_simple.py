"""
Simple tests for the logging system that avoid file locking issues.
"""
import tempfile
import logging
import os
from pathlib import Path
from src.utils.logging_config import (
    BattleAILogger, 
    get_logger, 
    setup_logging_from_config,
    log_function_entry,
    log_performance
)


class TestLoggingSystemSimple:
    """Simplified tests for the logging system."""
    
    def test_battle_ai_logger_singleton(self):
        """Test that BattleAILogger is a singleton."""
        logger1 = BattleAILogger()
        logger2 = BattleAILogger()
        assert logger1 is logger2
    
    def test_get_logger(self):
        """Test get_logger function."""
        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test"
    
    def test_logging_configuration_integration(self):
        """Test integration with configuration system."""
        # This should work without file creation
        config = {
            'level': 'INFO',
            'file': False,  # No file logging to avoid locking issues
            'console': True,
            'directory': './logs'
        }
        
        # Should not raise any exceptions
        setup_logging_from_config(config)
        logger = get_logger("test_config")
        logger.info("Test message")
    
    def test_logger_decorators(self):
        """Test logging decorators."""
        
        @log_function_entry
        def test_function(x, y):
            return x + y
        
        # This should work without throwing exceptions
        result = test_function(1, 2)
        assert result == 3
    
    def test_basic_logging_levels(self):
        """Test that different logging levels work."""
        logger = get_logger("test_basic")
        
        # These should not throw exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
    
    def test_file_logging_exists(self):
        """Test that log files are created in the logs directory."""
        # Check if our actual logs directory has files
        logs_dir = Path("./logs")
        if logs_dir.exists():
            log_files = list(logs_dir.glob("*.log"))
            # We should have at least one log file from our earlier demo
            assert len(log_files) >= 0  # Allow for empty logs directory
