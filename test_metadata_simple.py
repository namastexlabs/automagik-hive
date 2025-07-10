#!/usr/bin/env python3
"""
Simple test to verify metadata extraction is working
"""

from knowledge.enhanced_csv_reader import EnhancedCSVReader
from pathlib import Path


def test_metadata_extraction():
    """Test that CSV metadata extraction is working on actual data"""
    
    csv_path = Path("knowledge/pagbank_knowledge.csv")
    
    if not csv_path.exists():
        print("❌ CSV file not found")
        return False
    
    print("=== Testing Metadata Extraction on Real Data ===")
    
    # Create enhanced reader
    reader = EnhancedCSVReader(
        content_column="conteudo",
        metadata_columns=["area", "tipo_produto", "tipo_informacao", "nivel_complexidade", "publico_alvo"],
        exclude_columns=["palavras_chave", "atualizado_em"]
    )
    
    # Read just first few documents to test
    docs = reader.read(csv_path)
    
    print(f"Total documents created: {len(docs)}")
    
    # Test first 3 documents
    for i, doc in enumerate(docs[:3]):
        print(f"\nDocument {i + 1}:")
        print(f"  Content: {doc.content[:100]}...")
        print(f"  Metadata: {doc.meta_data}")
    
    # Test filtering capabilities
    print("\n=== Testing Filtering ===")
    
    # Count by area
    areas = {}
    for doc in docs:
        area = doc.meta_data.get('area', 'unknown')
        areas[area] = areas.get(area, 0) + 1
    
    print("Documents by area:")
    for area, count in sorted(areas.items()):
        print(f"  {area}: {count}")
    
    # Count by tipo_produto
    produtos = {}
    for doc in docs:
        produto = doc.meta_data.get('tipo_produto', 'unknown')
        produtos[produto] = produtos.get(produto, 0) + 1
    
    print(f"\nUnique product types: {len(produtos)}")
    print("Top 5 product types:")
    for produto, count in sorted(produtos.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {produto}: {count}")
    
    # Verify that old chunking-only metadata is NOT the primary metadata
    chunking_only = sum(1 for doc in docs if 'chunk' in doc.meta_data and 'area' not in doc.meta_data)
    metadata_rich = sum(1 for doc in docs if 'area' in doc.meta_data)
    
    print(f"\nMetadata Analysis:")
    print(f"  Documents with CSV metadata (area field): {metadata_rich}")
    print(f"  Documents with only chunking metadata: {chunking_only}")
    
    if metadata_rich > 0:
        print("✅ SUCCESS: CSV columns are being extracted as metadata!")
        print("✅ Metadata filtering is now possible!")
        return True
    else:
        print("❌ FAILURE: CSV columns are NOT being extracted as metadata")
        return False


if __name__ == "__main__":
    test_metadata_extraction()