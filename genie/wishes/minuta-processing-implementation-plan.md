# 🗺️ MINUTA Processing Pipeline - Complete Implementation Plan

**Date:** 2025-02-11
**Status:** Architecture Planning Phase
**Target:** Add MINUTA processing to existing CTE workflow

---

## 📋 Executive Summary

This document outlines the complete architecture for adding MINUTA invoice processing to the existing `processamento-faturas` workflow. MINUTAs will be processed **sequentially AFTER** all CTE processing completes, using a separate but parallel pipeline structure.

---

## 🎯 Requirements Recap

### Business Requirements
1. ✅ Process MINUTAs from the **same Excel files** as CTEs
2. ✅ Filter by `TIPO == 'MINUTA'` (separate from `TIPO == 'CTE'`)
3. ✅ Group by **CNPJ Claro** (not by PO like CTEs)
4. ✅ Execute **sequentially AFTER** all CTE processing completes
5. ✅ Different API flow: `minutGen → main-minut-gen → main-minut-download → [conditional regional] → invoiceUpload`
6. ✅ Regional conditional downloads based on state (Tocantins/Sergipe)
7. ✅ PDF concatenation for base + regional PDFs
8. ✅ Database sync for jack_retrieval agent access

### Technical Specifications

#### Excel Columns Required for MINUTA
```python
REQUIRED_COLUMNS = [
    "CNPJ Claro",        # Grouping key
    "Valor",             # Invoice value
    "TIPO",              # Filter: must be 'MINUTA'
    "PO",                # Purchase order number
    "Competência",       # Date for range calculation
    "Empresa Origem"     # Company name
]
```

#### API Payload Specifications

**1. minutGen (Claro System)**
```json
{
  "flow_name": "minutGen",
  "parameters": {
    "orders": ["600705814", "600705857"],  // Batched by same CNPJ
    "city": "SALVADOR",  // From ReceitaWS API
    "headless": false
  }
}
```

**2. main-minut-gen (ESL System)**
```json
{
  "flow_name": "main-minut-gen",
  "parameters": {
    "po": "600705814",
    "minutes": ["16159"],  // Array of MINUTA numbers
    "total_value": 1042.98,
    "startDate": "01/06/2025",
    "endDate": "30/08/2025",
    "headless": false
  }
}
```

**3. main-minut-download (ESL System)**
```json
{
  "flow_name": "main-minut-download",
  "parameters": {
    "po": "600705857",
    "minutes": ["16084"],
    "total_value": 94.74,
    "cnpj": "66970229001805",  // CNPJ Claro (no formatting)
    "headless": false
  }
}
```
**Output:** Returns PDF file via binary response

**4. main-minut-download-palmas (Tocantins Regional)**
```json
{
  "flow_name": "main-minut-download-palmas",
  "parameters": {
    "po": "600705857",
    "minutes": ["16084"],
    "total_value": 94.74,
    "cnpj": "66970229001805",
    "headless": false
  }
}
```
**Output:** Returns PDF file via binary response

**5. main-minut-download-aracaju (Sergipe Regional)**
```json
{
  "flow_name": "main-minut-download-aracaju",
  "parameters": {
    "po": "600705857",
    "minutes": ["16084"],
    "total_value": 94.74,
    "cnpj": "66970229001805",
    "headless": false
  }
}
```
**Output:** Returns PDF file via binary response

**6. invoiceUpload (Same as CTE)**
```json
{
  "flow_name": "invoiceUpload",
  "parameters": {
    "po": "600705857",
    "invoice": "<base64_encoded_concatenated_pdf>",
    "invoice_filename": "minuta_66970229001805.pdf",
    "headless": false
  }
}
```

---

## 🏗️ Architecture Overview

### High-Level Flow Diagram

```
┌────────────────────────────────────────────────────────────────┐
│ INITIALIZATION (Modified)                                      │
│ ─────────────────────────────────────────────────────────────  │
│ Download Email → Excel → Split by TIPO:                        │
│   ├─ TIPO=='CTE' → mctech/ctes/ctes_DATE.json                │
│   └─ TIPO=='MINUTA' → mctech/minutas/minutas_DATE.json       │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ CTE PROCESSING (Existing - Unchanged)                          │
│ ─────────────────────────────────────────────────────────────  │
│ Steps 2-5: Process all CTEs through complete lifecycle         │
│ Status: PENDING → ... → UPLOADED → COMPLETED                   │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ MINUTA PROCESSING (New Sequential Pipeline)                    │
│ ─────────────────────────────────────────────────────────────  │
│ Step 6: minuta_json_analysis                                   │
│ Step 7: minuta_status_routing                                  │
│ Step 8: minuta_cnpj_processing                                 │
│ Step 9: minuta_completion                                      │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ DATABASE SYNC (Modified)                                       │
│ ─────────────────────────────────────────────────────────────  │
│ Step 10: Sync both CTE + MINUTA data to PostgreSQL            │
│ ⚠️ MUST REMAIN FINAL STEP                                     │
└────────────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure

### Directory Organization

```
mctech/
├── sheets/                          # Original Excel files
│   └── upload_11-09-2025.xlsx
│
├── ctes/                            # CTE JSONs (existing)
│   └── ctes_11-09-2025_14h30.json
│
├── minutas/                         # MINUTA JSONs (new)
│   ├── minutas_11-09-2025_14h30.json    # Consolidated MINUTA data
│   ├── downloads/                        # Base PDF downloads
│   │   └── minuta_66970229001805.pdf
│   ├── regional/                         # Regional PDFs
│   │   ├── palmas_66970229001805.pdf
│   │   └── aracaju_66970229001805.pdf
│   └── concatenated/                     # Final merged PDFs
│       └── final_66970229001805.pdf
│
├── downloads/                       # CTE downloads (existing)
└── temp/                           # Temporary processing
```

### MINUTA JSON Schema

**File:** `mctech/minutas/minutas_11-09-2025_14h30.json`

```json
{
  "batch_info": {
    "batch_id": "daily_20250211_143022",
    "source_file": "mctech/sheets/upload_11-09-2025.xlsx",
    "processing_timestamp": "2025-02-11T14:30:22Z",
    "total_minutas": 45,
    "total_ctes_excluded": 128
  },
  "cnpj_groups": [
    {
      "cnpj_claro": "66970229001805",
      "cnpj_claro_formatted": "66.970.229/0018-05",
      "empresa_origem": "CLARO S.A.",
      "status": "PENDING",

      // City/State data from ReceitaWS API
      "city": "SALVADOR",
      "state": "BA",
      "municipio": "SALVADOR",
      "uf": "BA",

      // Aggregated MINUTA data
      "minutas": [
        {
          "po": "600705814",
          "nf_cte": "16159",
          "valor": 1042.98,
          "data_original": 45678,
          "competencia": "2025-06-18"
        },
        {
          "po": "600705857",
          "nf_cte": "16084",
          "valor": 94.74,
          "data_original": 45678,
          "competencia": "2025-06-18"
        }
      ],

      // Aggregated metrics
      "minuta_count": 2,
      "total_value": 1137.72,
      "po_list": ["600705814", "600705857"],
      "start_date": "01/06/2025",
      "end_date": "30/08/2025",

      // Regional download flags
      "requires_regional": true,
      "regional_type": null,  // "palmas", "aracaju", or null

      // Processing metadata
      "created_at": "2025-02-11T14:30:22Z",
      "last_updated": "2025-02-11T14:30:22Z",
      "protocol_number": null,  // Set after upload

      // File tracking
      "pdf_files": {
        "base": null,
        "regional": null,
        "concatenated": null
      }
    }
  ],
  "summary": {
    "total_cnpj_groups": 15,
    "total_minutas": 45,
    "total_value": 125000.00,
    "total_pos": 23
  }
}
```

---

## 🔄 MINUTA Status Flow

### Status Enum Definition

```python
class MinutaProcessingStatus(Enum):
    """MINUTA Processing Status Enum - Separate pipeline from CTE"""
    PENDING = "PENDING"                              # Initial state
    WAITING_GENERATION = "WAITING_GENERATION"        # After minutGen
    GENERATED = "GENERATED"                          # After main-minut-gen
    WAITING_DOWNLOAD = "WAITING_DOWNLOAD"           # Ready for download
    DOWNLOADED = "DOWNLOADED"                        # Base PDF downloaded
    WAITING_REGIONAL_DOWNLOAD = "WAITING_REGIONAL"  # Needs Palmas/Aracaju
    REGIONAL_DOWNLOADED = "REGIONAL_DOWNLOADED"      # Regional PDF downloaded
    PDF_CONCATENATED = "PDF_CONCATENATED"            # PDFs merged
    UPLOADED = "UPLOADED"                            # Upload completed
    COMPLETED = "COMPLETED"                          # Final state

    # Failure states
    FAILED_GENERATION = "FAILED_GENERATION"
    FAILED_DOWNLOAD = "FAILED_DOWNLOAD"
    FAILED_REGIONAL_DOWNLOAD = "FAILED_REGIONAL_DOWNLOAD"
    FAILED_CONCATENATION = "FAILED_CONCATENATION"
    FAILED_UPLOAD = "FAILED_UPLOAD"
```

### Status Transition Flow

```
PENDING
   ↓ minutGen (Claro) - batched by CNPJ
WAITING_GENERATION
   ↓ main-minut-gen (ESL) - per CNPJ group
GENERATED
   ↓ main-minut-download (ESL) - per CNPJ group
DOWNLOADED
   ↓ Check state (UF)
   ├─ IF UF == "TO" → main-minut-download-palmas
   ├─ IF UF == "SE" → main-minut-download-aracaju
   └─ ELSE → skip regional
   ↓
REGIONAL_DOWNLOADED (or skip to PDF_CONCATENATED)
   ↓ Concatenate PDFs (base + regional)
PDF_CONCATENATED
   ↓ invoiceUpload with concatenated PDF
UPLOADED
   ↓ [Future: Send email with attachments]
COMPLETED
```

---

## 🆕 New Workflow Steps (Detailed)

### Step 1 Modification: `execute_daily_initialization_step`

**Changes Required:**
1. Create **TWO** JSON files from same Excel:
   - `mctech/ctes/ctes_DATE.json` (existing)
   - `mctech/minutas/minutas_DATE.json` (new)

2. Add `process_excel_to_minuta_json()` function

**Implementation:**

```python
async def execute_daily_initialization_step(step_input: StepInput) -> StepOutput:
    """Initialize daily processing - creates BOTH CTE and MINUTA JSONs"""

    # ... existing Gmail download logic ...

    for file_info in downloaded_files:
        excel_path = file_info["path"]
        email_datetime = file_info.get('email_date')

        # Process CTEs (existing)
        cte_json_path = f"mctech/ctes/ctes_{email_datetime}.json"
        cte_success, cte_error = await process_excel_to_json(
            excel_path, cte_json_path, daily_batch_id
        )

        # Process MINUTAs (new)
        minuta_json_path = f"mctech/minutas/minutas_{email_datetime}.json"
        minuta_success, minuta_error = await process_excel_to_minuta_json(
            excel_path, minuta_json_path, daily_batch_id
        )

        new_emails_processed.append({
            "cte_json_created": cte_success,
            "minuta_json_created": minuta_success,
            "cte_error": cte_error,
            "minuta_error": minuta_error
        })

    # Scan for existing MINUTA JSONs
    existing_minuta_json_files = glob.glob("mctech/minutas/minutas_*.json")

    initialization_results = {
        # ... existing fields ...
        "minuta_json_files_found": existing_minuta_json_files,
        "total_minuta_files": len(existing_minuta_json_files)
    }

    return StepOutput(content=json.dumps(initialization_results))
```

---

### New Helper: `process_excel_to_minuta_json()`

**Purpose:** Convert Excel → MINUTA JSON grouped by CNPJ Claro

**Implementation:**

```python
async def process_excel_to_minuta_json(
    excel_path: str,
    json_path: str,
    batch_id: str
) -> tuple[bool, dict | None]:
    """
    Process Excel file and create MINUTA JSON grouped by CNPJ Claro

    Returns: (success: bool, validation_error: dict | None)
    """
    try:
        import pandas as pd
        import os

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
        valor_column = 'valor CHAVE' if 'valor CHAVE' in available_columns else 'Valor'

        # Find CNPJ Claro column (with variations)
        cnpj_column = None
        for possible_name in ['CNPJ Claro', 'CNPJ CLARO', 'CNPJ_CLARO', 'cnpj_claro']:
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

        logger.info(f"✅ All required MINUTA columns validated")

        # Filter ONLY MINUTA records
        minuta_df = df[df['TIPO'] == 'MINUTA'].copy()
        logger.info(f"🔍 Filtered MINUTAs: {len(minuta_df)} records (excluded {len(df) - len(minuta_df)} CTE records)")

        if minuta_df.empty:
            error_msg = f"No MINUTA records found in Excel file (only CTEs or empty)"
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
        for cnpj_claro, group in minuta_df.groupby(cnpj_column):
            if pd.isna(cnpj_claro) or cnpj_claro == '':
                continue

            # Extract minutas for this CNPJ
            minutas = []
            total_value = 0
            competencia_values = []
            po_list = []

            for _, row in group.iterrows():
                # Process competencia value
                competencia_raw = row.get('Competência', '')
                start_date_str, end_date_str, data_original = process_order_dates(competencia_raw)

                minuta_data = {
                    "po": str(row.get('PO', '')),
                    "nf_cte": str(row.get('NF/CTE', '')),
                    "valor": float(str(row.get(valor_column, '0')).replace(',', '.')),
                    "data_original": data_original,
                    "competencia": str(row.get('Competência', ''))
                }
                minutas.append(minuta_data)

                # Accumulate metrics
                total_value += minuta_data["valor"]
                competencia_values.append(competencia_raw)

                po = str(row.get('PO', ''))
                if po not in po_list:
                    po_list.append(po)

            # Calculate CNPJ-level start and end dates
            if competencia_values:
                start_date, end_date, _ = process_order_dates(competencia_values[0])
            else:
                start_date = "01/01/2025"
                end_date = "31/12/2025"

            # Get first row for company data
            first_row = group.iloc[0]
            empresa_origem = str(first_row.get('Empresa Origem', ''))

            # Remove formatting from CNPJ Claro for API calls (keep only digits)
            cnpj_claro_clean = ''.join(filter(str.isdigit, str(cnpj_claro)))

            # Lookup city and state from ReceitaWS API
            city, state, municipio, uf, receita_data = await lookup_cnpj_info(cnpj_claro_clean)

            # Determine regional download requirement
            requires_regional = uf in ["TO", "SE"]
            regional_type = None
            if uf == "TO":
                regional_type = "palmas"
            elif uf == "SE":
                regional_type = "aracaju"

            # Create CNPJ group structure
            cnpj_group = {
                "cnpj_claro": cnpj_claro_clean,
                "cnpj_claro_formatted": str(cnpj_claro),
                "empresa_origem": empresa_origem,
                "status": "PENDING",

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

                # File tracking
                "pdf_files": {
                    "base": None,
                    "regional": None,
                    "concatenated": None
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
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(consolidated_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ MINUTA JSON created: {json_path}")
        logger.info(f"📊 Summary: {consolidated_data['summary']['total_cnpj_groups']} CNPJs, {consolidated_data['summary']['total_minutas']} MINUTAs, Total: R$ {consolidated_data['summary']['total_value']:,.2f}")

        return True, None

    except Exception as e:
        logger.error(f"❌ Error processing Excel to MINUTA JSON: {e!s}")
        import traceback
        logger.error(f"💥 Traceback: {traceback.format_exc()}")
        return False, None
```

---

### New Helper: `lookup_cnpj_info()`

**Purpose:** Query ReceitaWS API for city/state information

**Implementation:**

```python
async def lookup_cnpj_info(cnpj: str) -> tuple[str, str, str, str, dict]:
    """
    Lookup CNPJ information from ReceitaWS API

    Args:
        cnpj: CNPJ with only digits (no formatting)

    Returns:
        (city, state, municipio, uf, full_response)

    Example:
        city = "SALVADOR", state = "BA", municipio = "SALVADOR", uf = "BA"
    """
    try:
        # ReceitaWS API endpoint
        url = f"https://receitaws.com.br/v1/cnpj/{cnpj}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get("status") == "OK":
                        # Extract city and state
                        municipio = data.get("municipio", "").upper()
                        uf = data.get("uf", "").upper()

                        # City name processing (convert to CAPS with special chars preserved)
                        city = municipio.upper()
                        state = uf.upper()

                        logger.info(f"✅ CNPJ {cnpj}: {city}/{state}")

                        return city, state, municipio, uf, data
                    else:
                        logger.error(f"❌ ReceitaWS API returned error status for CNPJ {cnpj}: {data}")
                        return "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", {}
                else:
                    logger.error(f"❌ ReceitaWS API HTTP {response.status} for CNPJ {cnpj}")
                    return "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", {}

    except asyncio.TimeoutError:
        logger.error(f"⏱️ ReceitaWS API timeout for CNPJ {cnpj}")
        return "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", {}
    except Exception as e:
        logger.error(f"❌ Error looking up CNPJ {cnpj}: {e}")
        return "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", {}
```

---

### Step 6: `execute_minuta_json_analysis_step`

**Purpose:** Analyze all MINUTA JSON files and extract CNPJ group status information

**Implementation:**

```python
async def execute_minuta_json_analysis_step(step_input: StepInput) -> StepOutput:
    """Analyze all MINUTA JSON files and extract CNPJ group status information"""
    logger.info("🔍 Starting MINUTA JSON analysis...")

    # Get initialization results
    previous_output = step_input.get_step_output("daily_initialization")
    if not previous_output:
        raise ValueError("Daily initialization step output not found")

    init_results = json.loads(previous_output.content)

    data_extractor = create_data_extractor_agent()

    # Analysis context for agent
    analysis_context = f"""
    ANALYZE MINUTA JSON FILES FOR CNPJ GROUP STATUS TRACKING:

    NEW MINUTA FILES: {json.dumps(init_results.get("minuta_json_files_found", []), indent=2)}

    FOR EACH JSON FILE:
    1. Load and parse the consolidated structure
    2. Extract individual CNPJ group status from "cnpj_groups" array
    3. Categorize CNPJ groups by current status:
       - PENDING: Ready for minutGen
       - WAITING_GENERATION: Ready for main-minut-gen
       - GENERATED: Ready for main-minut-download
       - DOWNLOADED: Ready for regional or concatenation
       - REGIONAL_DOWNLOADED: Ready for concatenation
       - PDF_CONCATENATED: Ready for upload
       - UPLOADED: Completed (skip)
       - FAILED_*: Needs error handling

    OUTPUT STRUCTURE:
    {{
        "processing_categories": {{
            "pending_cnpjs": [...],
            "generation_cnpjs": [...],
            "download_cnpjs": [...],
            "regional_download_cnpjs": [...],
            "concatenation_cnpjs": [...],
            "upload_cnpjs": [...],
            "completed_cnpjs": [...],
            "failed_cnpjs": [...]
        }}
    }}
    """

    response = data_extractor.run(analysis_context)

    # REAL JSON FILE ANALYSIS
    analysis_results = {
        "processing_categories": {
            "pending_cnpjs": [],
            "generation_cnpjs": [],
            "download_cnpjs": [],
            "regional_download_cnpjs": [],
            "concatenation_cnpjs": [],
            "upload_cnpjs": [],
            "completed_cnpjs": [],
            "failed_cnpjs": []
        },
        "json_file_status": {},
        "analysis_summary": {
            "total_cnpj_groups_found": 0,
            "cnpjs_needing_processing": 0,
            "cnpjs_completed": 0,
            "files_needing_processing": 0,
            "files_completed": 0
        },
        "analysis_timestamp": datetime.now(UTC).isoformat(),
        "agent_response": str(response.content) if response.content else "No response"
    }

    # Get all MINUTA JSON files
    all_minuta_json_files = init_results.get("minuta_json_files_found", [])

    for json_file_path in all_minuta_json_files:
        try:
            if not os.path.exists(json_file_path):
                logger.warning(f"⚠️ MINUTA JSON file not found: {json_file_path}")
                continue

            logger.info(f"📄 Analyzing MINUTA JSON: {json_file_path}")

            with open(json_file_path, encoding="utf-8") as f:
                json_data = json.load(f)

            # Extract CNPJ group status information
            file_stats = {
                "total_cnpjs": 0,
                "pending": 0,
                "generation": 0,
                "download": 0,
                "regional_download": 0,
                "concatenation": 0,
                "uploaded": 0,
                "failed": 0,
                "needs_processing": False
            }

            # Parse CNPJ groups from JSON
            cnpj_groups = json_data.get("cnpj_groups", [])
            for group in cnpj_groups:
                cnpj = group.get("cnpj_claro")
                status = group.get("status", "PENDING")
                file_stats["total_cnpjs"] += 1

                cnpj_entry = {"cnpj": cnpj, "json_file": json_file_path}

                # Categorize CNPJ by status
                if status == "PENDING":
                    analysis_results["processing_categories"]["pending_cnpjs"].append(cnpj_entry)
                    file_stats["pending"] += 1
                    file_stats["needs_processing"] = True

                elif status == "WAITING_GENERATION":
                    analysis_results["processing_categories"]["generation_cnpjs"].append(cnpj_entry)
                    file_stats["generation"] += 1
                    file_stats["needs_processing"] = True

                elif status == "GENERATED":
                    analysis_results["processing_categories"]["download_cnpjs"].append(cnpj_entry)
                    file_stats["download"] += 1
                    file_stats["needs_processing"] = True

                elif status == "DOWNLOADED":
                    # Check if regional download is needed
                    if group.get("requires_regional", False):
                        analysis_results["processing_categories"]["regional_download_cnpjs"].append(cnpj_entry)
                        file_stats["regional_download"] += 1
                    else:
                        # Skip to concatenation
                        analysis_results["processing_categories"]["concatenation_cnpjs"].append(cnpj_entry)
                        file_stats["concatenation"] += 1
                    file_stats["needs_processing"] = True

                elif status == "REGIONAL_DOWNLOADED":
                    analysis_results["processing_categories"]["concatenation_cnpjs"].append(cnpj_entry)
                    file_stats["concatenation"] += 1
                    file_stats["needs_processing"] = True

                elif status == "PDF_CONCATENATED":
                    analysis_results["processing_categories"]["upload_cnpjs"].append(cnpj_entry)
                    file_stats["concatenation"] += 1
                    file_stats["needs_processing"] = True

                elif status == "UPLOADED":
                    analysis_results["processing_categories"]["completed_cnpjs"].append(cnpj_entry)
                    file_stats["uploaded"] += 1
                    file_stats["needs_processing"] = True  # Need to send email

                elif status == "COMPLETED":
                    # Truly completed
                    file_stats["completed"] = file_stats.get("completed", 0) + 1

                elif status.startswith("FAILED_"):
                    analysis_results["processing_categories"]["failed_cnpjs"].append(cnpj_entry)
                    file_stats["failed"] += 1
                    file_stats["needs_processing"] = True

            analysis_results["json_file_status"][json_file_path] = file_stats
            analysis_results["analysis_summary"]["total_cnpj_groups_found"] += file_stats["total_cnpjs"]

            if file_stats["needs_processing"]:
                analysis_results["analysis_summary"]["files_needing_processing"] += 1
                analysis_results["analysis_summary"]["cnpjs_needing_processing"] += (
                    file_stats["pending"] + file_stats["generation"] +
                    file_stats["download"] + file_stats["regional_download"] +
                    file_stats["concatenation"] + file_stats["failed"]
                )
            else:
                analysis_results["analysis_summary"]["files_completed"] += 1

            analysis_results["analysis_summary"]["cnpjs_completed"] += file_stats["uploaded"]

            logger.info(f"✅ MINUTA JSON analyzed: {file_stats['total_cnpjs']} CNPJs, needs_processing: {file_stats['needs_processing']}")

        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            logger.error(f"❌ Failed to analyze MINUTA JSON {json_file_path}: {e!s}")
            continue
        except Exception as e:
            logger.error(f"❌ Unexpected error analyzing MINUTA {json_file_path}: {e!s}")
            continue

    set_session_state(step_input, "minuta_analysis_results", analysis_results)

    logger.info(f"🔍 MINUTA JSON analysis completed - {analysis_results['analysis_summary']['cnpjs_needing_processing']} CNPJs need processing")

    return StepOutput(content=json.dumps(analysis_results))
```

---

### Step 7: `execute_minuta_status_routing_step`

**Purpose:** Route each CNPJ group to appropriate processing action based on status

**Implementation:**

```python
async def execute_minuta_status_routing_step(step_input: StepInput) -> StepOutput:
    """Route each CNPJ group to appropriate processing action based on status"""
    logger.info("🎯 Starting MINUTA status-based routing...")

    # Get analysis results
    previous_output = step_input.get_step_output("minuta_json_analysis")
    if not previous_output:
        raise ValueError("MINUTA JSON analysis step output not found")

    analysis_results = json.loads(previous_output.content)
    processing_categories = analysis_results["processing_categories"]

    api_orchestrator = create_api_orchestrator_agent()

    routing_context = f"""
    STATUS-BASED ROUTING FOR MINUTA CNPJ GROUP PROCESSING:

    PROCESSING CATEGORIES:
    {json.dumps(processing_categories, indent=2)}

    ROUTING LOGIC:
    - PENDING → minutGen API call (batched by CNPJ) → WAITING_GENERATION
    - WAITING_GENERATION → main-minut-gen API call (individual CNPJ) → GENERATED
    - GENERATED → main-minut-download API call (individual CNPJ) → DOWNLOADED
    - DOWNLOADED → Check requires_regional:
        • IF state == "TO" → main-minut-download-palmas → REGIONAL_DOWNLOADED
        • IF state == "SE" → main-minut-download-aracaju → REGIONAL_DOWNLOADED
        • ELSE → skip to PDF_CONCATENATED
    - REGIONAL_DOWNLOADED → PDF concatenation → PDF_CONCATENATED
    - PDF_CONCATENATED → invoiceUpload API call → UPLOADED
    - UPLOADED → [Future: Send email] → COMPLETED
    - COMPLETED → Skip (already finished)
    - FAILED → Error handling and retry logic

    CREATE PROCESSING QUEUE:
    Group CNPJs by required API action and prepare execution plan
    """

    response = api_orchestrator.run(routing_context)

    # Create processing queues based on status
    routing_results = {
        "processing_queues": {
            "minuta_generation_queue": {
                "action": "minutGen",
                "cnpjs": processing_categories["pending_cnpjs"],
                "batch_processing": True,  # Can batch multiple CNPJs
                "priority": 1
            },
            "esl_generation_queue": {
                "action": "main-minut-gen",
                "cnpjs": processing_categories["generation_cnpjs"],
                "batch_processing": False,  # Individual processing
                "priority": 2
            },
            "download_queue": {
                "action": "main-minut-download",
                "cnpjs": processing_categories["download_cnpjs"],
                "batch_processing": False,  # Individual processing
                "priority": 3
            },
            "regional_download_queue": {
                "action": "regional_download",  # Will split into palmas/aracaju
                "cnpjs": processing_categories["regional_download_cnpjs"],
                "batch_processing": False,
                "priority": 4
            },
            "concatenation_queue": {
                "action": "pdf_concatenation",
                "cnpjs": processing_categories["concatenation_cnpjs"],
                "batch_processing": False,
                "priority": 5
            },
            "upload_queue": {
                "action": "invoiceUpload",
                "cnpjs": processing_categories["upload_cnpjs"],
                "batch_processing": False,
                "priority": 6
            },
            "email_queue": {
                "action": "sendEmail",
                "cnpjs": processing_categories["completed_cnpjs"],
                "batch_processing": False,
                "priority": 7
            }
        },
        "execution_plan": {
            "total_actions": len(processing_categories["pending_cnpjs"]) +
                           len(processing_categories["generation_cnpjs"]) +
                           len(processing_categories["download_cnpjs"]) +
                           len(processing_categories["regional_download_cnpjs"]) +
                           len(processing_categories["concatenation_cnpjs"]) +
                           len(processing_categories["upload_cnpjs"]),
            "batch_actions": 1,  # minutGen
            "individual_actions": "varies based on CNPJ count",
            "estimated_execution_time_minutes": 30
        },
        "completed_cnpjs": processing_categories["completed_cnpjs"],
        "routing_timestamp": datetime.now(UTC).isoformat(),
        "agent_response": str(response.content) if response.content else "No response"
    }

    set_session_state(step_input, "minuta_routing_results", routing_results)

    logger.info(f"🎯 MINUTA routing completed - {routing_results['execution_plan']['total_actions']} actions queued")

    return StepOutput(content=json.dumps(routing_results))
```

---

### Step 8: `execute_minuta_cnpj_processing_step`

**Purpose:** Execute individual API calls for each CNPJ group based on routing decisions

**Implementation:** (Due to length, showing key sections)

```python
async def execute_minuta_cnpj_processing_step(step_input: StepInput) -> StepOutput:
    """Execute individual API calls for each CNPJ group based on routing decisions"""
    logger.info("⚙️ Starting MINUTA CNPJ processing...")

    # Get routing results
    previous_output = step_input.get_step_output("minuta_status_routing")
    if not previous_output:
        raise ValueError("MINUTA routing step output not found")

    routing_results = json.loads(previous_output.content)
    processing_queues = routing_results["processing_queues"]

    # Initialize API client
    api_client = BrowserAPIClient()

    processing_results = {
        "api_executions": {},
        "status_updates": {},
        "failed_cnpjs": {},
        "execution_summary": {
            "successful_actions": 0,
            "failed_actions": 0,
            "cnpjs_updated": 0,
            "cnpjs_failed": 0
        },
        "processing_timestamp": datetime.now(UTC).isoformat()
    }

    # Process each queue in priority order
    for queue_name, queue_data in processing_queues.items():
        action = queue_data["action"]
        cnpjs = queue_data["cnpjs"]
        batch_processing = queue_data["batch_processing"]

        logger.info(f"⚙️ Processing {queue_name} with {len(cnpjs)} CNPJs")

        if not cnpjs:  # Skip empty queues
            continue

        try:
            # === MINUTA GENERATION (minutGen - Claro) ===
            if action == "minutGen":
                # Batch processing - group all POs by CNPJ
                for cnpj_data in cnpjs:
                    cnpj = cnpj_data["cnpj"]
                    json_file = cnpj_data["json_file"]

                    # Load CNPJ group details
                    cnpj_group = await load_cnpj_group_from_json(json_file, cnpj)

                    # Build payload
                    payload = {
                        "flow_name": "minutGen",
                        "parameters": {
                            "orders": cnpj_group["po_list"],
                            "city": cnpj_group["city"],
                            "headless": get_headless_setting()
                        }
                    }

                    api_response = await api_client.execute_api_call("minutGen", payload)

                    if api_response["success"]:
                        new_status = "WAITING_GENERATION"
                        processing_results["status_updates"][cnpj] = {
                            "new_status": new_status,
                            "json_file": json_file
                        }
                        processing_results["execution_summary"]["successful_actions"] += 1
                        processing_results["execution_summary"]["cnpjs_updated"] += 1
                    else:
                        processing_results["failed_cnpjs"][cnpj] = {
                            "action": action,
                            "error": api_response.get("error", "Unknown error"),
                            "json_file": json_file
                        }
                        processing_results["execution_summary"]["failed_actions"] += 1
                        processing_results["execution_summary"]["cnpjs_failed"] += 1

            # === ESL GENERATION (main-minut-gen) ===
            elif action == "main-minut-gen":
                for cnpj_data in cnpjs:
                    cnpj = cnpj_data["cnpj"]
                    json_file = cnpj_data["json_file"]

                    cnpj_group = await load_cnpj_group_from_json(json_file, cnpj)

                    # For each PO in the CNPJ group, call main-minut-gen
                    for po in cnpj_group["po_list"]:
                        # Get minutas for this PO
                        po_minutas = [m for m in cnpj_group["minutas"] if m["po"] == po]
                        minute_numbers = [m["nf_cte"] for m in po_minutas]
                        po_value = sum(m["valor"] for m in po_minutas)

                        payload = {
                            "flow_name": "main-minut-gen",
                            "parameters": {
                                "po": po,
                                "minutes": minute_numbers,
                                "total_value": po_value,
                                "startDate": cnpj_group["start_date"],
                                "endDate": cnpj_group["end_date"],
                                "headless": get_headless_setting()
                            }
                        }

                        api_response = await api_client.execute_api_call("main-minut-gen", payload)

                        # Check success
                        if not api_response["success"]:
                            logger.error(f"❌ main-minut-gen failed for PO {po}")
                            processing_results["failed_cnpjs"][cnpj] = {
                                "action": action,
                                "po": po,
                                "error": api_response.get("error"),
                                "json_file": json_file
                            }
                            processing_results["execution_summary"]["failed_actions"] += 1
                            break  # Stop processing this CNPJ
                    else:
                        # All POs succeeded
                        new_status = "GENERATED"
                        processing_results["status_updates"][cnpj] = {
                            "new_status": new_status,
                            "json_file": json_file
                        }
                        processing_results["execution_summary"]["successful_actions"] += 1
                        processing_results["execution_summary"]["cnpjs_updated"] += 1

            # === MINUTA DOWNLOAD (main-minut-download) ===
            elif action == "main-minut-download":
                for cnpj_data in cnpjs:
                    cnpj = cnpj_data["cnpj"]
                    json_file = cnpj_data["json_file"]

                    cnpj_group = await load_cnpj_group_from_json(json_file, cnpj)

                    # Download for each PO
                    for po in cnpj_group["po_list"]:
                        po_minutas = [m for m in cnpj_group["minutas"] if m["po"] == po]
                        minute_numbers = [m["nf_cte"] for m in po_minutas]
                        po_value = sum(m["valor"] for m in po_minutas)

                        payload = {
                            "flow_name": "main-minut-download",
                            "parameters": {
                                "po": po,
                                "minutes": minute_numbers,
                                "total_value": po_value,
                                "cnpj": cnpj,
                                "headless": get_headless_setting()
                            }
                        }

                        api_response = await api_client.execute_api_call("main-minut-download", payload)

                        if not api_response["success"]:
                            logger.error(f"❌ main-minut-download failed for PO {po}")
                            processing_results["failed_cnpjs"][cnpj] = {
                                "action": action,
                                "po": po,
                                "error": api_response.get("error"),
                                "json_file": json_file
                            }
                            processing_results["execution_summary"]["failed_actions"] += 1
                            break
                    else:
                        # All downloads succeeded
                        # Save PDF file path
                        base_pdf_path = f"mctech/minutas/downloads/minuta_{cnpj}.pdf"

                        new_status = "DOWNLOADED"
                        processing_results["status_updates"][cnpj] = {
                            "new_status": new_status,
                            "json_file": json_file,
                            "base_pdf": base_pdf_path
                        }
                        processing_results["execution_summary"]["successful_actions"] += 1
                        processing_results["execution_summary"]["cnpjs_updated"] += 1

            # === REGIONAL DOWNLOADS (Palmas/Aracaju) ===
            elif action == "regional_download":
                for cnpj_data in cnpjs:
                    cnpj = cnpj_data["cnpj"]
                    json_file = cnpj_data["json_file"]

                    cnpj_group = await load_cnpj_group_from_json(json_file, cnpj)

                    # Determine regional flow based on state
                    regional_type = cnpj_group.get("regional_type")
                    if regional_type == "palmas":
                        flow_name = "main-minut-download-palmas"
                    elif regional_type == "aracaju":
                        flow_name = "main-minut-download-aracaju"
                    else:
                        logger.warning(f"⚠️ CNPJ {cnpj} has no regional_type, skipping")
                        continue

                    # Download regional PDF for each PO
                    for po in cnpj_group["po_list"]:
                        po_minutas = [m for m in cnpj_group["minutas"] if m["po"] == po]
                        minute_numbers = [m["nf_cte"] for m in po_minutas]
                        po_value = sum(m["valor"] for m in po_minutas)

                        payload = {
                            "flow_name": flow_name,
                            "parameters": {
                                "po": po,
                                "minutes": minute_numbers,
                                "total_value": po_value,
                                "cnpj": cnpj,
                                "headless": get_headless_setting()
                            }
                        }

                        api_response = await api_client.execute_api_call(flow_name, payload)

                        if not api_response["success"]:
                            logger.error(f"❌ {flow_name} failed for PO {po}")
                            processing_results["failed_cnpjs"][cnpj] = {
                                "action": flow_name,
                                "po": po,
                                "error": api_response.get("error"),
                                "json_file": json_file
                            }
                            processing_results["execution_summary"]["failed_actions"] += 1
                            break
                    else:
                        # Regional download succeeded
                        regional_pdf_path = f"mctech/minutas/regional/{regional_type}_{cnpj}.pdf"

                        new_status = "REGIONAL_DOWNLOADED"
                        processing_results["status_updates"][cnpj] = {
                            "new_status": new_status,
                            "json_file": json_file,
                            "regional_pdf": regional_pdf_path
                        }
                        processing_results["execution_summary"]["successful_actions"] += 1
                        processing_results["execution_summary"]["cnpjs_updated"] += 1

            # === PDF CONCATENATION ===
            elif action == "pdf_concatenation":
                for cnpj_data in cnpjs:
                    cnpj = cnpj_data["cnpj"]
                    json_file = cnpj_data["json_file"]

                    cnpj_group = await load_cnpj_group_from_json(json_file, cnpj)

                    # Get PDF paths
                    base_pdf = cnpj_group["pdf_files"].get("base")
                    regional_pdf = cnpj_group["pdf_files"].get("regional")

                    # Concatenate PDFs
                    concatenated_pdf_path = f"mctech/minutas/concatenated/final_{cnpj}.pdf"

                    success = await concatenate_pdfs(
                        base_pdf=base_pdf,
                        regional_pdf=regional_pdf,
                        output_path=concatenated_pdf_path
                    )

                    if success:
                        new_status = "PDF_CONCATENATED"
                        processing_results["status_updates"][cnpj] = {
                            "new_status": new_status,
                            "json_file": json_file,
                            "concatenated_pdf": concatenated_pdf_path
                        }
                        processing_results["execution_summary"]["successful_actions"] += 1
                        processing_results["execution_summary"]["cnpjs_updated"] += 1
                    else:
                        processing_results["failed_cnpjs"][cnpj] = {
                            "action": action,
                            "error": "PDF concatenation failed",
                            "json_file": json_file
                        }
                        processing_results["execution_summary"]["failed_actions"] += 1
                        processing_results["execution_summary"]["cnpjs_failed"] += 1

            # === INVOICE UPLOAD ===
            elif action == "invoiceUpload":
                for cnpj_data in cnpjs:
                    cnpj = cnpj_data["cnpj"]
                    json_file = cnpj_data["json_file"]

                    cnpj_group = await load_cnpj_group_from_json(json_file, cnpj)

                    # Get concatenated PDF path
                    concatenated_pdf = cnpj_group["pdf_files"].get("concatenated")

                    if not concatenated_pdf or not os.path.exists(concatenated_pdf):
                        logger.error(f"❌ Concatenated PDF not found for CNPJ {cnpj}")
                        processing_results["failed_cnpjs"][cnpj] = {
                            "action": action,
                            "error": "Concatenated PDF not found",
                            "json_file": json_file
                        }
                        continue

                    # Convert PDF to base64
                    with open(concatenated_pdf, 'rb') as f:
                        pdf_content = f.read()
                    invoice_base64 = base64.b64encode(pdf_content).decode('utf-8')

                    # Use first PO for upload (or aggregate)
                    primary_po = cnpj_group["po_list"][0]

                    payload = {
                        "flow_name": "invoiceUpload",
                        "parameters": {
                            "po": primary_po,
                            "invoice": invoice_base64,
                            "invoice_filename": f"minuta_{cnpj}.pdf",
                            "headless": get_headless_setting()
                        }
                    }

                    api_response = await api_client.execute_api_call("invoiceUpload", payload)

                    if api_response["success"]:
                        # Extract protocol
                        success, protocol, message = api_client.parse_invoice_upload_response(api_response)

                        new_status = "UPLOADED"
                        processing_results["status_updates"][cnpj] = {
                            "new_status": new_status,
                            "json_file": json_file,
                            "protocol": protocol
                        }
                        processing_results["execution_summary"]["successful_actions"] += 1
                        processing_results["execution_summary"]["cnpjs_updated"] += 1
                    else:
                        processing_results["failed_cnpjs"][cnpj] = {
                            "action": action,
                            "error": api_response.get("error"),
                            "json_file": json_file
                        }
                        processing_results["execution_summary"]["failed_actions"] += 1
                        processing_results["execution_summary"]["cnpjs_failed"] += 1

            # TODO: Email sending for UPLOADED CNPJs

        except Exception as e:
            logger.error(f"❌ Error processing {queue_name}: {e!s}")
            processing_results["api_executions"][queue_name] = {
                "action": action,
                "error": str(e),
                "success": False
            }
            processing_results["execution_summary"]["failed_actions"] += 1

    set_session_state(step_input, "minuta_processing_results", processing_results)

    # Close HTTP session
    await api_client.close_session()

    logger.info(f"⚙️ MINUTA processing completed - {processing_results['execution_summary']['cnpjs_updated']} CNPJs updated")

    return StepOutput(content=json.dumps(processing_results))
```

---

### New Helper: `concatenate_pdfs()`

**Purpose:** Merge base + regional PDFs into single file

**Implementation:**

```python
async def concatenate_pdfs(
    base_pdf: str,
    regional_pdf: str | None,
    output_path: str
) -> bool:
    """
    Concatenate base PDF with optional regional PDF

    Args:
        base_pdf: Path to base MINUTA PDF
        regional_pdf: Optional path to regional PDF (Palmas/Aracaju)
        output_path: Output path for concatenated PDF

    Returns:
        True if successful, False otherwise
    """
    try:
        from PyPDF2 import PdfMerger

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        merger = PdfMerger()

        # Append base PDF
        if base_pdf and os.path.exists(base_pdf):
            merger.append(base_pdf)
            logger.info(f"📄 Added base PDF: {base_pdf}")
        else:
            logger.error(f"❌ Base PDF not found: {base_pdf}")
            return False

        # Append regional PDF if exists
        if regional_pdf and os.path.exists(regional_pdf):
            merger.append(regional_pdf)
            logger.info(f"📄 Added regional PDF: {regional_pdf}")
        else:
            logger.info(f"📄 No regional PDF to concatenate")

        # Write concatenated PDF
        merger.write(output_path)
        merger.close()

        logger.info(f"✅ PDF concatenated successfully: {output_path}")
        return True

    except Exception as e:
        logger.error(f"❌ PDF concatenation failed: {e}")
        import traceback
        logger.error(f"💥 Traceback: {traceback.format_exc()}")
        return False
```

---

### New Helper: `load_cnpj_group_from_json()`

**Purpose:** Load specific CNPJ group data from JSON file

**Implementation:**

```python
async def load_cnpj_group_from_json(json_file: str, cnpj: str) -> dict:
    """
    Load specific CNPJ group from MINUTA JSON file

    Args:
        json_file: Path to MINUTA JSON file
        cnpj: CNPJ Claro to load

    Returns:
        CNPJ group dictionary
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        # Find CNPJ group
        for group in json_data.get("cnpj_groups", []):
            if group.get("cnpj_claro") == cnpj:
                return group

        raise ValueError(f"CNPJ {cnpj} not found in {json_file}")

    except Exception as e:
        logger.error(f"❌ Failed to load CNPJ {cnpj} from {json_file}: {e}")
        raise
```

---

### Step 9: `execute_minuta_completion_step`

**Purpose:** Update MINUTA JSON files with new statuses and generate summary

**Implementation:**

```python
async def execute_minuta_completion_step(step_input: StepInput) -> StepOutput:
    """Complete MINUTA processing cycle and update JSON files with new statuses"""
    completion_start_time = datetime.now(UTC)
    logger.info("🏁 Starting MINUTA completion and JSON updates...")

    # Get processing results
    previous_output = step_input.get_step_output("minuta_cnpj_processing")
    if not previous_output:
        raise ValueError("MINUTA CNPJ processing step output not found")

    processing_results = json.loads(previous_output.content)

    # Handle case where API was unavailable
    status_updates = processing_results.get("status_updates", {})
    if not status_updates:
        logger.warning("⚠️ No MINUTA status updates available")
        return StepOutput(content=json.dumps({
            "status": "SUCCESS",
            "message": "MINUTA completion successful - no status updates to apply",
            "files_updated": 0,
            "completion_timestamp": datetime.now(UTC).isoformat()
        }))

    file_manager = create_file_manager_agent()

    completion_context = f"""
    MINUTA COMPLETION - UPDATE JSON FILES WITH NEW STATUSES:

    STATUS UPDATES TO APPLY:
    {json.dumps(status_updates, indent=2)}

    TASKS:
    1. Update each MINUTA JSON file with new CNPJ group statuses
    2. Update PDF file paths where applicable
    3. Update protocol numbers where available
    4. Preserve all other data in JSON structure
    5. Add processing timestamp to track last update
    6. Generate MINUTA summary report
    """

    response = file_manager.run(completion_context)

    # REAL JSON file updates
    files_updated = {}
    for cnpj, update_info in status_updates.items():
        json_file = update_info["json_file"]
        new_status = update_info["new_status"]

        if json_file not in files_updated:
            files_updated[json_file] = {
                "cnpjs_updated": [],
                "update_count": 0
            }

        files_updated[json_file]["cnpjs_updated"].append(f"{cnpj} → {new_status}")
        files_updated[json_file]["update_count"] += 1

        # REAL FILE UPDATE
        try:
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)

                # Update the status for this specific CNPJ group
                for group in json_data.get("cnpj_groups", []):
                    if group.get("cnpj_claro") == cnpj:
                        group["status"] = new_status
                        group["last_updated"] = datetime.now(UTC).isoformat()

                        # Update PDF paths if present
                        if "base_pdf" in update_info:
                            group["pdf_files"]["base"] = update_info["base_pdf"]
                        if "regional_pdf" in update_info:
                            group["pdf_files"]["regional"] = update_info["regional_pdf"]
                        if "concatenated_pdf" in update_info:
                            group["pdf_files"]["concatenated"] = update_info["concatenated_pdf"]
                        if "protocol" in update_info:
                            group["protocol_number"] = update_info["protocol"]

                        logger.info(f"✅ Updated CNPJ {cnpj} status to {new_status} in {json_file}")
                        break

                # Write updated JSON back to file
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)

                logger.info(f"💾 MINUTA JSON updated: {json_file}")
            else:
                logger.warning(f"⚠️ MINUTA JSON not found: {json_file}")

        except Exception as e:
            logger.error(f"❌ Failed to update MINUTA JSON {json_file}: {e!s}")
            continue

    # Get session state for final summary
    session_state = get_session_state(step_input)

    previous_init_output = step_input.get_step_output("daily_initialization")
    if previous_init_output:
        init_results = json.loads(previous_init_output.content)
    else:
        init_results = session_state.get("initialization_results", {})

    minuta_analysis_results = session_state.get("minuta_analysis_results", {})

    # Calculate execution time
    completion_end_time = datetime.now(UTC)
    workflow_start_time = session_state.get("workflow_start_time", completion_start_time)
    if isinstance(workflow_start_time, str):
        workflow_start_time = datetime.fromisoformat(workflow_start_time.replace('Z', '+00:00'))

    completion_summary = {
        "minuta_execution_summary": {
            "execution_date": datetime.now(UTC).strftime("%Y-%m-%d"),
            "daily_batch_id": session_state.get("daily_batch_id", "unknown"),
            "overall_status": "SUCCESS"
        },
        "minuta_processing_statistics": {
            "total_cnpj_groups_found": minuta_analysis_results.get("analysis_summary", {}).get("total_cnpj_groups_found", 0),
            "cnpjs_processed_today": processing_results["execution_summary"]["cnpjs_updated"],
            "cnpjs_failed_today": processing_results["execution_summary"]["cnpjs_failed"],
            "cnpjs_uploaded_today": len([c for c, u in status_updates.items() if u["new_status"] == "UPLOADED"]),
            "api_calls_successful": processing_results["execution_summary"]["successful_actions"],
            "api_calls_failed": processing_results["execution_summary"]["failed_actions"]
        },
        "minuta_json_file_updates": files_updated,
        "minuta_status_transitions_applied": status_updates,
        "minuta_failed_cnpjs_detail": processing_results.get("failed_cnpjs", {}),
        "completion_timestamp": datetime.now(UTC).isoformat(),
        "agent_response": str(response.content) if response.content else "No response"
    }

    logger.info("🏁 MINUTA processing cycle completed!")

    # Log detailed results
    stats = completion_summary['minuta_processing_statistics']
    logger.info(f"✅ MINUTAs processed: {stats['cnpjs_processed_today']} CNPJ groups")
    logger.info(f"❌ MINUTAs failed: {stats['cnpjs_failed_today']} CNPJ groups")
    logger.info(f"📤 MINUTAs uploaded: {stats['cnpjs_uploaded_today']} CNPJ groups")

    return StepOutput(content=json.dumps(completion_summary))
```

---

### Step 10 Modification: `execute_database_sync_step`

**Changes Required:** Extend to sync MINUTA data in addition to CTE data

**Implementation:**

```python
async def execute_database_sync_step(step_input: StepInput) -> StepOutput:
    """
    🗄️ FINAL STEP: Synchronize CTE + MINUTA JSON files to PostgreSQL database

    ⚠️ CRITICAL: MUST REMAIN FINAL STEP
    """
    sync_start_time = datetime.now(UTC)
    logger.info("🗄️ Starting database synchronization - FINAL STEP (CTE + MINUTA)")

    try:
        # Get database URL from environment
        database_url = os.getenv('HIVE_DATABASE_URL')
        if not database_url:
            raise ValueError("HIVE_DATABASE_URL environment variable not set")

        # Initialize CTE processor (handles both CTE and MINUTA)
        processor = CTEProcessor(database_url)

        # Process CTE JSONs
        cte_directory = "mctech/ctes"
        await processor.process_directory(cte_directory)
        cte_count = await processor.get_order_count()

        # Process MINUTA JSONs (using same processor)
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

        return StepOutput(content=json.dumps(error_result, indent=2))
```

---

### Modified Workflow Factory

**Updated workflow creation with MINUTA steps:**

```python
def get_processamento_faturas_workflow(**kwargs) -> Workflow:
    """Factory function to create ProcessamentoFaturas with CTE + MINUTA processing"""

    workflow = Workflow(
        name="processamento_faturas",
        description="Daily CTE + MINUTA invoice processing with status-based routing",
        steps=[
            # === CTE PROCESSING (Existing) ===
            Step(
                name="daily_initialization",
                description="Initialize daily processing - creates CTE + MINUTA JSONs",
                executor=execute_daily_initialization_step,
                max_retries=2,
            ),
            Step(
                name="json_analysis",
                description="Analyze CTE JSON files and determine PO processing requirements",
                executor=execute_json_analysis_step,
                max_retries=2,
            ),
            Step(
                name="status_based_routing",
                description="Route CTEs by status",
                executor=execute_status_based_routing_step,
                max_retries=3,
            ),
            Step(
                name="individual_po_processing",
                description="Process individual CTE POs",
                executor=execute_individual_po_processing_step,
                max_retries=3,
            ),
            Step(
                name="daily_completion",
                description="Update CTE JSON files and send notifications",
                executor=execute_daily_completion_step,
                max_retries=1,
            ),

            # === MINUTA PROCESSING (New) ===
            Step(
                name="minuta_json_analysis",
                description="Analyze MINUTA JSON files and determine CNPJ processing requirements",
                executor=execute_minuta_json_analysis_step,
                max_retries=2,
            ),
            Step(
                name="minuta_status_routing",
                description="Route MINUTAs by CNPJ status",
                executor=execute_minuta_status_routing_step,
                max_retries=3,
            ),
            Step(
                name="minuta_cnpj_processing",
                description="Process individual MINUTA CNPJ groups through API pipeline",
                executor=execute_minuta_cnpj_processing_step,
                max_retries=3,
            ),
            Step(
                name="minuta_completion",
                description="Update MINUTA JSON files and generate summary",
                executor=execute_minuta_completion_step,
                max_retries=1,
            ),

            # === FINAL SYNC (Modified) ===
            Step(
                name="database_sync",
                description="🗄️ FINAL STEP: Sync CTE + MINUTA to PostgreSQL. ⚠️ MUST REMAIN FINAL",
                executor=execute_database_sync_step,
                max_retries=2,
            ),
        ],
        **kwargs,
    )

    logger.info("ProcessamentoFaturas Workflow initialized with CTE + MINUTA processing")
    return workflow
```

---

## 🔧 BrowserAPIClient Extensions

**New Methods Required:**

```python
class BrowserAPIClient:
    """Enhanced Browser API client with MINUTA support"""

    # ... existing methods ...

    def build_minut_gen_payload(self, cnpj_group: dict) -> dict:
        """Build payload for minutGen (Claro)"""
        return {
            "flow_name": "minutGen",
            "parameters": {
                "orders": cnpj_group["po_list"],
                "city": cnpj_group["city"],
                "headless": get_headless_setting()
            }
        }

    def build_main_minut_gen_payload(self, cnpj_group: dict, po: str, minutas: list) -> dict:
        """Build payload for main-minut-gen (ESL)"""
        minute_numbers = [m["nf_cte"] for m in minutas]
        total_value = sum(m["valor"] for m in minutas)

        return {
            "flow_name": "main-minut-gen",
            "parameters": {
                "po": po,
                "minutes": minute_numbers,
                "total_value": total_value,
                "startDate": cnpj_group["start_date"],
                "endDate": cnpj_group["end_date"],
                "headless": get_headless_setting()
            }
        }

    def build_main_minut_download_payload(self, cnpj: str, po: str, minutas: list, total_value: float) -> dict:
        """Build payload for main-minut-download (ESL)"""
        minute_numbers = [m["nf_cte"] for m in minutas]

        return {
            "flow_name": "main-minut-download",
            "parameters": {
                "po": po,
                "minutes": minute_numbers,
                "total_value": total_value,
                "cnpj": cnpj,
                "headless": get_headless_setting()
            }
        }

    def build_regional_download_payload(self, flow_name: str, cnpj: str, po: str, minutas: list, total_value: float) -> dict:
        """Build payload for regional downloads (Palmas/Aracaju)"""
        minute_numbers = [m["nf_cte"] for m in minutas]

        return {
            "flow_name": flow_name,
            "parameters": {
                "po": po,
                "minutes": minute_numbers,
                "total_value": total_value,
                "cnpj": cnpj,
                "headless": get_headless_setting()
            }
        }
```

---

## 📊 Database Schema Extensions

**CTEProcessor Extensions Required:**

```python
class CTEProcessor:
    """Processor for CTE and MINUTA data synchronization"""

    # ... existing CTE methods ...

    async def process_minuta_directory(self, directory_path: str) -> None:
        """Process all MINUTA JSON files in directory"""
        import glob

        json_files = glob.glob(f"{directory_path}/minutas_*.json")

        for json_file in json_files:
            await self.process_minuta_file(json_file)

    async def process_minuta_file(self, file_path: str) -> None:
        """Process single MINUTA JSON file and upsert to database"""
        with open(file_path, 'r') as f:
            data = json.load(f)

        for cnpj_group in data.get("cnpj_groups", []):
            await self.upsert_minuta_group(cnpj_group)

    async def upsert_minuta_group(self, cnpj_group: dict) -> None:
        """Upsert MINUTA CNPJ group to database"""
        # Use same table as CTEs or separate table based on schema decision
        # UPSERT operation to overwrite existing data
        pass

    async def get_minuta_count(self) -> int:
        """Get total count of MINUTA CNPJ groups in database"""
        # Query count from database
        pass
```

---

## 🚨 Error Handling Strategy

### MINUTA-Specific Error States

1. **FAILED_GENERATION**: minutGen or main-minut-gen failed
   - **Recovery**: Retry with exponential backoff
   - **Max Retries**: 3

2. **FAILED_DOWNLOAD**: main-minut-download failed
   - **Recovery**: Retry with backoff
   - **Fallback**: Manual processing notification

3. **FAILED_REGIONAL_DOWNLOAD**: Palmas/Aracaju download failed
   - **Recovery**: Retry regional download
   - **Fallback**: Continue without regional (base PDF only)

4. **FAILED_CONCATENATION**: PDF merge failed
   - **Recovery**: Validate PDF integrity, retry
   - **Fallback**: Use base PDF only

5. **FAILED_UPLOAD**: invoiceUpload failed
   - **Recovery**: Retry upload
   - **Manual Intervention**: Alert admin

---

## 📱 WhatsApp Notification Extensions

**Modified Daily Completion Message:**

```python
whatsapp_message = f"""🏁 *PROCESSAMENTO DIÁRIO CONCLUÍDO*

📊 *CTEs Processados:*
✅ POs processados: {cte_stats['pos_processed_today']}
❌ POs falharam: {cte_stats['pos_failed_today']}
📤 Uploads: {cte_stats['pos_uploaded_today']}

📊 *MINUTAs Processados:*
✅ CNPJs processados: {minuta_stats['cnpjs_processed_today']}
❌ CNPJs falharam: {minuta_stats['cnpjs_failed_today']}
📤 Uploads: {minuta_stats['cnpjs_uploaded_today']}

📧 Emails recebidos: {stats['new_emails_processed']}
"""
```

---

## 🧪 Testing Strategy

### Unit Tests Required

1. **`test_process_excel_to_minuta_json()`**
   - Valid Excel → correct MINUTA JSON structure
   - Missing columns → validation error
   - No MINUTA records → validation error
   - CNPJ grouping correctness

2. **`test_lookup_cnpj_info()`**
   - Valid CNPJ → correct city/state
   - Invalid CNPJ → error handling
   - API timeout → fallback behavior

3. **`test_concatenate_pdfs()`**
   - Base + regional → merged PDF
   - Base only → base PDF copied
   - Invalid PDFs → error handling

4. **`test_minuta_status_transitions()`**
   - PENDING → WAITING_GENERATION
   - DOWNLOADED → regional routing logic
   - All status flows valid

### Integration Tests Required

1. **End-to-End MINUTA Pipeline**
   - Sample Excel → complete MINUTA processing
   - Verify JSON creation
   - Verify status progression
   - Verify database sync

2. **Regional Download Conditional**
   - Tocantins CNPJ → Palmas download
   - Sergipe CNPJ → Aracaju download
   - Other states → skip regional

3. **Database Sync Verification**
   - MINUTA data correctly stored
   - jack_retrieval can query MINUTAs

---

## 📋 Implementation Checklist

### Phase 1: Foundation
- [ ] Add `MinutaProcessingStatus` enum
- [ ] Implement `lookup_cnpj_info()` helper
- [ ] Implement `process_excel_to_minuta_json()`
- [ ] Implement `concatenate_pdfs()` helper
- [ ] Implement `load_cnpj_group_from_json()` helper

### Phase 2: Workflow Steps
- [ ] Modify `execute_daily_initialization_step` for dual JSON creation
- [ ] Implement `execute_minuta_json_analysis_step`
- [ ] Implement `execute_minuta_status_routing_step`
- [ ] Implement `execute_minuta_cnpj_processing_step` (largest task)
- [ ] Implement `execute_minuta_completion_step`

### Phase 3: API Client Extensions
- [ ] Add MINUTA payload builders to `BrowserAPIClient`
- [ ] Add MINUTA response parsers
- [ ] Handle binary PDF downloads
- [ ] Verify payload formats match browser-agent-api

### Phase 4: Database Integration
- [ ] Extend `CTEProcessor` for MINUTA data
- [ ] Add `process_minuta_directory()` method
- [ ] Implement MINUTA UPSERT operations
- [ ] Modify `execute_database_sync_step`

### Phase 5: Testing
- [ ] Unit tests for all new helpers
- [ ] Integration tests for MINUTA pipeline
- [ ] End-to-end test with sample Excel
- [ ] Verify database sync correctness

### Phase 6: jack_retrieval Agent Updates
- [ ] Update prompts to include MINUTA queries
- [ ] Add MINUTA-specific tools/functions
- [ ] Test MINUTA data retrieval
- [ ] Update final report format

### Phase 7: Monitoring & Notifications
- [ ] Update WhatsApp messages for MINUTA stats
- [ ] Add MINUTA metrics to completion summary
- [ ] Implement MINUTA-specific error alerts

---

## 🎯 Success Criteria

### Functional Requirements
✅ Excel files processed to create both CTE + MINUTA JSONs
✅ MINUTAs grouped by CNPJ Claro
✅ City/State retrieved from ReceitaWS API
✅ Regional downloads for Tocantins/Sergipe
✅ PDF concatenation working correctly
✅ Status progression through all stages
✅ Database sync includes MINUTA data
✅ jack_retrieval can query MINUTAs

### Performance Requirements
✅ MINUTA processing completes within 30 minutes
✅ ReceitaWS API lookups < 5 seconds per CNPJ
✅ PDF concatenation < 2 seconds per file
✅ No blocking of CTE processing

### Quality Requirements
✅ Zero data loss during processing
✅ All errors logged with recovery strategies
✅ Comprehensive test coverage > 80%
✅ Documentation complete and accurate

---

## 📝 Dependencies & Prerequisites

### Python Packages
- `PyPDF2` or `pikepdf` for PDF concatenation
- `aiohttp` for ReceitaWS API calls (already installed)
- All existing dependencies maintained

### Environment Variables
No new environment variables required (all existing variables reused)

### External APIs
- **ReceitaWS API**: `https://receitaws.com.br/v1/cnpj/{cnpj}`
  - Free tier: 3 requests/minute
  - Requires rate limiting consideration

---

## 🚀 Deployment Strategy

### Rollout Plan
1. **Development Environment**: Test complete pipeline
2. **Staging Environment**: Validate with real Excel files
3. **Production Rollout**:
   - Phase 1: Monitor CTE processing (no MINUTA)
   - Phase 2: Enable MINUTA processing for 1 week
   - Phase 3: Full production with monitoring

### Rollback Plan
- MINUTA steps can be disabled without affecting CTE processing
- Database sync backwards compatible (ignores MINUTA data if not present)

---

## 📚 Additional Notes

### ReceitaWS API Rate Limiting
Free tier allows 3 requests/minute. Implementation should:
- Cache CNPJ lookups within session
- Add delay between requests if needed
- Handle rate limit errors gracefully

### PDF File Storage
- Base PDFs: ~500KB average
- Regional PDFs: ~300KB average
- Concatenated PDFs: ~800KB average
- Daily storage: ~50MB for 50 CNPJs

### Future Enhancements
- Email sending for completed MINUTA uploads
- MINUTA-specific WhatsApp notifications
- Historical MINUTA reporting
- MINUTA analytics dashboard

---

**End of Implementation Plan**

**Next Steps:** Review this plan, approve architecture decisions, then proceed with implementation phase.
