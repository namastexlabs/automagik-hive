# Status Update Verification Guide

## Quick Verification Steps

### 1. Start Development Server
```bash
# From project root
make dev

# Or with background execution
Bash(command="make dev", run_in_background=True)
```

### 2. Monitor Logs
```bash
# Watch for status update messages
tail -f logs/server.log | grep -E "(Content status|processing|completed|error)"
```

### 3. Upload Test Document
- Open AgentOS UI: `http://localhost:8886/agui`
- Navigate to Knowledge section
- Upload a multi-page PDF (e.g., 5+ pages)
- Watch the UI for loading spinner behavior

### 4. Expected Log Output

#### Success Path
```
INFO Starting document processing content_id=abc123
INFO Page-based splitting completed content_id=abc123 page_groups=3
INFO Content status updated to completed content_id=abc123
INFO Database persistence completed persisted_count=3
```

#### Error Path
```
ERROR Page-based splitting failed content_id=abc123 error_type=ValueError
ERROR Content status updated to error content_id=abc123
```

### 5. Database Verification

#### Check Status in Database
```sql
-- Connect to database
psql $HIVE_DATABASE_URL

-- Query knowledge content status
SELECT id, name, status, status_message, created_at, updated_at
FROM agno.agno_knowledge
WHERE id = 'your_uploaded_document_id'
ORDER BY updated_at DESC
LIMIT 10;

-- Expected result for successful upload:
--  id    | name         | status    | status_message | created_at | updated_at
-- -------+--------------+-----------+----------------+------------+------------
--  abc123| document.pdf | completed | NULL           | 2025-10-15 | 2025-10-15
```

#### Verify Document Chunks
```sql
-- Check that child documents exist in knowledge_base
SELECT id, name, meta_data->>'page_range_start' as page_start,
       meta_data->>'page_range_end' as page_end,
       meta_data->>'parent_knowledge_id' as parent_id
FROM agno.knowledge_base
WHERE meta_data->>'parent_knowledge_id' = 'abc123'
ORDER BY (meta_data->>'page_range_start')::int;

-- Expected result for 3-page document (2 pages per chunk):
--  id              | name         | page_start | page_end | parent_id
-- -----------------+--------------+------------+----------+-----------
--  abc123_pages_1-2| document.pdf | 1          | 2        | abc123
--  abc123_pages_3-3| document.pdf | 3          | 3        | abc123
```

### 6. UI Behavior Verification

#### Expected UI Flow
1. **Upload initiated**: Status shows "Processing..."
2. **Processing in progress**: Loading spinner visible, polling `/knowledge/content/{id}/status`
3. **Processing complete**: Status updates to "Completed", spinner disappears
4. **Document available**: Can view/search uploaded content

#### Polling Endpoint Check
```bash
# Monitor status endpoint calls
curl -s http://localhost:8886/api/v1/knowledge/content/abc123/status

# Expected response (success):
{
  "status": "completed",
  "id": "abc123",
  "name": "document.pdf"
}

# Expected response (error):
{
  "status": "error",
  "id": "abc123",
  "name": "document.pdf",
  "error": "Processing failed: ..."
}
```

## Troubleshooting

### Issue: Status Stuck in "Processing"
**Symptoms**: UI shows infinite loading spinner, status never updates

**Check**:
1. Verify `contents_db` is initialized:
   ```python
   # In logs
   grep "Content status updated" logs/server.log
   ```

2. Check for errors in status update:
   ```python
   grep "Failed to update content status" logs/server.log
   ```

3. Verify database connection:
   ```sql
   SELECT 1 FROM agno.agno_knowledge LIMIT 1;
   ```

**Fix**: Ensure `HIVE_DATABASE_URL` is set correctly and database is accessible

### Issue: Status Shows "Error" Incorrectly
**Symptoms**: Document processed successfully but shows error status

**Check**:
1. Review processing logs for actual errors:
   ```python
   grep -A 10 "PROCESSING ERROR DETAILS" logs/server.log
   ```

2. Check if error occurred during processing:
   ```python
   grep "Processing failed for content" logs/server.log
   ```

**Fix**: Address the underlying processing error (PDF extraction, entity extraction, etc.)

### Issue: Multiple Status Updates
**Symptoms**: Status changes multiple times or flips between states

**Check**:
1. Verify single `_load_content()` call per upload:
   ```python
   grep "Starting document processing" logs/server.log | grep "content_id=abc123"
   ```

2. Check for concurrent processing:
   ```sql
   SELECT COUNT(*) FROM agno.agno_knowledge WHERE id = 'abc123';
   -- Should return 1, not multiple rows
   ```

**Fix**: Ensure upload endpoint doesn't trigger multiple processing calls

## Status Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                      Document Upload                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │   processing   │ ◄─── Initial status set by Agno
                  └────────┬───────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   PDF Extraction &     │
              │   Page Splitting       │
              └────────┬───────────────┘
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
   ┌──────────┐              ┌──────────┐
   │ SUCCESS  │              │  ERROR   │
   └────┬─────┘              └────┬─────┘
        │                         │
        ▼                         ▼
   ┌──────────┐              ┌──────────┐
   │completed │              │  error   │ ◄─── status_message contains error
   └────┬─────┘              └────┬─────┘
        │                         │
        ▼                         ▼
   ┌──────────┐              ┌──────────┐
   │UI shows  │              │UI shows  │
   │success   │              │error     │
   └──────────┘              └──────────┘
```

## Implementation Notes

### Status String Values
- `"processing"`: Initial state (set by Agno framework)
- `"completed"`: Successfully processed and persisted
- `"error"`: Processing failed with error message

### Database Fields
- `status`: String field in `agno_knowledge.status`
- `status_message`: Optional error message in `agno_knowledge.status_message`

### Update Method
```python
# Get existing row
existing = self.knowledge.contents_db.get_knowledge_content(content_id)

# Update status
if existing:
    existing.status = "completed"  # or "error"
    existing.status_message = error_msg  # For errors only

    # Persist update
    self.knowledge.contents_db.upsert_knowledge_content(existing)
```

## Performance Expectations

- **Page splitting**: <2s for 10-page PDF
- **Status update**: <100ms per update
- **UI polling interval**: ~1s between checks
- **Total upload time**: 3-5s for typical multi-page PDF

## Related Files

- `/lib/knowledge/row_based_csv_knowledge.py` - Status update implementation
- `/agno/db/schemas/knowledge.py` - KnowledgeRow schema definition
- `/api/routes/knowledge.py` - Status polling endpoint
- `/lib/knowledge/config/knowledge_processing.yaml` - Processing configuration

---
**Last Updated**: 2025-10-15 19:43 UTC
**Agent**: hive-coder
