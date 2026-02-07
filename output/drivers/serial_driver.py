"""
Serial port output driver for communicating with RC vehicles.
Sends control data over USB serial connection.
"""

import serial
import json
import os
from typing import Dict, Any, Optional
from .base_driver import BaseDriver


class SerialDriver(BaseDriver):
    """
    Serial port output driver for RC vehicle control.
    """
    
    CONFIG_FILE = "serial.json"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize serial driver.
        
        Args:
            config: Configuration dictionary. If None, loads from serial.json
                    Expected keys:
                    - 'port': Serial port name (e.g., 'COM3', '/dev/ttyUSB0')
                    - 'baudrate': Baud rate (default: 9600)
                    - 'timeout': Read/write timeout in seconds (default: 1.0)
        """
        # Load config from file if not provided
        if config is None:
            config = self._load_config_file()
        
        super().__init__(config)
        self.port = config.get('port')
        self.baudrate = config.get('baudrate', 9600)
        self.timeout = config.get('timeout', 1.0)
        self.serial_connection = None
        self.error_message = None
    
    @staticmethod
    def _load_config_file() -> Dict[str, Any]:
        """
        Load serial configuration from JSON file.
        
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file not found
        """
        # Determine config file path
        driver_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(os.path.dirname(driver_dir), 'configs')
        config_path = os.path.join(config_dir, SerialDriver.CONFIG_FILE)
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Serial config file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
        
    def connect(self) -> bool:
        """
        Establish serial connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not self.port:
                self.error_message = "Serial port not specified"
                return False
            
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            self.connected = True
            self.error_message = None
            return True
            
        except serial.SerialException as e:
            self.error_message = str(e)
            self.connected = False
            return False
    
    def disconnect(self) -> bool:
        """
        Close serial connection.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                self.connected = False
                self.error_message = None
                return True
            return True
            
        except Exception as e:
            self.error_message = str(e)
            return False
    
    def send_data(self, data: Dict[str, Any]) -> bool:
        """
        Send control data over serial connection.
        
        Args:
            data: Dictionary with control values
        
        Returns:
            True if data sent successfully, False otherwise
        """
        if not self.connected or not self.serial_connection:
            self.error_message = "Serial connection not established"
            return False
        
        try:
            # Format data as JSON string
            json_data = json.dumps(data)
            # Add newline as message delimiter
            message = json_data + '\n'
            
            # Send data
            self.serial_connection.write(message.encode())
            return True
            
        except Exception as e:
            self.error_message = str(e)
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get serial driver status.
        
        Returns:
            Status dictionary
        """
        return {
            'type': 'serial',
            'connected': self.connected,
            'port': self.port,
            'baudrate': self.baudrate,
            'error': self.error_message
        }
    
    @staticmethod
    def get_available_ports() -> list:
        """
        Get list of available serial ports.
        
        Returns:
            List of available port names
        """
        try:
            import serial.tools.list_ports
            ports = []
            for port in serial.tools.list_ports.comports():
                ports.append(port.device)
            return ports
        except Exception:
            return []
