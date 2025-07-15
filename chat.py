#!/usr/bin/env python3
"""
Rich-based chat application that looks like a web chat interface
Uses API endpoints to get all events and display them in chat form
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Rich imports
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.prompt import Prompt
from rich.align import Align
from rich.status import Status
from rich.rule import Rule
from rich.table import Table
from rich.columns import Columns
from rich.padding import Padding
from rich.box import ROUNDED
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

console = Console()

class WebChatInterface:
    """Rich-based web-style chat interface using API endpoints"""
    
    def __init__(self, api_base_url: str = "http://localhost:9888"):
        self.api_base_url = api_base_url
        self.session = None
        self.messages = []
        self.events = []
        self.session_id = None
        self.connected = False
        self.layout = Layout()
        self.live = None
        self.running = True
        
    def setup_layout(self):
        """Setup the Rich layout to look like a web chat"""
        # Main layout: header, chat area, input area
        self.layout.split(
            Layout(name="header", size=5),
            Layout(name="chat_area", ratio=1),
            Layout(name="input_area", size=5),
        )
        
        # Header with title and status
        self.update_header()
        
        # Chat area with messages and events side by side
        self.layout["chat_area"].split_row(
            Layout(name="messages", ratio=2),
            Layout(name="events", ratio=1)
        )
        
        # Input area - show current input or prompt
        self.update_input_area()
        
        # Initialize panels
        self.update_messages_panel()
        self.update_events_panel()
    
    def update_header(self):
        """Update header with connection status"""
        status_color = "green" if self.connected else "red"
        status_icon = "🟢" if self.connected else "🔴"
        
        header_content = Table.grid(padding=1)
        header_content.add_column(justify="left")
        header_content.add_column(justify="center")
        header_content.add_column(justify="right")
        
        header_content.add_row(
            f"[bold white]Ana Chat[/bold white]",
            f"[bold cyan]Real-time Agent Monitor[/bold cyan]",
            f"[{status_color}]{status_icon} {('Connected' if self.connected else 'Disconnected')}[/{status_color}]"
        )
        
        if self.session_id:
            header_content.add_row(
                "",
                f"[dim]Session: {self.session_id[:8]}...[/dim]",
                f"[dim]Messages: {len(self.messages)} | Events: {len(self.events)}[/dim]"
            )
        
        self.layout["header"].update(
            Panel(
                header_content,
                style="blue",
                box=ROUNDED
            )
        )
    
    def update_messages_panel(self):
        """Update messages panel with chat-style layout"""
        if not self.messages:
            content = Align.center(
                Text("👋 Welcome to Ana Chat!\n\n"
                     "Ask me anything about PagBank services.\n"
                     "I'll route your query to the right specialist.",
                     style="dim italic")
            )
        else:
            # Create message bubbles
            message_content = []
            for i, msg in enumerate(self.messages[-15:]):  # Show last 15 messages
                message_content.append(self.create_message_bubble(msg, i))
                message_content.append("")  # Spacing between messages
            
            content = "\n".join(message_content)
        
        self.layout["messages"].update(
            Panel(
                content,
                title="💬 Chat Messages",
                border_style="green",
                box=ROUNDED,
                padding=(1, 2)
            )
        )
    
    def create_message_bubble(self, msg: Dict[str, Any], index: int) -> str:
        """Create a web-style message bubble"""
        sender = msg["sender"]
        content = msg["content"]
        timestamp = msg.get("timestamp", "")
        success_info = msg.get("success_info", "")
        
        # Different styles for different senders
        if sender == "You":
            # User message - right aligned, blue
            bubble_style = "blue"
            prefix = "                    "  # Right align
            icon = "👤"
        elif sender == "Ana":
            # Ana message - left aligned, cyan
            bubble_style = "cyan"
            prefix = ""
            icon = "🤖"
        elif sender == "Specialist":
            # Specialist message - left aligned, green
            bubble_style = "green"
            prefix = ""
            icon = "👨‍💼"
        else:
            # System message - center, yellow
            bubble_style = "yellow"
            prefix = "          "
            icon = "🔧"
        
        # Format timestamp
        time_str = f" [dim]({timestamp})[/dim]" if timestamp else ""
        
        # Create bubble content
        bubble_content = f"[bold]{icon} {sender}[/bold]{time_str}\n"
        
        # Format message content
        if content.startswith('#'):
            # Markdown content for specialist
            bubble_content += f"[{bubble_style}]{content}[/{bubble_style}]"
        else:
            bubble_content += f"[{bubble_style}]{content}[/{bubble_style}]"
        
        # Add success info if present
        if success_info:
            bubble_content += f"\n[dim]{success_info}[/dim]"
        
        return f"{prefix}{bubble_content}"
    
    def update_events_panel(self):
        """Update events panel with real-time activity"""
        if not self.events:
            content = Align.center(
                Text("📊 No events yet...\n\n"
                     "Agent activity will appear here\n"
                     "when you send a message.",
                     style="dim italic")
            )
        else:
            # Create event stream
            event_content = []
            for event in self.events[-20:]:  # Show last 20 events
                event_content.append(self.format_event(event))
            
            content = "\n".join(event_content)
        
        self.layout["events"].update(
            Panel(
                content,
                title="📊 Agent Activity",
                border_style="yellow",
                box=ROUNDED,
                padding=(1, 1)
            )
        )
    
    def update_input_area(self):
        """Update the input area"""
        input_text = getattr(self, 'current_input', '')
        if input_text:
            content = f"[bold cyan]💬 {input_text}[/bold cyan]"
        else:
            content = "[dim]Ready for your message...[/dim]"
        
        self.layout["input_area"].update(
            Panel(
                content,
                title="💬 Chat Input",
                border_style="blue",
                box=ROUNDED
            )
        )
    
    def format_event(self, event: Dict[str, Any]) -> str:
        """Format an event for display"""
        event_type = event.get("type", "unknown")
        data = event.get("data", {})
        timestamp = event.get("timestamp", "")
        
        # Parse timestamp
        try:
            if timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime("%H:%M:%S")
            else:
                time_str = datetime.now().strftime("%H:%M:%S")
        except:
            time_str = datetime.now().strftime("%H:%M:%S")
        
        # Format based on event type
        if event_type == "team_init":
            return f"[dim]{time_str}[/dim] [green]🚀 Team initialized[/green]"
        elif event_type == "query_processing":
            query = data.get("query", "")[:40]
            return f"[dim]{time_str}[/dim] [blue]📝 Processing: {query}...[/blue]"
        elif event_type == "agent_selection":
            agent = data.get("agent_name", "Unknown")
            confidence = data.get("confidence", 0)
            return f"[dim]{time_str}[/dim] [magenta]👤 Selected: {agent}[/magenta]"
        elif event_type == "tool_usage":
            tool = data.get("tool_name", "Unknown")
            return f"[dim]{time_str}[/dim] [yellow]🔧 Using: {tool}[/yellow]"
        elif event_type == "knowledge_search":
            query = data.get("search_query", "")[:30]
            count = data.get("results_count", 0)
            return f"[dim]{time_str}[/dim] [cyan]📚 Search: {query}... → {count} results[/cyan]"
        elif event_type == "response_generated":
            length = data.get("response_length", 0)
            return f"[dim]{time_str}[/dim] [green]✅ Response: {length} chars[/green]"
        elif event_type == "success_criteria":
            words = data.get("word_count", 0)
            routing = data.get("has_routing", False)
            status = "✅" if words <= 15 and routing else "❌"
            return f"[dim]{time_str}[/dim] [bright_green]{status} Success: {words}/15 words[/bright_green]"
        elif event_type == "error":
            error = data.get("error_message", "")[:50]
            return f"[dim]{time_str}[/dim] [red]❌ Error: {error}...[/red]"
        else:
            return f"[dim]{time_str}[/dim] [white]📊 {event_type}[/white]"
    
    async def check_api_health(self) -> bool:
        """Check if the API is healthy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/api/v1/health") as response:
                    if response.status == 200:
                        return True
                    return False
        except:
            return False
    
    async def initialize_connection(self):
        """Initialize connection to the API"""
        try:
            # Check API health
            if not await self.check_api_health():
                console.print("❌ API server is not running. Please start it with: uv run python api/main.py", style="red")
                return False
            
            # Create session
            self.session = aiohttp.ClientSession()
            self.connected = True
            
            # Generate session ID
            self.session_id = f"chat-{int(time.time())}"
            
            # Add welcome message
            self.add_message("System", "✅ Connected to Ana API!\nReady to chat with PagBank specialists.")
            
            # Add initial event
            self.add_event({
                "type": "team_init",
                "data": {"team_name": "Ana Team"},
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            console.print(f"❌ Connection failed: {e}", style="red")
            return False
    
    def add_message(self, sender: str, content: str, timestamp: str = "", success_info: str = ""):
        """Add a message to the chat"""
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M:%S")
        
        message = {
            "sender": sender,
            "content": content,
            "timestamp": timestamp,
            "success_info": success_info
        }
        self.messages.append(message)
        
        # Update UI - will be refreshed in main loop
    
    def add_event(self, event: Dict[str, Any]):
        """Add an event to the events panel"""
        self.events.append(event)
        
        # Update UI - will be refreshed in main loop
    
    def check_success_criteria(self, response: str) -> tuple[bool, str]:
        """Check Ana's success criteria"""
        # Extract Ana's part only (before specialist response)
        ana_part = response.split('#')[0].strip()
        
        # Count words (clean text only)
        clean_text = re.sub(r'[^\w\s]', ' ', ana_part)
        word_count = len([w for w in clean_text.split() if w.strip()])
        
        # Check for routing
        has_routing = "forward_task_to_member" in response
        
        success = word_count <= 15 and has_routing
        
        if success:
            return True, f"✅ {word_count}/15 words + routing"
        else:
            issues = []
            if word_count > 15:
                issues.append(f"{word_count}/15 words")
            if not has_routing:
                issues.append("no routing")
            return False, f"❌ {', '.join(issues)}"
    
    def clean_response(self, response_text: str) -> str:
        """Clean up response text"""
        lines = [line.strip() for line in response_text.split('\n') if line.strip()]
        clean_lines = []
        
        for line in lines:
            # Skip debug/tool information
            if any(skip in line for skip in ['Tool Calls:', 'ID:', 'Arguments:', 'DEBUG', 'METRICS']):
                continue
            clean_lines.append(line)
        
        return '\n'.join(clean_lines)
    
    async def send_message(self, message: str):
        """Send message to Ana team via API"""
        if not self.session or not self.connected:
            self.add_message("System", "❌ Not connected to API. Please restart the application.")
            return
        
        # Add user message
        self.add_message("You", message)
        
        # Add processing event
        self.add_event({
            "type": "query_processing",
            "data": {"query": message},
            "timestamp": datetime.now().isoformat()
        })
        
        # Show thinking message
        self.add_message("Ana", "🤔 Thinking...")
        
        try:
            # Send to API
            start_time = time.time()
            
            # Simulate some events during processing
            await asyncio.sleep(0.1)
            self.add_event({
                "type": "agent_selection",
                "data": {"agent_name": "Ana Router", "confidence": 0.95},
                "timestamp": datetime.now().isoformat()
            })
            
            await asyncio.sleep(0.1)
            self.add_event({
                "type": "tool_usage",
                "data": {"tool_name": "search_knowledge_base"},
                "timestamp": datetime.now().isoformat()
            })
            
            # Make API call
            form_data = aiohttp.FormData()
            form_data.add_field('message', message)
            form_data.add_field('session_id', self.session_id)
            form_data.add_field('user_id', 'chat-user')
            form_data.add_field('stream', 'false')
            form_data.add_field('monitor', 'true')
            
            async with self.session.post(
                f"{self.api_base_url}/playground/teams/ana-pagbank-assistant/runs",
                data=form_data
            ) as response:
                elapsed_time = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Remove thinking message
                    self.messages.pop()
                    
                    # Process response
                    response_text = result.get("content", str(result))
                    clean_response = self.clean_response(response_text)
                    
                    # Check success criteria
                    success, criteria_msg = self.check_success_criteria(response_text)
                    
                    # Add success criteria event
                    self.add_event({
                        "type": "success_criteria",
                        "data": {
                            "word_count": len(clean_response.split()),
                            "has_routing": "forward_task_to_member" in response_text
                        },
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Format timing
                    timing = f"{elapsed_time:.1f}s"
                    
                    # Check for routing patterns
                    routing_phrases = ['Encaminhando para nosso especialista', 'Direcionando para nosso especialista', 'Conectando com especialista']
                    is_routing = any(phrase in clean_response for phrase in routing_phrases)
                    
                    if is_routing and '#' in clean_response:
                        # Split Ana's routing from specialist response
                        parts = clean_response.split('#', 1)
                        ana_response = parts[0].strip()
                        specialist_response = parts[1].strip() if len(parts) > 1 else ""
                        
                        # Add Ana's routing
                        self.add_message("Ana", ana_response, timing, criteria_msg)
                        
                        # Add specialist response if present
                        if specialist_response:
                            self.add_message("Specialist", f"#{specialist_response}")
                    else:
                        # Single response
                        self.add_message("Ana", clean_response, timing, criteria_msg)
                    
                    # Add response event
                    self.add_event({
                        "type": "response_generated",
                        "data": {"response_length": len(clean_response)},
                        "timestamp": datetime.now().isoformat()
                    })
                    
                else:
                    # Remove thinking message
                    self.messages.pop()
                    error_msg = await response.text()
                    self.add_message("System", f"❌ API Error: {error_msg}")
                    
                    # Add error event
                    self.add_event({
                        "type": "error",
                        "data": {"error_message": error_msg},
                        "timestamp": datetime.now().isoformat()
                    })
                    
        except Exception as e:
            # Remove thinking message
            if self.messages and self.messages[-1]["content"] == "🤔 Thinking...":
                self.messages.pop()
            
            self.add_message("System", f"❌ Error: {e}")
            
            # Add error event
            self.add_event({
                "type": "error",
                "data": {"error_message": str(e)},
                "timestamp": datetime.now().isoformat()
            })
    
    async def run(self):
        """Main run loop"""
        console.print("🚀 Starting Ana Chat...", style="yellow")
        
        # Initialize connection
        if not await self.initialize_connection():
            console.print("❌ Failed to initialize. Make sure the API server is running.", style="red")
            return
        
        # Setup layout
        self.setup_layout()
        
        # Use Live display with proper input integration
        with Live(self.layout, refresh_per_second=2, screen=False) as live:
            self.live = live
            
            # Main chat loop with integrated input
            while self.running:
                try:
                    # Show we're waiting for input
                    self.current_input = "Type your message and press Enter..."
                    self.update_input_area()
                    live.refresh()
                    
                    # Pause live to get clean input
                    live.stop()
                    
                    # Get user input
                    user_input = input()
                    
                    # Resume live display
                    live.start()
                    
                    # Clear input area
                    self.current_input = ""
                    self.update_input_area()
                    live.refresh()
                    
                    if user_input.strip():
                        if user_input.strip().lower() in ['quit', 'exit', 'bye']:
                            break
                        
                        # Send message
                        await self.send_message(user_input.strip())
                        
                        # Update displays
                        self.update_header()
                        self.update_messages_panel()
                        self.update_events_panel()
                        live.refresh()
                    
                except KeyboardInterrupt:
                    break
                except EOFError:
                    break
                except Exception as e:
                    console.print(f"Input error: {e}", style="red")
        
        # Cleanup
        if self.session:
            await self.session.close()
        
        console.print("👋 Chat session ended.", style="yellow")

async def main():
    """Main entry point"""
    # Check if API server is running
    chat = WebChatInterface()
    
    if not await chat.check_api_health():
        console.print("❌ API server is not running!", style="red")
        console.print("Please start the API server first:", style="yellow")
        console.print("  uv run python api/main.py", style="cyan")
        console.print("Then run this chat app again.", style="yellow")
        return
    
    await chat.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!", style="yellow")