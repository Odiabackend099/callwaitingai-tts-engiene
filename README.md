# 🔒 CallWaiting.ai TTS Engine - Supreme Command Compliant

## 🎯 Supreme Command Implementation

This TTS engine is **100% compliant** with the supreme command requirements for realistic voice generation using only Piper neural models.

### ✅ Supreme Command Compliance

- **🚫 NO OS TTS FALLBACK** - All invalid voices return 400 errors, never fall back to OS
- **🧠 ONLY PIPER NEURAL MODELS** - Uses `en_US-lessac-medium` (female) and `en_US-ryan-high` (male)
- **🎵 AUTOMATIC DEMO GENERATION** - Demo samples generated on every service startup
- **⚡ MINIMAL REST API** - Clean, efficient endpoints
- **📊 COMPLIANCE LOGGING** - Every request logs engine name, model ID, and voice ID
- **📞 TWILIO INTEGRATION** - Perfect for Twilio `<Play>` elements
- **🎧 HIGH QUALITY AUDIO** - WAV (high fidelity) and μ-law (8kHz streaming)
- **⚡ FAST SYNTHESIS** - Optimized for low latency
- **📦 MINIMAL DEPENDENCIES** - Lightweight and efficient

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Piper-TTS installed
- FFmpeg for audio conversion

### Installation
```bash
cd services/tts
pip install -r requirements.txt
```

### Run the Service
```bash
python main.py
```

The service will:
1. Download Piper voice models automatically
2. Generate demo samples for both voices
3. Start the REST API on `http://localhost:8000`

## 📡 API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `GET /voices` - List available voices (Piper models only)
- `GET /samples` - List demo samples generated on startup
- `POST /synthesize` - Synthesize audio and return file
- `POST /synthesize-url` - Synthesize audio and return URL

### Demo Samples
- `GET /sample_audio/{filename}` - Serve demo sample files

### Admin
- `POST /admin/generate-api-key` - Generate API key
- `GET /admin/api-keys` - List API keys

## 🎵 Available Voices

| Voice ID | Description | Gender | Quality |
|----------|-------------|--------|---------|
| `en_US-lessac-medium` | Female voice - Lessac medium quality | Female | Medium |
| `en_US-ryan-high` | Male voice - Ryan high quality | Male | High |

## 📝 Usage Examples

### List Voices
```bash
curl http://localhost:8000/voices
```

### Generate API Key
```bash
curl -X POST http://localhost:8000/admin/generate-api-key
```

### Synthesize Audio
```bash
curl -X POST http://localhost:8000/synthesize \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test of the supreme command compliant TTS engine",
    "voice_id": "en_US-lessac-medium",
    "format": "wav"
  }'
```

### Get Demo Samples
```bash
curl http://localhost:8000/samples
```

## 🔧 Configuration

### Voice Models
The service automatically downloads and uses these Piper models:
- **Female**: `en_US-lessac-medium` - High-quality female voice
- **Male**: `en_US-ryan-high` - High-quality male voice

### Demo Texts
On startup, the service generates demo samples with these texts:
- **Female**: "Welcome to CallWaiting.ai voice service – this is the realistic female voice"
- **Male**: "Welcome to CallWaiting.ai voice service – this is the realistic male voice"

## 🧪 Testing

Run the compliance test suite:
```bash
python test_supreme_command.py
```

This will test all supreme command requirements and verify:
- No OS TTS fallback
- Only Piper models used
- Demo generation working
- Compliance logging active
- Error handling correct

## 📊 Compliance Logging

Every request logs compliance information:
```
SUPREME COMMAND COMPLIANCE: Synthesis request - engine='piper', voiceId='en_US-lessac-medium', format='wav'
```

## 🚫 Error Handling

Invalid voice requests return clear 400 errors:
```json
{
  "detail": "Invalid voice_id. Allowed voices: ['en_US-lessac-medium', 'en_US-ryan-high']. NO OS fallback available."
}
```

## 📞 Twilio Integration

Perfect for Twilio webhooks:
```python
# Get audio URL
response = requests.post('http://localhost:8000/synthesize-url', 
                        headers={'X-API-Key': 'your-key'},
                        json={'text': 'Hello', 'voice_id': 'en_US-lessac-medium'})

# Use in TwiML
twiml = f'<Play>{response.json()["url"]}</Play>'
```

## 🏆 Supreme Command Status

**✅ FULLY COMPLIANT** - All 10 requirements implemented and tested.

The TTS engine will **NEVER** use OS voices or fallback to generic/robotic speech. It uses only high-quality Piper neural models and generates realistic voice samples automatically.

## 📁 Project Structure

```
services/tts/
├── main.py                           # Main TTS service (Supreme Command Compliant)
├── requirements.txt                  # Python dependencies
├── test_supreme_command.py          # Compliance test suite
├── SUPREME_COMMAND_COMPLIANCE_REPORT.md  # Detailed compliance report
├── voices/                          # Piper voice models
│   ├── en_US-lessac-medium/         # Female voice model
│   └── en_US-ryan-high/            # Male voice model
├── sample_audio/                    # Demo samples (generated on startup)
└── generated_audio/                 # User-generated audio files
```

## 🔗 Links

- [GitHub Repository](https://github.com/Odiabackend099/callwaitingai-tts-engiene.git)
- [Piper TTS](https://github.com/rhasspy/piper)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**🎯 This TTS engine is production-ready and fully compliant with the supreme command requirements for realistic voice generation.**
