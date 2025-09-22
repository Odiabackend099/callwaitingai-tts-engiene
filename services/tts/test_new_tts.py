#!/usr/bin/env python3
"""
Quick test for the new TTS engine foundation
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def test_piper_installation():
    """Test if Piper is properly installed"""
    try:
        result = subprocess.run(["piper", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Piper installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Piper not working properly")
            return False
    except Exception as e:
        print(f"❌ Piper not found: {e}")
        return False

def test_voice_models():
    """Test if voice models exist"""
    voices_dir = Path("voices")
    required_voices = ["en_US-lessac-medium", "en_US-ryan-high"]
    
    all_good = True
    for voice_id in required_voices:
        voice_dir = voices_dir / voice_id
        model_file = voice_dir / f"{voice_id}.onnx"
        config_file = voice_dir / f"{voice_id}.onnx.json"
        
        if model_file.exists() and config_file.exists():
            model_size = model_file.stat().st_size
            print(f"✅ {voice_id}: Model ({model_size // 1_000_000}MB), Config OK")
        else:
            print(f"❌ {voice_id}: Missing files")
            all_good = False
    
    return all_good

def test_simple_synthesis():
    """Test simple synthesis"""
    try:
        # Test with Lessac model
        voice_dir = Path("voices/en_US-lessac-medium")
        model_file = voice_dir / "en_US-lessac-medium.onnx"
        config_file = voice_dir / "en_US-lessac-medium.onnx.json"
        
        if not (model_file.exists() and config_file.exists()):
            print("❌ Lessac model files missing")
            return False
        
        # Create test output
        test_output = "test_output.wav"
        
        # Run Piper synthesis
        cmd = [
            "piper",
            "--model", str(model_file),
            "--config", str(config_file),
            "--output_file", test_output
        ]
        
        print("🔊 Testing synthesis...")
        process = subprocess.run(
            cmd,
            input="Hello, this is a test of the new TTS engine.",
            text=True,
            capture_output=True,
            timeout=30
        )
        
        if process.returncode == 0:
            if os.path.exists(test_output):
                file_size = os.path.getsize(test_output)
                print(f"✅ Synthesis successful: {file_size} bytes")
                
                # Clean up
                os.remove(test_output)
                return True
            else:
                print("❌ No output file generated")
                return False
        else:
            print(f"❌ Synthesis failed: {process.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Synthesis test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing New TTS Engine Foundation")
    print("=" * 50)
    
    tests = [
        ("Piper Installation", test_piper_installation),
        ("Voice Models", test_voice_models),
        ("Simple Synthesis", test_simple_synthesis)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        try:
            if test_func():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}\n")
    
    print("=" * 50)
    print(f"🏆 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 NEW TTS ENGINE FOUNDATION IS WORKING!")
        print("✅ Ready for realistic voice generation")
    else:
        print("🔧 Some issues need to be fixed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
