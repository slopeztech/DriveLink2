"""
UDP output driver for communicating with RC vehicles.
Sends control data over UDP packets to ESP32.
"""

import json
import os
import socket
import struct
from typing import Dict, Any, Optional
from .base_driver import BaseDriver


class UdpDriver(BaseDriver):
    """
    UDP output driver for RC vehicle control.
    Sends data to ESP32 in the following format:
    - 2 bytes: power (uint16_t, little endian)
    - 1 byte: direction (uint8_t)
    - 2 bytes: steering (int16_t, little endian)
    """
    
    CONFIG_FILE = "udp.json"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize UDP driver.
        
        Args:
            config: Configuration dictionary. If None, loads from udp.json
                    Expected keys:
                    - 'host': ESP32 IP address (default: 192.168.4.1)
                    - 'port': UDP port (default: 4210)
                    - 'timeout': Socket timeout in seconds (default: 0.5)
        """
        # Load config from file if not provided
        if config is None:
            config = self._load_config_file()
        
        super().__init__(config)
        self.host = config.get('host', '192.168.4.1')
        self.port = config.get('port', 4210)
        self.timeout = config.get('timeout', 0.5)
        self.socket = None
        self.error_message = None
    
    @staticmethod
    def _load_config_file() -> Dict[str, Any]:
        """
        Load UDP configuration from JSON file.
        
        Returns:
            Configuration dictionary
        
        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'configs')
        config_path = os.path.join(config_dir, UdpDriver.CONFIG_FILE)
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"UDP config file not found: {config_path}. "
                "Please create udp.json in output/configs/"
            )
    
    def connect(self) -> bool:
        """
        Create UDP socket for sending data.
        
        Returns:
            True if socket created successfully, False otherwise
        """
        try:
            if self.socket is not None:
                self.disconnect()
            
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(self.timeout)
            
            self.connected = True
            self.error_message = None
            print(f"UDP socket created. Target: {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.error_message = f"Error creating UDP socket: {e}"
            print(self.error_message)
            self.connected = False
            return False
    
    def disconnect(self) -> bool:
        """
        Close UDP socket.
        
        Returns:
            True if socket closed successfully, False otherwise
        """
        try:
            if self.socket is not None:
                self.socket.close()
                self.socket = None
            
            self.connected = False
            print("UDP socket closed")
            return True
            
        except Exception as e:
            self.error_message = f"Error closing UDP socket: {e}"
            print(self.error_message)
            return False
    
    def send_data(self, data: Dict[str, Any]) -> bool:
        """
        Send control data to ESP32 via UDP.
        
        Expected data format:
        {
            'throttle': float (0.0-1.0),
            'steering': float (-1.0 to 1.0),
            'direction': int (0=stop, 1=forward, 2=reverse)
        }
        
        Converts to ESP32 format:
        - throttle * 1000 (0-1000)
        - direction (0, 1, 2)
        - steering * 1000 (-1000 to 1000)
        
        Args:
            data: Dictionary containing control values
            
        Returns:
            True if data sent successfully, False otherwise
        """
        if not self.connected or self.socket is None:
            self.error_message = "UDP socket not connected"
            return False
        
        try:
            # Extract data with default values
            throttle = data.get('throttle', 0.0)
            steering = data.get('steering', 0.0)
            direction = data.get('direction', 0)
            
            # Convert to ESP32 format
            # Power: 0-1000 (uint16_t)
            power = int(throttle * 1000)
            power = max(0, min(1000, power))  # Clamp 0-1000
            
            # Direction: 0, 1, 2 (uint8_t)
            direction = int(direction)
            direction = max(0, min(2, direction))  # Clamp 0-2
            
            # Steering: -1000 to 1000 (int16_t)
            steering = int(steering * 1000)
            steering = max(-1000, min(1000, steering))  # Clamp -1000 to 1000
            
            # Pack data in little endian format
            # H = unsigned short (2 bytes)
            # B = unsigned char (1 byte)
            # h = signed short (2 bytes)
            packet = struct.pack('<HBh', power, direction, steering)
            
            # Send UDP packet
            self.socket.sendto(packet, (self.host, self.port))
            
            self.error_message = None
            return True
            
        except Exception as e:
            self.error_message = f"Error sending UDP data: {e}"
            print(self.error_message)
            return False
    
    def is_connected(self) -> bool:
        """
        Check if UDP socket is ready to send.
        
        Returns:
            True if connected, False otherwise
        """
        return self.connected and self.socket is not None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current driver status.
        
        Returns:
            Dictionary containing status information
        """
        return {
            'type': 'udp',
            'connected': self.connected,
            'host': self.host,
            'port': self.port,
            'timeout': self.timeout,
            'error': self.error_message
        }
    
    def __del__(self):
        """
        Cleanup when object is destroyed.
        """
        if self.socket is not None:
            self.disconnect()
