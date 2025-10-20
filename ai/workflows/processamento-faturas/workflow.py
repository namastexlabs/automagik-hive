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
import calendar
import hashlib
import json
import math
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
from dateutil import relativedelta

# Import CTEProcessor for database synchronization
from ai.agents.jack_retrieval.processor import CTEProcessor
from lib.config.models import get_default_model_id, resolve_model
from lib.gmail.auth import GmailAuthenticator
from lib.gmail.downloader import GmailDownloader
from lib.gmail.sender import GmailSender
from lib.logging import logger


def get_headless_setting() -> bool:
    """Get headless setting from environment variable (defaults to True if not set)"""
    return os.getenv("HEADLESS", "true").lower() == "true"


def get_minuta_pipeline_wait_time() -> int:
    """Get wait time (seconds) between MINUTA steps, defaults to 180"""
    try:
        return max(0, int(os.getenv("MINUTA_PIPELINE_WAIT_TIME", "180")))
    except ValueError:
        return 180


class ProcessingStatus(Enum):
    """CTE Processing Status Enum"""
    PENDING = "pending"
    CHECK_ORDER_STATUS = "check_order_status"
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
    FAILED_VALIDATION = "failed_validation"
    FAILED_MONITORING = "failed_monitoring"
    FAILED_DOWNLOAD = "failed_download"
    FAILED_UPLOAD = "failed_upload"
    FAILED_EMAIL = "failed_email"  # Email sending failures


class MinutaProcessingStatus(str, Enum):
    """MINUTA Processing Status Enum"""
    PENDING = "PENDING"
    CHECK_ORDER_STATUS = "CHECK_ORDER_STATUS"  # After minutGen - awaiting claroCheck validation
    CLARO_GENERATED = "CLARO_GENERATED"  # After claroCheck approval
    ESL_GENERATED = "ESL_GENERATED"      # After main-minut-gen (3min wait)
    DOWNLOADED = "DOWNLOADED"            # After main-minut-download
    REGIONAL_DOWNLOADED = "REGIONAL_DOWNLOADED"  # After palmas/aracaju (if applicable)
    CONCATENATED = "CONCATENATED"        # After PDF merge
    UPLOADED = "UPLOADED"                # After invoiceUpload
    COMPLETED = "COMPLETED"              # After email sent
    FAILED_GENERATION = "FAILED_GENERATION"
    FAILED_DOWNLOAD = "FAILED_DOWNLOAD"
    FAILED_REGIONAL = "FAILED_REGIONAL"
    FAILED_CONCATENATION = "FAILED_CONCATENATION"
    FAILED_UPLOAD = "FAILED_UPLOAD"


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
            db_url=os.getenv("HIVE_DATABASE_URL", "postgresql://localhost:5532/hive"), # Trocar pro .env
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
            "2. **Schema Detection**: Expected columns: 'TIPO', 'NF/CTE', 'PO', 'Valor' (or 'valor CHAVE'), 'Empresa Origem', 'CNPJ Fornecedor', 'Competência'",
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
            "- Required Fields: All CTE records must have 'NF/CTE', 'Valor' (or 'valor CHAVE'), 'Competência' (stored as data_original), 'CNPJ Fornecedor'",
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
        self.base_url = base_url or os.getenv("BROWSER_API_BASE_URL")
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
                "headless": get_headless_setting()
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
                "headless": get_headless_setting()
            }
        }

        logger.info(f"🔍 Built invoice monitoring payload for {len(monitoring_orders)} orders")
        return payload

    def build_invoice_download_payload(self, order: dict[str, Any]) -> dict[str, Any]:
        """Build payload for individual invoice download"""
        po_number = order["po_number"]
        cte_numbers = [str(cte["NF/CTE"]) for cte in order["ctes"]]

        payload = {
            "flow_name": "main-download-invoice",
            "parameters": {
                "po": po_number,
                "ctes": cte_numbers,
                "total_value": order["po_total_value"],
                "startDate": order["start_date"],
                "endDate": order["end_date"],
                "headless": get_headless_setting()
            }
        }

        logger.info(f"📥 Built download payload for PO {po_number} with {len(cte_numbers)} CTEs")
        return payload

    def build_claro_check_payload(self, po_number: str) -> dict[str, Any]:
        """Build payload for claroCheck validation"""
        payload = {
            "flow_name": "claroCheck",
            "parameters": {
                "orders": [po_number],
                "headless": get_headless_setting()
            }
        }
        return payload

    def build_invoice_monitor_payload(self, po_number: str) -> dict[str, Any]:
        """Build payload for individual invoiceMonitor"""
        payload = {
            "flow_name": "invoiceMonitor",
            "parameters": {
                "orders": [po_number],
                "headless": get_headless_setting()
            }
        }
        return payload

    def parse_claro_check_response(self, api_response: dict[str, Any]) -> tuple[bool, str, str]:
        """Parse claroCheck response and determine status transition"""
        try:
            # Browser agent business status is at raw_response.output.status
            output_status = api_response.get("raw_response", {}).get("output", {}).get("status", "")

            # Status transition logic - handle empty/None status
            if not output_status.strip():
                return False, "FAILED_VALIDATION", "Empty or missing status from browser agent"
            if output_status == "Aguardando Liberação":
                return True, "CHECK_ORDER_STATUS", "Order still awaiting release"
            if output_status == "Agendamento Pendente":
                return True, "WAITING_MONITORING", "Order ready for monitoring"
            if output_status == "Autorizado Emissão de NF" or output_status == "Autorizada Emissão Nota Fiscal":
                return True, "MONITORED", "Order authorized, ready for download"
            return False, "FAILED_VALIDATION", "Unknown status received"

        except Exception:
            return False, "FAILED_VALIDATION", "Response parsing error"

    def parse_claro_check_response_for_minuta(self, api_response: dict[str, Any]) -> tuple[bool, str, str]:
        """
        Parse claroCheck response for MINUTA workflow with simplified status logic.

        Only transitions to CLARO_GENERATED when order is approved for invoice generation.

        Status Mapping:
        - "Aguardando Liberação" → CHECK_ORDER_STATUS (retry next run)
        - "Agendamento Pendente" → CLARO_GENERATED (approved)
        - "Autorizada Emissão Nota Fiscal" → CLARO_GENERATED (approved)
        - Other/Empty → FAILED_GENERATION

        Returns:
            (success: bool, status: str, message: str)
        """
        try:
            output_status = api_response.get("raw_response", {}).get("output", {}).get("status", "")

            # Handle empty/None status
            if not output_status.strip():
                return False, "FAILED_GENERATION", "Empty or missing status from browser agent"

            # LIBERADO → CLARO_GENERATED (approved for pipeline)
            if output_status in ["Agendamento Pendente", "Autorizado Emissão de NF", "Autorizada Emissão Nota Fiscal"]:
                return True, "CLARO_GENERATED", f"Order approved ({output_status}) - ready for multi-hop pipeline"

            # NÃO LIBERADO → CHECK_ORDER_STATUS (remains, retry next run)
            if output_status == "Aguardando Liberação":
                return True, "CHECK_ORDER_STATUS", "Order still awaiting release - will retry next run"

            # Unknown status
            return False, "FAILED_GENERATION", f"Unknown status received: {output_status}"

        except Exception as e:
            logger.error(f"Error parsing claroCheck response for MINUTA: {e}")
            return False, "FAILED_GENERATION", f"Response parsing error: {str(e)}"

    def parse_invoice_upload_response(self, api_response: dict[str, Any]) -> tuple[bool, str, str]:
        """Extract protocol from invoiceUpload response"""
        try:
            raw_response = api_response.get("raw_response", {})
            browser_output = raw_response.get("output", {})
            protocol = browser_output.get("protocol", "")

            if protocol:
                logger.info(f"📋 Protocol extracted: {protocol}")
                return True, protocol, "Upload successful with protocol"

            logger.warning("⚠️ No protocol found in upload response")
            return False, "", "Upload failed - no protocol"
        except Exception as e:
            logger.error(f"❌ Error parsing upload response: {e}")
            return False, "", f"Response parsing error: {e!s}"

    def process_invoice_zips(self, po_number: str, protocol: str) -> dict:
        """Extract and rename ZIP files with protocol"""
        import glob
        import os
        import shutil
        import zipfile

        # Find downloaded ZIP using multiple patterns
        zip_patterns = [
            f"mctech/downloads/pedido {po_number}.zip",  # Real format from API
            f"mctech/downloads/fatura_{po_number}.zip",  # Fallback format
            f"mctech/downloads/*{po_number}*.zip"       # Wildcard search
        ]

        original_zip = None
        for pattern in zip_patterns:
            if "*" in pattern:
                # Use glob for wildcard patterns
                matches = glob.glob(pattern)
                if matches:
                    original_zip = matches[0]  # Use first match
                    break
            # Direct file check
            elif os.path.exists(pattern):
                original_zip = pattern
                break

        if not original_zip:
            logger.error(f"❌ ZIP file not found for PO {po_number}. Searched patterns: {zip_patterns}")
            return {"attachments": [], "error": "ZIP file not found"}

        logger.info(f"📦 Found ZIP file for PO {po_number}: {original_zip}")

        # Extract to temp directory
        temp_dir = f"mctech/temp/{po_number}"
        os.makedirs(temp_dir, exist_ok=True)

        try:
            with zipfile.ZipFile(original_zip, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            # Create 3 new ZIPs with protocol naming
            attachments = []

            # 1. Fatura ZIP (preserve original filename + add protocol)
            fatura_files = glob.glob(f"{temp_dir}/Fatura/*")
            if fatura_files:
                # Get original fatura filename (without extension)
                original_fatura = os.path.basename(fatura_files[0])
                fatura_name = os.path.splitext(original_fatura)[0]
                fatura_zip = f"mctech/downloads/{fatura_name}_{protocol}.zip"
                self._create_zip(fatura_files, fatura_zip)
                attachments.append(fatura_zip)

            # 2. PDF ZIP
            pdf_files = glob.glob(f"{temp_dir}/PDF/*")
            if pdf_files:
                pdf_zip = f"mctech/downloads/PDF_protocolo_{protocol}.zip"
                self._create_zip(pdf_files, pdf_zip)
                attachments.append(pdf_zip)

            # 3. XML ZIP
            xml_files = glob.glob(f"{temp_dir}/XML/*")
            if xml_files:
                xml_zip = f"mctech/downloads/XML_protocolo_{protocol}.zip"
                self._create_zip(xml_files, xml_zip)
                attachments.append(xml_zip)

            logger.info(f"✅ Created {len(attachments)} ZIP files with protocol {protocol}")
            return {"attachments": attachments}

        except Exception as e:
            logger.error(f"❌ Error processing ZIPs: {e}")
            return {"attachments": [], "error": str(e)}
        finally:
            # Cleanup temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def _create_zip(self, files: list, output_path: str) -> None:
        """Helper to create ZIP from file list"""
        import zipfile
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files:
                zipf.write(file_path, os.path.basename(file_path))

    def build_invoice_upload_payload(self, order: dict[str, Any], invoice_file_path: str) -> dict[str, Any]:
        """Build payload for invoice upload by extracting fatura from ZIP file"""

        po_number = order["po_number"]
        
        # Extract invoice file from downloaded ZIP
        import base64
        import glob
        import os
        import zipfile
        
        invoice_base64 = ""
        actual_filename = f"fatura_{po_number}.pdf"
        file_found = False
        
        # Look for downloaded ZIP files (with actual names from API)
        zip_patterns = [
            f"mctech/downloads/pedido {po_number}.zip",  # Real format from API
            f"mctech/downloads/fatura_{po_number}.zip",  # Fallback format
            f"mctech/downloads/*{po_number}*.zip"       # Wildcard search
        ]
        
        zip_file_path = None
        for pattern in zip_patterns:
            if "*" in pattern:
                # Use glob for wildcard patterns
                matches = glob.glob(pattern)
                if matches:
                    zip_file_path = matches[0]  # Use first match
                    break
            # Direct file check
            elif os.path.exists(pattern):
                zip_file_path = pattern
                break
        
        if zip_file_path:
            logger.info(f"📦 Found ZIP file: {zip_file_path}")
            
            try:
                # Validate ZIP file integrity first
                if not zipfile.is_zipfile(zip_file_path):
                    logger.error(f"❌ File is not a valid ZIP: {zip_file_path}")
                    raise zipfile.BadZipFile(f"Invalid ZIP file: {zip_file_path}")
                
                with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                    # Test ZIP integrity
                    try:
                        zip_ref.testzip()
                        logger.info(f"✅ ZIP integrity validated: {zip_file_path}")
                    except Exception as integrity_error:
                        logger.error(f"❌ ZIP integrity check failed: {integrity_error}")
                        raise zipfile.BadZipFile(f"Corrupted ZIP file: {zip_file_path}")
                    
                    # List all files in ZIP for debugging
                    zip_contents = zip_ref.namelist()
                    logger.info(f"📋 ZIP contents ({len(zip_contents)} files): {zip_contents}")
                    
                    # Validate ZIP structure - must contain Fatura/ folder
                    fatura_folder_found = any(path.startswith("Fatura/") for path in zip_contents)
                    if not fatura_folder_found:
                        logger.error("❌ No 'Fatura/' folder found in ZIP structure")
                        logger.error(f"📋 Available folders: {[path for path in zip_contents if path.endswith('/')]}")
                        raise ValueError("Invalid ZIP structure: missing Fatura/ folder")
                    
                    # Look for invoice files in Fatura/ folder with enhanced validation
                    invoice_candidates = []
                    for file_path in zip_contents:
                        # Check if file is in Fatura/ folder and matches pattern
                        if (file_path.startswith("Fatura/") and
                            "fatura_" in file_path.lower() and
                            not file_path.endswith("/") and
                            file_path.lower().endswith(".pdf")):  # Must be PDF
                            invoice_candidates.append(file_path)
                    
                    if not invoice_candidates:
                        logger.error("❌ No valid fatura_*.pdf files found in Fatura/ folder")
                        fatura_files = [f for f in zip_contents if f.startswith("Fatura/") and not f.endswith("/")]
                        logger.error(f"📋 Files in Fatura/: {fatura_files}")
                        raise FileNotFoundError("No fatura_*.pdf files found in ZIP")
                    
                    # Use the first valid invoice file (or implement selection logic if multiple)
                    invoice_file = invoice_candidates[0]
                    if len(invoice_candidates) > 1:
                        logger.warning(f"⚠️ Multiple invoice files found, using first: {invoice_file}")
                        logger.warning(f"📋 All candidates: {invoice_candidates}")
                    
                    # Extract and validate the invoice file
                    with zip_ref.open(invoice_file) as invoice_data:
                        file_content = invoice_data.read()
                    
                    # Validate file content
                    if len(file_content) == 0:
                        logger.error(f"❌ Invoice file is empty: {invoice_file}")
                        raise ValueError(f"Empty invoice file: {invoice_file}")
                    
                    # Validate PDF header (basic PDF validation)
                    if not file_content.startswith(b"%PDF"):
                        logger.warning(f"⚠️ File does not appear to be a valid PDF: {invoice_file}")
                        logger.warning(f"📄 File header: {file_content[:20]}")
                    
                    invoice_base64 = base64.b64encode(file_content).decode("utf-8")
                    
                    # Extract just the filename (without Fatura/ prefix)
                    actual_filename = os.path.basename(invoice_file)
                    file_found = True
                    
                    logger.info(f"✅ Successfully extracted and validated invoice from ZIP: {invoice_file}")
                    logger.info(f"📄 File size: {len(file_content)} bytes, filename: {actual_filename}")
                    logger.info(f"🔍 Base64 preview: {invoice_base64[:50]}...")
                        
            except zipfile.BadZipFile as e:
                logger.error(f"❌ ZIP file error for {zip_file_path}: {e}")
                raise
            except FileNotFoundError as e:
                logger.error(f"❌ File not found in ZIP {zip_file_path}: {e}")
                raise
            except Exception as e:
                logger.error(f"❌ Unexpected error extracting from ZIP {zip_file_path}: {e}")
                raise
        
        else:
            # Try direct PDF file as fallback
            pdf_path = f"mctech/downloads/fatura_{po_number}.pdf"
            if os.path.exists(pdf_path):
                try:
                    with open(pdf_path, "rb") as f:
                        file_content = f.read()
                    invoice_base64 = base64.b64encode(file_content).decode("utf-8")
                    actual_filename = f"fatura_{po_number}.pdf"
                    file_found = True
                    logger.info(f"📄 Loaded direct PDF file: {pdf_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to read PDF file {pdf_path}: {e}")
        
        if not file_found:
            logger.error(f"❌ No invoice file found for PO {po_number}")
            logger.error("🔍 Checked locations:")
            logger.error(f"   - ZIP: {zip_file_path}")
            logger.error(f"   - PDF: mctech/downloads/fatura_{po_number}.pdf")
            raise FileNotFoundError(f"No invoice file found for PO {po_number}")

        payload = {
            "flow_name": "invoiceUpload",
            "parameters": {
                "po": po_number,
                "invoice": invoice_base64,
                "invoice_filename": actual_filename,
                "headless": get_headless_setting()
            }
        }

        logger.info(f"📤 Built upload payload for PO {po_number} (file: {actual_filename})")
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

            url = f"{self.base_url}/"  # Try root endpoint first
            async with self.session.get(url) as response:
                return response.status == 200
        except:
            # Try the main endpoint if root doesn't exist
            try:
                url = f"{self.base_url}/execute-flow"
                async with self.session.post(url, json={"flow_name": "test"}) as response:
                    # Any response (even error) means API is available
                    return True
            except:
                return False

    async def _execute_real_api_call(self, flow_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute real HTTP API call to Browser API"""
        start_time = datetime.now(UTC)
        
        # Build URL for execute-flow endpoint (early definition for exception handling)
        url = f"{self.base_url}/execute-flow"

        # Create aiohttp session if not exists OR recreate with proper timeout
        if self.session is None or self.session.timeout.total != self.timeout:
            if self.session:
                await self.session.close()
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)

        # Prepare request payload
        request_payload = {
            "flow_name": flow_name,
            "parameters": payload.get("parameters", {}),
            "headless": payload.get("headless", get_headless_setting())
        }

        # Execute HTTP POST request
        try:
            async with self.session.post(url, json=request_payload) as response:
                # Calculate execution time
                execution_time = (datetime.now(UTC) - start_time).total_seconds() * 1000

                # Get response data - Handle both JSON and binary file responses
                if response.content_type == "application/json":
                    response_data = await response.json()
                elif response.content_type in ["application/zip", "application/octet-stream", "application/x-zip-compressed"]:
                    # Handle binary file downloads (main-download-invoice)
                    if flow_name == "main-download-invoice":
                        # Read binary content
                        file_content = await response.read()
                        
                        # Create downloads directory if it doesn't exist
                        download_dir = "mctech/downloads"
                        os.makedirs(download_dir, exist_ok=True)
                        
                        # Extract PO number from payload for filename
                        po_number = payload.get("parameters", {}).get("po", "unknown")
                        
                        # Determine filename from Content-Disposition header or default
                        content_disposition = response.headers.get("content-disposition", "")
                        if "filename=" in content_disposition:
                            # Extract filename from header: filename="pedido 600698258.zip" (with spaces)
                            import re
                            # Improved regex to handle quotes and spaces properly
                            filename_match = re.search(r'filename=["\']?([^"\';]+)["\']?', content_disposition)
                            filename = filename_match.group(1).strip() if filename_match else f"fatura_{po_number}.zip"
                            logger.info(f"📄 API provided filename: '{filename}'")
                        else:
                            filename = f"fatura_{po_number}.zip"
                            logger.info(f"📄 Using default filename: '{filename}'")
                        
                        file_path = os.path.join(download_dir, filename)
                        
                        # Save binary file to disk
                        try:
                            with open(file_path, "wb") as f:
                                f.write(file_content)
                            
                            file_size = len(file_content)
                            logger.info(f"📁 File downloaded successfully: {filename} ({file_size} bytes)")
                            
                            # Verify file was written correctly
                            if os.path.exists(file_path) and os.path.getsize(file_path) == file_size:
                                logger.info(f"✅ File integrity verified: {file_path}")
                                file_download_success = True
                            else:
                                logger.error(f"❌ File integrity check failed: {file_path}")
                                file_download_success = False
                                
                        except Exception as e:
                            logger.error(f"❌ Failed to save file {filename}: {e}")
                            file_download_success = False
                            file_size = 0
                        
                        # Create JSON-compatible response structure for validation logic
                        response_data = {
                            "status": "success" if file_download_success else "error",
                            "flow": flow_name,
                            "output": {
                                "success": file_download_success,
                                "file_downloaded": file_download_success,
                                "file_path": file_path,
                                "filename": filename,
                                "file_size": file_size,
                                "text_output": f"Downloaded {filename} ({file_size} bytes)" if file_download_success else f"Failed to download {filename}",
                                "error": "" if file_download_success else "File download or save failed"
                            }
                        }
                    else:
                        # Binary response for non-download flow (unexpected)
                        logger.error(f"❌ Unexpected binary response for flow {flow_name}")
                        response_data = {
                            "status": "error",
                            "flow": flow_name,
                            "output": {
                                "success": False,
                                "error": f"Unexpected binary response for {flow_name}",
                                "text_output": "Received binary data for non-download flow"
                            }
                        }
                elif response.content_type in ["application/pdf", "application/x-pdf"]:
                    po_number = payload.get("parameters", {}).get("po", "unknown")
                    file_content = await response.read()

                    download_dir = Path("mctech/minutas/downloads")
                    download_dir.mkdir(parents=True, exist_ok=True)

                    content_disposition = response.headers.get("content-disposition", "")
                    filename = None
                    if "filename=" in content_disposition:
                        import re
                        match = re.search(r'filename=["\']?([^"\';]+)["\']?', content_disposition)
                        if match:
                            filename = match.group(1).strip()
                    if not filename:
                        filename = f"minuta_{po_number}.pdf"

                    file_path = download_dir / filename
                    with open(file_path, "wb") as f:
                        f.write(file_content)

                    logger.info("📁 PDF downloaded: {} ({} bytes)", file_path, len(file_content))

                    response_data = {
                        "status": "success",
                        "flow": flow_name,
                        "output": {
                            "success": True,
                            "file_path": str(file_path),
                            "text_output": f"Downloaded {filename}",
                            "error": ""
                        }
                    }
                else:
                    # Text response (fallback)
                    response_text = await response.text(errors="ignore")
                    response_data = {"text_output": response_text}

                # Log response details for debugging
                logger.info(f"📊 HTTP Response: {response.status} {response.reason}")
                logger.info(f"📊 Content-Type: {response.content_type}")
                logger.info(f"⏱️ Execution time: {execution_time:.2f}ms")

                # Check if request was successful
                if response.status == 200:
                    logger.info(f"📡 HTTP call successful for {flow_name}")
                    
                    # Extract Browser API response pattern
                    api_status = response_data.get("status")
                    output_data = response_data.get("output") or {}
                    browser_success = output_data.get("success", False)
                    text_output = output_data.get("text_output", "No output")
                    error_output = output_data.get("error", "")
                    
                    # Check both HTTP success AND browser process success
                    overall_success = (api_status == "success" or api_status is True) and browser_success
                    
                    if overall_success:
                        logger.info(f"✅ Browser process successful for {flow_name}")
                        api_result = {
                            "success": True,
                            "text_output": text_output,
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
                    # HTTP 200 but browser process failed
                    logger.error(f"❌ Browser process failed for {flow_name}")
                    logger.error(f"🔗 API Status: {api_status}")
                    logger.error(f"🔗 Browser Success: {browser_success}")
                    logger.error(f"📄 Browser Output: {text_output}")
                    if error_output:
                        logger.error(f"💥 Browser Error: {error_output}")
                    
                    api_result = {
                        "success": False,
                        "text_output": text_output,
                        "error": error_output or "Browser process failed",
                        "message": f"Flow {flow_name} browser process failed",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "raw_response": response_data
                    }

                    return {
                        "api_result": api_result,
                        "success": False,
                        "execution_time_ms": int(execution_time),
                        "endpoint": url,
                        "flow_name": flow_name,
                        "http_status": response.status,
                        "browser_success": browser_success,
                        "mode": "REAL_HTTP"
                    }
                # Log detailed error information
                logger.error(f"❌ HTTP {response.status} {response.reason} for {flow_name}")
                logger.error(f"🔗 URL: {url}")
                request_payload_str = json.dumps(request_payload, indent=2)
                logger.opt(raw=True).error(f"📋 Request payload: {request_payload_str}\n")
                response_content_str = json.dumps(response_data, indent=2) if response_data else "No content"
                logger.opt(raw=True).error(f"📄 Response content: {response_content_str}\n")
                
                error_message = response_data.get("error", response_data.get("detail", f"HTTP {response.status}"))
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"HTTP {response.status}: {error_message}"
                )
        
        except Exception as e:
            # Handle timeouts and other connection errors
            error_type = type(e).__name__
            import traceback
            traceback_str = traceback.format_exc()
            
            logger.error(f"❌ Connection error: {error_type} - {e!s}")
            logger.error(f"🔗 Failed URL: {url}")
            request_payload_str = json.dumps(request_payload, indent=2)
            logger.opt(raw=True).error(f"📋 Request payload: {request_payload_str}\n")
            logger.error(f"💥 Traceback: {traceback_str}")
            
            # Re-raise the exception to be handled by the retry logic
            raise


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

        failed_url = f"{self.base_url}/execute-flow"

        for attempt in range(self.max_retries):
            try:
                logger.info(f"🔗 Executing Browser API call: {flow_name} (attempt {attempt + 1})")
                payload_str = json.dumps(payload)
                logger.opt(raw=True).info(f"📋 Payload: {payload_str}\n")

                # Try real HTTP call first
                result = await self._execute_real_api_call(flow_name, payload)

                logger.info(f"✅ Real API call successful: {flow_name}")
                logger.info(f"📝 Response mode: {result.get('mode', 'REAL_HTTP')}")

                result["attempt"] = attempt + 1
                return result

            except aiohttp.ClientError as e:
                error_type = type(e).__name__
                logger.warning(f"⚠️ HTTP client error on attempt {attempt + 1}: {error_type} - {e!s}")
                logger.warning(f"🔗 Failed URL: {failed_url}")
                request_payload_str = json.dumps(payload, indent=2)
                logger.opt(raw=True).warning(f"📋 Request payload: {request_payload_str}\n")

                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"⏳ Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    # All real HTTP attempts failed
                    logger.error(f"❌ All HTTP attempts failed for {flow_name}")
                    logger.error(f"❌ Final error type: {error_type}")
                    raise ProcessamentoFaturasError(
                        f"HTTP request to {flow_name} failed after {self.max_retries} attempts",
                        "HTTPClientError",
                        f"{error_type}: {e!s}",
                        "check_browser_api_server_status"
                    )

            except Exception as e:
                error_type = type(e).__name__
                import traceback
                traceback_str = traceback.format_exc()
                
                logger.error(f"❌ Unexpected error on attempt {attempt + 1}: {error_type} - {e!s}")
                logger.error(f"🔗 Failed URL: {failed_url}")
                request_payload_str = json.dumps(payload, indent=2)
                logger.opt(raw=True).error(f"📋 Request payload: {request_payload_str}\n")
                logger.error(f"💥 Traceback: {traceback_str}")

                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"⏳ Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    # All attempts failed
                    logger.error(f"❌ All attempts failed for {flow_name}")
                    logger.error(f"❌ Final error type: {error_type}")
                    raise ProcessamentoFaturasError(
                        f"API call to {flow_name} failed after {self.max_retries} attempts",
                        "UnexpectedError",
                        f"{error_type}: {e!s}",
                        "check_browser_api_server_and_network"
                    )

        # This should never be reached, but satisfies linter
        return {}

    def build_minut_gen_payload(self, cnpj_group: dict[str, Any]) -> dict[str, Any]:
        """Build payload for minutGen - batches POs by same CNPJ for Bahia system"""

        # Extract PO numbers from the CNPJ group
        po_numbers = cnpj_group["po_list"]

        # Extract city from first PO's data (all POs in group share same CNPJ/city)
        city = cnpj_group.get("city", "SALVADOR")  # From ReceitaWS API

        payload = {
            "flow_name": "minutGen",
            "parameters": {
                "orders": po_numbers,
                "city": city,
                "headless": get_headless_setting()
            }
        }

        logger.info(f"🔧 Built minutGen payload for {len(po_numbers)} POs in {city}")
        return payload

    def build_main_minut_gen_payload(self, po_data: dict[str, Any], cnpj_group: dict[str, Any]) -> dict[str, Any]:
        """Build payload for main-minut-gen - ESL System per-PO invoice generation"""

        po_number = po_data["po"]

        # Extract MINUTA numbers for this specific PO from CNPJ group
        minuta_numbers = [
            m["nf_cte"] for m in cnpj_group["minutas"]
            if m["po"] == po_number
        ]

        # Convert to string format for API
        minuta_strings = [str(m) for m in minuta_numbers]

        payload = {
            "flow_name": "main-minut-gen",
            "parameters": {
                "po": po_number,
                "minutes": minuta_strings,
                "total_value": po_data["total_value"],
                "startDate": po_data.get("start_date", "01/06/2025"),
                "endDate": po_data.get("end_date", "30/08/2025"),
                "headless": get_headless_setting()
            }
        }

        logger.info(f"🔧 Built main-minut-gen payload for PO {po_number} with {len(minuta_strings)} MINUTAs")
        return payload

    def build_main_minut_download_payload(self, po_data: dict[str, Any], cnpj: str, cnpj_group: dict[str, Any]) -> dict[str, Any]:
        """Build payload for main-minut-download - ESL System per-PO PDF download"""

        po_number = po_data["po"]

        # Extract MINUTA numbers for this specific PO
        minuta_numbers = [
            m["nf_cte"] for m in cnpj_group["minutas"]
            if m["po"] == po_number
        ]

        # Convert to string format for API
        minuta_strings = [str(m) for m in minuta_numbers]

        # CNPJ should be unformatted (no dots, slashes, hyphens)
        cnpj_clean = cnpj.replace(".", "").replace("/", "").replace("-", "")

        payload = {
            "flow_name": "main-minut-download",
            "parameters": {
                "po": po_number,
                "minutes": minuta_strings,
                "total_value": po_data["total_value"],
                "cnpj": cnpj_clean,
                "headless": get_headless_setting()
            }
        }

        logger.info(f"📥 Built main-minut-download payload for PO {po_number} with CNPJ {cnpj_clean}")
        return payload

    def build_regional_download_payload(self, po_data: dict[str, Any], cnpj: str, cnpj_group: dict[str, Any], region: str) -> dict[str, Any]:
        """Build payload for regional downloads (Palmas/Aracaju)

        Args:
            po_data: PO-specific data including total_value
            cnpj: CNPJ identifier (will be cleaned)
            cnpj_group: Full CNPJ group data with minutas
            region: Either 'palmas' (Tocantins) or 'aracaju' (Sergipe)
        """

        po_number = po_data["po"]

        # Extract MINUTA numbers for this specific PO
        minuta_numbers = [
            m["nf_cte"] for m in cnpj_group["minutas"]
            if m["po"] == po_number
        ]

        # Convert to string format for API
        minuta_strings = [str(m) for m in minuta_numbers]

        # CNPJ should be unformatted
        cnpj_clean = cnpj.replace(".", "").replace("/", "").replace("-", "")

        # Determine flow name based on region
        flow_name = f"main-minut-download-{region}"

        payload = {
            "flow_name": flow_name,
            "parameters": {
                "po": po_number,
                "minutes": minuta_strings,
                "total_value": po_data["total_value"],
                "cnpj": cnpj_clean,
                "headless": get_headless_setting()
            }
        }

        logger.info(f"📥 Built {flow_name} payload for PO {po_number} in region {region.upper()}")
        return payload

    def build_minuta_invoice_upload_payload(self, cnpj_group: dict[str, Any], concatenated_pdf_path: str, po_number: str) -> dict[str, Any]:
        """Build payload for MINUTA invoice upload with concatenated PDF

        Args:
            cnpj_group: Full CNPJ group data with po_list
            concatenated_pdf_path: Path to concatenated PDF file
            po_number: PO associated with the upload

        Returns:
            Payload for invoiceUpload flow

        Note:
            - Uses FIRST PO from CNPJ group's po_list
            - PDF should contain ALL base + regional PDFs concatenated
        """

        cnpj_raw = (
            cnpj_group.get("cnpj")
            or cnpj_group.get("cnpj_claro")
            or cnpj_group.get("cnpj_claro_formatted")
        )

        if not cnpj_raw:
            raise KeyError("cnpj_claro")

        po_temp = cnpj_group.get("_po_temp", {}).get(po_number, {})
        base_filename = po_temp.get("base_pdf_filename")

        # Read and encode PDF file
        with open(concatenated_pdf_path, "rb") as f:
            pdf_content = f.read()
        invoice_base64 = base64.b64encode(pdf_content).decode("utf-8")

        if base_filename:
            invoice_filename = base_filename
        else:
            # Fallback to CNPJ-based filename if base not available
            invoice_filename = f"NFS-e_{po_number}.pdf"

        payload = {
            "flow_name": "invoiceUpload",
            "parameters": {
                "po": po_number,
                "invoice": invoice_base64,
                "invoice_filename": invoice_filename,
                "headless": get_headless_setting()
            }
        }

        logger.info(
            f"📤 Built MINUTA upload payload for PO {po_number} (arquivo: {invoice_filename})"
        )
        return payload

    async def save_pdf_response(self, api_response: dict[str, Any], output_path: str) -> dict[str, Any]:
        """Save binary PDF response from Browser API to file

        Args:
            api_response: API response containing binary PDF data
            output_path: Path where PDF should be saved

        Returns:
            Dictionary with save status and file metadata

        Note:
            Browser API returns PDF as binary content in response body
        """

        try:
            # Extract binary PDF content from API response
            # API returns binary directly in response for download flows
            pdf_content = api_response.get("raw_response", {}).get("content")

            if not pdf_content:
                logger.error("❌ No PDF content found in API response")
                return {
                    "success": False,
                    "error": "No PDF content in response",
                    "output_path": output_path
                }

            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # Write binary PDF to file
            with open(output_path, "wb") as f:
                f.write(pdf_content)

            # Verify file was created
            if not os.path.exists(output_path):
                logger.error(f"❌ Failed to create PDF file: {output_path}")
                return {
                    "success": False,
                    "error": "File not created after write",
                    "output_path": output_path
                }

            file_size = os.path.getsize(output_path)
            logger.info(f"✅ Saved PDF response to {output_path} ({file_size} bytes)")

            return {
                "success": True,
                "output_path": output_path,
                "file_size": file_size,
                "checksum": FileIntegrityManager.calculate_file_checksum(output_path)
            }

        except Exception as e:
            logger.error(f"❌ Error saving PDF response: {e}")
            return {
                "success": False,
                "error": str(e),
                "output_path": output_path
            }

    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None



# Session state helper for backward compatibility
def get_session_state(step_input: StepInput) -> dict[str, Any]:
    """Get workflow session state with backward compatibility"""
    if not hasattr(step_input, "workflow_session_state") or step_input.workflow_session_state is None:
        step_input.workflow_session_state = {}
    return step_input.workflow_session_state

def set_session_state(step_input: StepInput, key: str, value: Any) -> None:
    """Set workflow session state with backward compatibility"""
    session = get_session_state(step_input)
    session[key] = value


def xldate_to_datetime(xldatetime: int) -> datetime:
    """Convert Excel numeric date to datetime object"""
    temp_date = datetime(1899, 12, 31)
    (days, portion) = math.modf(xldatetime)
    
    delta_days = timedelta(days=days)
    secs = int(24 * 60 * 60 * portion)
    delta_seconds = timedelta(seconds=secs)
    the_time = temp_date + delta_days + delta_seconds
    return the_time


def process_order_dates(competencia_value: Any) -> tuple[str, str, int]:
    """
    Process competencia value and return start_date, end_date, and original data

    Args:
        competencia_value: Raw value from Excel (can be int, float, or string)

    Returns:
        tuple: (start_date_str, end_date_str, data_original)
    """
    # Handle different input types
    if isinstance(competencia_value, (int, float)) or (isinstance(competencia_value, str) and competencia_value.isdigit()):
        order_date = xldate_to_datetime(int(competencia_value))
        data_original = int(competencia_value)
    elif isinstance(competencia_value, str):
        # Handle date strings, remove time noise if present
        date_part = competencia_value.split(" ")[0]  # "2025-06-18 00:00:00" → "2025-06-18"
        order_date = datetime.strptime(date_part, "%Y-%m-%d")
        data_original = competencia_value
    else:
        raise ValueError(f"Unsupported competencia_value type: {type(competencia_value)}. Expected int, float, or string.")

    # Calculate previous month (first day)
    past_month = order_date + relativedelta.relativedelta(months=-1, day=1)
    past_month_string = past_month.strftime("%d/%m/%Y")

    # Calculate next month (last day)
    next_month = order_date + relativedelta.relativedelta(months=1, day=1)
    next_month = next_month.replace(day=calendar.monthrange(next_month.year, next_month.month)[1])
    next_month_string = next_month.strftime("%d/%m/%Y")
    
    return past_month_string, next_month_string, data_original


# ============================================================================
# MINUTA PROCESSING HELPERS - KISS Rate Limiting & PDF Operations
# ============================================================================

# Module-level cache and rate limiting state (KISS approach)
CNPJ_LOOKUP_CACHE: dict[str, tuple[str, str, str, str, dict[str, Any]]] = {}
LAST_CNPJ_API_CALL: datetime | None = None
MIN_DELAY_BETWEEN_CNPJ_CALLS = 20  # 20 seconds = 3 calls per minute


async def lookup_cnpj_info(cnpj: str) -> tuple[str, str, str, str, dict[str, Any]]:
    """
    Lookup CNPJ information from ReceitaWS API with rate limiting and cache

    Rate Limiting Strategy (KISS):
    - 3 requests per minute = 20 seconds between calls
    - Session-level cache (module-level dict)
    - Simple delay-based rate limiting

    Cache Strategy:
    - Cache hits: Return immediately without API call
    - Cache misses: Enforce 20s delay, make call, store in cache
    - Cache persists for workflow run duration

    Args:
        cnpj: CNPJ with only digits (no formatting)

    Returns:
        (city, state, municipio, uf, full_response)

    Example:
        city = "SALVADOR", state = "BA", municipio = "SALVADOR", uf = "BA"
    """
    global CNPJ_LOOKUP_CACHE, LAST_CNPJ_API_CALL

    # CACHE CHECK - Return immediately if cached
    if cnpj in CNPJ_LOOKUP_CACHE:
        logger.info(f"♻️ CNPJ cache HIT: {cnpj} (skipping API call)")
        return CNPJ_LOOKUP_CACHE[cnpj]

    logger.info(f"🔍 CNPJ cache MISS: {cnpj} (will call ReceitaWS API)")

    # RATE LIMITING - Enforce 20-second delay between API calls
    if LAST_CNPJ_API_CALL is not None:
        elapsed = (datetime.now(UTC) - LAST_CNPJ_API_CALL).total_seconds()
        if elapsed < MIN_DELAY_BETWEEN_CNPJ_CALLS:
            wait_time = MIN_DELAY_BETWEEN_CNPJ_CALLS - elapsed
            logger.info(f"⏳ Rate limiting: waiting {wait_time:.1f}s before CNPJ API call (3/minute limit)")
            await asyncio.sleep(wait_time)

    # MAKE API CALL
    try:
        # ReceitaWS API endpoint
        url = f"https://receitaws.com.br/v1/cnpj/{cnpj}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                # Update last call timestamp BEFORE processing response
                LAST_CNPJ_API_CALL = datetime.now(UTC)

                if response.status == 200:
                    data = await response.json()

                    if data.get("status") == "OK":
                        # Extract city and state
                        municipio = data.get("municipio", "").upper()
                        uf = data.get("uf", "").upper()

                        # City name processing (convert to CAPS with special chars preserved)
                        city = municipio.upper()
                        state = uf.upper()

                        logger.info(f"✅ ReceitaWS API success for CNPJ {cnpj}: {city}/{state}")

                        # CACHE THE RESULT
                        result = (city, state, municipio, uf, data)
                        CNPJ_LOOKUP_CACHE[cnpj] = result

                        return result
                    logger.error(f"❌ ReceitaWS API returned error status for CNPJ {cnpj}: {data}")
                    result = ("UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", {})
                    CNPJ_LOOKUP_CACHE[cnpj] = result  # Cache failures too
                    return result

                if response.status == 429:
                    # Rate limit exceeded - wait longer and retry once
                    logger.warning(f"⚠️ ReceitaWS rate limit (429) for CNPJ {cnpj} - waiting 60s and retrying")
                    await asyncio.sleep(60)

                    # Single retry after rate limit
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as retry_response:
                        LAST_CNPJ_API_CALL = datetime.now(UTC)

                        if retry_response.status == 200:
                            data = await retry_response.json()
                            if data.get("status") == "OK":
                                municipio = data.get("municipio", "").upper()
                                uf = data.get("uf", "").upper()
                                city = municipio.upper()
                                state = uf.upper()

                                result = (city, state, municipio, uf, data)
                                CNPJ_LOOKUP_CACHE[cnpj] = result
                                logger.info(f"✅ ReceitaWS retry success for CNPJ {cnpj}")
                                return result

                    # Retry failed
                    logger.error(f"❌ ReceitaWS retry failed for CNPJ {cnpj}")
                    result = ("UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", {})
                    CNPJ_LOOKUP_CACHE[cnpj] = result
                    return result
                logger.error(f"❌ ReceitaWS API HTTP {response.status} for CNPJ {cnpj}")
                result = ("UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", {})
                CNPJ_LOOKUP_CACHE[cnpj] = result
                return result

    except TimeoutError:
        logger.error(f"⏱️ ReceitaWS API timeout for CNPJ {cnpj}")
        result = ("UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", {})
        CNPJ_LOOKUP_CACHE[cnpj] = result
        return result
    except Exception as e:
        logger.error(f"❌ Error looking up CNPJ {cnpj}: {e}")
        result = ("UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", {})
        CNPJ_LOOKUP_CACHE[cnpj] = result
        return result


def clear_cnpj_lookup_cache() -> None:
    """Clear CNPJ lookup cache (call at workflow start for fresh run)"""
    global CNPJ_LOOKUP_CACHE, LAST_CNPJ_API_CALL
    CNPJ_LOOKUP_CACHE.clear()
    LAST_CNPJ_API_CALL = None
    logger.info("🧹 CNPJ lookup cache cleared")


async def concatenate_pdfs(pdf_paths: list[str], output_path: str) -> dict[str, Any]:
    """
    Concatenate multiple PDF files into a single PDF.

    Args:
        pdf_paths: List of paths to PDF files to concatenate
        output_path: Path where merged PDF should be saved

    Returns:
        dict with success status and details
    """
    try:
        from pypdf import PdfReader, PdfWriter

        writer = PdfWriter()

        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                logger.error(f"PDF file not found: {pdf_path}")
                return {"success": False, "error": f"File not found: {pdf_path}"}

            reader = PdfReader(pdf_path)
            for page in reader.pages:
                writer.add_page(page)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        logger.info(f"✅ Concatenated {len(pdf_paths)} PDFs → {output_path}")
        return {
            "success": True,
            "output_path": output_path,
            "total_pdfs": len(pdf_paths),
            "file_size": os.path.getsize(output_path)
        }

    except Exception as e:
        logger.error(f"PDF concatenation failed: {e!s}")
        return {"success": False, "error": str(e)}


def load_cnpj_group_from_json(json_file: str, cnpj_claro: str) -> dict[str, Any] | None:
    """
    Load specific CNPJ group data from MINUTA JSON file.

    Args:
        json_file: Path to minutas JSON file
        cnpj_claro: CNPJ to retrieve

    Returns:
        CNPJ group dict or None if not found
    """
    try:
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        for cnpj_group in data.get("cnpj_groups", []):
            if cnpj_group["cnpj_claro"] == cnpj_claro:
                return cnpj_group

        logger.warning(f"CNPJ {cnpj_claro} not found in {json_file}")
        return None

    except Exception as e:
        logger.error(f"Failed to load CNPJ group: {e!s}")
        return None


async def update_cnpj_status_in_json(
    json_file_path: str,
    cnpj_claro: str,
    new_status: MinutaProcessingStatus,
    protocol_number: str | None = None,
    pipeline_progress: dict[str, Any] | None = None,
    propagate_to_po: bool = False
) -> bool:
    """
    Update CNPJ group status in MINUTA JSON file.

    Args:
        json_file_path: Path to minutas JSON file
        cnpj_claro: CNPJ to update
        new_status: New MinutaProcessingStatus value
        protocol_number: Optional protocol number from upload

    Returns:
        True if update successful, False otherwise
    """
    try:
        # Read JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        # Find and update CNPJ group
        updated = False
        for group in json_data.get("cnpj_groups", []):
            if group["cnpj_claro"] == cnpj_claro:
                group["status"] = new_status
                group["last_updated"] = datetime.now(UTC).isoformat()

                # Update protocol if provided
                if protocol_number is not None:
                    group["protocol_number"] = protocol_number

                if pipeline_progress is not None:
                    group["pipeline_progress"] = pipeline_progress
                elif "pipeline_progress" in group:
                    # Ensure stale progress is cleared when not provided
                    del group["pipeline_progress"]

                updated = True
                logger.info(f"✅ Updated CNPJ {cnpj_claro} status to {new_status}")
                break

        if not updated:
            logger.warning(f"⚠️ CNPJ {cnpj_claro} not found in {json_file_path}")
            return False

        # Optional propagation to per-PO status map
        if propagate_to_po:
            po_status_map = group.setdefault("po_status", {})
            for po_key in list(po_status_map.keys()):
                po_status_map[po_key]["status"] = new_status.value
                if pipeline_progress is not None:
                    po_status_map[po_key]["pipeline_progress"] = pipeline_progress

        # Write back to file
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        return True

    except Exception as e:
        logger.error(f"❌ Failed to update CNPJ status in JSON: {e!s}")
        return False


async def update_po_status_in_json(
    json_file_path: str,
    cnpj_claro: str,
    po_number: str,
    new_status: MinutaProcessingStatus,
    pipeline_progress: dict[str, Any] | None = None,
    protocol_number: str | None = None
) -> bool:
    """Update status for a specific PO inside MINUTA JSON"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        updated = False
        for group in json_data.get("cnpj_groups", []):
            if group.get("cnpj_claro") != cnpj_claro:
                continue

            po_status_map = group.setdefault("po_status", {})
            po_entry = po_status_map.setdefault(po_number, {})
            po_entry["status"] = new_status.value
            po_entry["last_updated"] = datetime.now(UTC).isoformat()
            if pipeline_progress is not None:
                po_entry["pipeline_progress"] = pipeline_progress
            elif po_entry.get("pipeline_progress") and pipeline_progress is None:
                # clear previous progress when not provided
                po_entry.pop("pipeline_progress", None)

            if protocol_number is not None:
                po_entry["protocol_number"] = protocol_number

            updated = True
            break

        if not updated:
            logger.warning(f"⚠️ PO {po_number} not found for CNPJ {cnpj_claro} in {json_file_path}")
            return False

        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Updated PO {po_number} for CNPJ {cnpj_claro} → {new_status.value}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to update PO {po_number} status in JSON: {e!s}")
        return False


# Brasil API Parallel CNPJ Resolution with PostgreSQL Cache
# 🚨 TIMEOUT FIX: 60x faster than sequential ReceitaWS (35 CNPJs: 30s vs 12+ min)

async def lookup_cnpj_from_brasil_api(cnpj: str) -> tuple[str, str, str, str, dict[str, Any]]:
    """
    Lookup CNPJ information from Brasil API (NO rate limit, parallel-friendly).

    Args:
        cnpj: CNPJ identifier (14 digits, no formatting)

    Returns:
        Tuple of (city, state, municipio, uf, api_response)

    Note:
        Brasil API is PRIMARY source (no rate limit, fast 0.46s avg)
        Falls back to ReceitaWS if Brasil API fails
    """
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()

                    # Extract city/state from Brasil API response
                    municipio = data.get("municipio", "").upper()
                    uf = data.get("uf", "").upper()

                    logger.info(f"✅ Brasil API success: {municipio}/{uf} for CNPJ {cnpj}")

                    return municipio, uf, municipio, uf, data
                else:
                    logger.warning(f"⚠️ Brasil API HTTP {response.status} for CNPJ {cnpj}")
                    # Fall back to ReceitaWS
                    return await lookup_cnpj_info(cnpj)

    except Exception as e:
        logger.warning(f"⚠️ Brasil API error for CNPJ {cnpj}: {e}")
        # Fall back to ReceitaWS
        return await lookup_cnpj_info(cnpj)


async def load_cnpj_cache_from_db() -> dict[str, tuple[str, str, str, str]]:
    """
    Load CNPJ lookup cache from PostgreSQL (main hive database).

    Returns:
        Dictionary mapping CNPJ → (city, state, municipio, uf)

    Note:
        Uses main hive database (port 5532) same as cte_data/minuta_data
        Creates table if not exists (dynamic table creation pattern)
    """
    try:
        database_url = os.getenv("HIVE_DATABASE_URL")
        if not database_url:
            logger.warning("⚠️ HIVE_DATABASE_URL not set, cache disabled")
            return {}

        import psycopg

        async with await psycopg.AsyncConnection.connect(database_url) as conn:
            async with conn.cursor() as cur:
                # Create cache table if not exists (dynamic creation like cte_data)
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS hive.cnpj_lookup_cache (
                        cnpj_claro VARCHAR(14) PRIMARY KEY,
                        city VARCHAR(255) NOT NULL,
                        state VARCHAR(255) NOT NULL,
                        municipio VARCHAR(255) NOT NULL,
                        uf VARCHAR(2) NOT NULL,
                        source_api VARCHAR(50) NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        last_verified TIMESTAMPTZ DEFAULT NOW()
                    );

                    CREATE INDEX IF NOT EXISTS idx_cnpj_cache_source
                        ON hive.cnpj_lookup_cache(source_api);
                """)

                # Load all cached CNPJs
                await cur.execute("""
                    SELECT cnpj_claro, city, state, municipio, uf
                    FROM hive.cnpj_lookup_cache
                """)

                cache = {}
                rows = await cur.fetchall()
                for row in rows:
                    cnpj, city, state, municipio, uf = row
                    cache[cnpj] = (city, state, municipio, uf)

                logger.info(f"✅ Loaded {len(cache)} CNPJs from PostgreSQL cache")
                return cache

    except Exception as e:
        logger.warning(f"⚠️ Failed to load CNPJ cache: {e}")
        return {}


async def save_cnpj_to_cache(cnpj: str, city: str, state: str, municipio: str, uf: str, source_api: str = "brasil_api"):
    """
    Save CNPJ lookup to PostgreSQL cache (main hive database).

    Args:
        cnpj: CNPJ identifier (14 digits)
        city, state, municipio, uf: Location data
        source_api: API source ("brasil_api" or "receitaws")

    Note:
        UPSERT operation - updates if exists, inserts if new
    """
    try:
        database_url = os.getenv("HIVE_DATABASE_URL")
        if not database_url:
            return  # Cache disabled

        import psycopg

        async with await psycopg.AsyncConnection.connect(database_url) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    INSERT INTO hive.cnpj_lookup_cache
                        (cnpj_claro, city, state, municipio, uf, source_api)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (cnpj_claro)
                    DO UPDATE SET
                        city = EXCLUDED.city,
                        state = EXCLUDED.state,
                        municipio = EXCLUDED.municipio,
                        uf = EXCLUDED.uf,
                        source_api = EXCLUDED.source_api,
                        last_verified = NOW()
                """, (cnpj, city, state, municipio, uf, source_api))

                await conn.commit()

    except Exception as e:
        logger.warning(f"⚠️ Failed to save CNPJ {cnpj} to cache: {e}")


async def resolve_pending_cnpj_lookups(
    cnpj_groups: list[dict[str, Any]],
    max_concurrent: int = 10
) -> list[dict[str, Any]]:
    """
    Resolve PENDING_LOOKUP CNPJs using parallel Brasil API calls with PostgreSQL caching.

    Args:
        cnpj_groups: List of CNPJ group dicts (may have city="PENDING_LOOKUP")
        max_concurrent: Maximum concurrent API calls (default 10, no rate limit)

    Returns:
        Updated cnpj_groups with resolved city/state data

    Performance:
        - First run (35 uncached CNPJs): ~30 seconds (10 concurrent × 3s each)
        - Cached run (35 cached CNPJs): ~0 seconds (instant PostgreSQL lookup)
        - 60x faster than sequential ReceitaWS (12+ minutes)
    """
    # Load PostgreSQL cache
    cache = await load_cnpj_cache_from_db()

    pending_cnpjs = []
    cache_hits = 0
    cache_misses = 0

    # First pass: Check cache
    for cnpj_group in cnpj_groups:
        if cnpj_group.get("city") == "PENDING_LOOKUP":
            cnpj = cnpj_group["cnpj_claro"]

            if cnpj in cache:
                # Cache hit - instant lookup
                city, state, municipio, uf = cache[cnpj]
                cnpj_group["city"] = city
                cnpj_group["state"] = state
                cnpj_group["municipio"] = municipio
                cnpj_group["uf"] = uf
                cnpj_group["requires_regional"] = uf in ["TO", "SE"]
                cnpj_group["regional_type"] = "palmas" if uf == "TO" else ("aracaju" if uf == "SE" else None)
                cache_hits += 1
                logger.info(f"✅ Cache HIT: {cnpj} → {city}/{uf}")
            else:
                # Cache miss - need API lookup
                pending_cnpjs.append(cnpj_group)
                cache_misses += 1

    logger.info(f"📊 CNPJ Cache: {cache_hits} hits, {cache_misses} misses")

    if not pending_cnpjs:
        logger.info("✅ All CNPJs resolved from cache (0s)")
        return cnpj_groups

    # Second pass: Parallel API lookups for cache misses
    logger.info(f"🔍 Resolving {len(pending_cnpjs)} CNPJs via Brasil API (parallel, max {max_concurrent} concurrent)")

    semaphore = asyncio.Semaphore(max_concurrent)

    async def lookup_with_semaphore(cnpj_group):
        async with semaphore:
            cnpj = cnpj_group["cnpj_claro"]
            try:
                city, state, municipio, uf, api_response = await lookup_cnpj_from_brasil_api(cnpj)

                # Update CNPJ group
                cnpj_group["city"] = city
                cnpj_group["state"] = state
                cnpj_group["municipio"] = municipio
                cnpj_group["uf"] = uf
                cnpj_group["requires_regional"] = uf in ["TO", "SE"]
                cnpj_group["regional_type"] = "palmas" if uf == "TO" else ("aracaju" if uf == "SE" else None)

                # Save to cache
                await save_cnpj_to_cache(cnpj, city, state, municipio, uf, source_api="brasil_api")

                logger.info(f"✅ Resolved {cnpj} → {city}/{uf}")
                return True

            except Exception as e:
                logger.error(f"❌ Failed to resolve CNPJ {cnpj}: {e}")
                return False

    # Execute parallel lookups
    await asyncio.gather(*[lookup_with_semaphore(cnpj_group) for cnpj_group in pending_cnpjs])

    logger.info(f"✅ Resolved {len(pending_cnpjs)} CNPJs via parallel Brasil API")

    return cnpj_groups


async def process_excel_to_json(excel_path: str, json_path: str, batch_id: str) -> tuple[bool, dict | None]:
    """
    Process Excel file and create structured JSON with CTE data
    Returns (success: bool, validation_error: dict | None)
    """
    try:
        import os
        from pathlib import Path

        import pandas as pd
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        
        logger.info(f"📊 Processing Excel file: {excel_path}")
        
        # Read Excel file (auto-detect format: .xlsx, .xlsb, .xls, .ods)
        try:
            df = pd.read_excel(excel_path)  # Let pandas auto-detect the format
        except Exception as e:
            logger.error(f"❌ Failed to read Excel file {excel_path}: {e!s}")
            return False, None
        
        if df.empty:
            logger.warning(f"⚠️ Excel file is empty: {excel_path}")
            return False, None
            
        logger.info(f"📋 Excel loaded: {len(df)} rows, columns: {list(df.columns)}")
        
        available_columns = list(df.columns)
        
        # KISS Column Mapping - Handle variations in column names
        valor_column = "valor CHAVE" if "valor CHAVE" in available_columns else "Valor"
        
        # Check if CNPJ Claro exists - it's optional since we use CNPJ Fornecedor for actual processing
        # For CNPJ Claro, check for legitimate CNPJ column name variations (CNPJ is REQUIRED)
        cnpj_column = None
        for possible_name in ["CNPJ CLARO", "CNPJ Claro", "CNPJ_CLARO", "cnpj_claro", "CNPJ_Claro", "cnpj claro"]:
            if possible_name in available_columns:
                cnpj_column = possible_name
                logger.info(f"✅ Using '{possible_name}' column for CNPJ")
                break
        
        # Build required columns list with actual column names (CNPJ is REQUIRED)
        required_columns = [
            "Empresa Origem",
            valor_column,
            cnpj_column if cnpj_column else "CNPJ Claro",  # Use mapped name or expected name
            "TIPO",
            "NF/CTE",
            "PO",
            "Competência"
        ]
        
        # Validate ALL required columns are present BEFORE any processing
        logger.info(f"🔍 Validating required columns: {required_columns}")
        missing_columns = [col for col in required_columns if col not in available_columns]
        
        if missing_columns:
            error_msg = f"Excel validation failed - Missing required columns: {missing_columns}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"📋 Available columns: {available_columns}")
            logger.error(f"📄 File: {excel_path}")
            
            # Return validation error for reporting
            validation_error = {
                "file": excel_path,
                "error_type": "missing_columns",
                "missing_columns": missing_columns,
                "available_columns": available_columns,
                "timestamp": datetime.now(UTC).isoformat()
            }
            
            return False, validation_error
            
        logger.info("✅ All required columns validated successfully")
        
        # Filter only CTE records (exclude MINUTAS)
        if "TIPO" not in df.columns:
            logger.error("❌ Critical error: 'TIPO' column missing after validation")
            return False, None
            
        cte_df = df[df["TIPO"] == "CTE"].copy()
        logger.info(f"🔍 Filtered CTEs: {len(cte_df)} records (excluded {len(df) - len(cte_df)} MINUTA records)")
        
        if cte_df.empty:
            error_msg = "No CTE records found in Excel file (only MINUTAS or empty data)"
            logger.warning(f"⚠️ {error_msg}")
            
            # Return validation error for reporting
            validation_error = {
                "file": excel_path,
                "error_type": "no_cte_records",
                "total_records": len(df),
                "cte_records": len(cte_df),
                "timestamp": datetime.now(UTC).isoformat()
            }
            
            return False, validation_error
        
        # Group CTEs by PO and create structured JSON
        consolidated_data = {
            "batch_info": {
                "batch_id": batch_id,
                "source_file": excel_path,
                "processing_timestamp": datetime.now(UTC).isoformat(),
                "total_ctes": len(cte_df),
                "total_minutas_excluded": len(df) - len(cte_df)
            },
            "orders": []
        }
        
        # Group by PO column
        for po_number, po_group in cte_df.groupby("PO"):
            if pd.isna(po_number) or po_number == "":
                continue
                
            # Extract CTEs for this PO
            ctes = []
            po_total_value = 0
            competencia_values = []
            
            for _, row in po_group.iterrows():
                # Process competencia value using helper function
                competencia_raw = row.get("Competência", "")
                start_date_str, end_date_str, data_original = process_order_dates(competencia_raw)
                
                cte_data = {
                    "NF/CTE": str(row.get("NF/CTE", "")),
                    "valor_chave": str(row.get(valor_column, "")),
                    "empresa_origem": str(row.get("Empresa Origem", "")),
                    "cnpj_fornecedor": str(row.get("CNPJ Fornecedor", "")),
                    "cnpj_claro": str(row.get(cnpj_column, "")) if cnpj_column else "",  # Use mapped CNPJ column
                    "data_original": data_original  # Changed from 'competencia' to 'data_original'
                }
                ctes.append(cte_data)
                
                # Extract value for PO total (if numeric)
                try:
                    value = float(str(row.get(valor_column, "0")).replace(",", "."))
                    po_total_value += value
                except (ValueError, TypeError):
                    pass
                
                # Collect competencia values for PO date range calculation
                competencia_values.append(competencia_raw)
            
            # Calculate PO-level start and end dates using the first competencia value
            if competencia_values:
                start_date, end_date, _ = process_order_dates(competencia_values[0])
            else:
                start_date = "01/01/2025"
                end_date = "31/12/2025"
            
            # Create PO order structure
            order = {
                "po_number": str(po_number),
                "status": "PENDING",  # Initial status for new CTEs
                "ctes": ctes,
                "cte_count": len(ctes),
                "po_total_value": round(po_total_value, 2),
                "start_date": start_date,
                "end_date": end_date,
                "created_at": datetime.now(UTC).isoformat(),
                "last_updated": datetime.now(UTC).isoformat()
            }
            
            consolidated_data["orders"].append(order)
        
        consolidated_data["summary"] = {
            "total_orders": len(consolidated_data["orders"]),
            "total_ctes": sum(order["cte_count"] for order in consolidated_data["orders"]),
            "total_value": sum(order["po_total_value"] for order in consolidated_data["orders"])
        }
        
        # Write JSON file
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(consolidated_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ JSON created successfully: {json_path}")
        logger.info(f"📊 Summary: {consolidated_data['summary']['total_orders']} POs, {consolidated_data['summary']['total_ctes']} CTEs, Total: R$ {consolidated_data['summary']['total_value']:,.2f}")
        
        return True, None
        
    except Exception as e:
        logger.error(f"❌ Error processing Excel to JSON: {e!s}")
        import traceback
        logger.error(f"💥 Traceback: {traceback.format_exc()}")
        return False, None


async def process_excel_to_minuta_json(
    excel_path: str,
    json_path: str,
    batch_id: str
) -> tuple[bool, dict[str, Any] | None]:
    """
    Convert Excel MINUTA rows to structured JSON grouped by CNPJ Claro.

    Returns:
        (success: bool, validation_error: dict | None)
    """
    try:
        import pandas as pd

        # Ensure output directory exists
        os.makedirs(os.path.dirname(json_path), exist_ok=True)

        logger.info(f"📊 Processing Excel for MINUTA: {excel_path}")

        # Read Excel file
        df = pd.read_excel(excel_path)

        if df.empty:
            logger.warning(f"⚠️ Excel file is empty: {excel_path}")
            return False, None

        logger.info(f"📋 Excel loaded: {len(df)} rows")

        # Column mapping for MINUTA
        available_columns = list(df.columns)

        # Handle valor column variations
        valor_column = "valor CHAVE" if "valor CHAVE" in available_columns else "Valor"

        # Find CNPJ Claro column (with variations)
        cnpj_column = None
        for possible_name in ["CNPJ Claro", "CNPJ CLARO", "CNPJ_CLARO", "cnpj_claro"]:
            if possible_name in available_columns:
                cnpj_column = possible_name
                break

        # Build required columns list
        required_columns = [
            cnpj_column if cnpj_column else "CNPJ Claro",
            valor_column,
            "TIPO",
            "PO",
            "Competência",
            "Empresa Origem"
        ]

        # Validate columns
        missing_columns = [col for col in required_columns if col not in available_columns]

        if missing_columns:
            error_msg = f"MINUTA validation failed - Missing columns: {missing_columns}"
            logger.error(f"❌ {error_msg}")

            validation_error = {
                "file": excel_path,
                "error_type": "missing_columns",
                "missing_columns": missing_columns,
                "available_columns": available_columns,
                "timestamp": datetime.now(UTC).isoformat()
            }

            return False, validation_error

        logger.info("✅ All required MINUTA columns validated")

        # Filter ONLY MINUTA records
        minuta_df = df[df["TIPO"] == "MINUTA"].copy()
        logger.info(f"🔍 Filtered MINUTAs: {len(minuta_df)} records (excluded {len(df) - len(minuta_df)} CTE records)")

        if minuta_df.empty:
            error_msg = "No MINUTA records found in Excel file (only CTEs or empty)"
            logger.warning(f"⚠️ {error_msg}")

            validation_error = {
                "file": excel_path,
                "error_type": "no_minuta_records",
                "total_records": len(df),
                "minuta_records": len(minuta_df),
                "timestamp": datetime.now(UTC).isoformat()
            }

            return False, validation_error

        # Group MINUTAs by CNPJ Claro
        consolidated_data = {
            "batch_info": {
                "batch_id": batch_id,
                "source_file": excel_path,
                "processing_timestamp": datetime.now(UTC).isoformat(),
                "total_minutas": len(minuta_df),
                "total_ctes_excluded": len(df) - len(minuta_df)
            },
            "cnpj_groups": []
        }

        # Group by CNPJ Claro column
        import pandas as pd
        for cnpj_claro, group in minuta_df.groupby(cnpj_column):
            if pd.isna(cnpj_claro) or cnpj_claro == "":
                continue

            # Extract minutas for this CNPJ
            minutas = []
            total_value = 0.0
            competencia_values = []
            po_list = []
            po_values: dict[str, float] = {}

            for _, row in group.iterrows():
                # Process competencia value
                competencia_raw = row.get("Competência", "")
                start_date_str, end_date_str, data_original = process_order_dates(competencia_raw)

                minuta_data = {
                    "po": str(row.get("PO", "")),
                    "nf_cte": str(row.get("NF/CTE", "")),
                    "valor": float(str(row.get(valor_column, "0")).replace(",", ".")),
                    "data_original": data_original,
                    "competencia": str(row.get("Competência", ""))
                }
                minutas.append(minuta_data)

                # Accumulate metrics
                total_value += minuta_data["valor"]
                competencia_values.append(competencia_raw)

                po = str(row.get("PO", ""))
                if po not in po_list:
                    po_list.append(po)
                    po_values[po] = 0.0
                try:
                    po_values[po] += float(str(row.get(valor_column, "0")).replace(",", "."))
                except (TypeError, ValueError):
                    pass

            # Calculate CNPJ-level start and end dates
            if competencia_values:
                start_date, end_date, _ = process_order_dates(competencia_values[0])
            else:
                start_date = "01/01/2025"
                end_date = "31/12/2025"

            # Get first row for company data
            first_row = group.iloc[0]
            empresa_origem = str(first_row.get("Empresa Origem", ""))

            # Remove formatting from CNPJ Claro for API calls (keep only digits)
            cnpj_claro_clean = "".join(filter(str.isdigit, str(cnpj_claro)))

            # 🚨 TIMEOUT FIX: Defer CNPJ lookup to avoid initialization step timeout
            # City/state will be resolved during minuta_cnpj_processing_step
            # using parallel Brasil API lookups with PostgreSQL caching
            city = "PENDING_LOOKUP"
            state = "PENDING_LOOKUP"
            municipio = "PENDING_LOOKUP"
            uf = "PENDING_LOOKUP"

            logger.info(f"📋 CNPJ {cnpj_claro_clean}: Deferred city/state lookup (will resolve during processing)")

            # Determine regional download requirement (will be updated during lookup)
            requires_regional = False  # Will be set to True if uf in ["TO", "SE"]
            regional_type = None       # Will be set to "palmas"/"aracaju" during lookup

            # Create CNPJ group structure
            cnpj_group = {
                "cnpj_claro": cnpj_claro_clean,
                "cnpj_claro_formatted": str(cnpj_claro),
                "empresa_origem": empresa_origem,
                "status": MinutaProcessingStatus.PENDING,
                "po_status": {
                    po: {
                        "status": MinutaProcessingStatus.PENDING.value,
                        "pipeline_progress": None,
                        "last_updated": datetime.now(UTC).isoformat(),
                        "value": round(po_values.get(po, 0.0), 2)
                    }
                    for po in po_list
                },

                # Location data from ReceitaWS
                "city": city,
                "state": state,
                "municipio": municipio,
                "uf": uf,

                # MINUTA data
                "minutas": minutas,
                "minuta_count": len(minutas),
                "total_value": round(total_value, 2),
                "po_list": po_list,
                "start_date": start_date,
                "end_date": end_date,

                # Regional download flags
                "requires_regional": requires_regional,
                "regional_type": regional_type,

                # Processing metadata
                "created_at": datetime.now(UTC).isoformat(),
                "last_updated": datetime.now(UTC).isoformat(),
                "protocol_number": None,

                # File tracking (Initialize arrays for multi-PO support)
                "pdf_files": {
                    "base_city_hall_pdfs": [],         # Base city hall PDFs from main-minut-download
                    "additional_city_hall_pdfs": [],   # Additional PDFs from Palmas/Aracaju (if TO/SE)
                    "final_concatenated": None         # Final merged PDF for invoiceUpload
                }
            }

            consolidated_data["cnpj_groups"].append(cnpj_group)

        # Generate summary
        consolidated_data["summary"] = {
            "total_cnpj_groups": len(consolidated_data["cnpj_groups"]),
            "total_minutas": sum(group["minuta_count"] for group in consolidated_data["cnpj_groups"]),
            "total_value": sum(group["total_value"] for group in consolidated_data["cnpj_groups"]),
            "total_pos": len(set(po for group in consolidated_data["cnpj_groups"] for po in group["po_list"]))
        }

        # Write JSON file
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(consolidated_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ MINUTA JSON created: {json_path}")
        logger.info(f"📊 Summary: {consolidated_data['summary']['total_cnpj_groups']} CNPJs, {consolidated_data['summary']['total_minutas']} MINUTAs, Total: R$ {consolidated_data['summary']['total_value']:,.2f}")

        return True, None

    except Exception as e:
        logger.error(f"❌ Error processing Excel to MINUTA JSON: {e!s}")
        import traceback
        logger.error(f"💥 Traceback: {traceback.format_exc()}")
        return False, None


# New Daily Workflow Step Executors

async def execute_daily_initialization_step(step_input: StepInput) -> StepOutput:
    """Initialize daily processing cycle - scan for new emails and existing JSON files"""
    workflow_start_time = datetime.now(UTC)
    logger.info("🌅 Starting daily initialization...")

    # CRITICAL: Clear CNPJ lookup cache at workflow start for fresh daily run
    clear_cnpj_lookup_cache()
    logger.info("🧹 CNPJ cache cleared for fresh daily processing")

    # Initialize session state
    session_state = get_session_state(step_input)
    set_session_state(step_input, "workflow_start_time", workflow_start_time)

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

    try:
        logger.info("🚀 Starting real Gmail email processing...")
        
        # Use absolute paths for Gmail credentials (project root)
        project_root = Path(__file__).parent.parent.parent.parent
        credentials_path = project_root / "credentials.json"
        token_path = project_root / "token.json"
        
        logger.info(f"📁 Using credentials: {credentials_path}")
        logger.info(f"📁 Using token: {token_path}")
        
        gmail_authenticator = GmailAuthenticator(
            credentials_file=str(credentials_path),
            token_file=str(token_path)
        )
        gmail_downloader = GmailDownloader(authenticator=gmail_authenticator)

        # Download Excel attachments (max 3 emails per day)
        downloaded_files = gmail_downloader.download_excel_attachments(max_emails=3)

        for file_info in downloaded_files:
            # Process each Excel file and create corresponding JSON FOR BOTH CTE AND MINUTA
            excel_path = file_info["path"]
            # Use email sent time for clear naming: ctes_11-09-2025_14h30.json
            email_datetime = file_info.get("email_date", datetime.now(UTC).strftime("%d-%m-%Y_%Hh%M"))
            cte_json_path = f"mctech/ctes/ctes_{email_datetime}.json"
            minuta_json_path = f"mctech/minutas/minutas_{email_datetime}.json"

            try:
                # REAL EXCEL PROCESSING - Convert Excel to CTE JSON
                cte_json_created, cte_validation_error = await process_excel_to_json(excel_path, cte_json_path, daily_batch_id)

                # Store CTE validation error if present
                if cte_validation_error:
                    session_state = get_session_state(step_input)
                    if "validation_errors" not in session_state:
                        session_state["validation_errors"] = []
                    session_state["validation_errors"].append(cte_validation_error)

                # REAL EXCEL PROCESSING - Convert Excel to MINUTA JSON
                minuta_json_created, minuta_validation_error = await process_excel_to_minuta_json(excel_path, minuta_json_path, daily_batch_id)

                # Store MINUTA validation error if present (only if it's not "no_minuta_records" - that's expected)
                if minuta_validation_error and minuta_validation_error.get("error_type") != "no_minuta_records":
                    session_state = get_session_state(step_input)
                    if "validation_errors" not in session_state:
                        session_state["validation_errors"] = []
                    session_state["validation_errors"].append(minuta_validation_error)

                new_emails_processed.append({
                    "filename": file_info["filename"],
                    "file_path": file_info["path"],
                    "size_bytes": file_info["size_bytes"],
                    "checksum": file_info["checksum"],
                    "email_id": file_info["email_id"],
                    "cte_json_created": cte_json_path,
                    "cte_json_exists": cte_json_created,
                    "minuta_json_created": minuta_json_path,
                    "minuta_json_exists": minuta_json_created,
                    "status": "NEW_PENDING" if (cte_json_created or minuta_json_created) else "FAILED_EXTRACTION"
                })

                if cte_json_created:
                    logger.info(f"✅ CTE Excel processed successfully: {excel_path} → {cte_json_path}")
                else:
                    logger.error(f"❌ Failed to process CTE Excel: {excel_path}")

                if minuta_json_created:
                    logger.info(f"✅ MINUTA Excel processed successfully: {excel_path} → {minuta_json_path}")
                else:
                    logger.warning(f"⚠️ No MINUTAs found in Excel: {excel_path}")

            except Exception as e:
                logger.error(f"❌ Error processing Excel {excel_path}: {e!s}")
                new_emails_processed.append({
                    "filename": file_info["filename"],
                    "file_path": file_info["path"],
                    "size_bytes": file_info["size_bytes"],
                    "checksum": file_info["checksum"],
                    "email_id": file_info["email_id"],
                    "cte_json_created": cte_json_path,
                    "cte_json_exists": False,
                    "minuta_json_created": minuta_json_path,
                    "minuta_json_exists": False,
                    "status": "FAILED_EXTRACTION",
                    "error": str(e)
                })

        logger.info(f"📧 Real Gmail processing completed: {len(new_emails_processed)} files downloaded and processed")

    except Exception as e:
        logger.error(f"❌ Gmail processing failed: {e!s}")
        # Continue workflow without new emails if Gmail fails
        new_emails_processed = []

    # REAL DIRECTORY SCANNING - Find all existing JSON files (CTE and MINUTA)
    import glob
    cte_json_pattern = "mctech/ctes/ctes_*.json"
    existing_cte_json_files = glob.glob(cte_json_pattern)

    minuta_json_pattern = "mctech/minutas/minutas_*.json"
    existing_minuta_json_files = glob.glob(minuta_json_pattern)

    if not existing_cte_json_files:
        logger.info("📁 No existing CTE JSON files found in mctech/ctes/ directory")
        existing_cte_json_files = []
    else:
        logger.info(f"📁 Found {len(existing_cte_json_files)} existing CTE JSON files: {existing_cte_json_files}")

    if not existing_minuta_json_files:
        logger.info("📁 No existing MINUTA JSON files found in mctech/minutas/ directory")
        existing_minuta_json_files = []
    else:
        logger.info(f"📁 Found {len(existing_minuta_json_files)} existing MINUTA JSON files: {existing_minuta_json_files}")

    initialization_results = {
        "daily_batch_id": daily_batch_id,
        "new_emails_processed": len(new_emails_processed),
        "new_json_files_created": new_emails_processed,
        "existing_json_files_found": existing_cte_json_files,
        "minuta_json_files_found": existing_minuta_json_files,
        "total_files_to_analyze": len(new_emails_processed) + len(existing_cte_json_files),
        "total_minuta_files": len(existing_minuta_json_files),
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
       - CHECK_ORDER_STATUS: Ready for claroCheck validation
       - WAITING_MONITORING: Ready for invoiceMonitor
       - MONITORED: Ready for download
       - DOWNLOADED: Ready for upload
       - UPLOADED: Already completed (skip)
       - FAILED_*: Needs error handling

    OUTPUT STRUCTURE:
    {{
        "processing_categories": {{
            "pending_pos": [...],
            "validation_pos": [...],
            "monitoring_pos": [...],
            "download_pos": [...],
            "upload_pos": [...],
            "completed_pos": [...],
            "failed_pos": [...]
        }},
        "json_file_status": {{
            "file_path": "po_status_summary_placeholder"
        }}
    }}
    """

    response = data_extractor.run(analysis_context)

    # REAL JSON FILE ANALYSIS - Parse actual JSON files and extract PO status
    import os
    analysis_results = {
        "processing_categories": {
            "pending_pos": [],
            "validation_pos": [],
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

    all_json_files = init_results["existing_json_files_found"] + [
        file_info["cte_json_created"] for file_info in init_results["new_json_files_created"]
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
                "validation": 0,
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
                elif status == "CHECK_ORDER_STATUS":
                    analysis_results["processing_categories"]["validation_pos"].append(po_entry)
                    file_stats["validation"] += 1
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
                    file_stats["needs_processing"] = True  # Need to send email
                elif status == "COMPLETED":
                    # Don't add to any processing category - truly done
                    file_stats["completed"] = file_stats.get("completed", 0) + 1
                    # Note: Don't set needs_processing = True for COMPLETED
                elif status.startswith("FAILED_"):
                    analysis_results["processing_categories"]["failed_pos"].append(po_entry)
                    file_stats["failed"] += 1
                    file_stats["needs_processing"] = True

            analysis_results["json_file_status"][json_file_path] = file_stats
            analysis_results["analysis_summary"]["total_pos_found"] += file_stats["total_pos"]

            if file_stats["needs_processing"]:
                analysis_results["analysis_summary"]["files_needing_processing"] += 1
                analysis_results["analysis_summary"]["pos_needing_processing"] += (
                    file_stats["pending"] + file_stats["validation"] + file_stats["waiting_monitoring"] +
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
    - PENDING → invoiceGen API call → CHECK_ORDER_STATUS
    - CHECK_ORDER_STATUS → claroCheck API call (individual) → [based on output.status]:
        • "Aguardando Liberação" → keeps CHECK_ORDER_STATUS (for next day)
        • "Agendamento Pendente" → WAITING_MONITORING
        • "Autorizada Emissão Nota Fiscal" → MONITORED
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
            "order_validation_queue": {
                "action": "claroCheck",
                "pos": processing_categories["validation_pos"],
                "batch_processing": False,  # Individual processing
                "priority": 1.5  # Between generation and monitoring
            },
            "invoice_monitoring_queue": {
                "action": "invoiceMonitor",
                "pos": processing_categories["monitoring_pos"],
                "batch_processing": False,  # Process each PO individually
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
            },
            "email_queue": {
                "action": "sendEmail",
                "pos": processing_categories["completed_pos"],  # UPLOADED status POs
                "batch_processing": False,
                "priority": 5
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
        "failed_orders": {},  # Track orders that failed browser processing
        "execution_summary": {
            "successful_actions": 0,
            "failed_actions": 0,
            "browser_failures": 0,  # Failed due to browser process
            "pos_updated": 0,
            "pos_failed": 0
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
                        "headless": get_headless_setting()
                    }
                }

                api_response = await api_client.execute_api_call(action, payload)

                # Extract browser success information
                browser_success = api_response.get("api_result", {}).get("success", False) if api_response["success"] else False
                browser_error = api_response.get("api_result", {}).get("error", "Unknown error")
                browser_output = api_response.get("api_result", {}).get("text_output", "No output")

                processing_results["api_executions"][queue_name] = {
                    "action": action,
                    "pos_processed": po_numbers,
                    "batch_mode": True,
                    "http_success": api_response["success"],
                    "browser_success": browser_success,
                    "overall_success": api_response["success"] and browser_success,
                    "execution_time_ms": api_response.get("execution_time_ms", 0),
                    "api_response": api_response.get("api_result", {}),
                    "browser_error": browser_error if not browser_success else None,
                    "browser_output": browser_output
                }

                # Update status ONLY if both HTTP and browser process succeeded
                if api_response["success"] and browser_success:
                    new_status = {
                        "invoiceGen": "CHECK_ORDER_STATUS",  # Now goes to Claro validation
                        "invoiceMonitor": "MONITORED"
                    }.get(action, "UNKNOWN")

                    logger.info(f"✅ Batch {action} successful - updating {len(pos)} POs to {new_status}")
                    for po_data in pos:
                        processing_results["status_updates"][po_data["po_number"]] = {
                            "new_status": new_status,
                            "json_file": po_data["json_file"]
                        }

                    processing_results["execution_summary"]["successful_actions"] += 1
                    processing_results["execution_summary"]["pos_updated"] += len(pos)
                
                elif api_response["success"] and not browser_success:
                    # HTTP successful but browser process failed - track all POs as failed
                    logger.error(f"❌ Batch {action} browser process failed - all {len(pos)} POs affected")
                    logger.error(f"💥 Browser Error: {browser_error}")
                    
                    for po_data in pos:
                        processing_results["failed_orders"][po_data["po_number"]] = {
                            "action": action,
                            "failure_type": "browser_process_failure",
                            "error": browser_error,
                            "output": browser_output,
                            "json_file": po_data["json_file"]
                        }
                    
                    processing_results["execution_summary"]["browser_failures"] += 1
                    processing_results["execution_summary"]["pos_failed"] += len(pos)
                
                else:
                    # HTTP call failed
                    logger.error(f"❌ HTTP call failed for batch {action} - all {len(pos)} POs affected")
                    
                    for po_data in pos:
                        processing_results["failed_orders"][po_data["po_number"]] = {
                            "action": action,
                            "failure_type": "http_failure",
                            "error": api_response.get("error", "HTTP call failed"),
                            "json_file": po_data["json_file"]
                        }
                    
                    processing_results["execution_summary"]["failed_actions"] += 1
                    processing_results["execution_summary"]["pos_failed"] += len(pos)

            else:
                # Individual processing for downloads, uploads, and validations
                individual_results = {}

                for po_data in pos:
                    po_number = po_data["po_number"]
                    json_file = po_data["json_file"]

                    if action == "claroCheck":
                        # Handle claroCheck validation
                        payload = api_client.build_claro_check_payload(po_number)
                        api_response = await api_client.execute_api_call(action, payload)

                        # Parse claroCheck response for status transition
                        if api_response["success"]:
                            browser_success, new_status, message = api_client.parse_claro_check_response(api_response.get("api_result", {}))

                            individual_results[po_number] = {
                                "http_success": True,
                                "browser_success": browser_success,
                                "overall_success": browser_success,
                                "execution_time_ms": api_response.get("execution_time_ms", 0),
                                "api_response": api_response.get("api_result", {}),
                                "validation_result": {
                                    "new_status": new_status,
                                    "message": message
                                }
                            }

                            if browser_success:
                                logger.info(f"✅ claroCheck validation successful for PO {po_number} - updating to {new_status}")
                                processing_results["status_updates"][po_number] = {
                                    "new_status": new_status,
                                    "json_file": json_file
                                }
                                processing_results["execution_summary"]["successful_actions"] += 1
                                processing_results["execution_summary"]["pos_updated"] += 1
                            else:
                                logger.error(f"❌ claroCheck validation failed for PO {po_number}: {message}")
                                processing_results["failed_orders"][po_number] = {
                                    "action": action,
                                    "failure_type": "validation_failure",
                                    "error": message,
                                    "json_file": json_file
                                }
                                processing_results["execution_summary"]["browser_failures"] += 1
                                processing_results["execution_summary"]["pos_failed"] += 1
                        else:
                            # HTTP call failed for claroCheck
                            individual_results[po_number] = {
                                "http_success": False,
                                "browser_success": False,
                                "overall_success": False,
                                "execution_time_ms": api_response.get("execution_time_ms", 0),
                                "error": api_response.get("error", "HTTP call failed")
                            }

                            processing_results["failed_orders"][po_number] = {
                                "action": action,
                                "failure_type": "http_failure",
                                "error": api_response.get("error", "HTTP call failed"),
                                "json_file": json_file
                            }
                            processing_results["execution_summary"]["failed_actions"] += 1
                            processing_results["execution_summary"]["pos_failed"] += 1

                        continue  # Skip to next PO for claroCheck processing

                    if action == "sendEmail":
                        # Handle email sending for completed uploads
                        # Load JSON to get full PO details including protocol
                        try:
                            with open(json_file) as f:
                                json_data = json.load(f)

                            # Find the specific PO in the JSON orders array
                            po_details = None
                            for order in json_data.get("orders", []):
                                if order.get("po_number") == po_number:
                                    po_details = order
                                    break

                            if po_details is None:
                                raise ValueError(f"PO {po_number} not found in JSON orders")

                        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
                            logger.error(f"❌ Failed to load JSON for PO {po_number}: {e}")
                            processing_results["failed_orders"][po_number] = {
                                "action": action,
                                "failure_type": "json_error",
                                "error": str(e),
                                "json_file": json_file
                            }
                            processing_results["execution_summary"]["failed_actions"] += 1
                            processing_results["execution_summary"]["pos_failed"] += 1
                            continue

                        # Get protocol from JSON
                        protocol = po_details.get("protocol_number")
                        logger.info(f"🔍 DEBUG: PO {po_number} protocol_number extraction: {protocol}")
                        logger.info(f"🔍 DEBUG: po_details keys: {list(po_details.keys()) if po_details else 'None'}")

                        if not protocol:
                            logger.error(f"❌ No protocol found for PO {po_number}")
                            processing_results["failed_orders"][po_number] = {
                                "action": action,
                                "failure_type": "missing_protocol",
                                "error": "No protocol number in JSON",
                                "json_file": json_file
                            }
                            processing_results["execution_summary"]["failed_actions"] += 1
                            processing_results["execution_summary"]["pos_failed"] += 1
                            continue

                        cliente = po_details["ctes"][0]["empresa_origem"]

                        # Process ZIPs
                        zip_result = api_client.process_invoice_zips(po_number, protocol)

                        if zip_result.get("error"):
                            logger.error(f"❌ ZIP processing failed for PO {po_number}: {zip_result['error']}")
                            processing_results["failed_orders"][po_number] = {
                                "action": action,
                                "failure_type": "zip_processing_failure",
                                "error": zip_result["error"],
                                "json_file": json_file
                            }
                            processing_results["execution_summary"]["failed_actions"] += 1
                            processing_results["execution_summary"]["pos_failed"] += 1
                            continue

                        # Send email
                        sender = GmailSender()
                        email_recipient = os.getenv("INVOICE_EMAIL_RECIPIENT")
                        email_result = sender.send_invoice_email(
                            to_email=email_recipient,
                            po_number=po_number,
                            protocol=protocol,
                            cliente=cliente,
                            attachments=zip_result["attachments"]
                        )

                        individual_results[po_number] = {
                            "email_sent": email_result.success,
                            "message_id": email_result.message_id,
                            "error": email_result.error,
                            "attachments_count": len(zip_result["attachments"])
                        }

                        # Update status based on email result
                        if email_result.success:
                            logger.info(f"✅ Email sent successfully for PO {po_number}")
                            new_status = "COMPLETED"
                            processing_results["status_updates"][po_number] = {
                                "new_status": new_status,
                                "json_file": json_file
                            }
                            processing_results["execution_summary"]["successful_actions"] += 1
                            processing_results["execution_summary"]["pos_updated"] += 1
                        else:
                            logger.error(f"❌ Email failed for PO {po_number}: {email_result.error}")
                            # Update status to FAILED_EMAIL for retry capability
                            processing_results["status_updates"][po_number] = {
                                "new_status": "FAILED_EMAIL",
                                "json_file": json_file
                            }
                            processing_results["failed_orders"][po_number] = {
                                "action": action,
                                "failure_type": "email_failure",
                                "error": email_result.error,
                                "json_file": json_file
                            }
                            processing_results["execution_summary"]["failed_actions"] += 1
                            processing_results["execution_summary"]["pos_failed"] += 1

                        continue  # Skip to next PO for sendEmail processing

                    # Load JSON to get real PO details (for non-claroCheck actions)
                    po_details = None
                    try:
                        if os.path.exists(json_file):
                            with open(json_file, encoding="utf-8") as f:
                                json_data = json.load(f)
                            
                            # Find the specific PO in the JSON
                            for order in json_data.get("orders", []):
                                if order.get("po_number") == po_number:
                                    po_details = {
                                        "po_number": po_number,
                                        "protocol_number": order.get("protocol_number"),
                                        "ctes": order.get("ctes", []),
                                        "po_total_value": order.get("po_total_value", 0),
                                        "start_date": order.get("start_date", ""),
                                        "end_date": order.get("end_date", ""),
                                        "client_data": order.get("client_data", {}),
                                        "date_range": order.get("date_range", {}),
                                        "value_totals": order.get("value_totals", {})
                                    }
                                    logger.info(f"📊 Loaded real PO details for {po_number}: {len(po_details.get('ctes', []))} CTEs, Value: {po_details.get('po_total_value', 0)}")
                                    logger.info(f"🔍 DEBUG: Extracted po_details for {po_number}: protocol_number={po_details.get('protocol_number')}")
                                    break
                            
                            if po_details is None:
                                logger.error(f"❌ PO {po_number} not found in JSON file {json_file}")
                                raise ValueError(f"PO {po_number} not found in JSON")
                        else:
                            logger.error(f"❌ JSON file not found: {json_file}")
                            raise FileNotFoundError(f"JSON file not found: {json_file}")
                            
                    except Exception as e:
                        logger.error(f"❌ Failed to load PO details for {po_number}: {e}")
                        processing_results["failed_orders"][po_number] = {
                            "action": action,
                            "failure_type": "data_loading_failure",
                            "error": f"Failed to load PO details: {e!s}",
                            "json_file": json_file
                        }
                        processing_results["execution_summary"]["failed_actions"] += 1
                        processing_results["execution_summary"]["pos_failed"] += 1
                        continue  # Skip this PO if we can't load its details

                    # Build payload for the specific action
                    try:
                        if action == "main-download-invoice":
                            payload = api_client.build_invoice_download_payload(po_details)
                        elif action == "invoiceUpload":
                            payload = api_client.build_invoice_upload_payload(po_details, f"mctech/downloads/fatura_{po_number}.pdf")
                        elif action == "invoiceMonitor":
                            payload = api_client.build_invoice_monitor_payload(po_number)
                        else:
                            logger.error(f"❌ Unknown individual action: {action}")
                            processing_results["failed_orders"][po_number] = {
                                "action": action,
                                "failure_type": "unknown_action",
                                "error": f"Unknown action: {action}",
                                "json_file": json_file
                            }
                            processing_results["execution_summary"]["failed_actions"] += 1
                            processing_results["execution_summary"]["pos_failed"] += 1
                            continue
                    except FileNotFoundError as e:
                        logger.error(f"❌ File not found for PO {po_number} in action {action}: {e}")
                        processing_results["failed_orders"][po_number] = {
                            "action": action,
                            "failure_type": "file_not_found",
                            "error": str(e),
                            "json_file": json_file
                        }
                        processing_results["execution_summary"]["failed_actions"] += 1
                        processing_results["execution_summary"]["pos_failed"] += 1
                        continue
                    except Exception as e:
                        logger.error(f"❌ Failed to build payload for PO {po_number} in action {action}: {e}")
                        processing_results["failed_orders"][po_number] = {
                            "action": action,
                            "failure_type": "payload_build_failure",
                            "error": str(e),
                            "json_file": json_file
                        }
                        processing_results["execution_summary"]["failed_actions"] += 1
                        processing_results["execution_summary"]["pos_failed"] += 1
                        continue

                    api_response = await api_client.execute_api_call(action, payload)

                    # Extract browser success information for individual processing
                    browser_success = api_response.get("api_result", {}).get("success", False) if api_response["success"] else False
                    browser_error = api_response.get("api_result", {}).get("error", "Unknown error")
                    browser_output = api_response.get("api_result", {}).get("text_output", "No output")

                    individual_results[po_number] = {
                        "http_success": api_response["success"],
                        "browser_success": browser_success,
                        "overall_success": api_response["success"] and browser_success,
                        "execution_time_ms": api_response.get("execution_time_ms", 0),
                        "api_response": api_response.get("api_result", {}),
                        "browser_error": browser_error if not browser_success else None
                    }

                    # Update individual PO status ONLY if both HTTP and browser process succeeded
                    if api_response["success"] and browser_success:
                        # Handle special case for invoiceUpload with protocol extraction
                        if action == "invoiceUpload":
                            # Extract protocol from upload response
                            success, protocol, message = api_client.parse_invoice_upload_response(api_response)

                            if success and protocol:
                                # Store protocol in JSON for email processing
                                try:
                                    with open(json_file) as f:
                                        json_data = json.load(f)

                                    json_data["protocol_number"] = protocol
                                    json_data["last_updated"] = datetime.now(UTC).isoformat()

                                    with open(json_file, "w") as f:
                                        json.dump(json_data, f, indent=2, ensure_ascii=False)

                                    logger.info(f"📝 Protocol {protocol} saved to JSON for PO {po_number}")
                                except Exception as e:
                                    logger.error(f"❌ Failed to save protocol to JSON: {e}")
                            else:
                                logger.warning(f"⚠️ No protocol extracted for PO {po_number}: {message}")

                        # Map action to resulting status
                        new_status = {
                            "invoiceMonitor": "MONITORED",
                            "main-download-invoice": "DOWNLOADED",
                            "invoiceUpload": "UPLOADED"
                        }.get(action, "UNKNOWN")

                        logger.info(f"✅ Individual {action} successful for PO {po_number} - updating to {new_status}")

                        processing_results["status_updates"][po_number] = {
                            "new_status": new_status,
                            "json_file": json_file
                        }

                        processing_results["execution_summary"]["successful_actions"] += 1
                        processing_results["execution_summary"]["pos_updated"] += 1
                    
                    elif api_response["success"] and not browser_success:
                        # HTTP successful but browser process failed
                        logger.error(f"❌ Individual {action} browser process failed for PO {po_number}")
                        logger.error(f"💥 Browser Error: {browser_error}")
                        
                        processing_results["failed_orders"][po_number] = {
                            "action": action,
                            "failure_type": "browser_process_failure",
                            "error": browser_error,
                            "output": browser_output,
                            "json_file": json_file
                        }
                        
                        processing_results["execution_summary"]["browser_failures"] += 1
                        processing_results["execution_summary"]["pos_failed"] += 1
                    
                    else:
                        # HTTP call failed
                        logger.error(f"❌ HTTP call failed for individual {action} for PO {po_number}")
                        
                        processing_results["failed_orders"][po_number] = {
                            "action": action,
                            "failure_type": "http_failure",
                            "error": api_response.get("error", "HTTP call failed"),
                            "json_file": json_file
                        }
                        
                        processing_results["execution_summary"]["failed_actions"] += 1
                        processing_results["execution_summary"]["pos_failed"] += 1

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
    completion_start_time = datetime.now(UTC)
    logger.info("🏁 Starting daily completion and JSON updates...")

    # Get processing results
    previous_output = step_input.get_step_output("individual_po_processing")
    if not previous_output:
        raise ValueError("Individual PO processing step output not found")

    processing_results = json.loads(previous_output.content)
    
    # Handle case where API was unavailable - no status updates to apply
    status_updates = processing_results.get("status_updates", {})
    if not status_updates:
        logger.warning("⚠️ No status updates available - API may be unavailable, completing without file updates")
        return StepOutput(content=json.dumps({
            "status": "SUCCESS",
            "message": "Daily completion successful - no status updates to apply",
            "api_available": False,
            "files_updated": 0,
            "completion_timestamp": datetime.now(UTC).isoformat()
        }))

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

    # REAL JSON file updates - Actually update the files
    files_updated = {}
    for po_number, update_info in status_updates.items():
        json_file = update_info["json_file"]
        new_status = update_info["new_status"]
        
        if json_file not in files_updated:
            files_updated[json_file] = {
                "pos_updated": [],
                "update_count": 0
            }

        files_updated[json_file]["pos_updated"].append(f"{po_number} → {new_status}")
        files_updated[json_file]["update_count"] += 1

        # REAL FILE UPDATE: Update the actual JSON file
        try:
            import os
            if os.path.exists(json_file):
                with open(json_file, encoding="utf-8") as f:
                    json_data = json.load(f)
                
                # Update the status for this specific PO
                for order in json_data.get("orders", []):
                    if order.get("po_number") == po_number:
                        order["status"] = new_status
                        order["last_updated"] = datetime.now(UTC).isoformat()
                        logger.info(f"✅ Updated PO {po_number} status to {new_status} in {json_file}")
                        break
                
                # Write updated JSON back to file
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                    
                logger.info(f"💾 JSON file updated successfully: {json_file}")
            else:
                logger.warning(f"⚠️ JSON file not found: {json_file}")
                
        except Exception as e:
            logger.error(f"❌ Failed to update JSON file {json_file}: {e!s}")
            # Continue with other files if one fails

    # Get all session state for final summary
    session_state = get_session_state(step_input)
    
    # Ensure init_results is from the step output, not session state
    previous_init_output = step_input.get_step_output("daily_initialization")
    if previous_init_output:
        init_results = json.loads(previous_init_output.content)
    else:
        # Fallback to session state if step output not available
        init_results = session_state.get("initialization_results", {})
        logger.warning("⚠️ Using session state for init_results - step output not found")
    
    analysis_results = session_state.get("analysis_results", {})
    
    # Calculate actual execution time
    completion_end_time = datetime.now(UTC)
    
    # Get workflow start time from session state or use completion start as fallback
    workflow_start_time = session_state.get("workflow_start_time", completion_start_time)
    if isinstance(workflow_start_time, str):
        workflow_start_time = datetime.fromisoformat(workflow_start_time.replace("Z", "+00:00"))
    
    total_execution_time_seconds = (completion_end_time - workflow_start_time).total_seconds()
    total_execution_time_minutes = round(total_execution_time_seconds / 60, 2)

    # Get MINUTA completion metrics for summary
    minuta_completion_output = step_input.get_step_output("minuta_completion")
    minuta_metrics = {}
    if minuta_completion_output:
        try:
            minuta_completion_data = json.loads(minuta_completion_output.content)
            minuta_metrics = {
                "cnpj_groups_processed": minuta_completion_data.get("minuta_statistics", {}).get("cnpj_groups_processed", 0),
                "minutas_processed": minuta_completion_data.get("minuta_statistics", {}).get("minutas_processed", 0),
                "cnpj_groups_failed": minuta_completion_data.get("minuta_statistics", {}).get("cnpj_groups_failed", 0),
                "regional_downloads": minuta_completion_data.get("minuta_statistics", {}).get("regional_downloads", 0),
                "total_value": minuta_completion_data.get("minuta_statistics", {}).get("total_value", 0.0),
                "execution_time_minutes": minuta_completion_data.get("minuta_execution_summary", {}).get("execution_time_minutes", 0)
            }
        except Exception as e:
            logger.warning(f"⚠️ Could not extract MINUTA metrics for summary: {e}")

    completion_summary = {
        "daily_execution_summary": {
            "execution_date": datetime.now(UTC).strftime("%Y-%m-%d"),
            "daily_batch_id": session_state.get("daily_batch_id", init_results.get("daily_batch_id", "unknown")),
            "total_execution_time_minutes": total_execution_time_minutes,
            "workflow_start_time": workflow_start_time.isoformat(),
            "workflow_end_time": completion_end_time.isoformat(),
            "overall_status": "SUCCESS"
        },
        "cte_processing": {
            "new_emails_processed": init_results.get("new_emails_processed", 0),
            "existing_files_analyzed": len(init_results.get("existing_json_files_found", [])),
            "total_pos_found": analysis_results.get("analysis_summary", {}).get("total_pos_found", 0),
            "pos_processed_today": processing_results["execution_summary"]["pos_updated"],
            "pos_failed_today": processing_results["execution_summary"]["pos_failed"],
            "pos_completed_today": len([po for po, update in status_updates.items() if update["new_status"] == "COMPLETED"]),
            "pos_uploaded_today": len([po for po, update in status_updates.items() if update["new_status"] == "UPLOADED"]),
            "api_calls_successful": processing_results["execution_summary"]["successful_actions"],
            "api_calls_failed": processing_results["execution_summary"]["failed_actions"],
            "browser_process_failures": processing_results["execution_summary"]["browser_failures"]
        },
        "minuta_processing": minuta_metrics,
        "json_file_updates": files_updated,
        "status_transitions_applied": status_updates,
        "failed_orders_detail": processing_results.get("failed_orders", {}),
        "next_execution_scheduled": {
            "next_run": (datetime.now(UTC) + timedelta(days=1)).replace(hour=8, minute=0, second=0).isoformat(),
            "frequency": "daily",
            "estimated_pos_for_next_run": analysis_results.get("analysis_summary", {}).get("pos_needing_processing", 0) - processing_results["execution_summary"]["pos_updated"]
        },
        "completion_timestamp": datetime.now(UTC).isoformat(),
        "agent_response": str(response.content) if response.content else "No response"
    }

    # Backward compatibility - keep old processing_statistics key for existing integrations
    completion_summary["processing_statistics"] = completion_summary["cte_processing"]

    logger.info("🏁 Daily processing cycle completed!")
    
    # Log detailed processing results
    stats = completion_summary["processing_statistics"]
    logger.info(f"✅ Successfully processed: {stats['pos_processed_today']} POs")
    logger.info(f"❌ Failed to process: {stats['pos_failed_today']} POs")
    logger.info(f"📤 Reached UPLOADED status: {stats['pos_uploaded_today']} POs")
    logger.info(f"✉️ Emails sent (COMPLETED): {stats['pos_completed_today']} POs")
    
    # Log failure details if any
    failed_orders = processing_results.get("failed_orders", {})
    if failed_orders:
        logger.warning(f"⚠️ {len(failed_orders)} POs failed processing:")
        for po_number, failure_info in failed_orders.items():
            failure_type = failure_info.get("failure_type", "unknown")
            error = failure_info.get("error", "No error details")
            logger.warning(f"   • PO {po_number}: {failure_type} - {error}")
    
    # Log API call statistics
    logger.info(f"📡 API calls successful: {stats['api_calls_successful']}")
    logger.info(f"📡 API calls failed: {stats['api_calls_failed']}")
    logger.info(f"🌐 Browser process failures: {stats['browser_process_failures']}")
    
    logger.info(f"⏰ Next execution scheduled: {completion_summary['next_execution_scheduled']['next_run']}")

    # 📱 SEND WHATSAPP NOTIFICATION - Daily completion report (CTE + MINUTA combined)
    # Load Omni API settings from environment (explicit import to avoid scope issues)
    import os as env_os
    omni_api_url = env_os.getenv("OMNI_API_URL")
    omni_api_key = env_os.getenv("OMNI_API_KEY")
    omni_phone_numbers_str = env_os.getenv("OMNI_PHONE_NUMBERS")

    # Parse comma-separated phone numbers
    omni_phone_numbers = [phone.strip() for phone in omni_phone_numbers_str.split(",") if phone.strip()]

    try:
        # Calculate status transitions for enhanced statistics
        status_breakdown = {}
        for po_number, update_info in status_updates.items():
            new_status = update_info["new_status"]
            if new_status in status_breakdown:
                status_breakdown[new_status] += 1
            else:
                status_breakdown[new_status] = 1

        # Build enhanced statistics message
        enhanced_stats = []

        # Map status to friendly names with icons
        status_display = {
            "CHECK_ORDER_STATUS": "🔒 Aguardando liberação",
            "WAITING_MONITORING": "⏳ Aguardando agendamento",
            "MONITORED": "📅 Agendados",
            "DOWNLOADED": "📦 Kits baixados",
            "UPLOADED": "✅ Uploads realizados"
        }

        # Add each status with count to enhanced stats
        for status, count in status_breakdown.items():
            if status in status_display:
                enhanced_stats.append(f"{status_display[status]}: {count}")

        # Join enhanced stats with newlines
        enhanced_stats_text = "\n".join(enhanced_stats) if enhanced_stats else "Nenhuma atualização de status"

        # Check for validation errors from session state
        validation_errors = session_state.get("validation_errors", [])
        validation_error_text = ""

        if validation_errors:
            validation_error_text = "\n\n⚠️ *Erros de Validação:*\n"
            for error in validation_errors:
                file_name = error.get("file", "arquivo desconhecido").split("/")[-1]  # Just filename
                error_type = error.get("error_type", "erro desconhecido")

                if error_type == "missing_columns":
                    missing_cols = error.get("missing_columns", [])
                    validation_error_text += f"❌ {file_name}: Colunas ausentes: {', '.join(missing_cols)}\n"
                elif error_type == "no_cte_records":
                    total_records = error.get("total_records", 0)
                    validation_error_text += f"❌ {file_name}: Nenhum CTE encontrado ({total_records} registros analisados)\n"
                else:
                    validation_error_text += f"❌ {file_name}: {error_type}\n"

        # Get MINUTA completion results from session state
        minuta_completion_output = step_input.get_step_output("minuta_completion")
        minuta_stats_text = ""

        if minuta_completion_output:
            try:
                minuta_completion_data = json.loads(minuta_completion_output.content)
                minuta_stats = minuta_completion_data.get("minuta_statistics", {})
                minuta_exec_summary = minuta_completion_data.get("minuta_execution_summary", {})

                # Only add MINUTA section if actual processing occurred (not placeholder)
                if minuta_stats.get("cnpj_groups_processed", 0) > 0 or minuta_stats.get("cnpj_groups_failed", 0) > 0:
                    minuta_stats_text = f"""

📋 *MINUTAs Processados:*
✅ CNPJs processados: {minuta_stats.get('cnpj_groups_processed', 0)}
📄 Minutas geradas: {minuta_stats.get('minutas_processed', 0)}
📍 Downloads regionais: {minuta_stats.get('regional_downloads', 0)}
❌ CNPJs falharam: {minuta_stats.get('cnpj_groups_failed', 0)}
⏱️ Tempo MINUTA: {minuta_exec_summary.get('execution_time_minutes', 0):.1f} min"""
            except Exception as e:
                logger.warning(f"⚠️ Could not parse MINUTA completion data: {e}")

        # Build combined WhatsApp message
        whatsapp_message = f"""🏁 *PROCESSAMENTO DIÁRIO CONCLUÍDO*

📊 *CTEs Processados:*
✅ POs processados: {stats['pos_processed_today']}
❌ POs falharam: {stats['pos_failed_today']}
📤 Uploads realizados: {stats['pos_uploaded_today']}
✉️ Emails enviados: {stats['pos_completed_today']}
📧 Emails recebidos: {stats['new_emails_processed']}{minuta_stats_text}

📋 *Status atualizados:*
{enhanced_stats_text}{validation_error_text}

⏱️ *Tempo total:* {total_execution_time_minutes:.1f} minutos""".strip()

        # Log WhatsApp message before sending
        logger.info("📱 Mensagem WhatsApp que será enviada:")
        logger.info("=" * 60)
        logger.info(whatsapp_message)
        logger.info("=" * 60)

        # Send WhatsApp notification via Omni API
        import requests

        logger.info(f"📱 Using Omni API: {omni_api_url} -> {len(omni_phone_numbers)} recipients (key: ...{omni_api_key[-6:]})")
        
        url = omni_api_url
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {omni_api_key}",
            "Content-Type": "application/json"
        }
        
        # Send message to all phone numbers
        sent_count = 0
        failed_numbers = []
        
        for phone_number in omni_phone_numbers:
            try:
                payload = {
                    "phone_number": phone_number,
                    "text": whatsapp_message
                }
                
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    logger.info(f"📱 Message sent successfully to {phone_number}")
                    sent_count += 1
                else:
                    logger.error(f"❌ Failed to send to {phone_number}: HTTP {response.status_code}")
                    failed_numbers.append(phone_number)
                    
            except Exception as e:
                logger.error(f"❌ Error sending to {phone_number}: {e}")
                failed_numbers.append(phone_number)
        
        if sent_count == 0:
            raise Exception(f"Failed to send to all {len(omni_phone_numbers)} numbers")
        
        logger.info(f"📱 Daily completion notification sent via Omni WhatsApp API successfully to {sent_count}/{len(omni_phone_numbers)} recipients")
        completion_summary["whatsapp_notification"] = {
            "sent": True,
            "timestamp": datetime.now(UTC).isoformat(),
            "recipients_total": len(omni_phone_numbers),
            "recipients_success": sent_count,
            "recipients_failed": len(failed_numbers),
            "failed_numbers": failed_numbers,
            "message_preview": whatsapp_message[:100] + "..."
        }
        
    except Exception as e:
        logger.error(f"❌ Error sending WhatsApp notification: {e}")
        completion_summary["whatsapp_notification"] = {
            "sent": False,
            "timestamp": datetime.now(UTC).isoformat(),
            "error": str(e)
        }

    return StepOutput(content=json.dumps(completion_summary))







# ============================================================================
# MINUTA WORKFLOW STEPS - PHASE 2 IMPLEMENTATION
# ============================================================================


def build_minuta_whatsapp_message(
    cnpj_groups_processed: int,
    cnpj_groups_failed: int,
    protocolos_gerados: int,
    pedidos_liberados: int,
    minutas_concluidas: int,
    minutas_processadas: int,
    minutas_falharam: int,
    regional_downloads: int,
    total_value: float,
    execution_time: float,
    cnpj_details: list[dict] | None = None
) -> str:
    """
    Build WhatsApp notification message for MINUTA processing

    Args:
        cnpj_groups_processed: Number of CNPJ groups successfully processed
        cnpj_groups_failed: Number of CNPJ groups that failed processing
        protocolos_gerados: Number of POs that got protocols (PENDING → CHECK_ORDER_STATUS)
        pedidos_liberados: Number of POs released for invoice generation (CHECK_ORDER_STATUS → CLARO_GENERATED)
        minutas_concluidas: Number of POs that completed multihop pipeline
        minutas_processadas: Number of POs that updated status successfully
        minutas_falharam: Number of POs that failed (not counting CHECK_ORDER_STATUS)
        regional_downloads: Number of regional downloads (Palmas/Aracaju)
        total_value: Total monetary value of MINUTAs processed (R$)
        execution_time: Total execution time in minutes
        cnpj_details: Optional list of CNPJ processing details with status

    Returns:
        Formatted WhatsApp message string
    """
    message = f"""📋 *PROCESSAMENTO MINUTA CONCLUÍDO*

📄 *Minutas processadas:* {minutas_processadas}
❌ *Minutas falharam:* {minutas_falharam}

🔖 *Protocolos gerados:* {protocolos_gerados}
📤 *Pedidos liberados para emissão de NF:* {pedidos_liberados}
✅ *Minutas concluídas:* {minutas_concluidas}

💰 *Valor total:* R$ {total_value:,.2f}

⏱️ *Tempo execução:* {execution_time:.1f} minutos"""

    return message.strip()


async def execute_minuta_json_analysis_step(step_input: StepInput) -> StepOutput:
    """Analyze all MINUTA JSON files and extract CNPJ group status information"""
    logger.info("🔍 Starting MINUTA JSON analysis...")

    previous_output = step_input.get_step_output("daily_initialization")
    if not previous_output:
        logger.warning("⚠️ Daily initialization step output not found - MINUTA analysis skipped")
        return StepOutput(content=json.dumps({"status": "SKIPPED", "reason": "No initialization data"}))

    init_results = json.loads(previous_output.content)
    data_extractor = create_data_extractor_agent()
    _ = data_extractor.run("ANALYZE MINUTA JSON FILES")

    # Clean architecture: Detect ALL relevant statuses for hybrid processing
    processing_categories = {
        "pending_cnpjs": [],           # PENDING → minutGen
        "check_order_cnpjs": [],       # CHECK_ORDER_STATUS → claroCheck
        "claro_generated_cnpjs": [],   # CLARO/ESL/DOWNLOADED/etc → multi-hop pipeline
        "failed_cnpjs": [],            # FAILED_* → manual intervention
        "completed_cnpjs": []          # UPLOADED/COMPLETED → skip
    }

    analysis_results = {
        "processing_categories": processing_categories,
        "analysis_summary": {
            "total_cnpj_groups_found": 0,
            "pending_count": 0,
            "check_order_count": 0,
            "claro_generated_count": 0,
            "failed_count": 0,
            "completed_count": 0
        },
        "analysis_timestamp": datetime.now(UTC).isoformat()
    }

    all_minuta_json_files = init_results.get("minuta_json_files_found", [])

    # 🚨 TIMEOUT FIX: Resolve PENDING_LOOKUP CNPJs using parallel Brasil API
    all_cnpj_groups = []

    for json_file_path in all_minuta_json_files:
        try:
            if not os.path.exists(json_file_path):
                continue

            with open(json_file_path, encoding="utf-8") as f:
                json_data = json.load(f)

            cnpj_groups = json_data.get("cnpj_groups", [])

            # Track CNPJ groups for batch resolution
            for group in cnpj_groups:
                group["json_file"] = json_file_path  # Add file reference

                # Ensure per-PO status structure exists
                po_status_map = group.setdefault("po_status", {})
                if not po_status_map:
                    temp_values: dict[str, float] = {}
                    for minuta in group.get("minutas", []):
                        po_number = str(minuta.get("po", ""))
                        if not po_number:
                            continue
                        temp_values.setdefault(po_number, 0.0)
                        try:
                            temp_values[po_number] += float(minuta.get("valor", 0.0))
                        except (TypeError, ValueError):
                            pass
                        po_status_map.setdefault(po_number, {
                            "status": MinutaProcessingStatus.PENDING.value,
                            "pipeline_progress": None,
                            "last_updated": datetime.now(UTC).isoformat(),
                            "value": round(temp_values.get(po_number, 0.0), 2)
                        })
                else:
                    # Ensure value field exists for legacy entries
                    recomputed_values: dict[str, float] = {}
                    for minuta in group.get("minutas", []):
                        po_number = str(minuta.get("po", ""))
                        if not po_number:
                            continue
                        recomputed_values.setdefault(po_number, 0.0)
                        try:
                            recomputed_values[po_number] += float(minuta.get("valor", 0.0))
                        except (TypeError, ValueError):
                            pass
                    for po_number, po_entry in po_status_map.items():
                        po_entry.setdefault("value", round(recomputed_values.get(po_number, 0.0), 2))

                all_cnpj_groups.append(group)

        except Exception as e:
            logger.error(f"❌ Error loading MINUTA {json_file_path}: {e!s}")
            continue

    # Resolve all PENDING_LOOKUP CNPJs in parallel (Brasil API + PostgreSQL cache)
    logger.info(f"🔍 Resolving PENDING_LOOKUP CNPJs for {len(all_cnpj_groups)} CNPJ groups...")
    all_cnpj_groups = await resolve_pending_cnpj_lookups(all_cnpj_groups, max_concurrent=10)

    # Update JSON files with resolved city/state data
    json_file_updates = {}
    for cnpj_group in all_cnpj_groups:
        json_file_path = cnpj_group.get("json_file")
        if not json_file_path:
            continue

        if json_file_path not in json_file_updates:
            json_file_updates[json_file_path] = []
        json_file_updates[json_file_path].append(cnpj_group)

    # Write updated data back to JSON files
    for json_file_path, cnpj_groups_to_update in json_file_updates.items():
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            # Update each CNPJ group in the JSON
            for updated_group in cnpj_groups_to_update:
                for group in json_data.get("cnpj_groups", []):
                    if group["cnpj_claro"] == updated_group["cnpj_claro"]:
                        group["city"] = updated_group["city"]
                        group["state"] = updated_group["state"]
                        group["municipio"] = updated_group["municipio"]
                        group["uf"] = updated_group["uf"]
                        group["requires_regional"] = updated_group["requires_regional"]
                        group["regional_type"] = updated_group["regional_type"]
                        group["last_updated"] = datetime.now(UTC).isoformat()
                        break

            # Write back to file
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Updated {len(cnpj_groups_to_update)} CNPJ groups in {json_file_path}")

        except Exception as e:
            logger.error(f"❌ Failed to update {json_file_path}: {e}")

    # Now process groups for status analysis - detect ALL relevant statuses
    for cnpj_group in all_cnpj_groups:
        try:
            cnpj = cnpj_group.get("cnpj_claro")
            json_file_path = cnpj_group.get("json_file")

            po_status_map = cnpj_group.get("po_status", {})
            pending_pos: list[str] = []
            failed_pos: list[str] = []
            uploaded_pos: list[str] = []

            for po_number, po_entry in po_status_map.items():
                status_value = po_entry.get("status", MinutaProcessingStatus.CLARO_GENERATED.value)
                try:
                    po_status = MinutaProcessingStatus(status_value)
                except ValueError:
                    po_status = MinutaProcessingStatus.CLARO_GENERATED

                if po_status in {MinutaProcessingStatus.UPLOADED, MinutaProcessingStatus.COMPLETED}:
                    uploaded_pos.append(po_number)
                    continue

                failed_step = po_entry.get("pipeline_progress", {}).get("failed_step") if isinstance(po_entry.get("pipeline_progress"), dict) else None
                if failed_step:
                    failed_pos.append(po_number)

                pending_pos.append(po_number)

            entry = {
                "cnpj": cnpj,
                "json_file": json_file_path,
                "status": cnpj_group.get("status", MinutaProcessingStatus.PENDING).value if isinstance(cnpj_group.get("status"), MinutaProcessingStatus) else str(cnpj_group.get("status", MinutaProcessingStatus.PENDING.value)),
                "requires_regional": bool(cnpj_group.get("requires_regional")),
                "uf": cnpj_group.get("uf"),
                "pending_pos": pending_pos,
                "failed_pos": failed_pos,
                "uploaded_pos": uploaded_pos
            }

            # Get CNPJ-level status
            cnpj_status = entry["status"]

            # Categorize by CNPJ-level status
            if cnpj_status == MinutaProcessingStatus.PENDING.value:
                processing_categories["pending_cnpjs"].append(entry)
                analysis_results["analysis_summary"]["pending_count"] += 1
            elif cnpj_status == MinutaProcessingStatus.CHECK_ORDER_STATUS.value:
                processing_categories["check_order_cnpjs"].append(entry)
                analysis_results["analysis_summary"]["check_order_count"] += 1
            elif not pending_pos and uploaded_pos:
                processing_categories["completed_cnpjs"].append(entry)
                analysis_results["analysis_summary"]["completed_count"] += 1
            elif pending_pos:
                processing_categories["claro_generated_cnpjs"].append(entry)
                analysis_results["analysis_summary"]["claro_generated_count"] += 1
                if failed_pos:
                    analysis_results["analysis_summary"]["failed_count"] += len(failed_pos)
            else:
                # Default to pending bucket if nothing set
                processing_categories["pending_cnpjs"].append(entry)
                analysis_results["analysis_summary"]["pending_count"] += 1

            analysis_results["analysis_summary"]["total_cnpj_groups_found"] += 1

        except Exception as e:
            logger.error(f"❌ Error analyzing CNPJ group {cnpj}: {e!s}")
            continue

    set_session_state(step_input, "minuta_analysis_results", analysis_results)

    # Log summary
    logger.info("🔍 MINUTA JSON analysis completed:")
    logger.info(f"  📋 Total CNPJs: {analysis_results['analysis_summary']['total_cnpj_groups_found']}")
    logger.info(f"  ⏳ PENDING (→ minutGen): {analysis_results['analysis_summary']['pending_count']}")
    logger.info(f"  🔍 CHECK_ORDER_STATUS (→ claroCheck): {analysis_results['analysis_summary']['check_order_count']}")
    logger.info(f"  🚀 CLARO_GENERATED (→ pipeline): {analysis_results['analysis_summary']['claro_generated_count']}")
    logger.info(f"  ❌ FAILED: {analysis_results['analysis_summary']['failed_count']}")
    logger.info(f"  ✅ COMPLETED: {analysis_results['analysis_summary']['completed_count']}")

    return StepOutput(content=json.dumps(analysis_results))


async def execute_minuta_status_routing_step(step_input: StepInput) -> StepOutput:
    """Route CNPJs to 3 queues: minutGen (PENDING) → claroCheck (CHECK_ORDER_STATUS) → multi-hop pipeline (CLARO_GENERATED)"""
    logger.info("🎯 Starting MINUTA routing (hybrid architecture)...")

    previous_output = step_input.get_step_output("minuta_json_analysis")
    if not previous_output:
        return StepOutput(content=json.dumps({"status": "SKIPPED"}))

    analysis_results = json.loads(previous_output.content)
    processing_categories = analysis_results.get("processing_categories", {})

    api_orchestrator = create_api_orchestrator_agent()
    _ = api_orchestrator.run("MINUTA ROUTING")

    # Clean architecture: 3 queues for sequential processing
    processing_queues = {}

    # Queue 1: PENDING → CHECK_ORDER_STATUS (minutGen isolated)
    pending_cnpjs = processing_categories.get("pending_cnpjs", [])
    if pending_cnpjs:
        processing_queues["minuta_generation_queue"] = {
            "action": "minutGen",
            "current_status": "PENDING",
            "next_status": "CHECK_ORDER_STATUS",
            "cnpjs": pending_cnpjs
        }
        logger.info(f"📝 Queue 1: {len(pending_cnpjs)} CNPJs routed to minutGen")

    # Queue 2: CHECK_ORDER_STATUS → CLARO_GENERATED (claroCheck validation)
    check_order_cnpjs = processing_categories.get("check_order_cnpjs", [])
    if check_order_cnpjs:
        processing_queues["order_validation_queue"] = {
            "action": "claroCheck",
            "current_status": "CHECK_ORDER_STATUS",
            "next_status_if_approved": "CLARO_GENERATED",
            "next_status_if_pending": "CHECK_ORDER_STATUS",
            "batch_processing": False,  # Process individual POs
            "cnpjs": check_order_cnpjs
        }
        logger.info(f"🔍 Queue 2: {len(check_order_cnpjs)} CNPJs routed to claroCheck validation")

    # Queue 3: CLARO_GENERATED → UPLOADED (multi-hop pipeline)
    claro_generated_cnpjs = processing_categories.get("claro_generated_cnpjs", [])
    if claro_generated_cnpjs:
        enriched_entries = []
        for entry in claro_generated_cnpjs:
            pending_pos = entry.get("pending_pos", [])
            if not pending_pos:
                continue
            entry_copy = dict(entry)
            entry_copy["pending_pos"] = pending_pos
            enriched_entries.append(entry_copy)

        if enriched_entries:
            processing_queues["multi_hop_pipeline_queue"] = {
                "action": "multi_hop_pipeline",
                "current_status": "CLARO_GENERATED",
                "target_status": "UPLOADED",
                "pipeline_steps": [
                    {
                        "step": 1,
                        "action": "main-minut-gen",
                        "next_status": "ESL_GENERATED",
                        "wait_time_seconds": get_minuta_pipeline_wait_time()
                    },
                    {
                        "step": 2,
                        "action": "main-minut-download",
                        "next_status": "DOWNLOADED"
                    },
                    {
                        "step": 3,
                        "action": "regional-download",
                        "next_status": "REGIONAL_DOWNLOADED",
                        "conditional": "requires_regional"
                    },
                    {
                        "step": 4,
                        "action": "concatenate",
                        "next_status": "CONCATENATED"
                    },
                    {
                        "step": 5,
                        "action": "invoiceUpload",
                        "next_status": "UPLOADED",
                        "extract_protocol": True
                    }
                ],
                "cnpjs": enriched_entries
            }
            logger.info(f"🚀 Queue 3: {len(enriched_entries)} CNPJs com POs pendentes na pipeline")
        else:
            logger.info("ℹ️ Nenhum PO pendente para multi-hop nesta rodada")

    routing_results = {
        "processing_queues": processing_queues,
        "routing_timestamp": datetime.now(UTC).isoformat(),
        "queues_created": len(processing_queues)
    }

    set_session_state(step_input, "minuta_routing_results", routing_results)
    logger.info(f"🎯 MINUTA routing completed: {len(processing_queues)} queues created")

    return StepOutput(content=json.dumps(routing_results))


async def execute_minuta_cnpj_processing_step(step_input: StepInput) -> StepOutput:
    """
    Clean hybrid processing: 3 distinct branches
    - Branch 1: minutGen (PENDING → CHECK_ORDER_STATUS)
    - Branch 2: claroCheck (CHECK_ORDER_STATUS → CLARO_GENERATED or stays)
    - Branch 3: Multi-hop pipeline (CLARO_GENERATED → UPLOADED)
    """
    logger.info("⚙️ Starting MINUTA CNPJ processing (hybrid architecture)...")

    # Get routing results
    previous_output = step_input.get_step_output("minuta_status_routing")
    if not previous_output:
        logger.warning("⚠️ No routing results found - skipping")
        return StepOutput(content=json.dumps({
            "execution_summary": {
                "cnpjs_updated": 0,
                "cnpjs_failed": 0,
                "protocolos_gerados": 0,
                "pedidos_liberados": 0,
                "minutas_concluidas": 0,
                "minutas_processadas": 0,
                "minutas_falharam": 0,
                "total_value": 0.0,
                "regional_downloads": 0,
                "pipeline_executions": 0,
                "pipeline_completions": 0,
                "pipeline_failures": 0,
                "pipeline_execution_time_seconds": 0.0,
                "pipeline_avg_time_minutes": 0.0
            },
            "status": "SKIPPED"
        }))

    routing_results = json.loads(previous_output.content)
    processing_queues = routing_results.get("processing_queues", {})

    if not processing_queues:
        logger.info("ℹ️ No queues to process")
        return StepOutput(content=json.dumps({
            "execution_summary": {
                "cnpjs_updated": 0,
                "cnpjs_failed": 0,
                "protocolos_gerados": 0,
                "pedidos_liberados": 0,
                "minutas_concluidas": 0,
                "minutas_processadas": 0,
                "minutas_falharam": 0,
                "total_value": 0.0,
                "regional_downloads": 0,
                "pipeline_executions": 0,
                "pipeline_completions": 0,
                "pipeline_failures": 0,
                "pipeline_execution_time_seconds": 0.0,
                "pipeline_avg_time_minutes": 0.0
            },
            "status": "NO_QUEUES"
        }))

    # Initialize API client
    api_client = BrowserAPIClient()

    # Execution summary
    execution_summary = {
        "cnpjs_updated": 0,
        "cnpjs_failed": 0,
        "protocolos_gerados": 0,  # Branch 1: POs PENDING → CHECK_ORDER_STATUS
        "pedidos_liberados": 0,    # Branch 2: POs CHECK_ORDER_STATUS → CLARO_GENERATED
        "minutas_concluidas": 0,   # Branch 3: POs que completaram multihop pipeline
        "minutas_processadas": 0,  # POs que atualizaram status com sucesso
        "minutas_falharam": 0,     # POs que falharam (não contando CHECK_ORDER_STATUS)
        "total_value": 0.0,
        "regional_downloads": 0,
        "pipeline_executions": 0,
        "pipeline_completions": 0,
        "pipeline_failures": 0,
        "pipeline_execution_time_seconds": 0.0
    }

    # ═══════════════════════════════════════════════════════════════
    # BRANCH 1: minutGen Isolated (PENDING → CHECK_ORDER_STATUS)
    # ═══════════════════════════════════════════════════════════════
    if "minuta_generation_queue" in processing_queues:
        queue_info = processing_queues["minuta_generation_queue"]
        cnpjs = queue_info.get("cnpjs", [])

        logger.info(f"📝 Branch 1: Processing {len(cnpjs)} CNPJs via minutGen...")

        for entry in cnpjs:
            result = await execute_minutgen_only(entry, api_client)

            if result["success"]:
                execution_summary["cnpjs_updated"] += 1

                # Count POs that got protocols generated (PENDING → CHECK_ORDER_STATUS)
                cnpj_group = load_cnpj_group_from_json(entry["json_file"], entry["cnpj"])
                if cnpj_group:
                    po_count = len(cnpj_group.get("po_list", []))
                    execution_summary["protocolos_gerados"] += po_count
                    execution_summary["minutas_processadas"] += po_count  # POs que mudaram status
            else:
                execution_summary["cnpjs_failed"] += 1

                # Count POs that failed
                cnpj_group = load_cnpj_group_from_json(entry["json_file"], entry["cnpj"])
                if cnpj_group:
                    execution_summary["minutas_falharam"] += len(cnpj_group.get("po_list", []))

    # ═══════════════════════════════════════════════════════════════
    # BRANCH 2: claroCheck Validation (CHECK_ORDER_STATUS → CLARO_GENERATED or stays)
    # ═══════════════════════════════════════════════════════════════
    if "order_validation_queue" in processing_queues:
        queue_info = processing_queues["order_validation_queue"]
        cnpjs = queue_info.get("cnpjs", [])

        logger.info(f"🔍 Branch 2: Validating {len(cnpjs)} CNPJs via claroCheck...")

        for entry in cnpjs:
            result = await execute_claro_check_for_minuta(entry, api_client)

            if result["success"]:
                if result["status"] == MinutaProcessingStatus.CLARO_GENERATED.value:
                    execution_summary["cnpjs_updated"] += 1

                    # Count POs released for invoice generation (CHECK_ORDER_STATUS → CLARO_GENERATED)
                    pos_approved_count = len(result["pos_approved"])
                    execution_summary["pedidos_liberados"] += pos_approved_count
                    execution_summary["minutas_processadas"] += pos_approved_count  # POs que mudaram status

                    # Load CNPJ group to get total value
                    cnpj_group = load_cnpj_group_from_json(entry["json_file"], result["cnpj"])
                    if cnpj_group:
                        execution_summary["total_value"] += cnpj_group.get("total_value", 0.0)

                    logger.info(f"✅ CNPJ {result['cnpj']} approved → CLARO_GENERATED ({pos_approved_count} POs)")
                else:
                    # POs still pending (CHECK_ORDER_STATUS) - not failures, just waiting
                    logger.info(f"⏳ CNPJ {result['cnpj']} still pending → CHECK_ORDER_STATUS ({len(result['pos_pending'])} POs)")
            else:
                execution_summary["cnpjs_failed"] += 1
                logger.error(f"❌ CNPJ {entry['cnpj']} validation failed")

    # ═══════════════════════════════════════════════════════════════
    # BRANCH 3: Multi-Hop Pipeline (CLARO_GENERATED → UPLOADED)
    # ═══════════════════════════════════════════════════════════════
    if "multi_hop_pipeline_queue" in processing_queues:
        queue_info = processing_queues["multi_hop_pipeline_queue"]
        cnpjs = queue_info.get("cnpjs", [])
        pipeline_steps = queue_info.get("pipeline_steps", [])

        logger.info(f"🚀 Branch 3: Processing {len(cnpjs)} CNPJs via multi-hop pipeline...")

        for entry in cnpjs:
            pipeline_start = datetime.now(UTC)
            result = await execute_multi_hop_pipeline(entry, pipeline_steps, api_client)
            processed = result.get("processed_pos", [])
            failed = result.get("failed_pos", [])

            execution_summary["pipeline_executions"] += 1
            if failed:
                execution_summary["pipeline_failures"] += 1
            if processed and not failed:
                execution_summary["pipeline_completions"] += 1

            # Count minutas (POs) that completed the entire multihop pipeline
            if processed and not failed:
                execution_summary["minutas_concluidas"] += len(processed)
                execution_summary["minutas_processadas"] += len(processed)  # POs que mudaram status

            # Count minutas that failed in pipeline
            if failed:
                execution_summary["minutas_falharam"] += len(failed)

            if processed:
                execution_summary["cnpjs_updated"] += 1

            if failed:
                execution_summary["cnpjs_failed"] += 1

            execution_summary["total_value"] += result.get("total_value", 0.0)
            execution_summary["regional_downloads"] += result.get("regional_downloads", 0)

            pipeline_end = datetime.now(UTC)
            execution_summary["pipeline_execution_time_seconds"] += (
                pipeline_end - pipeline_start
            ).total_seconds()

    # Close API client
    await api_client.close_session()

    # Build results
    if execution_summary.get("pipeline_executions"):
        avg_minutes = execution_summary["pipeline_execution_time_seconds"] / execution_summary["pipeline_executions"] / 60
        execution_summary["pipeline_avg_time_minutes"] = round(avg_minutes, 2)
    else:
        execution_summary["pipeline_avg_time_minutes"] = 0.0

    processing_results = {
        "execution_summary": execution_summary,
        "processing_timestamp": datetime.now(UTC).isoformat()
    }

    set_session_state(step_input, "minuta_processing_results", processing_results)
    logger.info(
        f"✅ MINUTA processing completed: {execution_summary['po_completed']} POs concluídos, "
        f"{execution_summary['po_failed']} POs com falha"
    )

    return StepOutput(content=json.dumps(processing_results))


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS: Clean isolated implementations
# ═══════════════════════════════════════════════════════════════════════════════

async def execute_minutgen_only(
    cnpj_entry: dict,
    api_client: "BrowserAPIClient"
) -> dict:
    """Execute ONLY minutGen for a CNPJ (PENDING → CHECK_ORDER_STATUS)"""
    cnpj_claro = cnpj_entry.get("cnpj")
    json_file_path = cnpj_entry.get("json_file")

    if not cnpj_claro or not json_file_path:
        return {"success": False, "error": "Missing CNPJ or file path"}

    logger.info(f"📝 minutGen: {cnpj_claro}")

    # Load CNPJ group
    cnpj_group = load_cnpj_group_from_json(json_file_path, cnpj_claro)
    if not cnpj_group:
        return {"success": False, "error": "CNPJ not found in JSON"}

    # Execute minutGen
    payload = api_client.build_minut_gen_payload(cnpj_group)
    response = await api_client.execute_api_call("minutGen", payload)

    http_success = response.get("success", False)
    browser_success = response.get("api_result", {}).get("success", http_success)

    if http_success and browser_success:
        # Update status: PENDING → CHECK_ORDER_STATUS (awaiting claroCheck validation)
        await update_cnpj_status_in_json(
            json_file_path,
            cnpj_claro,
            MinutaProcessingStatus.CHECK_ORDER_STATUS
        )

        # Ensure per-PO statuses advance to CHECK_ORDER_STATUS
        try:
            for po_number in cnpj_group.get("po_list", []):
                await update_po_status_in_json(
                    json_file_path,
                    cnpj_claro,
                    str(po_number),
                    MinutaProcessingStatus.CHECK_ORDER_STATUS,
                    pipeline_progress={
                        "current_step": 0,
                        "total_steps": 5,
                        "last_step_completed": "minutGen",
                        "last_step_timestamp": datetime.now(UTC).isoformat(),
                        "failed_step": None
                    }
                )
        except Exception as exc:
            logger.warning(f"⚠️ Failed to update PO statuses after minutGen: {exc}")
        logger.info(f"✅ minutGen completed: {cnpj_claro} → CHECK_ORDER_STATUS (awaiting claroCheck)")
        return {"success": True}
    else:
        # Update status: FAILED_GENERATION
        await update_cnpj_status_in_json(
            json_file_path,
            cnpj_claro,
            MinutaProcessingStatus.FAILED_GENERATION
        )
        for po_number in cnpj_group.get("po_list", []):
            await update_po_status_in_json(
                json_file_path,
                cnpj_claro,
                str(po_number),
                MinutaProcessingStatus.FAILED_GENERATION,
                pipeline_progress={
                    "current_step": 1,
                    "total_steps": 5,
                    "last_step_completed": "main-minut-gen",
                    "last_step_timestamp": datetime.now(UTC).isoformat(),
                    "failed_step": "main-minut-gen"
                }
            )
        error_msg = response.get("api_result", {}).get("error") or response.get("error", "minutGen API failed")
        logger.error(f"❌ minutGen failed: {cnpj_claro} - {error_msg}")
        return {"success": False, "error": error_msg}


async def execute_claro_check_for_minuta(
    cnpj_entry: dict,
    api_client: "BrowserAPIClient"
) -> dict:
    """
    Execute claroCheck validation for MINUTA CNPJ.

    Validates each PO individually via claroCheck API. Transitions to CLARO_GENERATED
    ONLY when order is approved for invoice generation.

    Transitions:
    - Approved → CLARO_GENERATED (ready for multi-hop pipeline)
    - Still Pending → CHECK_ORDER_STATUS (remains for next run)

    Returns:
        {
            "success": bool,
            "cnpj": str,
            "status": str,  # Final CNPJ status
            "pos_checked": int,
            "pos_approved": list[str],
            "pos_pending": list[str],
            "error": str | None
        }
    """
    cnpj_claro = cnpj_entry.get("cnpj")
    json_file_path = cnpj_entry.get("json_file")
    pending_pos = cnpj_entry.get("pending_pos", [])

    if not cnpj_claro or not json_file_path:
        return {"success": False, "error": "Missing CNPJ or file path"}

    if not pending_pos:
        logger.warning(f"⚠️ No pending POs for CNPJ {cnpj_claro} - skipping claroCheck")
        return {"success": False, "error": "No pending POs"}

    logger.info(f"🔍 Executing claroCheck for CNPJ {cnpj_claro} ({len(pending_pos)} POs)...")

    # Load CNPJ group
    cnpj_group = load_cnpj_group_from_json(json_file_path, cnpj_claro)
    if not cnpj_group:
        return {"success": False, "error": "CNPJ not found in JSON"}

    pos_approved = []
    pos_still_pending = []

    # Check each PO individually
    for po_number in pending_pos:
        try:
            # Build payload
            payload = api_client.build_claro_check_payload(str(po_number))

            # Execute API call
            api_response = await api_client.execute_api_call("claroCheck", payload)

            if not api_response["success"]:
                logger.error(f"❌ claroCheck API call failed for PO {po_number}")
                pos_still_pending.append(str(po_number))
                continue

            # Parse response with MINUTA-specific logic
            browser_success, new_status, message = api_client.parse_claro_check_response_for_minuta(
                api_response.get("api_result", {})
            )

            if not browser_success:
                logger.error(f"❌ claroCheck validation failed for PO {po_number}: {message}")
                pos_still_pending.append(str(po_number))
                continue

            # Categorize by status
            if new_status == "CLARO_GENERATED":
                pos_approved.append(str(po_number))
                logger.info(f"✅ PO {po_number} APPROVED → ready for CLARO_GENERATED")
            elif new_status == "CHECK_ORDER_STATUS":
                pos_still_pending.append(str(po_number))
                logger.info(f"⏳ PO {po_number} STILL PENDING → retry next run")

            # Small delay between individual PO checks
            await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"❌ Exception checking PO {po_number}: {e}")
            pos_still_pending.append(str(po_number))

    # Determine CNPJ-level status
    if pos_approved and not pos_still_pending:
        # ALL POs approved → CLARO_GENERATED
        final_status = MinutaProcessingStatus.CLARO_GENERATED
        logger.info(f"🎉 All POs approved for CNPJ {cnpj_claro} → CLARO_GENERATED")
    elif pos_approved and pos_still_pending:
        # PARTIAL approval → remain CHECK_ORDER_STATUS
        final_status = MinutaProcessingStatus.CHECK_ORDER_STATUS
        logger.info(f"⏳ Partial approval for CNPJ {cnpj_claro} ({len(pos_approved)}/{len(pending_pos)} approved) → remains CHECK_ORDER_STATUS")
    else:
        # NO approvals → remain CHECK_ORDER_STATUS
        final_status = MinutaProcessingStatus.CHECK_ORDER_STATUS
        logger.info(f"⏳ No approvals yet for CNPJ {cnpj_claro} → remains CHECK_ORDER_STATUS")

    # Update JSON with new status
    await update_cnpj_status_in_json(
        json_file_path=json_file_path,
        cnpj_claro=cnpj_claro,
        new_status=final_status
    )

    # Update per-PO statuses
    try:
        for po_number in pos_approved:
            await update_po_status_in_json(
                json_file_path,
                cnpj_claro,
                str(po_number),
                MinutaProcessingStatus.CLARO_GENERATED,
                pipeline_progress={
                    "current_step": 1,
                    "total_steps": 5,
                    "last_step_completed": "claroCheck",
                    "last_step_timestamp": datetime.now(UTC).isoformat(),
                    "failed_step": None
                }
            )
        for po_number in pos_still_pending:
            await update_po_status_in_json(
                json_file_path,
                cnpj_claro,
                str(po_number),
                MinutaProcessingStatus.CHECK_ORDER_STATUS,
                pipeline_progress={
                    "current_step": 0,
                    "total_steps": 5,
                    "last_step_completed": "claroCheck",
                    "last_step_timestamp": datetime.now(UTC).isoformat(),
                    "failed_step": None
                }
            )
    except Exception as exc:
        logger.warning(f"⚠️ Failed to update PO statuses after claroCheck: {exc}")

    return {
        "success": True,
        "cnpj": cnpj_claro,
        "status": final_status.value,
        "pos_checked": len(pending_pos),
        "pos_approved": pos_approved,
        "pos_pending": pos_still_pending
    }


async def execute_multi_hop_pipeline(
    cnpj_entry: dict,
    pipeline_steps: list[dict],
    api_client: "BrowserAPIClient"
) -> dict:
    """Execute multi-hop pipeline: CLARO_GENERATED → UPLOADED with real-time status updates"""
    cnpj_claro = cnpj_entry.get("cnpj")
    json_file_path = cnpj_entry.get("json_file")

    if not cnpj_claro or not json_file_path:
        return {"success": False, "error": "Missing CNPJ or file path"}

    logger.info(f"🚀 Multi-hop pipeline: {cnpj_claro}")

    cnpj_group = load_cnpj_group_from_json(json_file_path, cnpj_claro)
    if not cnpj_group:
        return {"success": False, "error": "CNPJ not found in JSON"}

    status_sequence = [
        MinutaProcessingStatus.CLARO_GENERATED,
        MinutaProcessingStatus.ESL_GENERATED,
        MinutaProcessingStatus.DOWNLOADED,
        MinutaProcessingStatus.REGIONAL_DOWNLOADED,
        MinutaProcessingStatus.CONCATENATED,
        MinutaProcessingStatus.UPLOADED,
    ]

    def _status_index(status: MinutaProcessingStatus) -> int:
        try:
            return status_sequence.index(status)
        except ValueError:
            return -1

    po_status_map = cnpj_group.setdefault("po_status", {})
    po_groups = _group_minutas_by_po(cnpj_group)

    if not po_status_map:
        now_iso = datetime.now(UTC).isoformat()
        for po_num in po_groups.keys():
            po_status_map.setdefault(po_num, {
                "status": MinutaProcessingStatus.CLARO_GENERATED.value,
                "last_updated": now_iso
            })

    pending_pos = cnpj_entry.get("pending_pos") or []

    if not pending_pos:
        po_status_candidates = []
        for po, data in po_status_map.items():
            status_val = data.get("status", MinutaProcessingStatus.CLARO_GENERATED.value)
            try:
                status_enum = MinutaProcessingStatus(status_val)
            except ValueError:
                status_enum = MinutaProcessingStatus.CLARO_GENERATED
            if status_enum not in {MinutaProcessingStatus.UPLOADED, MinutaProcessingStatus.COMPLETED}:
                po_status_candidates.append(po)
        pending_pos = po_status_candidates

    if not pending_pos:
        pending_pos = list(po_groups.keys())

    if not pending_pos:
        logger.info(f"ℹ️ No pending POs for CNPJ {cnpj_claro}")
        return {"success": True, "processed_pos": [], "failed_pos": []}

    processed_pos: list[str] = []
    failed_pos: list[str] = []
    total_minutas = 0
    total_value = 0.0
    regional_downloads = 0

    for po_number in pending_pos:
        po_entry = po_status_map.get(po_number, {})
        status_value = po_entry.get("status", MinutaProcessingStatus.CLARO_GENERATED.value)
        try:
            current_status = MinutaProcessingStatus(status_value)
        except ValueError:
            current_status = MinutaProcessingStatus.CLARO_GENERATED

        current_idx = _status_index(current_status)
        logger.info(f"📦 Processing PO {po_number} (status {current_status.value})")

        po_groups = _group_minutas_by_po(cnpj_group)
        po_data_cached = po_groups.get(po_number, {})
        try:
            po_total_value = float(po_data_cached.get("total_value", 0.0))
        except (TypeError, ValueError):
            po_total_value = 0.0
        po_minuta_count = len(po_data_cached.get("minutas", []))
        po_entry.setdefault("value", round(po_total_value, 2))

        for step_config in pipeline_steps:
            step_num = step_config["step"]
            action = step_config["action"]
            next_status = MinutaProcessingStatus(step_config["next_status"])

            target_idx = _status_index(next_status)
            if current_idx >= 0 and target_idx >= 0 and current_idx >= target_idx:
                logger.info(f"⏭️ Step {step_num} skipped for PO {po_number}")
                await update_po_status_in_json(
                    json_file_path,
                    cnpj_claro,
                    po_number,
                    current_status,
                    pipeline_progress={
                        "current_step": step_num,
                        "total_steps": len(pipeline_steps),
                        "last_step_completed": action,
                        "last_step_timestamp": datetime.now(UTC).isoformat(),
                        "failed_step": None
                    }
                )
                continue

            if step_config.get("conditional") and not cnpj_group.get(step_config["conditional"], False):
                logger.info(f"⏭️ Conditional step {action} skipped for PO {po_number}")
                await update_po_status_in_json(
                    json_file_path,
                    cnpj_claro,
                    po_number,
                    current_status,
                    pipeline_progress={
                        "current_step": step_num,
                        "total_steps": len(pipeline_steps),
                        "last_step_completed": action,
                        "last_step_timestamp": datetime.now(UTC).isoformat(),
                        "failed_step": None
                    }
                )
                po_entry["pipeline_progress"] = {
                    "current_step": step_num,
                    "total_steps": len(pipeline_steps),
                    "last_step_completed": action,
                    "last_step_timestamp": datetime.now(UTC).isoformat(),
                    "failed_step": None
                }
                continue

            logger.info(f"📊 Step {step_num}/5 - {action} for PO {po_number}")
            success, result = await execute_pipeline_action(
                action,
                cnpj_group,
                json_file_path,
                api_client,
                po_number
            )

            if not success:
                logger.error(f"❌ Step {action} failed for PO {po_number}")
                await update_po_status_in_json(
                    json_file_path,
                    cnpj_claro,
                    po_number,
                    current_status,
                    pipeline_progress={
                        "current_step": step_num,
                        "total_steps": len(pipeline_steps),
                        "last_step_completed": action,
                        "last_step_timestamp": datetime.now(UTC).isoformat(),
                        "failed_step": action
                    }
                )
                po_entry["status"] = current_status.value
                po_entry["pipeline_progress"] = {
                    "current_step": step_num,
                    "total_steps": len(pipeline_steps),
                    "last_step_completed": action,
                    "last_step_timestamp": datetime.now(UTC).isoformat(),
                    "failed_step": action
                }
                failed_pos.append(po_number)
                break

            protocol = result.get("protocol") if step_config.get("extract_protocol") else None

            await update_po_status_in_json(
                json_file_path,
                cnpj_claro,
                po_number,
                next_status,
                pipeline_progress={
                    "current_step": step_num,
                    "total_steps": len(pipeline_steps),
                    "last_step_completed": action,
                    "last_step_timestamp": datetime.now(UTC).isoformat(),
                    "failed_step": None
                },
                protocol_number=protocol
            )

            po_entry["status"] = next_status.value
            po_entry["pipeline_progress"] = {
                "current_step": step_num,
                "total_steps": len(pipeline_steps),
                "last_step_completed": action,
                "last_step_timestamp": datetime.now(UTC).isoformat(),
                "failed_step": None
            }

            current_status = next_status
            current_idx = _status_index(current_status)

            if step_config.get("wait_time_seconds"):
                wait = step_config["wait_time_seconds"]
                if wait:
                    logger.info(f"⏳ Waiting {wait}s before next step for PO {po_number}")
                    await asyncio.sleep(wait)

            if result.get("regional"):
                regional_downloads += 1
        else:
            processed_pos.append(po_number)
            temp_store = cnpj_group.get("_po_temp", {})
            temp_store.pop(po_number, None)
            total_minutas += po_minuta_count
            total_value += po_total_value
            continue

        # Clean temp storage on failure before continuing to next PO
        temp_store = cnpj_group.get("_po_temp", {})
        temp_store.pop(po_number, None)

    # Update aggregated CNPJ status if all POs completed
    po_status_map = cnpj_group.get("po_status", {})
    if po_status_map:
        try:
            all_completed = all(
                MinutaProcessingStatus(po_data.get("status", MinutaProcessingStatus.CLARO_GENERATED.value))
                in {MinutaProcessingStatus.UPLOADED, MinutaProcessingStatus.COMPLETED}
                for po_data in po_status_map.values()
            )
        except ValueError:
            all_completed = False

        if all_completed:
            await update_cnpj_status_in_json(
                json_file_path,
                cnpj_claro,
                MinutaProcessingStatus.UPLOADED
            )

    return {
        "success": len(failed_pos) == 0,
        "processed_pos": processed_pos,
        "failed_pos": failed_pos,
        "minutas_count": total_minutas,
        "total_value": total_value,
        "regional_downloads": regional_downloads
    }


async def execute_pipeline_action(
    action: str,
    cnpj_group: dict,
    json_file_path: str,
    api_client: "BrowserAPIClient",
    po_number: str
) -> tuple[bool, dict]:
    """
    Execute single pipeline action and return (success, result_dict).
    Clean dispatcher aligned with plan - no overhead.
    """
    try:
        po_groups = _group_minutas_by_po(cnpj_group)
        po_data = po_groups.get(po_number)
        if po_data is None:
            return False, {"error": f"PO {po_number} not found in MINUTA JSON"}

        if action == "main-minut-gen":
            payload = api_client.build_main_minut_gen_payload(po_data, cnpj_group)
            response = await api_client.execute_api_call("main-minut-gen", payload)

            if response.get("success") and response.get("api_result", {}).get("success", True):
                return True, {
                    "minutas_count": len(po_data.get("minutas", [])),
                    "po": po_number
                }

            error_msg = response.get("api_result", {}).get("error") or response.get("error", "main-minut-gen failed")
            return False, {"error": error_msg}

        if action == "main-minut-download":
            payload = api_client.build_main_minut_download_payload(po_data, cnpj_group["cnpj_claro"], cnpj_group)
            response = await api_client.execute_api_call("main-minut-download", payload)

            if not response.get("success"):
                return False, {"error": "Download API failed"}

            api_result = response.get("api_result", {}) or {}
            raw_output = api_result.get("raw_response", {}).get("output", {}) if api_result.get("raw_response") else {}
            downloaded_files = api_result.get("downloadedFiles") or []

            pdf_path = api_result.get("file_path") or raw_output.get("file_path")
            if not pdf_path and downloaded_files:
                pdf_path = downloaded_files[0]

            if not pdf_path:
                return False, {"error": "No PDF path returned from Browser API"}

            pdf_path = str(pdf_path)
            if str(po_number) not in pdf_path:
                logger.warning(f"⚠️ Downloaded file name does not include PO {po_number}: {pdf_path}")

            temp_store = _get_po_temp_storage(cnpj_group, po_number)
            temp_store["base_pdf_paths"] = [pdf_path]
            temp_store.setdefault("base_pdf_filename", os.path.basename(pdf_path))
            return True, {"file_path": pdf_path}

        if action == "regional-download":
            uf = cnpj_group.get("uf")
            endpoint_map = {"TO": "main-minut-download-palmas", "SE": "main-minut-download-aracaju"}
            endpoint = endpoint_map.get(uf)

            if not endpoint:
                return True, {"skipped": True}

            payload = api_client.build_regional_download_payload(po_data, cnpj_group["cnpj_claro"], cnpj_group, uf.lower())
            response = await api_client.execute_api_call(endpoint, payload)
            if not response.get("success"):
                return False, {"error": "Regional download API failed"}

            api_result = response.get("api_result", {}) or {}
            raw_output = api_result.get("raw_response", {}).get("output", {}) if api_result.get("raw_response") else {}
            downloaded_files = api_result.get("downloadedFiles") or []

            regional_path = api_result.get("file_path") or raw_output.get("file_path")
            if not regional_path and downloaded_files:
                regional_path = downloaded_files[0]

            if not regional_path:
                return False, {"error": "No regional PDF path returned from Browser API"}

            regional_path = str(regional_path)
            temp_store = _get_po_temp_storage(cnpj_group, po_number)
            regional_paths = temp_store.get("regional_pdf_paths", [])
            regional_paths.append(regional_path)
            temp_store["regional_pdf_paths"] = regional_paths
            return True, {"file_path": regional_path, "regional": True}

        if action == "concatenate":
            temp_store = _get_po_temp_storage(cnpj_group, po_number)
            base_pdfs = temp_store.get("base_pdf_paths", [])
            regional_pdfs = temp_store.get("regional_pdf_paths", [])
            all_pdfs = base_pdfs + regional_pdfs

            if not all_pdfs:
                return False, {"error": "No PDFs to concatenate"}

            final_path = f"mctech/minutas/concatenated/final_{cnpj_group['cnpj_claro']}_{po_number}.pdf"
            concat_result = await concatenate_pdfs(all_pdfs, final_path)
            if not concat_result.get("success"):
                return False, {"error": concat_result.get("error", "Concatenation failed")}

            temp_store["final_pdf_path"] = final_path
            return True, {"file_path": final_path}

        if action == "invoiceUpload":
            temp_store = _get_po_temp_storage(cnpj_group, po_number)
            final_pdf = temp_store.get("final_pdf_path")
            if not final_pdf:
                return False, {"error": "No final PDF path"}

            payload = api_client.build_minuta_invoice_upload_payload(cnpj_group, final_pdf, po_number)
            response = await api_client.execute_api_call("invoiceUpload", payload)

            if response.get("success") and response.get("api_result", {}).get("success"):
                protocol = response.get("api_result", {}).get("protocol")
                return True, {"protocol": protocol, "file_path": final_pdf}

            return False, {"error": response.get("api_result", {}).get("error", "Upload API failed")}

        return False, {"error": f"Unknown action: {action}"}

    except Exception as e:
        logger.error(f"❌ Exception in {action}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, {"error": str(e)}


def _group_minutas_by_po(cnpj_group: dict) -> dict[str, dict]:
    """Helper: Group minutas by PO number"""
    po_groups = {}
    for minuta in cnpj_group.get("minutas", []):
        po_number = minuta.get("po")
        if not po_number:
            continue
        if po_number not in po_groups:
            po_groups[po_number] = {
                "po": po_number,
                "minutas": [],
                "total_value": 0.0,
                "start_date": cnpj_group.get("start_date"),
                "end_date": cnpj_group.get("end_date")
            }
        po_groups[po_number]["minutas"].append(minuta)
        try:
            po_groups[po_number]["total_value"] += float(minuta.get("valor", 0.0))
        except (TypeError, ValueError):
            pass
    return po_groups


def _get_po_temp_storage(cnpj_group: dict, po_number: str) -> dict:
    """Retrieve per-PO temporary storage container"""
    po_temp = cnpj_group.setdefault("_po_temp", {})
    return po_temp.setdefault(po_number, {
        "base_pdf_paths": [],
        "regional_pdf_paths": [],
        "final_pdf_path": None
    })


# Original execute_minuta_completion_step continues below (with WhatsApp notifications)


async def execute_minuta_completion_step(step_input: StepInput) -> StepOutput:
    """Complete MINUTA processing cycle with comprehensive metrics and WhatsApp notifications"""
    completion_start_time = datetime.now(UTC)
    logger.info("🏁 Starting MINUTA completion and notifications...")

    # Get MINUTA processing results
    previous_output = step_input.get_step_output("minuta_cnpj_processing")
    if not previous_output:
        logger.warning("⚠️ MINUTA processing step output not found - completion skipped")
        return StepOutput(content=json.dumps({"status": "SKIPPED", "reason": "No processing data"}))

    processing_results = json.loads(previous_output.content)

    # Handle placeholder case (real implementation will replace this)
    if processing_results.get("placeholder"):
        logger.warning("⚠️ MINUTA completion skipped - placeholder implementation")
        return StepOutput(content=json.dumps({
            "status": "SUCCESS",
            "message": "MINUTA completion skipped - placeholder",
            "completion_timestamp": datetime.now(UTC).isoformat()
        }))

    # Get session state for workflow timing
    session_state = get_session_state(step_input)
    minuta_start_time = session_state.get("minuta_start_time", completion_start_time)
    if isinstance(minuta_start_time, str):
        minuta_start_time = datetime.fromisoformat(minuta_start_time.replace("Z", "+00:00"))

    # Calculate execution time
    completion_end_time = datetime.now(UTC)
    execution_time_seconds = (completion_end_time - minuta_start_time).total_seconds()
    execution_time_minutes = round(execution_time_seconds / 60, 2)

    # Extract metrics from processing results
    execution_summary = processing_results.get("execution_summary", {})
    cnpj_groups_processed = execution_summary.get("cnpjs_updated", 0)
    cnpj_groups_failed = execution_summary.get("cnpjs_failed", 0)
    protocolos_gerados = execution_summary.get("protocolos_gerados", 0)
    pedidos_liberados = execution_summary.get("pedidos_liberados", 0)
    minutas_concluidas = execution_summary.get("minutas_concluidas", 0)
    minutas_processadas = execution_summary.get("minutas_processadas", 0)
    minutas_falharam = execution_summary.get("minutas_falharam", 0)
    regional_downloads = execution_summary.get("regional_downloads", 0)
    total_value = execution_summary.get("total_value", 0.0)
    pipeline_executions = execution_summary.get("pipeline_executions", 0)
    pipeline_completions = execution_summary.get("pipeline_completions", 0)
    pipeline_failures = execution_summary.get("pipeline_failures", 0)
    pipeline_avg_minutes = execution_summary.get("pipeline_avg_time_minutes", 0.0)

    # Extract CNPJ details for WhatsApp message
    cnpj_details = processing_results.get("cnpj_status_details", [])

    # Build comprehensive completion summary
    completion_summary = {
        "minuta_execution_summary": {
            "execution_date": datetime.now(UTC).strftime("%Y-%m-%d"),
            "execution_time_minutes": execution_time_minutes,
            "minuta_start_time": minuta_start_time.isoformat(),
            "minuta_end_time": completion_end_time.isoformat(),
            "overall_status": "SUCCESS"
        },
        "minuta_statistics": {
            "cnpj_groups_processed": cnpj_groups_processed,
            "cnpj_groups_failed": cnpj_groups_failed,
            "protocolos_gerados": protocolos_gerados,
            "pedidos_liberados": pedidos_liberados,
            "minutas_concluidas": minutas_concluidas,
            "minutas_processadas": minutas_processadas,
            "minutas_falharam": minutas_falharam,
            "regional_downloads": regional_downloads,
            "total_value": total_value,
            "pipeline_executions": pipeline_executions,
            "pipeline_completions": pipeline_completions,
            "pipeline_failures": pipeline_failures,
            "pipeline_avg_time_minutes": pipeline_avg_minutes,
            "success_rate": round((cnpj_groups_processed / max(cnpj_groups_processed + cnpj_groups_failed, 1)) * 100, 1)
        },
        "completion_timestamp": completion_end_time.isoformat()
    }

    # Log MINUTA-specific metrics with emoji prefixes
    logger.info("📋 ===== MINUTA PROCESSING COMPLETE =====")
    logger.info(f"✅ CNPJs processados: {cnpj_groups_processed}")
    logger.info(f"❌ CNPJs falharam: {cnpj_groups_failed}")
    logger.info(f"📄 Minutas processadas: {minutas_processadas}")
    logger.info(f"❌ Minutas falharam: {minutas_falharam}")
    logger.info(f"🔖 Protocolos gerados: {protocolos_gerados}")
    logger.info(f"📤 Pedidos liberados para emissão de NF: {pedidos_liberados}")
    logger.info(f"✅ Minutas concluídas: {minutas_concluidas}")
    logger.info(f"📍 Downloads regionais: {regional_downloads}")
    logger.info(f"💰 Valor total: R$ {total_value:,.2f}")
    logger.info(
        f"🔁 Pipelines executados: {pipeline_executions} | concluídos: {pipeline_completions} | falhas: {pipeline_failures}"
    )
    if pipeline_executions:
        logger.info(f"⏱️ Tempo médio pipeline: {pipeline_avg_minutes:.2f} minutos")
    logger.info(f"⏱️ Tempo execução: {execution_time_minutes:.1f} minutos")

    # Log CNPJ details if available
    if cnpj_details:
        logger.info(f"🔗 Status por CNPJ ({len(cnpj_details)} grupos):")
        for detail in cnpj_details[:5]:  # Log first 5 for visibility
            cnpj = detail.get("cnpj", "N/A")
            status = detail.get("status", "UNKNOWN")
            minutas_count = detail.get("minutas_count", 0)
            logger.info(f"   • {cnpj}: {minutas_count} minutas - {status}")

    # 📱 SEND WHATSAPP NOTIFICATION - MINUTA completion report
    try:
        import os as env_os
        omni_api_url = env_os.getenv("OMNI_API_URL")
        omni_api_key = env_os.getenv("OMNI_API_KEY")
        omni_phone_numbers_str = env_os.getenv("OMNI_PHONE_NUMBERS")

        if omni_api_url and omni_api_key and omni_phone_numbers_str:
            # Parse comma-separated phone numbers
            omni_phone_numbers = [phone.strip() for phone in omni_phone_numbers_str.split(",") if phone.strip()]

            # Build WhatsApp message using helper function
            whatsapp_message = build_minuta_whatsapp_message(
                cnpj_groups_processed=cnpj_groups_processed,
                cnpj_groups_failed=cnpj_groups_failed,
                protocolos_gerados=protocolos_gerados,
                pedidos_liberados=pedidos_liberados,
                minutas_concluidas=minutas_concluidas,
                minutas_processadas=minutas_processadas,
                minutas_falharam=minutas_falharam,
                regional_downloads=regional_downloads,
                total_value=total_value,
                execution_time=execution_time_minutes,
                cnpj_details=cnpj_details
            )

            # Log WhatsApp message before sending
            logger.info("📱 Mensagem WhatsApp MINUTA que será enviada:")
            logger.info("=" * 60)
            logger.info(whatsapp_message)
            logger.info("=" * 60)

            # Send WhatsApp notification via Omni API
            import requests

            logger.info(f"📱 Sending MINUTA completion via Omni API to {len(omni_phone_numbers)} recipients")

            url = omni_api_url
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {omni_api_key}",
                "Content-Type": "application/json"
            }

            # Send message to all phone numbers
            sent_count = 0
            failed_numbers = []

            for phone_number in omni_phone_numbers:
                try:
                    payload = {
                        "phone_number": phone_number,
                        "text": whatsapp_message
                    }

                    response = requests.post(url, json=payload, headers=headers, timeout=30)

                    if response.status_code in [200, 201]:
                        logger.info(f"📱 MINUTA message sent successfully to {phone_number}")
                        sent_count += 1
                    else:
                        logger.error(f"❌ Failed to send MINUTA message to {phone_number}: HTTP {response.status_code}")
                        failed_numbers.append(phone_number)

                except Exception as e:
                    logger.error(f"❌ Error sending MINUTA message to {phone_number}: {e}")
                    failed_numbers.append(phone_number)

            if sent_count > 0:
                logger.info(f"📱 MINUTA completion notification sent to {sent_count}/{len(omni_phone_numbers)} recipients")
                completion_summary["whatsapp_notification"] = {
                    "sent": True,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "recipients_total": len(omni_phone_numbers),
                    "recipients_success": sent_count,
                    "recipients_failed": len(failed_numbers),
                    "failed_numbers": failed_numbers,
                    "message_preview": whatsapp_message[:100] + "..."
                }
            else:
                logger.error(f"❌ Failed to send MINUTA notification to all {len(omni_phone_numbers)} numbers")
                completion_summary["whatsapp_notification"] = {
                    "sent": False,
                    "error": f"Failed to send to all {len(omni_phone_numbers)} recipients",
                    "failed_numbers": failed_numbers
                }
        else:
            logger.warning("⚠️ Omni API credentials not configured - WhatsApp notification skipped")
            completion_summary["whatsapp_notification"] = {
                "sent": False,
                "error": "Omni API credentials not configured"
            }

    except Exception as e:
        logger.error(f"❌ Error sending MINUTA WhatsApp notification: {e}")
        completion_summary["whatsapp_notification"] = {
            "sent": False,
            "timestamp": datetime.now(UTC).isoformat(),
            "error": str(e)
        }

    # MINUTA-specific error alerts
    if cnpj_groups_failed > 0:
        logger.error(f"🚨 MINUTA ERROR ALERT: {cnpj_groups_failed} CNPJ groups failed processing")

        # Log specific failure types
        failure_details = processing_results.get("failure_details", {})
        if "rate_limit_exceeded" in failure_details:
            logger.error(f"🚨 ReceitaWS rate limit exceeded: {failure_details['rate_limit_exceeded']} occurrences")
        if "regional_download_failed" in failure_details:
            logger.error(f"🚨 Regional download failures: {failure_details['regional_download_failed']} occurrences")
        if "pdf_concatenation_failed" in failure_details:
            logger.error(f"🚨 PDF concatenation failures: {failure_details['pdf_concatenation_failed']} occurrences")
        if "cnpj_lookup_failed" in failure_details:
            logger.error(f"🚨 CNPJ lookup failures: {failure_details['cnpj_lookup_failed']} occurrences")

    logger.info("🏁 MINUTA processing and notification completed!")

    return StepOutput(content=json.dumps(completion_summary))


async def execute_database_sync_step(step_input: StepInput) -> StepOutput:
    """
    🗄️ FINAL STEP: Synchronize CTE + MINUTA JSON files to PostgreSQL database

    This step MUST ALWAYS BE THE FINAL STEP in the workflow to ensure:
    - Jack retrieval agent has access to latest data
    - Real-time data queries reflect current status
    - Database state matches JSON file contents

    ⚠️ CRITICAL: DO NOT ADD STEPS AFTER THIS ONE - New steps must be added BEFORE this step
    """
    sync_start_time = datetime.now(UTC)
    logger.info("🗄️ Starting database synchronization - FINAL STEP (CTE + MINUTA)")

    try:
        # Get database URL from environment
        database_url = os.getenv("HIVE_DATABASE_URL")
        if not database_url:
            raise ValueError("HIVE_DATABASE_URL environment variable not set")

        # Initialize CTE processor (handles both CTE and MINUTA)
        processor = CTEProcessor(database_url)

        # Process CTE JSON files
        cte_directory = "mctech/ctes"
        await processor.process_directory(cte_directory)
        cte_count = await processor.get_order_count()

        # Process MINUTA JSON files
        minuta_directory = "mctech/minutas"
        await processor.process_minuta_directory(minuta_directory)
        minuta_count = await processor.get_minuta_count()

        sync_end_time = datetime.now(UTC)
        execution_time = (sync_end_time - sync_start_time).total_seconds()

        result = {
            "status": "SUCCESS",
            "database_sync_completed": True,
            "cte_directory": cte_directory,
            "minuta_directory": minuta_directory,
            "total_cte_orders_in_database": cte_count,
            "total_minuta_cnpjs_in_database": minuta_count,
            "sync_execution_time_seconds": execution_time,
            "sync_timestamp": sync_end_time.isoformat(),
            "message": f"✅ Database synchronized: {cte_count} CTE orders + {minuta_count} MINUTA CNPJs available for jack_retrieval queries."
        }

        logger.info(f"✅ Database sync completed: {cte_count} CTEs + {minuta_count} MINUTAs in {execution_time:.2f}s")
        
        return StepOutput(content=json.dumps(result, indent=2))
        
    except Exception as e:
        sync_end_time = datetime.now(UTC)
        execution_time = (sync_end_time - sync_start_time).total_seconds()
        
        error_result = {
            "status": "FAILED",
            "database_sync_completed": False,
            "error": str(e),
            "sync_execution_time_seconds": execution_time,
            "sync_timestamp": sync_end_time.isoformat(),
            "message": f"❌ Database synchronization failed: {e}"
        }
        
        logger.error(f"❌ Database sync failed: {e}")
        
        # Don't raise the exception - return the error info instead
        # This allows the workflow to complete and report the sync failure
        return StepOutput(content=json.dumps(error_result, indent=2))


# Factory function to create ProcessamentoFaturas workflow
def get_processamento_faturas_workflow(**kwargs) -> Workflow:
    """Factory function to create ProcessamentoFaturas daily scheduled workflow with CTE + MINUTA processing"""

    # Create workflow with daily execution: CTE processing followed by MINUTA processing (sequential)
    workflow = Workflow(
        name="processamento_faturas",
        description="Daily scheduled CTE + MINUTA invoice processing with sequential execution: CTE completes first, then MINUTA processing begins",
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
                description="Update CTE JSON files with new statuses and schedule next execution",
                executor=execute_daily_completion_step,
                max_retries=1,
            ),
            # ═══════════════════════════════════════════════════════════════
            # MINUTA PROCESSING PIPELINE (Sequential - Runs AFTER CTE)
            # ═══════════════════════════════════════════════════════════════
            Step(
                name="minuta_json_analysis",
                description="📋 Analyze MINUTA JSON files and categorize CNPJ groups by status",
                executor=execute_minuta_json_analysis_step,
                max_retries=2,
            ),
            Step(
                name="minuta_status_routing",
                description="📋 Route CNPJ groups to appropriate MINUTA processing actions based on status",
                executor=execute_minuta_status_routing_step,
                max_retries=2,
            ),
            Step(
                name="minuta_cnpj_processing",
                description="📋 Process MINUTA CNPJ groups through API calls (minutGen → main-minut-gen → downloads → concatenation → upload)",
                executor=execute_minuta_cnpj_processing_step,
                max_retries=3,
            ),
            Step(
                name="minuta_completion",
                description="📋 Update MINUTA JSON files with final statuses and send WhatsApp notifications",
                executor=execute_minuta_completion_step,
                max_retries=1,
            ),
            # ═══════════════════════════════════════════════════════════════
            # DATABASE SYNC (Final Step - Syncs Both CTE + MINUTA)
            # ═══════════════════════════════════════════════════════════════
            Step(
                name="database_sync",
                description="🗄️ FINAL STEP: Synchronize all CTE + MINUTA JSON data to PostgreSQL database for jack_retrieval agent queries. ⚠️ MUST ALWAYS BE THE FINAL STEP - DO NOT ADD STEPS AFTER THIS ONE",
                executor=execute_database_sync_step,
                max_retries=2,
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
        - Execute status-based processing: PENDING → CHECK_ORDER_STATUS → WAITING_MONITORING → MONITORED → DOWNLOADED → UPLOADED
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
