"""
HTTP output driver for communicating with RC vehicles.
Sends control data over HTTP requests.
"""

import json
import os
from typing import Dict, Any, Optional
import requests
from .base_driver import BaseDriver


class HttpDriver(BaseDriver):
    """
    HTTP output driver for RC vehicle control.
    """
    
    CONFIG_FILE = "http.json"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize HTTP driver.
        
        Args:
            config: Configuration dictionary. If None, loads from http.json
                    Expected keys:
                    - 'host': Server hostname or IP address
                    - 'port': Server port (default: 8000)
                    - 'endpoint': API endpoint (default: '/control')
                    - 'timeout': Request timeout in seconds (default: 2.0)
        """
        # Load config from file if not provided
        if config is None:
            config = self._load_config_file()
        
        super().__init__(config)
        self.host = config.get('host')
        self.port = config.get('port', 8000)
        self.endpoint = config.get('endpoint', '/control')
        self.timeout = config.get('timeout', 2.0)
        self.url = f"http://{self.host}:{self.port}{self.endpoint}"
        self.error_message = None
    
    @staticmethod
    def _load_config_file() -> Dict[str, Any]:
        """
        Load HTTP configuration from JSON file.
        
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file not found
        """
        # Determine config file path
        driver_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(os.path.dirname(driver_dir), 'configs')
        config_path = os.path.join(config_dir, HttpDriver.CONFIG_FILE)
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"HTTP config file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
        
    def connect(self) -> bool:
        """
        Establish HTTP connection (ping the server).
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not self.host:
                self.error_message = "Host not specified"
                return False
            
            # Try to ping the server
            response = requests.get(
                f"http://{self.host}:{self.port}/health",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.connected = True
                self.error_message = None
                return True
            else:
                self.error_message = f"Server returned status code {response.status_code}"
                return False
                
        except requests.exceptions.ConnectionError as e:
            self.error_message = f"Connection failed: {e}"
            self.connected = False
            return False
        except requests.exceptions.Timeout as e:
            self.error_message = f"Connection timeout: {e}"
            self.connected = False
            return False
        except Exception as e:
            self.error_message = str(e)
            self.connected = False
            return False
    
    def disconnect(self) -> bool:
        """
        Close HTTP connection.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        self.connected = False
        self.error_message = None
        return True
    
    def send_data(self, data: Dict[str, Any]) -> bool:
        """
        Send control data via HTTP POST request.
        
        Args:
            data: Dictionary with control values
        
        Returns:
            True if data sent successfully, False otherwise
        """
        if not self.connected:
            self.error_message = "HTTP connection not established"
            return False
        
        try:
            # Send POST request with JSON data
            response = requests.post(
                self.url,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201, 202, 204]:
                self.error_message = None
                return True
            else:
                self.error_message = f"Server returned status code {response.status_code}"
                return False
                
        except requests.exceptions.RequestException as e:
            self.error_message = str(e)
            self.connected = False
            return False
        except Exception as e:
            self.error_message = str(e)
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get HTTP driver status.
        
        Returns:
            Status dictionary
        """
        return {
            'type': 'http',
            'connected': self.connected,
            'url': self.url,
            'timeout': self.timeout,
            'error': self.error_message
        }
