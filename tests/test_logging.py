"""
Test suite for Logging system
Task 1.1.6: Set up logging configuration - Testing
"""

import pytest
import tempfile
import os
import logging
from pathlib import Path
from src.utils.logging_config import BattleAILogger, get_logger, setup_logging_from_config


class TestLoggingSystem:
    """Test cases for logging system."""
    
    def test_battle_ai_logger_singleton(self):
        """Test that BattleAILogger is a singleton."""
        logger1 = BattleAILogger()
        logger2 = BattleAILogger()
        
        assert logger1 is logger2
    
    def test_get_logger(self):
        """Test logger creation and retrieval."""
        logger = get_logger("test_module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
    
    def test_logging_levels(self):
        """Test different logging levels."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup logging to temporary directory
            config = {
                'level': 'DEBUG',
                'file': True,
                'console': False,
                'directory': temp_dir
            }
            
            setup_logging_from_config(config)
            logger = get_logger("test_levels")
            
            # Test all logging levels
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")
            
            # Properly shutdown logging to close file handles
            logging.shutdown()
            
            # Check that log files were created
            log_files = list(Path(temp_dir).glob("*.log"))
            assert len(log_files) > 0
    
    def test_file_logging(self):
        """Test file logging functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                'level': 'INFO',
                'file': True,
                'console': False,
                'directory': temp_dir
            }
            
            setup_logging_from_config(config)
            logger = get_logger("test_file")
            
            test_message = "Test file logging message"
            logger.info(test_message)
            
            # Properly shutdown logging to close file handles
            logging.shutdown()
            
            # Check that log file contains our message
            log_files = list(Path(temp_dir).glob("battle_ai_*.log"))
            assert len(log_files) > 0
            
            with open(log_files[0], 'r', encoding='utf-8') as f:
                content = f.read()
                assert test_message in content
    
    def test_error_logging(self):
        """Test error-specific logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                'level': 'DEBUG',
                'file': True,
                'console': False,
                'directory': temp_dir
            }
            
            setup_logging_from_config(config)
            logger = get_logger("test_error")
            
            error_message = "Test error logging"
            logger.error(error_message)
            
            # Properly shutdown logging to close file handles
            logging.shutdown()
            
            # Check error log file
            error_log = Path(temp_dir) / "battle_ai_errors.log"
            assert error_log.exists()
            
            with open(error_log, 'r', encoding='utf-8') as f:
                content = f.read()
                assert error_message in content
    
    def test_logging_configuration_integration(self):
        """Test integration with configuration system."""
        from src.utils.config import Config
        
        config = Config()
        assert config.logging.level == "INFO"
        assert config.logging.console is True
        assert config.logging.directory == "logs"
    
    def test_logger_decorators(self):
        """Test logging decorators."""
        # Setup a clean logging environment for this test
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                'level': 'DEBUG',
                'file': True,
                'console': False,
                'directory': temp_dir
            }
            
            setup_logging_from_config(config)
            
            from src.utils.logging_config import log_function_entry, log_performance
            
            @log_function_entry
            @log_performance
            def test_function(x, y):
                return x + y
            
            # This should work without errors
            result = test_function(1, 2)
            assert result == 3
            
            # Properly shutdown logging to close file handles
            logging.shutdown()
