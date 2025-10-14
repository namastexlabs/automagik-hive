# Forge Task Master Report: Knowledge Enhancement Foundation
**Generated**: 2025-10-14 12:50 UTC
**Wish**: knowledge-enhancement-wish
**Group**: Foundation & Configuration
**Complexity**: 5/10 (Medium - Multi-file feature with configuration)

## Task Creation Summary

### Task Details
- **Title**: `feat: knowledge enhancement foundation with config and models`
- **Branch**: `feat/knowledge-foundation-config`
- **Primary Agent**: @hive-coder
- **Reasoning Effort**: medium/think hard

## Task Description

### Task Overview
Implement foundation layer for enhanced knowledge system including Pydantic models for metadata, configuration schema validation, YAML-based processing config, and global settings integration.

### Context & Background
Building the foundation for an enhanced knowledge processing system that will support document type detection, intelligent chunking, entity extraction, and business unit classification. This foundation layer provides the configuration and data models needed by all downstream processing components.

**Complete Context Loading:**
@genie/wishes/knowledge-enhancement-wish.md - Complete wish specification with requirements
@genie/reports/forge-plan-knowledge-enhancement-202510141240.md - Planning report with task breakdown
@lib/models/ - Existing model patterns to follow
@lib/config/settings.py - Settings architecture for integration
@lib/knowledge/row_based_csv_knowledge.py - Current knowledge base implementation
@lib/knowledge/config/ - New configuration directory (to be created)
@CLAUDE.md - Project-wide patterns and standards
@ai/CLAUDE.md - AI domain patterns and conventions
@ai/agents/CLAUDE.md - Agent patterns for future integration
@lib/knowledge/CLAUDE.md - Knowledge system documentation

## Advanced Prompting Instructions

<context_gathering>
Start by examining existing patterns in lib/models/ and lib/config/
Focus on Pydantic model conventions and settings integration patterns
Process configuration requirements from wish document
</context_gathering>

<task_breakdown>
1. [Discovery] Analyze existing model and config patterns
   - Review lib/models/ for Pydantic conventions
   - Study lib/config/settings.py integration points
   - Map configuration requirements from wish

2. [Implementation] Build foundation components
   - Create metadata models with validation
   - Implement config schema with defaults
   - Build config loader with search paths
   - Integrate with global settings

3. [Verification] Validate all components work together
   - Test model validation with sample data
   - Verify config loading from YAML
   - Confirm settings integration
   - Ensure zero impact on existing code
</task_breakdown>

<success_criteria>
✅ All Pydantic models validate Brazilian document metadata
✅ Config loader implements env → default → built-in fallback chain
✅ YAML config structure matches specification exactly
✅ Settings integration provides global toggle and path override
✅ Complete test coverage for all new components
✅ Zero breaking changes to existing knowledge system
</success_criteria>

<never_do>
❌ Put configuration in agent YAML files (must be centralized)
❌ Hardcode values that should be configurable
❌ Skip validation for custom entity patterns
❌ Break existing knowledge base functionality
❌ Forget Brazilian Portuguese support in defaults
</never_do>

## Technical Implementation Details

### 1. Metadata Models (lib/models/knowledge_metadata.py)
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum

class DocumentType(str, Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    REPORT = "report"
    EMAIL = "email"
    FAQ = "faq"
    MANUAL = "manual"
    SPECIFICATION = "specification"
    GENERAL = "general"

class ExtractedEntities(BaseModel):
    dates: List[str] = Field(default_factory=list)
    amounts: List[str] = Field(default_factory=list)
    names: List[str] = Field(default_factory=list)
    organizations: List[str] = Field(default_factory=list)
    custom: Dict[str, List[str]] = Field(default_factory=dict)

class EnhancedMetadata(BaseModel):
    document_type: DocumentType = DocumentType.GENERAL
    confidence_score: float = Field(ge=0.0, le=1.0)
    business_unit: Optional[str] = None
    extracted_entities: ExtractedEntities = Field(default_factory=ExtractedEntities)
    processing_date: str
    chunk_info: Optional[Dict[str, Any]] = None
    source_file: Optional[str] = None
```

### 2. Processing Config Schema (lib/knowledge/config/processing_config.py)
```python
class CustomEntity(BaseModel):
    name: str
    patterns: Optional[List[str]] = None
    regex: Optional[str] = None

class ProcessingConfig(BaseModel):
    processing: ProcessingSettings
    type_detection: TypeDetectionConfig
    chunking: ChunkingConfig
    entity_extraction: EntityExtractionConfig
    business_unit_detection: BusinessUnitConfig
```

### 3. Default Configuration (lib/knowledge/config/knowledge_processing.yaml)
Full YAML structure as specified in task bundling, with Brazilian document patterns and business unit keywords.

### 4. Config Loader (lib/knowledge/config/config_loader.py)
```python
def load_knowledge_config() -> ProcessingConfig:
    # Search order implementation
    # 1. Check env var HIVE_KNOWLEDGE_CONFIG_PATH
    # 2. Load lib/knowledge/config/knowledge_processing.yaml
    # 3. Fall back to built-in defaults
    # Return validated ProcessingConfig
```

### 5. Settings Integration (lib/config/settings.py)
```python
class HiveSettings(BaseSettings):
    # Add new fields
    hive_enable_enhanced_knowledge: bool = True
    hive_knowledge_config_path: Optional[str] = None

    @field_validator('hive_knowledge_config_path')
    def validate_config_path(cls, v):
        if v and not Path(v).exists():
            raise ValueError(f"Config path does not exist: {v}")
        return v
```

## Testing Requirements

### Unit Tests Structure
```
tests/lib/
├── models/
│   └── test_knowledge_metadata.py
└── knowledge/
    └── config/
        ├── test_config_loader.py
        └── test_processing_config.py
```

### Test Coverage Requirements
- Model validation with edge cases
- Config loading with missing files
- Settings integration validation
- Brazilian Portuguese entity extraction
- Custom entity pattern matching

## Technical Constraints
- Must use Pydantic v2 patterns
- Config must be YAML (not JSON)
- Support both pattern and regex for custom entities
- Maintain backward compatibility

## Reasoning Configuration
reasoning_effort: medium/think hard
verbosity: low (status updates), high (code implementation)

## Complexity Assessment
**Score: 5/10** - Medium complexity due to:
- Multiple integrated components
- Configuration schema design
- Settings integration
- Test coverage requirements
- But no external dependencies or breaking changes

## Validation Checklist
- [ ] All Pydantic models created and validated
- [ ] YAML config matches exact specification
- [ ] Config loader implements search priority
- [ ] Settings integration complete
- [ ] All tests passing
- [ ] No impact on existing code
- [ ] Brazilian Portuguese defaults included

## Human Follow-up Actions
1. Review task creation confirmation
2. Monitor agent execution progress
3. Validate test coverage reports
4. Review Death Testament for completion
5. Approve for next group execution

## Task Dependencies
- **Upstream**: None (foundation layer)
- **Downstream**: All other knowledge enhancement groups depend on this

## Estimated Completion
- Agent Time: 15-20 minutes
- Components: 5 files + tests
- Verification: 5-10 minutes

## Branch Strategy
Create feature branch: `feat/knowledge-foundation-config`
- Isolated from main development
- Clean commits with descriptive messages
- Ready for integration testing

---

**Death Testament**: Task created with comprehensive context loading and complete implementation specifications. All @ references included for perfect agent isolation and execution.