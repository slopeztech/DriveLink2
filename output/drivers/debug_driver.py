"""
Debug output driver for displaying control data in the GUI.
Stores all input data for real-time display.
"""

import json
import os
from typing import Dict, Any, Optional
from .base_driver import BaseDriver


class DebugDriver(BaseDriver):
    """
    Debug output driver that stores control data for GUI display.
    Useful for testing input mapping and debugging without RC hardware.
    """
    
    CONFIG_FILE = "debug.json"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize debug driver.
        
        Args:
            config: Configuration dictionary (optional, loads from debug.json if None)
        """
        if config is None:
            config = self._load_config_file()
        
        super().__init__(config)
        self.error_message = None
        self._print_count = 0
        self.last_data = {}
    
    @staticmethod
    def _load_config_file() -> Dict[str, Any]:
        """Load debug configuration from JSON file."""
        driver_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(os.path.dirname(driver_dir), 'configs')
        config_path = os.path.join(config_dir, DebugDriver.CONFIG_FILE)
        
        if not os.path.exists(config_path):
            # Return default config if file doesn't exist
            return {"driver_type": "debug", "display_in_gui": True}
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def connect(self) -> bool:
        """Establish debug connection."""
        self.connected = True
        self.error_message = None
        self.last_data = {}
        print("\n" + "="*60)
        print("DEBUG DRIVER CONNECTED - Data will display in GUI")
        print("="*60 + "\n")
        return True
    
    def disconnect(self) -> bool:
        """Close debug connection."""
        self.connected = False
        self.error_message = None
        print("\n" + "="*60)
        print("DEBUG DRIVER DISCONNECTED")
        print(f"Total frames received: {self._print_count}")
        print("="*60 + "\n")
        return True
    
    def send_data(self, data: Dict[str, Any]) -> bool:
        """Store control data for GUI display."""
        if not self.connected:
            self.error_message = "Debug driver not connected"
            return False
        
        try:
            self._print_count += 1
            self.last_data = data.copy()
            return True
        except Exception as e:
            self.error_message = str(e)
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get debug driver status."""
        return {
            'type': 'debug',
            'connected': self.connected,
            'frames_received': self._print_count,
            'last_data': self.last_data,
            'error': self.error_message
        }
