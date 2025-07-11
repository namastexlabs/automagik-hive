#!/usr/bin/env python3
"""
Validate knowledge files for structural consistency and extract business units.
This script parses the three knowledge files and validates their structure.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import unicodedata


def normalize_text(text: str) -> str:
    """Normalize text by removing non-breaking spaces and extra whitespace."""
    # Replace non-breaking spaces with regular spaces
    text = text.replace('\xa0', ' ')
    # Normalize unicode characters
    text = unicodedata.normalize('NFKC', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text.strip()


def parse_knowledge_file(file_path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    """
    Parse a knowledge file and extract documents.
    
    Returns:
        Tuple of (documents, issues) where documents is a list of dicts with
        'problem', 'solution', 'typification' keys and issues is a list of error messages.
    """
    documents = []
    issues = []
    
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Split by document separator (handling variations)
        # First normalize line endings
        content = content.replace('\r\n', '\n')
        # Split by --- followed by newline or end of string
        raw_docs = re.split(r'---\s*\n', content)
        
        # Remove empty docs
        raw_docs = [doc.strip() for doc in raw_docs if doc.strip()]
        
        for i, doc in enumerate(raw_docs):
            # Expected headers
            headers = {
                'problem': '## Problema a ser resolvido',
                'solution': '## Como resolver o problema',
                'typification': '## Como tipificar o atendimento'
            }
            
            # Extract sections using regex
            sections = {}
            for key, header in headers.items():
                pattern = rf'{re.escape(header)}\n(.*?)(?=##|$)'
                match = re.search(pattern, doc, re.DOTALL)
                if match:
                    sections[key] = normalize_text(match.group(1))
                else:
                    issues.append(f"Document {i+1}: Missing section '{header}'")
            
            # Check if all sections found
            if len(sections) == 3:
                # Validate non-empty content
                for key, content in sections.items():
                    if not content:
                        issues.append(f"Document {i+1}: Empty content in section '{headers[key]}'")
                
                documents.append(sections)
            
    except Exception as e:
        issues.append(f"Error reading file: {str(e)}")
    
    return documents, issues


def extract_business_units(documents: List[Dict[str, str]]) -> List[str]:
    """Extract unique business units from typification sections."""
    business_units = set()
    
    for doc in documents:
        typification = doc.get('typification', '')
        
        # Look for "Unidade de negócio: " pattern and capture just the unit name
        # Split by lines to handle multi-line typification
        lines = typification.split('\n')
        for line in lines:
            if 'Unidade de negócio:' in line:
                # Extract just the value after the colon
                parts = line.split(':', 1)
                if len(parts) == 2:
                    unit = normalize_text(parts[1])
                    # Remove trailing punctuation and spaces
                    unit = unit.rstrip('.,;: ')
                    if unit:  # Only add non-empty units
                        business_units.add(unit)
                break  # Only take the first occurrence
    
    return sorted(list(business_units))


def main():
    """Main validation function."""
    knowledge_dir = Path('docs/knowledge_examples')
    files = ['antecipacao.md', 'cartoes.md', 'conta.md']
    
    validation_report = {}
    all_documents = []
    all_business_units = set()
    
    print("Validating knowledge files...\n")
    
    for file_name in files:
        file_path = knowledge_dir / file_name
        print(f"Processing {file_name}...")
        
        documents, issues = parse_knowledge_file(file_path)
        
        validation_report[file_name] = {
            'doc_count': len(documents),
            'issues': issues,
            'line_count': len(file_path.read_text().splitlines()) if file_path.exists() else 0
        }
        
        all_documents.extend(documents)
        
        # Extract business units from this file
        units = extract_business_units(documents)
        all_business_units.update(units)
        
        print(f"  - Documents: {len(documents)}")
        print(f"  - Issues: {len(issues)}")
        if issues:
            for issue in issues[:3]:  # Show first 3 issues
                print(f"    * {issue}")
            if len(issues) > 3:
                print(f"    * ... and {len(issues) - 3} more issues")
    
    print(f"\nTotal documents: {len(all_documents)}")
    print(f"\nUnique business units found: {len(all_business_units)}")
    for unit in sorted(all_business_units):
        # Count occurrences
        count = sum(1 for doc in all_documents if unit in doc.get('typification', ''))
        print(f"  - '{unit}' ({count} occurrences)")
    
    # Save validation report
    report_path = Path('validation_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'files': validation_report,
            'total_documents': len(all_documents),
            'unique_business_units': sorted(list(all_business_units))
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nValidation report saved to: {report_path}")
    
    # Check for critical issues
    total_issues = sum(len(report['issues']) for report in validation_report.values())
    if total_issues == 0:
        print("\n✅ All files are valid and ready for CSV generation!")
        return True
    else:
        print(f"\n⚠️  Found {total_issues} issues that need attention.")
        return False


if __name__ == '__main__':
    main()