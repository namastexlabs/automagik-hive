# TODO: Memory System Agent

## Objective
Implement a persistent memory system using SqliteMemoryDb that enables pattern detection, user memory tracking, and session management across all agents in the PagBank system.

## Technical Requirements
- [ ] Set up SqliteMemoryDb with persistent storage file
- [ ] Configure Memory object with enable_agentic_memory=True
- [ ] Implement user memory creation and retrieval system
- [ ] Create session summary generation after each conversation
- [ ] Develop pattern detection for recurring issues:
  - Common technical problems
  - Frequent customer complaints
  - Repeated fraud attempts
  - Service improvement opportunities
- [ ] Configure memory retention policies (30-day default)
- [ ] Implement memory search functionality
- [ ] Create memory backup and restore procedures
- [ ] Set up shared memory access for all agents
- [ ] Implement team_session_state persistence

## Code Structure
```python
pagbank/  # Root project directory (clean structure)
  memory/
    memory_config.py              # Memory system configuration ✅ COMPLETED
    memory_manager.py             # Core memory management ✅ COMPLETED
    pattern_detector.py           # Pattern analysis algorithms ✅ COMPLETED
    session_manager.py            # Session state management ✅ COMPLETED
  data/
    memory/
      pagbank_memory_dev.db      # SQLite database files ✅ COMPLETED
      pagbank_sessions.db        # Session database ✅ COMPLETED
  config/
    database.py                   # Database configuration ✅ AVAILABLE
```

## Research Required
- Agno memory.v2 documentation
- SqliteMemoryDb configuration options
- Agentic memory best practices
- Pattern detection algorithms
- Session state persistence strategies
- Memory search optimization

## Integration Points
- Input from: All agents (memory creation)
- Output to: Main orchestrator (pattern insights)
- Shared with: All specialist teams (historical context)
- Critical for: Frustration detection, personalization

## Testing Checklist
- [ ] Unit tests for memory CRUD operations
- [ ] Integration test with multiple agents
- [ ] Pattern detection accuracy validation
- [ ] Session state persistence across restarts
- [ ] Memory search performance (<100ms)
- [ ] Concurrent access stress testing
- [ ] Memory size growth monitoring
- [ ] Backup/restore functionality test

## Deliverables
1. Configured SqliteMemoryDb instance
2. Memory management module
3. Pattern detection system
4. Session state persistence layer
5. Memory usage analytics report

## Implementation Example
```python
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno import Claude
from typing import Dict, List, Any

class PagBankMemoryManager:
    def __init__(self):
        # Initialize persistent memory
        self.memory_db = SqliteMemoryDb(
            table_name="pagbank_memories",
            db_file="pagbank/memory/memory_db/pagbank_memory.db"
        )
        
        self.memory = Memory(
            db=self.memory_db,
            enable_agentic_memory=True
        )
    
    def detect_patterns(self, user_id: str) -> Dict[str, Any]:
        """Detect recurring patterns in user interactions"""
        memories = self.memory.search(
            f"user:{user_id}",
            limit=50
        )
        
        patterns = {
            "technical_issues": [],
            "frustration_indicators": [],
            "common_requests": [],
            "fraud_attempts": []
        }
        
        # Pattern detection logic
        for memory in memories:
            # Analyze memory content for patterns
            pass
        
        return patterns
    
    def create_session_summary(self, session_data: Dict) -> str:
        """Create summary of conversation session"""
        summary = {
            "customer_id": session_data["customer_id"],
            "topics_discussed": session_data["routing_history"],
            "resolution_status": session_data["resolved"],
            "frustration_level": session_data["frustration_level"],
            "key_insights": self._extract_insights(session_data)
        }
        
        # Store summary in memory
        self.memory.add(
            content=str(summary),
            metadata={
                "type": "session_summary",
                "customer_id": session_data["customer_id"],
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return summary
```

## Session State Structure
```python
team_session_state = {
    # Customer identification
    "customer_id": "string",
    "customer_name": "string",
    
    # Interaction tracking
    "interaction_count": 0,
    "clarification_count": 0,
    "frustration_level": 0,  # 0-3 scale
    
    # History
    "message_history": [],
    "routing_history": [],
    
    # Current state
    "current_topic": "string",
    "last_topic": "string",
    "resolved": False,
    "awaiting_human": False,
    
    # Support data
    "tickets": [],
    "protocols": [],
    
    # Quality metrics
    "satisfaction_score": None,
    "resolution_time": None,
    
    # Customer context
    "customer_context": {
        "education_level": "unknown",
        "communication_style": "unknown",
        "preferred_channel": "chat"
    }
}
```

## Priority Items
1. Frustration pattern detection (critical for escalation)
2. Technical issue tracking (improve product)
3. Session continuity (remember previous conversations)
4. Fraud attempt logging (security requirement)
5. Performance optimization for real-time access