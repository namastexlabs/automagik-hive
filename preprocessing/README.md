# Knowledge Base Preprocessing

This directory contains scripts to preprocess knowledge files and generate the CSV for the RAG system.

## Scripts

### 1. `validate_knowledge.py`
Validates the structure of knowledge files in `docs/knowledge_examples/`:
- Checks document separators
- Validates required sections
- Reports any formatting issues

### 2. `generate_rag_csv.py`
Generates the knowledge base CSV from validated files:
- Parses documents from markdown files
- Extracts business units from typification
- Creates `knowledge/knowledge_rag.csv`

## Usage

```bash
# First validate the knowledge files
python preprocessing/validate_knowledge.py

# Then generate the CSV
python preprocessing/generate_rag_csv.py
```

## Business Units Found

From the 64 documents analyzed:
- **Adquirência Web** (9 documents) - Web acquiring and sales anticipation
- **Adquirência Web / Adquirência Presencial** (2 documents) - Hybrid web/in-person acquiring
- **Emissão** (13 documents) - Card emission and management
- **PagBank** (40 documents) - Digital account and banking services

## Output

The script generates `knowledge/knowledge_rag.csv` with columns:
- `problem` - The customer problem/question
- `solution` - The solution/answer
- `typification` - Service classification details
- `business_unit` - The business unit responsible

This CSV is used by the RAG system at runtime.