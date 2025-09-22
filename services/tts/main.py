from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import asyncio
import aiofiles
import httpx
import tempfile
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CallWaiting TTS Engine", version="1.0.0")

# Configuration - SUPREME COMMAND COMPLIANCE
VOICES_DIR = "voices"
API_KEYS_FILE = "api_keys.json"
ALLOWED_VOICES = ["en_US-lessac-medium", "en_US-ryan-high"]  # FIXED: Match actual model filenames
RATE_LIMIT_PER_MINUTE = 60
ENGINE_NAME = "piper"  # SUPREME COMMAND: Always log engine name

# Voice model URLs - SUPREME COMMAND: Only Piper neural models
VOICE_MODELS = {
    "en_US-lessac-medium": {
        "model_url": "https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
        "description": "Female voice - Lessac medium quality",
        "gender": "female"
    },
    "en_US-ryan-high": {
        "model_url": "https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_US/ryan/high/en_US-ryan-high.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_US/ryan/high/en_US-ryan-high.onnx.json",
        "description": "Male voice - Ryan high quality",
        "gender": "male"
    }
}

# SUPREME COMMAND: Demo texts for startup
DEMO_TEXTS = {
    "en_US-lessac-medium": "Welcome to CallWaiting.ai voice service – this is the realistic female voice",
    "en_US-ryan-high": "Welcome to CallWaiting.ai voice service – this is the realistic male voice"
}

# Pydantic models
class SynthesizeRequest(BaseModel):
    text: str
    voice_id: str
    format: str = "wav"  # wav or mulaw

class SynthesizeURLRequest(BaseModel):
    text: str
    voice_id: str
    format: str = "wav"

class APIKeyResponse(BaseModel):
    api_key: str
    created_at: str
    expires_at: str

# API Key management
class APIKeyManager:
    def __init__(self, keys_file: str):
        self.keys_file = keys_file
        self.keys = self.load_keys()
    
    def load_keys(self) -> Dict:
        if os.path.exists(self.keys_file):
            with open(self.keys_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_keys(self):
        with open(self.keys_file, 'w') as f:
            json.dump(self.keys, f, indent=2)
    
    def generate_key(self) -> str:
        """Generate a new API key"""
        key = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(days=365)).isoformat()
        
        self.keys[key] = {
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at,
            "rate_limit": {"requests": 0, "window_start": datetime.now().isoformat()}
        }
        self.save_keys()
        return key
    
    def validate_key(self, key: str) -> bool:
        """Validate API key"""
        if key not in self.keys:
            return False
        
        key_data = self.keys[key]
        expires_at = datetime.fromisoformat(key_data["expires_at"])
        
        if datetime.now() > expires_at:
            del self.keys[key]
            self.save_keys()
            return False
        
        return True
    
    def check_rate_limit(self, key: str) -> bool:
        """Check if key is within rate limits"""
        if key not in self.keys:
            return False
        
        key_data = self.keys[key]
        now = datetime.now()
        window_start = datetime.fromisoformat(key_data["rate_limit"]["window_start"])
        
        # Reset window if more than a minute has passed
        if (now - window_start).total_seconds() > 60:
            key_data["rate_limit"]["requests"] = 0
            key_data["rate_limit"]["window_start"] = now.isoformat()
            self.save_keys()
        
        # Check if under rate limit
        if key_data["rate_limit"]["requests"] >= RATE_LIMIT_PER_MINUTE:
            return False
        
        # Increment request count
        key_data["rate_limit"]["requests"] += 1
        self.save_keys()
        return True

# Initialize API key manager
api_key_manager = APIKeyManager(API_KEYS_FILE)

# Voice manager
class VoiceManager:
    def __init__(self):
        self.voices_dir = VOICES_DIR
        self.ensure_voices_directory()
    
    def ensure_voices_directory(self):
        """Ensure voices directory exists"""
        os.makedirs(self.voices_dir, exist_ok=True)
        for voice in ALLOWED_VOICES:
            voice_dir = os.path.join(self.voices_dir, voice)
            os.makedirs(voice_dir, exist_ok=True)
    
    async def download_voice_model(self, voice_id: str) -> bool:
        """Download voice model if not exists"""
        if voice_id not in VOICE_MODELS:
            return False
        
        voice_dir = os.path.join(self.voices_dir, voice_id)
        model_path = os.path.join(voice_dir, f"{voice_id}.onnx")
        config_path = os.path.join(voice_dir, f"{voice_id}.json")
        
        # Check if already downloaded
        if os.path.exists(model_path) and os.path.exists(config_path):
            return True
        
        model_info = VOICE_MODELS[voice_id]
        
        async with httpx.AsyncClient() as client:
            try:
                # Download model
                logger.info(f"Downloading model for {voice_id}...")
                response = await client.get(model_info["model_url"])
                response.raise_for_status()
                
                async with aiofiles.open(model_path, 'wb') as f:
                    await f.write(response.content)
                
                # Download config
                logger.info(f"Downloading config for {voice_id}...")
                response = await client.get(model_info["config_url"])
                response.raise_for_status()
                
                async with aiofiles.open(config_path, 'w') as f:
                    await f.write(response.text)
                
                logger.info(f"Successfully downloaded {voice_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to download {voice_id}: {e}")
                return False
    
    def get_voice_path(self, voice_id: str) -> Optional[str]:
        """Get path to voice model - SUPREME COMMAND: Only Piper models"""
        if voice_id not in ALLOWED_VOICES:
            logger.error(f"SUPREME COMMAND VIOLATION: Invalid voice_id '{voice_id}' - not in allowed voices: {ALLOWED_VOICES}")
            return None
        
        voice_dir = os.path.join(self.voices_dir, voice_id)
        model_path = os.path.join(voice_dir, f"{voice_id}.onnx")
        
        if os.path.exists(model_path):
            logger.info(f"SUPREME COMMAND COMPLIANCE: Using Piper model '{voice_id}' at {model_path}")
            return model_path
        else:
            logger.error(f"SUPREME COMMAND VIOLATION: Piper model file missing for '{voice_id}' at {model_path}")
        return None
    
    def get_config_path(self, voice_id: str) -> Optional[str]:
        """Get path to voice config - SUPREME COMMAND: Only Piper models"""
        if voice_id not in ALLOWED_VOICES:
            logger.error(f"SUPREME COMMAND VIOLATION: Invalid voice_id '{voice_id}' - not in allowed voices: {ALLOWED_VOICES}")
            return None
        
        voice_dir = os.path.join(self.voices_dir, voice_id)
        config_path = os.path.join(voice_dir, f"{voice_id}.json")
        
        if os.path.exists(config_path):
            logger.info(f"SUPREME COMMAND COMPLIANCE: Using Piper config '{voice_id}' at {config_path}")
            return config_path
        else:
            logger.error(f"SUPREME COMMAND VIOLATION: Piper config file missing for '{voice_id}' at {config_path}")
        return None
    
    async def generate_demo_samples(self) -> Dict[str, str]:
        """SUPREME COMMAND: Generate demo samples on startup"""
        logger.info("SUPREME COMMAND: Generating demo samples for both voices...")
        demo_samples = {}
        
        # Ensure samples directory exists
        samples_dir = "sample_audio"
        os.makedirs(samples_dir, exist_ok=True)
        
        for voice_id in ALLOWED_VOICES:
            model_path = self.get_voice_path(voice_id)
            config_path = self.get_config_path(voice_id)
            
            if not model_path or not config_path:
                logger.error(f"SUPREME COMMAND VIOLATION: Cannot generate demo for {voice_id} - model/config missing")
                continue
            
            demo_text = DEMO_TEXTS[voice_id]
            demo_filename = f"demo_{voice_id}.wav"
            demo_path = os.path.join(samples_dir, demo_filename)
            
            try:
                # Generate demo using Piper
                cmd = [
                    "piper",
                    "--model", model_path,
                    "--config", config_path,
                    "--output_file", demo_path
                ]
                
                process = subprocess.run(
                    cmd,
                    input=demo_text,
                    text=True,
                    capture_output=True,
                    timeout=30
                )
                
                if process.returncode == 0:
                    demo_samples[voice_id] = demo_filename
                    logger.info(f"SUPREME COMMAND COMPLIANCE: Generated demo sample for {voice_id} -> {demo_filename}")
                else:
                    logger.error(f"SUPREME COMMAND VIOLATION: Failed to generate demo for {voice_id}: {process.stderr}")
                    
            except Exception as e:
                logger.error(f"SUPREME COMMAND VIOLATION: Exception generating demo for {voice_id}: {e}")
        
        return demo_samples

# Initialize voice manager
voice_manager = VoiceManager()

# Dependency for API key validation
async def validate_api_key(x_api_key: str = Header(...)) -> str:
    """Validate API key from header"""
    if not api_key_manager.validate_key(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key"
        )
    
    if not api_key_manager.check_rate_limit(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    return x_api_key

@app.on_event("startup")
async def startup_event():
    """SUPREME COMMAND: Download voice models and generate demo samples on startup"""
    logger.info("SUPREME COMMAND: Starting TTS Engine with Piper neural models only...")
    
    # Download voice models
    for voice_id in ALLOWED_VOICES:
        await voice_manager.download_voice_model(voice_id)
    
    # SUPREME COMMAND: Generate demo samples automatically
    demo_samples = await voice_manager.generate_demo_samples()
    
    logger.info(f"SUPREME COMMAND COMPLIANCE: TTS Engine ready with {len(demo_samples)} demo samples generated!")
    logger.info(f"SUPREME COMMAND: Engine='{ENGINE_NAME}', Models={ALLOWED_VOICES}, No OS fallback enabled")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/voices")
async def list_voices():
    """List available voices - SUPREME COMMAND: Only Piper neural models"""
    voices = []
    for voice_id in ALLOWED_VOICES:
        model_path = voice_manager.get_voice_path(voice_id)
        config_path = voice_manager.get_config_path(voice_id)
        
        voices.append({
            "id": voice_id,
            "name": voice_id,
            "description": VOICE_MODELS[voice_id]["description"],
            "gender": VOICE_MODELS[voice_id]["gender"],
            "engine": ENGINE_NAME,  # SUPREME COMMAND: Log engine name
            "available": model_path is not None and config_path is not None
        })
    
    logger.info(f"SUPREME COMMAND COMPLIANCE: Listed {len(voices)} Piper voices, engine='{ENGINE_NAME}'")
    return {"voices": voices}

@app.get("/samples")
async def list_demo_samples():
    """SUPREME COMMAND: List demo samples generated on startup"""
    samples_dir = "sample_audio"
    samples = []
    
    if os.path.exists(samples_dir):
        for filename in os.listdir(samples_dir):
            if filename.startswith("demo_") and filename.endswith(".wav"):
                voice_id = filename.replace("demo_", "").replace(".wav", "")
                if voice_id in ALLOWED_VOICES:
                    samples.append({
                        "voice_id": voice_id,
                        "filename": filename,
                        "url": f"/sample_audio/{filename}",
                        "description": f"Demo sample for {VOICE_MODELS[voice_id]['description']}"
                    })
    
    logger.info(f"SUPREME COMMAND COMPLIANCE: Listed {len(samples)} demo samples")
    return {"samples": samples}

@app.get("/sample_audio/{filename}")
async def serve_demo_sample(filename: str):
    """SUPREME COMMAND: Serve demo sample files"""
    if not filename.startswith("demo_") or not filename.endswith(".wav"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid demo sample filename"
        )
    
    sample_path = os.path.join("sample_audio", filename)
    
    if not os.path.exists(sample_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo sample not found"
        )
    
    logger.info(f"SUPREME COMMAND COMPLIANCE: Serving demo sample {filename}")
    return FileResponse(
        sample_path,
        media_type="audio/wav",
        filename=filename
    )

@app.post("/synthesize")
async def synthesize_audio(
    request: SynthesizeRequest,
    api_key: str = Depends(validate_api_key)
):
    """Synthesize audio and return as file response - SUPREME COMMAND: Only Piper, no OS fallback"""
    
    # SUPREME COMMAND: Log compliance
    logger.info(f"SUPREME COMMAND COMPLIANCE: Synthesis request - engine='{ENGINE_NAME}', voiceId='{request.voice_id}', format='{request.format}'")
    
    # SUPREME COMMAND: Validate voice - return 400 error, NO OS fallback
    if request.voice_id not in ALLOWED_VOICES:
        logger.error(f"SUPREME COMMAND VIOLATION: Invalid voice_id '{request.voice_id}' - returning 400 error, NO OS fallback")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid voice_id. Allowed voices: {ALLOWED_VOICES}. NO OS fallback available."
        )
    
    # Validate format
    if request.format not in ["wav", "mulaw"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Allowed formats: wav, mulaw"
        )
    
    model_path = voice_manager.get_voice_path(request.voice_id)
    config_path = voice_manager.get_config_path(request.voice_id)
    
    # SUPREME COMMAND: If Piper model missing, return 400 error - NO OS fallback
    if not model_path or not config_path:
        logger.error(f"SUPREME COMMAND VIOLATION: Piper model missing for '{request.voice_id}' - returning 400 error, NO OS fallback")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Piper voice model {request.voice_id} not available. NO OS fallback available."
        )
    
    try:
        # Generate temporary output file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            output_path = tmp_file.name
        
        # SUPREME COMMAND: Use ONLY Piper for synthesis
        cmd = [
            "piper",
            "--model", model_path,
            "--config", config_path,
            "--output_file", output_path
        ]
        
        logger.info(f"SUPREME COMMAND COMPLIANCE: Running Piper synthesis - model='{request.voice_id}', engine='{ENGINE_NAME}'")
        
        # Run synthesis
        process = subprocess.run(
            cmd,
            input=request.text,
            text=True,
            capture_output=True,
            timeout=30
        )
        
        if process.returncode != 0:
            logger.error(f"SUPREME COMMAND VIOLATION: Piper synthesis failed for '{request.voice_id}': {process.stderr}")
            raise Exception(f"Piper synthesis failed: {process.stderr}")
        
        logger.info(f"SUPREME COMMAND COMPLIANCE: Piper synthesis successful for '{request.voice_id}'")
        
        # Convert to requested format if needed
        if request.format == "mulaw":
            # Convert to μ-law 8kHz
            mulaw_path = output_path.replace(".wav", ".mulaw")
            convert_cmd = [
                "ffmpeg", "-y",
                "-i", output_path,
                "-ar", "8000",
                "-ac", "1",
                "-f", "mulaw",
                mulaw_path
            ]
            
            subprocess.run(convert_cmd, capture_output=True, timeout=10)
            
            # Return μ-law file
            return FileResponse(
                mulaw_path,
                media_type="audio/basic",
                filename=f"synthesized_{request.voice_id}.mulaw"
            )
        else:
            # Return WAV file
            return FileResponse(
                output_path,
                media_type="audio/wav",
                filename=f"synthesized_{request.voice_id}.wav"
            )
    
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Synthesis timeout"
        )
    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Synthesis failed"
        )
    finally:
        # Cleanup temporary files
        for temp_file in [output_path]:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

@app.post("/synthesize-url")
async def synthesize_audio_url(
    request: SynthesizeURLRequest,
    api_key: str = Depends(validate_api_key)
):
    """Synthesize audio and return URL to stored file - SUPREME COMMAND: Only Piper, no OS fallback"""
    
    # SUPREME COMMAND: Log compliance
    logger.info(f"SUPREME COMMAND COMPLIANCE: URL synthesis request - engine='{ENGINE_NAME}', voiceId='{request.voice_id}', format='{request.format}'")
    
    # SUPREME COMMAND: Validate voice - return 400 error, NO OS fallback
    if request.voice_id not in ALLOWED_VOICES:
        logger.error(f"SUPREME COMMAND VIOLATION: Invalid voice_id '{request.voice_id}' - returning 400 error, NO OS fallback")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid voice_id. Allowed voices: {ALLOWED_VOICES}. NO OS fallback available."
        )
    
    # Validate format
    if request.format not in ["wav", "mulaw"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Allowed formats: wav, mulaw"
        )
    
    model_path = voice_manager.get_voice_path(request.voice_id)
    config_path = voice_manager.get_config_path(request.voice_id)
    
    # SUPREME COMMAND: If Piper model missing, return 400 error - NO OS fallback
    if not model_path or not config_path:
        logger.error(f"SUPREME COMMAND VIOLATION: Piper model missing for '{request.voice_id}' - returning 400 error, NO OS fallback")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Piper voice model {request.voice_id} not available. NO OS fallback available."
        )
    
    try:
        # Generate filename based on text hash
        text_hash = hashlib.md5(request.text.encode()).hexdigest()[:8]
        filename = f"{request.voice_id}_{text_hash}.{request.format}"
        output_dir = "generated_audio"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        
        # SUPREME COMMAND: Use ONLY Piper for synthesis
        cmd = [
            "piper",
            "--model", model_path,
            "--config", config_path,
            "--output_file", output_path
        ]
        
        logger.info(f"SUPREME COMMAND COMPLIANCE: Running Piper URL synthesis - model='{request.voice_id}', engine='{ENGINE_NAME}'")
        
        # Run synthesis
        process = subprocess.run(
            cmd,
            input=request.text,
            text=True,
            capture_output=True,
            timeout=30
        )
        
        if process.returncode != 0:
            logger.error(f"SUPREME COMMAND VIOLATION: Piper synthesis failed for '{request.voice_id}': {process.stderr}")
            raise Exception(f"Piper synthesis failed: {process.stderr}")
        
        logger.info(f"SUPREME COMMAND COMPLIANCE: Piper URL synthesis successful for '{request.voice_id}'")
        
        # Convert to requested format if needed
        if request.format == "mulaw":
            # Convert to μ-law 8kHz
            mulaw_path = output_path.replace(".wav", ".mulaw")
            convert_cmd = [
                "ffmpeg", "-y",
                "-i", output_path,
                "-ar", "8000",
                "-ac", "1",
                "-f", "mulaw",
                mulaw_path
            ]
            
            subprocess.run(convert_cmd, capture_output=True, timeout=10)
            
            # Update output path to mulaw file
            output_path = mulaw_path
        
        # Return URL
        base_url = "http://localhost:8000"  # This should be configurable
        file_url = f"{base_url}/audio/{filename}"
        
        logger.info(f"SUPREME COMMAND COMPLIANCE: Generated audio URL for '{request.voice_id}' - engine='{ENGINE_NAME}'")
        
        return {
            "url": file_url,
            "filename": filename,
            "voice_id": request.voice_id,
            "format": request.format,
            "text_hash": text_hash,
            "engine": ENGINE_NAME  # SUPREME COMMAND: Include engine name in response
        }
    
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Synthesis timeout"
        )
    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Synthesis failed"
        )

@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve generated audio files"""
    audio_path = os.path.join("generated_audio", filename)
    
    if not os.path.exists(audio_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    media_type = "audio/wav" if filename.endswith(".wav") else "audio/basic"
    
    return FileResponse(
        audio_path,
        media_type=media_type,
        filename=filename
    )

@app.post("/admin/generate-api-key")
async def generate_api_key():
    """Generate a new API key (admin endpoint)"""
    key = api_key_manager.generate_key()
    key_data = api_key_manager.keys[key]
    
    return APIKeyResponse(
        api_key=key,
        created_at=key_data["created_at"],
        expires_at=key_data["expires_at"]
    )

@app.get("/admin/api-keys")
async def list_api_keys():
    """List all API keys (admin endpoint)"""
    keys_info = []
    for key, data in api_key_manager.keys.items():
        keys_info.append({
            "api_key": key[:8] + "...",  # Masked key
            "created_at": data["created_at"],
            "expires_at": data["expires_at"],
            "requests_last_minute": data["rate_limit"]["requests"]
        })
    
    return {"api_keys": keys_info}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

