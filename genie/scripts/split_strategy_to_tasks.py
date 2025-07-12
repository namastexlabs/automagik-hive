#!/usr/bin/env python3
"""
Script to mechanically split the platform strategy document into separate task cards
"""

import re
from pathlib import Path

# Read the strategy file
strategy_file = Path("/home/namastex/workspace/pagbank-multiagents/genie/active/pagbank-agents-platform-strategy.md")
with open(strategy_file, 'r') as f:
    content = f.read()

# Define the sections to extract as separate task cards
task_cards = {
    # Shared context files
    "shared/00-platform-context.md": {
        "start": "# PagBank Agents Platform - Technical Implementation Plan",
        "end": "### Complete API Endpoints",
        "title": "Platform Context and Overview"
    },
    "shared/01-api-endpoints.md": {
        "start": "### Complete API Endpoints",
        "end": "### Folder Structure",
        "title": "API Endpoints Reference"
    },
    "shared/02-folder-structure.md": {
        "start": "### Folder Structure",
        "end": "### Ana Team Configuration",
        "title": "Project Folder Structure"
    },
    
    # Configuration examples
    "shared/03-yaml-configurations.md": {
        "start": "### Ana Team Configuration",
        "end": "### NEW: Conversation Typification Workflow",
        "title": "YAML Configuration Examples"
    },
    
    # Phase 1 tasks
    "phase1/01-refactor-ana-team.md": {
        "start": "1. **Refactor Ana Team**",
        "end": "2. **Setup Database Infrastructure**",
        "title": "Refactor Ana Team to Simple Mode Route"
    },
    "phase1/02-database-infrastructure.md": {
        "start": "2. **Setup Database Infrastructure**",
        "end": "3. **Create Base API Structure**",
        "title": "Setup Database Infrastructure"
    },
    "phase1/03-base-api-structure.md": {
        "start": "3. **Create Base API Structure**",
        "end": "4. **Migrate Existing Agents**",
        "title": "Create Base API Structure"
    },
    "phase1/04-migrate-agents.md": {
        "start": "4. **Migrate Existing Agents**",
        "end": "### Phase 2: Platform Core",
        "title": "Migrate Existing Agents"
    },
    
    # Phase 2 tasks
    "phase2/01-agent-versioning.md": {
        "start": "1. **Agent Versioning System**",
        "end": "2. **Typification Workflow**",
        "title": "Implement Agent Versioning System"
    },
    "phase2/02-typification-workflow.md": {
        "start": "### NEW: Conversation Typification Workflow",
        "end": "### Typification as Workflow",
        "title": "Build Typification Workflow"
    },
    "phase2/03-configuration-hotreload.md": {
        "start": "3. **Configuration Hot Reload**",
        "end": "### Phase 3: Production Features",
        "title": "Configuration Hot Reload System"
    },
    
    # Phase 3 tasks
    "phase3/01-enhanced-monitoring.md": {
        "start": "1. **Enhanced Monitoring**",
        "end": "2. **Advanced Playground**",
        "title": "Enhanced Monitoring and Metrics"
    },
    "phase3/02-advanced-playground.md": {
        "start": "### Advanced Playground Configuration",
        "end": "### API Implementation",
        "title": "Advanced Playground Setup"
    },
    "phase3/03-security-compliance.md": {
        "start": "3. **Security & Compliance**",
        "end": "4. **Load Testing & Optimization**",
        "title": "Security and Compliance Features"
    },
    
    # Implementation details
    "shared/04-database-schema.md": {
        "start": "### NEW: Configuration Management Database Schema",
        "end": "### Configuration Migration System",
        "title": "Database Schema Definitions"
    },
    "shared/05-config-migration.md": {
        "start": "### Configuration Migration System",
        "end": "### Database-Driven Configuration API",
        "title": "Configuration Migration System"
    },
    "shared/06-database-api.md": {
        "start": "### Database-Driven Configuration API",
        "end": "### Agent Registry",
        "title": "Database-Driven Configuration API"
    },
    "shared/07-dependencies.md": {
        "start": "### UV Dependencies",
        "end": "### Settings Compatibility Matrix",
        "title": "UV Dependencies and Project Setup"
    },
    "shared/08-implementation-timeline.md": {
        "start": "## Implementation Timeline & Migration Strategy",
        "end": None,  # Goes to end of file
        "title": "Complete Implementation Timeline"
    }
}

# Create task card directories
base_dir = Path("/home/namastex/workspace/pagbank-multiagents/genie/task-cards")

# Function to extract content between markers
def extract_section(content, start_marker, end_marker):
    if start_marker not in content:
        return None
    
    start_idx = content.find(start_marker)
    if end_marker and end_marker in content[start_idx:]:
        end_idx = content.find(end_marker, start_idx)
        return content[start_idx:end_idx].strip()
    else:
        # If no end marker, go to end of file
        return content[start_idx:].strip()

# Split and save each task card
for file_path, markers in task_cards.items():
    full_path = base_dir / file_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract section
    section_content = extract_section(content, markers["start"], markers.get("end"))
    
    if section_content:
        # Add header to each task card
        task_content = f"""# Task Card: {markers['title']}

## Overview
This task card is part of the PagBank Multi-Agent Platform migration.

## Reference
- Main strategy: `/genie/active/pagbank-agents-platform-strategy.md`
- Demo app reference: `/genie/agno-demo-app/`

---

{section_content}

---

## Validation Steps
TODO: Add specific validation steps for this task

## Dependencies
TODO: List dependencies on other task cards

Co-Authored-By: Automagik Genie <genie@namastex.ai>
"""
        
        with open(full_path, 'w') as f:
            f.write(task_content)
        print(f"✅ Created: {file_path}")
    else:
        print(f"❌ Failed to extract: {file_path}")

print("\n📋 Task cards created successfully!")
print(f"Total cards: {len(task_cards)}")