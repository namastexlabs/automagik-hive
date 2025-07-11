#!/usr/bin/env python3
"""Start PagBank system with WhatsApp Evolution API configured"""

import os
import subprocess
import sys

# Set Evolution API environment variables
print("🔧 Configuring Evolution API for WhatsApp...")
os.environ["EVOLUTION_API_BASE_URL"] = "http://192.168.112.142:8080"
os.environ["EVOLUTION_API_API_KEY"] = "BEE0266C2040-4D83-8FAA-A9A3EF89DDEF"
os.environ["EVOLUTION_API_INSTANCE"] = "SofIA"
os.environ["EVOLUTION_API_FIXED_RECIPIENT"] = "5511986780008@s.whatsapp.net"

print("✅ Evolution API configured:")
print(f"   BASE_URL: {os.environ['EVOLUTION_API_BASE_URL']}")
print(f"   INSTANCE: {os.environ['EVOLUTION_API_INSTANCE']}")
print(f"   RECIPIENT: {os.environ['EVOLUTION_API_FIXED_RECIPIENT']}")
print()

# Start playground with the environment variables set
print("🚀 Starting PagBank Multi-Agent System with WhatsApp enabled...")
print()

# Use subprocess to run playground.py with the environment variables
subprocess.run([sys.executable, "playground.py"], env=os.environ)