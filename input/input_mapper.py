"""
Input mapping configuration loader and manager.
Handles loading, validation, and access to input configuration files.
"""

import json
import os
from typing import Dict, Any, Optional


class InputConfig:
    """
    Represents a loaded input configuration with mapped controls.
    """
    
    def __init__(self, config_data: Dict[str, Any]):
        """
        Initialize input configuration from JSON data.
        
        Args:
            config_data: Dictionary containing the configuration
        """
        self.name = config_data.get("mapping_name", "Unknown")
        self.description = config_data.get("description", "")
        self.version = config_data.get("version", "1.0")
        
        self.axes = config_data.get("axes", {})
        self.buttons = config_data.get("buttons", {})
        self.hats = config_data.get("hats", {})
        
    def get_axis_mapping(self, action: str) -> Optional[Dict[str, Any]]:
        """
        Get axis configuration for a specific action.
        
        Args:
            action: Action name (e.g., 'steering', 'throttle', 'brake')
            
        Returns:
            Dictionary with axis configuration or None if not found
        """
        return self.axes.get(action)
    
    def get_button_mapping(self, action: str) -> Optional[Dict[str, Any]]:
        """
        Get button configuration for a specific action.
        
        Args:
            action: Action name (e.g., 'shift_up', 'shift_down')
            
        Returns:
            Dictionary with button configuration or None if not found
        """
        return self.buttons.get(action)
    
    def get_axis_id_for_action(self, action: str) -> Optional[int]:
        """
        Get axis ID for a specific action.
        
        Args:
            action: Action name
            
        Returns:
            Axis ID or None if not found
        """
        mapping = self.get_axis_mapping(action)
        return mapping.get("axis_id") if mapping else None
    
    def get_button_id_for_action(self, action: str) -> Optional[int]:
        """
        Get button ID for a specific action.
        
        Args:
            action: Action name
            
        Returns:
            Button ID or None if not found
        """
        mapping = self.get_button_mapping(action)
        return mapping.get("button_id") if mapping else None
    
    def get_action_for_button(self, button_id: int) -> Optional[str]:
        """
        Get action name for a specific button ID.
        
        Args:
            button_id: Button identifier
            
        Returns:
            Action name or None if not mapped
        """
        for action, config in self.buttons.items():
            if config.get("button_id") == button_id:
                return action
        return None
    
    def get_action_for_axis(self, axis_id: int) -> Optional[str]:
        """
        Get action name for a specific axis ID.
        
        Args:
            axis_id: Axis identifier
            
        Returns:
            Action name or None if not mapped
        """
        for action, config in self.axes.items():
            if config.get("axis_id") == axis_id:
                return action
        return None
    
    def apply_axis_processing(self, action: str, raw_value: float) -> float:
        """
        Apply processing to axis value (deadzone, inversion, sensitivity).
        
        Args:
            action: Action name
            raw_value: Raw axis value from -1 to 1
            
        Returns:
            Processed axis value
        """
        mapping = self.get_axis_mapping(action)
        if not mapping:
            return raw_value
        
        value = raw_value
        
        # Apply deadzone
        deadzone = mapping.get("deadzone", 0.0)
        if abs(value) < deadzone:
            value = 0.0
        
        # Apply inversion
        if mapping.get("inverted", False):
            value = -value
        
        # Apply sensitivity
        sensitivity = mapping.get("sensitivity", 1.0)
        value *= sensitivity
        
        # Clamp to -1 to 1 range
        value = max(-1.0, min(1.0, value))
        
        return value
    
    def __repr__(self):
        return f"<InputConfig: {self.name} v{self.version}>"


class InputMapper:
    """
    Manager for loading and accessing input configuration files.
    """
    
    DEFAULT_CONFIG_FILE = "default_input.json"
    CONFIG_DIR = "input"
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize input mapper.
        
        Args:
            config_path: Path to configuration file. If None, uses default.
        """
        self.config: Optional[InputConfig] = None
        self.config_path = config_path
        
    def load_default_config(self) -> InputConfig:
        """
        Load the default input configuration.
        
        Returns:
            Loaded InputConfig object
            
        Raises:
            FileNotFoundError: If default config file not found
            ValueError: If config file is invalid
        """
        # Determine config directory path
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_dir = os.path.join(script_dir, self.CONFIG_DIR)
        default_path = os.path.join(config_dir, self.DEFAULT_CONFIG_FILE)
        
        return self.load_config(default_path)
    
    def load_config(self, config_path: str) -> InputConfig:
        """
        Load input configuration from a JSON file.
        
        Args:
            config_path: Path to the configuration file or filename only
            
        Returns:
            Loaded InputConfig object
            
        Raises:
            FileNotFoundError: If config file not found
            ValueError: If config file is invalid JSON
        """
        # If path doesn't exist and it's just a filename, try in config directory
        if not os.path.exists(config_path):
            if not os.path.sep in config_path and not '/' in config_path:
                # It's just a filename, try in config directory
                script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                config_dir = os.path.join(script_dir, self.CONFIG_DIR)
                config_path = os.path.join(config_dir, config_path)
            
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.config = InputConfig(config_data)
            self.config_path = config_path
            
            return self.config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def get_config(self) -> Optional[InputConfig]:
        """
        Get the currently loaded configuration.
        
        Returns:
            Current InputConfig or None if not loaded
        """
        return self.config
    
    def save_config(self, output_path: Optional[str] = None):
        """
        Save current configuration to a JSON file.
        
        Args:
            output_path: Path where to save. If None, overwrites current file.
            
        Raises:
            ValueError: If no configuration is loaded
        """
        if not self.config:
            raise ValueError("No configuration loaded to save")
        
        save_path = output_path or self.config_path
        if not save_path:
            raise ValueError("No output path specified")
        
        config_data = {
            "mapping_name": self.config.name,
            "description": self.config.description,
            "version": self.config.version,
            "axes": self.config.axes,
            "buttons": self.config.buttons,
            "hats": self.config.hats
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
    
    def list_available_configs(self) -> list:
        """
        List all available configuration files in the input directory.
        
        Returns:
            List of configuration file names
        """
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_dir = os.path.join(script_dir, self.CONFIG_DIR)
        
        if not os.path.exists(config_dir):
            return []
        
        configs = []
        for filename in os.listdir(config_dir):
            if filename.endswith('.json'):
                configs.append(filename)
        
        return configs
