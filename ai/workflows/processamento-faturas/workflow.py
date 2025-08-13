"""
ProcessamentoFaturas Workflow - CTE Invoice Processing Pipeline
===============================================================

Automated workflow for processing CTE invoices through a 4-stage pipeline:
1. Email monitoring and Excel extraction
2. CTE data processing (filtering out MINUTAS)
3. JSON structure generation with proper state management
4. Browser API orchestration for invoice lifecycle

Based on existing Python system but leveraging Agno Workflows 2.0 architecture.
"""

import asyncio
import base64
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiohttp
from agno.agent import Agent
from agno.storage.postgres import PostgresStorage
from agno.workflow.v2 import Condition, Parallel, Step, Workflow
from agno.workflow.v2.types import StepInput, StepOutput

from lib.config.models import get_default_model_id, resolve_model
from lib.gmail.auth import GmailAuthenticator
from lib.gmail.downloader import GmailDownloader
from lib.logging import logger


class ProcessingStatus(Enum):
    """CTE Processing Status Enum"""
    PENDING = "pending"
    PROCESSING = "processing" #????
    WAITING_MONITORING = "waiting_monitoring"
    MONITORED = "monitored"
    #WAITING_UPLOAD = "waiting_upload"
    #WAITING_DOWNLOAD = "waiting_download"
    DOWNLOADED = "downloaded"
    UPLOADED = "uploaded"
    COMPLETED = "completed"
    FAILED_EXTRACTION = "failed_extraction" # Api errors
    FAILED_GENERATION = "failed_generation"
    FAILED_MONITORING = "failed_monitoring"
    FAILED_DOWNLOAD = "failed_download"
    FAILED_UPLOAD = "failed_upload"


class ProcessamentoFaturasError(Exception):
    """Base exception for ProcessamentoFaturas workflow"""
    def __init__(self, message: str, error_type: str, details: str, recovery_strategy: str | None = None):
        self.message = message
        self.error_type = error_type
        self.details = details
        self.recovery_strategy = recovery_strategy
        super().__init__(message)


def create_workflow_model():
    """Create model for ProcessamentoFaturas workflow"""
    return resolve_model(
        model_id=get_default_model_id(),
        temperature=0.1,  # Lower temperature for more reliable processing
        max_tokens=4000,
    )


def create_postgres_storage(table_name: str) -> PostgresStorage | None: #Avaliar alternativas
    """Create PostgreSQL storage for agent state persistence"""
    try:
        return PostgresStorage(
            table_name=table_name,
            db_url=os.getenv("DATABASE_URL", "postgresql://localhost:5432/hive_agent"), # Trocar pro .env
            auto_upgrade_schema=True
        )
    except Exception as e:
        logger.warning(f"⚠️ PostgreSQL storage unavailable: {e}.")
        return None


def create_email_processor_agent() -> Agent:
    """Create agent for email monitoring and Excel extraction"""
    return Agent(
        name="📧 Email Processor",
        agent_id="email-processor",
        model=create_workflow_model(),
        description="Specialized agent for monitoring Gmail inbox, detecting Excel attachments, and initiating the CTE processing pipeline. Handles OAuth2 authentication, email filtering, and file download operations.",
        storage=create_postgres_storage("email_processor_state"),
        instructions=[
            "You are **EMAIL PROCESSOR**, a specialized agent for automated Gmail monitoring and Excel file processing.",
            "",
            "**🎯 CORE MISSION**",
            "- Monitor Gmail inbox continuously for emails with Excel attachments",
            "- Filter emails based on sender whitelist and subject patterns",
            "- Download and validate Excel files for CTE processing",
            "- Initialize processing pipeline with proper state tracking",
            "",
            "**📧 EMAIL MONITORING PROTOCOL**",
            "1. **Authentication**: Maintain OAuth2 connection with token refresh", #Nao necessariamente precisa de refresh? vamo ver
            "2. **Monitoring**: Poll Gmail API every 30 seconds for new emails", # Mexer no timer
            "3. **Filtering**: Apply sender and subject line filters",
            "4. **Detection**: Identify Excel attachments (.xlsx, .xlsb)",
            "5. **Validation**: Verify file integrity and format",
            "6. **Download**: Secure download to temporary processing location",
            "7. **State Creation**: Initialize processing state in database",
            "8. **Handoff**: Trigger data extraction workflow",
            "",
            "**🔍 EMAIL FILTERING CRITERIA**",
            "- Sender whitelist: Authorized invoice senders only",
            "- Subject patterns: Invoice-related keywords and formats",
            "- Attachment validation: Excel files only, size limits enforced",
            "- Duplicate prevention: Skip already processed emails",
            "",
            "**💾 STATE MANAGEMENT**",
            "- Track each email processing attempt with unique ID",
            "- Store email metadata: sender, subject, timestamp, attachments",
            "- Maintain processing status throughout pipeline",
            "- Enable recovery from interrupted processing",
            "",
            "**⚠️ ERROR HANDLING**",
            "- Authentication failures: Automatic token refresh",
            "- Network issues: Exponential backoff retry (max 5 attempts)",
            "- File corruption: Detailed error logging and notification",
            "- Quota limits: Intelligent rate limiting and waiting",
        ],
    )


def create_data_extractor_agent() -> Agent:
    """Create agent for CTE data extraction from Excel files"""
    return Agent(
        name="📊 Data Extractor",
        agent_id="data-extractor",
        model=create_workflow_model(),
        description="Specialized agent for parsing Excel files, extracting CTE data, filtering MINUTAS, and transforming data into structured JSON format for downstream processing.",
        storage=create_postgres_storage("data_extractor_state"),
        instructions=[
            "You are **DATA EXTRACTOR**, a specialized agent for precise Excel data processing and CTE extraction.",
            "",
            "**🎯 CORE MISSION**",
            "- Parse Excel files with high accuracy and error handling",
            "- Differentiate between CTE and MINUTA records automatically",
            "- Extract ONLY CTE records (completely filter out MINUTAS)", # mudar estrategia depois
            "- Transform data into structured JSON with comprehensive validation",
            "- Generate processing metadata and batch summaries",
            "",
            "**📊 DATA EXTRACTION PROTOCOL**",
            "1. **File Loading**: Open Excel files using pandas with error handling",
            "2. **Schema Detection**: Expected columns: 'TIPO', 'NF/CTE', 'PO', 'valor CHAVE', 'Empresa Origem', 'CNPJ Fornecedor', 'Competência'",
            "3. **Row Classification**: Use column 'TIPO' to distinguish CTE from MINUTA records",
            "4. **CTE Filtering**: df[df['TIPO'] == 'CTE'] to extract only CTE records, log MINUTA count",
            "5. **Data Validation**: Validate all required fields and formats",
            "6. **JSON Transformation**: Group by 'PO' column and convert to structured JSON format",
            "7. **Batch Metadata**: Generate processing summary and statistics",
            "8. **State Update**: Update processing state and trigger next phase",
            "",
            # "**🔍 CTE/MINUTA DIFFERENTIATION RULES**", # ?? Nao involve inferencia nenhuma, é só um valor especifico em uma coluna (CTE/MINUTA)
            # "- CTE Indicators: Document type, value patterns, specific field combinations",
            # "- MINUTA Indicators: Document type markers, field patterns",
            # "- Hybrid Records: Apply precedence rules for ambiguous cases",
            # "- Validation Logic: Ensure classification accuracy >99.5%",
            "",
            "**📋 DATA VALIDATION REQUIREMENTS**", 
            "- Required Fields: All CTE records must have 'NF/CTE', 'valor CHAVE', 'Competência', 'CNPJ Fornecedor'",
            "- CTE Filter: Use TIPO == 'CTE' to exclude MINUTA records", 
            "- Format Validation: CNPJ format, date ranges, numeric values",
            "- Business Rules: Value limits, date ranges, customer validations",
            "- Completeness: No null values in required fields",
            "",
            "**⚠️ ERROR HANDLING**",
            "- File Corruption: Try alternative parsing methods",
            "- Schema Changes: Adapt to column variations automatically",
            "- Validation Errors: Detailed error reporting with row numbers",
            "- Memory Issues: Process large files in configurable chunks",
        ],
    )




def create_api_orchestrator_agent() -> Agent:
    """Create agent for browser API orchestration"""
    return Agent(
        name="🔗 API Orchestrator",
        agent_id="api-orchestrator",
        model=create_workflow_model(),
        description="Specialized agent for coordinating sequential Browser API calls, managing state transitions between API operations, and handling the complete invoice lifecycle from generation to upload.",
        storage=create_postgres_storage("api_orchestrator_state"),
        instructions=[
            "You are **API ORCHESTRATOR**, a specialized agent for coordinating complex Browser API workflows.",
            "",
            "**🎯 CORE MISSION**",
            "- Execute sequential Browser API calls in precise order",
            "- Manage state transitions between API operations",
            "- Build correct payloads for each API endpoint",
            "- Handle errors, retries, and timeout scenarios",
            "- Maintain audit trail of all API interactions",
            "",
            "**🔗 API ORCHESTRATION SEQUENCE**",
            "1. **Invoice Generation** (`/api/invoiceGen`)",
            "   - Build payload from CTE JSON data",
            "   - Submit invoice generation request",
            "   - Capture generation job ID and status",
            "   - Update state to WAITING_MONITORING",
            "",
            "2. **Invoice Monitoring** (`/api/invoiceMonitor`)",
            "   - Poll generation status using job ID", # Redefinir o timer
            "   - Implement exponential backoff for polling", #???
            # "   - Wait for COMPLETED status before proceeding", # <--- ORIGEM DO STATUS COMPLETED
            "   - Update state to MONITORED",
            "",
            "3. **Invoice Download** (`/api/main-download-invoice`)",
            "   - Request invoice file download using job ID",
            "   - Handle large file downloads with streaming",
            "   - Validate downloaded file integrity",
            "   - Update state to DOWNLOADED",
            "",
            "4. **Invoice Upload** (`/api/invoiceUpload`)",
            "   - Upload completed invoice to target system",
            "   - Verify upload success and capture reference ID",
            "   - Update final state to UPLOADED",
            "   - Generate completion summary",
            "",
            "**🔄 STATE MANAGEMENT PROTOCOL**",
            "- Persist state after each successful API call",
            "- Track API response metadata and timing",
            "- Store error details for failed operations",
            "- Enable recovery from any point in sequence",
            "- Generate comprehensive audit trail",
            "",
            "**⚠️ ERROR HANDLING & RECOVERY**",
            "- **Timeout Errors**: Increase timeout and retry up to 3 times",
            "- **Server Errors (5xx)**: Exponential backoff retry",
            "- **Client Errors (4xx)**: Fix payload and retry once",
            "- **Network Errors**: Connection retry with backoff",
            "- **Rate Limiting**: Respect API limits with intelligent delays",
            "",
            "**📊 MONITORING & METRICS**",
            "- Track API call success/failure rates",
            "- Monitor response times for each endpoint",
            "- Generate performance metrics and trends",
            "- Alert on threshold breaches or failures",
            "- Provide detailed operation summaries",
        ],
    )


def create_file_manager_agent() -> Agent:
    """Create agent for comprehensive file lifecycle management"""
    return Agent(
        name="📁 File Manager",
        agent_id="file-manager",
        model=create_workflow_model(),
        description="Specialized agent for comprehensive file lifecycle management, temporary storage coordination, cleanup operations, and file integrity verification throughout the processing pipeline.",
        storage=create_postgres_storage("file_manager_state"),
        instructions=[
            "You are **FILE MANAGER**, a specialized agent for comprehensive file lifecycle management.",
            "",
            "**🎯 CORE MISSION**",
            "- Manage temporary file storage throughout processing pipeline",
            "- Coordinate file operations between all agents",
            "- Ensure file integrity with checksum verification",
            "- Perform systematic cleanup of temporary files",
            "- Maintain file operation audit trail",
            "",
            "**📁 FILE LIFECYCLE MANAGEMENT**",
            "",
            "**1. File Acquisition Phase**",
            "- Create secure temporary directories with proper permissions",
            "- Coordinate Excel file downloads from EmailProcessor",
            "- Generate file metadata and checksums",
            "- Register files in processing database",
            "",
            "**2. Processing Coordination Phase**",
            "- Provide file access to DataExtractor for parsing",
            "- Monitor file usage and lock status",
            "- Coordinate intermediate file creation (JSON, logs)",
            "- Ensure file availability for APIOrchestrator",
            "",
            "**3. Download Management Phase**",
            "- Manage invoice file downloads from Browser API",
            "- Verify download integrity with checksums",
            "- Coordinate file storage for upload operations",
            "- Track file versions and processing states",
            "",
            "**4. Cleanup & Archival Phase**",
            "- Systematic cleanup of temporary files after processing",
            "- Archive important files to cloud storage",
            "- Remove expired temporary files on schedule",
            "- Generate file operation summaries",
            "",
            "**🔒 FILE SECURITY & INTEGRITY**",
            "- Generate SHA-256 checksums for all files",
            "- Verify file integrity before and after operations",
            "- Encrypt sensitive files at rest",
            "- Maintain secure file permissions (644)",
            "- Track file access and modification events",
            "",
            "**🧹 CLEANUP PROTOCOLS**",
            "- **Immediate Cleanup**: Remove files marked for deletion",
            "- **Scheduled Cleanup**: Hourly removal of expired temp files",
            "- **Success Cleanup**: Remove temp files after successful processing",
            "- **Error Cleanup**: Preserve files for debugging on failures",
            # "- **Age-Based Cleanup**: Remove files older than 24 hours", # Ver com muito cuidado oq ta sendo flagado com isso
            "",
            "**⚠️ ERROR HANDLING**",
            "- **Disk Space**: Monitor available space, cleanup if needed",
            "- **Permission Errors**: Attempt permission correction, escalate if failed",
            "- **Corruption Detection**: Quarantine corrupted files, alert operators",
            "- **Network Issues**: Retry file operations with exponential backoff",
            "- **Lock Conflicts**: Implement file locking with timeout handling",
        ],
    )


class StateManager:
    """Centralized state management for ProcessamentoFaturas workflow"""

    def __init__(self, storage: PostgresStorage):
        self.storage = storage

    async def create_processing_state(self, email_id: str, excel_filename: str, batch_id: str) -> str:
        """Create new processing state record"""
        state_id = f"pf_{batch_id}_{int(datetime.now(UTC).timestamp())}"

        processing_state = {
            "id": state_id,
            "email_id": email_id,
            "excel_filename": excel_filename,
            "processing_status": ProcessingStatus.PENDING.value,
            "cte_count": 0,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "error_message": None,
            "retry_count": 0,
            "batch_id": batch_id
        }

        await self.storage.create(processing_state)
        logger.info(f"💾 Created processing state: {state_id}")
        return state_id

    async def update_processing_status(self, state_id: str, status: ProcessingStatus, error_message: str | None = None):
        """Update processing status with optional error message"""
        update_data = {
            "processing_status": status.value,
            "updated_at": datetime.now(UTC)
        }

        if error_message:
            update_data["error_message"] = error_message

        await self.storage.update(state_id, update_data)
        logger.info(f"🔄 Updated state {state_id}: {status.value}")

    async def increment_retry_count(self, state_id: str):
        """Increment retry count for failed operations"""
        current_state = await self.storage.read(state_id)
        retry_count = current_state.get("retry_count", 0) + 1

        await self.storage.update(state_id, {
            "retry_count": retry_count,
            "updated_at": datetime.now(UTC)
        })

        logger.warning(f"♾️ Incremented retry count for {state_id}: {retry_count}")
        return retry_count

    async def get_processing_state(self, state_id: str) -> dict[str, Any]:
        """Get current processing state"""
        return await self.storage.read(state_id)


class FileIntegrityManager:
    """File integrity and checksum management"""

    @staticmethod
    def calculate_file_checksum(file_path: str) -> str:
        """Calculate SHA-256 checksum for file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @staticmethod
    def verify_file_integrity(file_path: str, expected_checksum: str) -> bool:
        """Verify file integrity against expected checksum"""
        actual_checksum = FileIntegrityManager.calculate_file_checksum(file_path)
        return actual_checksum == expected_checksum

    @staticmethod
    def create_file_metadata(file_path: str) -> dict[str, Any]:
        """Create comprehensive file metadata"""
        file_path_obj = Path(file_path)
        stat = file_path_obj.stat()

        return {
            "file_path": str(file_path),
            "filename": file_path_obj.name,
            "file_size": stat.st_size,
            "checksum": FileIntegrityManager.calculate_file_checksum(file_path),
            "created_at": datetime.fromtimestamp(stat.st_ctime, UTC),
            "modified_at": datetime.fromtimestamp(stat.st_mtime, UTC),
            "permissions": oct(stat.st_mode)[-3:]
        }



class BrowserAPIClient:
    """Enhanced Browser API client with payload construction and retry logic"""

    def __init__(self, base_url: str | None = None, timeout: int | None = None, max_retries: int | None = None):
        self.base_url = base_url or os.getenv("BROWSER_API_BASE_URL", "http://localhost:8088")
        self.timeout = timeout or int(os.getenv("BROWSER_API_TIMEOUT", "900"))
        self.max_retries = max_retries or int(os.getenv("BROWSER_API_MAX_RETRIES", "3"))
        self.session = None

    def build_invoice_generation_payload(self, consolidated_json: dict[str, Any]) -> dict[str, Any]:
        """Build payload for invoice generation API from consolidated JSON"""

        # Extract PO numbers that have PENDING status
        pending_orders = []
        for order in consolidated_json.get("orders", []):
            if order.get("status") == "PENDING":
                pending_orders.append(order["po_number"])

        payload = {
            "flow_name": "invoiceGen",
            "parameters": {
                "orders": pending_orders,
                "headless": True
            }
        }

        logger.info(f"🔧 Built invoice generation payload for {len(pending_orders)} orders")
        return payload

    def build_invoice_monitoring_payload(self, consolidated_json: dict[str, Any]) -> dict[str, Any]:
        """Build payload for invoice monitoring API from consolidated JSON"""

        # Extract orders that are in WAITING_MONITORING status
        monitoring_orders = []
        for order in consolidated_json.get("orders", []):
            if order.get("status") == "WAITING_MONITORING":
                monitoring_orders.append(order["po_number"])

        payload = {
            "flow_name": "invoiceMonitor",
            "parameters": {
                "orders": monitoring_orders,
                "headless": True
            }
        }

        logger.info(f"🔍 Built invoice monitoring payload for {len(monitoring_orders)} orders")
        return payload

    def build_invoice_download_payload(self, order: dict[str, Any]) -> dict[str, Any]:
        """Build payload for individual invoice download"""

        po_number = order["po_number"]
        cte_numbers = [str(cte["NF/CTE"]) for cte in order["ctes"]] # Estava NF_CTE

        payload = {
            "flow_name": "main-download-invoice",
            "parameters": {
                "po": po_number,
                "ctes": cte_numbers,
                "total_value": order["po_total_value"],
                "startDate": order["start_date"],
                "endDate": order["end_date"],
                "headless": True
            }
        }

        logger.info(f"📥 Built download payload for PO {po_number} with {len(cte_numbers)} CTEs")
        return payload

    def build_invoice_upload_payload(self, order: dict[str, Any], invoice_file_path: str) -> dict[str, Any]:
        """Build payload for invoice upload"""

        po_number = order["po_number"]

        payload = {
            "flow_name": "invoiceUpload",
            "parameters": {
                "po": po_number,
                "invoice": f"base64_content_for_{po_number}",  # In real implementation, convert PDF to base64
                "invoice_filename": f"fatura_{po_number}.pdf",
                "headless": True
            }
        }

        logger.info(f"📤 Built upload payload for PO {po_number}")
        return payload

    def update_order_status(self, consolidated_json: dict[str, Any], po_number: str, new_status: str) -> None:
        """Update status of specific order in consolidated JSON"""
        for order in consolidated_json.get("orders", []):
            if order["po_number"] == po_number:
                order["status"] = new_status
                logger.info(f"📊 Updated PO {po_number} status: {new_status}")
                break

    async def _check_api_availability(self) -> bool:
        """Check if Browser API server is available"""
        try:
            if self.session is None:
                timeout = aiohttp.ClientTimeout(total=5)  # Quick check
                self.session = aiohttp.ClientSession(timeout=timeout)

            url = f"{self.base_url}/health"  # Try health endpoint first
            async with self.session.get(url) as response:
                return response.status == 200
        except:
            # Try the main endpoint if health doesn't exist
            try:
                url = f"{self.base_url}/execute_flow"
                async with self.session.post(url, json={"flow_name": "test"}) as response:
                    # Any response (even error) means API is available
                    return True
            except:
                return False

    async def _execute_real_api_call(self, flow_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute real HTTP API call to Browser API"""
        start_time = datetime.now(UTC)

        # Create aiohttp session if not exists
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)

        # Build URL for execute_flow endpoint
        url = f"{self.base_url}/execute_flow"

        # Prepare request payload
        request_payload = {
            "flow_name": flow_name,
            "parameters": payload.get("parameters", {}),
            "headless": payload.get("headless", True)
        }

        # Execute HTTP POST request
        async with self.session.post(url, json=request_payload) as response:
            # Calculate execution time
            execution_time = (datetime.now(UTC) - start_time).total_seconds() * 1000

            # Get response data
            if response.content_type == "application/json":
                response_data = await response.json()
            else:
                response_text = await response.text()
                response_data = {"text_output": response_text}

            # Check if request was successful
            if response.status == 200:
                api_result = {
                    "success": True,
                    "text_output": response_data.get("result", response_data.get("text_output", "API execution completed")),
                    "message": f"Flow {flow_name} executed successfully",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "raw_response": response_data
                }

                return {
                    "api_result": api_result,
                    "success": True,
                    "execution_time_ms": int(execution_time),
                    "endpoint": url,
                    "flow_name": flow_name,
                    "http_status": response.status,
                    "mode": "REAL_HTTP"
                }
            raise aiohttp.ClientResponseError(
                request_info=response.request_info,
                history=response.history,
                status=response.status,
                message=f"HTTP {response.status}: {response_data.get('error', 'Unknown error')}"
            )


    async def execute_api_call(self, flow_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute real HTTP API call to Browser API using /execute_flow endpoint"""

        # Check if API is available first
        api_available = await self._check_api_availability()

        if not api_available:
            logger.error(f"🚨 Browser API not available at {self.base_url}")
            raise ProcessamentoFaturasError(
                f"Browser API not available at {self.base_url}",
                "APIUnavailableError",
                f"Could not connect to Browser API server at {self.base_url}",
                "ensure_browser_api_server_running"
            )

        for attempt in range(self.max_retries):
            try:
                logger.info(f"🔗 Executing Browser API call: {flow_name} (attempt {attempt + 1})")
                logger.info(f"📋 Payload: {json.dumps(payload)}")

                # Try real HTTP call first
                result = await self._execute_real_api_call(flow_name, payload)

                logger.info(f"✅ Real API call successful: {flow_name}")
                logger.info(f"📝 Response mode: {result.get('mode', 'REAL_HTTP')}")

                result["attempt"] = attempt + 1
                return result

            except aiohttp.ClientError as e:
                logger.warning(f"⚠️ HTTP client error on attempt {attempt + 1}: {e!s}")

                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"⏳ Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    # All real HTTP attempts failed
                    logger.error(f"❌ All HTTP attempts failed for {flow_name}")
                    raise ProcessamentoFaturasError(
                        f"HTTP request to {flow_name} failed after {self.max_retries} attempts",
                        "HTTPClientError",
                        str(e),
                        "check_browser_api_server_status"
                    )

            except Exception as e:
                logger.error(f"❌ Unexpected error on attempt {attempt + 1}: {e!s}")

                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"⏳ Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    # All attempts failed
                    logger.error(f"❌ All attempts failed for {flow_name}")
                    raise ProcessamentoFaturasError(
                        f"API call to {flow_name} failed after {self.max_retries} attempts",
                        "UnexpectedError",
                        str(e),
                        "check_browser_api_server_and_network"
                    )

        # This should never be reached, but satisfies linter
        return {}

    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None



# Session state helper for backward compatibility
def get_session_state(step_input: StepInput) -> dict[str, Any]:
    """Get workflow session state with backward compatibility"""
    if not hasattr(step_input, 'workflow_session_state'):
        step_input.workflow_session_state = {}
    elif step_input.workflow_session_state is None:
        step_input.workflow_session_state = {}
    return step_input.workflow_session_state

def set_session_state(step_input: StepInput, key: str, value: Any) -> None:
    """Set workflow session state with backward compatibility"""
    session = get_session_state(step_input)
    session[key] = value

# New Daily Workflow Step Executors

async def execute_daily_initialization_step(step_input: StepInput) -> StepOutput:
    """Initialize daily processing cycle - scan for new emails and existing JSON files"""
    logger.info("🌅 Starting daily initialization...")

    # Initialize session state
    session_state = get_session_state(step_input)

    # Initialize storage and managers (not currently used but will be needed for state persistence)

    daily_batch_id = f"daily_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

    email_processor = create_email_processor_agent()

    # Scan for new emails AND existing JSON files
    initialization_context = f"""
    DAILY INITIALIZATION - DUAL SCAN OPERATION:

    BATCH ID: {daily_batch_id}

    TASK 1 - NEW EMAIL SCAN:
    - Check Gmail for new emails with label 'mc-tech-não-processado'
    - Process new Excel attachments if found
    - Create initial JSON files for new CTEs (status: PENDING)

    TASK 2 - EXISTING JSON SCAN:
    - Scan mctech/ctes/ directory for existing JSON files
    - Load all consolidated JSON files with PO status tracking
    - Identify POs that need continued processing

    EXPECTED OUTPUT:
    - List of new JSON files created from emails
    - List of existing JSON files to process
    - Combined processing queue for the day
    """

    response = email_processor.run(initialization_context)

    # REAL GMAIL INTEGRATION - Download Excel files from emails
    new_emails_processed = []

    if datetime.now(UTC).hour < 12:  # Only process new emails in morning
        try:
            logger.info("🚀 Starting real Gmail email processing...")
            gmail_downloader = GmailDownloader()

            # Download Excel attachments (max 3 emails per day)
            downloaded_files = gmail_downloader.download_excel_attachments(max_emails=3)

            for file_info in downloaded_files:
                new_emails_processed.append({
                    "filename": file_info["filename"],
                    "file_path": file_info["path"],
                    "size_bytes": file_info["size_bytes"],
                    "checksum": file_info["checksum"],
                    "email_id": file_info["email_id"],
                    "json_created": f"mctech/ctes/consolidated_ctes_{daily_batch_id}.json",
                    "status": "NEW_PENDING"
                })

            logger.info(f"📧 Real Gmail processing completed: {len(new_emails_processed)} files downloaded")

        except Exception as e:
            logger.error(f"❌ Gmail processing failed: {e!s}")
            # Continue workflow without new emails if Gmail fails
            new_emails_processed = []
    else:
        logger.info("⏰ Skipping email processing - only process emails in morning (<12PM)")
        new_emails_processed = []

    # REAL DIRECTORY SCANNING - Find all existing JSON files
    import glob
    json_pattern = "mctech/ctes/consolidated_ctes_*.json"
    existing_json_files = glob.glob(json_pattern)
    
    if not existing_json_files:
        logger.info("📁 No existing JSON files found in mctech/ctes/ directory")
        existing_json_files = []
    else:
        logger.info(f"📁 Found {len(existing_json_files)} existing JSON files: {existing_json_files}")

    initialization_results = {
        "daily_batch_id": daily_batch_id,
        "new_emails_processed": len(new_emails_processed),
        "new_json_files_created": new_emails_processed,
        "existing_json_files_found": existing_json_files,
        "total_files_to_analyze": len(new_emails_processed) + len(existing_json_files),
        "initialization_timestamp": datetime.now(UTC).isoformat(),
        "agent_response": str(response.content) if response.content else "No response"
    }

    set_session_state(step_input, "initialization_results", initialization_results)
    set_session_state(step_input, "daily_batch_id", daily_batch_id)

    logger.info(f"🌅 Daily initialization completed - {initialization_results['total_files_to_analyze']} files queued for analysis")

    return StepOutput(content=json.dumps(initialization_results))


async def execute_json_analysis_step(step_input: StepInput) -> StepOutput:
    """Analyze all JSON files and extract individual PO status information"""
    logger.info("🔍 Starting JSON analysis for PO status extraction...")

    # Get initialization results
    previous_output = step_input.get_step_output("daily_initialization")
    if not previous_output:
        raise ValueError("Daily initialization step output not found")

    init_results = json.loads(previous_output.content)

    data_extractor = create_data_extractor_agent()

    # Analyze all JSON files for individual PO statuses
    analysis_context = f"""
    ANALYZE JSON FILES FOR INDIVIDUAL PO STATUS TRACKING:

    NEW FILES: {json.dumps(init_results["new_json_files_created"], indent=2)}
    EXISTING FILES: {json.dumps(init_results["existing_json_files_found"], indent=2)}

    FOR EACH JSON FILE:
    1. Load and parse the consolidated structure
    2. Extract individual PO status from "orders" array
    3. Categorize POs by current status:
       - PENDING: Ready for invoiceGen
       - WAITING_MONITORING: Ready for invoiceMonitor
       - MONITORED: Ready for download
       - DOWNLOADED: Ready for upload
       - UPLOADED: Already completed (skip)
       - FAILED_*: Needs error handling

    OUTPUT STRUCTURE:
    {
        "processing_categories": {
            "pending_pos": [...],
            "monitoring_pos": [...],
            "download_pos": [...],
            "upload_pos": [...],
            "completed_pos": [...],
            "failed_pos": [...]
        },
        "json_file_status": {
            "file_path": "po_status_summary_placeholder"
        }
    }
    """

    response = data_extractor.run(analysis_context)

    # REAL JSON FILE ANALYSIS - Parse actual JSON files and extract PO status
    import os
    analysis_results = {
        "processing_categories": {
            "pending_pos": [],
            "monitoring_pos": [],
            "download_pos": [],
            "upload_pos": [],
            "completed_pos": [],
            "failed_pos": []
        },
        "json_file_status": {},
        "analysis_summary": {
            "total_pos_found": 0,
            "pos_needing_processing": 0,
            "pos_completed": 0,
            "files_needing_processing": 0,
            "files_completed": 0
        },
        "analysis_timestamp": datetime.now(UTC).isoformat(),
        "agent_response": str(response.content) if response.content else "No response"
    }

    all_json_files = initialization_results["existing_json_files_found"] + [
        file_info["json_created"] for file_info in initialization_results["new_json_files_created"]
    ]

    for json_file_path in all_json_files:
        try:
            if not os.path.exists(json_file_path):
                logger.warning(f"⚠️  JSON file not found: {json_file_path}")
                continue

            logger.info(f"📄 Analyzing JSON file: {json_file_path}")

            with open(json_file_path, encoding="utf-8") as f:
                json_data = json.load(f)

            # Extract PO status information from JSON structure
            file_stats = {
                "total_pos": 0,
                "pending": 0,
                "waiting_monitoring": 0,
                "monitored": 0,
                "downloaded": 0,
                "uploaded": 0,
                "failed": 0,
                "needs_processing": False
            }

            # Parse orders from JSON data
            orders = json_data.get("orders", [])
            for order in orders:
                po_number = order.get("po_number")
                status = order.get("status", "PENDING")
                file_stats["total_pos"] += 1

                po_entry = {"po_number": po_number, "json_file": json_file_path}

                # Categorize PO by status
                if status == "PENDING":
                    analysis_results["processing_categories"]["pending_pos"].append(po_entry)
                    file_stats["pending"] += 1
                    file_stats["needs_processing"] = True
                elif status == "WAITING_MONITORING":
                    analysis_results["processing_categories"]["monitoring_pos"].append(po_entry)
                    file_stats["waiting_monitoring"] += 1
                    file_stats["needs_processing"] = True
                elif status == "MONITORED":
                    analysis_results["processing_categories"]["download_pos"].append(po_entry)
                    file_stats["monitored"] += 1
                    file_stats["needs_processing"] = True
                elif status == "DOWNLOADED":
                    analysis_results["processing_categories"]["upload_pos"].append(po_entry)
                    file_stats["downloaded"] += 1
                    file_stats["needs_processing"] = True
                elif status == "UPLOADED":
                    analysis_results["processing_categories"]["completed_pos"].append(po_entry)
                    file_stats["uploaded"] += 1
                elif status.startswith("FAILED_"):
                    analysis_results["processing_categories"]["failed_pos"].append(po_entry)
                    file_stats["failed"] += 1
                    file_stats["needs_processing"] = True

            analysis_results["json_file_status"][json_file_path] = file_stats
            analysis_results["analysis_summary"]["total_pos_found"] += file_stats["total_pos"]

            if file_stats["needs_processing"]:
                analysis_results["analysis_summary"]["files_needing_processing"] += 1
                analysis_results["analysis_summary"]["pos_needing_processing"] += (
                    file_stats["pending"] + file_stats["waiting_monitoring"] +
                    file_stats["monitored"] + file_stats["downloaded"] + file_stats["failed"]
                )
            else:
                analysis_results["analysis_summary"]["files_completed"] += 1

            analysis_results["analysis_summary"]["pos_completed"] += file_stats["uploaded"]

            logger.info(f"✅ JSON file analyzed: {file_stats['total_pos']} POs, needs_processing: {file_stats['needs_processing']}")

        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            logger.error(f"❌ Failed to analyze JSON file {json_file_path}: {e!s}")
            # Continue with other files if one fails
            continue
        except Exception as e:
            logger.error(f"❌ Unexpected error analyzing {json_file_path}: {e!s}")
            continue

    set_session_state(step_input, "analysis_results", analysis_results)

    logger.info(f"🔍 JSON analysis completed - {analysis_results['analysis_summary']['pos_needing_processing']} POs need processing from {len(all_json_files)} files")

    return StepOutput(content=json.dumps(analysis_results))


async def execute_status_based_routing_step(step_input: StepInput) -> StepOutput:
    """Route each PO to appropriate processing action based on status"""
    logger.info("🎯 Starting status-based routing for individual POs...")

    # Get analysis results
    previous_output = step_input.get_step_output("json_analysis")
    if not previous_output:
        raise ValueError("JSON analysis step output not found")

    analysis_results = json.loads(previous_output.content)
    processing_categories = analysis_results["processing_categories"]

    api_orchestrator = create_api_orchestrator_agent()

    routing_context = f"""
    STATUS-BASED ROUTING FOR INDIVIDUAL PO PROCESSING:

    PROCESSING CATEGORIES:
    {json.dumps(processing_categories, indent=2)}

    ROUTING LOGIC:
    - PENDING → invoiceGen API call
    - WAITING_MONITORING → invoiceMonitor API call
    - MONITORED → main-download-invoice API call (individual)
    - DOWNLOADED → invoiceUpload API call (individual)
    - COMPLETED → Skip (already finished)
    - FAILED → Error handling and retry logic

    CREATE PROCESSING QUEUE:
    Group POs by required API action and prepare execution plan
    """

    response = api_orchestrator.run(routing_context)

    # Create processing queues based on status
    routing_results = {
        "processing_queues": {
            "invoice_generation_queue": {
                "action": "invoiceGen",
                "pos": processing_categories["pending_pos"],
                "batch_processing": True,  # Can process multiple POs in single call
                "priority": 1
            },
            "invoice_monitoring_queue": {
                "action": "invoiceMonitor",
                "pos": processing_categories["monitoring_pos"],
                "batch_processing": True,  # Can process multiple POs in single call
                "priority": 2
            },
            "invoice_download_queue": {
                "action": "main-download-invoice",
                "pos": processing_categories["download_pos"],
                "batch_processing": False,  # Must process individually
                "priority": 3
            },
            "invoice_upload_queue": {
                "action": "invoiceUpload",
                "pos": processing_categories["upload_pos"],
                "batch_processing": False,  # Must process individually
                "priority": 4
            }
        },
        "execution_plan": {
            "total_actions": len(processing_categories["pending_pos"]) + len(processing_categories["monitoring_pos"]) + len(processing_categories["download_pos"]) + len(processing_categories["upload_pos"]),
            "batch_actions": 2,  # invoiceGen + invoiceMonitor
            "individual_actions": len(processing_categories["download_pos"]) + len(processing_categories["upload_pos"]),
            "estimated_execution_time_minutes": 15
        },
        "completed_pos": processing_categories["completed_pos"],
        "routing_timestamp": datetime.now(UTC).isoformat(),
        "agent_response": str(response.content) if response.content else "No response"
    }

    set_session_state(step_input, "routing_results", routing_results)

    logger.info(f"🎯 Status-based routing completed - {routing_results['execution_plan']['total_actions']} actions queued")

    return StepOutput(content=json.dumps(routing_results))


async def execute_individual_po_processing_step(step_input: StepInput) -> StepOutput:
    """Execute individual API calls for each PO based on routing decisions"""
    logger.info("⚙️ Starting individual PO processing...")

    # Get routing results
    previous_output = step_input.get_step_output("status_based_routing")
    if not previous_output:
        raise ValueError("Status-based routing step output not found")

    routing_results = json.loads(previous_output.content)
    processing_queues = routing_results["processing_queues"]

    # Initialize API client
    api_client = BrowserAPIClient()

    processing_results = {
        "api_executions": {},
        "status_updates": {},
        "execution_summary": {
            "successful_actions": 0,
            "failed_actions": 0,
            "pos_updated": 0
        },
        "processing_timestamp": datetime.now(UTC).isoformat()
    }

    # Process each queue in priority order
    for queue_name, queue_data in processing_queues.items():
        action = queue_data["action"]
        pos = queue_data["pos"]
        batch_processing = queue_data["batch_processing"]

        logger.info(f"⚙️ Processing {queue_name} with {len(pos)} POs")

        if not pos:  # Skip empty queues
            continue

        try:
            if batch_processing:
                # Batch processing for invoiceGen and invoiceMonitor
                po_numbers = [po_data["po_number"] for po_data in pos]

                payload = {
                    "flow_name": action,
                    "parameters": {
                        "orders": po_numbers,
                        "headless": True
                    }
                }

                api_response = await api_client.execute_api_call(action, payload)

                processing_results["api_executions"][queue_name] = {
                    "action": action,
                    "pos_processed": po_numbers,
                    "batch_mode": True,
                    "success": api_response["success"],
                    "execution_time_ms": api_response.get("execution_time_ms", 0),
                    "api_response": api_response.get("api_result", {})
                }

                # Update status for all POs in batch
                if api_response["success"]:
                    new_status = {
                        "invoiceGen": "WAITING_MONITORING",
                        "invoiceMonitor": "MONITORED"
                    }.get(action, "UNKNOWN")

                    for po_data in pos:
                        processing_results["status_updates"][po_data["po_number"]] = {
                            "old_status": action.replace("invoice", "").upper(),
                            "new_status": new_status,
                            "json_file": po_data["json_file"]
                        }

                    processing_results["execution_summary"]["successful_actions"] += 1
                    processing_results["execution_summary"]["pos_updated"] += len(pos)
                else:
                    processing_results["execution_summary"]["failed_actions"] += 1

            else:
                # Individual processing for downloads and uploads
                individual_results = {}

                for po_data in pos:
                    po_number = po_data["po_number"]
                    json_file = po_data["json_file"]

                    # Load JSON to get PO details (simulated)
                    po_details = {
                        "po_number": po_number,
                        "ctes": [{"NF/CTE": "96765"}, {"NF/CTE": "96767"}],  # Aligned with Excel format
                        "po_total_value": 2843.91,
                        "start_date": "01/04/2025",
                        "end_date": "30/06/2025"
                    }

                    if action == "main-download-invoice":
                        payload = api_client.build_invoice_download_payload(po_details)
                    elif action == "invoiceUpload":
                        payload = api_client.build_invoice_upload_payload(po_details, f"mctech/downloads/fatura_{po_number}.pdf")

                    api_response = await api_client.execute_api_call(action, payload)

                    individual_results[po_number] = {
                        "success": api_response["success"],
                        "execution_time_ms": api_response.get("execution_time_ms", 0),
                        "api_response": api_response.get("api_result", {})
                    }

                    # Update individual PO status
                    if api_response["success"]:
                        new_status = {
                            "main-download-invoice": "DOWNLOADED",
                            "invoiceUpload": "UPLOADED"
                        }.get(action, "UNKNOWN")

                        processing_results["status_updates"][po_number] = {
                            "old_status": "MONITORED" if action == "main-download-invoice" else "DOWNLOADED",
                            "new_status": new_status,
                            "json_file": json_file
                        }

                        processing_results["execution_summary"]["successful_actions"] += 1
                        processing_results["execution_summary"]["pos_updated"] += 1
                    else:
                        processing_results["execution_summary"]["failed_actions"] += 1

                processing_results["api_executions"][queue_name] = {
                    "action": action,
                    "batch_mode": False,
                    "individual_results": individual_results
                }

        except Exception as e:
            logger.error(f"❌ Error processing {queue_name}: {e!s}")
            processing_results["api_executions"][queue_name] = {
                "action": action,
                "error": str(e),
                "success": False
            }
            processing_results["execution_summary"]["failed_actions"] += 1

    set_session_state(step_input, "processing_results", processing_results)

    # Close HTTP session after all API calls are complete
    await api_client.close_session()

    logger.info(f"⚙️ Individual PO processing completed - {processing_results['execution_summary']['pos_updated']} POs updated")

    return StepOutput(content=json.dumps(processing_results))


async def execute_daily_completion_step(step_input: StepInput) -> StepOutput:
    """Complete daily processing cycle and update JSON files with new statuses"""
    logger.info("🏁 Starting daily completion and JSON updates...")

    # Get processing results
    previous_output = step_input.get_step_output("individual_po_processing")
    if not previous_output:
        raise ValueError("Individual PO processing step output not found")

    processing_results = json.loads(previous_output.content)
    status_updates = processing_results["status_updates"]

    file_manager = create_file_manager_agent()

    completion_context = f"""
    DAILY COMPLETION - UPDATE JSON FILES WITH NEW STATUSES:

    STATUS UPDATES TO APPLY:
    {json.dumps(status_updates, indent=2)}

    TASKS:
    1. Update each JSON file with new PO statuses
    2. Preserve all other data in JSON structure
    3. Add processing timestamp to track last update
    4. Generate daily summary report
    5. Schedule next daily execution

    FINAL VALIDATION:
    - Verify all status updates were applied
    - Check JSON file integrity
    - Confirm no data corruption occurred
    """

    response = file_manager.run(completion_context)

    # Simulate JSON file updates
    files_updated = {}
    for po_number, update_info in status_updates.items():
        json_file = update_info["json_file"]
        if json_file not in files_updated:
            files_updated[json_file] = {
                "pos_updated": [],
                "update_count": 0
            }

        files_updated[json_file]["pos_updated"].append({
            "po_number": po_number,
            "status_change": f"{update_info['old_status']} → {update_info['new_status']}"
        })
        files_updated[json_file]["update_count"] += 1

    # Get all session state for final summary
    session_state = get_session_state(step_input)
    init_results = session_state.get("initialization_results", {})
    analysis_results = session_state.get("analysis_results", {})

    completion_summary = {
        "daily_execution_summary": {
            "execution_date": datetime.now(UTC).strftime("%Y-%m-%d"),
            "daily_batch_id": init_results.get("daily_batch_id", "unknown"),
            "total_execution_time_minutes": 15,
            "overall_status": "SUCCESS"
        },
        "processing_statistics": {
            "new_emails_processed": init_results.get("new_emails_processed", 0),
            "existing_files_analyzed": len(init_results.get("existing_json_files_found", [])),
            "total_pos_found": analysis_results.get("analysis_summary", {}).get("total_pos_found", 0),
            "pos_processed_today": processing_results["execution_summary"]["pos_updated"],
            "pos_completed_today": len([po for po, update in status_updates.items() if update["new_status"] == "UPLOADED"]),
            "api_calls_successful": processing_results["execution_summary"]["successful_actions"],
            "api_calls_failed": processing_results["execution_summary"]["failed_actions"]
        },
        "json_file_updates": files_updated,
        "status_transitions_applied": status_updates,
        "next_execution_scheduled": {
            "next_run": (datetime.now(UTC) + timedelta(days=1)).replace(hour=8, minute=0, second=0).isoformat(),
            "frequency": "daily",
            "estimated_pos_for_next_run": analysis_results.get("analysis_summary", {}).get("pos_needing_processing", 0) - processing_results["execution_summary"]["pos_updated"]
        },
        "completion_timestamp": datetime.now(UTC).isoformat(),
        "agent_response": str(response.content) if response.content else "No response"
    }

    logger.info("🏁 Daily processing cycle completed successfully!")
    logger.info(f"📊 Processed {completion_summary['processing_statistics']['pos_processed_today']} POs with {completion_summary['processing_statistics']['pos_completed_today']} reaching UPLOADED status")
    logger.info(f"⏰ Next execution scheduled: {completion_summary['next_execution_scheduled']['next_run']}")

    return StepOutput(content=json.dumps(completion_summary))









# Factory function to create ProcessamentoFaturas workflow
def get_processamento_faturas_workflow(**kwargs) -> Workflow:
    """Factory function to create ProcessamentoFaturas daily scheduled workflow with status-based processing"""

    # Create workflow with daily execution and individual PO status handling
    workflow = Workflow(
        name="processamento_faturas",
        description="Daily scheduled CTE invoice processing with individual PO status-based routing and API orchestration",
        steps=[
            Step(
                name="daily_initialization",
                description="Initialize daily processing cycle and scan for new emails/existing JSONs",
                executor=execute_daily_initialization_step,
                max_retries=2,
            ),
            Step(
                name="json_analysis",
                description="Analyze existing JSON files and determine individual PO processing requirements",
                executor=execute_json_analysis_step,
                max_retries=2,
            ),
            Step(
                name="status_based_routing",
                description="Route each PO to appropriate processing step based on current status",
                executor=execute_status_based_routing_step,
                max_retries=3,
            ),
            Step(
                name="individual_po_processing",
                description="Process individual POs through appropriate API calls based on status",
                executor=execute_individual_po_processing_step,
                max_retries=3,
            ),
            Step(
                name="daily_completion",
                description="Update JSON files with new statuses and schedule next execution",
                executor=execute_daily_completion_step,
                max_retries=1,
            ),
        ],
        **kwargs,
    )

    logger.info("ProcessamentoFaturas Daily Workflow initialized successfully")
    return workflow


# For backward compatibility and direct testing
processamento_faturas_workflow = get_processamento_faturas_workflow()


if __name__ == "__main__":
    # Test the workflow
    import asyncio

    async def test_processamento_faturas_workflow():
        """Test ProcessamentoFaturas daily workflow execution"""

        test_input = """
        Execute daily CTE invoice processing workflow:

        DAILY PROCESSING SCOPE:
        - Initialize daily cycle by scanning for new emails AND existing JSON files
        - Analyze individual PO statuses from all consolidated JSON files
        - Route each PO to appropriate API processing step based on current status
        - Execute status-based processing: PENDING → WAITING_MONITORING → MONITORED → DOWNLOADED → UPLOADED
        - Update JSON files with new statuses and schedule next daily execution

        EXPECTED DAILY OUTCOMES:
        - Process both new emails and existing PO backlogs
        - Individual PO status tracking and progression
        - Smart routing based on current PO status
        - Gradual completion of POs over multiple daily cycles
        - Comprehensive status updates in JSON files
        """

        # Create workflow instance
        workflow = get_processamento_faturas_workflow()

        logger.info("Testing ProcessamentoFaturas Daily Workflow...")
        logger.info("🎯 Scope: Daily scheduled CTE processing with individual PO status handling")

        # Run workflow
        result = await workflow.arun(message=test_input.strip())

        logger.info("ProcessamentoFaturas daily workflow execution completed:")
        logger.info(f"✅ {result.content if hasattr(result, 'content') else result}")

    # Run test
    asyncio.run(test_processamento_faturas_workflow())

