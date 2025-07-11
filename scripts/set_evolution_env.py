#!/usr/bin/env python3
"""Set Evolution API environment variables for the session"""

import os

# Set Evolution API environment variables
os.environ["EVOLUTION_API_BASE_URL"] = "http://192.168.112.142:8080"
os.environ["EVOLUTION_API_API_KEY"] = "BEE0266C2040-4D83-8FAA-A9A3EF89DDEF"
os.environ["EVOLUTION_API_INSTANCE"] = "SofIA"
os.environ["EVOLUTION_API_FIXED_RECIPIENT"] = "5511986780008@s.whatsapp.net"

print("✅ Evolution API environment variables set:")
print(f"   BASE_URL: {os.environ['EVOLUTION_API_BASE_URL']}")
print(f"   INSTANCE: {os.environ['EVOLUTION_API_INSTANCE']}")
print(f"   RECIPIENT: {os.environ['EVOLUTION_API_FIXED_RECIPIENT']}")
print("\nYou can now run playground.py and WhatsApp should work!")