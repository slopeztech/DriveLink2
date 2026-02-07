"""
Responsive GUI for displaying steering wheel and pedal data.
"""

import pygame
import sys
import math
import time
import requests
import threading
import json
import os
from io import BytesIO
from PIL import Image, ImageEnhance

# Color definitions
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
LIGHT_GRAY = (180, 180, 180)
DARK_GRAY = (50, 50, 50)
GREEN = (0, 255, 0)
RED = (255, 50, 50)
BLUE = (50, 150, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
PURPLE = (200, 0, 255)


class SteeringWheelUI:
    """
    Responsive UI for displaying steering wheel, pedals, and button data.
    """
    
    def __init__(self, width=1200, height=800, input_config=None, output_config_name=None, driving_mode=None):
        """
        Initialize the UI window.
        
        Args:
            width: Window width in pixels
            height: Window height in pixels
            input_config: InputConfig object for input mapping (optional)
            output_config_name: Output configuration name or path (optional)
            driving_mode: DrivingMode instance (optional)
        """
        pygame.init()
        pygame.joystick.init()
        
        self.width = width
        self.height = height
        self.input_config = input_config
        self.output_config_name = output_config_name
        self.driving_mode = driving_mode
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("DriveLink2")
        
        # Fonts (will be updated based on screen size)
        self._update_fonts()
        
        self.clock = pygame.time.Clock()
        self.running = False
        self.joystick = None
        
        # Message log for status panel
        self.messages = []
        self.max_messages = 10
        
        # MJPEG Stream support
        self.stream_url = None
        self.stream_thread = None
        self.stream_running = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.stream_config = {}
        self._load_default_stream_config()
        
        # Time tracking for physics updates
        self.last_time = time.time()
        
        # Initialize output manager if config is provided
        self.output_manager = None
        if output_config_name:
            self._initialize_output()
        
        # Add initial messages
        self._add_message(f"DriveLink2 started", CYAN)
        if self.driving_mode:
            self._add_message(f"Mode: {self.driving_mode.name}", GREEN)
    
    def _load_default_stream_config(self):
        """Load default stream configuration."""
        self.stream_config = {
            'display': {
                'flip_vertical': True,
                'flip_horizontal': False,
                'rotation': 0,
                'brightness': 1.0,
                'contrast': 1.0,
                'saturation': 1.0
            },
            'resolution': {
                'target_width': None,
                'target_height': None,
                'maintain_aspect_ratio': True
            },
            'performance': {
                'max_fps': 30
            }
        }
        
    def _update_fonts(self):
        """Update font sizes based on current screen dimensions."""
        base_size = min(self.width, self.height)
        self.font_large = pygame.font.Font(None, int(base_size * 0.03))  # Reduced from 0.04
        self.font_medium = pygame.font.Font(None, int(base_size * 0.025))  # Reduced from 0.03
        self.font_small = pygame.font.Font(None, int(base_size * 0.02))  # Reduced from 0.025
    
    def _initialize_output(self):
        """Initialize output manager from config name."""
        try:
            from output import OutputManager
            
            # Determine driver type and config from output_config_name
            if self.output_config_name.lower().endswith('.json'):
                config_name = self.output_config_name.rsplit('.', 1)[0]
                if 'serial' in config_name.lower():
                    driver_type = 'serial'
                elif 'http' in config_name.lower():
                    driver_type = 'http'
                else:
                    self._add_message(f"Could not determine driver: {self.output_config_name}", YELLOW)
                    return
            else:
                # Assume it's the driver type
                driver_type = self.output_config_name.lower()
            
            self.output_manager = OutputManager(driver_type)
            
            # Try to connect
            if self.output_manager.connect():
                status = self.output_manager.get_status()
                self._add_message(f"Output connected: {driver_type}", GREEN)
            else:
                status = self.output_manager.get_status()
                error_msg = status.get('error', 'Unknown error')
                self._add_message(f"Output error: {error_msg}", RED)
                
        except Exception as e:
            self._add_message(f"Output initialization error: {str(e)}", RED)
            self.output_manager = None
    
    def _add_message(self, text: str, color=WHITE):
        """Add a message to the message log."""
        timestamp = time.strftime("%H:%M:%S")
        self.messages.append({
            'text': text,
            'color': color,
            'time': timestamp
        })
        # Keep only last N messages
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
        
    def _draw_text(self, text, pos, font, color=WHITE):
        """Draw text on the screen."""
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, pos)
        
    def _draw_bar(self, x, y, width, height, value, label):
        """
        Draw a progress bar with label and value.
        
        Args:
            x, y: Position
            width, height: Bar dimensions
            value: Value from -1 to 1
            label: Text label for the bar
        """
        # Draw label
        self._draw_text(label, (x, y - height * 0.8), self.font_small)
        
        # Draw bar border
        pygame.draw.rect(self.screen, WHITE, (x, y, width, height), 2)
        
        # Calculate and draw fill (value ranges from -1 to 1)
        fill_width = int(((value + 1) / 2) * (width - 4))
        if fill_width > 0:
            pygame.draw.rect(self.screen, GREEN, (x + 2, y + 2, fill_width, height - 4))
        
        # Draw numeric value
        value_text = f"{value:+.3f}"
        self._draw_text(value_text, (x + width + width * 0.02, y + height * 0.15), self.font_small)
        
    def _draw_button_grid(self, x, y, button_states, columns):
        """
        Draw a grid of buttons showing their states.
        
        Args:
            x, y: Starting position
            button_states: List of boolean states
            columns: Number of columns in the grid
        """
        button_size = int(min(self.width, self.height) * 0.05)
        spacing = int(button_size * 0.2)
        
        for i, state in enumerate(button_states):
            row = i // columns
            col = i % columns
            
            btn_x = x + col * (button_size + spacing)
            btn_y = y + row * (button_size + spacing)
            
            # Color based on state
            color = RED if state else GRAY
            pygame.draw.rect(self.screen, color, (btn_x, btn_y, button_size, button_size))
            pygame.draw.rect(self.screen, WHITE, (btn_x, btn_y, button_size, button_size), 2)
            
            # Button number or action name
            if self.input_config:
                action = self.input_config.get_action_for_button(i)
                if action and state:
                    # Show action name when pressed
                    text = action.replace('_', ' ')[:8]  # Truncate if too long
                else:
                    text = str(i)
            else:
                text = str(i)
            
            text_surface = self.font_small.render(text, True, WHITE)
            text_rect = text_surface.get_rect(center=(btn_x + button_size//2, btn_y + button_size//2))
            self.screen.blit(text_surface, text_rect)
            
    def _handle_resize(self):
        """Handle window resize event and update responsive elements."""
        self.width, self.height = self.screen.get_size()
        self._update_fonts()
    
    def _collect_joystick_data(self) -> dict:
        """
        Collect current joystick state and return as processed data dictionary.
        
        Returns:
            Dictionary with control data ready to send to output drivers
        """
        data = {}
        
        # Collect axis data
        for i in range(self.joystick.get_numaxes()):
            axis_value = self.joystick.get_axis(i)
            
            if self.input_config:
                action = self.input_config.get_action_for_axis(i)
                if action:
                    # Apply axis processing (deadzone, inversion, sensitivity)
                    processed_value = self.input_config.apply_axis_processing(action, axis_value)
                    data[action] = processed_value
                else:
                    # No mapping found for this axis, use generic name
                    data[f'axis_{i}'] = axis_value
            else:
                # Use generic names if no config
                data[f'axis_{i}'] = axis_value
        
        # Collect button data
        for i in range(self.joystick.get_numbuttons()):
            button_state = self.joystick.get_button(i)
            
            if self.input_config:
                action = self.input_config.get_action_for_button(i)
                if action:
                    data[action] = button_state
                else:
                    # No mapping found for this button, use generic name
                    data[f'button_{i}'] = button_state
            else:
                # Use generic names if no config
                data[f'button_{i}'] = button_state
        
        # Collect hat/D-pad data
        for i in range(self.joystick.get_numhats()):
            hat_value = self.joystick.get_hat(i)
            data[f'hat_{i}'] = hat_value
        
        return data
    
    def _send_joystick_data(self):
        """Send collected joystick data to output manager if available."""
        # Collect raw input data
        data = self._collect_joystick_data()
        
        # Process through driving mode if available
        if self.driving_mode:
            # Update driving mode physics
            current_time = time.time()
            delta_time = current_time - self.last_time
            self.last_time = current_time
            
            self.driving_mode.update(delta_time)
            
            # Process input through driving mode
            data = self.driving_mode.process_input(data)
        
        # Send to output manager
        if self.output_manager and self.output_manager.driver.connected:
            try:
                self.output_manager.send_data(data)
            except Exception as e:
                self._add_message(f"Error sending data: {str(e)[:30]}", RED)
        
    def _handle_resize(self):
        """Handle window resize event and update responsive elements."""
        self.width, self.height = self.screen.get_size()
        self._update_fonts()
        
    def _draw_no_device_screen(self):
        """Draw error screen when no device is connected."""
        self.screen.fill(BLACK)
        msg1 = "No steering wheel/joystick detected"
        msg2 = "Connect a device and restart"
        
        text1 = self.font_large.render(msg1, True, RED)
        text2 = self.font_medium.render(msg2, True, WHITE)
        
        rect1 = text1.get_rect(center=(self.width//2, self.height//2 - 20))
        rect2 = text2.get_rect(center=(self.width//2, self.height//2 + 20))
        
        self.screen.blit(text1, rect1)
        self.screen.blit(text2, rect2)
        
        pygame.display.flip()
        pygame.time.wait(3000)
        
    def _draw_interface(self):
        """Draw the main interface with all controls."""
        # Clear screen
        self.screen.fill(BLACK)
        
        # Calculate responsive dimensions
        margin = int(self.width * 0.01)  # Reduced from 0.02
        
        # Get telemetry data from driving mode
        telemetry = self.driving_mode.get_telemetry() if self.driving_mode else {
            'speed': 0, 'gear': 0, 'power': 0, 'mode': 'N/A'
        }
        
        # === CENTRAL BOTTOM PANEL - Tachometers and Gear ===
        self._draw_central_panel(telemetry)
        
        # === LEFT BOTTOM - Position and Inclination Indicator ===
        self._draw_position_indicator()
        
        # === RIGHT BOTTOM - Output Data Panel ===
        self._draw_output_data_panel()
        
        # === CENTER AREA - MJPEG Stream (if configured) ===
        if self.stream_url:
            self._draw_stream_video()
        
        # === TOP - Title and Config Info ===
        self._draw_text(
            f"DriveLink2 - {self.joystick.get_name()}", 
            (margin, margin), 
            self.font_large, 
            YELLOW
        )
        
        config_y = margin + int(self.height * 0.03)  # Reduced from 0.04
        config_text = f"Modo: {telemetry['mode']}"
        if self.input_config:
            config_text += f" | Config: {self.input_config.name}"
        self._draw_text(config_text, (margin, config_y), self.font_small, LIGHT_GRAY)
        
    def _draw_central_panel(self, telemetry):
        """Draw central panel with tachometers and gear indicator."""
        # Panel dimensions - reduced size
        panel_width = int(self.width * 0.35)  # Reduced from 0.45
        panel_height = int(self.height * 0.25)  # Reduced from 0.35
        panel_x = (self.width - panel_width) // 2
        panel_y = self.height - panel_height - int(self.height * 0.01)  # Reduced margin
        
        # Draw panel background
        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.set_alpha(200)
        panel_surface.fill(DARK_GRAY)
        self.screen.blit(panel_surface, (panel_x, panel_y))
        pygame.draw.rect(self.screen, BLUE, (panel_x, panel_y, panel_width, panel_height), 3)
        
        # Tachometer dimensions - reduced size
        tach_radius = int(panel_height * 0.3)  # Reduced from 0.35
        tach_y = panel_y + panel_height // 2
        
        # Left tachometer - BRAKE
        left_tach_x = panel_x + panel_width // 4
        # Get brake value from joystick
        brake_value = 0.0
        if self.joystick:
            data = self._collect_joystick_data()
            brake_raw = data.get('brake', 0.0)
            brake_value = ((brake_raw + 1.0) / 2.0) * 100.0  # Convert -1,1 to 0-100%
        
        self._draw_tachometer(
            left_tach_x, tach_y, tach_radius,
            brake_value, 0, 100,
            "BRAKE", "%", RED
        )
        
        # Right tachometer - POWER
        right_tach_x = panel_x + (3 * panel_width) // 4
        self._draw_tachometer(
            right_tach_x, tach_y, tach_radius,
            telemetry['power'], 0, 100,
            "POWER", "%", ORANGE
        )
        
        # Center - GEAR INDICATOR
        gear_x = panel_x + panel_width // 2
        gear_y = tach_y
        self._draw_gear_indicator(gear_x, gear_y, telemetry['gear'], int(tach_radius * 0.8))
        
        # Speed bar at top of panel
        speed_bar_width = int(panel_width * 0.8)
        speed_bar_height = int(panel_height * 0.08)
        speed_bar_x = panel_x + (panel_width - speed_bar_width) // 2
        speed_bar_y = panel_y + int(panel_height * 0.05)
        self._draw_speed_bar(speed_bar_x, speed_bar_y, speed_bar_width, speed_bar_height, telemetry['speed'])
    
    def _draw_tachometer(self, x, y, radius, value, min_val, max_val, label, unit, color):
        """Draw a circular tachometer gauge."""
        # Draw outer circle
        pygame.draw.circle(self.screen, GRAY, (x, y), radius, 3)
        
        # Draw arc for the gauge
        start_angle = math.pi * 0.75  # 135 degrees
        end_angle = math.pi * 2.25    # 405 degrees (270 degree sweep)
        
        # Draw background arc
        self._draw_arc(x, y, radius - 10, start_angle, end_angle, DARK_GRAY, 8)
        
        # Calculate value angle
        value_clamped = max(min_val, min(value, max_val))
        value_ratio = (value_clamped - min_val) / (max_val - min_val)
        value_angle = start_angle + (end_angle - start_angle) * value_ratio
        
        # Draw value arc
        self._draw_arc(x, y, radius - 10, start_angle, value_angle, color, 8)
        
        # Draw center circle
        pygame.draw.circle(self.screen, BLACK, (x, y), int(radius * 0.5))
        pygame.draw.circle(self.screen, color, (x, y), int(radius * 0.5), 2)
        
        # Draw value text
        value_text = f"{int(value)}"
        value_surface = self.font_large.render(value_text, True, WHITE)
        value_rect = value_surface.get_rect(center=(x, y - int(radius * 0.1)))
        self.screen.blit(value_surface, value_rect)
        
        # Draw unit
        unit_surface = self.font_small.render(unit, True, LIGHT_GRAY)
        unit_rect = unit_surface.get_rect(center=(x, y + int(radius * 0.15)))
        self.screen.blit(unit_surface, unit_rect)
        
        # Draw label below
        label_surface = self.font_small.render(label, True, color)
        label_rect = label_surface.get_rect(center=(x, y + radius + 20))
        self.screen.blit(label_surface, label_rect)
    
    def _draw_arc(self, x, y, radius, start_angle, end_angle, color, width):
        """Draw an arc (part of a circle)."""
        # Create a list of points along the arc
        points = []
        steps = 50
        for i in range(steps + 1):
            angle = start_angle + (end_angle - start_angle) * (i / steps)
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            points.append((px, py))
        
        # Draw the arc as a series of lines
        if len(points) > 1:
            pygame.draw.lines(self.screen, color, False, points, width)
    
    def _draw_gear_indicator(self, x, y, gear, size):
        """Draw gear indicator in the center."""
        # Draw background circle
        pygame.draw.circle(self.screen, DARK_GRAY, (x, y), size)
        pygame.draw.circle(self.screen, CYAN, (x, y), size, 3)
        
        # Determine gear text
        if isinstance(gear, str):
            # Direct mode shows 'D', or other string values
            gear_text = gear
            gear_color = BLUE
        elif gear == 0:
            gear_text = "N"
            gear_color = YELLOW
        elif gear == -1:
            gear_text = "R"
            gear_color = RED
        else:
            gear_text = str(gear)
            gear_color = GREEN
        
        # Draw gear number
        gear_font = pygame.font.Font(None, int(size * 1.2))
        gear_surface = gear_font.render(gear_text, True, gear_color)
        gear_rect = gear_surface.get_rect(center=(x, y))
        self.screen.blit(gear_surface, gear_rect)
        
        # Draw "GEAR" label
        label_surface = self.font_small.render("GEAR", True, LIGHT_GRAY)
        label_rect = label_surface.get_rect(center=(x, y + size + 15))
        self.screen.blit(label_surface, label_rect)
    
    def _draw_speed_bar(self, x, y, width, height, speed_percent):
        """Draw Speed % bar indicator."""
        # Draw background
        pygame.draw.rect(self.screen, DARK_GRAY, (x, y, width, height))
        pygame.draw.rect(self.screen, WHITE, (x, y, width, height), 2)
        
        # Draw speed fill
        speed_ratio = min(abs(speed_percent) / 100.0, 1.0)
        fill_width = int(width * speed_ratio)
        
        # Color gradient from green (0%) to red (100%)
        # Calculate RGB values for smooth transition
        if speed_ratio < 0.5:
            # Green to Yellow (0-50%)
            red_val = int(255 * (speed_ratio * 2))
            green_val = 255
        else:
            # Yellow to Red (50-100%)
            red_val = 255
            green_val = int(255 * (2 - speed_ratio * 2))
        
        speed_color = (red_val, green_val, 0)
        
        if fill_width > 0:
            pygame.draw.rect(self.screen, speed_color, (x, y, fill_width, height))
        
        # Draw speed value
        speed_text = f"{speed_percent:.1f}%"
        self._draw_text(speed_text, (x + width + 10, y + height // 4), self.font_small, WHITE)
    
    def _draw_position_indicator(self):
        """Draw car position and inclination indicator (left bottom)."""
        # Panel dimensions - reduced size
        panel_width = int(self.width * 0.15)  # Reduced from 0.2
        panel_height = int(self.height * 0.2)  # Reduced from 0.25
        panel_x = int(self.width * 0.01)  # Reduced margin
        panel_y = self.height - panel_height - int(self.height * 0.01)  # Reduced margin
        
        # Draw panel background
        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.set_alpha(200)
        panel_surface.fill(DARK_GRAY)
        self.screen.blit(panel_surface, (panel_x, panel_y))
        pygame.draw.rect(self.screen, BLUE, (panel_x, panel_y, panel_width, panel_height), 3)
        
        # Draw title
        self._draw_text("STEERING", (panel_x + 10, panel_y + 10), self.font_small, CYAN)
        
        # Get steering angle
        steering_angle = 0.0
        if self.joystick:
            if self.input_config:
                action = 'steering'
                axis_mapping = self.input_config.get_axis_mapping(action)
                if axis_mapping:
                    axis_id = axis_mapping.get('axis_id')
                    if axis_id is not None:
                        raw_value = self.joystick.get_axis(axis_id)
                        steering_angle = self.input_config.apply_axis_processing(action, raw_value)
            else:
                # Default to axis 0
                steering_angle = self.joystick.get_axis(0)
        
        # Convert steering to angle (-1 to 1 -> -90 to 90 degrees for display)
        angle_deg = steering_angle * 90
        
        # Draw circular steering indicator
        center_x = panel_x + panel_width // 2
        center_y = panel_y + int(panel_height * 0.55)
        indicator_radius = int(min(panel_width, panel_height) * 0.25)  # Reduced from 0.28
        
        # Draw outer circle (gauge background)
        pygame.draw.circle(self.screen, DARK_GRAY, (center_x, center_y), indicator_radius)
        pygame.draw.circle(self.screen, LIGHT_GRAY, (center_x, center_y), indicator_radius, 3)
        
        # Draw tick marks for reference angles
        tick_angles = [-90, -45, 0, 45, 90]
        for tick_angle in tick_angles:
            angle_rad = math.radians(tick_angle - 90)  # -90 to start from top
            # Outer tick
            outer_x = center_x + (indicator_radius - 5) * math.cos(angle_rad)
            outer_y = center_y + (indicator_radius - 5) * math.sin(angle_rad)
            # Inner tick
            inner_x = center_x + (indicator_radius - 15) * math.cos(angle_rad)
            inner_y = center_y + (indicator_radius - 15) * math.sin(angle_rad)
            
            tick_color = CYAN if tick_angle == 0 else GRAY
            tick_width = 3 if tick_angle == 0 else 1
            pygame.draw.line(self.screen, tick_color, (outer_x, outer_y), (inner_x, inner_y), tick_width)
        
        # Draw steering range arc (from -90 to +90)
        start_angle = math.pi  # 180 degrees (left)
        end_angle = 0  # 0 degrees (right)
        self._draw_arc(center_x, center_y, indicator_radius - 8, start_angle, end_angle, BLUE, 2)
        
        # Draw current steering indicator (needle)
        angle_rad = math.radians(angle_deg - 90)  # -90 to start from top
        needle_length = indicator_radius - 20
        needle_end_x = center_x + needle_length * math.cos(angle_rad)
        needle_end_y = center_y + needle_length * math.sin(angle_rad)
        
        # Draw needle
        pygame.draw.line(self.screen, YELLOW, (center_x, center_y), 
                        (needle_end_x, needle_end_y), 4)
        pygame.draw.circle(self.screen, YELLOW, (int(needle_end_x), int(needle_end_y)), 6)
        
        # Draw center circle
        pygame.draw.circle(self.screen, BLACK, (center_x, center_y), 15)
        pygame.draw.circle(self.screen, YELLOW, (center_x, center_y), 15, 2)
        
        # Draw angle value in the center
        angle_text = f"{angle_deg:+.0f}°"
        angle_font = pygame.font.Font(None, int(indicator_radius * 0.35))
        angle_surface = angle_font.render(angle_text, True, WHITE)
        angle_rect = angle_surface.get_rect(center=(center_x, center_y))
        self.screen.blit(angle_surface, angle_rect)
        
        # Draw inclination placeholder (for future implementation)
        self._draw_text("Inclination: 0.0°", (panel_x + 10, panel_y + panel_height - 15), 
                       self.font_small, GRAY)
    
    def _draw_output_data_panel(self):
        """Draw output data panel (right bottom)."""
        # Panel dimensions - reduced size
        panel_width = int(self.width * 0.2)  # Reduced from 0.25
        panel_height = int(self.height * 0.25)  # Reduced from 0.35
        panel_x = self.width - panel_width - int(self.width * 0.01)  # Reduced margin
        panel_y = self.height - panel_height - int(self.height * 0.01)  # Reduced margin
        
        # Draw panel background
        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.set_alpha(220)
        panel_surface.fill(DARK_GRAY)
        self.screen.blit(panel_surface, (panel_x, panel_y))
        pygame.draw.rect(self.screen, BLUE, (panel_x, panel_y, panel_width, panel_height), 3)
        
        # Draw title
        self._draw_text("OUTPUT DATA", (panel_x + 10, panel_y + 10), self.font_small, CYAN)
        
        # Get last joystick data
        if self.joystick:
            data = self._collect_joystick_data()
            
            # Process through driving mode if available
            if self.driving_mode:
                data = self.driving_mode.process_input(data)
            
            y_offset = panel_y + 35
            line_height = int(panel_height * 0.055)
            
            # Define which data to display and in what order
            display_order = [
                ('steering', 'Steering', CYAN),
                ('throttle', 'Throttle', GREEN),
                ('brake', 'Brake', RED),
                ('clutch', 'Clutch', YELLOW),
                ('shift_up', 'Shift Up', LIGHT_GRAY),
                ('shift_down', 'Shift Down', LIGHT_GRAY),
                ('simulated_speed', 'Speed %', ORANGE),
                ('simulated_power', 'Power %', ORANGE),
                ('simulated_gear', 'Gear', PURPLE),
            ]
            
            for key, label, color in display_order:
                if key in data:
                    value = data[key]
                    
                    # Format value based on type
                    if isinstance(value, float):
                        if 'simulated' in key:
                            value_str = f"{value:.1f}"
                        else:
                            value_str = f"{value:+.2f}"
                        # Color based on magnitude
                        if abs(value) > 0.1:
                            value_color = color
                        else:
                            value_color = GRAY
                    elif isinstance(value, bool):
                        value_str = "ON" if value else "off"
                        value_color = color if value else GRAY
                    elif isinstance(value, int):
                        value_str = str(value)
                        value_color = color
                    else:
                        value_str = str(value)
                        value_color = WHITE
                    
                    # Draw label
                    self._draw_text(f"{label}:", (panel_x + 10, y_offset), self.font_small, LIGHT_GRAY)
                    
                    # Draw value (right-aligned)
                    value_surface = self.font_small.render(value_str, True, value_color)
                    value_x = panel_x + panel_width - value_surface.get_width() - 10
                    self.screen.blit(value_surface, (value_x, y_offset))
                    
                    y_offset += line_height
            
            # Show output driver status at bottom
            y_offset = panel_y + panel_height - 40
            if self.output_manager and self.output_manager.driver.connected:
                driver_name = self.output_manager.driver.__class__.__name__.replace('Driver', '')
                self._draw_text(f"Output: {driver_name}", (panel_x + 10, y_offset), 
                               self.font_small, GREEN)
            else:
                self._draw_text("Output: Disconnected", (panel_x + 10, y_offset), 
                               self.font_small, RED)
        else:
            # No joystick connected
            self._draw_text("No device connected", (panel_x + 10, panel_y + 40), 
                           self.font_small, RED)
    
    def _draw_debug_overlay(self):
        """Draw debug data overlay showing all control values."""
        if not hasattr(self.output_manager.driver, 'last_data'):
            return
        
        last_data = self.output_manager.driver.last_data
        if not last_data:
            return
        
        # Create semi-transparent overlay background
        overlay_width = int(self.width * 0.45)
        overlay_height = int(self.height * 0.9)
        overlay_x = self.width - overlay_width - int(self.width * 0.02)
        overlay_y = int(self.height * 0.05)
        
        # Draw background
        overlay_surface = pygame.Surface((overlay_width, overlay_height))
        overlay_surface.set_alpha(230)
        overlay_surface.fill((20, 20, 30))
        self.screen.blit(overlay_surface, (overlay_x, overlay_y))
        
        # Draw border
        pygame.draw.rect(self.screen, BLUE, (overlay_x, overlay_y, overlay_width, overlay_height), 2)
        
        # Title
        title_y = overlay_y + int(self.height * 0.02)
        self._draw_text("DEBUG DATA", (overlay_x + 10, title_y), self.font_medium, YELLOW)
        
        # Separator
        mapped_controls = {}
        unmapped_controls = {}
        
        for key, value in last_data.items():
            if key.startswith('axis_') or key.startswith('button_'):
                unmapped_controls[key] = value
            else:
                mapped_controls[key] = value
        
        # Draw mapped controls
        y_pos = title_y + int(self.height * 0.05)
        if mapped_controls:
            self._draw_text("MAPPED CONTROLS:", (overlay_x + 10, y_pos), self.font_small, GREEN)
            y_pos += int(self.height * 0.03)
            
            for key, value in mapped_controls.items():
                if isinstance(value, float):
                    value_str = f"{value:+.3f}"
                    color = GREEN if abs(value) > 0.1 else LIGHT_GRAY
                elif isinstance(value, (bool, int)):
                    value_str = "PRESSED" if value else "released"
                    color = GREEN if value else LIGHT_GRAY
                else:
                    value_str = str(value)
                    color = WHITE
                
                # Draw key
                text = f"{key:15s}"
                self._draw_text(text, (overlay_x + 15, y_pos), self.font_small, LIGHT_GRAY)
                
                # Draw value
                self._draw_text(value_str, (overlay_x + overlay_width - 100, y_pos), self.font_small, color)
                y_pos += int(self.height * 0.025)
        
        # Draw unmapped controls
        if unmapped_controls:
            y_pos += int(self.height * 0.02)
            self._draw_text("UNMAPPED:", (overlay_x + 10, y_pos), self.font_small, YELLOW)
            y_pos += int(self.height * 0.03)
            
            for key, value in unmapped_controls.items():
                if isinstance(value, float):
                    value_str = f"{value:+.3f}"
                    color = YELLOW if abs(value) > 0.1 else LIGHT_GRAY
                elif isinstance(value, (bool, int)):
                    value_str = "ON" if value else "off"
                    color = YELLOW if value else LIGHT_GRAY
                else:
                    value_str = str(value)
                    color = WHITE
                
                text = f"{key:12s}"
                self._draw_text(text, (overlay_x + 15, y_pos), self.font_small, LIGHT_GRAY)
                self._draw_text(value_str, (overlay_x + overlay_width - 100, y_pos), self.font_small, color)
                y_pos += int(self.height * 0.025)    
    def set_stream_url(self, stream_url, config_file=None):
        """Configure and start MJPEG stream.
        
        Args:
            stream_url: URL to MJPEG stream (e.g., 'http://192.168.1.135/stream')
            config_file: Path to stream configuration JSON file (optional)
        """
        self.stream_url = stream_url
        
        # Load configuration if provided
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    # Update stream_config with loaded values
                    if 'display' in config:
                        self.stream_config['display'].update(config['display'])
                    if 'resolution' in config:
                        self.stream_config['resolution'].update(config['resolution'])
                    if 'performance' in config:
                        self.stream_config['performance'].update(config['performance'])
                    self._add_message(f"Stream config loaded", GREEN)
            except Exception as e:
                self._add_message(f"Config error: {str(e)[:30]}", YELLOW)
        
        if self.stream_url and not self.stream_running:
            self.stream_running = True
            self.stream_thread = threading.Thread(target=self._stream_reader, daemon=True)
            self.stream_thread.start()
            self._add_message(f"Stream started", CYAN)
    
    def _stream_reader(self):
        """Read MJPEG stream in background thread."""
        try:
            response = requests.get(self.stream_url, stream=True, timeout=5)
            if response.status_code != 200:
                self._add_message(f"Stream error: {response.status_code}", RED)
                return
            
            boundary = None
            buffer = b''
            
            for chunk in response.iter_content(chunk_size=1024):
                if not self.stream_running:
                    break
                
                buffer += chunk
                
                # Find boundary
                if boundary is None:
                    if b'--' in buffer:
                        idx = buffer.find(b'\r\n')
                        if idx > 0:
                            boundary = buffer[:idx]
                            buffer = buffer[idx+2:]
                
                if boundary:
                    # Find frame boundaries
                    parts = buffer.split(boundary)
                    for part in parts[:-1]:
                        # Extract JPEG data
                        if b'\xff\xd8\xff' in part:  # JPEG start marker
                            jpeg_start = part.find(b'\xff\xd8\xff')
                            jpeg_end = part.find(b'\xff\xd9', jpeg_start) + 2
                            if jpeg_end > jpeg_start:
                                try:
                                    img = Image.open(BytesIO(part[jpeg_start:jpeg_end]))
                                    
                                    # Apply configured transformations
                                    img = self._apply_image_transforms(img)
                                    
                                    # Convert to pygame surface
                                    img_str = pygame.image.fromstring(
                                        img.tobytes(), img.size, img.mode
                                    )
                                    with self.frame_lock:
                                        self.current_frame = img_str
                                except Exception as e:
                                    pass  # Skip bad frames
                    
                    buffer = parts[-1]
        except Exception as e:
            self._add_message(f"Stream error: {str(e)[:30]}", RED)
            self.stream_running = False
    
    def _apply_image_transforms(self, img):
        """Apply configured transformations to image.
        
        Args:
            img: PIL Image object
            
        Returns:
            Transformed PIL Image
        """
        display_cfg = self.stream_config.get('display', {})
        
        # Apply flip transformations
        if display_cfg.get('flip_horizontal', False):
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        if display_cfg.get('flip_vertical', False):
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
        
        # Apply rotation
        rotation = display_cfg.get('rotation', 0)
        if rotation == 90:
            img = img.transpose(Image.ROTATE_270)
        elif rotation == 180:
            img = img.transpose(Image.ROTATE_180)
        elif rotation == 270:
            img = img.transpose(Image.ROTATE_90)
        
        # Apply brightness adjustment
        brightness = display_cfg.get('brightness', 1.0)
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness)
        
        # Apply contrast adjustment
        contrast = display_cfg.get('contrast', 1.0)
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)
        
        # Apply saturation adjustment
        saturation = display_cfg.get('saturation', 1.0)
        if saturation != 1.0:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(saturation)
        
        return img
    
    def _draw_stream_video(self):
        """Draw MJPEG stream video in center area."""
        # Get frame dimensions (use most of screen except panels area)
        panel_height = int(self.height * 0.25)
        margin = int(self.width * 0.01)
        
        # Video area: full width, from top to just above panels
        video_x = 0
        video_y = 0
        video_width = self.width
        video_height = self.height - panel_height - margin
        
        # Draw video background
        pygame.draw.rect(self.screen, DARK_GRAY, (video_x, video_y, video_width, video_height))
        
        # Draw current frame if available
        if self.current_frame:
            with self.frame_lock:
                frame = self.current_frame
                if frame:
                    # Scale frame to fit video area
                    frame_w, frame_h = frame.get_size()
                    scale = min(video_width / frame_w, video_height / frame_h)
                    new_w = int(frame_w * scale)
                    new_h = int(frame_h * scale)
                    
                    scaled_frame = pygame.transform.scale(frame, (new_w, new_h))
                    # Center frame
                    offset_x = (video_width - new_w) // 2
                    offset_y = (video_height - new_h) // 2
                    self.screen.blit(scaled_frame, (video_x + offset_x, video_y + offset_y))
        else:
            # Show loading message
            loading_text = "Stream connecting..."
            text_surface = self.font_medium.render(loading_text, True, LIGHT_GRAY)
            text_rect = text_surface.get_rect(
                center=(video_x + video_width // 2, video_y + video_height // 2)
            )
            self.screen.blit(text_surface, text_rect)        
    def run(self):
        """Main loop for the UI."""
        # Check for connected joysticks
        joystick_count = pygame.joystick.get_count()
        if joystick_count == 0:
            self._draw_no_device_screen()
            pygame.quit()
            return False
        
        # Initialize first joystick (steering wheel)
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        
        self._add_message(f"Device: {self.joystick.get_name()}", GREEN)
        
        # Initialize time tracking
        self.last_time = time.time()
        
        # Activate driving mode
        if self.driving_mode:
            self.driving_mode.activate()
        
        self.running = True
        
        while self.running:
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    self._handle_resize()
            
            # Send joystick data to output manager (if connected)
            self._send_joystick_data()
            
            # Draw interface
            self._draw_interface()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS
        
        # Cleanup
        if self.output_manager and self.output_manager.driver.connected:
            self.output_manager.disconnect()
        
        pygame.quit()
        return True
