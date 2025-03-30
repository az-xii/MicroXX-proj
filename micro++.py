"""
Micro++ - A tool for compiling and deploying C++ code to microcontrollers
Compatible with Windows and Linux only
"""

import argparse
import os
import sys
import platform
import importlib.util
import subprocess
import json
import logging
from pathlib import Path
from typing import Optional


class MicroPP:
    def __init__(self):
        self.base_dir = Path(__file__).parent.absolute()
        self.boards_dir = self.base_dir / "boards"
        self.config_file = self.base_dir / "config.json"
        self.tools_dir = self.base_dir / "tools"
        self.sdks_dir = self.base_dir / "sdks"

        # Check for supported OS
        self.system = platform.system().lower()
        if self.system not in ['windows', 'linux']:
            self.exit_unsupported_os()

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger('micro++')

        # Load configuration
        self.load_config()

        # Ensure directories exist
        self.boards_dir.mkdir(exist_ok=True)
        self.tools_dir.mkdir(exist_ok=True)
        self.sdks_dir.mkdir(exist_ok=True)

    def exit_unsupported_os(self):
        """Exit with error message for unsupported OS (macOS)"""
        print("ERROR: This tool only supports Windows and Linux operating systems.")
        print("macOS is not supported. Please use a Windows or Linux machine instead.")
        sys.exit(1)

    def load_config(self):
        """Load configuration from config file or create default if not exists"""
        if not self.config_file.exists():
            self.logger.info("Creating default configuration")
            self.config = {
                "toolchains": {
                    "arm-gcc": {
                        "linux": "/usr/bin/arm-none-eabi-gcc",
                        "windows": "C:\\Program Files (x86)\\GNU Arm Embedded Toolchain\\bin\\arm-none-eabi-gcc.exe"
                    },
                    "xtensa-gcc": {
                        "linux": "/opt/xtensa-esp32-elf/bin/xtensa-esp32-elf-gcc",
                        "windows": "C:\\esp\\tools\\xtensa-esp32-elf\\bin\\xtensa-esp32-elf-gcc.exe"
                    }
                },
                "sdks": {}
            }
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        else:
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                # Validate minimum config structure
                if "toolchains" not in self.config:
                    self.config["toolchains"] = {}
                if "sdks" not in self.config:
                    self.config["sdks"] = {}
            except json.JSONDecodeError:
                self.logger.error(f"Invalid JSON in config file: {self.config_file}")
                self.logger.info("Creating new configuration")
                self.config = {"toolchains": {}, "sdks": {}}

    def save_config(self):
        """Save configuration to config file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def parse_args(self) -> argparse.Namespace:
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(
            description="Micro++ - Compile and deploy C++ to microcontrollers (Windows/Linux only)",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  List available boards:
    python micro++.py list-boards

  Add a new board:
    python micro++.py add-board my_board.json

  Compile and deploy to a board:
    python micro++.py compile --source C:\\PROJECTS\\MicroCC\\blink.cpp -b RP2040 -a E:

  Compile and deploy with verbose output:
    python micro++.py compile --source C:\\PROJECTS\\MicroCC\\blink.cpp -b ESP32 -a /dev/ttyUSB0 -v
            """
        )

        # Create subparsers for different command modes
        subparsers = parser.add_subparsers(dest='command', help='Command to execute')

        # Board management commands
        subparsers.add_parser('list-boards', help='List available boards')

        add_parser = subparsers.add_parser('add-board', help='Add a new board from JSON file')
        add_parser.add_argument('json_file', help='JSON file containing board specification')

        # Configuration commands
        config_parser = subparsers.add_parser('config', help='Configure toolchains and SDKs')
        config_parser.add_argument('--show', action='store_true', help='Show current configuration')
        config_parser.add_argument('--toolchain', choices=['arm-gcc', 'xtensa-gcc'],
                                  help='Configure a specific toolchain')
        config_parser.add_argument('--sdk', choices=['pico-sdk'],
                                  help='Configure a specific SDK')
        config_parser.add_argument('--path', help='Path to the toolchain or SDK')

        # Compile and deploy command
        compile_parser = subparsers.add_parser('compile', help='Compile and deploy code')
        compile_parser.add_argument('--source', type=str, required=True, help='Source file to compile')
        compile_parser.add_argument('-b', '--board', required=True, help='Target board')
        compile_parser.add_argument('-a', '--address', required=True,
                                  help='Address (e.g., COM6, /dev/ttyUSB0)')
        compile_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
        compile_parser.add_argument('--compile-only', action='store_true',
                                  help='Compile only, do not deploy')

        return parser.parse_args()

    def show_config(self):
        """Display current configuration"""
        print("Current Configuration:")
        print(json.dumps(self.config, indent=2))
        return True

    def configure_toolchain(self, toolchain_name, path):
        """Configure a toolchain with a custom path"""
        system = "windows" if platform.system().lower() == "windows" else "linux"
        
        if "toolchains" not in self.config:
            self.config["toolchains"] = {}
        if toolchain_name not in self.config["toolchains"]:
            self.config["toolchains"][toolchain_name] = {}
            
        self.config["toolchains"][toolchain_name][system] = path
        self.save_config()
        
        self.logger.info(f"Configured {toolchain_name} for {system}: {path}")
        return True

    def configure_sdk(self, sdk_name, path):
        """Configure an SDK with a custom path"""
        system = "windows" if platform.system().lower() == "windows" else "linux"
        
        if "sdks" not in self.config:
            self.config["sdks"] = {}
        if sdk_name not in self.config["sdks"]:
            self.config["sdks"][sdk_name] = {}
            
        self.config["sdks"][sdk_name][system] = path
        self.save_config()
        
        self.logger.info(f"Configured {sdk_name} for {system}: {path}")
        return True

    def list_available_boards(self):
        """List all available boards"""
        if not self.boards_dir.exists():
            self.logger.info("No boards directory found. Creating one...")
            self.boards_dir.mkdir(exist_ok=True)
            return False

        boards = [f.stem for f in self.boards_dir.glob("*.py") if f.is_file() and f.stem != "__init__"]

        if not boards:
            self.logger.info("No boards found. Use 'add-board' to add a new board.")
            return False

        print("Available boards:")
        for board in boards:
            # Try to load the board module to get more info
            board_module = self.load_board_module(board)
            if board_module and hasattr(board_module, 'get_spec'):
                spec = board_module.get_spec()
                print(f"  - {board}: {spec.get('name', board)}")
                if 'libraries' in spec:
                    print(f"    Supported libraries: {', '.join(lib.split('/')[-1] for lib in spec['libraries'][:3])}...")
            else:
                print(f"  - {board}")

        return True

    def add_new_board(self, json_file: str):
        """Add a new board from a JSON specification file"""
        try:
            json_path = Path(json_file)
            if not json_path.exists():
                self.logger.error(f"JSON file not found: {json_file}")
                return False

            with open(json_path, 'r') as f:
                board_spec = json.load(f)

            # Basic validation
            required_keys = ["name", "toolchain", "firmware_format", "compile_flags", "libraries"]
            missing_keys = [key for key in required_keys if key not in board_spec]
            if missing_keys:
                self.logger.error(f"Missing required keys in board specification: {', '.join(missing_keys)}")
                return False

            # Create board module
            board_name = board_spec["name"]
            board_file = self.boards_dir / f"{board_name}.py"

            # Ensure boards directory exists
            self.boards_dir.mkdir(exist_ok=True)

            with open(board_file, 'w') as f:
                f.write(f'''\"\"\"
Board specification for {board_name}
\"\"\"

def get_spec():
    return {board_spec}

def get_libraries():
    return {board_spec['libraries']}

def get_firmware_format():
    return "{board_spec['firmware_format']}"

def get_toolchain():
    return "{board_spec['toolchain']}"

def get_compile_flags():
    return {board_spec['compile_flags']}

def generate_firmware(compiled_file):
    # Board-specific firmware generation logic
    # This is a placeholder that should be customized
    print(f"Generating {get_firmware_format()} firmware for {{compiled_file}}")
    output_file = compiled_file.with_suffix(f".{{get_firmware_format()}}")

    # For demonstration purposes, just create an empty file
    with open(output_file, 'w') as f:
        f.write("# Placeholder firmware file\\n")

    return output_file

def deploy_firmware(firmware_file, address):
    # Board-specific deployment logic
    # This is a placeholder that should be customized
    print(f"Deploying {{firmware_file}} to {{address}}")
    # Example deployment command
    # subprocess.run(["tool", "flash", "-p", address, firmware_file])
    return True
''')
            self.logger.info(f"Added new board: {board_name}")
            return True
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in file: {json_file}")
            return False
        except Exception as e:
            self.logger.error(f"Error adding board: {str(e)}")
            return False

    def load_board_module(self, board_name: str):
        """Load a board module by name"""
        board_file = self.boards_dir / f"{board_name}.py"
        if not board_file.exists():
            self.logger.error(f"Board '{board_name}' not found")
            return None

        try:
            spec = importlib.util.spec_from_file_location(board_name, board_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except Exception as e:
            self.logger.error(f"Error loading board module: {str(e)}")
            return None

    def get_toolchain_path(self, toolchain_name: str) -> Optional[str]:
        """Get the toolchain path for the current OS"""
        system = "windows" if platform.system().lower() == "windows" else "linux"

        if toolchain_name not in self.config.get("toolchains", {}):
            self.logger.error(f"Toolchain '{toolchain_name}' not found in config")
            return None

        if system not in self.config["toolchains"][toolchain_name]:
            self.logger.error(f"Toolchain '{toolchain_name}' not configured for {system}")
            return None

        toolchain_path = self.config["toolchains"][toolchain_name][system]

        # Check if the toolchain exists
        if not Path(toolchain_path).exists():
            self.logger.error(f"Toolchain not found at: {toolchain_path}")
            self.logger.info("Run setup.py to install toolchains or update config")
            return None

        return toolchain_path

    def compile(self, source_file: str, board_module, verbose: bool = False) -> Optional[Path]:
        """Compile the source file for the target board"""
        toolchain_name = board_module.get_toolchain()
        toolchain_path = self.get_toolchain_path(toolchain_name)

        if not toolchain_path:
            return None

        source_path = Path(source_file)
        if not source_path.exists():
            self.logger.error(f"Source file not found: {source_file}")
            return None

        output_path = source_path.with_suffix(".o")

        # Get board-specific compile flags
        compile_flags = board_module.get_compile_flags()

        # Add SDK include paths if the board specifies an SDK
        if hasattr(board_module, 'get_sdk') and callable(getattr(board_module, 'get_sdk')):
            sdk_name = board_module.get_sdk()
            if sdk_name:
                system = "windows" if platform.system().lower() == "windows" else "linux"
                if sdk_name in self.config.get("sdks", {}) and system in self.config["sdks"][sdk_name]:
                    sdk_path = Path(self.config["sdks"][sdk_name][system])
                    if sdk_path.exists():
                        if sdk_name == "pico-sdk":
                            # Add Pico SDK include paths
                            sdk_include_paths = [
                                f"-I{sdk_path}/src/common/pico_stdlib_headers/include",
                                f"-I{sdk_path}/src/rp2_common/hardware_gpio/include",
                                f"-I{sdk_path}/src/rp2_common/pico_platform/include",
                                f"-I{sdk_path}/src/rp2040/hardware_regs/include",
                                f"-I{sdk_path}/src/common/pico_base_headers/include",
                                f"-I{sdk_path}/src/boards/include",
                                f"-I{sdk_path}/src/rp2_common/hardware_base/include",
                                f"-I{sdk_path}/src/rp2_common/hardware_sync/include",
                                f"-I{sdk_path}/src/rp2_common/hardware_irq/include",
                                f"-I{sdk_path}/src/rp2_common/hardware_timer/include",
                                f"-I{sdk_path}/build/generated/pico_base"  # Include generated files
                            ]
                            compile_flags.extend(sdk_include_paths)
                        if verbose:
                            self.logger.info(f"Using {sdk_name} at: {sdk_path}")
                    else:
                        self.logger.warning(f"SDK path not found: {sdk_path}")
                else:
                    self.logger.warning(f"SDK '{sdk_name}' not configured for {system}")

        # Build command
        cmd = [toolchain_path, "-c", str(source_path), "-o", str(output_path)]
        cmd.extend(compile_flags)

        # Execute compilation
        try:
            if verbose:
                self.logger.info(f"Executing: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                check=False,  # Don't raise exception, handle manually
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                self.logger.error("Compilation failed")
                self.logger.error(result.stderr)
                return None

            self.logger.info("Compilation successful")
            return output_path
        except Exception as e:
            self.logger.error(f"Compilation error: {str(e)}")
            return None

    def build_and_deploy(self, args):
        """Main workflow to build and deploy code"""
        # Load board module
        board_module = self.load_board_module(args.board)
        if not board_module:
            self.logger.error(f"Board '{args.board}' not supported")
            self.logger.info("Use 'list-boards' to see available boards")
            return False

        # Compile
        if args.verbose:
            self.logger.info(f"Compiling {args.source} for {args.board}...")
        compiled_file = self.compile(args.source, board_module, args.verbose)
        if not compiled_file:
            self.logger.error("Compilation failed")
            return False

        if args.compile_only:
            self.logger.info(f"Compilation successful: {compiled_file}")
            return True

        # Generate firmware
        try:
            if args.verbose:
                self.logger.info("Generating firmware...")
            firmware_file = board_module.generate_firmware(compiled_file)
            if not firmware_file or not firmware_file.exists():
                self.logger.error("Firmware generation failed")
                return False
        except Exception as e:
            self.logger.error(f"Error generating firmware: {str(e)}")
            return False

        # Deploy
        try:
            if args.verbose:
                self.logger.info(f"Deploying to {args.address}...")
            success = board_module.deploy_firmware(firmware_file, args.address)

            if success:
                self.logger.info(f"Successfully deployed {firmware_file.name}")
                return True
            else:
                self.logger.error("Deployment failed")
                return False
        except Exception as e:
            self.logger.error(f"Error during deployment: {str(e)}")
            return False

    def run(self):
        """Main entry point for the tool"""
        args = self.parse_args()

        # Set verbose logging if requested
        if hasattr(args, 'verbose') and args.verbose:
            self.logger.setLevel(logging.DEBUG)

        # Handle commands
        if args.command == 'list-boards':
            return 0 if self.list_available_boards() else 1

        elif args.command == 'add-board':
            return 0 if self.add_new_board(args.json_file) else 1

        elif args.command == 'config':
            if args.show:
                return 0 if self.show_config() else 1
            elif args.toolchain and args.path:
                return 0 if self.configure_toolchain(args.toolchain, args.path) else 1
            elif args.sdk and args.path:
                return 0 if self.configure_sdk(args.sdk, args.path) else 1
            else:
                self.logger.error("Invalid configuration command")
                return 1

        elif args.command == 'compile':
            return 0 if self.build_and_deploy(args) else 1

        else:
            self.logger.error(f"Unknown command: {args.command}")
            return 1


def main():
    tool = MicroPP()
    sys.exit(tool.run())


if __name__ == "__main__":
    main()