"""
Configuration generator for creating new input mapping configurations.
Helps identify axis and button IDs on your joystick.
"""

import pygame
import json
import os
from datetime import datetime

def detect_joystick_layout():
    """Interactive joystick detection and configuration generator."""
    
    pygame.init()
    pygame.joystick.init()
    
    joysticks = pygame.joystick.get_count()
    
    if joysticks == 0:
        print("✗ No joystick detected!")
        print("Please connect your steering wheel and try again.")
        return None
    
    print(f"\nFound {joysticks} joystick(s)")
    
    # For now, use the first joystick
    js = pygame.joystick.Joystick(0)
    js.init()
    
    print(f"\nDetected: {js.get_name()}")
    print(f"Axes: {js.get_numaxes()}")
    print(f"Buttons: {js.get_numbuttons()}")
    print(f"Hats: {js.get_numhats()}")
    
    # Create configuration template
    config = {
        "mapping_name": f"Configuration for {js.get_name()}",
        "description": f"Auto-detected configuration created {datetime.now().isoformat()}",
        "version": "1.0",
        "axes": {},
        "buttons": {},
        "hats": {}
    }
    
    # Detect common axis patterns
    print("\n" + "="*60)
    print("AXIS DETECTION")
    print("="*60)
    print("\nPlease perform the following actions to map axes:")
    print("1. Rotate steering wheel fully LEFT and RIGHT")
    print("2. Press THROTTLE/ACCELERATOR pedal fully")
    print("3. Press BRAKE pedal fully")
    print("\nPress ENTER when ready, then perform actions...")
    input()
    
    print("\nMonitoring for 10 seconds...")
    
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    axis_activity = {}
    
    while pygame.time.get_ticks() - start_time < 10000:
        for event in pygame.event.get():
            if event.type == pygame.JOYAXISMOTION:
                # Only track significant movements (> 0.5)
                if abs(event.value) > 0.5:
                    if event.axis not in axis_activity:
                        axis_activity[event.axis] = []
                    axis_activity[event.axis].append(event.value)
        
        pygame.event.pump()
        clock.tick(60)
    
    # Analyze axis activity
    print("\nAxis Activity Detected:")
    for axis_id in sorted(axis_activity.keys()):
        values = axis_activity[axis_id]
        avg_value = sum(values) / len(values)
        print(f"  axis_{axis_id}: {len(values)} readings, avg={avg_value:+.2f}")
    
    # Suggest mappings based on activity
    if 0 in axis_activity:
        config["axes"]["steering"] = {
            "axis_id": 0,
            "description": "Steering wheel rotation",
            "inverted": False,
            "deadzone": 0.05,
            "sensitivity": 1.0
        }
    
    if 5 in axis_activity:
        config["axes"]["throttle"] = {
            "axis_id": 5,
            "description": "Accelerator pedal",
            "inverted": False,
            "deadzone": 0.05,
            "sensitivity": 1.0
        }
    
    if 4 in axis_activity:
        config["axes"]["brake"] = {
            "axis_id": 4,
            "description": "Brake pedal",
            "inverted": False,
            "deadzone": 0.05,
            "sensitivity": 1.0
        }
    
    # Detect buttons
    print("\n" + "="*60)
    print("BUTTON DETECTION")
    print("="*60)
    print("\nPress all buttons on your controller...")
    print("Press ESCAPE when done")
    
    button_presses = set()
    
    start_time = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start_time < 20000:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    break
            if event.type == pygame.JOYBUTTONDOWN:
                button_presses.add(event.button)
                print(f"  Button {event.button} pressed")
        
        pygame.event.pump()
        clock.tick(60)
    
    # Map detected buttons
    button_names = {
        0: "horn",
        1: "camera_change",
        2: "clutch",
        3: "handbrake",
        4: "shift_down",
        5: "shift_up",
        6: "pause",
        7: "reset"
    }
    
    for button_id in sorted(button_presses):
        if button_id < len(button_names):
            name = button_names[button_id]
        else:
            name = f"button_{button_id}"
        
        config["buttons"][name] = {
            "button_id": button_id,
            "description": f"Button {button_id}"
        }
    
    pygame.quit()
    
    # Save configuration
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    config_name = f"joystick_{timestamp}.json"
    config_path = os.path.join("input", config_name)
    
    os.makedirs("input", exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✓ Configuration saved to: {config_path}")
    print(f"\nTo use this configuration:")
    print(f"  python main.py input {config_name}")
    
    return config_path

if __name__ == "__main__":
    print("\n" + "="*60)
    print("DRIVELINK2 - JOYSTICK CONFIGURATION GENERATOR")
    print("="*60)
    
    try:
        detect_joystick_layout()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
