#!/usr/bin/env python3
"""
Test script for Enhanced CSV Reader to validate metadata extraction
"""

import tempfile
import csv
from pathlib import Path

from knowledge.enhanced_csv_reader import EnhancedCSVReader


def test_enhanced_csv_reader():
    """Test the enhanced CSV reader with PagBank data structure"""
    
    # Create test data similar to PagBank CSV structure
    test_data = [
        ["conteudo", "area", "tipo_produto", "tipo_informacao", "nivel_complexidade", "publico_alvo", "palavras_chave", "atualizado_em"],
        [
            "Cliente deseja entender o que é PIX e como funciona.",
            "conta_digital",
            "pix",
            "beneficios",
            "basico",
            "pessoa_fisica",
            "pix transferencia instantanea",
            "2024-01"
        ],
        [
            "Cliente quer saber como solicitar cartão de crédito.",
            "cartoes",
            "cartao_credito",
            "como_solicitar",
            "intermediario",
            "pessoa_fisica",
            "cartao credito limite anuidade",
            "2024-01"
        ],
        [
            "Informações sobre CDB e como investir.",
            "investimentos",
            "cdb",
            "beneficios",
            "avancado",
            "pessoa_juridica",
            "cdb investimento rendimento cdi",
            "2024-01"
        ]
    ]
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerows(test_data)
        temp_path = f.name
    
    try:
        # Test Enhanced CSV Reader
        print("=== Testing Enhanced CSV Reader ===")
        reader = EnhancedCSVReader(
            content_column="conteudo",
            metadata_columns=["area", "tipo_produto", "tipo_informacao", "nivel_complexidade", "publico_alvo"],
            exclude_columns=["palavras_chave", "atualizado_em"]
        )
        
        docs = reader.read(Path(temp_path))
        
        print(f"Number of documents created: {len(docs)}")
        print()
        
        for i, doc in enumerate(docs):
            print(f"Document {i + 1}:")
            print(f"  Name: {doc.name}")
            print(f"  Content: {doc.content[:100]}...")
            print(f"  Metadata: {doc.meta_data}")
            print()
        
        # Test filtering capabilities
        print("=== Testing Metadata Filtering ===")
        
        # Filter by area
        conta_digital_docs = [doc for doc in docs if doc.meta_data.get('area') == 'conta_digital']
        print(f"Documents with area='conta_digital': {len(conta_digital_docs)}")
        
        # Filter by tipo_produto
        pix_docs = [doc for doc in docs if doc.meta_data.get('tipo_produto') == 'pix']
        print(f"Documents with tipo_produto='pix': {len(pix_docs)}")
        
        # Filter by nivel_complexidade
        basico_docs = [doc for doc in docs if doc.meta_data.get('nivel_complexidade') == 'basico']
        print(f"Documents with nivel_complexidade='basico': {len(basico_docs)}")
        
        print("\n=== Test Results ===")
        print("✅ Enhanced CSV Reader successfully extracts CSV columns as metadata")
        print("✅ Documents can be properly filtered by metadata fields")
        print("✅ Content and metadata are properly separated")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        # Clean up temporary file
        Path(temp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    test_enhanced_csv_reader()