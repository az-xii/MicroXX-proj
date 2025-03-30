# Micro++

A powerful tool for compiling and deploying C++ code to microcontrollers.


## Overview

Micro++ simplifies the process of compiling C++ code and deploying it to various microcontroller platforms. It provides a unified interface for working with different boards, toolchains, and SDKs.

### Key Features

- **Multi-board support**: Pre-configured support for RP2040 (Raspberry Pi Pico) and ESP32
- **Extensible architecture**: Easily add new boards with JSON configuration
- **Integrated toolchain management**: Automatic setup of ARM GCC and Xtensa toolchains
- **SDK integration**: Built-in support for Raspberry Pi Pico SDK
- **Command-line interface**: Simple commands for all operations

## System Requirements

- **Operating Systems**: Windows or Linux
- **Dependencies**: Git (for SDK setup)

> **Note**: macOS is not currently supported. soeey

## Installation

1. Clone this repository:
```bash
git clone https://github.com/https://github.com/az-xii/MicroXX-proj
cd micropp
```

2. Run the setup script to download necessary toolchains and SDKs:
```bash
python setup.py
```

This will:
- Download and install ARM GCC toolchain
- Download and install Xtensa GCC toolchain for ESP32
- Clone the Raspberry Pi Pico SDK
- Set up board definitions for RP2040 and ESP32

## Usage

### List Available Boards

```bash
python micro++.py list-boards
```

### Add a New Board

Create a JSON file with your board specification, then:

```bash
python micro++.py add-board my_custom_board.json
```

### Configure Toolchains and SDKs

View current configuration:
```bash
python micro++.py config --show
```

Configure a toolchain:
```bash
python micro++.py config --toolchain arm-gcc --path /path/to/arm-gcc
```

Configure an SDK:
```bash
python micro++.py config --sdk pico-sdk --path /path/to/pico-sdk
```

### Compile and Deploy

```bash
python micro++.py compile --source path/to/source.cpp --board RP2040 --address E:
```

Compile only (without deployment):
```bash
python micro++.py compile --source path/to/source.cpp --board ESP32 --address /dev/ttyUSB0 --compile-only
```

With verbose output:
```bash
python micro++.py compile --source path/to/source.cpp --board RP2040 --address COM6 -v
```

## Board Definitions

Micro++ currently includes configurations for:

- **RP2040** (Raspberry Pi Pico): Uses ARM GCC toolchain and outputs UF2 firmware
- **ESP32**: Uses Xtensa GCC toolchain and outputs BIN firmware

### Adding Custom Boards

Create a JSON file with the following structure:

```json
{
  "name": "MyBoard",
  "toolchain": "arm-gcc",
  "firmware_format": "hex",
  "compile_flags": ["-mcpu=cortex-m4", "-mthumb", "-O2"],
  "libraries": ["header1.h", "header2.h"]
}
```

Then add it using:
```bash
python micro++.py add-board my_board.json
```

## Project Structure

```
micropp/
├── micro++.py      # Main tool
├── setup.py        # Setup script
├── config.json     # Configuration file
├── boards/         # Board definitions
├── tools/          # Toolchains
└── sdks/           # SDKs
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
