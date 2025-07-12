#!/usr/bin/env python3
"""
Clean task cards:
1. Remove all time references (days, hours, weeks)
2. Remove migration/backwards compatibility references
3. Update to V2 clean rewrite approach
"""

import re
from pathlib import Path

task_cards_dir = Path("/home/namastex/workspace/pagbank-multiagents/genie/task-cards")

# Patterns to remove/replace
patterns = [
    # Remove time durations
    (r'\*\*Duration\*\*: \d+ days?\s*\n', ''),
    (r'\*\*Duration\*\*: \d+ hours?\s*\n', ''),
    (r'\(?\d+ days?\)?', ''),
    (r'\(?\d+ hours?\)?', ''),
    (r'\(?\d+ weeks?\)?', ''),
    (r'Week \d+-\d+', ''),
    (r'### Phase \d+: [^\n]+ \(Week[^\)]+\)', lambda m: m.group(0).split('(')[0].strip()),
    
    # Update migration references
    (r'migration', 'V2 implementation'),
    (r'Migration', 'V2 Implementation'),
    (r'migrate', 'implement in V2'),
    (r'Migrate', 'Implement in V2'),
    (r'migrator', 'V2 loader'),
    (r'Migrator', 'V2 Loader'),
    
    # Remove backwards compatibility
    (r'backward[s]? compatibility', 'V2 clean implementation'),
    (r'Backward[s]? Compatibility', 'V2 Clean Implementation'),
    (r'rollback plan[^\n]+\n', ''),
    (r'Rollback Plan[^\n]+\n', ''),
    (r'feature flag[^\n]+\n', ''),
    (r'Feature Flag[^\n]+\n', ''),
    (r'USE_NEW_ANA[^\n]+\n', ''),
    (r'parallel validation', 'V2 validation'),
    (r'Parallel Validation', 'V2 Validation'),
    (r'95%\+ match rate[^\n]+', 'All V2 tests pass'),
    
    # Clean up step headers
    (r'### Step \d+: ([^\(]+)\([^\)]+\)', r'### Step \1'),
    (r'### Step (\d+): ([^\n]+)', r'### Step \1: \2'),
    
    # Update references
    (r'refactor', 'implement'),
    (r'Refactor', 'Implement'),
]

def clean_file(file_path):
    """Clean a single markdown file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original = content
    
    # Apply all patterns
    for pattern, replacement in patterns:
        if callable(replacement):
            content = re.sub(pattern, replacement, content)
        else:
            content = re.sub(pattern, replacement, content)
    
    # Clean up multiple blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    if content != original:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Cleaned: {file_path.name}")
    else:
        print(f"⏭️  No changes: {file_path.name}")

# Process all markdown files
for md_file in task_cards_dir.rglob("*.md"):
    clean_file(md_file)

print("\n✅ Task cards cleaned for V2!")