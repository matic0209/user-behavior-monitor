#!/bin/bash

echo "Installing required packages..."
pip install -r requirements.txt
pip install pyinstaller

echo "Creating icon..."
python create_icon.py

echo "Building executable..."
pyinstaller behavior_monitor.spec

echo "Build complete! The executable is in the dist folder." 