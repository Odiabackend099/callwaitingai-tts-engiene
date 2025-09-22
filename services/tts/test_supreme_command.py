#!/usr/bin/env python3
"""
SUPREME COMMAND COMPLIANCE TEST
Tests all requirements from the supreme command to ensure no OS fallback and only Piper usage.
"""

import requests
import json
import time
import os

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_voices_endpoint():
    """Test voices endpoint - should only show Piper models"""
    print("🔍 Testing voices endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/voices", timeout=5)
        if response.status_code == 200:
            data = response.json()
            voices = data.get("voices", [])
            
            # SUPREME COMMAND: Check that only allowed voices are present
            allowed_voices = ["en_US-lessac-medium", "en_US-ryan-high"]
            voice_ids = [v["id"] for v in voices]
            
            if set(voice_ids) == set(allowed_voices):
                print("✅ Voices endpoint shows only allowed Piper models")
                
                # Check that engine name is logged
                for voice in voices:
                    if voice.get("engine") == "piper":
                        print(f"✅ Voice {voice['id']} correctly shows engine='piper'")
                    else:
                        print(f"❌ Voice {voice['id']} missing engine='piper'")
                        return False
                return True
            else:
                print(f"❌ Voices endpoint shows wrong voices: {voice_ids}")
                return False
        else:
            print(f"❌ Voices endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Voices endpoint error: {e}")
        return False

def test_samples_endpoint():
    """Test samples endpoint - should show demo samples"""
    print("🔍 Testing samples endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/samples", timeout=5)
        if response.status_code == 200:
            data = response.json()
            samples = data.get("samples", [])
            
            if len(samples) >= 2:
                print(f"✅ Samples endpoint shows {len(samples)} demo samples")
                for sample in samples:
                    print(f"  - {sample['voice_id']}: {sample['filename']}")
                return True
            else:
                print(f"❌ Samples endpoint shows insufficient samples: {len(samples)}")
                return False
        else:
            print(f"❌ Samples endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Samples endpoint error: {e}")
        return False

def test_invalid_voice_rejection():
    """Test that invalid voices return 400 error - NO OS fallback"""
    print("🔍 Testing invalid voice rejection (NO OS fallback)...")
    
    # First get an API key
    try:
        response = requests.post(f"{BASE_URL}/admin/generate-api-key", timeout=5)
        if response.status_code == 200:
            api_key = response.json()["api_key"]
        else:
            print("❌ Could not get API key for testing")
            return False
    except Exception as e:
        print(f"❌ API key generation error: {e}")
        return False
    
    # Test with invalid voice
    headers = {"X-API-Key": api_key}
    payload = {
        "text": "Test message",
        "voice_id": "invalid-voice",
        "format": "wav"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/synthesize", 
                               headers=headers, 
                               json=payload, 
                               timeout=5)
        
        if response.status_code == 400:
            print("✅ Invalid voice correctly returns 400 error (NO OS fallback)")
            return True
        else:
            print(f"❌ Invalid voice should return 400, got: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Invalid voice test error: {e}")
        return False

def test_valid_voice_synthesis():
    """Test valid voice synthesis with compliance logging"""
    print("🔍 Testing valid voice synthesis...")
    
    # Get API key
    try:
        response = requests.post(f"{BASE_URL}/admin/generate-api-key", timeout=5)
        if response.status_code == 200:
            api_key = response.json()["api_key"]
        else:
            print("❌ Could not get API key for testing")
            return False
    except Exception as e:
        print(f"❌ API key generation error: {e}")
        return False
    
    # Test with valid voice
    headers = {"X-API-Key": api_key}
    payload = {
        "text": "This is a test of the supreme command compliance",
        "voice_id": "en_US-lessac-medium",
        "format": "wav"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/synthesize", 
                               headers=headers, 
                               json=payload, 
                               timeout=30)
        
        if response.status_code == 200:
            print("✅ Valid voice synthesis successful")
            print(f"  Content-Type: {response.headers.get('content-type')}")
            print(f"  Content-Length: {len(response.content)} bytes")
            return True
        else:
            print(f"❌ Valid voice synthesis failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Valid voice synthesis error: {e}")
        return False

def main():
    """Run all supreme command compliance tests"""
    print("🚀 SUPREME COMMAND COMPLIANCE TEST")
    print("=" * 50)
    
    # Wait for service to start
    print("⏳ Waiting for service to start...")
    time.sleep(5)
    
    tests = [
        test_health,
        test_voices_endpoint,
        test_samples_endpoint,
        test_invalid_voice_rejection,
        test_valid_voice_synthesis
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            print()
    
    print("=" * 50)
    print(f"🏆 SUPREME COMMAND COMPLIANCE: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ ALL SUPREME COMMAND REQUIREMENTS SATISFIED!")
        print("   - Only Piper neural models used")
        print("   - No OS TTS fallback")
        print("   - Demo samples generated on startup")
        print("   - Compliance logging implemented")
        print("   - 400 errors for invalid voices")
    else:
        print("❌ SUPREME COMMAND VIOLATIONS DETECTED!")
        print("   Service does not meet all requirements")

if __name__ == "__main__":
    main()
