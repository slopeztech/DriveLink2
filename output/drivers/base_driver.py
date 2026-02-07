"""
Base driver class for output methods.
All output drivers should inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseDriver(ABC):
    """
    Abstract base class for output drivers.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the driver.
        
        Args:
            config: Configuration dictionary for the driver
        """
        self.config = config
        self.connected = False
        
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the output device.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close connection to the output device.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def send_data(self, data: Dict[str, Any]) -> bool:
        """
        Send data to the RC vehicle.
        
        Args:
            data: Dictionary containing control values
                  Expected keys: 'steering', 'throttle', 'brake', 'shift_up', 'shift_down'
        
        Returns:
            True if data sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the driver.
        
        Returns:
            Dictionary with status information
        """
        pass
