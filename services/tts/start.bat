@echo off
REM CallWaiting TTS Engine Startup Script for Windows

echo 🎯 Starting CallWaiting TTS Engine...
echo ==================================

REM Check if setup has been run
if not exist "api_keys.json" (
    echo ⚠️  First time setup detected. Running setup...
    python setup.py
    echo.
)

REM Check if voice models exist
if not exist "voices\lessac-medium" (
    echo ⚠️  Voice models not found. Running setup...
    python setup.py
    echo.
)

REM Check if sample audio exists
if not exist "sample_audio" (
    echo 📢 Generating sample audio files...
    python generate_samples.py
    echo.
)

echo 🚀 Starting TTS Engine server...
echo 📍 Server will be available at: http://localhost:8000
echo 📖 API Documentation: http://localhost:8000/docs
echo 🔑 API Keys available in: api_keys.json
echo.
echo Press Ctrl+C to stop the server
echo ==================================

REM Start the server
python main.py


