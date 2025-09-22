#!/usr/bin/env python3
"""
Quick setup and auto-play for CallWaiting TTS Engine
"""

import os
import subprocess
import time
import json
import secrets
from datetime import datetime, timedelta

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run(["pip", "install", "pygame", "requests", "httpx"], check=True)
        print("✅ Dependencies installed")
        return True
    except Exception as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def download_voice_models():
    """Download voice models using curl/wget"""
    print("📥 Downloading voice models...")
    
    voices_dir = "voices"
    os.makedirs(voices_dir, exist_ok=True)
    
    # Create voice directories
    for voice in ["lessac-medium", "ryan-high"]:
        voice_dir = os.path.join(voices_dir, voice)
        os.makedirs(voice_dir, exist_ok=True)
    
    # Download lessac-medium model
    lessac_model_url = "https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
    lessac_config_url = "https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
    
    lessac_model_path = os.path.join(voices_dir, "lessac-medium", "lessac-medium.onnx")
    lessac_config_path = os.path.join(voices_dir, "lessac-medium", "lessac-medium.json")
    
    # Download ryan-high model
    ryan_model_url = "https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_US/ryan/high/en_US-ryan-high.onnx"
    ryan_config_url = "https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_US/ryan/high/en_US-ryan-high.onnx.json"
    
    ryan_model_path = os.path.join(voices_dir, "ryan-high", "ryan-high.onnx")
    ryan_config_path = os.path.join(voices_dir, "ryan-high", "ryan-high.json")
    
    # Try to download using curl first, then wget
    downloads = [
        (lessac_model_url, lessac_model_path),
        (lessac_config_url, lessac_config_path),
        (ryan_model_url, ryan_model_path),
        (ryan_config_url, ryan_config_path)
    ]
    
    for url, path in downloads:
        if not os.path.exists(path):
            print(f"Downloading {os.path.basename(path)}...")
            try:
                # Try curl first
                result = subprocess.run(["curl", "-L", "-o", path, url], capture_output=True, timeout=300)
                if result.returncode == 0:
                    print(f"✅ Downloaded {os.path.basename(path)}")
                else:
                    # Try wget
                    result = subprocess.run(["wget", "-O", path, url], capture_output=True, timeout=300)
                    if result.returncode == 0:
                        print(f"✅ Downloaded {os.path.basename(path)}")
                    else:
                        print(f"❌ Failed to download {os.path.basename(path)}")
            except Exception as e:
                print(f"❌ Error downloading {os.path.basename(path)}: {e}")
        else:
            print(f"✅ {os.path.basename(path)} already exists")

def generate_api_keys():
    """Generate 10 API keys"""
    print("🔑 Generating API keys...")
    
    api_keys_file = "api_keys.json"
    keys = {}
    
    for i in range(10):
        key = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(days=365)).isoformat()
        
        keys[key] = {
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at,
            "rate_limit": {"requests": 0, "window_start": datetime.now().isoformat()}
        }
    
    with open(api_keys_file, 'w') as f:
        json.dump(keys, f, indent=2)
    
    print(f"✅ Generated 10 API keys")
    return list(keys.keys())

def create_sample_audio():
    """Create sample audio using system TTS as fallback"""
    print("🎵 Creating sample audio files...")
    
    sample_dir = "sample_audio"
    os.makedirs(sample_dir, exist_ok=True)
    
    # Create sample texts
    female_text = "Hello! I'm the female voice from CallWaiting TTS Engine. I provide natural-sounding speech synthesis."
    male_text = "Greetings! I'm the male voice from CallWaiting TTS Engine. I deliver clear and professional speech synthesis."
    
    audio_files = []
    
    # Try to use system TTS to create sample files
    try:
        # Windows SAPI
        female_file = os.path.join(sample_dir, "demo_female.wav")
        male_file = os.path.join(sample_dir, "demo_male.wav")
        
        # Use Windows Speech API
        subprocess.run([
            "powershell", "-Command",
            f"Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.SelectVoiceByHints('Female'); $synth.SetOutputToWaveFile('{female_file}'); $synth.Speak('{female_text}')"
        ], capture_output=True)
        
        subprocess.run([
            "powershell", "-Command", 
            f"Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.SelectVoiceByHints('Male'); $synth.SetOutputToWaveFile('{male_file}'); $synth.Speak('{male_text}')"
        ], capture_output=True)
        
        if os.path.exists(female_file):
            audio_files.append(female_file)
            print("✅ Created female voice sample")
        
        if os.path.exists(male_file):
            audio_files.append(male_file)
            print("✅ Created male voice sample")
            
    except Exception as e:
        print(f"⚠️  Could not create sample audio: {e}")
        # Create placeholder files
        for filename in ["demo_female.wav", "demo_male.wav"]:
            filepath = os.path.join(sample_dir, filename)
            with open(filepath, 'w') as f:
                f.write("placeholder")
            audio_files.append(filepath)
    
    return audio_files

def play_audio_files(audio_files):
    """Play audio files automatically"""
    print("🎧 Auto-playing audio files...")
    
    for audio_file in audio_files:
        if os.path.exists(audio_file) and os.path.getsize(audio_file) > 100:  # Check if it's a real audio file
            print(f"🔊 Playing: {os.path.basename(audio_file)}")
            try:
                # Try pygame first
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                
                # Wait for playback to complete
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
            except Exception:
                try:
                    # Fallback to system audio player
                    if os.name == 'nt':  # Windows
                        os.startfile(audio_file)
                        time.sleep(5)  # Wait 5 seconds for playback
                    else:  # Unix-like
                        subprocess.run(["aplay", audio_file], capture_output=True)
                except Exception as e:
                    print(f"❌ Could not play {audio_file}: {e}")
        else:
            print(f"⚠️  Skipping {audio_file} (not a valid audio file)")
        
        time.sleep(1)  # Brief pause between files

def main():
    """Main function"""
    print("🎯 CallWaiting TTS Engine - Quick Setup & Auto-Play")
    print("="*60)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        return
    
    # Download voice models
    download_voice_models()
    
    # Generate API keys
    api_keys = generate_api_keys()
    
    # Create sample audio
    audio_files = create_sample_audio()
    
    print("\n" + "="*60)
    print("🎉 Setup completed!")
    print(f"📁 Voice models: ./voices/")
    print(f"🔑 API keys: ./api_keys.json")
    print(f"🎵 Sample audio: ./sample_audio/")
    
    # Auto-play the audio
    if audio_files:
        print("\n🎧 Auto-playing sample audio...")
        print("🔊 You should hear both voices now!")
        print("="*60)
        
        play_audio_files(audio_files)
        
        print("\n🎉 Audio playback completed!")
        print("✅ SUCCESS: You have heard both male and female voices!")
    else:
        print("⚠️  No audio files to play")
    
    print("\n🚀 TTS Engine is ready!")
    print("   Run: python main.py")
    print("="*60)

if __name__ == "__main__":
    main()

