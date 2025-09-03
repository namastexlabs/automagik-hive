# Technical Specification Document: ClaroCheck Validation Route Integration

## 1. OVERVIEW
**Objective**: Integrate a new claroCheck validation route into the existing processamento-faturas workflow to validate PO status before proceeding with monitoring operations.

**Success Metrics**: 
- Seamless integration without breaking existing workflow
- Proper status transition logic based on claroCheck API responses
- Improved reliability by validating PO readiness before monitoring
- Maintained compatibility with existing JSON structure and API patterns

## 2. FUNCTIONAL REQUIREMENTS

### Core Features
- **New Status Integration**: Add CHECK_ORDER_STATUS status between PENDING and WAITING_MONITORING/MONITORED
- **Individual PO Validation**: Process one PO at a time through claroCheck API
- **Dynamic Status Transition**: Route to different statuses based on API response validation
- **Response Parsing**: Extract and validate status information from claroCheck output
- **Retry Logic**: Handle validation failures and implement appropriate retry mechanisms

### User Stories
- As a system operator, I want POs to be validated before monitoring so that only ready orders are processed
- As a workflow designer, I want failed validations to be handled gracefully without breaking the entire batch
- As a data analyst, I want validation results to be logged and traceable for audit purposes
- As a system maintainer, I want the integration to follow existing patterns for consistency

## 3. NON-FUNCTIONAL REQUIREMENTS

### Performance
- claroCheck API calls should complete within 60 seconds (matching existing timeout)
- Individual processing should not significantly impact total daily execution time
- Batch processing efficiency maintained for generation and monitoring phases

### Security
- Maintain existing authentication and authorization patterns
- Secure handling of PO data in API payloads
- Proper error logging without exposing sensitive information

### Reliability
- Graceful handling of claroCheck API failures
- Proper status rollback if validation fails
- Integration with existing retry mechanisms (max 3 retries)

## 4. TECHNICAL ARCHITECTURE

### Updated Status Flow
```
Current Flow:
PENDING → WAITING_MONITORING → MONITORED → DOWNLOADED → UPLOADED

New Flow:
PENDING → CHECK_ORDER_STATUS → WAITING_MONITORING/MONITORED → DOWNLOADED → UPLOADED
```

### Enhanced ProcessingStatus Enum
```python
class ProcessingStatus(Enum):
    """CTE Processing Status Enum"""
    PENDING = "pending"
    CHECK_ORDER_STATUS = "check_order_status"  # NEW STATUS
    WAITING_MONITORING = "waiting_monitoring"
    MONITORED = "monitored"
    DOWNLOADED = "downloaded"
    UPLOADED = "uploaded"
    COMPLETED = "completed"
    FAILED_EXTRACTION = "failed_extraction"
    FAILED_GENERATION = "failed_generation"
    FAILED_MONITORING = "failed_monitoring"
    FAILED_VALIDATION = "failed_validation"  # NEW FAILURE TYPE
    FAILED_DOWNLOAD = "failed_download"
    FAILED_UPLOAD = "failed_upload"
```

### BrowserAPIClient Enhancement
```python
class BrowserAPIClient:
    # ... existing methods ...
    
    def build_claro_check_payload(self, po_number: str) -> dict[str, Any]:
        """Build payload for claroCheck API validation"""
        payload = {
            "flow_name": "claroCheck",
            "parameters": {
                "orders": [po_number],  # Single PO validation
                "headless": True        # Run headless for validation
            }
        }
        logger.info(f"🔍 Built claroCheck validation payload for PO {po_number}")
        return payload
    
    def parse_claro_check_response(self, api_response: dict[str, Any]) -> tuple[bool, str, str]:
        """Parse claroCheck response and determine status transition
        
        Returns:
            tuple: (success: bool, new_status: str, message: str)
        """
        try:
            # Extract response data
            output = api_response.get("api_result", {}).get("output", {})
            status_field = output.get("status", "")
            text_output = output.get("text_output", "")
            success = output.get("success", False)
            
            if not success:
                return False, "CHECK_ORDER_STATUS", f"Validation failed: {text_output}"
            
            # Status transition logic based on claroCheck response
            if status_field == "Aguardando Liberação":
                return True, "CHECK_ORDER_STATUS", "Order still awaiting liberation - will retry"
            elif status_field == "Agendamento Pendente":
                return True, "WAITING_MONITORING", "Order ready for monitoring"
            elif status_field == "Autorizada Emissão Nota Fiscal":
                return True, "MONITORED", "Order authorized - skip monitoring"
            else:
                logger.warning(f"Unknown claroCheck status: {status_field}")
                return True, "WAITING_MONITORING", f"Unknown status '{status_field}' - defaulting to monitoring"
                
        except Exception as e:
            logger.error(f"Error parsing claroCheck response: {e}")
            return False, "CHECK_ORDER_STATUS", f"Response parsing error: {str(e)}"
```

## 5. WORKFLOW INTEGRATION

### Updated JSON Analysis Step
```python
async def execute_json_analysis_step(step_input: StepInput) -> StepOutput:
    """Enhanced analysis with CHECK_ORDER_STATUS handling"""
    
    analysis_results = {
        "processing_categories": {
            "pending_pos": [],
            "validation_pos": [],      # NEW CATEGORY
            "monitoring_pos": [],
            "download_pos": [],
            "upload_pos": [],
            "completed_pos": [],
            "failed_pos": []
        }
        # ... rest of structure
    }
    
    # Enhanced status categorization
    for order in orders:
        status = order.get("status", "PENDING")
        po_entry = {"po_number": po_number, "json_file": json_file_path}
        
        if status == "PENDING":
            analysis_results["processing_categories"]["pending_pos"].append(po_entry)
        elif status == "CHECK_ORDER_STATUS":  # NEW STATUS HANDLING
            analysis_results["processing_categories"]["validation_pos"].append(po_entry)
        elif status == "WAITING_MONITORING":
            analysis_results["processing_categories"]["monitoring_pos"].append(po_entry)
        # ... rest of status handling
```

### Enhanced Status-Based Routing
```python
async def execute_status_based_routing_step(step_input: StepInput) -> StepOutput:
    """Enhanced routing with claroCheck validation queue"""
    
    routing_results = {
        "processing_queues": {
            "invoice_generation_queue": {
                "action": "invoiceGen",
                "pos": processing_categories["pending_pos"],
                "batch_processing": True,
                "priority": 1
            },
            "order_validation_queue": {  # NEW QUEUE
                "action": "claroCheck",
                "pos": processing_categories["validation_pos"],
                "batch_processing": False,  # Individual processing required
                "priority": 2
            },
            "invoice_monitoring_queue": {
                "action": "invoiceMonitor", 
                "pos": processing_categories["monitoring_pos"],
                "batch_processing": True,
                "priority": 3
            },
            # ... rest of queues with updated priorities
        }
    }
```

### Individual PO Processing Enhancement
```python
async def execute_individual_po_processing_step(step_input: StepInput) -> StepOutput:
    """Enhanced processing with claroCheck validation"""
    
    # ... existing queue processing logic ...
    
    elif action == "claroCheck":
        # Individual claroCheck validation processing
        individual_results = {}
        
        for po_data in pos:
            po_number = po_data["po_number"]
            json_file = po_data["json_file"]
            
            # Build claroCheck payload for individual PO
            payload = api_client.build_claro_check_payload(po_number)
            
            # Execute API call
            api_response = await api_client.execute_api_call("claroCheck", payload)
            
            # Parse response and determine status transition
            validation_success, new_status, message = api_client.parse_claro_check_response(api_response)
            
            # Record individual result
            individual_results[po_number] = {
                "http_success": api_response["success"],
                "validation_success": validation_success,
                "new_status": new_status,
                "message": message,
                "execution_time_ms": api_response.get("execution_time_ms", 0),
                "api_response": api_response.get("api_result", {})
            }
            
            # Update status based on validation result
            if api_response["success"] and validation_success:
                logger.info(f"✅ claroCheck validation successful for PO {po_number} - updating to {new_status}")
                processing_results["status_updates"][po_number] = {
                    "old_status": "CHECK_ORDER_STATUS",
                    "new_status": new_status,
                    "json_file": json_file,
                    "validation_message": message
                }
                processing_results["execution_summary"]["successful_actions"] += 1
                processing_results["execution_summary"]["pos_updated"] += 1
            else:
                # Validation failed - keep in CHECK_ORDER_STATUS for retry
                logger.warning(f"⚠️ claroCheck validation failed for PO {po_number}: {message}")
                processing_results["failed_orders"][po_number] = {
                    "action": "claroCheck",
                    "failure_type": "validation_failure",
                    "error": message,
                    "json_file": json_file
                }
                processing_results["execution_summary"]["failed_actions"] += 1
                processing_results["execution_summary"]["pos_failed"] += 1
```

## 6. API INTEGRATION DESIGN

### ClaroCheck Payload Structure
```json
{
    "flow_name": "claroCheck",
    "parameters": {
        "orders": ["600687310"],
        "headless": true
    }
}
```

### Expected Response Structure
```json
{
    "status": "success",
    "flow": "claroCheck",
    "output": {
        "success": true,
        "text_output": "Order validation completed",
        "message": "Invoice monitoring Claro completed successfully", 
        "timestamp": "2025-08-27T10:30:00.000Z",
        "status": "Autorizada Emissão Nota Fiscal"
    }
}
```

### Validation Logic Implementation
```python
def validate_claro_check_response(self, response: dict[str, Any]) -> dict[str, Any]:
    """Comprehensive validation of claroCheck API response"""
    
    validation_result = {
        "is_valid": False,
        "status_transition": "CHECK_ORDER_STATUS",
        "message": "",
        "retry_recommended": False
    }
    
    try:
        # Validate response structure
        if not isinstance(response, dict):
            validation_result["message"] = "Invalid response format"
            return validation_result
            
        output = response.get("output", {})
        if not output:
            validation_result["message"] = "Missing output data"
            return validation_result
        
        # Check API success status
        api_success = output.get("success", False)
        if not api_success:
            validation_result["message"] = f"API reported failure: {output.get('text_output', 'Unknown error')}"
            validation_result["retry_recommended"] = True
            return validation_result
        
        # Extract and validate status field
        status_value = output.get("status", "").strip()
        if not status_value:
            validation_result["message"] = "Missing status field in response"
            validation_result["retry_recommended"] = True
            return validation_result
        
        # Status transition mapping
        status_transitions = {
            "Aguardando Liberação": {
                "new_status": "CHECK_ORDER_STATUS",
                "message": "Order awaiting liberation - will retry in next cycle",
                "retry": True
            },
            "Agendamento Pendente": {
                "new_status": "WAITING_MONITORING", 
                "message": "Order ready for monitoring phase",
                "retry": False
            },
            "Autorizada Emissão Nota Fiscal": {
                "new_status": "MONITORED",
                "message": "Order authorized - proceeding directly to download",
                "retry": False
            }
        }
        
        if status_value in status_transitions:
            transition = status_transitions[status_value]
            validation_result.update({
                "is_valid": True,
                "status_transition": transition["new_status"],
                "message": transition["message"],
                "retry_recommended": transition["retry"]
            })
        else:
            # Unknown status - log warning and default to monitoring
            logger.warning(f"Unknown claroCheck status '{status_value}' - defaulting to WAITING_MONITORING")
            validation_result.update({
                "is_valid": True,
                "status_transition": "WAITING_MONITORING",
                "message": f"Unknown status '{status_value}' - defaulting to monitoring phase",
                "retry_recommended": False
            })
        
        return validation_result
        
    except Exception as e:
        validation_result["message"] = f"Response validation error: {str(e)}"
        validation_result["retry_recommended"] = True
        return validation_result
```

## 7. ERROR HANDLING & RECOVERY

### Validation Failure Scenarios
```python
class ValidationError(ProcessamentoFaturasError):
    """Specific error for claroCheck validation failures"""
    pass

# Error handling patterns
async def handle_claro_check_failure(self, po_number: str, error_details: dict) -> dict:
    """Handle claroCheck validation failures with appropriate recovery strategy"""
    
    failure_type = error_details.get("failure_type", "unknown")
    error_message = error_details.get("error", "No error details")
    
    recovery_strategies = {
        "http_failure": {
            "action": "retry_next_cycle",
            "status": "CHECK_ORDER_STATUS",
            "message": f"HTTP failure - will retry: {error_message}"
        },
        "validation_failure": {
            "action": "retry_next_cycle", 
            "status": "CHECK_ORDER_STATUS",
            "message": f"Validation failed - will retry: {error_message}"
        },
        "timeout_error": {
            "action": "retry_with_delay",
            "status": "CHECK_ORDER_STATUS", 
            "message": f"Timeout occurred - will retry with delay: {error_message}"
        },
        "unknown_status": {
            "action": "proceed_with_caution",
            "status": "WAITING_MONITORING",
            "message": f"Unknown status received - proceeding to monitoring: {error_message}"
        }
    }
    
    strategy = recovery_strategies.get(failure_type, recovery_strategies["validation_failure"])
    
    logger.warning(f"🔄 Recovery strategy for PO {po_number}: {strategy['action']}")
    return strategy
```

### Retry Logic Enhancement
```python
async def execute_claro_check_with_retry(self, po_number: str, max_retries: int = 3) -> dict:
    """Execute claroCheck with exponential backoff retry logic"""
    
    for attempt in range(max_retries):
        try:
            payload = self.build_claro_check_payload(po_number)
            api_response = await self.execute_api_call("claroCheck", payload)
            
            # Validate response
            validation_result = self.validate_claro_check_response(api_response.get("api_result", {}))
            
            if validation_result["is_valid"]:
                return {
                    "success": True,
                    "attempt": attempt + 1,
                    "status_transition": validation_result["status_transition"],
                    "message": validation_result["message"],
                    "api_response": api_response
                }
            elif not validation_result["retry_recommended"]:
                # Don't retry if not recommended
                return {
                    "success": False,
                    "attempt": attempt + 1,
                    "error": validation_result["message"],
                    "final_attempt": True
                }
            
        except Exception as e:
            logger.warning(f"⚠️ claroCheck attempt {attempt + 1} failed for PO {po_number}: {e}")
            
            if attempt < max_retries - 1:
                # Wait before retry (exponential backoff)
                wait_time = (2 ** attempt) * 5  # 5, 10, 20 seconds
                logger.info(f"⏳ Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
            
    # All attempts failed
    return {
        "success": False,
        "attempt": max_retries,
        "error": f"All {max_retries} attempts failed",
        "final_attempt": True
    }
```

## 8. TEST-DRIVEN DEVELOPMENT STRATEGY

### Red-Green-Refactor Integration

#### Red Phase - Failing Tests
```python
import pytest
from unittest.mock import AsyncMock, patch

class TestClaroCheckIntegration:
    """Test suite for claroCheck validation integration"""
    
    @pytest.mark.asyncio
    async def test_claro_check_payload_construction(self):
        """Test claroCheck payload is built correctly"""
        client = BrowserAPIClient()
        payload = client.build_claro_check_payload("600687310")
        
        expected = {
            "flow_name": "claroCheck",
            "parameters": {
                "orders": ["600687310"],
                "headless": True
            }
        }
        assert payload == expected
    
    @pytest.mark.asyncio
    async def test_claro_check_response_parsing_awaiting_liberation(self):
        """Test parsing of 'Aguardando Liberação' response"""
        client = BrowserAPIClient()
        
        mock_response = {
            "api_result": {
                "output": {
                    "success": True,
                    "status": "Aguardando Liberação",
                    "text_output": "Order awaiting liberation"
                }
            }
        }
        
        success, new_status, message = client.parse_claro_check_response(mock_response)
        
        assert success == True
        assert new_status == "CHECK_ORDER_STATUS"
        assert "awaiting liberation" in message.lower()
    
    @pytest.mark.asyncio 
    async def test_claro_check_response_parsing_authorized(self):
        """Test parsing of 'Autorizada Emissão Nota Fiscal' response"""
        client = BrowserAPIClient()
        
        mock_response = {
            "api_result": {
                "output": {
                    "success": True,
                    "status": "Autorizada Emissão Nota Fiscal", 
                    "text_output": "Order authorized"
                }
            }
        }
        
        success, new_status, message = client.parse_claro_check_response(mock_response)
        
        assert success == True
        assert new_status == "MONITORED"
        assert "authorized" in message.lower()
    
    @pytest.mark.asyncio
    async def test_processing_status_enum_updated(self):
        """Test that ProcessingStatus enum includes new statuses"""
        assert ProcessingStatus.CHECK_ORDER_STATUS.value == "check_order_status"
        assert ProcessingStatus.FAILED_VALIDATION.value == "failed_validation"
    
    @pytest.mark.asyncio
    async def test_json_analysis_categorizes_validation_pos(self):
        """Test JSON analysis properly categorizes CHECK_ORDER_STATUS POs"""
        # This test would mock JSON data with CHECK_ORDER_STATUS orders
        # and verify they're categorized in validation_pos
        pass
    
    @pytest.mark.asyncio
    async def test_individual_processing_handles_claro_check(self):
        """Test individual processing handles claroCheck queue"""
        # Mock API responses and verify status transitions
        pass
```

#### Green Phase - Minimal Implementation
1. Add new enum values to ProcessingStatus
2. Implement basic build_claro_check_payload method
3. Implement basic parse_claro_check_response method
4. Add validation_pos category to analysis results
5. Add claroCheck queue to routing logic
6. Implement basic claroCheck processing in individual step

#### Refactor Phase - Quality Improvements
1. Extract validation logic into separate class
2. Add comprehensive error handling
3. Implement retry mechanisms with exponential backoff
4. Add detailed logging and metrics
5. Optimize payload construction
6. Add response caching if beneficial

### Test Categories

#### Unit Tests
- **Payload Construction**: Test build_claro_check_payload with various inputs
- **Response Parsing**: Test parse_claro_check_response with all status variations
- **Validation Logic**: Test validate_claro_check_response error handling
- **Status Transitions**: Test all possible status flows
- **Error Handling**: Test failure scenarios and recovery strategies

#### Integration Tests
- **API Client Integration**: Test actual claroCheck API calls (mocked)
- **Workflow Integration**: Test end-to-end workflow with claroCheck step
- **JSON File Updates**: Test status updates are persisted correctly
- **Queue Processing**: Test claroCheck queue processes correctly

#### End-to-End Tests
- **Complete Flow**: Test PENDING → CHECK_ORDER_STATUS → WAITING_MONITORING/MONITORED
- **Multiple POs**: Test batch processing with mixed validation results
- **Error Recovery**: Test failure scenarios don't break workflow
- **Status Persistence**: Test status updates survive workflow restarts

## 9. IMPLEMENTATION PHASES

### Phase 1: Core Status Integration (Week 1)
**Deliverables**:
- Add CHECK_ORDER_STATUS and FAILED_VALIDATION to ProcessingStatus enum
- Update JSON analysis step to categorize validation_pos
- Add order_validation_queue to routing logic
- Basic claroCheck processing in individual step
- Unit tests for new enum values and basic categorization

### Phase 2: API Client Enhancement (Week 1-2)
**Deliverables**:
- Implement build_claro_check_payload method
- Implement parse_claro_check_response method  
- Add validate_claro_check_response method
- Integration tests for payload construction and response parsing
- Error handling for malformed responses

### Phase 3: Workflow Integration (Week 2)
**Deliverables**:
- Complete individual_po_processing enhancement for claroCheck
- Status transition logic based on validation results
- JSON file update integration
- End-to-end tests for complete status flow
- Documentation updates

### Phase 4: Error Handling & Optimization (Week 2-3)
**Deliverables**:
- Comprehensive error handling and recovery strategies
- Retry logic with exponential backoff
- Detailed logging and metrics collection
- Performance optimization for individual processing
- Complete test suite with high coverage

### Phase 5: Production Deployment & Monitoring (Week 3)
**Deliverables**:
- Production configuration and deployment
- Monitoring and alerting integration
- Performance benchmarking and optimization
- Documentation for operational procedures
- User training and rollout plan

## 10. EDGE CASES & ERROR HANDLING

### Boundary Conditions
- **Empty Response**: Handle cases where claroCheck returns no output data
- **Malformed JSON**: Gracefully handle corrupted API responses
- **Timeout Scenarios**: Handle API timeouts without failing entire batch
- **Unknown Status Values**: Default to safe fallback status for unknown responses
- **Network Failures**: Retry with exponential backoff for connection issues

### Error Scenarios
- **API Unavailable**: Skip validation and proceed to monitoring with warning
- **Invalid PO Numbers**: Log error and mark PO as FAILED_VALIDATION
- **Rate Limiting**: Implement proper backoff and respect API limits
- **Authentication Failures**: Handle auth errors gracefully with retry
- **Partial Batch Failures**: Process successful validations while handling failures

### Recovery Strategies
```python
recovery_strategies = {
    "api_unavailable": {
        "action": "bypass_validation",
        "fallback_status": "WAITING_MONITORING",
        "notify": True
    },
    "rate_limited": {
        "action": "exponential_backoff",
        "max_wait": 300,  # 5 minutes
        "notify": False
    },
    "validation_timeout": {
        "action": "retry_next_cycle", 
        "status": "CHECK_ORDER_STATUS",
        "notify": True
    },
    "unknown_response": {
        "action": "proceed_with_caution",
        "fallback_status": "WAITING_MONITORING", 
        "notify": True
    }
}
```

## 11. ACCEPTANCE CRITERIA

### Definition of Done
- [ ] **Status Flow Updated**: ProcessingStatus enum includes CHECK_ORDER_STATUS and FAILED_VALIDATION
- [ ] **API Integration Complete**: BrowserAPIClient handles claroCheck flow with proper payload construction
- [ ] **Response Validation**: All three status responses properly parsed and mapped to correct transitions
- [ ] **Workflow Integration**: JSON analysis, routing, and individual processing handle validation queue
- [ ] **Error Handling**: Comprehensive error handling with retry logic and recovery strategies
- [ ] **Testing Complete**: Unit, integration, and end-to-end tests with >90% coverage
- [ ] **Documentation Updated**: Technical documentation and operational procedures complete
- [ ] **Backward Compatibility**: Existing functionality unchanged and working correctly

### Validation Steps
1. **Unit Testing**: All individual components tested in isolation with mocked dependencies
2. **Integration Testing**: API client integration tested with mock claroCheck responses
3. **Workflow Testing**: Complete workflow tested with various PO status combinations
4. **Error Scenario Testing**: All error scenarios tested with appropriate recovery verified
5. **Performance Testing**: Validation step adds <10% to total daily execution time
6. **Production Testing**: Staged rollout with monitoring and rollback capability

### Quality Gates
- **Code Coverage**: >90% test coverage for all new code
- **Performance**: No significant impact on existing workflow performance
- **Reliability**: <1% failure rate for validation step in production
- **Compatibility**: Zero breaking changes to existing API contracts
- **Documentation**: Complete technical and operational documentation
- **Monitoring**: Comprehensive logging and metrics for observability

## 12. CONFIGURATION UPDATES

### Environment Variables
```env
# ClaroCheck API Configuration
CLARO_CHECK_ENABLED=true
CLARO_CHECK_TIMEOUT=60
CLARO_CHECK_MAX_RETRIES=3
CLARO_CHECK_RETRY_DELAY=5
CLARO_CHECK_BATCH_SIZE=1

# Validation Behavior
VALIDATION_BYPASS_ON_FAILURE=false
VALIDATION_LOG_LEVEL=INFO
VALIDATION_NOTIFICATION_ENABLED=true
```

### YAML Configuration
```yaml
# ai/workflows/processamento-faturas/config.yaml
version: "1.2.0"  # Bump version for claroCheck integration

claroCheck:
  enabled: true
  processing_mode: "individual"  # Always process one PO at a time
  timeout_seconds: 60
  max_retries: 3
  retry_delay_seconds: 5
  
  # Status transition mapping
  status_transitions:
    "Aguardando Liberação": "CHECK_ORDER_STATUS"
    "Agendamento Pendente": "WAITING_MONITORING" 
    "Autorizada Emissão Nota Fiscal": "MONITORED"
    
  # Error handling
  error_handling:
    bypass_on_api_failure: false
    fallback_status: "WAITING_MONITORING"
    notify_on_failure: true
    
  # Performance settings
  performance:
    parallel_processing: false  # Always sequential for validation
    batch_delay_ms: 1000       # Delay between individual validations
```

This technical specification provides a comprehensive roadmap for integrating the claroCheck validation route into the existing processamento-faturas workflow while maintaining compatibility, reliability, and performance standards.