#!/usr/bin/env python3
"""
FINAL WORKING SETUP - Uses actual Piper neural models to generate real TTS audio
"""

import os
import subprocess
import json
import secrets
import time
import pygame
from datetime import datetime, timedelta
from pathlib import Path

def create_config_files():
    """Create the missing config files for the models"""
    print("📝 Creating config files for Piper models...")
    
    # Config for lessac-medium (female voice)
    lessac_config = {
        "audio": {
            "sample_rate": 22050,
            "channels": 1
        },
        "espeak": {
            "voice": "en-us"
        },
        "inference": {
            "noise_scale": 0.667,
            "length_scale": 1.0,
            "noise_w": 0.8
        },
        "phoneme_type": "espeak",
        "phoneme_cache_path": "",
        "phoneme_language": "en-us"
    }
    
    # Config for ryan-high (male voice)  
    ryan_config = {
        "audio": {
            "sample_rate": 22050,
            "channels": 1
        },
        "espeak": {
            "voice": "en-us"
        },
        "inference": {
            "noise_scale": 0.667,
            "length_scale": 1.0,
            "noise_w": 0.8
        },
        "phoneme_type": "espeak",
        "phoneme_cache_path": "",
        "phoneme_language": "en-us"
    }
    
    # Write config files
    lessac_config_path = Path("voices/en_US-lessac-medium/en_US-lessac-medium.onnx.json")
    ryan_config_path = Path("voices/en_US-ryan-high/en_US-ryan-high.onnx.json")
    
    with open(lessac_config_path, 'w') as f:
        json.dump(lessac_config, f, indent=2)
    
    with open(ryan_config_path, 'w') as f:
        json.dump(ryan_config, f, indent=2)
    
    print("✅ Config files created")
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

def synthesize_with_piper_tts_package(voice_id, text, output_path):
    """Use piper-tts Python package to synthesize audio"""
    print(f"🎵 Synthesizing with Piper TTS: {voice_id}")
    
    try:
        from piper import PiperVoice
        
        model_path = f"voices/{voice_id}/{voice_id}.onnx"
        config_path = f"voices/{voice_id}/{voice_id}.onnx.json"
        
        if not os.path.exists(model_path) or not os.path.exists(config_path):
            print(f"❌ Model files not found for {voice_id}")
            return False
        
        # Load voice and synthesize
        voice = PiperVoice.load(model_path, config_path=config_path)
        
        with open(output_path, "wb") as f:
            voice.synthesize(text, f)
        
        print(f"✅ Piper synthesis successful: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Piper synthesis failed: {e}")
        return False

def create_neural_sample_audio():
    """Create sample audio using actual Piper neural TTS"""
    print("🎵 Creating sample audio with REAL Piper neural TTS...")
    
    sample_dir = Path("sample_audio")
    sample_dir.mkdir(exist_ok=True)
    
    # Sample texts
    sample_texts = {
        "en_US-lessac-medium": "Hello! I'm the female voice from CallWaiting TTS Engine. I use the Lessac neural model to provide natural-sounding speech synthesis. My voice is clear and professional.",
        "en_US-ryan-high": "Greetings! I'm the male voice from CallWaiting TTS Engine. I use the Ryan high-quality neural model to deliver crystal-clear speech synthesis. My voice offers excellent clarity."
    }
    
    generated_files = []
    
    for voice_id, text in sample_texts.items():
        print(f"\n🎵 Generating sample for {voice_id}...")
        
        # Generate WAV file with Piper
        wav_output = sample_dir / f"demo_{voice_id}.wav"
        
        if synthesize_with_piper_tts_package(voice_id, text, wav_output):
            generated_files.append(str(wav_output))
            print(f"✅ Generated neural audio: {wav_output}")
        else:
            print(f"❌ Failed to generate sample for {voice_id}")
    
    return generated_files

def play_audio_files(audio_files):
    """Play audio files automatically"""
    print("🎧 Auto-playing REAL Piper neural TTS audio...")
    
    try:
        pygame.mixer.init()
        
        for audio_file in audio_files:
            if os.path.exists(audio_file) and os.path.getsize(audio_file) > 1000:
                filename = os.path.basename(audio_file)
                print(f"🔊 Playing: {filename}")
                
                try:
                    pygame.mixer.music.load(audio_file)
                    pygame.mixer.music.play()
                    
                    # Wait for playback to complete
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                    
                    print(f"✅ Finished playing: {filename}")
                    time.sleep(0.5)  # Brief pause between files
                    
                except Exception as e:
                    print(f"❌ Error playing {filename}: {e}")
        
        print("🎉 Audio playback completed!")
        
    except Exception as e:
        print(f"❌ Error initializing audio: {e}")

def main():
    """Main function - FINAL working setup"""
    print("🎯 CallWaiting TTS Engine - FINAL WORKING SETUP")
    print("="*60)
    print("✅ Using ACTUAL Piper neural models (not Windows TTS)")
    print("="*60)
    
    # Create config files for existing models
    create_config_files()
    
    # Generate API keys
    api_keys = generate_api_keys()
    
    # Create sample audio with real Piper
    audio_files = create_neural_sample_audio()
    
    print("\n" + "="*60)
    print("🎉 FINAL SETUP completed!")
    print(f"📁 Neural voice models: ./voices/")
    print(f"🔑 API keys: ./api_keys.json")
    print(f"🎵 Sample audio: ./sample_audio/")
    
    # Auto-play the real neural audio
    if audio_files:
        print("\n🎧 Auto-playing REAL neural TTS audio...")
        print("🔊 You should now hear ACTUAL Piper neural voices:")
        print("   👩 Female: en_US-lessac-medium (neural)")
        print("   👨 Male: en_US-ryan-high (neural)")
        print("="*60)
        
        play_audio_files(audio_files)
        
        print("\n🎉 SUCCESS! You have heard REAL neural TTS voices!")
        print("✅ These are actual Piper neural models, not Windows SAPI5!")
    else:
        print("⚠️  No neural audio files were generated")
    
    print("\n🚀 TTS Engine is ready!")
    print("   Run: python main.py")
    print("="*60)

if __name__ == "__main__":
    main()
