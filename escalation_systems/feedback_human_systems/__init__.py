"""
Feedback Collection and Human Agent Mock System for PagBank Multi-Agent System.

This module provides:
- Feedback Collector Agent for customer feedback management
- Human Agent Mock system for simulating human agent responses
- Conversation history management
- Feedback analytics and pattern detection
"""

from .conversation_manager import ConversationManager
from .feedback_analyzer import FeedbackAnalyzer
from .feedback_collector import FeedbackCollector
from .human_agent_mock import HumanAgentMock

__all__ = [
    "FeedbackCollector",
    "HumanAgentMock",
    "ConversationManager",
    "FeedbackAnalyzer"
]