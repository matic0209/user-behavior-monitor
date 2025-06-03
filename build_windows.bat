@echo off
echo Checking Python installation...
python --version
if errorlevel 1 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.8.10 from https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe
    pause
    exit /b 1
)

echo.
echo Installing required packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install requirements
    pause
    exit /b 1
)

pip install pyinstaller
if errorlevel 1 (
    echo Failed to install pyinstaller
    pause
    exit /b 1
)

echo.
echo Creating icon...
python create_icon.py
if errorlevel 1 (
    echo Failed to create icon
    pause
    exit /b 1
)

echo.
echo Building executable...
pyinstaller behavior_monitor.spec
if errorlevel 1 (
    echo Failed to build executable
    pause
    exit /b 1
)

echo.
echo Build complete! The executable is in the dist folder.
echo.
echo To run the application:
echo 1. Navigate to the dist folder
echo 2. Run behavior_monitor.exe
echo.
echo Note: You may need to run the application as administrator
echo to monitor keyboard and mouse events.
echo.
pause 