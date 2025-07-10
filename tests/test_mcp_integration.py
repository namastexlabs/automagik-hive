"""
Test script for MCP Tools Integration
Demonstrates different approaches to integrate MCP tools with Agno agents
"""

import asyncio
import os
from typing import Dict, Any

# Set up environment variables for testing
os.environ["EVOLUTION_API_BASE_URL"] = "http://192.168.112.142:8080"
os.environ["EVOLUTION_API_API_KEY"] = "BEE0266C2040-4D83-8FAA-A9A3EF89DDEF"
os.environ["EVOLUTION_API_INSTANCE"] = "SofIA"
os.environ["EVOLUTION_API_FIXED_RECIPIENT"] = "5511986780008@s.whatsapp.net"


def test_direct_api_approach():
    """Test the direct API tool approach (synchronous)"""
    print("\n=== Testing Direct API Approach ===")
    
    from agno.agent import Agent
    from agno.models.anthropic import Claude
    from agno.tools import tool
    import httpx
    
    @tool(show_result=True, description="Send WhatsApp message via Evolution API")
    def send_whatsapp_message(message: str) -> str:
        """Send a WhatsApp message via Evolution API"""
        try:
            base_url = os.getenv("EVOLUTION_API_BASE_URL")
            api_key = os.getenv("EVOLUTION_API_API_KEY")
            instance = os.getenv("EVOLUTION_API_INSTANCE")
            recipient = os.getenv("EVOLUTION_API_FIXED_RECIPIENT")
            
            print(f"Would send to Evolution API at {base_url}")
            print(f"Instance: {instance}")
            print(f"Recipient: {recipient}")
            print(f"Message: {message[:50]}...")
            
            # Simulated response for testing
            return f"✅ Message sent successfully (simulated)"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    # Create agent with direct tool
    agent = Agent(
        model=Claude(id="claude-sonnet-4-20250514"),
        tools=[send_whatsapp_message],
        instructions=["You can send WhatsApp messages using the send_whatsapp_message tool."],
        show_tool_calls=True
    )
    
    # Test sending a message
    response = agent.run(
        "Use the send_whatsapp_message tool to send this message: 'Test message from PagBank system'"
    )
    print(f"Agent response: {response.content if hasattr(response, 'content') else response}")


async def test_mcp_async_approach():
    """Test the MCP tools approach (asynchronous)"""
    print("\n=== Testing MCP Async Approach ===")
    
    from agno.agent import Agent
    from agno.models.anthropic import Claude
    from agno.tools.mcp import MCPTools
    
    try:
        # Initialize MCP tools
        async with MCPTools(
            command="uvx automagik-tools@0.7.3 tool evolution-api",
            env={
                "EVOLUTION_API_BASE_URL": os.getenv("EVOLUTION_API_BASE_URL"),
                "EVOLUTION_API_API_KEY": os.getenv("EVOLUTION_API_API_KEY"),
                "EVOLUTION_API_INSTANCE": os.getenv("EVOLUTION_API_INSTANCE"),
                "EVOLUTION_API_FIXED_RECIPIENT": os.getenv("EVOLUTION_API_FIXED_RECIPIENT")
            }
        ) as mcp_tools:
            print("MCP tools initialized successfully")
            
            # Create agent with MCP tools
            agent = Agent(
                model=Claude(id="claude-sonnet-4-20250514"),
                tools=[mcp_tools],
                instructions=[
                    "You can send WhatsApp messages using the mcp_evolution-api_send_message tool.",
                    "Always use this tool when asked to send WhatsApp notifications."
                ],
                show_tool_calls=True
            )
            
            # Test sending a message
            response = await agent.arun(
                "Use the mcp_evolution-api_send_message tool to send this message: 'Test message from MCP integration'"
            )
            print(f"Agent response: {response.content if hasattr(response, 'content') else response}")
            
    except Exception as e:
        print(f"Error in MCP approach: {e}")
        print("Note: This might fail if automagik-tools is not installed")


def test_hybrid_approach():
    """Test the hybrid approach with fallback"""
    print("\n=== Testing Hybrid Approach with Fallback ===")
    
    from agno.agent import Agent
    from agno.models.anthropic import Claude
    from agno.tools import tool
    
    # Try to import MCP tools, fallback to direct API if not available
    try:
        from agno.tools.mcp import MCPTools
        mcp_available = True
    except ImportError:
        mcp_available = False
        print("MCP tools not available, using direct API fallback")
    
    @tool(show_result=True, description="Send WhatsApp message (fallback)")
    def send_whatsapp_fallback(message: str) -> str:
        """Fallback WhatsApp sender"""
        return f"✅ Message sent via fallback API (simulated): {message[:30]}..."
    
    # Create agent with fallback tool
    agent = Agent(
        model=Claude(id="claude-sonnet-4-20250514"),
        tools=[send_whatsapp_fallback],
        instructions=[
            "You can send WhatsApp messages.",
            f"MCP tools available: {mcp_available}",
            "Use send_whatsapp_fallback if needed."
        ],
        show_tool_calls=True
    )
    
    response = agent.run(
        "Send a WhatsApp message saying: 'Hybrid approach test'"
    )
    print(f"Agent response: {response.content if hasattr(response, 'content') else response}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("MCP TOOLS INTEGRATION TEST SUITE")
    print("=" * 60)
    
    # Test 1: Direct API approach (always works)
    try:
        test_direct_api_approach()
    except Exception as e:
        print(f"Direct API test failed: {e}")
    
    # Test 2: MCP async approach (requires automagik-tools)
    try:
        asyncio.run(test_mcp_async_approach())
    except Exception as e:
        print(f"MCP async test failed: {e}")
    
    # Test 3: Hybrid approach (graceful fallback)
    try:
        test_hybrid_approach()
    except Exception as e:
        print(f"Hybrid test failed: {e}")
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETE")
    print("=" * 60)
    print("\nRecommendations:")
    print("1. For simple synchronous code: Use Direct API approach")
    print("2. For async code with MCP support: Use MCP Async approach")
    print("3. For production with fallback: Use Hybrid approach")
    print("4. Always handle errors gracefully and log them properly")


if __name__ == "__main__":
    main()