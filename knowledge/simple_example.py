#!/usr/bin/env python3
"""
Simple example of how to use the Knowledge Hot Reload Manager
"""

from knowledge.hot_reload_manager import KnowledgeHotReloadManager, create_quick_entry

def demo_knowledge_management():
    """Demonstrate simple knowledge management"""
    
    print("🎯 KISS Knowledge Management Demo")
    print("=" * 50)
    
    # 1. Start the manager (would run in background in real app)
    manager = KnowledgeHotReloadManager()
    print("\n1. Manager initialized ✅")
    
    # 2. Add some knowledge entries
    print("\n2. Adding knowledge entries...")
    
    # Example 1: New PIX feature
    create_quick_entry(
        content="PIX Agendado: Nova funcionalidade permite agendar transferências PIX para datas futuras, até 60 dias de antecedência. Disponível no app PagBank.",
        area="conta_digital",
        tipo_produto="pix",
        tipo_informacao="beneficios",
        palavras_chave="pix agendado transferencia futura 60 dias app pagbank nova funcionalidade"
    )
    
    # Example 2: Credit card update  
    create_quick_entry(
        content="Limite de Crédito Dinâmico: O PagBank agora oferece aumento automático de limite baseado no comportamento de pagamento do cliente.",
        area="cartoes",
        tipo_produto="limite_credito",
        tipo_informacao="beneficios",
        palavras_chave="limite credito dinamico aumento automatico comportamento pagamento cliente"
    )
    
    # Example 3: Investment product
    create_quick_entry(
        content="CDB Liquidez Diária: Novo produto de investimento CDB com liquidez diária e rendimento de 100% do CDI.",
        area="investimentos", 
        tipo_produto="cdb",
        tipo_informacao="beneficios",
        palavras_chave="cdb liquidez diaria rendimento 100 cdi investimento novo produto"
    )
    
    print("✅ Created 3 knowledge update files")
    print("\n📁 Files created in knowledge/updates/ folder")
    print("   They will be automatically processed by the manager")
    
    print("\n🔄 To see this in action:")
    print("   1. Run 'uv run python knowledge/hot_reload_manager.py' in another terminal")
    print("   2. The manager will process the files automatically")
    print("   3. Add more files to knowledge/updates/ and watch them get processed")

if __name__ == "__main__":
    demo_knowledge_management()