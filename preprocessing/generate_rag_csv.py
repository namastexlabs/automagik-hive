#!/usr/bin/env python3
"""
Generate a new CSV file from validated knowledge files.
This creates a CSV with columns: problem, solution, typification, business_unit
"""

import re
import csv
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
    # Remove extra whitespace while preserving newlines
    lines = text.split('\n')
    normalized_lines = [' '.join(line.split()) for line in lines]
    return '\n'.join(normalized_lines).strip()


def extract_business_unit(typification: str) -> str:
    """Extract business unit from typification text."""
    lines = typification.split('\n')
    for line in lines:
        if 'Unidade de negócio:' in line:
            # Extract just the value after the colon
            parts = line.split(':', 1)
            if len(parts) == 2:
                unit = parts[1].strip()
                # Normalize the unit name
                if 'Adquirência Web' in unit:
                    if 'Presencial' in unit:
                        return 'Adquirência Web / Adquirência Presencial'
                    return 'Adquirência Web'
                elif 'Emissão' in unit:
                    return 'Emissão'
                elif 'PagBank' in unit:
                    return 'PagBank'
    return ''  # Default if not found


def parse_knowledge_file(file_path: Path) -> List[Dict[str, str]]:
    """
    Parse a knowledge file and extract documents.
    
    Returns:
        List of documents with 'problem', 'solution', 'typification', 'business_unit' keys
    """
    documents = []
    
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Split by document separator
        content = content.replace('\r\n', '\n')
        raw_docs = re.split(r'---\s*\n', content)
        
        # Remove empty docs
        raw_docs = [doc.strip() for doc in raw_docs if doc.strip()]
        
        for doc in raw_docs:
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
                    # Preserve the full content for typification, normalize others
                    if key == 'typification':
                        sections[key] = match.group(1).strip()
                    else:
                        sections[key] = normalize_text(match.group(1))
            
            # Check if all sections found
            if len(sections) == 3:
                # Extract business unit
                business_unit = extract_business_unit(sections['typification'])
                
                # Clean typification to just contain the structured data
                typification_lines = []
                for line in sections['typification'].split('\n'):
                    line = line.strip()
                    if line and not line.startswith('---'):
                        typification_lines.append(line)
                
                document = {
                    'problem': sections['problem'],
                    'solution': sections['solution'],
                    'typification': '\n'.join(typification_lines),
                    'business_unit': business_unit
                }
                documents.append(document)
            
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
    
    return documents


def main():
    """Generate CSV from knowledge files."""
    knowledge_dir = Path('docs/knowledge_examples')
    files = ['antecipacao.md', 'cartoes.md', 'conta.md']
    
    all_documents = []
    business_unit_counts = {}
    
    print("Generating CSV from knowledge files...\n")
    
    # Parse all files
    for file_name in files:
        file_path = knowledge_dir / file_name
        print(f"Processing {file_name}...")
        
        documents = parse_knowledge_file(file_path)
        all_documents.extend(documents)
        
        # Count business units
        for doc in documents:
            unit = doc['business_unit']
            if unit:
                business_unit_counts[unit] = business_unit_counts.get(unit, 0) + 1
        
        print(f"  - Extracted {len(documents)} documents")
    
    print(f"\nTotal documents: {len(all_documents)}")
    print(f"\nBusiness units found:")
    for unit, count in sorted(business_unit_counts.items()):
        print(f"  - '{unit}': {count} documents")
    
    # Generate CSV
    csv_path = Path('knowledge/knowledge_rag.csv')
    csv_path.parent.mkdir(exist_ok=True)
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['problem', 'solution', 'typification', 'business_unit']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        
        writer.writeheader()
        for doc in all_documents:
            writer.writerow(doc)
    
    print(f"\n✅ CSV generated successfully: {csv_path}")
    print(f"   - Total rows: {len(all_documents)}")
    print(f"   - Columns: {', '.join(fieldnames)}")
    
    # Save summary
    summary = {
        'total_documents': len(all_documents),
        'business_units': business_unit_counts,
        'csv_path': str(csv_path),
        'columns': fieldnames
    }
    
    summary_path = Path('csv_generation_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\nSummary saved to: {summary_path}")


if __name__ == '__main__':
    main()