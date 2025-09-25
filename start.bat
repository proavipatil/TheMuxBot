@echo off
title MuxBot Startup

echo Starting MuxBot...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.11.9 from python.org
    pause
    exit /b 1
)

REM Create necessary directories
if not exist "downloads" mkdir downloads
if not exist "temp" mkdir temp
if not exist "logs" mkdir logs

REM Check if .env file exists
if not exist ".env" (
    echo .env file not found. Please create it from .env.example
    pause
    exit /b 1
)

REM Install Python dependencies
if exist "requirements.txt" (
    echo Installing Python dependencies...
    pip install -r requirements.txt
)

REM Start the bot
echo Starting MuxBot...
python main.py

pause