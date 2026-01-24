"""
Configuration Manager

Handles loading and managing application configuration.
"""

import yaml
from pathlib import Path
from typing import Any, Dict
import logging


logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_file: str = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to config file (optional)
        """
        if config_file is None:
            # Default config file location
            config_file = Path(__file__).parent.parent.parent / 'config' / 'default_config.yaml'
        
        self.config_file = Path(config_file)
        self.config: Dict = {}
        
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info(f"Configuration loaded from {self.config_file}")
            else:
                logger.warning(f"Config file not found: {self.config_file}, using defaults")
                self.config = self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            'app': {
                'name': 'AutoFolder AI',
                'version': '1.0.0',
                'mode': 'base'
            },
            'safety': {
                'preview_required': True,
                'undo_enabled': True,
                'max_undo_history': 10,
                'dry_run_default': False,
                'never_delete': True
            },
            'organization': {
                'default_folder': 'Downloads',
                'create_folders_if_missing': True,
                'handle_conflicts': 'rename',
                'preserve_timestamps': True,
                'ignore_hidden_files': True
            },
            'ai': {
                'enabled': False,
                'model_path': '../AI Model',
                'use_local_only': True,
                'confidence_threshold': 0.7
            },
            'ui': {
                'theme': 'light',
                'show_preview': True,
                'window_width': 1200,
                'window_height': 800
            },
            'logging': {
                'enabled': True,
                'level': 'INFO',
                'log_file': 'logs/autofolder.log'
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
    
    def save(self):
        """Save configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
