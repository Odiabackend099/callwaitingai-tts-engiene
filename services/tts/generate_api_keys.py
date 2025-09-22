#!/usr/bin/env python3
"""
Generate API keys for the TTS engine
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

def generate_api_keys():
    """Generate 10 API keys for the TTS engine"""
    print("🔑 GENERATING API KEYS FOR TTS ENGINE")
    print("=" * 50)
    
    # Create API keys
    keys = {}
    for i in range(10):
        key = f"cw_tts_{uuid.uuid4().hex[:16]}"
        keys[key] = {
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=365)).isoformat(),
            "rate_limit": 1000,  # requests per hour
            "used": 0
        }
    
    # Save to file
    api_keys_file = Path("api_keys.json")
    with open(api_keys_file, 'w') as f:
        json.dump(keys, f, indent=2)
    
    print("✅ Generated 10 API keys:")
    print()
    
    for i, (key, info) in enumerate(keys.items(), 1):
        print(f"{i:2d}. {key}")
        print(f"    Created: {info['created_at'][:10]}")
        print(f"    Expires: {info['expires_at'][:10]}")
        print(f"    Rate Limit: {info['rate_limit']} requests/hour")
        print()
    
    print("📁 API keys saved to: api_keys.json")
    print("🔒 Keep these keys secure and don't share them publicly")
    
    return keys

def main():
    """Main function"""
    print("🚀 CallWaiting.ai TTS Engine - API Key Generator")
    print("🎯 Mission: Generate 10 API keys for TTS service")
    print()
    
    keys = generate_api_keys()
    
    print("\n🏆 MISSION SUCCESS!")
    print("✅ 10 API keys generated successfully")
    print("✅ Keys saved to api_keys.json")
    print("✅ Ready for TTS engine authentication")
    
    return keys

if __name__ == "__main__":
    keys = main()
