#!/usr/bin/env python3
"""
Extract complete typification hierarchy from knowledge_rag.csv
Creates structured JSON file for validation in the 5-level typification workflow
"""

import json
import pandas as pd
from collections import defaultdict
from typing import Dict, Set, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_typification_block(typification_text: str) -> Dict[str, str]:
    """Parse a typification block into structured components"""
    lines = typification_text.strip().split('\n')
    components = {}
    
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            components[key.strip()] = value.strip()
    
    return components

def extract_hierarchy() -> Dict:
    """Extract complete hierarchical structure from CSV"""
    logger.info("Loading knowledge_rag.csv...")
    
    # Load CSV
    df = pd.read_csv("context/knowledge/knowledge_rag.csv")
    logger.info(f"Loaded {len(df)} rows from CSV")
    
    # Build hierarchical structure
    hierarchy = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    
    # Track statistics
    stats = {
        'total_rows': len(df),
        'unique_units': set(),
        'unique_products': set(),
        'unique_motives': set(),
        'unique_submotives': set(),
        'invalid_rows': 0
    }
    
    for idx, row in df.iterrows():
        try:
            # Parse typification components
            components = parse_typification_block(row['typification'])
            
            # Extract hierarchy levels
            unit = components.get('Unidade de negócio', '').strip()
            product = components.get('Produto', '').strip()
            motive = components.get('Motivo', '').strip()
            submotive = components.get('Submotivo', '').strip()
            conclusion = components.get('Conclusão', '').strip()
            
            # Validate all components exist
            if not all([unit, product, motive, submotive, conclusion]):
                logger.warning(f"Row {idx}: Missing components - {components}")
                stats['invalid_rows'] += 1
                continue
            
            # Add to hierarchy
            hierarchy[unit][product][motive].add(submotive)
            
            # Track statistics
            stats['unique_units'].add(unit)
            stats['unique_products'].add(product)
            stats['unique_motives'].add(motive)
            stats['unique_submotives'].add(submotive)
            
        except Exception as e:
            logger.error(f"Row {idx}: Error parsing typification - {e}")
            stats['invalid_rows'] += 1
    
    # Convert sets to sorted lists for JSON serialization
    result = {}
    for unit, products in hierarchy.items():
        result[unit] = {}
        for product, motives in products.items():
            result[unit][product] = {}
            for motive, submotives in motives.items():
                result[unit][product][motive] = sorted(list(submotives))
    
    # Create output directory
    import os
    os.makedirs("workflows/conversation_typification", exist_ok=True)
    
    # Save hierarchy to JSON
    output_file = "workflows/conversation_typification/hierarchy.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Hierarchy saved to {output_file}")
    
    # Print statistics
    logger.info("\n=== HIERARCHY STATISTICS ===")
    logger.info(f"Total rows processed: {stats['total_rows']}")
    logger.info(f"Invalid rows: {stats['invalid_rows']}")
    logger.info(f"Business Units: {len(stats['unique_units'])}")
    logger.info(f"Products: {len(stats['unique_products'])}")
    logger.info(f"Motives: {len(stats['unique_motives'])}")
    logger.info(f"Submotives: {len(stats['unique_submotives'])}")
    
    logger.info("\n=== BUSINESS UNITS ===")
    for unit in sorted(stats['unique_units']):
        product_count = len(result.get(unit, {}))
        logger.info(f"• {unit}: {product_count} products")
    
    # Calculate total paths
    total_paths = sum(
        len(motives) 
        for products in result.values() 
        for motives in products.values()
    )
    logger.info(f"\nTotal unique typification paths: {total_paths}")
    
    return result

def validate_hierarchy(hierarchy: Dict) -> bool:
    """Validate the extracted hierarchy structure"""
    logger.info("Validating hierarchy structure...")
    
    # Check required business units
    required_units = {
        "Adquirência Web",
        "Adquirência Web / Adquirência Presencial", 
        "Emissão",
        "PagBank"
    }
    
    found_units = set(hierarchy.keys())
    missing_units = required_units - found_units
    
    if missing_units:
        logger.error(f"Missing business units: {missing_units}")
        return False
    
    # Validate each business unit has products
    for unit, products in hierarchy.items():
        if not products:
            logger.error(f"Business unit '{unit}' has no products")
            return False
            
        # Validate each product has motives
        for product, motives in products.items():
            if not motives:
                logger.error(f"Product '{product}' in unit '{unit}' has no motives")
                return False
                
            # Validate each motive has submotives
            for motive, submotives in motives.items():
                if not submotives:
                    logger.error(f"Motive '{motive}' in product '{product}' has no submotives")
                    return False
    
    logger.info("Hierarchy validation completed successfully!")
    return True

def main():
    """Main extraction and validation process"""
    logger.info("Starting typification hierarchy extraction...")
    
    try:
        # Extract hierarchy
        hierarchy = extract_hierarchy()
        
        # Validate structure
        if validate_hierarchy(hierarchy):
            logger.info("✅ Hierarchy extraction and validation completed successfully!")
            return hierarchy
        else:
            logger.error("❌ Hierarchy validation failed!")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error during extraction: {e}")
        return None

if __name__ == "__main__":
    main()