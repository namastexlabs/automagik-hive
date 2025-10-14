# Forge Task: Foundation & Configuration

**Task ID**: knowledge-enhancement-foundation
**Branch**: wish/knowledge-enhancement
**Complexity**: 6
**Agent**: hive-coder
**Dependencies**: None (parallel with PDF Testing task)

## Task Overview
Create all foundational models and configuration infrastructure for the knowledge processing system. This includes Pydantic schemas for metadata validation, dedicated YAML configuration file separate from agent configs, and config loader utility with environment variable override support.

## Context & Background
The Knowledge Enhancement System needs robust data models and configuration management to support document processing. This foundation layer enables all subsequent processors and ensures type safety throughout the system.

**Affected systems:**
- @genie/wishes/knowledge-enhancement-wish.md - Complete wish specification with configuration architecture
- @genie/reports/forge-plan-knowledge-enhancement-202510141240.md - Approved execution plan with foundation requirements
- @lib/knowledge/row_based_csv_knowledge.py - Current implementation to extend
- @lib/config/settings.py - Pattern reference for settings integration
- @CLAUDE.md - Project patterns and configuration standards

## Advanced Prompting Instructions

<context_gathering>
Analyze existing config patterns in lib/config/, understand Pydantic validation requirements
Tool budget: focused on config structure and model design
reasoning_effort: medium/think hard
</context_gathering>

<task_breakdown>
1. [Discovery] Analyze existing configuration patterns
   - Study lib/config/settings.py for Pydantic patterns
   - Review lib/knowledge/ for current structures
   - Identify integration points for new config

2. [Implementation] Build foundation components
   - Create Pydantic metadata models
   - Define ProcessingConfig schema
   - Implement config loader with search paths
   - Create dedicated YAML configuration file
   - Integrate with global settings

3. [Verification] Validate foundation stability
   - Test model validation with sample data
   - Verify config loading from multiple sources
   - Ensure environment variable overrides work
   - Confirm backwards compatibility
</task_breakdown>

<success_criteria>
✅ EnhancedMetadata, ExtractedEntities, DocumentType models created
✅ ProcessingConfig Pydantic model validates YAML config
✅ lib/knowledge/config/knowledge_processing.yaml loads successfully
✅ Config loader searches paths: custom → default → built-in
✅ Settings expose hive_enable_enhanced_knowledge flag
✅ Settings support hive_knowledge_config_path override
✅ Unit tests validate all models and config loading
✅ No impact on existing CSV knowledge loading
</success_criteria>

<never_do>
❌ Mix processing config with agent configs
❌ Hardcode configuration paths
❌ Skip Pydantic validation
❌ Break existing configuration patterns
❌ Forget environment variable support
</never_do>

## Technical Implementation

### Metadata Models Structure
```python
# lib/models/knowledge_metadata.py

from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime

class DocumentType(str, Enum):
    FINANCIAL = "financial"
    REPORT = "report"
    INVOICE = "invoice"
    CONTRACT = "contract"
    MANUAL = "manual"
    GENERAL = "general"

class ExtractedEntities(BaseModel):
    dates: List[str] = Field(default_factory=list)
    amounts: List[float] = Field(default_factory=list)
    people: List[str] = Field(default_factory=list)
    organizations: List[str] = Field(default_factory=list)
    period: Optional[str] = None
    custom: Dict[str, List[str]] = Field(default_factory=dict)

class EnhancedMetadata(BaseModel):
    document_type: DocumentType = DocumentType.GENERAL
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    business_unit: Optional[str] = None
    extracted_entities: ExtractedEntities
    total_amount: Optional[float] = None
    urgency_level: Optional[str] = None
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = Field(ge=0, le=1, default=0.0)
```

### Processing Config Schema
```python
# lib/knowledge/config/processing_config.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class TypeDetectionConfig(BaseModel):
    use_filename: bool = True
    use_content: bool = True
    confidence_threshold: float = Field(ge=0, le=1, default=0.7)

class ChunkingConfig(BaseModel):
    method: str = Field(default="semantic", pattern="^(semantic|fixed)$")
    min_size: int = Field(ge=100, le=2000, default=500)
    max_size: int = Field(ge=500, le=5000, default=1500)
    overlap: int = Field(ge=0, le=200, default=50)
    preserve_tables: bool = True
    preserve_code_blocks: bool = True

class CustomEntity(BaseModel):
    name: str
    patterns: Optional[List[str]] = None
    regex: Optional[str] = None

class EntityExtractionConfig(BaseModel):
    enabled: bool = True
    extract_dates: bool = True
    extract_amounts: bool = True
    extract_names: bool = True
    extract_organizations: bool = True
    custom_entities: List[CustomEntity] = Field(default_factory=list)

class ProcessingConfig(BaseModel):
    enabled: bool = True
    parallel: bool = True
    accuracy_threshold: float = Field(ge=0, le=1, default=0.7)
    type_detection: TypeDetectionConfig = Field(default_factory=TypeDetectionConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    entity_extraction: EntityExtractionConfig = Field(default_factory=EntityExtractionConfig)
    business_unit_detection: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### Default Configuration File
```yaml
# lib/knowledge/config/knowledge_processing.yaml

processing:
  enabled: true
  parallel: true
  accuracy_threshold: 0.7

type_detection:
  use_filename: true
  use_content: true
  confidence_threshold: 0.7

chunking:
  method: "semantic"
  min_size: 500
  max_size: 1500
  overlap: 50
  preserve_tables: true
  preserve_code_blocks: true

entity_extraction:
  enabled: true
  extract_dates: true
  extract_amounts: true
  extract_names: true
  extract_organizations: true
  custom_entities:
    - name: "products"
      patterns: ["PIX", "Cartão", "Antecipação", "Boleto"]
    - name: "locations"
      patterns: ["São Paulo", "Rio de Janeiro", "Brasil"]
    - name: "account_numbers"
      regex: '\d{4}-\d{4}-\d{4}-\d{4}'

business_unit_detection:
  enabled: true
  auto_detect: true
  keywords:
    pagbank: ["pix", "conta", "app", "transferencia"]
    adquirencia: ["antecipacao", "vendas", "maquina"]
    emissao: ["cartao", "limite", "credito"]

metadata:
  auto_categorize: true
  auto_tag: true
  detect_urgency: true
```

### Config Loader Implementation
```python
# lib/knowledge/config/config_loader.py

from pathlib import Path
import yaml
import os
from typing import Optional
from .processing_config import ProcessingConfig

def load_knowledge_config(custom_path: Optional[str] = None) -> ProcessingConfig:
    """
    Load knowledge processing configuration.

    Search order:
    1. Custom path from parameter or environment
    2. lib/knowledge/config/knowledge_processing.yaml
    3. config/knowledge_processing.yaml
    4. Built-in defaults
    """
    # Check environment override
    env_path = os.getenv("HIVE_KNOWLEDGE_CONFIG_PATH")
    config_path = custom_path or env_path

    search_paths = [
        Path(config_path) if config_path else None,
        Path("lib/knowledge/config/knowledge_processing.yaml"),
        Path("config/knowledge_processing.yaml"),
    ]

    for path in search_paths:
        if path and path.exists():
            with path.open() as f:
                config_dict = yaml.safe_load(f)
                return ProcessingConfig(**config_dict.get("processing", {}))

    # Return defaults if no config found
    return ProcessingConfig()
```

### Settings Integration
```python
# Additions to lib/config/settings.py

class HiveSettings(BaseSettings):
    # ... existing fields ...

    # Knowledge Enhancement Configuration
    hive_enable_enhanced_knowledge: bool = Field(default=True)
    hive_knowledge_config_path: Optional[str] = Field(default=None)

    @field_validator('hive_knowledge_config_path')
    def validate_knowledge_config_path(cls, v):
        if v and not Path(v).exists():
            raise ValueError(f'Knowledge config path does not exist: {v}')
        return v
```

## Technical Constraints
- Must use Pydantic v2+ for validation
- Configuration must be YAML-based
- Support environment variable overrides
- Maintain backwards compatibility
- Follow existing project patterns

## Reasoning Configuration
reasoning_effort: medium/think hard
verbosity: low (concise implementation)

## Success Validation
```bash
# Test metadata models
uv run pytest tests/lib/models/test_knowledge_metadata.py -v

# Test config loading
uv run pytest tests/lib/knowledge/config/test_config_loader.py -v

# Test settings integration
uv run pytest tests/lib/config/test_settings_knowledge.py -v

# Validate YAML config
uv run python -c "from lib.knowledge.config.config_loader import load_knowledge_config; print(load_knowledge_config())"
```

## Deliverables
1. **Metadata models** in `lib/models/knowledge_metadata.py`
2. **ProcessingConfig** in `lib/knowledge/config/processing_config.py`
3. **YAML config** in `lib/knowledge/config/knowledge_processing.yaml`
4. **Config loader** in `lib/knowledge/config/config_loader.py`
5. **Settings integration** in `lib/config/settings.py`
6. **Unit tests** for all components

## Integration Points for Next Tasks
- Group B processors will import and use these models
- Config loader will be used by document processor
- Settings flags control feature activation
- YAML config drives all processing behavior

## Commit Format
```
Wish knowledge-enhancement: implement foundation models and configuration

- Created Pydantic models for enhanced metadata
- Added ProcessingConfig schema with validation
- Implemented config loader with search paths
- Created dedicated YAML configuration file
- Integrated with global settings

Co-Authored-By: Automagik Genie <genie@namastex.ai>
```