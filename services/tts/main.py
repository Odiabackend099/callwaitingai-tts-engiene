#!/usr/bin/env python3
"""
CallWaiting.ai TTS Engine - FIXED IMPLEMENTATION
Addresses critical issues in original code for realistic voice generation
"""

import os
import sys
import uuid
import json
import time
import hashlib
import subprocess
import logging
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
import signal

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import httpx
from contextlib import asynccontextmanager

# Configure logging with proper formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('tts_engine.log', mode='w')  # Fresh log each start
    ]
)
logger = logging.getLogger(__name__)

# Suppress noisy loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# Configuration
BASE_DIR = Path(__file__).parent
VOICES_DIR = BASE_DIR / "voices"
SAMPLES_DIR = BASE_DIR / "sample_audio"
GENERATED_DIR = BASE_DIR / "generated_audio"
CACHE_DIR = BASE_DIR / "audio_cache"

# Ensure directories exist
for dir_path in [VOICES_DIR, SAMPLES_DIR, GENERATED_DIR, CACHE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Voice configuration - HIGH QUALITY PIPER MODELS ONLY
PIPER_VOICES = {
    "en_US-lessac-medium": {
        "name": "Female Voice (Natural)",
        "gender": "female",
        "quality": "medium",
        "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
        "sample_rate": 22050
    },
    "en_US-ryan-high": {
        "name": "Male Voice (High Quality)",
        "gender": "male", 
        "quality": "high",
        "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/high/en_US-ryan-high.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/high/en_US-ryan-high.onnx.json",
        "sample_rate": 22050
    }
}

# API Models
class SynthesisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")
    voice_id: str = Field(..., description="Voice ID (en_US-lessac-medium or en_US-ryan-high)")
    format: str = Field(default="wav", pattern="^(wav|mp3|ulaw)$", description="Output format")

class SynthesisResponse(BaseModel):
    success: bool
    audio_file: Optional[str] = None
    url: Optional[str] = None
    duration: Optional[float] = None
    request_id: str
    message: Optional[str] = None

# Enhanced download with resume capability
async def download_with_resume(url: str, filepath: Path, timeout: int = 60) -> bool:
    """Download file with resume capability for unreliable networks"""
    logger.info(f"Downloading: {url}")
    
    headers = {}
    mode = 'wb'
    
    # Check for existing partial download
    if filepath.exists():
        existing_size = filepath.stat().st_size
        headers['Range'] = f'bytes={existing_size}-'
        mode = 'ab'
        logger.info(f"Resuming download from byte {existing_size}")
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream('GET', url, headers=headers) as response:
                response.raise_for_status()
                
                # Handle partial content response
                if response.status_code == 206:
                    logger.info("Resuming previous download")
                elif response.status_code == 200 and mode == 'ab':
                    # Server doesn't support resume, restart download
                    filepath.unlink()
                    mode = 'wb'
                    logger.info("Server doesn't support resume, restarting download")
                
                with open(filepath, mode) as f:
                    total_size = 0
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            total_size += len(chunk)
                
                logger.info(f"Download completed: {filepath} ({total_size} bytes)")
                return True
                
    except Exception as e:
        logger.error(f"Download failed: {e}")
        if filepath.exists():
            filepath.unlink()  # Clean up partial file
        raise

class TTSEngine:
    def __init__(self):
        self.initialized = False
        self.piper_path = None
        self.available_voices = {}
        self.startup_errors = []
    
    async def initialize(self):
        """Initialize TTS engine with comprehensive validation"""
        init_id = str(uuid.uuid4())[:8]
        logger.info(f"[{init_id}] Initializing TTS Engine...")
        
        try:
            # Step 1: Find and validate Piper installation
            self.piper_path = await self._find_piper_binary(init_id)
            
            # Step 2: Download voice models
            await self._download_voice_models(init_id)
            
            # Step 3: Validate each voice model
            for voice_id in PIPER_VOICES.keys():
                try:
                    if await self._validate_voice_model(voice_id, init_id):
                        self.available_voices[voice_id] = PIPER_VOICES[voice_id]
                        logger.info(f"[{init_id}] Voice validated: {voice_id}")
                    else:
                        self.startup_errors.append(f"Voice validation failed: {voice_id}")
                except Exception as e:
                    error_msg = f"Voice validation error: {voice_id} - {e}"
                    logger.error(f"[{init_id}] {error_msg}")
                    self.startup_errors.append(error_msg)
            
            if not self.available_voices:
                raise Exception("No valid voice models available after initialization")
            
            # Step 4: Generate demo samples
            await self._generate_demo_samples(init_id)
            
            self.initialized = True
            logger.info(f"[{init_id}] TTS Engine ready: {len(self.available_voices)} voices available")
            
            if self.startup_errors:
                logger.warning(f"[{init_id}] Startup completed with {len(self.startup_errors)} warnings")
            
        except Exception as e:
            logger.error(f"[{init_id}] TTS Engine initialization failed: {e}")
            raise RuntimeError(f"TTS Engine initialization failed: {e}")
    
    async def _find_piper_binary(self, init_id: str) -> str:
        """Find or install Piper binary"""
        # Try to find existing Piper installation
        test_paths = ["piper", "/usr/local/bin/piper", "/usr/bin/piper", 
                     str(BASE_DIR / "piper"), "python -m piper"]
        
        for path in test_paths:
            try:
                cmd = path.split() if ' ' in path else [path]
                result = subprocess.run(cmd + ["--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    logger.info(f"[{init_id}] Found Piper: {path} (version: {version})")
                    return path
            except Exception:
                continue
        
        # Try to install Piper if not found
        logger.info(f"[{init_id}] Piper not found, attempting installation...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "piper-tts"], 
                          check=True, capture_output=True)
            # Test the installation
            result = subprocess.run(["piper", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"[{init_id}] Piper installed successfully")
                return "piper"
        except Exception as e:
            logger.error(f"[{init_id}] Piper installation failed: {e}")
        
        raise Exception("Piper TTS not found and installation failed. Please install manually: pip install piper-tts")
    
    async def _download_voice_models(self, init_id: str):
        """Download voice models with retry logic"""
        for voice_id, config in PIPER_VOICES.items():
            voice_dir = VOICES_DIR / voice_id
            voice_dir.mkdir(parents=True, exist_ok=True)
            
            model_file = voice_dir / f"{voice_id}.onnx"
            config_file = voice_dir / f"{voice_id}.onnx.json"
            
            # Download model file
            if not model_file.exists() or model_file.stat().st_size < 1000:
                logger.info(f"[{init_id}] Downloading model: {voice_id}")
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        await download_with_resume(config["model_url"], model_file)
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise Exception(f"Failed to download {voice_id} model after {max_retries} attempts: {e}")
                        wait_time = (attempt + 1) * 2
                        logger.warning(f"[{init_id}] Download attempt {attempt + 1} failed, retrying in {wait_time}s")
                        await asyncio.sleep(wait_time)
            
            # Download config file
            if not config_file.exists():
                logger.info(f"[{init_id}] Downloading config: {voice_id}")
                await download_with_resume(config["config_url"], config_file)
    
    async def _validate_voice_model(self, voice_id: str, init_id: str) -> bool:
        """Validate voice model with actual synthesis test"""
        try:
            voice_dir = VOICES_DIR / voice_id
            model_file = voice_dir / f"{voice_id}.onnx"
            config_file = voice_dir / f"{voice_id}.onnx.json"
            
            # Check files exist and have reasonable size
            if not model_file.exists() or model_file.stat().st_size < 1000000:  # At least 1MB
                logger.error(f"[{init_id}] Model file missing or too small: {voice_id}")
                return False
                
            if not config_file.exists() or config_file.stat().st_size < 100:  # At least 100 bytes
                logger.error(f"[{init_id}] Config file missing or too small: {voice_id}")
                return False
            
            # Validate JSON config
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                    if 'audio' not in config_data or 'sample_rate' not in config_data['audio']:
                        logger.error(f"[{init_id}] Invalid config structure: {voice_id}")
                        return False
            except json.JSONDecodeError as e:
                logger.error(f"[{init_id}] Config JSON parsing failed: {voice_id} - {e}")
                return False
            
            # Test actual synthesis
            test_text = "Hello, this is a voice test."
            test_file = CACHE_DIR / f"validation_{voice_id}_{init_id}.wav"
            
            # Prepare Piper command
            cmd = [self.piper_path] if isinstance(self.piper_path, str) else self.piper_path.split()
            cmd.extend([
                "--model", str(model_file),
                "--config", str(config_file),
                "--output_file", str(test_file)
            ])
            
            logger.info(f"[{init_id}] Testing synthesis for {voice_id}")
            
            # Run synthesis with timeout
            process = subprocess.run(
                cmd,
                input=test_text,
                text=True,
                capture_output=True,
                timeout=30
            )
            
            if process.returncode != 0:
                logger.error(f"[{init_id}] Synthesis failed for {voice_id}: {process.stderr}")
                return False
            
            # Validate output file
            if not test_file.exists():
                logger.error(f"[{init_id}] No output file generated for {voice_id}")
                return False
            
            file_size = test_file.stat().st_size
            if file_size < 1000:  # At least 1KB
                logger.error(f"[{init_id}] Output file too small for {voice_id}: {file_size} bytes")
                return False
            
            # Validate it's actually a valid WAV file
            try:
                # Check WAV header
                with open(test_file, 'rb') as f:
                    header = f.read(12)
                    if not (header.startswith(b'RIFF') and header[8:12] == b'WAVE'):
                        logger.error(f"[{init_id}] Invalid WAV file for {voice_id}")
                        return False
            except Exception as e:
                logger.error(f"[{init_id}] WAV validation failed for {voice_id}: {e}")
                return False
            
            # Clean up test file
            test_file.unlink()
            
            logger.info(f"[{init_id}] Voice validation passed: {voice_id} ({file_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"[{init_id}] Voice validation exception for {voice_id}: {e}")
            return False
    
    async def _generate_demo_samples(self, init_id: str):
        """Generate demo samples for validated voices"""
        demo_texts = {
            "en_US-lessac-medium": "Hello, I'm the female voice from CallWaiting AI. This is a demonstration of realistic neural text-to-speech.",
            "en_US-ryan-high": "Hello, I'm the male voice from CallWaiting AI. This is a demonstration of realistic neural text-to-speech."
        }
        
        for voice_id, demo_text in demo_texts.items():
            if voice_id in self.available_voices:
                try:
                    sample_file = SAMPLES_DIR / f"demo_{voice_id}.wav"
                    await self._synthesize_internal(demo_text, voice_id, "wav", str(sample_file), init_id)
                    
                    # Verify the demo file
                    if sample_file.exists() and sample_file.stat().st_size > 1000:
                        logger.info(f"[{init_id}] Demo sample created: {voice_id}")
                    else:
                        logger.warning(f"[{init_id}] Demo sample creation failed: {voice_id}")
                        
                except Exception as e:
                    logger.error(f"[{init_id}] Demo generation failed for {voice_id}: {e}")
    
    async def _synthesize_internal(self, text: str, voice_id: str, format: str, output_path: str, request_id: str):
        """Internal synthesis method with enhanced error handling"""
        if not self.initialized:
            raise RuntimeError("TTS Engine not initialized")
        
        if voice_id not in self.available_voices:
            available = ", ".join(self.available_voices.keys())
            raise ValueError(f"Invalid voice_id '{voice_id}'. Available voices: {available}")
        
        voice_dir = VOICES_DIR / voice_id
        model_file = voice_dir / f"{voice_id}.onnx"
        config_file = voice_dir / f"{voice_id}.onnx.json"
        
        logger.info(f"[{request_id}] Starting synthesis: voice={voice_id}, text_len={len(text)}, format={format}")
        
        # Create temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            temp_wav_path = temp_wav.name
        
        try:
            # Prepare Piper command
            cmd = [self.piper_path] if isinstance(self.piper_path, str) else self.piper_path.split()
            cmd.extend([
                "--model", str(model_file),
                "--config", str(config_file),
                "--output_file", temp_wav_path
            ])
            
            # Run synthesis
            start_time = time.time()
            process = subprocess.run(
                cmd,
                input=text,
                text=True,
                capture_output=True,
                timeout=120  # Longer timeout for longer texts
            )
            synthesis_time = time.time() - start_time
            
            if process.returncode != 0:
                error_msg = process.stderr.strip() if process.stderr else "Unknown Piper error"
                raise RuntimeError(f"Piper synthesis failed: {error_msg}")
            
            # Validate temporary output
            temp_path = Path(temp_wav_path)
            if not temp_path.exists():
                raise RuntimeError("Piper produced no output file")
            
            temp_size = temp_path.stat().st_size
            if temp_size < 1000:
                raise RuntimeError(f"Piper output too small: {temp_size} bytes")
            
            logger.info(f"[{request_id}] Piper synthesis completed: {synthesis_time:.2f}s, {temp_size} bytes")
            
            # Format conversion
            output_path_obj = Path(output_path)
            
            if format.lower() == "wav":
                # Direct copy for WAV
                shutil.move(temp_wav_path, output_path)
            elif format.lower() == "ulaw":
                # Convert to μ-law for telephony
                subprocess.run([
                    "ffmpeg", "-y", "-i", temp_wav_path,
                    "-ar", "8000", "-ac", "1", "-acodec", "pcm_mulaw",
                    str(output_path)
                ], check=True, capture_output=True, timeout=60)
                os.unlink(temp_wav_path)
            elif format.lower() == "mp3":
                # Convert to MP3
                subprocess.run([
                    "ffmpeg", "-y", "-i", temp_wav_path,
                    "-codec:a", "libmp3lame", "-b:a", "128k",
                    str(output_path)
                ], check=True, capture_output=True, timeout=60)
                os.unlink(temp_wav_path)
            else:
                # Use ffmpeg for other formats
                subprocess.run([
                    "ffmpeg", "-y", "-i", temp_wav_path, str(output_path)
                ], check=True, capture_output=True, timeout=60)
                os.unlink(temp_wav_path)
            
            # Final validation
            if not output_path_obj.exists():
                raise RuntimeError("Format conversion failed - no output file")
            
            final_size = output_path_obj.stat().st_size
            if final_size < 100:
                raise RuntimeError(f"Final output too small: {final_size} bytes")
            
            logger.info(f"[{request_id}] Synthesis completed successfully: {final_size} bytes")
            
        except Exception as e:
            # Clean up temporary files
            for temp_file in [temp_wav_path]:
                if os.path.exists(temp_file):
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
            raise RuntimeError(f"Audio synthesis failed: {e}")
    
    async def synthesize(self, text: str, voice_id: str, format: str = "wav") -> Dict[str, Any]:
        """Public synthesis method with caching and validation"""
        request_id = str(uuid.uuid4())[:8]
        
        # Input validation
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if len(text) > 5000:
            raise HTTPException(status_code=400, detail="Text too long (maximum 5000 characters)")
        
        if voice_id not in self.available_voices:
            available = ", ".join(self.available_voices.keys())
            raise HTTPException(status_code=400, 
                              detail=f"Invalid voice_id '{voice_id}'. Available: {available}")
        
        # Cache key generation
        cache_key = hashlib.md5(f"{text}-{voice_id}-{format}".encode()).hexdigest()
        cache_file = CACHE_DIR / f"{cache_key}.{format.lower()}"
        
        # Check cache
        if cache_file.exists() and cache_file.stat().st_size > 100:
            logger.info(f"[{request_id}] Cache hit: {cache_key}")
            return {
                "success": True,
                "audio_file": str(cache_file),
                "duration": self._get_audio_duration(cache_file),
                "request_id": request_id
            }
        
        # Generate new audio
        output_file = GENERATED_DIR / f"{request_id}_{voice_id}.{format.lower()}"
        
        try:
            start_time = time.time()
            await self._synthesize_internal(text, voice_id, format, str(output_file), request_id)
            
            # Copy to cache
            shutil.copy2(output_file, cache_file)
            
            synthesis_duration = time.time() - start_time
            audio_duration = self._get_audio_duration(output_file)
            
            logger.info(f"[{request_id}] New synthesis completed: {synthesis_duration:.2f}s processing, {audio_duration:.2f}s audio")
            
            return {
                "success": True,
                "audio_file": str(output_file),
                "duration": audio_duration,
                "request_id": request_id
            }
            
        except Exception as e:
            logger.error(f"[{request_id}] Synthesis failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def _get_audio_duration(self, file_path: Path) -> float:
        """Get audio duration using ffprobe"""
        try:
            result = subprocess.run([
                "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                "-of", "csv=p=0", str(file_path)
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except Exception:
            pass
        
        # Fallback: estimate from file size (very rough)
        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            # Rough estimate: 1MB ≈ 60 seconds for 16kHz WAV
            return size_mb * 60
        except:
            return 0.0

# Global TTS engine instance
tts_engine = TTSEngine()

# Application lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    logger.info("Starting CallWaiting.ai TTS Engine...")
    
    # Startup
    try:
        await tts_engine.initialize()
        logger.info("TTS Engine initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize TTS Engine: {e}")
        sys.exit(1)
    
    # Shutdown
    logger.info("Shutting down TTS Engine...")

# FastAPI application
app = FastAPI(
    title="CallWaiting.ai TTS Engine",
    description="Realistic Neural Voice Synthesis with Piper",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple API key validation
VALID_API_KEYS = {"demo-key", "test-key", "dev-key"}

def validate_api_key(request: Request):
    """Validate API key from header"""
    api_key = request.headers.get("X-API-Key")
    if api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key

# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    if not tts_engine.initialized:
        raise HTTPException(status_code=503, detail="TTS Engine not initialized")
    
    health_info = {
        "status": "healthy",
        "engine": "piper",
        "voices_available": len(tts_engine.available_voices),
        "voices": list(tts_engine.available_voices.keys()),
        "piper_path": tts_engine.piper_path
    }
    
    if tts_engine.startup_errors:
        health_info["warnings"] = tts_engine.startup_errors
    
    return health_info

# Voice listing endpoint
@app.get("/voices")
async def list_voices():
    """List available voices with details"""
    return {
        "voices": [
            {
                "voice_id": voice_id,
                "name": config["name"],
                "gender": config["gender"],
                "quality": config["quality"],
                "sample_rate": config["sample_rate"]
            }
            for voice_id, config in tts_engine.available_voices.items()
        ]
    }

# Demo samples endpoint
@app.get("/samples")
async def list_samples():
    """List available demo samples"""
    samples = []
    for file in SAMPLES_DIR.glob("*.wav"):
        samples.append({
            "filename": file.name,
            "url": f"/sample_audio/{file.name}",
            "size": file.stat().st_size,
            "voice_id": file.stem.replace("demo_", "") if file.stem.startswith("demo_") else "unknown"
        })
    return {"samples": samples}

# Serve demo samples
@app.get("/sample_audio/{filename}")
async def serve_sample_audio(filename: str):
    """Serve demo audio files"""
    file_path = SAMPLES_DIR / filename
    if not file_path.exists() or not filename.endswith(('.wav', '.mp3')):
        raise HTTPException(status_code=404, detail="Sample not found")
    return FileResponse(file_path, media_type="audio/wav")

# Main synthesis endpoint
@app.post("/synthesize", response_model=SynthesisResponse)
async def synthesize_speech(request: SynthesisRequest, api_key: str = Depends(validate_api_key)):
    """Synthesize speech and return file path"""
    try:
        result = await tts_engine.synthesize(request.text, request.voice_id, request.format)
        return SynthesisResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Synthesis endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal synthesis error")

# URL-based synthesis for webhooks
@app.post("/synthesize-url", response_model=SynthesisResponse)
async def synthesize_speech_url(request: SynthesisRequest, api_key: str = Depends(validate_api_key)):
    """Synthesize speech and return public URL"""
    try:
        result = await tts_engine.synthesize(request.text, request.voice_id, request.format)
        
        file_path = Path(result["audio_file"])
        base_url = "http://localhost:8000"  # Configure this for your deployment
        url = f"{base_url}/generated_audio/{file_path.name}"
        
        return SynthesisResponse(
            success=True,
            url=url,
            duration=result["duration"],
            request_id=result["request_id"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL synthesis endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal synthesis error")

# Serve generated audio files
@app.get("/generated_audio/{filename}")
async def serve_generated_audio(filename: str):
    """Serve generated audio files"""
    file_path = GENERATED_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Determine media type
    media_type = "audio/wav"
    if filename.endswith('.mp3'):
        media_type = "audio/mpeg"
    elif filename.endswith('.ulaw'):
        media_type = "audio/basic"
    
    return FileResponse(file_path, media_type=media_type)

# Development endpoints
@app.post("/admin/generate-api-key")
async def generate_api_key():
    """Generate new API key"""
    new_key = str(uuid.uuid4())
    VALID_API_KEYS.add(new_key)
    return {"api_key": new_key}

@app.get("/admin/cache-stats")
async def cache_stats():
    """Get cache statistics"""
    cache_files = list(CACHE_DIR.glob("*"))
    generated_files = list(GENERATED_DIR.glob("*"))
    
    cache_size = sum(f.stat().st_size for f in cache_files if f.is_file())
    generated_size = sum(f.stat().st_size for f in generated_files if f.is_file())
    
    return {
        "cache_files": len(cache_files),
        "cache_size_