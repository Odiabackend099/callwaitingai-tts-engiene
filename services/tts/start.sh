#!/bin/bash

# CallWaiting TTS Engine Startup Script

echo "🎯 Starting CallWaiting TTS Engine..."
echo "=================================="

# Check if setup has been run
if [ ! -f "api_keys.json" ]; then
    echo "⚠️  First time setup detected. Running setup..."
    python setup.py
    echo ""
fi

# Check if voice models exist
if [ ! -d "voices/lessac-medium" ] || [ ! -d "voices/ryan-high" ]; then
    echo "⚠️  Voice models not found. Running setup..."
    python setup.py
    echo ""
fi

# Check if sample audio exists
if [ ! -d "sample_audio" ]; then
    echo "📢 Generating sample audio files..."
    python generate_samples.py
    echo ""
fi

echo "🚀 Starting TTS Engine server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔑 API Keys available in: api_keys.json"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="

# Start the server
python main.py


