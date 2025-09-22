#!/usr/bin/env python3
"""
Automatic setup script for CallWaiting TTS Engine
Downloads voice models, generates API keys, and creates sample audio
"""

import json
import os
import asyncio
import httpx
import logging
import subprocess
import tempfile
import time
import pygame
from datetime import datetime, timedelta
import secrets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def download_voice_models():
    """Download voice models if not already present"""
    voices_dir = "voices"
    os.makedirs(voices_dir, exist_ok=True)
    
    voice_models = {
        "lessac-medium": {
            "model_url": "https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
            "config_url": "https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
        },
        "ryan-high": {
            "model_url": "https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_US/ryan/high/en_US-ryan-high.onnx",
            "config_url": "https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_US/ryan/high/en_US-ryan-high.onnx.json"
        }
    }
    
    async with httpx.AsyncClient() as client:
        for voice_id, urls in voice_models.items():
            voice_dir = os.path.join(voices_dir, voice_id)
            os.makedirs(voice_dir, exist_ok=True)
            
            model_path = os.path.join(voice_dir, f"{voice_id}.onnx")
            config_path = os.path.join(voice_dir, f"{voice_id}.json")
            
            # Download model if not exists
            if not os.path.exists(model_path):
                logger.info(f"Downloading {voice_id} model...")
                try:
                    response = await client.get(urls["model_url"])
                    response.raise_for_status()
                    
                    with open(model_path, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info(f"Downloaded {voice_id} model ({len(response.content)} bytes)")
                except Exception as e:
                    logger.error(f"Failed to download {voice_id} model: {e}")
            else:
                logger.info(f"{voice_id} model already exists")
            
            # Download config if not exists
            if not os.path.exists(config_path):
                logger.info(f"Downloading {voice_id} config...")
                try:
                    response = await client.get(urls["config_url"])
                    response.raise_for_status()
                    
                    with open(config_path, 'w') as f:
                        f.write(response.text)
                    
                    logger.info(f"Downloaded {voice_id} config")
                except Exception as e:
                    logger.error(f"Failed to download {voice_id} config: {e}")
            else:
                logger.info(f"{voice_id} config already exists")

def generate_api_keys():
    """Generate 10 API keys"""
    api_keys_file = "api_keys.json"
    
    # Load existing keys if any
    if os.path.exists(api_keys_file):
        with open(api_keys_file, 'r') as f:
            keys = json.load(f)
    else:
        keys = {}
    
    # Generate 10 new keys
    new_keys = []
    for i in range(10):
        key = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(days=365)).isoformat()
        
        keys[key] = {
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at,
            "rate_limit": {"requests": 0, "window_start": datetime.now().isoformat()}
        }
        
        new_keys.append(key)
        logger.info(f"Generated API key {i+1}: {key}")
    
    # Save keys
    with open(api_keys_file, 'w') as f:
        json.dump(keys, f, indent=2)
    
    logger.info(f"Generated {len(new_keys)} API keys and saved to {api_keys_file}")
    return new_keys

def create_directories():
    """Create necessary directories"""
    directories = ["voices", "generated_audio", "sample_audio"]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def generate_sample_audio():
    """Generate sample audio files for both voices"""
    
    # Sample texts for demonstration
    sample_texts = {
        "lessac-medium": "Hello! I'm the female voice from CallWaiting TTS Engine. I use the Lessac medium quality model to provide natural-sounding speech synthesis.",
        "ryan-high": "Greetings! I'm the male voice from CallWaiting TTS Engine. I use the Ryan high quality model to deliver clear and professional speech synthesis."
    }
    
    voices_dir = "voices"
    output_dir = "sample_audio"
    os.makedirs(output_dir, exist_ok=True)
    
    generated_files = []
    
    for voice_id, text in sample_texts.items():
        print(f"Generating sample audio for {voice_id}...")
        
        # Check if voice model exists
        model_path = os.path.join(voices_dir, voice_id, f"{voice_id}.onnx")
        config_path = os.path.join(voices_dir, voice_id, f"{voice_id}.json")
        
        if not os.path.exists(model_path) or not os.path.exists(config_path):
            print(f"⚠️  Voice model not found for {voice_id}, skipping...")
            continue
        
        # Generate WAV file
        wav_output = os.path.join(output_dir, f"demo_{voice_id}.wav")
        
        try:
            cmd = [
                "piper",
                "--model", model_path,
                "--config", config_path,
                "--output_file", wav_output
            ]
            
            result = subprocess.run(
                cmd,
                input=text,
                text=True,
                capture_output=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"✅ Generated {wav_output}")
                generated_files.append(wav_output)
            else:
                print(f"❌ Failed to generate {voice_id}: {result.stderr.decode()}")
                
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout generating {voice_id}")
        except Exception as e:
            print(f"❌ Error generating {voice_id}: {e}")
    
    return generated_files

def play_audio_files(audio_files):
    """Play audio files automatically"""
    try:
        # Initialize pygame mixer
        pygame.mixer.init()
        
        for audio_file in audio_files:
            if os.path.exists(audio_file):
                print(f"🎵 Playing: {audio_file}")
                
                # Load and play the audio
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                
                # Wait for the audio to finish playing
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                # Brief pause between files
                time.sleep(0.5)
        
        print("🎉 Audio playback completed!")
        
    except Exception as e:
        print(f"❌ Error playing audio: {e}")
        print("💡 You can manually play the files in the sample_audio directory")

async def main():
    """Main setup function"""
    print("🎯 Setting up CallWaiting TTS Engine...")
    print("="*60)
    
    # Create directories
    create_directories()
    
    # Download voice models
    print("📥 Downloading voice models...")
    await download_voice_models()
    
    # Generate API keys
    print("🔑 Generating API keys...")
    api_keys = generate_api_keys()
    
    # Generate sample audio
    print("🎵 Generating sample audio files...")
    audio_files = generate_sample_audio()
    
    print("\n" + "="*60)
    print("🎉 Setup completed successfully!")
    print(f"📁 Voice models: ./voices/")
    print(f"🔑 API keys: ./api_keys.json")
    print(f"📊 Generated {len(api_keys)} API keys")
    print(f"🎵 Generated {len(audio_files)} audio files")
    
    # Auto-play the audio files
    if audio_files:
        print("\n🎧 Auto-playing sample audio files...")
        print("🔊 You should hear both voices now:")
        print("   👩 Female voice (Lessac-medium)")
        print("   👨 Male voice (Ryan-high)")
        print("="*60)
        
        play_audio_files(audio_files)
    else:
        print("⚠️  No audio files were generated")
    
    print("\n🚀 To start the TTS service:")
    print("   python main.py")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())

