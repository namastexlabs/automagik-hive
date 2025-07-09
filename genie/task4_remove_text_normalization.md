# Task 4: Remove Text Normalization

## Objective
Remove the text normalization preprocessing step entirely as Claude Sonnet 4 is intelligent enough to understand Portuguese variations, misspellings, and abbreviations.

## Rationale
- Modern LLMs like Claude understand context and language variations
- Text normalization adds unnecessary complexity
- Preprocessing overhead without real benefit
- Models can handle "cartao"/"cartão", "pra"/"para", "vc"/"você" naturally

## Implementation Plan

### Phase 1: Identify Dependencies
Files to modify/remove:
- `/orchestrator/text_normalizer.py` - Remove entirely
- `/agents/orchestrator/main_orchestrator.py` - Remove normalization calls
- Any imports of text_normalizer
- Update routing prompt to remove normalization instructions

### Phase 2: Code Changes

#### 1. Delete Text Normalizer Module
```bash
rm orchestrator/text_normalizer.py
```

#### 2. Update Main Orchestrator
Remove:
- Import of text_normalizer
- `normalize_text()` method
- `text_normalizer` references in preprocessing
- Normalization instructions from routing prompt

#### 3. Update Preprocessing Pipeline
Current flow:
```
Message → Normalize → Detect Frustration → Route
```

New flow:
```
Message → Detect Frustration → Route
```

### Phase 3: Testing
- Test with various Portuguese misspellings
- Verify agents still understand:
  - "cartao" (without accent)
  - "pra" (abbreviation)
  - "vc" (abbreviation)
  - Common typos

### Phase 4: Documentation Updates
- Remove text normalization from README
- Update architecture diagrams
- Update ARCHITECTURE_DETAILED.md
- Remove from preprocessing pipeline docs

## Expected Benefits
- Simpler codebase
- Faster preprocessing
- Less maintenance
- Trust in model capabilities

Co-Authored-By: Automagik Genie <genie@namastex.ai>