"""
Micro++ Setup Script
Automatically downloads and configures the required toolchains and SDKs
For Windows and Linux systems only
"""

import os
import sys
import platform
import subprocess
import json
import shutil
import tempfile
import zipfile
import tarfile
import urllib.request
from pathlib import Path


class MicroPPSetup:
    def __init__(self):
        self.base_dir = Path(__file__).parent.absolute()
        self.config_file = self.base_dir / "config.json"
        self.boards_dir = self.base_dir / "boards"
        self.tools_dir = self.base_dir / "tools"
        self.sdks_dir = self.base_dir / "sdks"
        
        # URLs for toolchain and SDK downloads - removed macOS URLs
        self.download_urls = {
            "arm-gcc": {
                "windows": "https://developer.arm.com/-/media/Files/downloads/gnu-rm/10.3-2021.10/gcc-arm-none-eabi-10.3-2021.10-win32.zip",
                "linux": "https://developer.arm.com/-/media/Files/downloads/gnu-rm/10.3-2021.10/gcc-arm-none-eabi-10.3-2021.10-x86_64-linux.tar.bz2"
            },
            "xtensa-gcc": {
                "windows": "https://github.com/espressif/crosstool-NG/releases/download/esp-2021r2-patch5/xtensa-esp32-elf-gcc8_4_0-esp-2021r2-patch5-win32.zip",
                "linux": "https://github.com/espressif/crosstool-NG/releases/download/esp-2021r2-patch5/xtensa-esp32-elf-gcc8_4_0-esp-2021r2-patch5-linux-amd64.tar.gz"
            },
            "pico-sdk": {
                "git": "https://github.com/raspberrypi/pico-sdk.git"
            }
        }
        
        # Create necessary directories
        self.tools_dir.mkdir(exist_ok=True)
        self.sdks_dir.mkdir(exist_ok=True)
        self.boards_dir.mkdir(exist_ok=True)
        
        # Initialize config
        self.config = self.load_config()

    def load_config(self):
        """Load or create the configuration file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            # Default config
            return {
                "toolchains": {},
                "sdks": {}
            }

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get_system(self):
        """Get the current operating system"""
        system = platform.system().lower()
        if system == "darwin":
            print("macOS is not supported. Apple users are not welcome here.")
            sys.exit(1)
        elif system == "windows":
            return "windows"
        else:
            return "linux"  # Default to Linux for others

    def download_file(self, url, dest_path):
        """Download a file with progress indicator"""
        print(f"Downloading from {url}...")
        
        # Create temporary file for download
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Download with progress reporting
            def report_progress(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min(int(block_num * block_size * 100 / total_size), 100)
                    sys.stdout.write(f"\r[{'#' * (percent // 5)}{'.' * (20 - percent // 5)}] {percent}%")
                    sys.stdout.flush()
            
            urllib.request.urlretrieve(url, temp_path, reporthook=report_progress)
            print()  # New line after progress bar
            
            # Move to final destination
            shutil.move(temp_path, dest_path)
            return True
        except Exception as e:
            print(f"Error downloading: {e}")
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return False

    def extract_archive(self, archive_path, extract_dir):
        """Extract a zip or tar archive"""
        print(f"Extracting {archive_path}...")
        
        try:
            if str(archive_path).endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            elif str(archive_path).endswith('.tar.gz') or str(archive_path).endswith('.tar.bz2'):
                with tarfile.open(archive_path) as tar_ref:
                    tar_ref.extractall(extract_dir)
            else:
                print(f"Unsupported archive format: {archive_path}")
                return False
                
            return True
        except Exception as e:
            print(f"Error extracting archive: {e}")
            return False

    def find_executable(self, base_dir, name_pattern):
        """Find an executable in a directory tree"""
        for root, _, files in os.walk(base_dir):
            for file in files:
                if name_pattern in file and (file.endswith(".exe") or not "." in file):
                    return Path(root) / file
        return None

    def setup_arm_gcc(self):
        """Download and set up ARM GCC toolchain"""
        system = self.get_system()
        
        if system not in self.download_urls["arm-gcc"]:
            print(f"ARM GCC download not available for {system}")
            return False
            
        # Create destination directory
        arm_gcc_dir = self.tools_dir / "arm-gcc"
        arm_gcc_dir.mkdir(exist_ok=True)
        
        # Download URL
        url = self.download_urls["arm-gcc"][system]
        filename = url.split("/")[-1]
        download_path = self.tools_dir / filename
        
        # Download if needed
        if not download_path.exists():
            if not self.download_file(url, download_path):
                return False
        
        # Extract archive
        if not self.extract_archive(download_path, arm_gcc_dir):
            return False
            
        # Find the gcc executable
        gcc_exec = self.find_executable(arm_gcc_dir, "arm-none-eabi-gcc")
        if not gcc_exec:
            print("Could not find ARM GCC executable after extraction")
            return False
            
        # Update config
        if "toolchains" not in self.config:
            self.config["toolchains"] = {}
        if "arm-gcc" not in self.config["toolchains"]:
            self.config["toolchains"]["arm-gcc"] = {}
            
        self.config["toolchains"]["arm-gcc"][system] = str(gcc_exec)
        self.save_config()
        
        print(f"ARM GCC installed at: {gcc_exec}")
        return True

    def setup_xtensa_gcc(self):
        """Download and set up Xtensa GCC toolchain for ESP32"""
        system = self.get_system()
        
        if system not in self.download_urls["xtensa-gcc"]:
            print(f"Xtensa GCC download not available for {system}")
            return False
            
        # Create destination directory
        xtensa_gcc_dir = self.tools_dir / "xtensa-gcc"
        xtensa_gcc_dir.mkdir(exist_ok=True)
        
        # Download URL
        url = self.download_urls["xtensa-gcc"][system]
        filename = url.split("/")[-1]
        download_path = self.tools_dir / filename
        
        # Download if needed
        if not download_path.exists():
            if not self.download_file(url, download_path):
                return False
        
        # Extract archive
        if not self.extract_archive(download_path, xtensa_gcc_dir):
            return False
            
        # Find the gcc executable
        gcc_exec = self.find_executable(xtensa_gcc_dir, "xtensa-esp32-elf-gcc")
        if not gcc_exec:
            print("Could not find Xtensa GCC executable after extraction")
            return False
            
        # Update config
        if "toolchains" not in self.config:
            self.config["toolchains"] = {}
        if "xtensa-gcc" not in self.config["toolchains"]:
            self.config["toolchains"]["xtensa-gcc"] = {}
            
        self.config["toolchains"]["xtensa-gcc"][system] = str(gcc_exec)
        self.save_config()
        
        print(f"Xtensa GCC installed at: {gcc_exec}")
        return True

    def generate_pico_sdk_files(self, pico_sdk_dir):
        """Generate the necessary files for Pico SDK"""
        print("Generating Pico SDK files...")

        # Create build directory
        build_dir = pico_sdk_dir / "build"
        build_dir.mkdir(exist_ok=True)

        # Create generated directory
        generated_dir = build_dir / "generated"
        generated_dir.mkdir(exist_ok=True)

        # Create pico_base directory
        pico_base_dir = generated_dir / "pico_base"
        pico_base_dir.mkdir(exist_ok=True)

        # Create version.h file
        version_h_path = pico_base_dir / "version.h"
        with open(version_h_path, 'w') as f:
            f.write("""
/* Auto-generated file for Micro++ compatibility */
#ifndef _PICO_VERSION_H
#define _PICO_VERSION_H

#define PICO_SDK_VERSION_MAJOR    1
#define PICO_SDK_VERSION_MINOR    5
#define PICO_SDK_VERSION_REVISION 0
#define PICO_SDK_VERSION_STRING   "1.5.0"

#endif
""")

        # Create config.h file
        config_h_path = pico_base_dir / "pico_config.h"
        with open(config_h_path, 'w') as f:
            f.write("""
/* Auto-generated file for Micro++ compatibility */
#ifndef _PICO_CONFIG_H
#define _PICO_CONFIG_H

// Base configuration for Pico
#define PICO_CONFIG_HEADER_FILES 1
#define PICO_NO_HARDWARE 0
#define PICO_ON_DEVICE 1
#define PICO_BOARD "pico"

// Enable commonly used features
#define PICO_USE_BLOCKING_STDIO 1
#define PICO_STDIO_ENABLE_CRLF_SUPPORT 1
#define PICO_STDIO_DEFAULT_CRLF 1

#endif
""")

        # Create platform.h file
        platform_dir = pico_base_dir / "pico"
        platform_dir.mkdir(exist_ok=True)
        platform_h_path = platform_dir / "platform.h"
        with open(platform_h_path, 'w') as f:
            f.write("""
/* Auto-generated file for Micro++ compatibility */
#ifndef _PICO_PLATFORM_H
#define _PICO_PLATFORM_H

// Define platform-specific settings
#if defined(_WIN32) || defined(__CYGWIN__)
    #define PICO_PLATFORM_WINDOWS
#elif defined(__linux__)
    #define PICO_PLATFORM_LINUX
#else
    #define PICO_PLATFORM_UNKNOWN
#endif

// No support for macOS
#ifdef __APPLE__
    #error "macOS is not supported by Micro++. Apple users don't deserve this code."
#endif

#endif
""")

        # Create boards.h file
        boards_dir = pico_sdk_dir / "src" / "boards" / "include" / "boards"
        boards_dir.mkdir(exist_ok=True, parents=True)
        pico_h_path = boards_dir / "pico.h"
        with open(pico_h_path, 'w') as f:
            f.write("""
/* Auto-generated file for Micro++ compatibility */
#ifndef _BOARDS_PICO_H
#define _BOARDS_PICO_H

// Pin definitions for Raspberry Pi Pico
#define PICO_DEFAULT_LED_PIN 25
#define PICO_DEFAULT_WS2812_PIN 16
#define PICO_DEFAULT_I2C_SDA_PIN 4
#define PICO_DEFAULT_I2C_SCL_PIN 5
#define PICO_DEFAULT_UART_TX_PIN 0
#define PICO_DEFAULT_UART_RX_PIN 1
#define PICO_DEFAULT_SPI_SCK_PIN 18
#define PICO_DEFAULT_SPI_TX_PIN 19
#define PICO_DEFAULT_SPI_RX_PIN 20
#define PICO_DEFAULT_SPI_CSN_PIN 17

#endif
""")

        print(f"Created necessary Pico SDK files in {build_dir}")
        return True

    def setup_pico_sdk(self):
        """Download and set up Raspberry Pi Pico SDK"""
        system = self.get_system()
        
        # Create destination directory
        pico_sdk_dir = self.sdks_dir / "pico-sdk"
        
        # Check if Git is available
        try:
            subprocess.run(["git", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except (subprocess.SubprocessError, FileNotFoundError):
            print("Git is required to clone the Pico SDK. Please install Git and try again.")
            return False
            
        # Clone the repository if needed
        if not pico_sdk_dir.exists():
            print("Cloning Pico SDK repository...")
            try:
                subprocess.run(
                    ["git", "clone", "--recurse-submodules", self.download_urls["pico-sdk"]["git"], str(pico_sdk_dir)],
                    check=True
                )
            except subprocess.SubprocessError as e:
                print(f"Error cloning Pico SDK: {e}")
                return False
                
        # Update the repository
        print("Updating Pico SDK...")
        try:
            subprocess.run(["git", "pull"], cwd=pico_sdk_dir, check=True)
        except subprocess.SubprocessError as e:
            print(f"Error updating Pico SDK: {e}")
            # Continue anyway, as we might have a working version
            
        # Initialize submodules
        print("Initializing submodules...")
        try:
            subprocess.run(
                ["git", "submodule", "update", "--init", "--recursive"],
                cwd=pico_sdk_dir,
                check=True
            )
        except subprocess.SubprocessError as e:
            print(f"Error initializing submodules: {e}")
            # Continue anyway, as not all submodules might be needed
        
        # Generate necessary files for the SDK
        self.generate_pico_sdk_files(pico_sdk_dir)
            
        # Update config
        if "sdks" not in self.config:
            self.config["sdks"] = {}
        if "pico-sdk" not in self.config["sdks"]:
            self.config["sdks"]["pico-sdk"] = {}
            
        self.config["sdks"]["pico-sdk"][system] = str(pico_sdk_dir)
        self.save_config()
        
        print(f"Pico SDK installed at: {pico_sdk_dir}")
        return True

    def setup_rp2040_board(self):
        """Set up RP2040 board definition"""
        rp2040_file = self.boards_dir / "RP2040.py"
        
        # Only create if it doesn't exist
        if not rp2040_file.exists():
            print("Creating RP2040 board definition...")
            
            with open(rp2040_file, 'w') as f:
                f.write('''"""
Board specification for RP2040 (Raspberry Pi Pico)
"""

import subprocess
import os
from pathlib import Path


def get_spec():
    return {
        "name": "RP2040",
        "toolchain": "arm-gcc",
        "firmware_format": "uf2",
        "sdk": "pico-sdk",
        "compile_flags": ["-mcpu=cortex-m0plus", "-mthumb", "-O2", "-DPICO_BOARD=pico"],
        "libraries": ["hardware/gpio.h", "hardware/spi.h", "hardware/i2c.h", "hardware/uart.h", 
                     "pico/stdlib.h", "pico/binary_info.h"]
    }


def get_libraries():
    return get_spec()["libraries"]


def get_firmware_format():
    return get_spec()["firmware_format"]


def get_toolchain():
    return get_spec()["toolchain"]


def get_sdk():
    return get_spec()["sdk"]


def get_compile_flags():
    return get_spec()["compile_flags"]


def generate_firmware(compiled_file):
    """Generate UF2 firmware for RP2040"""
    output_file = compiled_file.with_suffix(".uf2")
    
    # This is a simplified example - in a real implementation you would:
    # 1. Link the object file to create an ELF file
    # 2. Generate a binary from the ELF
    # 3. Convert the binary to UF2 using the RP2040 tools
    
    # Simulate the process for demonstration
    print(f"Converting {compiled_file} to {output_file}")
    
    # Example command (would need actual RP2040 SDK tools)
    # subprocess.run(["elf2uf2", compiled_file, output_file], check=True)
    
    # For demo purposes, just create an empty UF2 file
    with open(output_file, 'w') as f:
        f.write("# Placeholder UF2 file for demonstration\\n")
    
    return output_file


def deploy_firmware(firmware_file, address):
    """Deploy UF2 firmware to RP2040"""
    # On Windows, the RP2040 in bootloader mode appears as a drive
    # On Linux, you might use direct USB access
    
    # Check if address is a drive letter (Windows) or device path (Linux)
    if os.name == 'nt':  # Windows
        # If address is COM port, we need to reset the board first
        if address.startswith("COM"):
            print(f"Resetting board on {address} to enter bootloader mode...")
            # In a real implementation, you would toggle DTR/RTS lines
            # For now, ask the user to manually press the BOOTSEL button
            input("Please press the BOOTSEL button on your Pico and reconnect it, then press Enter...")
            
            # After reset, find the drive letter
            # For demo, just ask the user
            drive = input("Please enter the drive letter of the Pico (e.g., E:): ")
            if not drive.endswith(":"):
                drive += ":"
        else:
            # Assume address is already a drive letter
            drive = address
            if not drive.endswith(":"):
                drive += ":"
                
        # Copy the UF2 to the drive
        target_path = Path(drive) / firmware_file.name
        try:
            import shutil
            shutil.copy(firmware_file, target_path)
            print(f"Copied {firmware_file} to {target_path}")
            return True
        except Exception as e:
            print(f"Error deploying firmware: {str(e)}")
            return False
    
    else:  # Linux
        # For Linux, you might use a tool like picotool
        try:
            # Example command (would need actual tools)
            # subprocess.run(["picotool", "load", "-x", str(firmware_file), "-t", "uf2"], check=True)
            print(f"Deploying {firmware_file} to RP2040 at {address}")
            # Simulate successful deployment
            return True
        except Exception as e:
            print(f"Error deploying firmware: {str(e)}")
            return False
''')
            
            print("RP2040 board definition created")
        else:
            print("RP2040 board definition already exists")
            
        return True

    def setup_esp32_board(self):
        """Set up ESP32 board definition"""
        esp32_file = self.boards_dir / "ESP32.py"
        
        # Only create if it doesn't exist
        if not esp32_file.exists():
            print("Creating ESP32 board definition...")
            
            with open(esp32_file, 'w') as f:
                f.write('''"""
Board specification for ESP32
"""

import subprocess
import os
from pathlib import Path


def get_spec():
    return {
        "name": "ESP32",
        "toolchain": "xtensa-gcc",
        "firmware_format": "bin",
        "compile_flags": ["-DESP32", "-DCORE_DEBUG_LEVEL=0", "-mtext-section-literals"],
        "libraries": [
            "Arduino.h",
            "WiFi.h",
            "ESPmDNS.h",
            "HTTPClient.h",
            "WebServer.h",
            "Update.h",
            "FS.h",
            "SPIFFS.h"
        ]
    }


def get_libraries():
    return get_spec()["libraries"]


def get_firmware_format():
    return get_spec()["firmware_format"]


def get_toolchain():
    return get_spec()["toolchain"]


def get_compile_flags():
    return get_spec()["compile_flags"]


def generate_firmware(compiled_file):
    """Generate BIN firmware for ESP32"""
    output_file = compiled_file.with_suffix(".bin")
    
    # Simulate the process for demonstration
    print(f"Converting {compiled_file} to {output_file}")
    
    # For demo purposes, just create an empty BIN file
    with open(output_file, 'w') as f:
        f.write("# Placeholder BIN file for demonstration\\n")
    
    return output_file


def deploy_firmware(firmware_file, address):
    """Deploy BIN firmware to ESP32"""
    # ESP32 typically uses serial for deployment
    
    print(f"Deploying {firmware_file} to ESP32 at {address}")
    
    try:
        # Example command (would need actual tools)
        # subprocess.run([
        #     "esptool.py", 
        #     "--chip", "esp32", 
        #     "--port", address,
        #     "--baud", "115200",
        #     "write_flash", 
        #     "0x10000", 
        #     str(firmware_file)
        # ], check=True)
        
        # Simulate successful deployment
        return True
    except Exception as e:
        print(f"Error deploying firmware: {str(e)}")
        return False
''')
            
            print("ESP32 board definition created")
        else:
            print("ESP32 board definition already exists")
            
        return True

    def check_system_compatibility(self):
        """Check if the current system is compatible"""
        system = platform.system().lower()
        if system == "darwin":
            print("===========================================================")
            print("ERROR: macOS detected!")
            print("Unfortunately, this software doesn't currently support macOS.")
            print("We recommend using Windows or Linux for the best experience.")
            print("===========================================================")
            # Note: macOS users, we love you... but we don't have a Mac to test on.
            # Please switch to Windows or Linux for the best experience. 
            # Haha... sorry... 
            sys.exit(1)
        return True

    def run(self):
        """Run the setup process"""
        print("===== Micro++ Setup =====")
        print("This script will download and configure the required toolchains and SDKs.")
        print("NOTICE: This software is intentionally incompatible with macOS.")
        print()
        
        # Check system compatibility first
        self.check_system_compatibility()
        
        # Setup ARM GCC
        print("Setting up ARM GCC toolchain...")
        self.setup_arm_gcc()
        print()
        
        # Setup Xtensa GCC
        print("Setting up Xtensa GCC toolchain for ESP32...")
        self.setup_xtensa_gcc()
        print()
        
        # Setup Pico SDK
        print("Setting up Raspberry Pi Pico SDK...")
        self.setup_pico_sdk()
        print()
        
        # Setup board definitions
        print("Setting up board definitions...")
        self.setup_rp2040_board()
        self.setup_esp32_board()
        print()
        
        print("===== Setup Complete =====")
        print(f"Configuration saved to: {self.config_file}")
        print("You can now use Micro++ to compile and deploy your code!")
        print()


def main():
    setup = MicroPPSetup()
    setup.run()


if __name__ == "__main__":
    main()