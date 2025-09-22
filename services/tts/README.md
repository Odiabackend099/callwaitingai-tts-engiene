# CallWaiting.ai TTS Engine - Global API Service

🚀 **Finalized TTS engine with Nigerian voice integration**  
🔒 **Strict rule: Realistic voices only - NO robotic sounds**

## Features

- **3 High-Quality Voices**: Ryan (Male), Lessac (Female), Nigerian Female
- **REST API**: Clean endpoints for all projects
- **API Key Authentication**: 10 keys generated automatically
- **File Serving**: Audio files served at `/audio/<filename>.wav`
- **Nigerian Voice**: Integrated Nigerian-accented female voice
- **Demo Samples**: Pre-generated samples for all voices

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the TTS engine
python main.py
```

The service will start on `http://localhost:8000` and automatically:
- Generate 10 API keys
- Download Nigerian voice model
- Create demo samples for all voices

## API Endpoints

### Health Check
```bash
GET /health
```

### Get Available Voices
```bash
GET /voices
```

### Synthesize Audio (File)
```bash
POST /synthesize
Headers: x-api-key: YOUR_API_KEY
Body: {
  "text": "Hello world",
  "voiceId": "naija_female",
  "format": "wav"
}
```

### Synthesize Audio (URL)
```bash
POST /synthesize-url
Headers: x-api-key: YOUR_API_KEY
Body: {
  "text": "Hello world",
  "voiceId": "naija_female",
  "format": "wav"
}
```

### Serve Audio Files
```bash
GET /audio/{filename}
```

## Available Voices

| Voice ID | Name | Type | Description |
|----------|------|------|-------------|
| `en_US-ryan-high` | Ryan (Male) | Piper | High-quality male voice |
| `en_US-lessac-medium` | Lessac (Female) | Piper | High-quality female voice |
| `naija_female` | Nigerian Female | Nigerian | Nigerian-accented female voice |

## Integration Examples

### React Web Widget

```javascript
const synthesizeVoice = async (text, voiceId = 'naija_female') => {
  const response = await fetch('http://localhost:8000/synthesize-url', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': 'YOUR_API_KEY'
    },
    body: JSON.stringify({
      text: text,
      voiceId: voiceId,
      format: 'wav'
    })
  });
  
  const result = await response.json();
  
  if (result.success) {
    // Play the audio
    const audio = new Audio(result.audio_url);
    audio.play();
  }
};

// Usage
synthesizeVoice('Hello, welcome to CallWaiting AI', 'naija_female');
```

### Twilio IVR Integration

```python
from twilio.twiml import VoiceResponse

def handle_call():
    response = VoiceResponse()
    
    # Generate audio URL using TTS API
    tts_response = requests.post('http://localhost:8000/synthesize-url', 
        headers={'x-api-key': 'YOUR_API_KEY'},
        json={
            'text': 'Welcome to CallWaiting AI. How can I help you today?',
            'voiceId': 'naija_female',
            'format': 'wav'
        }
    )
    
    if tts_response.status_code == 200:
        audio_url = tts_response.json()['audio_url']
        response.play(audio_url)
    else:
        response.say('Welcome to CallWaiting AI')
    
    return str(response)
```

### WhatsApp Bot (n8n)

```javascript
// n8n HTTP Request Node Configuration
{
  "method": "POST",
  "url": "http://localhost:8000/synthesize-url",
  "headers": {
    "Content-Type": "application/json",
    "x-api-key": "YOUR_API_KEY"
  },
  "body": {
    "text": "{{ $json.message }}",
    "voiceId": "naija_female",
    "format": "wav"
  }
}

// Then use the audio_url in WhatsApp media message
```

### Node.js Integration

```javascript
const axios = require('axios');

class CallWaitingTTS {
  constructor(apiKey, baseUrl = 'http://localhost:8000') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
  }
  
  async synthesize(text, voiceId = 'naija_female', format = 'wav') {
    try {
      const response = await axios.post(`${this.baseUrl}/synthesize-url`, {
        text,
        voiceId,
        format
      }, {
        headers: {
          'x-api-key': this.apiKey
        }
      });
      
      return response.data;
    } catch (error) {
      throw new Error(`TTS Error: ${error.response?.data?.detail || error.message}`);
    }
  }
  
  async getVoices() {
    const response = await axios.get(`${this.baseUrl}/voices`);
    return response.data;
  }
}

// Usage
const tts = new CallWaitingTTS('YOUR_API_KEY');
const result = await tts.synthesize('Hello from Nigerian voice!', 'naija_female');
console.log('Audio URL:', result.audio_url);
```

### Python Integration

```python
import requests

class CallWaitingTTS:
    def __init__(self, api_key, base_url="http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
    
    def synthesize(self, text, voice_id="naija_female", format="wav"):
        response = requests.post(
            f"{self.base_url}/synthesize-url",
            headers={"x-api-key": self.api_key},
            json={
                "text": text,
                "voiceId": voice_id,
                "format": format
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"TTS Error: {response.json().get('detail', 'Unknown error')}")
    
    def get_voices(self):
        response = requests.get(f"{self.base_url}/voices")
        return response.json()

# Usage
tts = CallWaitingTTS("YOUR_API_KEY")
result = tts.synthesize("Hello from Nigerian voice!", "naija_female")
print(f"Audio URL: {result['audio_url']}")
```

## Environment Variables

- `TTS_HOST`: Base URL for the TTS service (default: `http://localhost:8000`)

## API Key Management

API keys are automatically generated on first run and stored in `api_keys.json`. Each key includes:
- Creation timestamp
- Expiration date (1 year)
- Rate limit (1000 requests/hour)
- Usage counter

## Demo Samples

Pre-generated demo samples are available at:
- `http://localhost:8000/audio/demo_en_US_ryan_high.wav`
- `http://localhost:8000/audio/demo_en_US_lessac_medium.wav`
- `http://localhost:8000/audio/demo_naija_female.wav`

## Deployment

### Local Development
```bash
python main.py
```

### Docker (Future AWS Deployment)
```bash
# Build image
docker build -t callwaiting-tts .

# Run container
docker run -p 8000:8000 -e TTS_HOST=https://your-domain.com callwaiting-tts
```

## Nigerian Voice Model

The Nigerian female voice (`naija_female`) uses the Ngadou/Nigerian Accent TTS model from Hugging Face. This provides authentic Nigerian-accented English speech synthesis.

**Model Details:**
- Repository: `Ngadou/nigerian_accent_tts_en`
- Type: SpeechT5 fine-tuned for Nigerian English
- Sample Rate: 22.05kHz
- Format: WAV (16-bit PCM)

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `400`: Invalid request (bad voice ID, missing text)
- `401`: Authentication error (invalid/missing API key)
- `404`: Audio file not found
- `500`: Internal server error

## Rate Limiting

Each API key has a rate limit of 1000 requests per hour. Usage is tracked and can be monitored via the `/admin/keys` endpoint.

## Support

For issues or questions:
1. Check the logs in `tts_engine.log`
2. Verify API key is valid
3. Ensure voice models are properly installed
4. Check network connectivity to the service

---

**🎯 Mission Accomplished: Global TTS API Service Ready!**  
**🔒 Strict Rule Compliance: Realistic voices only - NO robotic sounds**  
**🌍 Nigerian voice integration complete**
