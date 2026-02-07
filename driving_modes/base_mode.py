"""
Base class for driving modes.
All driving modes inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseDrivingMode(ABC):
    """Base class for all driving modes."""
    
    def __init__(self, name: str, description: str):
        """
        Initialize the driving mode.
        
        Args:
            name: Name of the driving mode
            description: Description of what this mode does
        """
        self.name = name
        self.description = description
        self.active = False
        
        # State variables that modes can use
        self.current_gear = 0  # 0=Neutral, 1-6=Gears, -1=Reverse
        self.speed = 0.0  # Speed percentage (0-100%)
        self.power = 0.0  # Power percentage (0-100%)
        
    @abstractmethod
    def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and return output data.
        
        This is the main method that each mode must implement.
        It receives raw input from the steering wheel/pedals and
        returns the processed output to send to the output driver.
        
        Args:
            input_data: Dictionary with input controls (steering, throttle, brake, buttons, etc.)
            
        Returns:
            Dictionary with processed output data
        """
        pass
    
    @abstractmethod
    def update(self, delta_time: float):
        """
        Update mode state based on time elapsed.
        
        This is called every frame to update physics, animations, etc.
        
        Args:
            delta_time: Time elapsed since last update in seconds
        """
        pass
    
    def activate(self):
        """Called when this mode becomes active."""
        self.active = True
        self.reset()
    
    def deactivate(self):
        """Called when this mode becomes inactive."""
        self.active = False
    
    def reset(self):
        """Reset mode state to initial values."""
        self.current_gear = 0
        self.speed = 0.0
        self.power = 0.0
    
    def get_telemetry(self) -> Dict[str, Any]:
        """
        Get current telemetry data for display.
        
        Returns:
            Dictionary with telemetry data (speed, gear, power, etc.)
        """
        return {
            'mode': self.name,
            'gear': self.current_gear,
            'speed': self.speed,
            'power': self.power
        }
