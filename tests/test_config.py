"""
Test suite for Configuration system
Task 1.9.1: Create unit tests for core classes
"""

import pytest
import tempfile
import os
from src.utils.config import Config, SimulationConfig, AgentConfig, ConfigManager


class TestConfig:
    """Test cases for configuration system."""
    
    def test_default_config(self):
        """Test default configuration creation."""
        config = Config()
        
        assert config.simulation.max_agents == 10
        assert config.agents.default_health == 100
        assert config.visualization.window_width == 1024
        assert config.logging.level == "INFO"
        assert config.development.debug_mode is True
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = Config()
        assert config.validate() is True
        
        # Test invalid configuration
        config.simulation.max_agents = -1
        with pytest.raises(ValueError):
            config.validate()
    
    def test_config_from_dict(self):
        """Test configuration creation from dictionary."""
        config_dict = {
            'simulation': {'max_agents': 20, 'fps': 30},
            'agents': {'default_health': 150}
        }
        
        config = Config.from_dict(config_dict)
        assert config.simulation.max_agents == 20
        assert config.simulation.fps == 30
        assert config.agents.default_health == 150
        # Other values should remain default
        assert config.visualization.window_width == 1024
    
    def test_config_to_dict(self):
        """Test configuration conversion to dictionary."""
        config = Config()
        config_dict = config.to_dict()
        
        assert 'simulation' in config_dict
        assert 'agents' in config_dict
        assert 'visualization' in config_dict
        assert 'logging' in config_dict
        assert 'development' in config_dict
    
    def test_config_file_operations(self):
        """Test configuration file save/load operations."""
        config = Config()
        config.simulation.max_agents = 25
        config.agents.default_health = 200
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            # Save configuration
            config.save_to_file(temp_path)
            assert os.path.exists(temp_path)
            
            # Load configuration
            loaded_config = Config.load_from_file(temp_path)
            assert loaded_config.simulation.max_agents == 25
            assert loaded_config.agents.default_health == 200
            
        finally:
            os.unlink(temp_path)
    
    def test_config_manager_singleton(self):
        """Test ConfigManager singleton behavior."""
        manager1 = ConfigManager()
        manager2 = ConfigManager()
        
        assert manager1 is manager2
    
    def test_config_manager_operations(self):
        """Test ConfigManager operations."""
        manager = ConfigManager()
        
        # Test getting default config
        config = manager.get_config()
        assert isinstance(config, Config)
        
        # Test that subsequent calls return the same config
        config2 = manager.get_config()
        assert config is config2
