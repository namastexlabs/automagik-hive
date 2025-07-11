# Step 4: Testing and Validation Plan

## Overview
This plan addresses the remaining 50% of Step 4 implementation, including comprehensive testing, validation of document counts, and ensuring the refactored system works correctly.

## 1. Document Count Validation

### Issue
- Plan expected: 39 documents (10 + 15 + 14)
- Actually found: 64 documents

### Validation Tasks
1. **Manual count verification**
   - Count `---` separators in each file
   - Verify parsing logic handles edge cases correctly
   - Check for duplicate documents or parsing errors

2. **Create validation script**
   ```python
   # preprocessing/validate_document_count.py
   - Count documents using different methods
   - Compare results
   - Identify any discrepancies
   ```

## 2. Comprehensive Testing Suite

### 2.1 Unit Tests

#### Knowledge Base Tests (`tests/test_knowledge_base.py`)
- [ ] Test CSV loading with new 4-column format
- [ ] Test business_unit filtering
- [ ] Test knowledge retrieval for each unit
- [ ] Test hybrid unit handling ("Adquirência Web / Adquirência Presencial")
- [ ] Test edge cases (empty queries, special characters)

#### Routing Tests (`tests/test_routing_logic.py`)
- [ ] Test routing accuracy for each business unit
- [ ] Test ambiguous query handling
- [ ] Test confidence scoring
- [ ] Test clarification question generation
- [ ] Validate all 64 documents route correctly

#### Agent Tests (`tests/test_business_unit_agents.py`)
- [ ] Test each agent initialization
- [ ] Test knowledge filtering per agent
- [ ] Test escalation triggers
- [ ] Test agent response format

### 2.2 Integration Tests

#### End-to-End Query Tests (`tests/test_e2e_queries.py`)
- [ ] Test complete query flow for each business unit:
  - Adquirência: "Como antecipar vendas da Cielo?"
  - Emissão: "Meu cartão não chegou"
  - PagBank: "Erro ao fazer PIX"
  - Hybrid: Test queries that should use hybrid unit docs

#### Knowledge Retrieval Accuracy (`tests/test_knowledge_accuracy.py`)
- [ ] For each of the 64 documents:
  - Extract the problem
  - Query the system
  - Verify correct knowledge is retrieved
  - Check business unit routing

### 2.3 Performance Tests

#### Load Tests (`tests/test_performance.py`)
- [ ] Measure query response time
- [ ] Test concurrent queries
- [ ] Verify vector search performance
- [ ] Check memory usage

## 3. Validation Scripts

### 3.1 Document Count Validator
```python
# preprocessing/validate_document_count.py
"""
Validate document counts match between:
1. Manual count of --- separators
2. Parsed documents in validation script
3. Generated CSV rows
4. Expected counts from plan
"""
```

### 3.2 Business Unit Coverage Validator
```python
# preprocessing/validate_business_unit_coverage.py
"""
Ensure all business units have adequate coverage:
- Minimum documents per unit
- Variety of problems covered
- No orphaned documents
"""
```

### 3.3 Knowledge Retrieval Validator
```python
# tests/validate_knowledge_retrieval.py
"""
Test that each document's knowledge can be retrieved:
- Query with problem text
- Verify solution matches
- Check business unit assignment
"""
```

## 4. Missing Functionality Tests

### 4.1 Hybrid Unit Handling
- [ ] Verify "Adquirência Web / Adquirência Presencial" documents are accessible
- [ ] Test queries that should match hybrid unit
- [ ] Ensure no routing conflicts

### 4.2 Edge Cases
- [ ] Multi-line content in CSV
- [ ] Special characters in queries
- [ ] Empty or null fields
- [ ] Very long documents (conta.md has 50+ line docs)

### 4.3 Error Handling
- [ ] Missing knowledge base
- [ ] Corrupted CSV
- [ ] Database connection failures
- [ ] Agent initialization failures

## 5. Test Execution Plan

### Phase 1: Validation (Day 1)
1. Run document count validation
2. Verify business unit extraction
3. Validate CSV generation accuracy
4. Address any discrepancies found

### Phase 2: Unit Testing (Day 1-2)
1. Run existing tests with new structure
2. Create missing unit tests
3. Fix any failing tests
4. Achieve 90%+ code coverage

### Phase 3: Integration Testing (Day 2)
1. Run end-to-end query tests
2. Validate knowledge retrieval accuracy
3. Test all 64 document scenarios
4. Verify routing accuracy

### Phase 4: Performance & Load Testing (Day 3)
1. Baseline performance metrics
2. Load test with concurrent users
3. Optimize if needed
4. Document performance characteristics

### Phase 5: User Acceptance Testing (Day 3)
1. Test with real user queries
2. Validate response quality
3. Check response times
4. Gather feedback

## 6. Rollback Plan

### 6.1 Create Backup
```bash
# Create backup before testing
tar -czf pagbank_backup_$(date +%Y%m%d).tar.gz \
  knowledge/knowledge_rag.csv \
  agents/specialists/*.py \
  orchestrator/routing_logic.py
```

### 6.2 Rollback Procedure
1. Restore old CSV
2. Restore old agent files
3. Revert routing logic
4. Clear vector database
5. Restart services

## 7. Success Criteria

### Functional Criteria
- [ ] All 64 documents are accessible via queries
- [ ] Each business unit handles its domain correctly
- [ ] Routing accuracy > 90%
- [ ] Knowledge retrieval accuracy > 95%
- [ ] No critical errors in 1000 test queries

### Performance Criteria
- [ ] Average query response < 2 seconds
- [ ] 99th percentile response < 5 seconds
- [ ] Support 10 concurrent users
- [ ] Memory usage < 2GB

### Quality Criteria
- [ ] Responses are accurate and helpful
- [ ] Appropriate escalation when needed
- [ ] Clear error messages
- [ ] Consistent response format

## 8. Test Data

### Sample Queries per Business Unit

#### Adquirência (11 docs)
1. "Como antecipar vendas?"
2. "Não consigo antecipar vendas da Cielo"
3. "Qual taxa de antecipação?"
4. "Antecipação agendada não funciona"
5. "Critérios para antecipação"

#### Emissão (13 docs)
1. "Solicitar cartão de crédito"
2. "Cartão não chegou"
3. "Aumentar limite do cartão"
4. "Cartão internacional não funciona"
5. "Cobrança de anuidade"

#### PagBank (40 docs)
1. "Fazer PIX"
2. "Erro no aplicativo"
3. "Folha de pagamento"
4. "Tarifa administrativa"
5. "Cadastrar chave PIX"

## 9. Documentation Updates

### 9.1 Test Results Documentation
- Document all test results
- Create test coverage report
- List known issues and limitations
- Performance benchmarks

### 9.2 User Guide Updates
- Update with new business unit structure
- Document query examples
- Explain routing behavior
- Add troubleshooting guide

## 10. Timeline

- **Day 1**: Validation & Unit Tests (8 hours)
- **Day 2**: Integration Tests (6 hours)
- **Day 3**: Performance Tests & UAT (6 hours)
- **Total**: 20 hours

## Next Steps

1. First, validate document count discrepancy
2. Create missing test files
3. Execute tests in phases
4. Document results
5. Address any issues found
6. Sign off on implementation