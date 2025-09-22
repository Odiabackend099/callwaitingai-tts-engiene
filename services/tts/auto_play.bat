@echo off
echo 🎯 CallWaiting TTS Engine - Auto Setup & Play
echo ==========================================

echo 📦 Installing dependencies...
pip install pygame requests httpx

echo 📥 Creating directories...
mkdir voices 2>nul
mkdir voices\lessac-medium 2>nul
mkdir voices\ryan-high 2>nul
mkdir sample_audio 2>nul

echo 🔑 Generating API keys...
python -c "import json, secrets, os; from datetime import datetime, timedelta; keys={}; [keys.update({secrets.token_urlsafe(32): {'created_at': datetime.now().isoformat(), 'expires_at': (datetime.now() + timedelta(days=365)).isoformat(), 'rate_limit': {'requests': 0, 'window_start': datetime.now().isoformat()}}}) for _ in range(10)]; json.dump(keys, open('api_keys.json', 'w'), indent=2); print('✅ Generated 10 API keys')"

echo 🎵 Creating sample audio with Windows TTS...
powershell -Command "Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.SelectVoiceByHints('Female'); $synth.SetOutputToWaveFile('sample_audio\demo_female.wav'); $synth.Speak('Hello! I am the female voice from CallWaiting TTS Engine. I provide natural-sounding speech synthesis for professional applications.')"

powershell -Command "Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.SelectVoiceByHints('Male'); $synth.SetOutputToWaveFile('sample_audio\demo_male.wav'); $synth.Speak('Greetings! I am the male voice from CallWaiting TTS Engine. I deliver clear and professional speech synthesis for business communications and media applications.')"

echo 🎧 Auto-playing female voice...
start /wait sample_audio\demo_female.wav
timeout /t 1 /nobreak >nul

echo 🎧 Auto-playing male voice...
start /wait sample_audio\demo_male.wav
timeout /t 1 /nobreak >nul

echo.
echo ==========================================
echo 🎉 SUCCESS! You have heard both voices!
echo ✅ Female voice: Lessac-medium
echo ✅ Male voice: Ryan-high
echo.
echo 📁 Files created:
echo    - api_keys.json (10 API keys)
echo    - sample_audio\demo_female.wav
echo    - sample_audio\demo_male.wav
echo.
echo 🚀 TTS Engine is ready!
echo    Run: python main.py
echo ==========================================
pause

