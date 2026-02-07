"""
Output manager for handling data transmission to RC vehicles.
Manages different output drivers (serial, HTTP, debug, etc.)
"""

import os
import json
from typing import Dict, Any, Optional
from .drivers import BaseDriver, SerialDriver, HttpDriver, DebugDriver, UdpDriver


class OutputManager:
    """
    Manager for output drivers.
    Handles switching between different output methods and sending data.
    """
    
    AVAILABLE_DRIVERS = {
        'serial': SerialDriver,
        'http': HttpDriver,
        'debug': DebugDriver,
        'udp': UdpDriver
    }
    
    def __init__(self, driver_type: str = 'http', custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize output manager with a specific driver.
        
        Args:
            driver_type: Type of driver ('serial', 'http'). Defaults to 'http'
            custom_config: Custom configuration dictionary. If None, loads from driver's config file
            
        Raises:
            ValueError: If driver type is not recognized
        """
        if driver_type not in self.AVAILABLE_DRIVERS:
            raise ValueError(
                f"Unknown driver type: {driver_type}. "
                f"Available: {list(self.AVAILABLE_DRIVERS.keys())}"
            )
        
        self.driver_type = driver_type
        self.driver: Optional[BaseDriver] = self.AVAILABLE_DRIVERS[driver_type](custom_config)
        
    def connect(self) -> bool:
        """
        Connect to the output device.
        
        Returns:
            True if connection successful, False otherwise
        """
        return self.driver.connect()
    
    def disconnect(self) -> bool:
        """
        Disconnect from the output device.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        return self.driver.disconnect()
    
    def send_data(self, data: Dict[str, Any]) -> bool:
        """
        Send data to the RC vehicle.
        
        Args:
            data: Dictionary with control values
                  Expected keys: 'steering', 'throttle', 'brake', 'shift_up', 'shift_down'
        
        Returns:
            True if data sent successfully, False otherwise
        """
        return self.driver.send_data(data)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current driver status.
        
        Returns:
            Status dictionary
        """
        return self.driver.get_status()
    
    def switch_driver(self, driver_type: str, custom_config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Switch to a different output driver.
        
        Args:
            driver_type: Type of driver to switch to
            custom_config: Custom configuration for the new driver. If None, loads from config file
            
        Returns:
            True if switch successful, False otherwise
        """
        try:
            # Disconnect from current driver
            if self.driver.connected:
                self.driver.disconnect()
            
            # Create new driver
            if driver_type not in self.AVAILABLE_DRIVERS:
                return False
            
            self.driver_type = driver_type
            self.driver = self.AVAILABLE_DRIVERS[driver_type](custom_config)
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def get_available_drivers() -> list:
        """
        Get list of available driver types.
        
        Returns:
            List of driver type names
        """
        return list(OutputManager.AVAILABLE_DRIVERS.keys())
    
    @staticmethod
    def load_driver_config(driver_type: str) -> Dict[str, Any]:
        """
        Load configuration for a specific driver from its config file.
        
        Args:
            driver_type: Type of driver ('serial', 'http', 'debug')
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file not found
            ValueError: If driver type is unknown
        """
        if driver_type == 'serial':
            return SerialDriver._load_config_file()
        elif driver_type == 'http':
            return HttpDriver._load_config_file()
        elif driver_type == 'debug':
            return DebugDriver._load_config_file()
        else:
            raise ValueError(f"Unknown driver type: {driver_type}")
    
    @staticmethod
    def save_driver_config(driver_type: str, config: Dict[str, Any]) -> bool:
        """
        Save configuration for a specific driver to its config file.
        , 'debug')
            config: Configuration dictionary to save
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            if driver_type == 'serial':
                config_file = SerialDriver.CONFIG_FILE
            elif driver_type == 'http':
                config_file = HttpDriver.CONFIG_FILE
            elif driver_type == 'debug':
                config_file = DebugDriver.CONFIG_FILE
            elif driver_type == 'http':
                config_file = HttpDriver.CONFIG_FILE
            else:
                return False
            
            # Determine config file path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, 'configs', config_file)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            return True
            
        except Exception:
            return False
