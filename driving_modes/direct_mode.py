"""
Direct driving mode.
Passes input directly to output without any processing.
"""

from typing import Dict, Any
from .base_mode import BaseDrivingMode


class DirectMode(BaseDrivingMode):
    """
    Direct mode: passes steering wheel and pedal inputs directly to output.
    No simulation, no gear changes, just raw input forwarding.
    """
    
    def __init__(self):
        super().__init__(
            name="Direct",
            description="Direct pass-through mode - sends raw inputs to output"
        )
    
    def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input by passing it directly through.
        
        Args:
            input_data: Raw input data from steering wheel and pedals
            
        Returns:
            Same data, passed through unchanged
        """
        # In direct mode, we simply return the input data as-is
        # The output driver will receive exactly what the wheel/pedals send
        
        # Extract basic values for telemetry display
        throttle = input_data.get('throttle', 0.0)
        brake = input_data.get('brake', 0.0)
        
        # Update telemetry (for display purposes)
        # Power = throttle intensity
        self.power = ((throttle + 1.0) / 2.0) * 100.0  # Convert -1,1 to 0-100%
        
        # In direct mode, speed follows power directly
        self.speed = self.power  # Speed % matches power %
        
        # Direct mode shows 'D' (Drive) instead of a gear number
        self.current_gear = 'D'
        
        return input_data.copy()
    
    def update(self, delta_time: float):
        """
        Update mode state.
        
        In direct mode, there's no physics simulation,
        so this doesn't do much.
        
        Args:
            delta_time: Time elapsed since last update in seconds
        """
        # No physics simulation in direct mode
        pass
    
    def reset(self):
        """Reset mode state."""
        super().reset()
