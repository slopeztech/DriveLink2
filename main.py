"""
DriveLink2 - Steering Wheel and Pedals Reader
Main entry point for the application.
"""

import argparse
import json
import os
from gui import SteeringWheelUI
from input import InputMapper
from driving_modes import DirectMode, CarSimMode


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='DriveLink2 - Steering Wheel and Pedals Reader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python main.py
  python main.py input default_input.json
  python main.py output configs/serial.json
  python main.py input logitech_g29.json output configs/http.json
        '''
    )
    
    parser.add_argument(
        'input',
        nargs='?',
        default=None,
        help='Input config mode keyword'
    )
    parser.add_argument(
        'input_config',
        nargs='?',
        default=None,
        help='Input configuration file name or path'
    )
    parser.add_argument(
        'output',
        nargs='?',
        default=None,
        help='Output config mode keyword'
    )
    parser.add_argument(
        'output_config',
        nargs='?',
        default=None,
        help='Output configuration file name or path'
    )
    parser.add_argument(
        '-m', '--mode',
        choices=['direct', 'carsim'],
        default='direct',
        help='Driving mode: direct (pass-through) or carsim (car simulation)'
    )
    parser.add_argument(
        '-s', '--stream',
        default=None,
        help='MJPEG stream URL (e.g., http://192.168.1.135/stream)'
    )
    parser.add_argument(
        '--stream-config',
        default='stream_config.json',
        help='Stream configuration file (default: stream_config.json)'
    )
    
    return parser.parse_args()


def main():
    """Initialize and run the steering wheel UI."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Process input and output arguments
    input_config_name = None
    output_config_name = None
    
    # Parse the positional arguments in order
    pos_args = [
        args.input,
        args.input_config,
        args.output,
        args.output_config
    ]
    pos_args = [arg for arg in pos_args if arg is not None]
    
    # Process arguments in pairs (mode, value)
    i = 0
    while i < len(pos_args):
        arg = pos_args[i]
        
        if arg.lower() in ['input', 'i']:
            # Next argument should be the input config name
            if i + 1 < len(pos_args):
                input_config_name = pos_args[i + 1]
                i += 2
            else:
                i += 1
        elif arg.lower() in ['output', 'o']:
            # Next argument should be the output config name
            if i + 1 < len(pos_args):
                output_config_name = pos_args[i + 1]
                i += 2
            else:
                i += 1
        else:
            i += 1
    
    # Load input configuration
    input_config = None
    mapper = InputMapper()
    try:
        if input_config_name:
            input_config = mapper.load_config(input_config_name)
            print(f"✓ Loaded input configuration: {input_config.name}")
        else:
            input_config = mapper.load_default_config()
            print(f"✓ Loaded default input configuration: {input_config.name}")
        
        print(f"  Version: {input_config.version}")
        print(f"  Description: {input_config.description}")
        print(f"  Axes mapped: {len(input_config.axes)}")
        print(f"  Buttons mapped: {len(input_config.buttons)}")
    except Exception as e:
        print(f"✗ Warning: Could not load input configuration: {e}")
        print("  Running without input mapping...")
        input_config = None
    
    # Initialize driving mode
    driving_mode = None
    if args.mode == 'carsim':
        driving_mode = CarSimMode()
        print(f"✓ Driving mode: {driving_mode.name} - {driving_mode.description}")
    else:
        driving_mode = DirectMode()
        print(f"✓ Driving mode: {driving_mode.name} - {driving_mode.description}")
    
    # Initialize and run UI with configuration
    ui = SteeringWheelUI(
        width=1200,
        height=800,
        input_config=input_config,
        output_config_name=output_config_name,
        driving_mode=driving_mode
    )
    
    # Configure stream if provided
    stream_url = args.stream
    
    # If no stream URL provided via command line, try to load from config file
    if not stream_url and args.stream_config and os.path.exists(args.stream_config):
        try:
            with open(args.stream_config, 'r') as f:
                stream_config = json.load(f)
                if 'stream' in stream_config and 'url' in stream_config['stream']:
                    stream_url = stream_config['stream']['url']
                    print(f"✓ Loaded stream URL from config: {stream_url}")
        except Exception as e:
            print(f"✗ Warning: Could not load stream config: {e}")
    
    if stream_url:
        ui.set_stream_url(stream_url, config_file=args.stream_config)
    
    ui.run()


if __name__ == "__main__":
    main()
