# DriveLink2 - Steering Wheel and Pedals Reader

A comprehensive Python application that reads input from steering wheels and pedals (such as Logitech G29) and routes the data to various output destinations with multiple simulation modes.

## Features

- **Multiple Input Support**: Compatible with various steering wheel and pedal controllers
- **Multiple Output Drivers**: UDP, HTTP, Serial, and Debug outputs
- **Driving Modes**: 
  - Direct mode for raw pass-through
  - CarSim mode for realistic vehicle simulation
- **GUI Interface**: Real-time visual feedback of input values
- **Flexible Configuration**: JSON-based configuration system
- **Multi-threaded Architecture**: Efficient concurrent processing

## Project Structure

```
DriveLink2/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── generate_config.py      # Configuration file generator
├── stream_config.json      # Streaming configuration
│
├── driving_modes/          # Simulation modes
│   ├── base_mode.py       # Base mode class
│   ├── direct_mode.py     # Direct pass-through mode
│   ├── carsim_mode.py     # Realistic vehicle simulation
│   └── carsim_config.json # CarSim mode settings
│
├── input/                  # Input handling
│   ├── input_mapper.py    # Input mapping and processing
│   └── default_input.json # Default input configuration
│
├── output/                 # Output management
│   ├── output_manager.py  # Output coordinator
│   ├── output_config.json # Output configuration
│   ├── configs/           # Output driver configurations
│   │   ├── debug.json
│   │   ├── http.json
│   │   ├── serial.json
│   │   └── udp.json
│   └── drivers/           # Output driver implementations
│       ├── base_driver.py
│       ├── debug_driver.py
│       ├── http_driver.py
│       ├── serial_driver.py
│       └── udp_driver.py
│
└── gui/                    # User interface
    └── ui.py             # GUI implementation
```

## Requirements

- Python 3.8 or higher
- pygame >= 2.1.0
- Pillow >= 9.0.0
- requests >= 2.28.0
- pyserial >= 3.5

## Installation

1. Clone or download the repository
2. Navigate to the project directory
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the application with default settings:

```bash
python main.py
```

### With Input Configuration

Specify an input configuration file:

```bash
python main.py input default_input.json
```

### With Output Configuration

Specify an output driver:

```bash
python main.py output configs/serial.json
```

### Combined Configuration

Specify both input and output:

```bash
python main.py input default_input.json output configs/udp.json
```

## Driving Modes

### Direct Mode
- **Purpose**: Raw pass-through without any processing
- **Use Case**: Direct control applications with minimal latency
- **Usage**: Default mode when running the application

### CarSim Mode
- **Purpose**: Realistic vehicle simulation
- **Features**:
  - 6-speed manual transmission with reverse
  - Engine physics (RPM simulation)
  - Clutch control
  - Speed calculation based on gear and RPM
- **Use Case**: Realistic driving simulators
- **Configuration**: See `driving_modes/carsim_config.json`

## Output Drivers

### Debug Driver
- Prints output values to console
- Useful for testing and debugging

### UDP Driver
- Sends telemetry data via UDP
- Configuration: `output/configs/udp.json`
- Default: localhost:5005

### HTTP Driver
- Sends data via HTTP POST requests
- Configuration: `output/configs/http.json`
- Supports custom endpoints

### Serial Driver
- Sends data via serial port
- Configuration: `output/configs/serial.json`
- Useful for hardware integration

## Configuration Files

### Input Configuration
Located in `input/` directory. Defines:
- Controller type and mapping
- Input axis assignments
- Deadzone settings

### Output Configuration
Located in `output/configs/` directory. Specifies:
- Output driver type
- Connection parameters
- Data format settings

## GUI Features

The application includes a real-time GUI that displays:
- Current input values (steering, throttle, brake, clutch)
- Active driving mode
- Connected output drivers

## Telemetry Output

The application streams the following telemetry data:
- **Steering**: Wheel rotation angle (-1.0 to 1.0)
- **Throttle**: Accelerator pedal position (0.0 to 1.0)
- **Brake**: Brake pedal position (0.0 to 1.0)
- **Clutch**: Clutch pedal position (0.0 to 1.0)
- **Gear**: Current transmission gear
- **RPM**: Engine RPM (CarSim mode)
- **Speed**: Vehicle speed (CarSim mode)
- **Power**: Engine power output

## Development

### Adding a New Output Driver

1. Create a new file in `output/drivers/`
2. Inherit from `BaseDriver`
3. Implement required methods:
   - `connect()`
   - `send()`
   - `disconnect()`
4. Add configuration file to `output/configs/`

### Adding a New Driving Mode

1. Create a new file in `driving_modes/`
2. Inherit from `BaseMode`
3. Implement the processing logic
4. Register in main.py

## Troubleshooting

### Controller Not Detected
- Check that the steering wheel is connected and powered on
- Verify pygame can access the device
- Run with debug driver to see raw input values

### Output Not Receiving Data
- Verify network connectivity for UDP/HTTP modes
- Check serial port settings for serial mode
- Confirm output configuration file paths

### Performance Issues
- Close other applications using the controller
- Reduce GUI refresh rate if needed
- Check CPU usage with debug driver

## Support

For issues, questions, or contributions, please refer to the project repository or contact the maintainer.

---

**Last Updated**: February 2026

