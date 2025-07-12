#!/usr/bin/env python3
"""Script to update imports after folder reorganization"""

import os
import re
from pathlib import Path

def update_file(filepath):
    """Update imports in a single file"""
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Update orchestrator imports
    content = re.sub(r'from orchestrator\.', 'from agents.orchestrator.', content)
    content = re.sub(r'import agents.orchestrator\.', 'import agents.orchestrator.', content)
    content = re.sub(r'import agents.orchestrator\b', 'import agents.orchestrator', content)
    
    # Update knowledge imports
    content = re.sub(r'from knowledge\.', 'from context.knowledge.', content)
    content = re.sub(r'import context.knowledge\.', 'import context.knowledge.', content)
    content = re.sub(r'import context.knowledge\b', 'import context.knowledge', content)
    
    # Update memory imports
    content = re.sub(r'from memory\.', 'from context.memory.', content)
    content = re.sub(r'import context.memory\.', 'import context.memory.', content)
    content = re.sub(r'import context.memory\b', 'import context.memory', content)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Updated: {filepath}")
        return True
    return False

def main():
    """Update all Python files"""
    
    root_dir = Path(__file__).parent.parent
    updated_count = 0
    
    # Find all Python files
    for filepath in root_dir.rglob('*.py'):
        # Skip venv and __pycache__
        if '.venv' in str(filepath) or '__pycache__' in str(filepath):
            continue
        
        if update_file(filepath):
            updated_count += 1
    
    print(f"\nTotal files updated: {updated_count}")

if __name__ == "__main__":
    main()