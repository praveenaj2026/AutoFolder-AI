"""
AutoFolder AI - Installer Build Script
Automates the creation of the Windows installer using Inno Setup
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_step(message):
    """Print a step message"""
    print(f"\n{Colors.OKBLUE}➜ {message}{Colors.ENDC}")

def print_success(message):
    """Print a success message"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_error(message):
    """Print an error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_warning(message):
    """Print a warning message"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def find_inno_setup():
    """Find Inno Setup compiler executable"""
    possible_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup\ISCC.exe",
        r"C:\Program Files\Inno Setup\ISCC.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def check_prerequisites():
    """Check if all prerequisites are met"""
    print_step("Checking prerequisites...")
    
    # Check if dist folder exists
    dist_folder = Path("dist/AutoFolder AI")
    if not dist_folder.exists():
        print_error(f"Distribution folder not found: {dist_folder}")
        print("Please run 'python build.py' first to create the PyInstaller build.")
        return False
    
    print_success(f"Found distribution folder: {dist_folder}")
    
    # Check if main executable exists
    exe_path = dist_folder / "AutoFolder AI.exe"
    if not exe_path.exists():
        print_error(f"Main executable not found: {exe_path}")
        return False
    
    print_success(f"Found main executable: {exe_path}")
    
    # Check for Inno Setup
    iscc = find_inno_setup()
    if not iscc:
        print_error("Inno Setup not found!")
        print("\nPlease install Inno Setup from: https://jrsoftware.org/isdl.php")
        print("Download 'Inno Setup 6' and install it with default settings.")
        return False
    
    print_success(f"Found Inno Setup: {iscc}")
    
    # Check if installer script exists
    script_path = Path("autofolder_installer.iss")
    if not script_path.exists():
        print_error(f"Installer script not found: {script_path}")
        return False
    
    print_success(f"Found installer script: {script_path}")
    
    # Check if LICENSE file exists
    license_path = Path("LICENSE")
    if not license_path.exists():
        print_warning("LICENSE file not found - installer will skip license page")
    else:
        print_success(f"Found LICENSE file")
    
    return True

def build_installer():
    """Build the installer using Inno Setup"""
    print_step("Building installer...")
    
    iscc = find_inno_setup()
    script_path = Path("autofolder_installer.iss").absolute()
    
    try:
        # Run Inno Setup compiler
        result = subprocess.run(
            [iscc, str(script_path)],
            capture_output=True,
            text=True,
            check=True
        )
        
        print(result.stdout)
        print_success("Installer built successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print_error("Failed to build installer!")
        print("\nError output:")
        print(e.stderr)
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def show_results():
    """Show the results and next steps"""
    output_dir = Path("installer_output")
    
    if output_dir.exists():
        print_step("Build Results:")
        print(f"\n{Colors.OKGREEN}Installer created successfully!{Colors.ENDC}\n")
        
        # Find the setup executable
        setup_files = list(output_dir.glob("AutoFolder-AI-Setup-*.exe"))
        if setup_files:
            setup_file = setup_files[0]
            file_size = setup_file.stat().st_size / (1024 * 1024)  # Convert to MB
            
            print(f"  📦 File: {setup_file.name}")
            print(f"  📏 Size: {file_size:.1f} MB")
            print(f"  📁 Location: {setup_file.absolute()}\n")
            
            print(f"{Colors.HEADER}Next Steps:{Colors.ENDC}")
            print("  1. Test the installer on a clean Windows system")
            print("  2. Verify all features work after installation")
            print("  3. Test the uninstaller")
            print("  4. Sign the installer (optional, for commercial distribution)")
            print("  5. Upload to your distribution platform\n")
        else:
            print_warning("Setup file not found in output directory")
    else:
        print_error("Output directory not found")

def main():
    """Main build process"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}  AutoFolder AI - Installer Builder{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    
    # Check prerequisites
    if not check_prerequisites():
        print_error("\nPrerequisites not met. Please fix the issues above and try again.")
        sys.exit(1)
    
    # Build installer
    if not build_installer():
        print_error("\nInstaller build failed.")
        sys.exit(1)
    
    # Show results
    show_results()
    
    print(f"\n{Colors.OKGREEN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}  Build completed successfully!{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{'='*60}{Colors.ENDC}\n")

if __name__ == "__main__":
    main()
