#!/usr/bin/env python3
"""
Install pyautogui dependencies script for Windows Git Bash environment
Pure English version to avoid GBK encoding issues
"""

import sys
import subprocess
import importlib.util

def check_module(module_name):
    """Check if module is installed"""
    spec = importlib.util.find_spec(module_name)
    return spec is not None

def install_module(module_name):
    """Install module"""
    try:
        print(f"Installing {module_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
        print(f"[OK] {module_name} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {module_name} installation failed: {e}")
        return False

def install_from_requirements():
    """Try to install from requirements-test.txt"""
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_file = os.path.join(os.path.dirname(script_dir), "requirements-test.txt")
    
    if os.path.exists(requirements_file):
        try:
            print(f"Installing from {requirements_file}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
            print("[OK] All test dependencies installed from requirements file")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[WARNING] Requirements file installation failed: {e}")
            print("Falling back to individual module installation...")
            return False
    return False

def main():
    print("Checking and installing test script dependencies...")
    print("=" * 50)
    
    # Try requirements file first
    if install_from_requirements():
        print("\n[SUCCESS] Dependencies installed from requirements-test.txt")
        return True
    
    # Fallback to individual installation
    print("Installing individual modules...")
    modules_to_check = ["pyautogui", "pillow"]
    missing_modules = []
    
    # Check dependencies
    for module in modules_to_check:
        if check_module(module):
            print(f"[OK] {module} is already installed")
        else:
            print(f"[MISSING] {module} is not installed")
            missing_modules.append(module)
    
    if not missing_modules:
        print("\n[SUCCESS] All dependencies are installed!")
        
        # Test pyautogui functionality
        print("\nTesting pyautogui functionality...")
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            width, height = pyautogui.size()
            print(f"[OK] Screen resolution: {width}x{height}")
            print("[OK] pyautogui is working properly")
        except Exception as e:
            print(f"[WARNING] pyautogui test failed: {e}")
            print("This might need to run in Windows environment or install additional system dependencies")
        
        return True
    
    # Install missing modules
    print(f"\nNeed to install {len(missing_modules)} modules...")
    success = True
    
    for module in missing_modules:
        if not install_module(module):
            success = False
    
    if success:
        print("\n[SUCCESS] All dependencies installed successfully!")
        print("You can now run the test scripts")
    else:
        print("\n[ERROR] Some dependencies failed to install")
        print("Please run manually: pip install pyautogui pillow")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
