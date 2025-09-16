# Invoice Email Workflow Implementation Plan

## Executive Summary
Implement automated email sending after successful invoice upload, including protocol-based ZIP renaming and status completion tracking.

## Current State Analysis

### ✅ Available Data
- **PO Number**: `po_number` field in JSON
- **Cliente Name**: `empresa_origem` field in JSON
- **ZIP Files**: Downloaded to `mctech/downloads/pedido {po}.zip`
- **Protocol Number**: Returned by `invoiceUpload` browser agent (not captured)

### ❌ Missing Components
- Email sending functionality in Gmail library
- Protocol number capture from upload response
- ZIP file splitting and renaming logic
- COMPLETED status transition

## KISS Implementation Plan

### Phase 1: Capture Protocol Number (30 mins)
**File**: `ai/workflows/processamento-faturas/workflow.py`

1. **Parse Upload Response**
   ```python
   # In parse_invoice_upload_response() - NEW METHOD
   def parse_invoice_upload_response(self, api_response: dict) -> tuple[bool, str, str]:
       """Extract protocol from invoiceUpload response"""
       raw_response = api_response.get("raw_response", {})
       browser_output = raw_response.get("output", {})
       protocol = browser_output.get("protocol", "")

       if protocol:
           return True, protocol, "Upload successful with protocol"
       return False, "", "Upload failed - no protocol"
   ```

2. **Store Protocol in JSON**
   ```python
   # Add import at top of workflow.py
   from datetime import datetime, UTC

   # Add protocol field when updating status to UPLOADED
   order["protocol_number"] = protocol
   order["status"] = "UPLOADED"
   order["last_updated"] = datetime.now(UTC).isoformat()
   ```

### Phase 2: Create Email Sender (45 mins)
**File**: `lib/gmail/sender.py` (NEW)

```python
import os
import mimetypes
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from dataclasses import dataclass

from .auth import GmailAuthenticator
from lib.logging import logger

@dataclass
class EmailResult:
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None

class GmailSender:
    """Robust email sender using existing Gmail authentication"""

    def __init__(self, authenticator=None):
        self.authenticator = authenticator or GmailAuthenticator()
        self.service = self.authenticator.get_gmail_service()

    def send_invoice_email(self, to_email: str, po_number: str,
                           protocol: str, cliente: str, attachments: List[str]) -> EmailResult:
        """Send invoice email with ZIP attachments"""
        try:
            # Create email subject and body
            subject = f"Pedido {po_number} protocolo {protocol}"
            body = f"Segue kit referente ao protocolo {protocol} e cliente {cliente}"

            logger.info(f"📧 Sending email to: {to_email}")
            logger.info(f"📋 Subject: {subject}")
            logger.info(f"📎 Attachments: {len(attachments)} files")

            # Use robust email sending method
            result = self.send_email_with_attachments(
                to=to_email,
                subject=subject,
                message=body,
                attachment_paths=attachments,
                content_type="text/plain"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Failed to send invoice email: {str(e)}")
            return EmailResult(success=False, error=str(e))

    def send_email_with_attachments(self, to: str, subject: str, message: str,
                                   attachment_paths: List[str], content_type: str = "text/plain",
                                   cc: Optional[List[str]] = None) -> EmailResult:
        """Robust email sending with multiple attachments"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['to'] = to
            msg['subject'] = subject

            if cc:
                msg['cc'] = ', '.join(cc)

            # Add body
            msg.attach(MIMEText(message, content_type.split('/')[-1]))

            # Add attachments
            for file_path in attachment_paths:
                if not os.path.exists(file_path):
                    logger.warning(f"⚠️ Attachment not found: {file_path}")
                    continue

                self._attach_file(msg, file_path)

            # Send email
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            message_id = result.get('id')
            logger.info(f"✅ Email sent successfully! Message ID: {message_id}")

            return EmailResult(success=True, message_id=message_id)

        except Exception as e:
            logger.error(f"❌ Failed to send email: {str(e)}")
            return EmailResult(success=False, error=str(e))

    def _attach_file(self, msg: MIMEMultipart, file_path: str) -> None:
        """Attach file to email message"""
        try:
            # Guess the content type based on the file's extension
            ctype, encoding = mimetypes.guess_type(file_path)
            if ctype is None or encoding is not None:
                ctype = 'application/octet-stream'

            main_type, sub_type = ctype.split('/', 1)

            with open(file_path, 'rb') as fp:
                attachment = MIMEBase(main_type, sub_type)
                attachment.set_payload(fp.read())

            # Encode file in ASCII characters to send by email
            encoders.encode_base64(attachment)

            # Add header as key/value pair to attachment part
            filename = os.path.basename(file_path)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename= "{filename}"'
            )

            msg.attach(attachment)
            logger.debug(f"📎 Attached file: {filename} ({ctype})")

        except Exception as e:
            logger.error(f"❌ Failed to attach file {file_path}: {str(e)}")
            raise
```

### Phase 3: ZIP Processing Logic (45 mins)
**File**: `ai/workflows/processamento-faturas/workflow.py`

```python
import os
import zipfile
import glob
import shutil

def process_invoice_zips(self, po_number: str, protocol: str) -> dict:
    """Extract and rename ZIP files with protocol"""

    # Find downloaded ZIP
    original_zip = f"mctech/downloads/pedido {po_number}.zip"

    # Extract to temp directory (create if needed)
    temp_dir = f"mctech/temp/{po_number}"
    os.makedirs(temp_dir, exist_ok=True)  # FIX: Create temp directory

    with zipfile.ZipFile(original_zip, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    # Create 3 new ZIPs with protocol naming
    attachments = []

    # 1. Fatura ZIP (preserve original filename + add protocol)
    fatura_files = glob.glob(f"{temp_dir}/Fatura/*")
    if fatura_files:
        # Get original fatura filename (without extension and path)
        original_fatura = os.path.basename(fatura_files[0])  # e.g., "fatura_abc123.pdf"
        fatura_name = os.path.splitext(original_fatura)[0]   # e.g., "fatura_abc123"
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

    # Cleanup temp directory
    shutil.rmtree(temp_dir)

    return {"attachments": attachments}

def _create_zip(self, files: list, output_path: str) -> None:
    """Helper to create ZIP from file list"""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files:
            zipf.write(file_path, os.path.basename(file_path))
```

### Phase 4: Workflow Integration (30 mins)
**File**: `ai/workflows/processamento-faturas/workflow.py`

1. **Add Email Queue to Processing Queues**
   ```python
   # In status_based_routing() - Add to processing_queues dict
   "processing_queues": {
       # ... existing queues (invoice_generation_queue, etc.)
       "email_queue": {
           "action": "sendEmail",
           "pos": processing_categories["completed_pos"],  # UPLOADED status POs
           "batch_processing": False,
           "priority": 5
       }
   }
   ```

2. **Handle COMPLETED Status in JSON Analysis**
   ```python
   # In json_analysis step - Add new status handling
   elif status == "COMPLETED":
       # Don't add to any processing category - truly done
       file_stats["completed"] += 1  # Just count them
       # Note: Don't set needs_processing = True for COMPLETED
   ```

3. **Add Email Action Handler**
   ```python
   # Add import at top of workflow.py
   from lib.gmail.sender import GmailSender

   # In individual_po_processing() - Add to existing action handling
   elif action == "sendEmail":
       # Get protocol from JSON
       protocol = po_details.get("protocol_number")

       if not protocol:
           logger.error(f"❌ No protocol found for PO {po_number}")
           processing_results["failed_orders"][po_number] = {
               "action": action,
               "failure_type": "missing_protocol",
               "error": "No protocol number in JSON",
               "json_file": json_file
           }
           continue

       cliente = po_details["ctes"][0]["empresa_origem"]

       # Process ZIPs
       zip_result = api_client.process_invoice_zips(po_number, protocol)

       # Send email
       sender = GmailSender()
       email_result = sender.send_invoice_email(
           to_email="dnl-fretes@claro.com.br",
           po_number=po_number,
           protocol=protocol,
           cliente=cliente,
           attachments=zip_result["attachments"]
       )

       # Update status based on email result using string literals (matching codebase pattern)
       if email_result.success:
           logger.info(f"✅ Email sent successfully for PO {po_number}")
           new_status = "COMPLETED"
           processing_results["status_updates"][po_number] = {
               "old_status": "UPLOADED",
               "new_status": new_status,
               "json_file": json_file
           }
           processing_results["execution_summary"]["successful_actions"] += 1
           processing_results["execution_summary"]["pos_updated"] += 1
       else:
           logger.error(f"❌ Email failed for PO {po_number}: {email_result.error}")
           processing_results["failed_orders"][po_number] = {
               "action": action,
               "failure_type": "email_failure",
               "error": email_result.error,
               "json_file": json_file
           }
           processing_results["execution_summary"]["failed_actions"] += 1
           processing_results["execution_summary"]["pos_failed"] += 1
   ```

### Phase 5: Status Completion (15 mins)

1. **Add New Status Constants**
   ```python
   # In POStatus class - add new statuses
   FAILED_EMAIL = "failed_email"
   # Note: COMPLETED already exists but ensure it's used properly
   ```

2. **Update Status Transitions**
   ```python
   # Status flow
   UPLOADED (in completed_pos) → sendEmail → COMPLETED or FAILED_EMAIL
   ```

3. **Update Final Report**
   ```python
   # In daily_completion()
   "pos_completed_today": len([po for po in updates
                               if po["new_status"] == "COMPLETED"])
   ```

4. **Make completed_pos Actionable**
   ```python
   # In json_analysis when status == "UPLOADED"
   file_stats["needs_processing"] = True  # Critical - trigger processing!
   ```

**Benefits of FAILED_EMAIL Status:**
- ✅ **Automatic categorization** into `failed_pos` for retry handling
- ✅ **Consistent error tracking** following existing pattern
- ✅ **Clear separation** between successful completion and email failures
- ✅ **Retry capability** - FAILED_EMAIL POs can be retried on next run

## Implementation Order

1. **Step 1**: Create `GmailSender` class (45 mins)
2. **Step 2**: Add protocol parsing to upload response (30 mins)
3. **Step 3**: Implement ZIP processing logic (45 mins)
4. **Step 4**: Integrate email workflow (30 mins)
5. **Step 5**: Test and validate (30 mins)

**Total Time**: ~3 hours

## Testing Checklist

- [ ] Protocol extracted from upload response
- [ ] Protocol saved to JSON file
- [ ] ZIP files correctly split into 3 categories
- [ ] Files renamed with protocol number
- [ ] Email sent with correct subject and body
- [ ] All 3 ZIP attachments included
- [ ] Status transitions to COMPLETED
- [ ] Final report shows completed count

## Risk Mitigation

1. **Email Recipient**: Currently hardcoded - needs configuration
2. **Error Handling**: Add try/catch for email failures
3. **Retry Logic**: Implement retry for transient failures
4. **Protocol Missing**: Fallback to manual intervention

## Success Criteria

✅ Automated email sending after upload
✅ Protocol-based file naming
✅ Correct email format and attachments
✅ Status properly transitions to COMPLETED
✅ No manual intervention required