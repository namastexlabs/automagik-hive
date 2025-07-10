# PagBank Knowledge System Fix Plan

## Issue Summary

The PagBank multi-agent system has several critical knowledge base issues that prevent proper information retrieval:

1. **Fixed**: `valid_metadata_filters` was incorrectly set as list instead of set
2. **Critical**: Missing OpenAI API key for embedding generation
3. **Critical**: Database constraint violations (NULL id values)
4. **Info Gap**: CSV shows 651 entries but startup logs show "571 entries"
5. **Management**: No clear process for updating knowledge base over time

## Root Cause Analysis

### 1. Knowledge Base Loading Failures

**Problem**: The knowledge base fails to load with two main errors:

```
ERROR: The api_key client option must be set either by passing api_key to the client or by setting the OPENAI_API_KEY environment variable

ERROR: null value in column "id" of relation "pagbank_knowledge" violates not-null constraint
```

**Root Cause**: 
- Missing OpenAI API key configuration
- Agno's PgVector implementation requires proper document IDs during upsert operations
- CSV reading process may not be generating proper document IDs

### 2. Startup Count Discrepancy

**Problem**: System reports "571 entries" but CSV has 651 entries (plus header)

**Root Cause**: Count likely comes from cached/old database state rather than current CSV file

### 3. Agent Search Returns "0 documents"

**Problem**: When agents search knowledge, they get no results

**Root Cause**: Knowledge base is not properly loaded due to embedding/database issues above

## Detailed Fix Plan

### Phase 1: Environment Configuration (Immediate)

#### 1.1 OpenAI API Key Setup
```bash
# Option A: Set environment variable
export OPENAI_API_KEY="your-api-key-here"

# Option B: Add to .env file
echo "OPENAI_API_KEY=your-api-key-here" >> .env

# Option C: Alternative embedder (no API key needed)
# Use local embeddings like Ollama or FastEmbed
```

#### 1.2 Database Reset
```bash
# Clear existing knowledge base to start fresh
# Connect to PostgreSQL and drop table
psql postgresql+psycopg://ai:ai@localhost:5532/ai -c "DROP TABLE IF EXISTS ai.pagbank_knowledge;"
```

### Phase 2: Code Fixes (Critical)

#### 2.1 Fix Knowledge Base Initialization ✅ COMPLETED
- [x] Changed `valid_metadata_filters` from list to set
- [x] This prevents the AttributeError: 'list' object has no attribute 'add'

#### 2.2 Enhanced Error Handling
```python
# Add to csv_knowledge_base.py
def load_knowledge_base(self, recreate: bool = False) -> None:
    """Load knowledge base into vector database with enhanced error handling"""
    try:
        print(f"Loading knowledge base from {self.csv_path}")
        
        # Verify OpenAI API key
        import os
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Verify CSV file exists and count rows
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
        
        import pandas as pd
        df = pd.read_csv(self.csv_path)
        print(f"CSV contains {len(df)} entries")
        
        # Load with proper error handling
        self.knowledge_base.load(recreate=recreate, upsert=True)
        print(f"Successfully loaded {len(df)} entries to knowledge base")
        
    except Exception as e:
        print(f"Knowledge base loading failed: {e}")
        print("Possible solutions:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Check PostgreSQL connection")
        print("3. Verify CSV file format")
        raise
```

#### 2.3 Alternative Embedder Configuration
```python
# Option for local embeddings (no API key needed)
from agno.embedder.ollama import OllamaEmbedder
from agno.embedder.fastembed import FastEmbedEmbedder

# In csv_knowledge_base.py, replace OpenAIEmbedder with:
embedder=FastEmbedEmbedder()  # Local, no API key needed
# OR
embedder=OllamaEmbedder()     # Requires local Ollama server
```

### Phase 3: Knowledge Base Management Strategy

#### 3.1 Update Workflow Design

Based on Agno documentation research, here's the recommended workflow for managing knowledge base updates:

```python
class KnowledgeBaseManager:
    """Manages PagBank knowledge base updates and maintenance"""
    
    def __init__(self, kb: PagBankCSVKnowledgeBase):
        self.kb = kb
        
    def update_from_csv(self, csv_path: str, strategy: str = "upsert"):
        """
        Update knowledge base from CSV file
        
        Strategies:
        - "recreate": Drop and rebuild entire knowledge base
        - "upsert": Update existing + add new entries  
        - "append": Only add new entries (skip_existing=True)
        """
        
        if strategy == "recreate":
            print("🔄 Recreating knowledge base from scratch...")
            self.kb.load_knowledge_base(recreate=True)
            
        elif strategy == "upsert":
            print("🔀 Upserting changes to knowledge base...")
            self.kb.knowledge_base.load(recreate=False, upsert=True, skip_existing=False)
            
        elif strategy == "append":
            print("➕ Adding new entries only...")
            self.kb.knowledge_base.load(recreate=False, upsert=False, skip_existing=True)
    
    def add_single_entry(self, content: str, metadata: dict):
        """Add a single new knowledge entry"""
        self.kb.knowledge_base.load_dict({
            "content": content,
            "metadata": metadata
        }, upsert=True)
    
    def validate_and_report(self):
        """Validate knowledge base and generate report"""
        stats = self.kb.get_knowledge_statistics()
        validation = self.kb.validate_knowledge_base()
        
        print("📊 Knowledge Base Report:")
        print(f"  Total entries: {stats.get('total_entries', 'Unknown')}")
        print(f"  Areas: {list(stats.get('by_area', {}).keys())}")
        print(f"  Validation status: {validation.get('overall_status', 'Unknown')}")
        
        return validation
```

#### 3.2 Recommended Update Process

1. **Daily Updates** (Minor changes):
   ```python
   # Add individual entries or small updates
   manager.add_single_entry(
       content="New PIX feature explanation...",
       metadata={"area": "conta_digital", "tipo_produto": "pix", "tipo_informacao": "beneficios"}
   )
   ```

2. **Weekly Updates** (Batch changes):
   ```python
   # Upsert from updated CSV
   manager.update_from_csv("updated_knowledge.csv", strategy="upsert")
   ```

3. **Monthly Rebuilds** (Full refresh):
   ```python
   # Complete recreation for major updates
   manager.update_from_csv("pagbank_knowledge.csv", strategy="recreate")
   ```

### Phase 4: Monitoring and Maintenance

#### 4.1 Health Check System
```python
def knowledge_health_check():
    """Automated health check for knowledge base"""
    kb = create_pagbank_knowledge_base()
    
    # Test 1: Basic connectivity
    try:
        stats = kb.get_knowledge_statistics()
        print(f"✅ Knowledge base connected - {stats['total_entries']} entries")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Test 2: Search functionality  
    try:
        results = kb.knowledge_base.search("cartão de crédito", num_documents=1)
        if len(results) > 0:
            print("✅ Search functionality working")
        else:
            print("⚠️ Search returns no results")
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return False
    
    # Test 3: Team-specific searches
    for team in ['cartoes', 'conta_digital', 'investimentos']:
        try:
            results = kb.search_with_filters("test", team=team, max_results=1)
            print(f"✅ {team} team search: {len(results)} results")
        except Exception as e:
            print(f"❌ {team} team search failed: {e}")
    
    return True
```

#### 4.2 Update Notification System
```python
class KnowledgeUpdateNotifier:
    """Notifies when knowledge base needs updates"""
    
    def check_csv_freshness(self):
        """Check if CSV file is newer than last knowledge base update"""
        csv_mtime = self.kb.csv_path.stat().st_mtime
        # Compare with vector DB last update timestamp
        # Trigger update if CSV is newer
        
    def detect_missing_coverage(self, query_logs: List[str]):
        """Analyze query logs to find knowledge gaps"""
        # Track queries that return no results
        # Suggest new knowledge areas to add
```

## Implementation Priority

### Immediate (Fix blocking issues):
1. ✅ Fix `valid_metadata_filters` set vs list issue
2. 🔄 Configure OpenAI API key or alternative embedder  
3. 🔄 Reset and reload knowledge base cleanly
4. 🔄 Verify agent search functionality

### Short-term (1-2 weeks):
1. Implement KnowledgeBaseManager class
2. Add health check system
3. Create update workflow documentation
4. Set up monitoring for knowledge base freshness

### Long-term (1 month):
1. Automated knowledge gap detection
2. Content suggestion system based on query patterns
3. A/B testing for knowledge base improvements
4. Integration with PagBank content management system

## Risk Mitigation

### Backup Strategy
- Always backup vector database before major updates
- Keep versioned CSV files with timestamp
- Test updates in staging environment first

### Rollback Plan
```python
def rollback_knowledge_base(backup_csv_path: str):
    """Emergency rollback to previous knowledge state"""
    kb = create_pagbank_knowledge_base()
    # Load from backup CSV with recreate=True
    kb.knowledge_base.load(recreate=True)
```

### Monitoring Alerts
- Alert if knowledge base search returns consistently low results
- Alert if embedding API costs spike unexpectedly  
- Alert if knowledge base size changes dramatically

## Success Metrics

1. **Technical Metrics**:
   - Knowledge base loads without errors
   - Search queries return >0 results for known topics
   - Response time < 2 seconds for knowledge searches

2. **Business Metrics**:
   - Increased agent confidence scores
   - Reduced "I don't know" responses
   - Improved customer satisfaction with answers

3. **Operational Metrics**:
   - Knowledge base uptime > 99.9%
   - Update deployment time < 5 minutes
   - Zero data loss during updates

This plan addresses both the immediate technical issues and establishes a sustainable long-term strategy for knowledge base management.