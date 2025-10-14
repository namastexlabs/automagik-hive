# Forge Task: Documentation & Knowledge Transfer

**Task ID**: knowledge-enhancement-documentation
**Branch**: wish/knowledge-enhancement
**Complexity**: 4
**Agent**: hive-coder
**Dependencies**: Foundation (A), Processors (B), Integration (C), Testing (D)

## Task Overview
Update knowledge documentation to reflect new enhanced processing capabilities. Include configuration options, usage examples, before/after comparisons, migration guidance, and architecture diagrams. Create comprehensive guide for users and developers.

## Context & Background
Documentation is essential for successful adoption of the knowledge enhancement system. Users need clear guidance on configuration, usage patterns, and migration from existing setups.

**Affected systems:**
- @genie/wishes/knowledge-enhancement-wish.md - Documentation requirements [line 328-333]
- @genie/reports/forge-plan-knowledge-enhancement-202510141240.md - Documentation scope
- @lib/knowledge/CLAUDE.md - Current knowledge documentation to update
- @CLAUDE.md - Documentation standards

## Advanced Prompting Instructions

<context_gathering>
Review all implemented components, understand user workflows, identify documentation gaps
Tool budget: focused on comprehensive documentation
reasoning_effort: low/think
</context_gathering>

<task_breakdown>
1. [Discovery] Analyze documentation needs
   - Review current CLAUDE.md structure
   - Identify all new features to document
   - Plan documentation organization
   - Gather usage examples

2. [Implementation] Create comprehensive documentation
   - Update architecture overview
   - Document configuration reference
   - Add usage examples and patterns
   - Create before/after comparisons
   - Write migration guide
   - Include troubleshooting section

3. [Verification] Validate documentation quality
   - Ensure all features documented
   - Verify code examples work
   - Check configuration accuracy
   - Confirm migration steps
</task_breakdown>

<success_criteria>
✅ lib/knowledge/CLAUDE.md updated comprehensively
✅ Configuration reference matches YAML structure
✅ Before/after examples demonstrate improvements
✅ Usage patterns documented for common scenarios
✅ Migration guide for existing users
✅ Troubleshooting section included
✅ Architecture diagrams updated
✅ Code examples tested and working
</success_criteria>

<never_do>
❌ Leave features undocumented
❌ Include outdated information
❌ Skip migration guidance
❌ Forget configuration examples
❌ Omit troubleshooting tips
</never_do>

## Documentation Structure

### Updated lib/knowledge/CLAUDE.md Outline

```markdown
# CLAUDE.md - Knowledge System

## Overview
- Enhanced document processing capabilities
- Automatic metadata enrichment
- Semantic chunking for LLM optimization
- Brazilian Portuguese support

## Architecture

### System Components
```
lib/knowledge/
├── processors/                    # Document processing pipeline
│   ├── document_processor.py     # Main orchestrator
│   ├── type_detector.py         # Document type detection
│   ├── entity_extractor.py      # Entity extraction
│   ├── metadata_enricher.py     # Metadata generation
│   └── semantic_chunker.py      # Smart chunking
├── config/
│   ├── knowledge_processing.yaml # Processing configuration
│   ├── processing_config.py     # Pydantic models
│   └── config_loader.py         # Configuration loader
├── filters/
│   └── enhanced_filters.py      # New metadata filters
└── row_based_csv_knowledge.py   # Enhanced knowledge base
```

## Quick Start

### Enabling Enhanced Processing
```python
from lib.knowledge.factories.knowledge_factory import get_knowledge_base

# Create knowledge base with processing
kb = get_knowledge_base(
    processing_enabled=True,  # Enable enhancement
    num_documents=5
)
```

### Configuration

#### Global Settings (.env)
```bash
HIVE_ENABLE_ENHANCED_KNOWLEDGE=true
HIVE_KNOWLEDGE_CONFIG_PATH=/custom/path/config.yaml  # Optional
```

#### Processing Configuration (knowledge_processing.yaml)
```yaml
processing:
  enabled: true
  parallel: true
  accuracy_threshold: 0.7

type_detection:
  use_filename: true
  use_content: true
  confidence_threshold: 0.7

chunking:
  method: "semantic"  # or "fixed"
  min_size: 500
  max_size: 1500
  overlap: 50
  preserve_tables: true

entity_extraction:
  enabled: true
  extract_dates: true
  extract_amounts: true
  extract_names: true
  extract_organizations: true

  # Custom entities for your domain
  custom_entities:
    - name: "products"
      patterns: ["PIX", "Cartão", "Boleto"]
    - name: "account_numbers"
      regex: '\d{4}-\d{4}-\d{4}-\d{4}'

business_unit_detection:
  enabled: true
  auto_detect: true
  keywords:
    pagbank: ["pix", "conta", "transferencia"]
    adquirencia: ["maquina", "vendas"]
```

## Features

### Document Type Detection
- Automatic detection from filename and content
- Brazilian document patterns supported
- Configurable confidence thresholds

### Entity Extraction
- **Built-in Types**:
  - Dates (DD/MM/YYYY, MM/YYYY)
  - Amounts (R$ format)
  - People names
  - Organizations

- **Custom Entities**:
  ```yaml
  custom_entities:
    - name: "cpf"
      regex: '\d{3}\.\d{3}\.\d{3}-\d{2}'
    - name: "invoice_numbers"
      patterns: ["NF-", "NFe-"]
  ```

### Semantic Chunking
- LLM-optimized chunk sizes
- Preserves document structure
- Table and paragraph awareness
- Context overlap for continuity

### Business Unit Auto-Detection
- Keyword-based classification
- Automatic routing to domains
- Configurable per business unit

## Usage Examples

### Basic Document Processing
```python
from lib.knowledge.processors.document_processor import DocumentProcessor
from lib.knowledge.config.config_loader import load_knowledge_config

# Load configuration
config = load_knowledge_config()

# Create processor
processor = DocumentProcessor(config)

# Process document
document = {
    "content": "Financial report content...",
    "name": "report_july.pdf"
}

result = processor.process(document)
print(f"Type: {result.metadata['document_type']}")
print(f"Entities: {result.metadata['extracted_entities']}")
```

### Filtering Enhanced Documents
```python
from lib.knowledge.filters.enhanced_filters import EnhancedKnowledgeFilter

# Filter by document type
financial_docs = EnhancedKnowledgeFilter.filter_by_document_type(
    documents, ["financial", "invoice"]
)

# Filter by date range
july_docs = EnhancedKnowledgeFilter.filter_by_date_range(
    documents,
    start_date="2025-07-01",
    end_date="2025-07-31"
)

# Filter by custom entities
pix_docs = EnhancedKnowledgeFilter.filter_by_custom_entities(
    documents,
    entity_type="products",
    entity_values=["PIX"]
)
```

## Before/After Comparison

### Before (Raw Chunks)
```json
{
  "content": "DESPESASDespesa com Pessoal Salários 13.239,00 07/2025",
  "metadata": {
    "page": 1,
    "chunk": 0,
    "chunk_size": 100
  }
}
```

### After (Enhanced Processing)
```json
{
  "content": "DESPESAS COM PESSOAL\nSalários: R$ 13.239,00\nPeríodo: 07/2025",
  "metadata": {
    "document_type": "financial",
    "category": "payroll",
    "business_unit": "hr",
    "tags": ["expenses", "salaries", "july_2025"],
    "extracted_entities": {
      "dates": ["07/2025"],
      "amounts": [13239.00],
      "period": "07/2025"
    },
    "chunking_method": "semantic",
    "confidence_score": 0.95
  }
}
```

## Migration Guide

### For Existing Users

1. **Enable Processing Gradually**:
   ```python
   # Start with processing disabled to test
   kb = get_knowledge_base(processing_enabled=False)

   # Enable when ready
   kb = get_knowledge_base(processing_enabled=True)
   ```

2. **Configure for Your Domain**:
   - Copy `knowledge_processing.yaml` template
   - Adjust entity patterns for your use case
   - Define business unit keywords
   - Test with sample documents

3. **Update Filters**:
   ```python
   # Old filtering
   docs = [d for d in kb.documents if "financial" in d.content]

   # New filtering
   from lib.knowledge.filters.enhanced_filters import EnhancedKnowledgeFilter
   docs = EnhancedKnowledgeFilter.filter_by_document_type(
       kb.documents, ["financial"]
   )
   ```

### Important Notes
- **CSV documents unchanged**: Existing CSV knowledge preserved
- **Forward-only**: Only new API uploads enhanced
- **Toggleable**: Can disable anytime via config
- **Backwards compatible**: Old code continues working

## Performance Considerations

### Optimization Tips
- Enable parallel processing for batch documents
- Adjust chunk sizes based on LLM context window
- Use type detection confidence threshold
- Cache processing config for performance

### Benchmarks
- 100 documents: <10 seconds
- Memory usage: <500MB
- Parallel speedup: 2-3x
- Accuracy: >85% for Brazilian documents

## Troubleshooting

### Common Issues

**Processing not working:**
```python
# Check if enabled
from lib.config.settings import settings
print(settings().hive_enable_enhanced_knowledge)

# Verify config loads
from lib.knowledge.config.config_loader import load_knowledge_config
config = load_knowledge_config()
print(config.enabled)
```

**Custom entities not extracted:**
```yaml
# Ensure regex is properly escaped in YAML
custom_entities:
  - name: "cpf"
    regex: '\\d{3}\\.\\d{3}\\.\\d{3}-\\d{2}'  # Note double backslash
```

**Performance issues:**
```python
# Enable parallel processing
config.parallel = True

# Reduce chunk overlap
config.chunking.overlap = 20
```

## API Reference

### DocumentProcessor
```python
class DocumentProcessor:
    def __init__(self, config: ProcessingConfig)
    def process(self, document: Dict) -> ProcessedDocument
```

### ProcessedDocument
```python
@dataclass
class ProcessedDocument:
    content: str
    metadata: Dict[str, Any]
    chunks: List[Dict[str, Any]]
```

### Configuration Models
- `ProcessingConfig`: Main configuration
- `TypeDetectionConfig`: Type detection settings
- `ChunkingConfig`: Chunking parameters
- `EntityExtractionConfig`: Entity extraction settings

## Advanced Topics

### Custom Entity Types
Create domain-specific extractors:
```python
class CustomEntityExtractor(EntityExtractor):
    def extract_invoice_numbers(self, content: str) -> List[str]:
        pattern = r'NF[eE]?\s*\d+'
        return re.findall(pattern, content)
```

### PDF Processing
Based on library selection from A/B testing:
```python
# Using selected library (e.g., docling)
from lib.knowledge.processors.pdf_processor import PDFProcessor

processor = PDFProcessor()
extracted_text = processor.extract(pdf_path)
```

### Extending Metadata
Add custom metadata fields:
```python
class CustomMetadataEnricher(MetadataEnricher):
    def enrich(self, document, doc_type, entities):
        metadata = super().enrich(document, doc_type, entities)
        metadata["custom_field"] = self.compute_custom_value(document)
        return metadata
```

## Testing

### Running Tests
```bash
# Unit tests
uv run pytest tests/lib/knowledge/processors/ -v

# Integration tests
uv run pytest tests/integration/test_enhanced_knowledge_e2e.py -v

# Performance tests
uv run pytest tests/lib/knowledge/test_processing_performance.py -v
```

### Coverage Report
```bash
uv run pytest tests/ \
  --cov=lib/knowledge \
  --cov-report=html
```

## Contributing

### Adding New Processors
1. Create processor class inheriting base
2. Add configuration schema
3. Write comprehensive tests
4. Update documentation

### Submitting Changes
1. Follow TDD methodology
2. Ensure >85% test coverage
3. Update CLAUDE.md documentation
4. Run full test suite

## Related Documentation
- [Main CLAUDE.md](../../CLAUDE.md) - Project guidelines
- [AI System](../../ai/CLAUDE.md) - Agent integration
- [Configuration](../config/CLAUDE.md) - Settings management
```

## Technical Constraints
- Documentation must be accurate and tested
- Code examples must be working
- Configuration must match implementation
- Migration steps must be safe

## Reasoning Configuration
reasoning_effort: low/think
verbosity: high (comprehensive documentation)

## Success Validation
```bash
# Verify documentation examples work
uv run python -c "
from lib.knowledge.factories.knowledge_factory import get_knowledge_base
kb = get_knowledge_base(processing_enabled=True)
print('✅ Documentation example works')
"

# Test configuration loading
uv run python -c "
from lib.knowledge.config.config_loader import load_knowledge_config
config = load_knowledge_config()
print(f'✅ Config loaded: {config.enabled}')
"

# Verify filter examples
uv run python -c "
from lib.knowledge.filters.enhanced_filters import EnhancedKnowledgeFilter
print('✅ Filter imports work')
"
```

## Deliverables
1. **Updated CLAUDE.md** with complete documentation
2. **Configuration reference** with all options
3. **Usage examples** for common scenarios
4. **Before/after comparisons** showing improvements
5. **Migration guide** for existing users
6. **Troubleshooting section** for common issues
7. **API reference** for developers

## Documentation Quality Checklist
- ✅ All features documented
- ✅ Code examples tested
- ✅ Configuration accurate
- ✅ Migration steps clear
- ✅ Troubleshooting helpful
- ✅ Performance tips included
- ✅ API reference complete
- ✅ Related links working

## Commit Format
```
Wish knowledge-enhancement: comprehensive documentation and knowledge transfer

- Updated lib/knowledge/CLAUDE.md with full guide
- Added configuration reference and examples
- Created before/after comparisons
- Wrote migration guide for users
- Included troubleshooting section
- Added API reference

Co-Authored-By: Automagik Genie <genie@namastex.ai>
```