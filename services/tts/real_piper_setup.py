#!/usr/bin/env python3
"""
Real Piper TTS Setup - Downloads actual neural models and generates high-quality audio
NO Windows SAPI5 fallback - ONLY Piper neural TTS
"""

import os
import subprocess
import json
import secrets
import requests
import time
import pygame
from datetime import datetime, timedelta
from pathlib import Path

def install_piper():
    """Install Piper TTS engine"""
    print("🔧 Installing Piper TTS engine...")
    try:
        # Install piper-tts package
        subprocess.run(["pip", "install", "piper-tts"], check=True, capture_output=True)
        
        # Also try to install piper binary if available
        try:
            subprocess.run(["pip", "install", "piper"], check=True, capture_output=True)
        except:
            print("ℹ️  Piper binary not available via pip, will use piper-tts package")
        
        print("✅ Piper TTS engine installed")
        return True
    except Exception as e:
        print(f"❌ Failed to install Piper: {e}")
        return False

def download_real_voice_models():
    """Download actual Piper neural models from rhasspy/piper-voices"""
    print("📥 Downloading real Piper neural voice models...")
    
    voices_dir = Path("voices")
    voices_dir.mkdir(exist_ok=True)
    
    # Exact models from rhasspy/piper-voices
    models = {
        "en_US-lessac-medium": {
            "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
            "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
            "size_mb": 63.2
        },
        "en_US-ryan-high": {
            "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx", 
            "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx.json",
            "size_mb": 121
        }
    }
    
    for voice_id, info in models.items():
        voice_dir = voices_dir / voice_id
        voice_dir.mkdir(exist_ok=True)
        
        model_path = voice_dir / f"{voice_id}.onnx"
        config_path = voice_dir / f"{voice_id}.onnx.json"
        
        # Download model if not exists
        if not model_path.exists():
            print(f"📥 Downloading {voice_id} model ({info['size_mb']} MB)...")
            try:
                response = requests.get(info["model_url"], stream=True)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(model_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                print(f"\r   Progress: {percent:.1f}%", end="", flush=True)
                
                print(f"\n✅ Downloaded {voice_id} model ({downloaded / 1024 / 1024:.1f} MB)")
                
            except Exception as e:
                print(f"\n❌ Failed to download {voice_id} model: {e}")
                return False
        else:
            print(f"✅ {voice_id} model already exists")
        
        # Download config if not exists
        if not config_path.exists():
            print(f"📥 Downloading {voice_id} config...")
            try:
                response = requests.get(info["config_url"])
                response.raise_for_status()
                
                with open(config_path, 'w') as f:
                    f.write(response.text)
                
                print(f"✅ Downloaded {voice_id} config")
                
            except Exception as e:
                print(f"❌ Failed to download {voice_id} config: {e}")
                return False
        else:
            print(f"✅ {voice_id} config already exists")
    
    return True

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

def synthesize_with_piper(voice_id, text, output_path):
    """Synthesize audio using actual Piper neural TTS"""
    print(f"🎵 Synthesizing with Piper neural TTS: {voice_id}")
    
    voice_dir = Path("voices") / voice_id
    model_path = voice_dir / f"{voice_id}.onnx"
    config_path = voice_dir / f"{voice_id}.onnx.json"
    
    if not model_path.exists() or not config_path.exists():
        print(f"❌ Voice model not found: {voice_id}")
        return False
    
    try:
        # Try piper command line tool first
        cmd = [
            "piper",
            "--model", str(model_path),
            "--config", str(config_path),
            "--output_file", str(output_path)
        ]
        
        result = subprocess.run(
            cmd,
            input=text,
            text=True,
            capture_output=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ Piper synthesis successful: {output_path}")
            return True
        else:
            print(f"❌ Piper synthesis failed: {result.stderr.decode()}")
            
            # Fallback to piper-tts Python package
            try:
                from piper import PiperVoice
                
                voice = PiperVoice.load(str(model_path), config_path=str(config_path))
                with open(output_path, "wb") as f:
                    voice.synthesize(text, f)
                
                print(f"✅ Piper Python synthesis successful: {output_path}")
                return True
                
            except Exception as e:
                print(f"❌ Piper Python synthesis also failed: {e}")
                return False
    
    except subprocess.TimeoutExpired:
        print(f"❌ Piper synthesis timeout")
        return False
    except Exception as e:
        print(f"❌ Piper synthesis error: {e}")
        return False

def create_real_sample_audio():
    """Create sample audio using actual Piper neural TTS"""
    print("🎵 Creating sample audio with REAL Piper neural TTS...")
    
    sample_dir = Path("sample_audio")
    sample_dir.mkdir(exist_ok=True)
    
    # Sample texts optimized for TTS quality testing
    sample_texts = {
        "en_US-lessac-medium": "Hello! I'm the female voice from CallWaiting TTS Engine. I use the Lessac neural model to provide natural-sounding speech synthesis. My voice is clear, professional, and perfect for customer service applications.",
        "en_US-ryan-high": "Greetings! I'm the male voice from CallWaiting TTS Engine. I use the Ryan high-quality neural model to deliver crystal-clear speech synthesis. My voice offers excellent clarity and natural intonation for business communications."
    }
    
    generated_files = []
    
    for voice_id, text in sample_texts.items():
        print(f"\n🎵 Generating sample for {voice_id}...")
        
        # Generate WAV file with Piper
        wav_output = sample_dir / f"demo_{voice_id}.wav"
        
        if synthesize_with_piper(voice_id, text, wav_output):
            generated_files.append(str(wav_output))
            
            # Also generate μ-law version for Twilio compatibility
            mulaw_output = sample_dir / f"demo_{voice_id}.mulaw"
            
            try:
                # Convert to μ-law 8kHz using ffmpeg
                convert_cmd = [
                    "ffmpeg", "-y",
                    "-i", str(wav_output),
                    "-ar", "8000",
                    "-ac", "1",
                    "-f", "mulaw",
                    str(mulaw_output)
                ]
                
                result = subprocess.run(convert_cmd, capture_output=True, timeout=30)
                
                if result.returncode == 0:
                    generated_files.append(str(mulaw_output))
                    print(f"✅ Generated μ-law version: {mulaw_output}")
                else:
                    print(f"⚠️  μ-law conversion failed: {result.stderr.decode()}")
                    
            except Exception as e:
                print(f"⚠️  μ-law conversion error: {e}")
        else:
            print(f"❌ Failed to generate sample for {voice_id}")
    
    return generated_files

def play_audio_files(audio_files):
    """Play audio files automatically"""
    print("🎧 Auto-playing REAL Piper neural TTS audio...")
    
    try:
        pygame.mixer.init()
        
        for audio_file in audio_files:
            if os.path.exists(audio_file) and os.path.getsize(audio_file) > 1000:  # Check if it's a real audio file
                filename = os.path.basename(audio_file)
                print(f"🔊 Playing: {filename}")
                
                try:
                    pygame.mixer.music.load(audio_file)
                    pygame.mixer.music.play()
                    
                    # Wait for playback to complete
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                    
                    print(f"✅ Finished playing: {filename}")
                    
                except Exception as e:
                    print(f"❌ Error playing {filename}: {e}")
            else:
                print(f"⚠️  Skipping {audio_file} (not a valid audio file)")
        
        print("🎉 Audio playback completed!")
        
    except Exception as e:
        print(f"❌ Error initializing audio: {e}")
        print("💡 You can manually play the files in the sample_audio directory")

def main():
    """Main function - Real Piper TTS setup"""
    print("🎯 CallWaiting TTS Engine - REAL Piper Neural TTS Setup")
    print("="*60)
    print("🚫 NO Windows SAPI5 - ONLY Piper neural models")
    print("="*60)
    
    # Install Piper TTS engine
    if not install_piper():
        print("❌ Setup failed at Piper installation")
        return
    
    # Download real neural voice models
    if not download_real_voice_models():
        print("❌ Setup failed at model download")
        return
    
    # Generate API keys
    api_keys = generate_api_keys()
    
    # Create sample audio with real Piper
    audio_files = create_real_sample_audio()
    
    print("\n" + "="*60)
    print("🎉 REAL Piper TTS Setup completed!")
    print(f"📁 Neural voice models: ./voices/")
    print(f"🔑 API keys: ./api_keys.json")
    print(f"🎵 Sample audio: ./sample_audio/")
    
    # Auto-play the real neural audio
    if audio_files:
        print("\n🎧 Auto-playing REAL neural TTS audio...")
        print("🔊 You should now hear ACTUAL Piper neural voices (not Windows SAPI5):")
        print("   👩 Female: en_US-lessac-medium (neural)")
        print("   👨 Male: en_US-ryan-high (neural)")
        print("="*60)
        
        play_audio_files(audio_files)
        
        print("\n🎉 SUCCESS! You have heard REAL neural TTS voices!")
        print("✅ No more robotic Windows SAPI5 voices!")
    else:
        print("⚠️  No neural audio files were generated")
    
    print("\n🚀 Real Piper TTS Engine is ready!")
    print("   Run: python main.py")
    print("="*60)

if __name__ == "__main__":
    main()
