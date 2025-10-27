# -*- coding: utf-8 -*-
"""
Configuration loader utility for the ERMES QGIS plugin.
Loads configuration from config.yml file.
"""
import os
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    import json
from typing import Dict, Any


class ConfigLoader:
    """Singleton class to load and manage plugin configuration."""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.yml file."""
        try:
            # Get the plugin root directory
            plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(plugin_dir, "config.yml")
            
            if not os.path.exists(config_path):
                raise FileNotFoundError(
                    f"Configuration file not found: {config_path}. "
                    "Please ensure config.yml exists in the plugin root directory."
                )
            
            with open(config_path, 'r', encoding='utf-8') as f:
                if YAML_AVAILABLE:
                    config = yaml.safe_load(f)
                else:
                    # Fallback to JSON parsing if YAML is not available
                    import json
                    config = json.load(f)
            
            if config is None:
                raise ValueError("Configuration file is empty or invalid.")
            
            return config
        
        except (ValueError, FileNotFoundError) as e:
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            error_type = "YAML" if YAML_AVAILABLE else "JSON"
            raise RuntimeError(f"Failed to load {error_type} configuration: {e}")
    
    @property
    def api_base_url(self) -> str:
        """Get the API base URL."""
        return self._config.get('api', {}).get('base_url', '')
    
    @property
    def api_endpoints(self) -> Dict[str, str]:
        """Get API endpoints."""
        return self._config.get('api', {}).get('endpoints', {})
    
    @property
    def token_lifetime_minutes(self) -> int:
        """Get token lifetime in minutes."""
        return self._config.get('token', {}).get('lifetime_minutes', 6000)
    
    @property
    def token_validation_interval_ms(self) -> int:
        """Get token validation interval in milliseconds."""
        return self._config.get('token', {}).get('validation_interval_ms', 60000)
    
    @property
    def token_expiration_buffer_minutes(self) -> int:
        """Get token expiration buffer time in minutes."""
        return self._config.get('token', {}).get('expiration_buffer_minutes', 5)
    
    @property
    def token_api_validation_timeout(self) -> int:
        """Get API validation timeout in seconds."""
        return self._config.get('token', {}).get('api_validation_timeout', 10)
    
    @property
    def polling_interval_seconds(self) -> int:
        """Get polling interval in seconds."""
        return self._config.get('polling', {}).get('interval_seconds', 1)
    
    @property
    def polling_error_sleep_seconds(self) -> int:
        """Get error sleep time in seconds."""
        return self._config.get('polling', {}).get('error_sleep_seconds', 5)
    
    @property
    def pipelines(self) -> list:
        """Get pipeline definitions."""
        return self._config.get('pipelines', [])
    
    def get_pipeline_info(self) -> Dict[str, Dict[str, str]]:
        """
        Get pipeline information as a dictionary keyed by pipeline name.
        Returns format: {name: {pipeline, description, image}}
        """
        pipelines = self.pipelines
        return {p['name']: {
            'pipeline': p['pipeline'],
            'description': p['description'],
            'image': p['image']
        } for p in pipelines}
    
    def get_pipeline_map(self) -> Dict[str, str]:
        """
        Get pipeline map for backward compatibility.
        Returns format: {name: pipeline_id}
        """
        pipeline_info = self.get_pipeline_info()
        return {k: v['pipeline'] for k, v in pipeline_info.items()}
    
    @property
    def image_type_map(self) -> Dict[str, str]:
        """Get image type mapping."""
        return self._config.get('image_types', {})
    
    @property
    def style_root(self) -> str:
        """Get style root directory."""
        return self._config.get('styles', {}).get('root_directory', 'styles')
    
    @property
    def style_map(self) -> Dict[str, str]:
        """Get style mapping."""
        return self._config.get('styles', {}).get('mappings', {})
    
    @property
    def credentials_file(self) -> str:
        """Get credentials file name."""
        return self._config.get('paths', {}).get('credentials_file', '.credentials')
    
    @property
    def images_directory(self) -> str:
        """Get images directory path."""
        return self._config.get('paths', {}).get('images_directory', 'images')
    
    @property
    def default_tab_index(self) -> int:
        """Get default tab index."""
        return self._config.get('ui', {}).get('default_tab_index', 0)
    
    @property
    def tab_states(self) -> list:
        """Get tab enabled states."""
        return self._config.get('ui', {}).get('tab_states', [])
    
    @property
    def processing_chunk_size(self) -> int:
        """Get processing chunk size."""
        return self._config.get('processing', {}).get('chunk_size', 8192)
    
    @property
    def temp_dir_prefix(self) -> str:
        """Get temporary directory prefix."""
        return self._config.get('processing', {}).get('temp_dir_prefix', 'qgis_ermes_')
    
    @property
    def cache_dir_name(self) -> str:
        """Get cache directory name."""
        return self._config.get('processing', {}).get('cache_dir_name', 'ermes_qgis')

