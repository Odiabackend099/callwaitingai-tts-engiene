#!/usr/bin/env python3
"""
Complete Test Suite for Fixed CallWaiting.ai TTS Engine
Validates realistic voice generation and all functionality
"""

import os
import sys
import json
import time
import asyncio
import subprocess
from pathlib import Path
from unittest.mock import patch
import tempfile
import shutil

import pytest
import httpx
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import after path setup
from main import app, tts_engine, PIPER_VOICES

class TestResults:
    """Enhanced test result tracking"""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
        self.start_time = time.time()
    
    def pass_test(self, test_name: str, details: str = ""):
        self.passed.append(f"✅ {test_name}: {details}")
        print(f"✅ PASS: {test_name}")
    
    def fail_test(self, test_name: str, error: str):
        self.failed.append(f"❌ {test_name}: {error}")
        print(f"❌ FAIL: {test_name} - {error}")
    
    def warn_test(self, test_name: str, warning: str):
        self.warnings.append(f"⚠️ {test_name}: {warning}")
        print(f"⚠️ WARN: {test_name} - {warning}")
    
    def print_final_report(self):
        duration = time.time() - self.start_time
        
        print("\n" + "="*70)
        print("🎯 FIXED TTS ENGINE TEST REPORT")
        print("="*70)
        
        print(f"\n⏱️ Test Duration: {duration:.2f} seconds")
        print(f"📊 Total Tests: {len(self.passed) + len(self.failed) + len(self.warnings)}")
        
        if self.passed:
            print(f"\n✅ PASSED TESTS ({len(self.passed)}):")
            for test in self.passed:
                print(f"  {test}")
        
        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.failed:
            print(f"\n❌ FAILED TESTS ({len(self.failed)}):")
            for failure in self.failed:
                print(f"  {failure}")
        
        success_rate = len(self.passed) / (len(self.passed) + len(self.failed)) * 100 if (self.passed or self.failed) else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        if len(self.failed) == 0:
            print("🏆 ALL TESTS PASSED - ENGINE IS WORKING!")
            return True
        else:
            print("🔧 SOME TESTS FAILED - NEEDS ATTENTION")
            return False

# Global test results
results = TestResults()

def test_1_system_prerequisites():
    """Test 1: Verify system prerequisites"""
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            results.fail_test("Python Version", f"Need Python 3.8+, got {sys.version}")
            return
        results.pass_test("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}")
        
        # Check Piper installation
        try:
            result = subprocess.run(["piper", "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                results.pass_test("Piper Installation", f"Found: {version}")
            else:
                results.warn_test("Piper Installation", "Not found in PATH, will attempt auto-install")
        except Exception:
            results.warn_test("Piper Installation", "Not found, will attempt auto-install")
        
        # Check FFmpeg (optional but recommended)
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                results.pass_test("FFmpeg Installation", "Available for format conversion")
            else:
                results.warn_test("FFmpeg Installation", "Not found - format conversion limited")
        except Exception:
            results.warn_test("FFmpeg Installation", "Not found - format conversion limited")
            
    except Exception as e:
        results.fail_test("System Prerequisites", str(e))

def test_2_directory_structure():
    """Test 2: Verify directory structure"""
    try:
        required_dirs = ["voices", "sample_audio", "generated_audio", "audio_cache"]
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists() and dir_path.is_dir():
                results.pass_test(f"Directory {dir_name}", "Exists")
            else:
                results.fail_test(f"Directory {dir_name}", "Missing or not a directory")
    except Exception as e:
        results.fail_test("Directory Structure", str(e))

def test_3_engine_initialization():
    """Test 3: Test TTS engine initialization"""
    try:
        # This will test the full initialization process
        if not tts_engine.initialized:
            results.fail_test("Engine Initialization", "Engine not initialized")
            return
        
        results.pass_test("Engine Initialization", "Engine initialized successfully")
        
        # Check available voices
        voice_count = len(tts_engine.available_voices)
        if voice_count >= 2:
            results.pass_test("Voice Loading", f"{voice_count} voices available")
        elif voice_count == 1:
            results.warn_test("Voice Loading", f"Only {voice_count} voice available")
        else:
            results.fail_test("Voice Loading", "No voices available")
        
        # Check specific voices
        for voice_id in PIPER_VOICES.keys():
            if voice_id in tts_engine.available_voices:
                results.pass_test(f"Voice {voice_id}", "Available and validated")
            else:
                results.fail_test(f"Voice {voice_id}", "Not available")
                
    except Exception as e:
        results.fail_test("Engine Initialization", str(e))

def test_4_voice_model_files():
    """Test 4: Verify voice model files"""
    try:
        for voice_id in PIPER_VOICES.keys():
            voice_dir = Path("voices") / voice_id
            model_file = voice_dir / f"{voice_id}.onnx"
            config_file = voice_dir / f"{voice_id}.onnx.json"
            
            # Check model file
            if model_file.exists():
                size = model_file.stat().st_size
                if size > 1_000_000:  # At least 1MB
                    results.pass_test(f"{voice_id} Model", f"Size: {size // 1_000_000}MB")
                else:
                    results.fail_test(f"{voice_id} Model", f"Too small: {size} bytes")
            else:
                results.fail_test(f"{voice_id} Model", "File missing")
            
            # Check config file
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        if 'audio' in config and 'sample_rate' in config['audio']:
                            results.pass_test(f"{voice_id} Config", f"Valid JSON, SR: {config['audio']['sample_rate']}")
                        else:
                            results.fail_test(f"{voice_id} Config", "Invalid structure")
                except json.JSONDecodeError:
                    results.fail_test(f"{voice_id} Config", "Invalid JSON")
            else:
                results.fail_test(f"{voice_id} Config", "File missing")
                
    except Exception as e:
        results.fail_test("Voice Model Files", str(e))

def test_5_api_endpoints():
    """Test 5: Test API endpoints"""
    try:
        with TestClient(app) as client:
            # Test health endpoint
            response = client.get("/health")
            if response.status_code == 200:
                data = response.json()
                results.pass_test("Health Endpoint", f"Status: {data.get('status', 'unknown')}")
            else:
                results.fail_test("Health Endpoint", f"HTTP {response.status_code}")
            
            # Test voices endpoint
            response = client.get("/voices")
            if response.status_code == 200:
                data = response.json()
                voice_count = len(data.get("voices", []))
                results.pass_test("Voices Endpoint", f"{voice_count} voices listed")
            else:
                results.fail_test("Voices Endpoint", f"HTTP {response.status_code}")
            
            # Test samples endpoint
            response = client.get("/samples")
            if response.status_code == 200:
                results.pass_test("Samples Endpoint", "Working")
            else:
                results.fail_test("Samples Endpoint", f"HTTP {response.status_code}")
                
    except Exception as e:
        results.fail_test("API Endpoints", str(e))

def test_6_synthesis_functionality():
    """Test 6: Test actual synthesis functionality"""
    try:
        with TestClient(app) as client:
            # Test data
            test_requests = [
                {
                    "text": "Hello, this is a test of the female voice.",
                    "voice_id": "en_US-lessac-medium",
                    "format": "wav"
                },
                {
                    "text": "Hello, this is a test of the male voice.",
                    "voice_id": "en_US-ryan-high", 
                    "format": "wav"
                }
            ]
            
            for i, test_req in enumerate(test_requests):
                if test_req["voice_id"] not in tts_engine.available_voices:
                    results.warn_test(f"Synthesis Test {i+1}", f"Voice {test_req['voice_id']} not available")
                    continue
                
                # Make synthesis request
                response = client.post(
                    "/synthesize",
                    json=test_req,
                    headers={"X-API-Key": "test-key"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        audio_file = data.get("audio_file")
                        if audio_file and Path(audio_file).exists():
                            file_size = Path(audio_file).stat().st_size
                            duration = data.get("duration", 0)
                            results.pass_test(
                                f"Synthesis {test_req['voice_id']}", 
                                f"Success: {file_size} bytes, {duration:.2f}s"
                            )
                        else:
                            results.fail_test(f"Synthesis {test_req['voice_id']}", "No output file")
                    else:
                        results.fail_test(f"Synthesis {test_req['voice_id']}", "Synthesis failed")
                else:
                    results.fail_test(f"Synthesis {test_req['voice_id']}", f"HTTP {response.status_code}")
                    
    except Exception as e:
        results.fail_test("Synthesis Functionality", str(e))

def test_7_audio_quality():
    """Test 7: Validate audio quality"""
    try:
        # Check demo samples if they exist
        sample_dir = Path("sample_audio")
        demo_files = list(sample_dir.glob("demo_*.wav"))
        
        if not demo_files:
            results.warn_test("Audio Quality", "No demo samples found")
            return
        
        for demo_file in demo_files:
            file_size = demo_file.stat().st_size
            
            # Basic size check
            if file_size < 1000:
                results.fail_test(f"Demo {demo_file.name}", f"Too small: {file_size} bytes")
                continue
            
            # Check WAV header
            try:
                with open(demo_file, 'rb') as f:
                    header = f.read(12)
                    if header.startswith(b'RIFF') and header[8:12] == b'WAVE':
                        results.pass_test(f"Demo {demo_file.name}", f"Valid WAV: {file_size} bytes")
                    else:
                        results.fail_test(f"Demo {demo_file.name}", "Invalid WAV header")
            except Exception as e:
                results.fail_test(f"Demo {demo_file.name}", f"Read error: {e}")
                
    except Exception as e:
        results.fail_test("Audio Quality", str(e))

def test_8_format_conversion():
    """Test 8: Test audio format conversion"""
    try:
        # Test if FFmpeg is available for format conversion
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
            ffmpeg_available = True
        except:
            ffmpeg_available = False
        
        if not ffmpeg_available:
            results.warn_test("Format Conversion", "FFmpeg not available - limited format support")
            return
        
        with TestClient(app) as client:
            # Test different formats
            formats_to_test = ["wav", "mp3"]
            
            for format_name in formats_to_test:
                response = client.post(
                    "/synthesize",
                    json={
                        "text": "Format conversion test.",
                        "voice_id": "en_US-lessac-medium",
                        "format": format_name
                    },
                    headers={"X-API-Key": "test-key"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        results.pass_test(f"Format {format_name.upper()}", "Conversion successful")
                    else:
                        results.fail_test(f"Format {format_name.upper()}", "Conversion failed")
                else:
                    results.fail_test(f"Format {format_name.upper()}", f"HTTP {response.status_code}")
                    
    except Exception as e:
        results.fail_test("Format Conversion", str(e))

def test_9_url_synthesis():
    """Test 9: Test URL-based synthesis for webhooks"""
    try:
        with TestClient(app) as client:
            response = client.post(
                "/synthesize-url",
                json={
                    "text": "This is a URL synthesis test.",
                    "voice_id": "en_US-lessac-medium",
                    "format": "wav"
                },
                headers={"X-API-Key": "test-key"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("url"):
                    # Test if the URL is accessible
                    audio_url = data["url"].replace("http://localhost:8000", "")
                    file_response = client.get(audio_url)
                    if file_response.status_code == 200:
                        results.pass_test("URL Synthesis", f"URL accessible: {data['url']}")
                    else:
                        results.fail_test("URL Synthesis", "Generated URL not accessible")
                else:
                    results.fail_test("URL Synthesis", "No URL returned")
            else:
                results.fail_test("URL Synthesis", f"HTTP {response.status_code}")
                
    except Exception as e:
        results.fail_test("URL Synthesis", str(e))

def test_10_error_handling():
    """Test 10: Test error handling"""
    try:
        with TestClient(app) as client:
            # Test invalid API key
            response = client.post(
                "/synthesize",
                json={"text": "Test", "voice_id": "en_US-lessac-medium", "format": "wav"},
                headers={"X-API-Key": "invalid-key"}
            )
            if response.status_code == 401:
                results.pass_test("Invalid API Key", "Properly rejected")
            else:
                results.fail_test("Invalid API Key", f"Unexpected status: {response.status_code}")
            
            # Test empty text
            response = client.post(
                "/synthesize",
                json={"text": "", "voice_id": "en_US-lessac-medium", "format": "wav"},
                headers={"X-API-Key": "test-key"}
            )
            if response.status_code == 400:
                results.pass_test("Empty Text", "Properly rejected")
            else:
                results.fail_test("Empty Text", f"Unexpected status: {response.status_code}")
            
            # Test invalid voice
            response = client.post(
                "/synthesize",
                json={"text": "Test", "voice_id": "invalid-voice", "format": "wav"},
                headers={"X-API-Key": "test-key"}
            )
            if response.status_code == 400:
                results.pass_test("Invalid Voice", "Properly rejected")
            else:
                results.fail_test("Invalid Voice", f"Unexpected status: {response.status_code}")
                
    except Exception as e:
        results.fail_test("Error Handling", str(e))

def test_11_performance():
    """Test 11: Basic performance test"""
    try:
        with TestClient(app) as client:
            start_time = time.time()
            
            response = client.post(
                "/synthesize",
                json={
                    "text": "This is a performance test of the text-to-speech system.",
                    "voice_id": "en_US-lessac-medium",
                    "format": "wav"
                },
                headers={"X-API-Key": "test-key"}
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    if duration < 30:  # Should complete within 30 seconds
                        results.pass_test("Performance", f"Synthesis completed in {duration:.2f}s")
                    else:
                        results.warn_test("Performance", f"Slow synthesis: {duration:.2f}s")
                else:
                    results.fail_test("Performance", "Synthesis failed")
            else:
                results.fail_test("Performance", f"HTTP {response.status_code}")
                
    except Exception as e:
        results.fail_test("Performance", str(e))

def test_12_cache_functionality():
    """Test 12: Test caching functionality"""
    try:
        with TestClient(app) as client:
            test_text = "Cache test message."
            
            # First request - should create cache
            start_time = time.time()
            response1 = client.post(
                "/synthesize",
                json={"text": test_text, "voice_id": "en_US-lessac-medium", "format": "wav"},
                headers={"X-API-Key": "test-key"}
            )
            first_duration = time.time() - start_time
            
            # Second request - should use cache
            start_time = time.time()
            response2 = client.post(
                "/synthesize",
                json={"text": test_text, "voice_id": "en_US-lessac-medium", "format": "wav"},
                headers={"X-API-Key": "test-key"}
            )
            second_duration = time.time() - start_time
            
            if response1.status_code == 200 and response2.status_code == 200:
                if second_duration < first_duration:
                    results.pass_test("Cache Functionality", f"Cache hit faster: {second_duration:.2f}s vs {first_duration:.2f}s")
                else:
                    results.warn_test("Cache Functionality", "No clear cache performance benefit")
            else:
                results.fail_test("Cache Functionality", "One or both requests failed")
                
    except Exception as e:
        results.fail_test("Cache Functionality", str(e))

def run_all_tests():
    """Run all tests in sequence"""
    print("🧪 Starting Fixed TTS Engine Test Suite...")
    print("="*70)
    
    test_functions = [
        test_1_system_prerequisites,
        test_2_directory_structure,
        test_3_engine_initialization,
        test_4_voice_model_files,
        test_5_api_endpoints,
        test_6_synthesis_functionality,
        test_7_audio_quality,
        test_8_format_conversion,
        test_9_url_synthesis,
        test_10_error_handling,
        test_11_performance,
        test_12_cache_functionality,
    ]
    
    for i, test_func in enumerate(test_functions, 1):
        print(f"\n[{i}/{len(test_functions)}] Running {test_func.__name__}...")
        try:
            test_func()
        except Exception as e:
            results.fail_test(test_func.__name__, f"Test exception: {e}")
        time.sleep(0.5)  # Brief pause between tests
    
    # Print final report
    success = results.print_final_report()
    return success

if __name__ == "__main__":
    print("🎯 CallWaiting.ai TTS Engine - Fixed Implementation Test Suite")
    print("Testing realistic voice generation and all functionality...")
    
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        sys.exit(1)