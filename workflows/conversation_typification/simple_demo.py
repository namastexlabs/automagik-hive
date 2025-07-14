#!/usr/bin/env python3
"""
Simple demo of the typification workflow without complex imports
Demonstrates the core functionality and validation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from workflows.conversation_typification.models import (
    HierarchicalTypification,
    UnidadeNegocio,
    validate_typification_path,
    get_valid_products,
    get_valid_motives,
    get_valid_submotives
)

def demonstrate_hierarchy_validation():
    """Demonstrate hierarchy validation features"""
    
    print("=== HIERARCHY VALIDATION DEMO ===\n")
    
    # Show valid products for each business unit
    business_units = ["Adquirência Web", "Emissão", "PagBank", "Adquirência Web / Adquirência Presencial"]
    
    for unit in business_units:
        products = get_valid_products(unit)
        print(f"📊 {unit}: {len(products)} products")
        for product in products[:2]:  # Show first 2
            print(f"   • {product}")
            
            # Show motives for first product
            motives = get_valid_motives(unit, product)
            if motives:
                print(f"     → {len(motives)} motives (first: {motives[0]})")
                
                # Show submotives for first motive
                submotives = get_valid_submotives(unit, product, motives[0])
                if submotives:
                    print(f"       → {len(submotives)} submotives")
        print()

def demonstrate_valid_typification():
    """Demonstrate creating valid typifications"""
    
    print("=== VALID TYPIFICATION DEMO ===\n")
    
    # Create a valid typification
    typification = HierarchicalTypification(
        unidade_negocio=UnidadeNegocio.ADQUIRENCIA_WEB,
        produto="Antecipação de Vendas",
        motivo="Dúvidas sobre a Antecipação de Vendas",
        submotivo="Cliente orientado sobre a Antecipação de Vendas"
    )
    
    print(f"✅ Valid typification created:")
    print(f"   Path: {typification.hierarchy_path}")
    print(f"   Business Unit: {typification.unidade_negocio.value}")
    print(f"   Product: {typification.produto}")
    print(f"   Conclusion: {typification.conclusao}")
    print()
    
    # Validate the path
    validation = validate_typification_path(
        typification.unidade_negocio.value,
        typification.produto,
        typification.motivo,
        typification.submotivo
    )
    
    print(f"✅ Validation result: {validation.valid}")
    print(f"   Level reached: {validation.level_reached}")
    print()

def demonstrate_invalid_typification():
    """Demonstrate validation of invalid typifications"""
    
    print("=== INVALID TYPIFICATION DEMO ===\n")
    
    # Try invalid product for business unit
    validation = validate_typification_path(
        "PagBank",  # Business unit
        "Antecipação de Vendas",  # Invalid product for PagBank
        "Some motive",
        "Some submotive"
    )
    
    print(f"❌ Invalid typification:")
    print(f"   Valid: {validation.valid}")
    print(f"   Level reached: {validation.level_reached}")
    print(f"   Error: {validation.error_message}")
    print(f"   Suggestions: {validation.suggested_corrections[:3]}")
    print()

def demonstrate_all_valid_paths():
    """Show examples of all valid paths"""
    
    print("=== ALL VALID PATHS SAMPLE ===\n")
    
    total_paths = 0
    
    # Get all business units
    business_units = ["Adquirência Web", "Emissão", "PagBank", "Adquirência Web / Adquirência Presencial"]
    
    for unit in business_units:
        products = get_valid_products(unit)
        unit_paths = 0
        
        for product in products:
            motives = get_valid_motives(unit, product)
            
            for motive in motives:
                submotives = get_valid_submotives(unit, product, motive)
                unit_paths += len(submotives)
        
        total_paths += unit_paths
        print(f"📊 {unit}: {unit_paths} complete paths")
    
    print(f"\n🎯 Total valid typification paths: {total_paths}")
    print()

def demonstrate_pydantic_validation():
    """Demonstrate Pydantic validation in action"""
    
    print("=== PYDANTIC VALIDATION DEMO ===\n")
    
    # Valid case
    try:
        typification = HierarchicalTypification(
            unidade_negocio=UnidadeNegocio.PAGBANK,
            produto="Pix",
            motivo="Envio de Pix",
            submotivo="Bloqueio de transação por segurança"
        )
        print("✅ Valid typification created successfully")
        print(f"   Path: {typification.hierarchy_path}")
        print()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print()
    
    # Invalid case - wrong product for business unit
    try:
        typification = HierarchicalTypification(
            unidade_negocio=UnidadeNegocio.PAGBANK,
            produto="Antecipação de Vendas",  # Invalid for PagBank
            motivo="Some motive",
            submotivo="Some submotive"
        )
        print("❌ This should have failed!")
    except Exception as e:
        print("✅ Pydantic validation correctly rejected invalid combination")
        print(f"   Error: {str(e)[:100]}...")
        print()

def main():
    """Main demo function"""
    
    print("🎯 PagBank 5-Level Typification Workflow Demo")
    print("=" * 50)
    print()
    
    try:
        demonstrate_hierarchy_validation()
        demonstrate_valid_typification()
        demonstrate_invalid_typification()
        demonstrate_all_valid_paths()
        demonstrate_pydantic_validation()
        
        print("✅ All demonstrations completed successfully!")
        print("\n🏁 The typification workflow is ready for integration with Ana team!")
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()