#!/usr/bin/env python3
"""
Test script for message validation

Tests empty message validation on different agent execution endpoints
to ensure the validation is working before messages reach Claude API.
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_empty_message_validation():
    """Test that empty messages are caught and return user-friendly errors."""
    
    base_url = "http://localhost:9888"
    
    # Test cases with empty messages
    test_cases = [
        {
            "name": "Empty message on /runs (JSON)",
            "url": f"{base_url}/runs",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "data": json.dumps({"message": "", "agent_id": "pagbank-specialist"})
        },
        {
            "name": "Whitespace-only message on /runs (JSON)",
            "url": f"{base_url}/runs",
            "method": "POST", 
            "headers": {"Content-Type": "application/json"},
            "data": json.dumps({"message": "   ", "team_id": "ana"})
        },
        {
            "name": "Missing message on /runs (JSON)",
            "url": f"{base_url}/runs",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "data": json.dumps({"team_id": "ana"})
        },
        {
            "name": "Empty message on versioned endpoint",
            "url": f"{base_url}/runs?version=1",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "data": json.dumps({"message": "", "agent_id": "pagbank-specialist"})
        }
    ]
    
    # Test with multipart form data (Agno's standard format)
    multipart_cases = [
        {
            "name": "Empty message on /runs (multipart)",
            "url": f"{base_url}/runs",
            "method": "POST",
            "form_data": {"message": "", "team_id": "ana"}
        },
        {
            "name": "Whitespace-only message on /runs (multipart)",
            "url": f"{base_url}/runs", 
            "method": "POST",
            "form_data": {"message": "   ", "agent_id": "pagbank-specialist"}
        }
    ]
    
    print("🧪 Testing empty message validation...")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        
        # Test JSON requests
        for test in test_cases:
            print(f"\n📋 Test: {test['name']}")
            try:
                async with session.request(
                    test["method"],
                    test["url"],
                    headers=test.get("headers", {}),
                    data=test.get("data")
                ) as response:
                    status = response.status
                    response_text = await response.text()
                    
                    if status == 400:
                        try:
                            response_json = json.loads(response_text)
                            error_code = response_json.get("error", {}).get("code")
                            error_message = response_json.get("error", {}).get("message")
                            
                            if error_code == "EMPTY_MESSAGE":
                                print(f"✅ PASS: Got expected empty message error")
                                print(f"   Status: {status}")
                                print(f"   Error: {error_message}")
                            else:
                                print(f"⚠️  PARTIAL: Got 400 error but wrong code: {error_code}")
                                print(f"   Message: {error_message}")
                        except json.JSONDecodeError:
                            print(f"⚠️  PARTIAL: Got 400 status but non-JSON response")
                            print(f"   Response: {response_text[:200]}")
                    else:
                        print(f"❌ FAIL: Expected 400 error, got {status}")
                        print(f"   Response: {response_text[:200]}")
                        
            except aiohttp.ClientError as e:
                print(f"❌ FAIL: Connection error: {e}")
            except Exception as e:
                print(f"❌ FAIL: Unexpected error: {e}")
        
        # Test multipart form data requests
        for test in multipart_cases:
            print(f"\n📋 Test: {test['name']}")
            try:
                form_data = aiohttp.FormData()
                for key, value in test["form_data"].items():
                    form_data.add_field(key, value)
                
                async with session.request(
                    test["method"],
                    test["url"],
                    data=form_data
                ) as response:
                    status = response.status
                    response_text = await response.text()
                    
                    if status == 400:
                        try:
                            response_json = json.loads(response_text)
                            error_code = response_json.get("error", {}).get("code")
                            error_message = response_json.get("error", {}).get("message")
                            
                            if error_code == "EMPTY_MESSAGE":
                                print(f"✅ PASS: Got expected empty message error")
                                print(f"   Status: {status}")
                                print(f"   Error: {error_message}")
                            else:
                                print(f"⚠️  PARTIAL: Got 400 error but wrong code: {error_code}")
                                print(f"   Message: {error_message}")
                        except json.JSONDecodeError:
                            print(f"⚠️  PARTIAL: Got 400 status but non-JSON response")
                            print(f"   Response: {response_text[:200]}")
                    else:
                        print(f"❌ FAIL: Expected 400 error, got {status}")
                        print(f"   Response: {response_text[:200]}")
                        
            except aiohttp.ClientError as e:
                print(f"❌ FAIL: Connection error: {e}")
            except Exception as e:
                print(f"❌ FAIL: Unexpected error: {e}")
    
    print("\n" + "="*60)
    print("🎯 Test Summary:")
    print("   - Empty messages should return 400 status")
    print("   - Error should have code 'EMPTY_MESSAGE'")
    print("   - Message should be user-friendly")
    print("   - This prevents raw Claude API errors from reaching users")


async def test_valid_message():
    """Test that valid messages still work normally."""
    
    base_url = "http://localhost:9888"
    
    print("\n🔍 Testing valid message handling...")
    print("="*60)
    
    test_message = "Hello, this is a test message"
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test with JSON
            async with session.post(
                f"{base_url}/runs",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"message": test_message, "team_id": "ana"})
            ) as response:
                status = response.status
                response_text = await response.text()
                
                print(f"📋 Valid message test (JSON):")
                print(f"   Status: {status}")
                
                if status == 200:
                    print("✅ PASS: Valid message processed successfully")
                elif status == 400:
                    print("❌ FAIL: Valid message was rejected")
                    print(f"   Response: {response_text[:200]}")
                else:
                    print(f"ℹ️  INFO: Got status {status} (may be expected for missing components)")
                    
        except Exception as e:
            print(f"❌ FAIL: Error testing valid message: {e}")


if __name__ == "__main__":
    print("🚀 Starting message validation tests...")
    print("   Make sure the server is running on http://localhost:9888")
    print("   Run: make dev")
    print()
    
    asyncio.run(test_empty_message_validation())
    asyncio.run(test_valid_message())
    
    print("\n✨ Testing complete!")
    print("   If tests pass, empty messages are now caught before reaching Claude API")
    print("   If tests fail, check server logs and middleware configuration")