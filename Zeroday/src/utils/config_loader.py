"""Configuration loader utility."""

import yaml
import os
from pathlib import Path


class ConfigLoader:
    """Load and manage configuration from YAML file."""
    
    def __init__(self, config_path="config.yaml"):
        """Initialize config loader.
        
        Args:
            config_path: Path to configuration YAML file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._create_directories()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            print(f"Warning: Config file {self.config_path} not found. Using defaults.")
            return self._get_default_config()
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            return self._get_default_config()
    
    def _get_default_config(self):
        """Return default configuration."""
        return {
            'detection': {
                'anomaly_threshold': 0.7,
                'behavioral_sensitivity': 0.8,
                'min_confidence': 0.75,
                'enable_ml_detection': True
            },
            'monitoring': {
                'log_paths': [],
                'real_time': True,
                'check_interval': 5,
                'max_log_size': 100
            },
            'alerting': {
                'email_enabled': False,
                'console_enabled': True,
                'min_severity': 'medium'
            },
            'system': {
                'work_dir': './data',
                'log_dir': './logs',
                'model_dir': './models',
                'report_dir': './reports'
            }
        }
    
    def _create_directories(self):
        """Create necessary directories if they don't exist."""
        dirs = [
            self.config['system']['work_dir'],
            self.config['system']['log_dir'],
            self.config['system']['model_dir'],
            self.config['system']['report_dir']
        ]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def get(self, *keys, default=None):
        """Get configuration value by nested keys.
        
        Args:
            *keys: Nested keys to access config value
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default

