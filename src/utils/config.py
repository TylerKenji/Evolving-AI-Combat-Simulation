"""
Configuration Management for Battle AI
Task 1.2.4: Design configuration management system
"""

import yaml
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class SimulationConfig:
    """Configuration for simulation parameters."""
    max_agents: int = 10
    battlefield_width: int = 800
    battlefield_height: int = 600
    time_step: float = 0.1
    max_simulation_time: float = 300.0
    fps: int = 60


@dataclass
class AgentConfig:
    """Configuration for agent parameters."""
    default_health: int = 100
    default_speed: float = 50.0
    collision_radius: float = 10.0
    vision_range: float = 150.0


@dataclass
class VisualizationConfig:
    """Configuration for visualization parameters."""
    window_width: int = 1024
    window_height: int = 768
    background_color: list = field(default_factory=lambda: [50, 50, 50])
    agent_colors: Dict[str, list] = field(default_factory=lambda: {
        'default': [100, 150, 255],
        'team1': [255, 100, 100],
        'team2': [100, 255, 100],
        'dead': [128, 128, 128]
    })


@dataclass
class LoggingConfig:
    """Configuration for logging parameters."""
    level: str = "INFO"
    file: str = "logs/battle_ai.log"
    console: bool = True
    directory: str = "logs"
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5


@dataclass
class DevelopmentConfig:
    """Configuration for development parameters."""
    debug_mode: bool = True
    show_fps: bool = True
    show_agent_info: bool = True


@dataclass
class Config:
    """Main configuration class containing all sub-configurations."""
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    agents: AgentConfig = field(default_factory=AgentConfig)
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    development: DevelopmentConfig = field(default_factory=DevelopmentConfig)
    
    @classmethod
    def load_from_file(cls, config_path: str) -> 'Config':
        """Load configuration from YAML file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as file:
            config_data = yaml.safe_load(file)
        
        return cls.from_dict(config_data)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Config':
        """Create configuration from dictionary."""
        config = cls()
        
        if 'simulation' in config_dict:
            config.simulation = SimulationConfig(**config_dict['simulation'])
        
        if 'agents' in config_dict:
            config.agents = AgentConfig(**config_dict['agents'])
        
        if 'visualization' in config_dict:
            config.visualization = VisualizationConfig(**config_dict['visualization'])
        
        if 'logging' in config_dict:
            config.logging = LoggingConfig(**config_dict['logging'])
        
        if 'development' in config_dict:
            config.development = DevelopmentConfig(**config_dict['development'])
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'simulation': self.simulation.__dict__,
            'agents': self.agents.__dict__,
            'visualization': self.visualization.__dict__,
            'logging': self.logging.__dict__,
            'development': self.development.__dict__
        }
    
    def save_to_file(self, config_path: str) -> None:
        """Save configuration to YAML file."""
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as file:
            yaml.dump(self.to_dict(), file, default_flow_style=False, indent=2)
    
    def validate(self) -> bool:
        """Validate configuration values."""
        errors = []
        
        # Simulation validation
        if self.simulation.max_agents <= 0:
            errors.append("max_agents must be positive")
        if self.simulation.battlefield_width <= 0:
            errors.append("battlefield_width must be positive")
        if self.simulation.battlefield_height <= 0:
            errors.append("battlefield_height must be positive")
        if self.simulation.time_step <= 0:
            errors.append("time_step must be positive")
        if self.simulation.fps <= 0:
            errors.append("fps must be positive")
        
        # Agent validation
        if self.agents.default_health <= 0:
            errors.append("default_health must be positive")
        if self.agents.default_speed < 0:
            errors.append("default_speed must be non-negative")
        if self.agents.collision_radius <= 0:
            errors.append("collision_radius must be positive")
        if self.agents.vision_range < 0:
            errors.append("vision_range must be non-negative")
        
        # Visualization validation
        if self.visualization.window_width <= 0:
            errors.append("window_width must be positive")
        if self.visualization.window_height <= 0:
            errors.append("window_height must be positive")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
        
        return True


class ConfigManager:
    """Singleton configuration manager."""
    
    _instance: Optional['ConfigManager'] = None
    _config: Optional[Config] = None
    
    def __new__(cls) -> 'ConfigManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_config(self, config_path: str = "config/default.yaml") -> Config:
        """Load configuration from file."""
        try:
            self._config = Config.load_from_file(config_path)
            self._config.validate()
            return self._config
        except FileNotFoundError:
            print(f"Warning: Config file {config_path} not found, using defaults")
            self._config = Config()
            return self._config
    
    def get_config(self) -> Config:
        """Get current configuration."""
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def reload_config(self, config_path: str = "config/default.yaml") -> Config:
        """Reload configuration from file."""
        return self.load_config(config_path)


# Global configuration manager instance
config_manager = ConfigManager()
