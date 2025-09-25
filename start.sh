#!/bin/bash

# MuxBot Startup Script

echo "Starting MuxBot..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.11.9"
    exit 1
fi

# Check if required system tools are installed
tools=("ffmpeg" "mkvmerge" "mediainfo" "aria2c" "rclone")
missing_tools=()

for tool in "${tools[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        missing_tools+=("$tool")
    fi
done

if [ ${#missing_tools[@]} -ne 0 ]; then
    echo "Missing required tools: ${missing_tools[*]}"
    echo "Please install them using your package manager"
    echo ""
    echo "Ubuntu/Debian:"
    echo "sudo apt update && sudo apt install ffmpeg mkvtoolnix mediainfo aria2 rclone"
    echo ""
    echo "CentOS/RHEL:"
    echo "sudo yum install ffmpeg mkvtoolnix mediainfo aria2 rclone"
    exit 1
fi

# Create necessary directories
mkdir -p downloads temp logs

# Check if .env file exists
if [ ! -f .env ]; then
    echo ".env file not found. Please create it from .env.example"
    exit 1
fi

# Install Python dependencies
if [ -f requirements.txt ]; then
    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

# Start the bot
echo "Starting MuxBot..."
python3 main.py