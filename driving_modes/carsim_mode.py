"""
CarSim driving mode.
Simulates a car with manual transmission and gears.
"""

import math
from typing import Dict, Any
from .base_mode import BaseDrivingMode


class CarSimMode(BaseDrivingMode):
    """
    CarSim mode: simulates a car with manual transmission.
    Uses percentage-based system for speed and power.
    Lower gears: faster acceleration, lower max speed.
    Higher gears: slower acceleration, higher max speed.
    """
    
    def __init__(self):
        super().__init__(
            name="CarSim",
            description="Car simulation mode with manual transmission"
        )
        
        # Gear characteristics (acceleration multiplier, max speed %)
        # Format: {gear: (acceleration_factor, max_speed_percent)}
        self.gear_characteristics = {
            -1: (1.5, 20.0),   # Reverse: fast accel, 20% max
            0: (0.0, 0.0),     # Neutral: no power
            1: (3.0, 20.0),    # 1st: fastest accel, 20% max speed
            2: (2.0, 40.0),    # 2nd: fast accel, 40% max speed
            3: (1.5, 60.0),    # 3rd: medium accel, 60% max speed
            4: (1.2, 80.0),    # 4th: slower accel, 80% max speed
            5: (0.9, 100.0),   # 5th: slowest accel, 100% max speed
        }
        
        # Physics parameters (configurable)
        self.inertia = 0.88  # 0-1, how much speed is retained per second (higher = more inertia)
        self.brake_power = 1.0  # Brake effectiveness multiplier
        self.base_acceleration = 12.0  # Base acceleration rate (% per second)
        
        # Physics state
        self.current_speed_percent = 0.0  # Current speed as percentage (0-100%)
        
        # Clutch state
        self.clutch_engaged = True
        
        # Gear shift cooldown (to prevent rapid shifting)
        self.shift_cooldown = 0.0
        self.shift_cooldown_time = 0.3  # seconds
        
        # Previous button states (for detecting button press/release)
        self.prev_shift_up = False
        self.prev_shift_down = False
        
        # Current input values (updated in process_input)
        self.current_throttle = 0.0
        self.current_brake = 0.0
        
    def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input with car simulation.
        
        Args:
            input_data: Raw input data from steering wheel and pedals
            
        Returns:
            Processed data with simulated car behavior
        """
        # Extract inputs
        steering = input_data.get('steering', 0.0)
        throttle = input_data.get('throttle', 0.0)
        brake = input_data.get('brake', 0.0)
        clutch = input_data.get('clutch', 0.0)
        
        # Convert throttle/brake from -1,1 to 0,1 range
        throttle_value = (throttle + 1.0) / 2.0  # 0 = no throttle, 1 = full throttle
        brake_value = (brake + 1.0) / 2.0  # 0 = no brake, 1 = full brake
        clutch_value = (clutch + 1.0) / 2.0 if clutch != 0.0 else 1.0  # 0 = clutch down, 1 = engaged
        
        # Store current input values for physics update
        self.current_throttle = throttle_value
        self.current_brake = brake_value
        
        # Update clutch state
        self.clutch_engaged = clutch_value > 0.5
        
        # Handle gear shifts
        shift_up = input_data.get('shift_up', False)
        shift_down = input_data.get('shift_down', False)
        
        # Detect button press (transition from False to True)
        if self.shift_cooldown <= 0:
            if shift_up and not self.prev_shift_up:
                self._shift_up()
            elif shift_down and not self.prev_shift_down:
                self._shift_down()
        
        self.prev_shift_up = shift_up
        self.prev_shift_down = shift_down
        
        # Update power and speed for telemetry
        self.power = throttle_value * 100.0
        self.speed = self.current_speed_percent
        
        # Create output data
        output_data = input_data.copy()
        output_data['simulated_speed'] = self.speed
        output_data['simulated_gear'] = self.current_gear
        output_data['simulated_power'] = self.power
        
        return output_data
    
    def update(self, delta_time: float):
        """
        Update car physics simulation.
        
        Args:
            delta_time: Time elapsed since last update in seconds
        """
        # Update shift cooldown
        if self.shift_cooldown > 0:
            self.shift_cooldown -= delta_time
        
        # Get current gear characteristics
        accel_factor, max_speed_percent = self.gear_characteristics.get(
            self.current_gear, (0.0, 0.0)
        )
        
        # Physics simulation
        if self.current_gear != 0 and self.clutch_engaged:
            # Calculate how much we're over the gear limit (engine braking effect)
            speed_over_limit = self.current_speed_percent - max_speed_percent
            
            # Apply throttle - acceleration based on gear
            if self.current_throttle > 0.001:  # Very low threshold for immediate response
                # Calculate base acceleration
                base_accel = self.base_acceleration * accel_factor * self.current_throttle * delta_time
                
                # Apply gear-speed penalty: higher gears need speed to work effectively
                # Lower gears (1, 2) work well at any speed, higher gears (4, 5) need momentum
                if self.current_gear > 0:  # Only for forward gears
                    # Calculate minimum effective speed for this gear (as percentage of max speed)
                    # Each gear needs at least some speed to work efficiently
                    min_effective_speed = (self.current_gear - 1) * 15.0  # 0%, 15%, 30%, 45%, 60% for gears 1-5
                    
                    if self.current_speed_percent < min_effective_speed:
                        # Apply penalty: the further below min speed, the harder to accelerate
                        speed_deficit = min_effective_speed - self.current_speed_percent
                        # Penalty factor: ranges from 0.1 (very slow) to 1.0 (no penalty)
                        penalty = max(0.1, 1.0 - (speed_deficit / (min_effective_speed + 1.0)) * 0.9)
                        base_accel *= penalty
                
                acceleration = base_accel
                
                # Only accelerate if we haven't reached the max speed for this gear
                if self.current_speed_percent < max_speed_percent:
                    # Add acceleration to speed
                    self.current_speed_percent += acceleration
                    
                    # Clamp to max speed for this gear (only when accelerating)
                    if self.current_speed_percent > max_speed_percent:
                        self.current_speed_percent = max_speed_percent
                # If we're above the max speed for this gear, apply engine braking
                else:
                    # Engine braking: more aggressive the further over the limit we are
                    # This simulates downshifting at high speed
                    over_limit_ratio = speed_over_limit / 100.0  # 0-1 scale
                    engine_brake_factor = 1.0 + (over_limit_ratio * 5.0)  # 1x to 6x braking
                    
                    decay_rate = 1.0 - (self.inertia ** delta_time)
                    self.current_speed_percent *= (1.0 - (decay_rate * engine_brake_factor))
            else:
                # No throttle - apply inertia decay with engine braking if over limit
                decay_rate = 1.0 - (self.inertia ** delta_time)
                
                if speed_over_limit > 0:
                    # Apply stronger engine braking when over the gear limit
                    over_limit_ratio = speed_over_limit / 100.0
                    engine_brake_factor = 1.0 + (over_limit_ratio * 4.0)  # 1x to 5x braking
                    self.current_speed_percent *= (1.0 - (decay_rate * engine_brake_factor))
                else:
                    # Normal inertia decay
                    self.current_speed_percent *= (1.0 - decay_rate)
            
            # Apply brake
            if self.current_brake > 0.01:
                brake_deceleration = self.brake_power * self.current_brake * 20.0 * delta_time
                self.current_speed_percent -= brake_deceleration
            
            # Apply direction based on gear
            if self.current_gear < 0:  # Reverse
                # In reverse, limit to negative speed
                self.current_speed_percent = min(self.current_speed_percent, 0)
                self.current_speed_percent = max(self.current_speed_percent, -max_speed_percent)
            else:
                # Forward gears
                self.current_speed_percent = max(self.current_speed_percent, 0)
        
        else:
            # Neutral or clutch disengaged - coast with inertia
            decay_rate = 1.0 - (self.inertia ** delta_time)
            self.current_speed_percent *= (1.0 - decay_rate)
            
            # Apply brake even in neutral
            if self.current_brake > 0.01:
                brake_deceleration = self.brake_power * self.current_brake * 20.0 * delta_time
                if self.current_speed_percent > 0:
                    self.current_speed_percent -= brake_deceleration
                else:
                    self.current_speed_percent += brake_deceleration
        
        # Clamp speed to valid range
        self.current_speed_percent = max(-100.0, min(100.0, self.current_speed_percent))
        
        # If speed is very low, set to zero
        if abs(self.current_speed_percent) < 0.1:
            self.current_speed_percent = 0.0
    
    def _shift_up(self):
        """Shift to higher gear."""
        if self.current_gear < 5:
            self.current_gear += 1
            self.shift_cooldown = self.shift_cooldown_time
            print(f"Shifted UP to gear {self.current_gear}")
    
    def _shift_down(self):
        """Shift to lower gear."""
        if self.current_gear > -1:
            self.current_gear -= 1
            self.shift_cooldown = self.shift_cooldown_time
            print(f"Shifted DOWN to gear {self.current_gear}")
    
    def reset(self):
        """Reset simulation state."""
        super().reset()
        self.current_speed_percent = 0.0
        self.clutch_engaged = True
        self.shift_cooldown = 0.0
        self.prev_shift_up = False
        self.prev_shift_down = False
        self.current_throttle = 0.0
        self.current_brake = 0.0
