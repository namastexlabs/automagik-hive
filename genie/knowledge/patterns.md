# 🧠 Discovered Patterns

## Multi-LLM Collaboration Pattern
**Context**: When facing complex problems for the first time  
**Solution**: Use `mcp__zen__chat` with Gemini-2.5-pro, referencing @codebase.md  
**Benefits**: 
- Leverages 1M context window
- Gets fresh perspective
- Validates approaches
- Discovers edge cases

## HITL Safety Pattern
**Context**: Any system modification that could impact stability  
**Solution**: Agent proposes → Human reviews → System applies  
**Benefits**:
- 80% automation value
- 1% risk compared to full autonomy
- Builds trust incrementally
- Maintains accountability

## Constitutional Constraints Pattern
**Context**: Preventing goal drift in autonomous systems  
**Solution**: Embed immutable rules that cannot be overridden  
**Example**:
```yaml
constitution:
  max_agents: 50
  max_depth: 3
  forbidden: ["file_write", "network_access"]
```
**Benefits**:
- Hard boundaries prevent runaway expansion
- Clear limits enable safe experimentation
- Simplifies debugging and rollback

## Template-Based Generation Pattern
**Context**: Dynamic component creation with safety  
**Solution**: Pre-approved templates with parameter substitution  
**Benefits**:
- Reduces configuration errors
- Ensures consistency
- Limits attack surface
- Speeds up development

## Timestamp Versioning Pattern
**Context**: Automatic version management without conflicts  
**Solution**: Use `YYYYMMDDHHMMSS` format for versions  
**Example**: `data-analyzer-20250126103045`  
**Benefits**:
- No manual version bumps
- Natural ordering
- Conflict-free
- Audit trail built-in

## Knowledge Evolution Pattern
**Context**: System learning without database complexity  
**Solution**: CSV-based RAG with hot-reload  
**Benefits**:
- Simple to implement
- Immediate availability
- Version controlled
- Human readable

## Resource Quota Pattern
**Context**: Preventing resource exhaustion  
**Solution**: Hierarchical limits with circuit breakers  
```python
quotas = {
    "api_tokens_per_hour": 100000,
    "max_concurrent_agents": 10,
    "memory_per_agent": "512MB"
}
```
**Benefits**:
- Prevents "fork bomb" scenarios
- Predictable costs
- Graceful degradation
- Easy monitoring

## Integration Discovery Pattern
**Context**: Understanding component dependencies  
**Solution**: Analyze YAML for cross-references  
**Benefits**:
- Prevents breaking changes
- Enables impact analysis
- Supports safe removal
- Documents relationships