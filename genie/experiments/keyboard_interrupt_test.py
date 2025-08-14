#!/usr/bin/env python3
"""
Test script to validate KeyboardInterrupt handling issue in cli/docker_manager.py

This script demonstrates the current bug and can be used to validate the fix.
FORGE_TASK_ID: 1161972c-9107-4c83-9aee-a13468eb33f0
"""

import signal
import sys
import time
from typing import List, Tuple


def simulate_current_behavior():
    """Simulate the current buggy behavior without KeyboardInterrupt handling."""
    print("🔍 Simulating current behavior (BUGGY)")
    print("This simulates how the current _interactive_install method behaves")
    print("Press Ctrl+C to see ungraceful termination...\n")
    
    try:
        # Simulate the current input calls that lack KeyboardInterrupt handling
        user_input = input("Would you like to install Hive Core? (Y/n): ")
        print(f"✅ You entered: {user_input}")
    except KeyboardInterrupt:
        # This shows what would happen if we DON'T handle it properly
        print("\n💥 CRASH! Ungraceful termination (current behavior)")
        raise  # Re-raise to show the crash
    

def simulate_fixed_behavior():
    """Simulate the fixed behavior with proper KeyboardInterrupt handling."""
    print("🔧 Simulating FIXED behavior")  
    print("This shows how the method should behave after the fix")
    print("Press Ctrl+C to see graceful handling...\n")
    
    try:
        user_input = input("Would you like to install Hive Core? (Y/n): ")
        print(f"✅ You entered: {user_input}")
        return True
    except KeyboardInterrupt:
        print("\n👋 Installation cancelled by user")
        return False


def analyze_input_calls():
    """Analyze the input() calls in the actual file."""
    print("📊 Analysis of input() calls in cli/docker_manager.py:")
    print("=" * 60)
    
    try:
        with open('/home/namastex/workspace/automagik-hive/cli/docker_manager.py', 'r') as f:
            lines = f.readlines()
        
        input_calls: List[Tuple[int, str]] = []
        in_interactive_install = False
        
        for i, line in enumerate(lines, 1):
            if 'def _interactive_install' in line:
                in_interactive_install = True
                print(f"🎯 Found _interactive_install method at line {i}")
            elif in_interactive_install and line.strip().startswith('def ') and '_interactive_install' not in line:
                in_interactive_install = False
                print(f"🏁 End of method at line {i}")
                break
            elif in_interactive_install and 'input(' in line and not line.strip().startswith('#'):
                input_calls.append((i, line.strip()))
        
        print(f"\n🐛 Found {len(input_calls)} vulnerable input() calls:")
        for line_num, line_content in input_calls:
            print(f"   Line {line_num}: {line_content}")
        
        # Check for existing KeyboardInterrupt handling
        file_content = ''.join(lines)
        if 'KeyboardInterrupt' in file_content:
            print("\n✅ KeyboardInterrupt handling found in file")
        else:
            print("\n❌ No KeyboardInterrupt handling found in file")
            print("🚨 BUG CONFIRMED: All input() calls are vulnerable")
            
        return input_calls
        
    except FileNotFoundError:
        print("❌ Could not find cli/docker_manager.py")
        return []


def demonstrate_problem():
    """Demonstrate the KeyboardInterrupt issue."""
    print("🧪 KeyboardInterrupt Handling Test")
    print("=" * 50)
    
    # First analyze the file
    input_calls = analyze_input_calls()
    
    if not input_calls:
        print("❌ Could not analyze input calls")
        return
    
    print("\n" + "=" * 50)
    print("🔄 Interactive Testing")
    print("Choose test mode:")
    print("1. Test current (buggy) behavior") 
    print("2. Test fixed behavior")
    print("3. Skip interactive test")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            print("\n🐛 Testing current behavior...")
            time.sleep(1)
            simulate_current_behavior()
        elif choice == "2":
            print("\n🔧 Testing fixed behavior...")
            time.sleep(1)
            result = simulate_fixed_behavior()
            print(f"Result: {result}")
        elif choice == "3":
            print("✅ Skipping interactive test")
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n💥 Demo interrupted! This shows the current problem.")


if __name__ == "__main__":
    demonstrate_problem()