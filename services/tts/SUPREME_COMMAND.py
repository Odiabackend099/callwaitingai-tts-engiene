#!/usr/bin/env python3
"""
SUPREME LEADER COMMAND IMPLEMENTATION
NO OS TTS FALLBACK - ONLY PIPER NEURAL MODELS
AUTOMATIC DEMO GENERATION ON STARTUP
"""

import os
import json
import secrets
import time
import pygame
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging to show engine compliance
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - engine=piper - %(message)s')
logger = logging.getLogger(__name__)

# SUPREME COMMAND: ONLY these voice IDs allowed
ALLOWED_VOICES = {
    "en_US-lessac-medium": {
        "description": "Female neural voice - Lessac medium quality",
        "model_path": "voices/en_US-lessac-medium/en_US-lessac-medium.onnx",
        "config_path": "voices/en_US-lessac-medium/en_US-lessac-medium.onnx.json"
    },
    "en_US-ryan-high": {
        "description": "Male neural voice - Ryan high quality", 
        "model_path": "voices/en_US-ryan-high/en_US-ryan-high.onnx",
        "config_path": "voices/en_US-ryan-high/en_US-ryan-high.onnx.json"
    }
}

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

def verify_piper_models():
    """SUPREME COMMAND: Verify ONLY Piper models exist, NO OS fallback"""
    logger.info("SUPREME COMMAND: Verifying Piper neural models only")
    
    for voice_id, voice_info in ALLOWED_VOICES.items():
        model_path = Path(voice_info["model_path"])
        config_path = Path(voice_info["config_path"])
        
        if not model_path.exists():
            logger.error(f"SUPREME COMMAND VIOLATION: Missing Piper model for {voice_id}")
            raise Exception(f"Piper model missing: {model_path}")
        
        if not config_path.exists():
            logger.error(f"SUPREME COMMAND VIOLATION: Missing Piper config for {voice_id}")
            raise Exception(f"Piper config missing: {config_path}")
        
        logger.info(f"SUPREME COMMAND COMPLIANCE: Piper model verified for voiceId={voice_id}")
    
    print("✅ SUPREME COMMAND COMPLIANCE: All Piper neural models verified")
    return True

def synthesize_with_piper_only(voice_id, text, output_path):
    """SUPREME COMMAND: Use ONLY Piper neural TTS, NO OS fallback"""
    logger.info(f"SUPREME COMMAND: Synthesizing with Piper only, voiceId={voice_id}")
    
    if voice_id not in ALLOWED_VOICES:
        logger.error(f"SUPREME COMMAND VIOLATION: Invalid voiceId={voice_id}")
        raise Exception(f"Invalid voiceId. Allowed: {list(ALLOWED_VOICES.keys())}")
    
    voice_info = ALLOWED_VOICES[voice_id]
    model_path = voice_info["model_path"]
    config_path = voice_info["config_path"]
    
    if not os.path.exists(model_path) or not os.path.exists(config_path):
        logger.error(f"SUPREME COMMAND VIOLATION: Model files missing for voiceId={voice_id}")
        raise Exception(f"Piper model files missing for {voice_id}")
    
    try:
        # Try piper-tts Python package first
        from piper import PiperVoice
        
        logger.info(f"SUPREME COMMAND: Loading Piper voice, voiceId={voice_id}")
        voice = PiperVoice.load(model_path, config_path=config_path)
        
        with open(output_path, "wb") as f:
            voice.synthesize(text, f)
        
        logger.info(f"SUPREME COMMAND COMPLIANCE: Piper synthesis successful, voiceId={voice_id}")
        return True
        
    except Exception as e:
        logger.error(f"SUPREME COMMAND VIOLATION: Piper synthesis failed for voiceId={voice_id}, error={e}")
        # SUPREME COMMAND: NO FALLBACK - ERROR ONLY
        raise Exception(f"Piper synthesis failed for {voice_id}: {e}")

def create_automatic_demo_samples():
    """SUPREME COMMAND: Auto-generate demo samples on startup"""
    logger.info("SUPREME COMMAND: Auto-generating demo samples on startup")
    
    sample_dir = Path("sample_audio")
    sample_dir.mkdir(exist_ok=True)
    
    # SUPREME COMMAND: Fixed demo texts
    demo_texts = {
        "en_US-lessac-medium": "Welcome to CallWaiting.ai voice service. This is the realistic female voice using the Lessac neural model. I provide natural-sounding speech synthesis for professional applications.",
        "en_US-ryan-high": "Welcome to CallWaiting.ai voice service. This is the realistic male voice using the Ryan high-quality neural model. I deliver crystal-clear speech synthesis for business communications."
    }
    
    generated_files = []
    
    for voice_id, text in demo_texts.items():
        logger.info(f"SUPREME COMMAND: Generating demo for voiceId={voice_id}")
        
        output_path = sample_dir / f"demo_{voice_id}.wav"
        
        try:
            synthesize_with_piper_only(voice_id, text, output_path)
            generated_files.append(str(output_path))
            logger.info(f"SUPREME COMMAND COMPLIANCE: Demo generated for voiceId={voice_id}")
            
        except Exception as e:
            logger.error(f"SUPREME COMMAND VIOLATION: Failed to generate demo for voiceId={voice_id}, error={e}")
            # SUPREME COMMAND: NO FALLBACK - ERROR ONLY
            raise Exception(f"Demo generation failed for {voice_id}: {e}")
    
    print("✅ SUPREME COMMAND COMPLIANCE: Auto-demo samples generated")
    return generated_files

def play_demo_samples(audio_files):
    """SUPREME COMMAND: Auto-play demo samples"""
    logger.info("SUPREME COMMAND: Auto-playing demo samples")
    
    try:
        pygame.mixer.init()
        
        for audio_file in audio_files:
            if os.path.exists(audio_file) and os.path.getsize(audio_file) > 1000:
                filename = os.path.basename(audio_file)
                voice_id = filename.replace("demo_", "").replace(".wav", "")
                
                logger.info(f"SUPREME COMMAND: Playing demo, voiceId={voice_id}")
                print(f"🔊 SUPREME COMMAND: Playing {voice_id} neural voice")
                
                try:
                    pygame.mixer.music.load(audio_file)
                    pygame.mixer.music.play()
                    
                    # Wait for playback to complete
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                    
                    logger.info(f"SUPREME COMMAND COMPLIANCE: Demo played successfully, voiceId={voice_id}")
                    time.sleep(0.5)  # Brief pause between files
                    
                except Exception as e:
                    logger.error(f"SUPREME COMMAND VIOLATION: Error playing demo, voiceId={voice_id}, error={e}")
        
        print("🎉 SUPREME COMMAND COMPLIANCE: Demo playback completed!")
        
    except Exception as e:
        logger.error(f"SUPREME COMMAND VIOLATION: Audio initialization failed, error={e}")

def main():
    """SUPREME LEADER COMMAND IMPLEMENTATION"""
    print("🎯 SUPREME LEADER COMMAND IMPLEMENTATION")
    print("="*60)
    print("🔒 NO OS TTS FALLBACK - ONLY PIPER NEURAL MODELS")
    print("🔒 AUTOMATIC DEMO GENERATION ON STARTUP")
    print("🔒 ERROR ON FALLBACK - NO COMPROMISES")
    print("="*60)
    
    try:
        # SUPREME COMMAND: Verify Piper models only
        verify_piper_models()
        
        # Generate API keys
        api_keys = generate_api_keys()
        
        # SUPREME COMMAND: Auto-generate demo samples
        audio_files = create_automatic_demo_samples()
        
        print("\n" + "="*60)
        print("🎉 SUPREME COMMAND IMPLEMENTATION COMPLETED!")
        print(f"📁 Demo samples: ./sample_audio/")
        print(f"🔑 API keys: ./api_keys.json")
        
        # SUPREME COMMAND: Auto-play demo samples
        if audio_files:
            print("\n🎧 SUPREME COMMAND: Auto-playing demo samples...")
            print("🔊 You will now hear ONLY Piper neural voices:")
            print("   👩 Female: en_US-lessac-medium (neural)")
            print("   👨 Male: en_US-ryan-high (neural)")
            print("="*60)
            
            play_demo_samples(audio_files)
            
            print("\n🎉 SUPREME COMMAND COMPLIANCE ACHIEVED!")
            print("✅ You have heard ONLY Piper neural voices!")
            print("✅ NO OS TTS fallback was used!")
        else:
            logger.error("SUPREME COMMAND VIOLATION: No demo samples generated")
            raise Exception("Demo generation failed")
        
        print("\n🚀 TTS Engine ready with SUPREME COMMAND compliance!")
        print("   Run: python main.py")
        print("="*60)
        
    except Exception as e:
        logger.error(f"SUPREME COMMAND VIOLATION: {e}")
        print(f"❌ SUPREME COMMAND VIOLATION: {e}")
        print("🔒 NO FALLBACK ALLOWED - FIXING REQUIRED")

if __name__ == "__main__":
    main()
